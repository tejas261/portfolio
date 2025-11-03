---
title: Portfolio Backend
emoji: 🚀
colorFrom: indigo
colorTo: purple
sdk: docker
pinned: false
---

FastAPI backend for a personal RAG (Retrieval-Augmented Generation) system.

Space type: Docker
- This Space uses a custom Dockerfile to run a FastAPI server with Uvicorn.
- Ensure the app listens on the port provided by the environment variable PORT.
- Default port in this repo is 7860, but the Dockerfile is set up for Spaces.

Run locally (without Docker)
- cd backend
- python -m uvicorn server:app --reload --host 0.0.0.0 --port 8000

Endpoints
- GET /              — simple OK
- GET /api           — health check
- POST /api/chat     — chat with the portfolio agent
- POST /api/rag/reindex — rebuilds vector store from backend/data
- GET /api/rag/sources — summaries of indexed sources
- GET /api/resume    — download the resume.pdf

Notes for Hugging Face Spaces
- This README frontmatter configures the Space (sdk: docker). If you saw “configuration error Missing configuration in README Base README.md template…”, it means the README lacked the required frontmatter. This file fixes that.
- The Dockerfile exposes and runs the server on port 7860. Hugging Face Spaces provides the PORT environment variable at runtime; ensure the server binds to 0.0.0.0 and uses that port if set.

Troubleshooting
- If you still see a configuration error, verify:
  1) This README.md is in the root of the Space repo.
  2) The YAML frontmatter (the block at the top between ---) is present and valid.
  3) The Docker build completes successfully and the container starts listening on $PORT.
- Check Space logs for details.
