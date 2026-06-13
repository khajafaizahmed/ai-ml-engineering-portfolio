# Evaluation Guide

A RAG system should be evaluated on retrieval and answer quality. Retrieval relevance checks whether the expected source documents appear in the top-k chunks. Answer faithfulness checks whether the generated response is supported by the retrieved context. Hallucination rate estimates the fraction of answer sentences that do not have enough lexical support in the context.

The evaluation harness in this project reads a JSONL file with questions, expected sources, and expected keywords. It runs the same ingestion and question-answering path used by the CLI and API. The output report includes mean retrieval relevance, mean answer keyword coverage, and an approximate hallucination rate.

Chunk size and overlap affect all metrics. Small chunks improve precise retrieval but can omit useful context. Large chunks preserve more context but may dilute similarity scores. A reranking step can be added after retrieval to reorder candidate chunks before generation.
