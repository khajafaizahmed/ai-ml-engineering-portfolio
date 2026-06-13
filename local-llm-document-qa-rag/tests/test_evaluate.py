import unittest

from rag_app.evaluate import lexical_hallucination_rate


class EvaluateTests(unittest.TestCase):
    def test_lexical_hallucination_rate_detects_unsupported_sentence(self):
        context = "The system uses citations and retrieved chunks for grounded answers."
        answer = "The system uses citations. It also predicts tomorrow's weather."
        rate = lexical_hallucination_rate(answer, context)
        self.assertGreater(rate, 0.0)


if __name__ == "__main__":
    unittest.main()
