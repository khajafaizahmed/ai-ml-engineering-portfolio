from fastapi.testclient import TestClient

from ml_service.app import app


def test_health_and_prediction_endpoints():
    client = TestClient(app)
    health = client.get("/health")
    assert health.status_code == 200
    assert health.json()["status"] == "ok"

    response = client.post(
        "/predict",
        json={
            "account_age_days": 45,
            "failed_login_count": 7,
            "transaction_amount": 420.0,
            "device_trust_score": 0.22,
        },
    )
    assert response.status_code == 200
    payload = response.json()
    assert 0.0 <= payload["probability"] <= 1.0
    assert payload["label"] in (0, 1)
    assert payload["model_version"]
