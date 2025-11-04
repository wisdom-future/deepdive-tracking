FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    postgresql-client \
    git \
    && rm -rf /var/lib/apt/lists/*

# Copy application code first
COPY . .

# Install Python dependencies from pyproject.toml
RUN pip install --no-cache-dir \
    ".[ai]"

# Install Google Cloud dependencies
RUN pip install --no-cache-dir \
    google-cloud-secret-manager \
    cloud-sql-python-connector \
    pg8000

# Expose port 8080 (Cloud Run standard)
EXPOSE 8080

# Run Uvicorn directly - minimal, no overhead
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8080", "--log-level", "info"]
