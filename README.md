# Interview AI
### AI-Powered Role-Based Candidate Screening System

> **Assignment**: AI/ML & Backend Engineering Intern  
> **Stack**: FastAPI · React 18 · FAISS · sentence-transformers · OpenAI GPT-3.5

---

## Overview

A fully functional end-to-end technical interview simulation platform powered by a **Retrieval-Augmented Generation (RAG)** pipeline. The system parses candidate resumes, retrieves domain-specific textbook knowledge via FAISS vector search, and dynamically generates adaptive interview questions scored in real time.

---

## System Architecture

```
┌──────────────────────────────────────────────────────┐
│           Frontend  (React 18 + Vite + Tailwind)     │
│  UploadScreen → InterviewScreen → SummaryScreen      │
└────────────────────────┬─────────────────────────────┘
                         │ HTTP (Axios)
┌────────────────────────▼─────────────────────────────┐
│              Backend  (FastAPI + SQLAlchemy)          │
│  /sessions  /resume  /question  /answer  /summary    │
└──────┬─────────────────┬────────────────┬────────────┘
       │                 │                │
  SQLite DB         FAISS Index      OpenAI API
  (sessions,       (ML textbook      (GPT-3.5-turbo
   Q&A history)     embeddings)       questions + scoring)
```

### RAG Pipeline
1. **Ingest** — PyMuPDF extracts text from ML textbook PDFs  
2. **Embed** — `sentence-transformers/all-MiniLM-L6-v2` creates dense vectors  
3. **Index** — FAISS stores and retrieves top-k semantically similar chunks  
4. **Generate** — GPT-3.5-turbo produces role/difficulty-calibrated questions grounded in retrieved context  
5. **Score** — GPT evaluates answers against source chunks (fallback: keyword-overlap heuristic)

---

## Features

| Feature | Details |
|---|---|
| **Resume Parsing** | PyMuPDF extracts skills, technologies, experience level |
| **Role-Based Sessions** | AI/ML Engineer · Backend Engineer · Data Scientist |
| **RAG Grounded Questions** | FAISS retrieval → GPT-3.5-turbo generation |
| **Adaptive Difficulty** | Junior / Mid / Senior calibration from resume |
| **3 Interviewer Personas** | Professional Mentor · Stress Interviewer · Academic Professor |
| **Real-time Scoring** | 1–5 score + feedback per answer |
| **Voice TTS/STT** | Web Speech API for question readout & dictation |
| **Session Recovery** | Resume interrupted sessions by UUID |
| **Evaluation Report** | SVG score gauge, per-question breakdown, topic coverage |
| **Offline Fallback** | Works without OpenAI via keyword scoring + template questions |

---

## Quick Start

### Prerequisites
- Python 3.10+
- Node.js 18+
- OpenAI API key (optional — local fallback available)

### 1. Clone & Setup Environment
```bash
git clone <repo-url>
cd pgagi-interview
```

Create `.env` at project root:
```env
OPENAI_API_KEY=sk-...       # optional — system runs without it
FAISS_INDEX_PATH=./faiss_index/index.faiss
CHUNKS_PATH=./faiss_index/chunks.json
MAX_QUESTIONS_PER_SESSION=5
```

### 2. Backend
```bash
cd backend
pip install -r requirements.txt

# Build the knowledge base (ML textbooks → FAISS index)
python create_sample_kb.py       # generates sample ML PDF
python rag/embedder.py           # embeds and indexes it

# Start API server
python -m uvicorn main:app --reload --port 8000
```

### 3. Frontend
```bash
cd frontend
npm install
npm run dev
```

Open **http://localhost:5173**

---

## API Reference

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/sessions` | Create interview session |
| `POST` | `/sessions/{id}/resume` | Upload & parse resume PDF |
| `POST` | `/sessions/{id}/mock-resume` | Use demo profile (no PDF needed) |
| `GET` | `/sessions/{id}/question` | Fetch next RAG-grounded question |
| `POST` | `/sessions/{id}/answer` | Submit answer → get score + feedback |
| `POST` | `/sessions/{id}/complete` | Mark session complete |
| `GET` | `/sessions/{id}/summary` | Get full evaluation report |
| `GET` | `/sessions/{id}` | Recover/inspect session state |

Interactive docs: **http://localhost:8000/docs**

---

## Project Structure

```
pgagi-interview/
├── backend/
│   ├── main.py               # FastAPI app entry
│   ├── db.py                 # SQLAlchemy engine + session
│   ├── models/               # SQLAlchemy ORM models
│   ├── routers/
│   │   ├── sessions.py       # Session creation, resume upload
│   │   └── interview.py      # Question, answer, summary endpoints
│   ├── services/
│   │   └── session_service.py # Orchestration logic
│   ├── rag/
│   │   ├── embedder.py       # PDF ingestion → FAISS index
│   │   ├── retriever.py      # Semantic similarity search
│   │   └── generator.py      # GPT question gen + answer scoring
│   ├── knowledge_base/       # ML textbook PDFs go here
│   ├── faiss_index/          # Auto-generated vector index
│   └── requirements.txt
└── frontend/
    ├── src/
    │   ├── App.jsx            # Shell, routing, settings modal
    │   ├── index.css          # Design system (professional light UI)
    │   ├── api/client.js      # Axios API client
    │   └── components/
    │       ├── UploadScreen.jsx   # Role selection, resume upload
    │       ├── InterviewScreen.jsx # Live Q&A with TTS/STT
    │       └── SummaryScreen.jsx   # Evaluation dashboard
    ├── tailwind.config.js
    └── vite.config.js
```

---

## Design Decisions

- **SQLite over Postgres** — zero-config, fits assignment scope, easily swappable  
- **FAISS (CPU)** — no cloud dependency, fast local approximate nearest neighbor search  
- **`all-MiniLM-L6-v2`** — 80MB model, strong semantic accuracy, runs on CPU in <1s  
- **Local fallbacks** — system is fully functional without OpenAI (template questions + keyword scoring)  
- **Session UUID recovery** — enables multi-tab usage and interrupted session resumption  

---

## Assignment Compliance

- ✅ RAG pipeline (FAISS + sentence-transformers + GPT)
- ✅ Resume parsing (PyMuPDF skills/tech/level extraction)
- ✅ Role-based adaptive questioning
- ✅ Real-time answer scoring (1–5) with feedback
- ✅ REST API with documented endpoints
- ✅ Frontend with full interview UX
- ✅ Session persistence & recovery
- ✅ Evaluation report with analytics
- ✅ Works offline (no mandatory API key)

---

*Built for AI/ML & Backend Engineering Intern Assignment*
