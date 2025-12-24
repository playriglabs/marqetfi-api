.PHONY: help install dev test lint format clean run docker-up docker-down migrate setup pre-commit cli worker worker-prefork worker-stop worker-kill kill-all beat

help:
	@echo "Available commands:"
	@echo "  install        Install production dependencies"
	@echo "  dev            Install development dependencies"
	@echo "  setup          Setup project (install + pre-commit)"
	@echo "  test           Run tests"
	@echo "  lint           Run linters"
	@echo "  format         Format code"
	@echo "  pre-commit     Run pre-commit on all files"
	@echo "  clean          Clean cache and build files"
	@echo "  run            Run development server"
	@echo "  cli            Run CLI commands (e.g., make cli cmd=init-db)"
	@echo "  worker         Run Celery worker (solo pool, recommended for dev)"
	@echo "  worker-prefork Run Celery worker (prefork pool, for production)"
	@echo "  worker-stop    Gracefully stop Celery workers"
	@echo "  worker-kill    Force kill Celery workers"
	@echo "  kill-all       Force kill all API processes (server, worker, beat)"
	@echo "  beat           Run Celery beat scheduler"
	@echo "  docker-up      Start Docker containers"
	@echo "  docker-down    Stop Docker containers"
	@echo "  migrate        Run database migrations"

install:
	pip install -r requirements.txt

dev:
	pip install -r requirements.txt -r requirements-dev.txt

setup: dev
	pre-commit install
	@echo "✅ Project setup complete!"

test:
	pytest -v --cov=app --cov-report=term --cov-report=html

lint:
	ruff check app/ tests/
	black --check app/ tests/
	isort --check-only app/ tests/
	mypy app/

format:
	black app/ tests/
	isort app/ tests/

pre-commit:
	pre-commit run --all-files

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type d -name ".pytest_cache" -exec rm -rf {} +
	find . -type d -name ".mypy_cache" -exec rm -rf {} +
	find . -type d -name ".ruff_cache" -exec rm -rf {} +
	rm -rf htmlcov/
	rm -rf .coverage

run:
	python run.py

docker-up:
	docker-compose up -d

docker-down:
	docker-compose down

migrate:
	alembic upgrade head

cli:
	python -m app.cli $(cmd)

worker:
	celery -A app.tasks.celery_app worker --loglevel=info --pool=solo

worker-prefork:
	celery -A app.tasks.celery_app worker --loglevel=info --pool=prefork --concurrency=4

beat:
	celery -A app.tasks.celery_app beat --loglevel=info

worker-stop:
	@echo "Stopping Celery workers..."
	@pkill -f "celery.*worker.*app.tasks.celery_app" || true
	@echo "✅ Workers stopped"

worker-kill:
	@echo "Force killing Celery workers..."
	@pkill -9 -f "celery.*worker.*app.tasks.celery_app" || true
	@echo "✅ Workers killed"

kill-all:
	@echo "Killing all MarqetFi API processes..."
	@pkill -9 -f "uvicorn.*app.main:app" || true
	@pkill -9 -f "celery.*app.tasks.celery_app" || true
	@pkill -9 -f "python.*run.py" || true
	@echo "✅ All processes killed"
