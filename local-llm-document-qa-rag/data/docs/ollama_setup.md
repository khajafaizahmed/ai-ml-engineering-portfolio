# Ollama Local LLM Setup

Ollama runs a local language model behind an HTTP API. After installing Ollama, pull a model such as `llama3.1:8b` and start the server. The RAG application calls `/api/generate` with a prompt that contains the top retrieved snippets and the user question.

The project is intentionally safe to run without Ollama. When the Ollama API is not reachable, the answer generator uses an extractive fallback that selects the most relevant sentences from retrieved chunks. This fallback makes tests deterministic and keeps the pipeline functional on laptops that do not have enough memory for a large model.
