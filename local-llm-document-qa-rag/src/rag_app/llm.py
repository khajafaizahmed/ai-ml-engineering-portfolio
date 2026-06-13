from __future__ import annotations

import json
import re
import textwrap
import urllib.error
import urllib.request
from dataclasses import dataclass

from .models import SearchResult


@dataclass(frozen=True)
class GeneratedText:
    text: str
    provider: str


class OllamaClient:
    """Minimal local Ollama generate API client using the Python standard library."""

    def __init__(self, base_url: str = "http://localhost:11434", model: str = "llama3.1:8b", timeout_seconds: int = 45) -> None:
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.timeout_seconds = timeout_seconds

    def generate(self, prompt: str) -> str:
        payload = json.dumps({"model": self.model, "prompt": prompt, "stream": False}).encode("utf-8")
        request = urllib.request.Request(
            f"{self.base_url}/api/generate",
            data=payload,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urllib.request.urlopen(request, timeout=self.timeout_seconds) as response:
                data = json.loads(response.read().decode("utf-8"))
        except (urllib.error.URLError, TimeoutError) as exc:
            raise RuntimeError(f"Ollama request failed: {exc}") from exc
        return str(data.get("response", "")).strip()


class ExtractiveAnswerer:
    """Deterministic fallback that answers from the highest scoring contexts."""

    provider = "extractive-fallback"

    def answer(self, question: str, contexts: list[SearchResult], max_sentences: int = 4) -> str:
        if not contexts:
            return "I could not find relevant local context for this question."

        question_terms = {term.lower() for term in re.findall(r"[A-Za-z][A-Za-z0-9_\-]+", question) if len(term) > 2}
        candidate_sentences: list[tuple[float, str, str]] = []
        for result in contexts:
            citation = result.chunk.citation()
            sentences = re.split(r"(?<=[.!?])\s+", result.chunk.text)
            for sentence in sentences:
                clean = sentence.strip()
                if not clean:
                    continue
                terms = {term.lower() for term in re.findall(r"[A-Za-z][A-Za-z0-9_\-]+", clean)}
                overlap = len(question_terms & terms)
                score = result.score + overlap * 0.05
                candidate_sentences.append((score, clean, citation))

        candidate_sentences.sort(key=lambda item: item[0], reverse=True)
        selected: list[str] = []
        seen: set[str] = set()
        for _, sentence, citation in candidate_sentences:
            normalized = sentence.lower()
            if normalized in seen:
                continue
            seen.add(normalized)
            selected.append(f"{sentence} [{citation}]")
            if len(selected) >= max_sentences:
                break
        return " ".join(selected)


class AnswerGenerator:
    """Generate grounded answers using Ollama with a deterministic fallback."""

    def __init__(self, provider: str = "auto", model: str = "llama3.1:8b", base_url: str = "http://localhost:11434") -> None:
        self.provider = provider
        self.ollama = OllamaClient(base_url=base_url, model=model)
        self.extractive = ExtractiveAnswerer()

    def build_prompt(self, question: str, contexts: list[SearchResult]) -> str:
        context_block = "\n\n".join(
            f"[{result.chunk.citation()}]\n{result.chunk.text}" for result in contexts
        )
        return textwrap.dedent(
            f"""
            You are a local RAG assistant. Answer the question using only the context snippets below.
            Every factual sentence must include a citation in square brackets using the source id exactly as given.
            If the context is insufficient, say what is missing instead of guessing.

            Context:
            {context_block}

            Question: {question}
            Answer:
            """
        ).strip()

    def generate(self, question: str, contexts: list[SearchResult]) -> GeneratedText:
        normalized = self.provider.lower().strip()
        if normalized in {"ollama", "auto"}:
            try:
                text = self.ollama.generate(self.build_prompt(question, contexts))
                if text:
                    text = ensure_citations(text, [result.chunk.citation() for result in contexts])
                    return GeneratedText(text=text, provider="ollama")
            except RuntimeError:
                if normalized == "ollama":
                    raise
        return GeneratedText(text=self.extractive.answer(question, contexts), provider=self.extractive.provider)


def ensure_citations(answer: str, citations: list[str]) -> str:
    """Append sources when an LLM forgets citation formatting."""
    if not citations:
        return answer
    if any(f"[{citation}]" in answer for citation in citations):
        return answer
    compact_sources = ", ".join(f"[{citation}]" for citation in citations[:4])
    return f"{answer}\n\nSources: {compact_sources}"
