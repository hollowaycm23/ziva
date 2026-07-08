.PHONY: install test lint run docker-up docker-down clean

install:
	pip install -r requirements.txt

test:
	python -m unittest discover tests -v

lint:
	python -m flake8 core/ extensions/ rag/ --max-line-length=150 --count

run:
	python -m uvicorn api.server:app --host 0.0.0.0 --port 8000 --reload

docker-up:
	docker-compose up -d

docker-down:
	docker-compose down

docker-logs:
	docker-compose logs -f

clean:
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete

venv:
	python -m venv venv
