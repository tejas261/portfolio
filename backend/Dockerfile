# Dockerfile
FROM python:3.11-slim

# System deps (faiss-cpu wheels usually work, but build tools are handy)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
  && rm -rf /var/lib/apt/lists/*

# Set workdir to the backend folder inside the image
WORKDIR /app

# Writable caches
ENV HF_HOME=/app/.cache/huggingface \
    TRANSFORMERS_CACHE=/app/.cache/hf \
    SENTENCE_TRANSFORMERS_HOME=/app/.cache/st \
    XDG_CACHE_HOME=/app/.cache
RUN mkdir -p /app/.cache/hf /app/.cache/st && chmod -R 777 /app/.cache

# Install deps
COPY requirements.txt ./requirements.txt
RUN pip install --no-cache-dir torch==2.4.1
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend code
COPY . .

RUN mkdir -p /app/rag/vector_store && chmod -R 777 /app/rag/vector_store

# Pre-fetch the model (correct syntax)
RUN python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2'); print('Pre-fetched all-MiniLM-L6-v2 into cache')"

ENV PYTHONPATH=/app
ENV PORT=7860
EXPOSE 7860
CMD ["uvicorn", "server:app", "--host", "0.0.0.0", "--port", "7860"]