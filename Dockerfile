# Elasticsearch v8 Data Injector
# Multi-stage build for optimized image size

FROM python:3.11-slim as builder

WORKDIR /app

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Create virtual environment
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt


# Production image
FROM python:3.11-slim

LABEL maintainer="Elasticsearch Data Injector"
LABEL description="Continuous data injector for Elasticsearch v8"
LABEL version="1.0.0"

WORKDIR /app

# Copy virtual environment from builder
COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Copy application code
COPY src/ ./src/

# Create non-root user for security
RUN useradd --create-home --shell /bin/bash injector && \
    chown -R injector:injector /app

USER injector

# Environment variables with defaults
ENV ES_HOST="https://elasticsearch:9200" \
    ES_USER="elastic" \
    ES_PASSWORD="changeme" \
    ES_INDEX="injector-data" \
    ES_VERIFY_CERTS="false" \
    BATCH_SIZE="100" \
    INJECTION_INTERVAL="1.0" \
    DATA_TYPE="logs" \
    MAX_RETRIES="5" \
    RETRY_DELAY="5.0" \
    PYTHONUNBUFFERED="1"

# Health check - verify Python and elasticsearch module are working
HEALTHCHECK --interval=30s --timeout=10s --start-period=10s --retries=3 \
    CMD python -c "from elasticsearch import Elasticsearch; print('OK')" || exit 1

# Run the injector
ENTRYPOINT ["python", "-u", "src/injector.py"]
