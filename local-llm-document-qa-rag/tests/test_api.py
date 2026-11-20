import os
import tempfile
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
os.environ["RAG_DOC_DIR"] = str(PROJECT_ROOT / "data" / "docs")
os.environ["RAG_STORE_DIR"] = tempfile.mkdtemp(prefix="rag_api_test_")

from fastapi.testclient import TestClient  # noqa: E402

from rag_app.api import app  # noqa: E402


class ApiTests(unittest.TestCase):
    def setUp(self) -> None:
        self.client = TestClient(app)

    def test_ingest_then_ask_returns_cited_answer(self) -> None:
        ingest = self.client.post("/ingest", json={"docs_path": os.environ["RAG_DOC_DIR"]})
        self.assertEqual(ingest.status_code, 200)
        self.assertGreater(ingest.json()["chunks"], 0)

        answer = self.client.post("/ask", json={"question": "How are answers grounded?", "top_k": 3})
        self.assertEqual(answer.status_code, 200)
        self.assertTrue(answer.json()["citations"])

    def test_ingest_rejects_paths_outside_doc_dir(self) -> None:
        for path in ["/etc", str(PROJECT_ROOT), os.environ["RAG_DOC_DIR"] + "/../../src"]:
            response = self.client.post("/ingest", json={"docs_path": path})
            self.assertEqual(response.status_code, 400, path)


if __name__ == "__main__":
    unittest.main()
