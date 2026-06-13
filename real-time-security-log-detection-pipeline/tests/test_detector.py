import unittest
from datetime import datetime, timedelta

from security_pipeline.detector import DetectionConfig, DetectionEngine
from security_pipeline.models import AuthEvent


def event_at(offset: int, username: str = "root", ip: str = "203.0.113.10", outcome: str = "failed") -> AuthEvent:
    return AuthEvent(
        timestamp=datetime(2026, 6, 12, 10, 0, 0) + timedelta(seconds=offset),
        host="web01",
        process="sshd",
        username=username,
        source_ip=ip,
        outcome=outcome,
        auth_method="password",
        raw="",
    )


class DetectionEngineTests(unittest.TestCase):
    def test_brute_force_alert_after_threshold(self):
        engine = DetectionEngine(DetectionConfig(brute_force_threshold=3, brute_force_window_seconds=60))
        alerts = []
        for offset in [0, 10, 20]:
            alerts.extend(engine.process(event_at(offset)))
        self.assertEqual(len(alerts), 1)
        self.assertEqual(alerts[0].alert_type, "BRUTE_FORCE")

    def test_new_device_alert_after_baseline_success(self):
        engine = DetectionEngine()
        first = event_at(0, username="alice", ip="198.51.100.10", outcome="accepted")
        second = event_at(30, username="alice", ip="198.51.100.44", outcome="accepted")
        self.assertEqual(engine.process(first), [])
        alerts = engine.process(second)
        self.assertTrue(any(alert.alert_type == "NEW_DEVICE_LOGIN" for alert in alerts))

    def test_success_velocity_alert_for_distinct_ips(self):
        engine = DetectionEngine(DetectionConfig(velocity_distinct_ip_threshold=3, velocity_window_seconds=120))
        alerts = []
        for offset, ip in [(0, "198.51.100.1"), (30, "198.51.100.2"), (60, "198.51.100.3")]:
            alerts.extend(engine.process(event_at(offset, username="alice", ip=ip, outcome="accepted")))
        self.assertTrue(any(alert.alert_type == "SUCCESS_VELOCITY" for alert in alerts))


if __name__ == "__main__":
    unittest.main()
