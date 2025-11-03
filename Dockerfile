FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Copy application code first
COPY . .

# Install Python dependencies
# FastAPI + Uvicorn + Database + Async support
RUN pip install --no-cache-dir \
    fastapi==0.104.1 \
    uvicorn[standard]==0.24.0 \
    sqlalchemy==2.0.23 \
    psycopg2-binary==2.9.9 \
    redis==5.0.1 \
    requests==2.31.0 \
    pydantic-settings==2.1.0 \
    pydantic==2.5.0 \
    python-multipart==0.0.6 \
    openai==1.3.5 \
    celery==5.3.4 \
    httpx==0.25.2 \
    google-cloud-secret-manager==2.25.0 \
    feedparser==6.0.10 \
    beautifulsoup4==4.12.2 \
    lxml==4.9.4 \
    python-dotenv==1.0.0 \
    aiohttp \
    alembic \
    simhash

# Expose port 8080 (Cloud Run standard)
EXPOSE 8080

# Run with PORT environment variable (Cloud Run expects this)
# Note: Cloud Run uses TCP probes to check container readiness
# The --access-log flag helps with debugging startup issues
CMD ["sh", "-c", "uvicorn src.main:app --host 0.0.0.0 --port ${PORT:-8080} --log-level info"]
