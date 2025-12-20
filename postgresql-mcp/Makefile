.PHONY: install run-server run-client test clean docker-build docker-up docker-down init-db help

help:
	@echo "Available targets:"
	@echo "  setup         - Complete database setup in one command (recommended)"
	@echo "  install       - Install dependencies"
	@echo "  run-server    - Run the MCP server"
	@echo "  run-client    - Run example client queries"
	@echo "  test          - Run tests"
	@echo "  clean         - Clean Python cache files"
	@echo "  docker-build  - Build Docker image"
	@echo "  docker-up     - Start services with Docker Compose"
	@echo "  docker-down   - Stop Docker Compose services"
	@echo "  init-db       - Initialize database and user only (use 'setup' for full setup)"

setup:
	@./setup.sh

install:
	pip install -e .

run-server:
	python mcp_server.py

run-client:
	@echo "Example: python mcp_client.py query 'How many tables are in the database?'"

test:
	pytest

clean:
	find . -type d -name __pycache__ -exec rm -r {} +
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete

build:
	docker build -t postgresql-mcp .

up:
	docker-compose up -d

down:
	docker-compose down

init-db:
	@echo "Initializing database only (PostgreSQL must be running)"
	@python scripts/init_db.py

test-connection:
	@python scripts/test_connection.py

