import unittest

from rag_app.chunker import chunk_document
from rag_app.models import Document


class ChunkerTests(unittest.TestCase):
    def test_chunking_uses_overlap_and_stable_citations(self):
        text = " ".join(f"word{i}" for i in range(25))
        document = Document(source="doc.md", text=text, metadata={})
        chunks = chunk_document(document, chunk_size=10, overlap=3)
        self.assertEqual(len(chunks), 4)
        self.assertEqual(chunks[0].start_word, 0)
        self.assertEqual(chunks[1].start_word, 7)
        self.assertTrue(chunks[0].citation().startswith("doc.md#c0000"))

    def test_invalid_overlap_is_rejected(self):
        document = Document(source="doc.md", text="hello world", metadata={})
        with self.assertRaises(ValueError):
            chunk_document(document, chunk_size=10, overlap=10)


if __name__ == "__main__":
    unittest.main()
