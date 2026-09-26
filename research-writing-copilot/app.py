"""Streamlit UI. Run: streamlit run app.py"""
import os
from pathlib import Path
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
THEMES = {
    'Light': dict(bg='#F6F8FC', panel='#FFFFFF', text='#172B46', muted='#52647A', accent='#245B93', line='#C8D5E5', soft='#EAF0F7', placeholder='#748399'),
    'Dark': dict(bg='#101827', panel='#1B2940', text='#F2F6FC', muted='#C4D0E0', accent='#77B7F8', line='#40516B', soft='#263A56', placeholder='#A8B8CB'),
    'High Contrast': dict(bg='#FFFFFF', panel='#FFFFFF', text='#111111', muted='#222222', accent='#073B80', line='#222222', soft='#E8EFFA', placeholder='#444444'),
}
if 'ui_theme' not in st.session_state:
    st.session_state.ui_theme = 'Light'
theme = st.session_state.ui_theme
t = THEMES[theme]
button_bg = '#245B93' if theme == 'Light' else ('#073B80' if theme == 'High Contrast' else '#77B7F8')
button_fg = '#FFFFFF' if theme != 'Dark' else '#101827'
selected_fg = button_fg
st.markdown(f"""<style>
:root {{color-scheme:{'dark' if theme == 'Dark' else 'light'};}}
html,body,.stApp,[data-testid="stAppViewContainer"] {{
 background:{t['bg']}!important;color:{t['text']}!important;font-family:Inter,"Segoe UI",Arial,sans-serif;
}}
[data-testid="stHeader"] {{background:{t['bg']}!important;}}
[data-testid="stMainBlockContainer"] {{max-width:1280px;padding-top:1.6rem;padding-bottom:4rem;}}
[data-testid="stSidebar"],[data-testid="stSidebarContent"] {{background:{t['panel']}!important;border-right:1px solid {t['line']}!important;}}
h1,h2,h3,h4,p,li,label,.stMarkdown,[data-testid="stWidgetLabel"],[data-testid="stMetricLabel"],
[data-testid="stSidebar"] * {{color:{t['text']}!important;}}
h1 {{font-size:2.1rem!important;font-weight:760!important;letter-spacing:-.025em;}}
h2,h3 {{font-weight:700!important;letter-spacing:-.02em;}}
[data-testid="stCaptionContainer"],[data-testid="stCaptionContainer"] * {{color:{t['muted']}!important;}}
.stTextInput input,.stTextArea textarea,input,textarea,[data-baseweb="input"] input,[data-baseweb="textarea"] textarea {{
 background:{t['panel']}!important;color:{t['text']}!important;-webkit-text-fill-color:{t['text']}!important;
 caret-color:{t['accent']}!important;border-radius:9px!important;
}}
input::placeholder,textarea::placeholder {{color:{t['placeholder']}!important;-webkit-text-fill-color:{t['placeholder']}!important;opacity:1!important;}}
[data-baseweb="input"],[data-baseweb="textarea"],[data-baseweb="select"]>div {{
 background:{t['panel']}!important;color:{t['text']}!important;border-color:{t['line']}!important;border-radius:9px!important;
}}
[data-baseweb="select"] input,[data-baseweb="select"] span,[data-baseweb="select"] [role="combobox"] {{
 color:{t['text']}!important;-webkit-text-fill-color:{t['text']}!important;
}}
[data-baseweb="popover"],[role="listbox"],[role="option"] {{background:{t['panel']}!important;color:{t['text']}!important;}}
[role="option"]:hover {{background:{t['soft']}!important;}}
[data-baseweb="input"]:focus-within,[data-baseweb="textarea"]:focus-within,[data-baseweb="select"]:focus-within {{
 border-color:{t['accent']}!important;box-shadow:0 0 0 2px {t['soft']}!important;
}}
.stButton>button[kind="primary"],.stDownloadButton>button {{
 background:{button_bg}!important;color:{button_fg}!important;border:1px solid {button_bg}!important;
 border-radius:9px!important;font-weight:650!important;min-height:2.6rem;
}}
.stButton>button[kind="primary"] *,.stDownloadButton>button * {{color:{button_fg}!important;}}
.stButton>button:not([kind="primary"]) {{
 background:{t['panel']}!important;color:{t['text']}!important;border:1px solid {t['line']}!important;
 border-radius:9px!important;font-weight:600!important;min-height:2.6rem;
}}
.stButton>button:not([kind="primary"]) * {{color:{t['text']}!important;}}
[data-testid="stMetric"],[data-testid="stFileUploader"],[data-testid="stExpander"] {{
 background:{t['panel']}!important;border:1px solid {t['line']}!important;border-radius:11px!important;
}}
[data-testid="stMetric"] {{padding:14px 18px;}}
[data-testid="stMetricValue"] {{color:{t['accent']}!important;font-weight:750;}}
[data-baseweb="tab-list"] {{background:{t['soft']}!important;padding:5px;border-radius:11px;gap:5px;}}
[data-baseweb="tab"] {{background:transparent!important;color:{t['text']}!important;border-radius:8px!important;padding:10px 15px;}}
[data-baseweb="tab"] * {{color:{t['text']}!important;}}
[data-baseweb="tab"][aria-selected="true"] {{background:{button_bg}!important;color:{selected_fg}!important;}}
[data-baseweb="tab"][aria-selected="true"] * {{color:{selected_fg}!important;}}
[data-testid="stAlert"] {{border-radius:10px;}}
hr {{border-color:{t['line']}!important;}}
</style>""", unsafe_allow_html=True)

if 'project' not in st.session_state:
    st.session_state.project = project_template()
if 'generated' not in st.session_state:
    st.session_state.generated = ''
if 'review' not in st.session_state:
    st.session_state.review = ''

p = st.session_state.project
theme_col, spacer_col = st.columns([1, 3])
with theme_col:
    st.selectbox('Appearance', list(THEMES), key='ui_theme', help='Choose a readable theme. Your manuscript content is unaffected.')
st.title('✦ Research Writing Copilot')
st.caption('Bilingual academic drafting • Strict author style profile • Bibliography key checks • Version history • Local-first project files')

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
    profile_path = Path(__file__).with_name('AUTHOR_STYLE_PROFILE.md')
    profile = profile_path.read_text(encoding='utf-8') if profile_path.exists() else ''
    response = client.responses.create(model=model.strip(), instructions=instructions + '\n\nAUTHOR STYLE GUIDANCE:\n' + profile, input=text, store=False)
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
