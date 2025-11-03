---
title: "Example Project — Portfolio RAG Agent"
year: 2024
type: "project"
tags: ["RAG", "FastAPI", "LangChain", "FAISS"]
role: "Full‑stack Engineer"
impact: "Improved personal assistant accuracy by expanding knowledge beyond resume."
---

Built a Retrieval‑Augmented Generation (RAG) agent for my portfolio.
Key parts:

- Data ingestion of multiple sources (resume.pdf, profile.yaml, qna.yaml, timeline.yaml, markdown notes)
- Local embeddings via sentence‑transformers (all‑MiniLM‑L6‑v2) and FAISS store
- FastAPI endpoints for chat, reindex, and source summaries
- Prompts tuned to prefer high‑signal sources (QnA, profile) and avoid hallucinations

Highlights:

- Implemented modular loaders for YAML/JSON/MD/PDF with rich metadata
- Added reindex endpoint to update knowledge without redeploy
- Prefixed chunks with `Source: <file> (type)` to improve grounding and citations
