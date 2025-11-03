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
    cloud-sql-python-connector \
    pg8000 \
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

# Run Uvicorn directly - minimal, no overhead
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8080", "--log-level", "info"]
