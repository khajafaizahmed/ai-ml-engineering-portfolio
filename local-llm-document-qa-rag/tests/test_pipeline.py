import tempfile
import unittest
from pathlib import Path

from rag_app.pipeline import RAGPipeline


class PipelineTests(unittest.TestCase):
    def test_ingest_and_ask_returns_cited_answer(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            docs = root / "docs"
            store = root / "store"
            docs.mkdir()
            (docs / "architecture.md").write_text(
                "RAG retrieves local chunks before generation. Answers include citations for auditability.",
                encoding="utf-8",
            )
            pipeline = RAGPipeline(store_dir=store, llm_provider="extractive")
            summary = pipeline.ingest(docs, chunk_size=20, overlap=2)
            self.assertEqual(summary["documents"], 1)
            answer = pipeline.ask("How are answers audited?", top_k=1)
            self.assertIn("architecture.md", answer.answer)
            self.assertEqual(answer.used_llm, "extractive-fallback")
            self.assertEqual(len(answer.contexts), 1)


if __name__ == "__main__":
    unittest.main()
