FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    postgresql-client \
    wget \
    && rm -rf /var/lib/apt/lists/*

# Install Cloud SQL Proxy
RUN wget https://dl.google.com/cloudsql/cloud_sql_proxy.linux.amd64 -O /usr/local/bin/cloud-sql-proxy && \
    chmod +x /usr/local/bin/cloud-sql-proxy

# Copy application code first
COPY . .

# Install Python dependencies
RUN pip install --no-cache-dir \
    fastapi \
    uvicorn[standard] \
    sqlalchemy \
    psycopg2-binary \
    redis \
    requests \
    pydantic-settings \
    pydantic \
    python-multipart \
    openai \
    celery \
    httpx \
    google-cloud-secret-manager \
    feedparser \
    beautifulsoup4 \
    lxml \
    python-dotenv \
    aiohttp \
    alembic \
    simhash \
    pytz \
    loguru \
    python-dateutil \
    langchain \
    numpy \
    scikit-learn

# Expose port 8080 (Cloud Run standard)
EXPOSE 8080

# Run with Cloud SQL Proxy and Uvicorn
# The proxy connects to Cloud SQL while app runs on 8080
# Proxy listens on localhost:5432 for database connections
CMD ["sh", "-c", "cloud-sql-proxy deepdive-engine:asia-east1:deepdive-db --port=5432 & uvicorn src.main:app --host 0.0.0.0 --port ${PORT:-8080} --log-level info"]
