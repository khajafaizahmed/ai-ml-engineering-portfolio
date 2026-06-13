.PHONY: setup test offline docker generate

setup:
	python -m pip install -e ".[dev]"

test:
	python -m unittest discover -s tests

offline:
	python -m security_pipeline.offline_demo --input data/sample_auth.log --output alerts.jsonl

generate:
	python -m security_pipeline.generate_logs --output data/sample_auth.log

docker:
	docker compose up --build
