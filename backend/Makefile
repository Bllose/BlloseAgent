.PHONY: install run test lint clean

install:
	pip install -r requirements.txt

run:
	uvicorn bllose_agent.main:app --reload --host 0.0.0.0 --port 8000

test:
	pytest -v

lint:
	ruff check bllose_agent/

clean:
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
