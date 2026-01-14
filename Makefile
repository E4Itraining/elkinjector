.PHONY: help build up down logs inject-logs inject-metrics inject-all inject-continuous check clean restart

# Default target
help:
	@echo "ElkInjector Docker Commands"
	@echo ""
	@echo "Usage: make [target]"
	@echo ""
	@echo "Infrastructure:"
	@echo "  build              Build Docker images"
	@echo "  up                 Start Elasticsearch and Kibana"
	@echo "  down               Stop all containers"
	@echo "  restart            Restart all containers"
	@echo "  logs               Show container logs"
	@echo ""
	@echo "Injection:"
	@echo "  inject-logs        Inject 10,000 log documents"
	@echo "  inject-metrics     Inject 10,000 metric documents"
	@echo "  inject-all         Inject 10,000 logs + metrics"
	@echo "  inject-continuous  Start continuous injection"
	@echo "  inject-custom      Inject with custom args (use ARGS=)"
	@echo ""
	@echo "Management:"
	@echo "  check              Check Elasticsearch connection"
	@echo "  clean              Delete all ElkInjector indices"
	@echo "  shell              Open shell in ElkInjector container"
	@echo ""
	@echo "Examples:"
	@echo "  make up                           # Start ES + Kibana"
	@echo "  make inject-logs                  # Inject logs"
	@echo "  make inject-custom ARGS='-n 5000' # Custom injection"

# Build Docker images
build:
	docker compose build

# Start Elasticsearch and Kibana
up:
	docker compose up -d elasticsearch kibana
	@echo ""
	@echo "Elasticsearch: http://localhost:9200"
	@echo "Kibana:        http://localhost:5601"

# Stop all containers
down:
	docker compose down

# Restart
restart: down up

# Show logs
logs:
	docker compose logs -f

# Inject logs only
inject-logs: build
	docker compose run --rm elkinjector elkinjector inject --logs --no-metrics --no-json -n 10000

# Inject metrics only
inject-metrics: build
	docker compose run --rm elkinjector elkinjector inject --no-logs --metrics --no-json -n 10000

# Inject all types
inject-all: build
	docker compose run --rm elkinjector elkinjector inject --logs --metrics -n 10000

# Continuous injection
inject-continuous: build
	docker compose run --rm elkinjector elkinjector inject --continuous --logs --metrics -b 500 -i 0.5

# Custom injection (use ARGS= to pass arguments)
inject-custom: build
	docker compose run --rm elkinjector elkinjector inject $(ARGS)

# Check connection
check: build
	docker compose run --rm elkinjector elkinjector check

# Clean indices
clean: build
	docker compose run --rm elkinjector elkinjector clean --force

# Open shell
shell: build
	docker compose run --rm elkinjector /bin/bash

# Show placeholders
placeholders: build
	docker compose run --rm elkinjector elkinjector show-placeholders

# Generate config
init-config: build
	docker compose run --rm -v $(PWD):/output elkinjector elkinjector init-config -o /output/elkinjector.yaml
