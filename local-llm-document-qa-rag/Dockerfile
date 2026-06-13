FROM python:3.11-slim
WORKDIR /app
COPY pyproject.toml README.md ./
COPY src ./src
COPY data ./data
RUN pip install --no-cache-dir -e .
ENV RAG_STORE_DIR=/app/.rag_store RAG_DOC_DIR=/app/data/docs
RUN python -m rag_app.cli ingest --docs /app/data/docs --store /app/.rag_store
EXPOSE 8000
CMD ["uvicorn", "rag_app.api:app", "--host", "0.0.0.0", "--port", "8000"]
