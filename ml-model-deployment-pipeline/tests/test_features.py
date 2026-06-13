from ml_service.features import FEATURE_NAMES, ordered_features


def test_ordered_features_uses_model_contract_order():
    payload = {
        "transaction_amount": 100.0,
        "device_trust_score": 0.5,
        "failed_login_count": 3,
        "account_age_days": 10,
    }
    assert ordered_features(payload) == [10.0, 3.0, 100.0, 0.5]
    assert FEATURE_NAMES[0] == "account_age_days"
