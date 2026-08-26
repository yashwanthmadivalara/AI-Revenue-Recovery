.PHONY: install run test lint format demo docker-up docker-down clean

install:
	pip install -r requirements.txt
	pip install pytest pytest-asyncio pytest-cov black ruff

run:
	uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

test:
	pytest -v --cov=app tests/

lint:
	ruff check .
	black --check .

format:
	ruff check --fix .
	black .

demo:
	python -m app.cli.demo --scenarios all

docker-up:
	docker-compose up --build -d

docker-down:
	docker-compose down

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	rm -rf .pytest_cache htmlcov .coverage revenue_recovery.db
