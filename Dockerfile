FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Copy application code first
COPY . .

# Install Python dependencies from requirements.txt or setup.py
# Try requirements.txt first, fallback to setup.py
RUN if [ -f requirements.txt ]; then \
        pip install --no-cache-dir -r requirements.txt; \
    elif [ -f setup.py ]; then \
        pip install --no-cache-dir -e .; \
    else \
        pip install --no-cache-dir flask uvicorn sqlalchemy psycopg2-binary redis requests; \
    fi

# Expose port 8080 (Cloud Run standard)
EXPOSE 8080

# Run with PORT environment variable (Cloud Run expects this)
# Note: Cloud Run uses TCP probes to check container readiness
# The --access-log flag helps with debugging startup issues
CMD ["sh", "-c", "uvicorn src.main:app --host 0.0.0.0 --port ${PORT:-8080} --log-level info"]
