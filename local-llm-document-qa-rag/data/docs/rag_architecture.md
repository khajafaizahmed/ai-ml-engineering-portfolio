# RAG Architecture Notes

A retrieval-augmented generation system separates document lookup from text generation. The ingestion step loads local technical documents, splits them into overlapping chunks, embeds each chunk, and stores the chunk text plus metadata in a vector index. The question-answering step embeds the user question, retrieves the highest scoring chunks, and passes only those snippets to the answer generator.

Grounding is enforced by prompt design and response validation. The answer generator is instructed to use the retrieved context only, and every factual sentence must include a citation such as `[rag_architecture.md#c0000]`. Citations let a reviewer inspect which chunk supported a statement. If the local LLM does not provide citations, the application appends the retrieved source identifiers so the answer remains auditable.

The portable demo uses JSON persistence and hashing embeddings because they run without external services. In a full local setup, sentence-transformer embeddings provide stronger semantic retrieval, while ChromaDB stores vectors, chunk metadata, and document identifiers in a persistent collection. Ollama supplies the local LLM so no document content leaves the machine.
