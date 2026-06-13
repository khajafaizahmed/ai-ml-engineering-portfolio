from __future__ import annotations

import hashlib
import re
from typing import Iterable

from .models import Chunk, Document

_WORD_RE = re.compile(r"\S+")


def split_words(text: str) -> list[str]:
    return _WORD_RE.findall(text)


def stable_chunk_id(source: str, index: int, text: str) -> str:
    digest = hashlib.sha1(f"{source}:{index}:{text[:200]}".encode("utf-8")).hexdigest()[:10]
    return f"c{index:04d}-{digest}"


def chunk_document(document: Document, chunk_size: int = 180, overlap: int = 40) -> list[Chunk]:
    """Split a document into overlapping word chunks.

    The overlap preserves context across chunk boundaries while keeping chunk ids stable.
    """
    if chunk_size <= 0:
        raise ValueError("chunk_size must be positive")
    if overlap < 0:
        raise ValueError("overlap must be non-negative")
    if overlap >= chunk_size:
        raise ValueError("overlap must be smaller than chunk_size")

    words = split_words(document.text)
    if not words:
        return []

    chunks: list[Chunk] = []
    start = 0
    index = 0
    while start < len(words):
        end = min(start + chunk_size, len(words))
        text = " ".join(words[start:end])
        chunks.append(
            Chunk(
                chunk_id=stable_chunk_id(document.source, index, text),
                source=document.source,
                text=text,
                start_word=start,
                end_word=end,
                metadata={**document.metadata, "chunk_index": index},
            )
        )
        if end == len(words):
            break
        start = end - overlap
        index += 1
    return chunks


def chunk_documents(documents: Iterable[Document], chunk_size: int = 180, overlap: int = 40) -> list[Chunk]:
    all_chunks: list[Chunk] = []
    for document in documents:
        all_chunks.extend(chunk_document(document, chunk_size=chunk_size, overlap=overlap))
    return all_chunks
