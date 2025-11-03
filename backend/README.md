---
title: Portfolio Backend
emoji: 🚀
---

FastAPI backend for a personal RAG (Retrieval-Augmented Generation) system about you.

What changed (multi-source RAG)

- Previously: only resume.pdf was indexed.
- Now: the RAG indexes everything in backend/data/, including:
  - profile.yaml (canonical facts: education, PU, hobbies, interests, links)
  - qna.yaml (high-signal Q&A pairs)
  - timeline.yaml (chronological events)
  - Markdown notes (e.g., hobbies.md, projects/\*.md with optional frontmatter)
  - resume.pdf (still supported)
- Endpoints to manage the index:
  - POST /api/rag/reindex — rebuilds the vector store from backend/data
  - GET /api/rag/sources — summaries of what is currently indexed

How to “train” it about yourself

1. Fill out data files in backend/data

   - profile.yaml — Add canonical facts. Example:
     name: "Tejas M"
     education:
     - level: "PU"
       institution: "ABC PU College"
       years: "2016–2018"
       interests: ["Distributed systems", "RAG and LLM agents"]
       hobbies: ["Badminton", "Photography", "Chess", "Traveling"]
   - qna.yaml — Short Q&A pairs that you want answered verbatim. Example:
     - q: "Where did Tejas do PU?"
       a: "ABC PU College (2016–2018)."
   - timeline.yaml — Important dates. Example:
     - date: "2022-06"
       event: "Graduated B.Tech (CSE) from XYZ University"
   - Add Markdown notes:
     - hobbies.md (already added)
     - projects/example.md (already added; copy this file and create one per project)
   - Keep resume.pdf for long-form accomplishments.

2. Rebuild the index (no redeploy needed)

   - Start the backend (see Run locally below).
   - Reindex:
     curl -X POST http://localhost:8000/api/rag/reindex
   - Inspect sources:
     curl http://localhost:8000/api/rag/sources

3. Ask questions
   - Chat with your agent:
     curl -X POST http://localhost:8000/api/chat \
      -H "Content-Type: application/json" \
      -d '{"message":"What are your hobbies?","session_id":"demo"}'

How documents are processed

- YAML/JSON:
  - profile-like YAML/JSON is flattened to searchable “facts”.
  - If the YAML is a list of objects with q/a fields, it’s treated as Q&A pairs.
- Markdown:
  - Frontmatter is parsed (between ---). It becomes metadata (title, tags, etc.).
  - Body content is embedded.
- PDF:
  - Text is extracted per page and embedded.
- Chunking:
  - Documents are split into ~800-char chunks with overlap, then embedded (all-MiniLM-L6-v2) into FAISS.
  - Each chunk is prefixed with a short header like:
    Source: profile.yaml (profile)

Answer quality and guardrails

- The agent prompt asks to:
  - Ground answers strictly in retrieved context. If info is missing, it says: "I don't have that info yet."
  - Prefer sources in this order: QnA > profile.yaml > timeline.yaml > resume.pdf > other notes.
  - Keep answers short and natural.
- For best results:
  - Put crisp facts into profile.yaml.
  - Add high-signal Q&A for must-know answers (school/PU, interests, strengths).
  - Use timeline.yaml for dates and milestones.
  - Use Markdown notes for longer narratives (bios, project stories).

Environment and configuration

- .env (loaded in server.py):
  - OPENROUTER_API_KEY=... (required for model calls)
  - OPENROUTER_MODEL=openai/gpt-oss-20b:free (override if needed)
  - CORS_ORIGINS=http://localhost:3000,http://localhost:8000
- Security note:
  - Never commit real API keys. If a key was exposed, rotate it.

Run locally

- From backend/:
  - python -m uvicorn server:app --reload --host 0.0.0.0 --port 8000
- Health check:
  - GET http://localhost:8000/api
  - GET http://localhost:8000/api/rag/sources
- Resume download:
  - GET http://localhost:8000/api/resume

Docker

- The provided Dockerfile runs uvicorn on port 7860 inside the container.
- Build and run (example):
  - docker build -t portfolio-backend .
  - docker run -p 7860:7860 --env-file .env portfolio-backend

FAQ

- I updated profile.yaml, but the agent still answers from the old data?
  - Call POST /api/rag/reindex.
- Can I add new files?
  - Yes, add YAML/JSON/MD/TXT/PDF into backend/data. Reindex afterwards.
- How do I add more projects?
  - Create more files under backend/data/projects/\*.md with frontmatter fields (title, year, tags).

File map

- backend/data/profile.yaml — canonical facts about you
- backend/data/qna.yaml — high-signal Q&A answers
- backend/data/timeline.yaml — dated events
- backend/data/hobbies.md — example markdown note
- backend/data/projects/example.md — example project note
- backend/data/resume.pdf — your resume

Internals (where to look)

- rag/loaders.py — Multi-format loaders and YAML flattening
- rag/init_rag.py — Builds vector store from backend/data, reindex support
- rag/agent.py — Retrieval and LLM calling with guardrails and source preference
- server.py — FastAPI endpoints, including /api/rag/reindex and /api/rag/sources
