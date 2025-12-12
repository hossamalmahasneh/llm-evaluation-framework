# llm-evaluation-framework
# 🏛️ PaperGrade: Deterministic Academic Evaluation Agent

![Python](https://img.shields.io/badge/Python-3.10%2B-blue?style=for-the-badge&logo=python)
![OpenAI](https://img.shields.io/badge/OpenAI-API-green?style=for-the-badge&logo=openai)
![LlamaIndex](https://img.shields.io/badge/LlamaIndex-RAG-orange?style=for-the-badge)
![License](https://img.shields.io/badge/License-MIT-lightgrey?style=for-the-badge)

> **Beyond Summarization:** An agentic workflow that ingests academic papers, critiques methodology, and rigorously evaluates content using an "LLM-as-a-Judge" framework.

---

## 🧐 The Problem
Standard "Chat with PDF" tools are insufficient for academic or professional use. They suffer from:
1.  **Hallucination:** Inventing citations or misinterpreting data.
2.  **Lack of Standardization:** Giving different answers to the same query.
3.  **Subjectivity:** Failing to provide quantitative metrics on paper quality.

## 💡 The Solution
**PaperGrade** is not a chatbot. It is a **deterministic evaluation pipeline**.

It leverages **RAG (Retrieval-Augmented Generation)** to ground answers in the source text and uses a secondary **Evaluator Agent** to grade the output against a strict JSON rubric.

### System Architecture
1.  **Ingestion Layer:** Parses PDF unstructured data into vector embeddings (using `text-embedding-3-small`).
2.  **Retrieval Layer:** Uses Hybrid Search (Keyword + Semantic) to retrieve the specific "Methodology" and "Results" sections.
3.  **Reasoning Engine:** An LLM Agent extracts key claims and cross-references them.
4.  **The Judge (Evaluation Layer):** A separate model instance grades the extracted summary for **Faithfulness** (Binary Pass/Fail) and **Conciseness** (1-5 Likert Scale).

---

## ⚡ Key Features

* **Structured Data Extraction:** Uses strict `JSON Schema` enforcement to ensure outputs are machine-readable, not just conversational text.
* **Anti-Hallucination Guardrails:** Sets `temperature=0.0` for extraction tasks and verifies claims against retrieved chunks.
* **Automated Scoring:** Every analysis includes a metadata report with confidence scores and faithfulness checks.
* **Professor-Grade Rubric:** Evaluation prompts are engineered based on academic peer-review standards.

---

## 🛠️ Tech Stack

* **Core:** Python 3.10+
* **LLM Orchestration:** LlamaIndex / OpenAI API
* **Vector Store:** In-Memory VectorStore (Scalable to Pinecone/Weaviate)
* **Validation:** Pydantic
* **Evaluation:** Custom LLM-as-a-Judge Prompts

---

## 🚀 Quick Start

### 1. Clone & Install
```bash
git clone [https://github.com/yourusername/PaperGrade.git](https://github.com/yourusername/PaperGrade.git)
cd PaperGrade
pip install -r requirements.txt
