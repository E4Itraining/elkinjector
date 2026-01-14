# ElkInjector Dockerfile
# Multi-stage build for optimized image size

# Stage 1: Builder
FROM python:3.11-slim as builder

WORKDIR /app

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy project files
COPY pyproject.toml .
COPY elkinjector/ elkinjector/

# Create wheel
RUN pip install --no-cache-dir build \
    && python -m build --wheel --outdir /app/dist

# Stage 2: Runtime
FROM python:3.11-slim as runtime

LABEL maintainer="E4Itraining"
LABEL description="Data injection tool for Elasticsearch"
LABEL version="1.0.0"

# Create non-root user
RUN useradd --create-home --shell /bin/bash elkinjector

WORKDIR /app

# Install the wheel from builder stage
COPY --from=builder /app/dist/*.whl /app/
RUN pip install --no-cache-dir /app/*.whl \
    && rm /app/*.whl

# Copy entrypoint script
COPY docker-entrypoint.sh /usr/local/bin/
RUN chmod +x /usr/local/bin/docker-entrypoint.sh

# Copy example config
COPY config.example.yaml /app/config.example.yaml

# Switch to non-root user
USER elkinjector

# Set environment variables
ENV ES_HOST=elasticsearch \
    ES_PORT=9200 \
    ES_SCHEME=http \
    INJECTION_BATCH_SIZE=1000 \
    INJECTION_INTERVAL=1.0

ENTRYPOINT ["docker-entrypoint.sh"]
CMD ["elkinjector", "--help"]
