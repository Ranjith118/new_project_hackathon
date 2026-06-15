FROM python:3.11.9-slim

WORKDIR /app

# Install system dependencies needed by chromadb, sentence-transformers, etc.
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy and install Python dependencies first (for layer caching)
COPY requirements.txt .
RUN pip install --upgrade pip && pip install -r requirements.txt

# Copy the application code
COPY . .

# Expose port (Render sets $PORT automatically)
EXPOSE 8000

# Start the server
CMD uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}
