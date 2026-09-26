"""Streamlit UI. Run: streamlit run app.py"""
import os
from io import BytesIO
import streamlit as st
from dotenv import load_dotenv
from openai import OpenAI
from docx import Document
from core import (
    DEFAULT_SECTIONS, add_revision, build_instructions, citation_audit,
    export_docx, load_project, markdown_manuscript, parse_references,
    project_template, save_project, section_text,
)

load_dotenv()
st.set_page_config(page_title='Research Writing Copilot', page_icon='✦', layout='wide')
st.markdown('''<style>
.stApp {background:linear-gradient(125deg,#09182e,#111d35 65%,#18223a);color:#f7f5ef;}
[data-testid="stSidebar"] {background:#0a172a;}
h1,h2,h3 {color:#e6c781!important;}
.stButton>button[kind="primary"] {background:#b99548;color:#08162b;border:0;font-weight:700;}
.stButton>button {border-color:#b99548;}
[data-testid="stMetricValue"] {color:#e6c781;}
</style>''', unsafe_allow_html=True)

if 'project' not in st.session_state:
    st.session_state.project = project_template()
if 'generated' not in st.session_state:
    st.session_state.generated = ''
if 'review' not in st.session_state:
    st.session_state.review = ''

p = st.session_state.project
st.title('✦ Research Writing Copilot')
st.caption('Bilingual academic drafting • Author-grounded content • Bibliography key checks • Version history • Local-first project files')

with st.sidebar:
    st.subheader('Model settings')
    api_key = st.text_input('OpenAI API key', value='', type='password', help='Used only for API requests in this session; not written to exported projects.')
    model = st.text_input('Model ID', value=os.getenv('OPENAI_MODEL', 'gpt-4.1'))
    st.divider()
    st.subheader('Project portability')
    uploaded_project = st.file_uploader('Import project JSON', type=['json'])
    if uploaded_project and st.button('Load imported project'):
        try:
            st.session_state.project = load_project(uploaded_project.getvalue().decode('utf-8'))
            st.rerun()
        except Exception as e:
            st.error(str(e))
    st.download_button('Export project JSON', save_project(p), file_name='research_project.json', mime='application/json', use_container_width=True)
    if st.button('New empty project', use_container_width=True):
        st.session_state.project = project_template()
        st.session_state.generated = ''
        st.session_state.review = ''
        st.rerun()
    st.caption('Projects remain in your browser session unless exported. No server-side database in this MVP.')

def call_model(instructions: str, text: str) -> str:
    if not api_key.strip():
        raise ValueError('Supply an OpenAI API key in the sidebar.')
    client = OpenAI(api_key=api_key.strip(), timeout=90.0, max_retries=2)
    response = client.responses.create(model=model.strip(), instructions=instructions, input=text, store=False)
    if not response.output_text.strip():
        raise RuntimeError('Model returned no plain text. Check model ID and API access.')
    return response.output_text.strip()

def read_source(file):
    name = file.name.lower()
    raw = file.getvalue()
    if name.endswith(('.md', '.txt', '.csv')):
        return raw.decode('utf-8-sig')
    if name.endswith('.docx'):
        d = Document(BytesIO(raw))
        parts = [x.text for x in d.paragraphs if x.text.strip()]
        for table in d.tables:
            for row in table.rows:
                parts.append(' | '.join(c.text for c in row.cells))
        return '\n'.join(parts)
    return ''

metadata, sources, writer, qa, manuscript = st.tabs(['01 / Study brief', '02 / Sources & voice', '03 / Write & revise', '04 / Quality checks', '05 / Manuscript'])

with metadata:
    st.subheader('Define the actual contribution')
    p['title'] = st.text_input('Manuscript title', value=p['title'])
    a,b,c = st.columns(3)
    p['language'] = a.selectbox('Writing language', ['English','Arabic'], index=0 if p['language']=='English' else 1)
    types = ['Original research','Review','Methods paper','Conceptual paper','Case study','Short communication']
    p['article_type'] = b.selectbox('Article type', types, index=types.index(p['article_type']) if p['article_type'] in types else 0)
    p['target_journal'] = c.text_input('Target journal / style', value=p['target_journal'])
    p['research_question'] = st.text_area('Research question / problem statement', p['research_question'], height=100)
    p['contribution'] = st.text_area('Author original contribution — what is genuinely new?', p['contribution'], height=120)
    p['method'] = st.text_area('Actual methodology / design / data provenance', p['method'], height=130)
    p['verified_findings'] = st.text_area('Verified results only — paste exact values, units and comparisons', p['verified_findings'], height=130)
    p['limitations'] = st.text_area('Actual study limitations', p['limitations'], height=100)

