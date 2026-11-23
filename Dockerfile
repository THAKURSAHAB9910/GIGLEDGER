# GIGLEDGER Decoupled Backend Dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Install python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt uvicorn[standard]

# Copy application source
COPY src/ ./src/
COPY sql/ ./sql/
COPY data/ ./data/

# Initialize and seed database
RUN python -m src.analytics.init_db

# Expose port (default 8000)
EXPOSE 8000

ENV PORT=8000
ENV HOST=0.0.0.0

CMD ["sh", "-c", "uvicorn src.api.main:app --host 0.0.0.0 --port ${PORT}"]
