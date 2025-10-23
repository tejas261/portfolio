# Dockerfile
FROM python:3.11-slim

# System deps (faiss-cpu wheels usually work, but build tools are handy)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
  && rm -rf /var/lib/apt/lists/*

# Set workdir to the backend folder inside the image
WORKDIR /app

# Install Python deps first (better caching)
COPY requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend code
COPY . .

# Ensure Python finds the backend package paths
ENV PYTHONPATH=/app


# Spaces Docker expects an app listening on port 7860 by default, but we also honor $PORT
ENV PORT=7860
EXPOSE 7860

# Run FastAPI with uvicorn
CMD ["uvicorn", "server:app", "--host", "0.0.0.0", "--port", "7860"]