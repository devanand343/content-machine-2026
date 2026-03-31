# 🤖 Full Content Machine 2026

> **An AI-powered, agentic content creation pipeline** that transforms topic lists into fully-researched, SEO-optimized, human-readable articles — with Human-in-the-Loop (HITL) approval built in. Generates a 1,500-word SEO article in approximately 90 seconds (depending on LLM latency)

---

## 📋 Table of Contents

- [Overview](#overview)
- [Key Features](#key-features)
- [Architecture](#architecture)
- [Project Structure](#project-structure)
- [Tech Stack](#tech-stack)
- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [Configuration](#configuration)
- [Running the App](#running-the-app)
- [How to Use](#how-to-use)
- [Pipeline Flow](#pipeline-flow)
- [Contributing](#contributing)
- [License](#license)

---

## Overview

**Full Content Machine 2026** is a fully automated, multi-agent RAG (Retrieval-Augmented Generation) system built with **LangGraph**, **LangChain**, **ChromaDB**, and **Streamlit**. You upload a simple CSV/Excel content calendar, and the machine produces polished, SEO-optimized articles — one at a time, with a human review checkpoint at the outline stage.

It's designed for content teams, SEO agencies, and solo creators who want to scale output without sacrificing quality.

---

## Key Features

- 📄 **CSV/Excel Content Calendar** — Bulk import topics & keywords
- 🧠 **Multi-Agent RAG Pipeline** — Separate agents for query generation, retrieval, outlining, drafting, and editing
- ✅ **Human-in-the-Loop (HITL)** — Review and approve or regenerate outlines before drafting begins
- 📚 **Knowledge Base Ingestion** — Upload PDFs/TXT files into ChromaDB collections for contextual research
- ✍️ **AI Writing & Editing** — GPT-powered drafting + editorial refinement pass
- 📦 **HTML Export** — Articles exported as clean, publish-ready HTML files
- 🔄 **LangGraph Orchestration** — Stateful, inspectable graph-based agent workflow
- 🎛️ **Streamlit UI** — Clean, interactive web interface — no code required to run

---

## Architecture

```
Content Calendar (CSV/Excel)
        │
        ▼
┌───────────────────┐
│  Query Generator  │  → Generates search queries from topic + keyword
└────────┬──────────┘
         │
         ▼
┌───────────────────┐
│    Retriever      │  → Fetches context from ChromaDB vector store
└────────┬──────────┘
         │
         ▼
┌───────────────────┐
│ Outline Generator │  → Creates structured article outline (GPT-4o)
└────────┬──────────┘
         │
    [HITL Review]   ← Human approves or rejects outline
         │
         ▼
┌───────────────────┐
│   Article Writer  │  → Drafts the full article (async, GPT-4o)
└────────┬──────────┘
         │
         ▼
┌───────────────────┐
│   Article Editor  │  → Refines tone, clarity, SEO
└────────┬──────────┘
         │
         ▼
┌───────────────────┐
│    HTML Exporter  │  → Saves final article to /exports
└───────────────────┘
```

---

## Project Structure

```
Content Machine/
├── app.py                  # Main Streamlit application entry point
├── requirements.txt        # Python dependencies (pinned versions)
├── .env                    # API keys and secrets (NOT committed to git)
├── .gitignore              # Files excluded from version control
├── README.md               # This file
│
├── src/                    # Core application modules
│   ├── __init__.py
│   ├── config.py           # App-wide configuration & ChromaDB collection names
│   ├── db.py               # ChromaDB initialization & collection management
│   ├── ingestion.py        # PDF/TXT ingestion into vector store
│   ├── query_generator.py  # Converts CSV rows into search queries
│   ├── retriever.py        # RAG retrieval from ChromaDB
│   ├── graph.py            # LangGraph pipeline definition & state management
│   ├── writer.py           # AI article drafting agent
│   ├── editor.py           # AI article editing/refinement agent
│   └── exporter.py         # HTML export utilities
│
├── chroma_db/              # Local ChromaDB vector store (auto-generated, git-ignored)
└── exports/                # Generated HTML articles (git-ignored)
```

---

## Tech Stack

| Layer | Technology |
|---|---|
| **UI** | [Streamlit](https://streamlit.io/) |
| **Orchestration** | [LangGraph](https://langchain-ai.github.io/langgraph/) |
| **LLM Framework** | [LangChain](https://python.langchain.com/) |
| **LLM Provider** | [OpenAI GPT-4o](https://openai.com/) |
| **Vector Database** | [ChromaDB](https://www.trychroma.com/) |
| **Embeddings** | OpenAI text-embedding-ada-002 |
| **Data Processing** | Pandas |
| **PDF Parsing** | pypdf, pypdfium2 |
| **Async Runtime** | asyncio + nest_asyncio |
| **Language** | Python 3.11+ |

---

## Prerequisites

- Python **3.11** or higher
- An **OpenAI API key** ([get one here](https://platform.openai.com/api-keys))
- `pip` or a virtual environment manager (`venv`, `conda`, etc.)
- Git (for version control)

---

## Installation

### 1. Clone the Repository

```bash
git clone https://github.com/YOUR_USERNAME/content-machine-2026.git
cd content-machine-2026
```

### 2. Create a Virtual Environment

```bash
python -m venv .myenv
source .myenv/bin/activate        # macOS / Linux
# .myenv\Scripts\activate         # Windows
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

---

## Configuration

Create a `.env` file in the project root (this is **git-ignored** for security):

```bash
cp .env.example .env   # if example exists, otherwise create manually
```

Add your secrets to `.env`:

```env
OPENAI_API_KEY=sk-...your-key-here...
# Add any other API keys or config values here
```

> ⚠️ **Never commit your `.env` file.** It is already listed in `.gitignore`.

---

## Running the App

```bash
# Make sure your virtual environment is active
source .myenv/bin/activate

# Launch the Streamlit app
streamlit run app.py
```

The app will open at **http://localhost:8501** in your browser.

---

## How to Use

### Step 1 — (Optional) Ingest a Knowledge Base
Use the **sidebar** to upload PDF or TXT files into a ChromaDB collection. This gives the AI contextual research material to draw from when writing articles.

### Step 2 — Upload Your Content Calendar
Upload a **CSV or Excel** file with at least two columns:
- **Topic** — The article title or subject
- **Keyword** — The primary SEO keyword to target

Example CSV:
```
Topic,Keyword,Search Intent
How to Start a Podcast,start a podcast,Informational
Best Running Shoes 2026,best running shoes,Commercial
```

### Step 3 — Map Columns
Select which columns correspond to **Topic** and **Keyword** using the dropdowns.

### Step 4 — Run the Machine
Click **🚀 Run Content Machine**. For each topic, the pipeline will:
1. Generate research queries
2. Retrieve relevant context from the vector store
3. Generate an **article outline** — then pause for your review

### Step 5 — Review the Outline (HITL)
- **✅ Approve** — Continue to drafting, editing, and export
- **❌ Reject & Regenerate** — Add feedback and get a revised outline

### Step 6 — Collect Exported Articles
Finished articles are saved as `.html` files in the `/exports` folder.

---

## Pipeline Flow

```
Upload Calendar → Query Gen → RAG Retrieval → Outline
                                                  ↓
                                          [Human Review]
                                         ↙           ↘
                                    Approve         Reject + Feedback
                                       ↓                  ↓
                                  Draft Article     Regenerate Outline
                                       ↓
                                  Edit Article
                                       ↓
                                  Export HTML
                                       ↓
                               Next Topic in Queue
```

---

## Contributing

Pull requests are welcome! For major changes, please open an issue first to discuss what you would like to change.

1. Fork the repo
2. Create your feature branch: `git checkout -b feature/your-feature`
3. Commit your changes: `git commit -m 'Add some feature'`
4. Push to the branch: `git push origin feature/your-feature`
5. Open a Pull Request

---

## License

This project is licensed under the **MIT License**. See the [LICENSE](LICENSE) file for details.

---

*Built with ❤️ using LangGraph, LangChain, OpenAI, ChromaDB & Streamlit.*
