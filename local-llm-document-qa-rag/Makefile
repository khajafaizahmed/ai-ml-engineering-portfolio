.PHONY: setup ingest ask evaluate test api

setup:
	python -m pip install -e ".[dev]"

ingest:
	python -m rag_app.cli ingest --docs data/docs --store .rag_store

ask:
	python -m rag_app.cli ask --question "How does the system avoid hallucinations?" --store .rag_store

evaluate:
	python -m rag_app.evaluate --docs data/docs --store .rag_store --eval-file data/eval/questions.jsonl

test:
	python -m unittest discover -s tests

api:
	uvicorn rag_app.api:app --reload --port 8000
