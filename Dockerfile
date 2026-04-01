# ============================================================
# Dockerfile for HaUI Agentic RAG Chatbot
# Optimized for Render deployment
# ============================================================
FROM python:3.11-slim AS base

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    TRANSFORMERS_CACHE=/app/.cache/huggingface \
    HF_HOME=/app/.cache/huggingface \
    SENTENCE_TRANSFORMERS_HOME=/app/.cache/sentence-transformers

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    git \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements first for better Docker layer caching
COPY requirements-deploy.txt .

# Install Python dependencies
RUN pip install --upgrade pip && \
    pip install -r requirements-deploy.txt

# Pre-download Vietnamese embedding model during build (cached in image)
RUN python -c "\
from sentence_transformers import SentenceTransformer; \
print('Downloading Vietnamese embedding model...'); \
model = SentenceTransformer('dangvantuan/vietnamese-embedding'); \
print('Model downloaded successfully!'); \
"

# Copy application code
COPY . .

# Create vector_db directory
RUN mkdir -p /app/vector_db

# Expose port (Render provides PORT env var)
EXPOSE 10000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=120s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:10000/health', timeout=5)" || exit 1

# Start the unified server
CMD ["python", "server.py"]