with sources:
    st.subheader('Ground the draft')
    files = st.file_uploader('Upload source notes or author samples (.txt, .md, .csv, .docx)', type=['txt','md','csv','docx'], accept_multiple_files=True)
    if files and st.button('Append uploads to source notes'):
        chunks = []
        for f in files:
            try:
                chunks.append(f'\n### File: {f.name}\n'+read_source(f)[:40000])
            except Exception as e:
                st.warning(f'Cannot extract {f.name}: {e}')
        p['source_notes'] += '\n'.join(chunks)
        st.success('Uploaded text appended. Review the source notes before generation.')
    p['source_notes'] = st.text_area('Source notes / extracted literature / research evidence', p['source_notes'], height=250)
    st.caption('Reference format: KEY | title, authors, year, DOI/URL, and evidence note. Only enter references you have checked.')
    p['references'] = st.text_area('Bibliography whitelist (one per line)', p['references'], height=160, placeholder='smith2024 | Smith et al. (2024). Title. DOI... | Supports claim X')
    p['author_voice'] = st.text_area('Author-owned style samples (optional)', p['author_voice'], height=150)
    refs, errors = parse_references(p['references'])
    st.write(f'Validated reference keys: **{len(refs)}**')
    for err in errors:
        st.error(err)

with writer:
    st.subheader('Section-by-section drafting')
    section = st.selectbox('Active section', list(p['sections']))
    instructions = st.text_area('Your instructions for this section', height=100, placeholder='State the central argument, emphasis, expected length, key sources and anything to avoid.')
    current = st.text_area('Current section (editable)', p['sections'][section], height=280, key='edit_'+section)
    left,mid,right = st.columns(3)
    if left.button('Save manual edits', use_container_width=True):
        add_revision(p, section, 'author manual edit', current)
        st.success('Saved in session and version history.')
    if mid.button('Generate section', type='primary', use_container_width=True):
        try:
            with st.spinner('Generating from your supplied evidence...'):
                st.session_state.generated = call_model(build_instructions(p,'draft',section,instructions), 'Draft this manuscript section.')
            st.success('Generated a candidate; review and accept explicitly.')
        except Exception as e:
            st.error(str(e))
    if right.button('Revise current section', use_container_width=True):
        try:
            if not current.strip():
                raise ValueError('Write or generate the section first.')
            with st.spinner('Revising the current section...'):
                st.session_state.generated = call_model(build_instructions(p,'revise',section,instructions), current)
            st.success('Revision prepared for author acceptance.')
        except Exception as e:
            st.error(str(e))
    if st.session_state.generated:
        candidate = st.text_area('Candidate output — inspect and edit before accepting', value=st.session_state.generated, height=360)
        if st.button('Accept candidate as active section', type='primary'):
            add_revision(p, section, 'AI candidate accepted by author', candidate)
            st.session_state.generated = ''
            st.rerun()
    with st.expander('Revision history'):
        for i, entry in reversed(list(enumerate(p['history']))):
            st.caption(f"#{i+1} — {entry['timestamp_utc']} — {entry['section']} — {entry['source']}")
            if st.button(f"Restore prior text from revision #{i+1}", key=f'restore_{i}'):
                add_revision(p, entry['section'], 'author restored earlier version', entry['previous'])
                st.rerun()

with qa:
    st.subheader('Citation-key and completeness diagnostics')
    refs, errors = parse_references(p['references'])
    audit = citation_audit(section_text(p), refs)
    col1,col2,col3 = st.columns(3)
    col1.metric('In-text citation tags', audit['in_text_citations'])
    col2.metric('Unknown citation keys', len(audit['unknown_keys']))
    col3.metric('Unused bibliography entries', len(audit['unused_references']))
    if audit['unknown_keys']:
        st.error('Unknown reference keys: ' + ', '.join(audit['unknown_keys']))
    if audit['unused_references']:
        st.info('Unused keys: ' + ', '.join(audit['unused_references']))
    if errors:
        st.error('Bibliography has formatting errors: ' + '; '.join(errors))
    st.caption('A valid key confirms membership in your bibliography, NOT that the source exists or supports the associated claim. Manually verify each citation and result.')
    selected = st.selectbox('Section to review', list(p['sections']), key='review_section')
    focus = st.text_input('Editorial review focus (optional)', key='review_focus')
    if st.button('Run academic editorial review'):
        try:
            if not p['sections'][selected].strip():
                raise ValueError('Selected section is empty.')
            with st.spinner('Reviewing evidence, logic and clarity...'):
                st.session_state.review = call_model(build_instructions(p,'review',selected,focus), p['sections'][selected])
        except Exception as e:
            st.error(str(e))
    if st.session_state.review:
        st.markdown(st.session_state.review)
        st.download_button('Download review notes', st.session_state.review, file_name='editorial_review.md')

with manuscript:
    st.subheader('Assemble and export')
    content = markdown_manuscript(p)
    st.markdown(content)
    st.download_button('Download Markdown', data=content, file_name='manuscript.md', mime='text/markdown', use_container_width=True)
    st.download_button('Download Word (.docx)', data=export_docx(p), file_name='manuscript.docx', mime='application/vnd.openxmlformats-officedocument.wordprocessingml.document', use_container_width=True)
    st.warning('This tool does not guarantee detector outcomes, source authenticity, publication acceptance, or compliance with journal AI-disclosure rules. The author must verify claims, citations, and disclosure obligations.')
