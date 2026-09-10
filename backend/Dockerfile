FROM python:3.11-slim

WORKDIR /app

# Install system dependencies:
#   tesseract-ocr  — required by pytesseract
#   libgomp1       — required by opencv-python-headless
#   libglib2.0-0, libsm6, libxrender1, libxext6 — cv2 runtime libs
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        tesseract-ocr \
        libgomp1 \
        libglib2.0-0 \
        libsm6 \
        libxrender1 \
        libxext6 && \
    rm -rf /var/lib/apt/lists/*

# Copy and install Python dependencies first (maximises layer cache)
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend source code
COPY backend/ .

# Copy shared modules that backend imports at runtime
COPY ai_engine/ ./ai_engine/
COPY rules/ ./rules/

ENV PYTHONUNBUFFERED=1

# Render injects $PORT at runtime; fall back to 8000 locally
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
