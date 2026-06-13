import unittest

from security_pipeline.log_parser import parse_line


class LogParserTests(unittest.TestCase):
    def test_failed_password_line_is_parsed(self):
        line = "Jun 12 10:00:00 web01 sshd[1234]: Failed password for root from 203.0.113.10 port 54000 ssh2"
        event = parse_line(line, year=2026)
        self.assertIsNotNone(event)
        assert event is not None
        self.assertEqual(event.username, "root")
        self.assertEqual(event.source_ip, "203.0.113.10")
        self.assertEqual(event.outcome, "failed")
        self.assertEqual(event.auth_method, "password")

    def test_accepted_publickey_line_is_parsed(self):
        line = "Jun 12 10:03:00 web01 sshd[1234]: Accepted publickey for alice from 198.51.100.10 port 55000 ssh2"
        event = parse_line(line, year=2026)
        self.assertIsNotNone(event)
        assert event is not None
        self.assertEqual(event.outcome, "accepted")
        self.assertEqual(event.auth_method, "publickey")


if __name__ == "__main__":
    unittest.main()
