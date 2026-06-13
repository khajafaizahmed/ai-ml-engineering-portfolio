import tempfile
import unittest
from pathlib import Path

from security_pipeline.offline_demo import run_offline


class OfflineDemoTests(unittest.TestCase):
    def test_offline_demo_emits_alerts(self):
        sample = Path(__file__).resolve().parents[1] / "data" / "sample_auth.log"
        with tempfile.TemporaryDirectory() as tmpdir:
            output = Path(tmpdir) / "alerts.jsonl"
            summary = run_offline(sample, output)
            self.assertGreaterEqual(summary["events_processed"], 8)
            self.assertGreaterEqual(summary["alerts_emitted"], 3)
            text = output.read_text(encoding="utf-8")
            self.assertIn("BRUTE_FORCE", text)


if __name__ == "__main__":
    unittest.main()
