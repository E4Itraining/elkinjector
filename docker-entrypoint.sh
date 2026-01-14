#!/bin/bash
set -e

# ElkInjector Docker Entrypoint
# Handles waiting for Elasticsearch and running the CLI

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Function to wait for Elasticsearch
wait_for_elasticsearch() {
    local host="${ES_HOST:-elasticsearch}"
    local port="${ES_PORT:-9200}"
    local scheme="${ES_SCHEME:-http}"
    local max_attempts="${ES_WAIT_ATTEMPTS:-30}"
    local wait_interval="${ES_WAIT_INTERVAL:-2}"

    local url="${scheme}://${host}:${port}"
    local attempt=1

    log_info "Waiting for Elasticsearch at ${url}..."

    while [ $attempt -le $max_attempts ]; do
        if curl -s -o /dev/null -w "%{http_code}" "${url}/_cluster/health" | grep -q "200\|401"; then
            log_info "Elasticsearch is ready!"
            return 0
        fi

        log_warn "Attempt $attempt/$max_attempts - Elasticsearch not ready, waiting ${wait_interval}s..."
        sleep $wait_interval
        attempt=$((attempt + 1))
    done

    log_error "Elasticsearch did not become ready in time"
    return 1
}

# Main entrypoint logic
main() {
    # If first argument is 'elkinjector', handle special cases
    if [ "$1" = "elkinjector" ]; then
        shift

        # If inject command, wait for Elasticsearch first
        if [ "$1" = "inject" ] || [ "$1" = "check" ] || [ "$1" = "clean" ]; then
            if [ "${SKIP_ES_WAIT:-false}" != "true" ]; then
                wait_for_elasticsearch || exit 1
            fi
        fi

        # Run elkinjector with remaining arguments
        exec elkinjector "$@"
    fi

    # If command starts with dash, assume it's elkinjector options
    if [ "${1:0:1}" = '-' ]; then
        exec elkinjector "$@"
    fi

    # Otherwise, run the command as-is
    exec "$@"
}

main "$@"
