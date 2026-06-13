FROM python:3.11-slim
WORKDIR /app
COPY pyproject.toml README.md ./
COPY src ./src
COPY models ./models
RUN pip install --no-cache-dir -e .
ENV MODEL_DIR=/app/models
EXPOSE 8080
CMD ["uvicorn", "ml_service.app:app", "--host", "0.0.0.0", "--port", "8080"]
