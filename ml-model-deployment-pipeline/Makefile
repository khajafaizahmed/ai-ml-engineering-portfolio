.PHONY: setup train test api docker

setup:
	python -m pip install -e ".[dev]"

train:
	python -m ml_service.train --model-dir models --versions v1 v2 --epochs 5

test:
	python -m pytest

api:
	uvicorn ml_service.app:app --reload --port 8080

docker:
	docker compose up --build
