from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import torch
from torch import nn
from torch.utils.data import DataLoader, TensorDataset

from .features import FEATURE_NAMES
from .model import RiskNet


def make_synthetic_dataset(samples: int, seed: int) -> tuple[np.ndarray, np.ndarray]:
    rng = np.random.default_rng(seed)
    account_age_days = rng.uniform(1, 3000, size=samples)
    failed_login_count = rng.poisson(2.0, size=samples).astype(float)
    transaction_amount = rng.gamma(shape=2.0, scale=120.0, size=samples)
    device_trust_score = rng.beta(a=3.0, b=2.0, size=samples)
    x = np.column_stack([account_age_days, failed_login_count, transaction_amount, device_trust_score]).astype(np.float32)

    logit = (
        -1.5
        - 0.0004 * account_age_days
        + 0.55 * failed_login_count
        + 0.0060 * transaction_amount
        - 2.2 * device_trust_score
        + rng.normal(0, 0.45, size=samples)
    )
    probability = 1.0 / (1.0 + np.exp(-logit))
    y = (probability > 0.5).astype(np.float32)
    return x, y


def train_one_version(version: str, model_dir: Path, epochs: int, seed: int) -> dict[str, object]:
    torch.manual_seed(seed)
    x, y = make_synthetic_dataset(samples=1200, seed=seed)
    reference_mean = x.mean(axis=0).tolist()
    reference_std = x.std(axis=0).tolist()

    x_normalized = ((x - np.asarray(reference_mean, dtype=np.float32)) / np.asarray(reference_std, dtype=np.float32)).astype(np.float32)
    dataset = TensorDataset(torch.tensor(x_normalized), torch.tensor(y))
    loader = DataLoader(dataset, batch_size=128, shuffle=True)
    model = RiskNet(input_dim=len(FEATURE_NAMES))
    optimizer = torch.optim.Adam(model.parameters(), lr=0.01)
    loss_fn = nn.BCEWithLogitsLoss()

    model.train()
    for _ in range(epochs):
        for batch_x, batch_y in loader:
            optimizer.zero_grad()
            logits = model(batch_x)
            loss = loss_fn(logits, batch_y)
            loss.backward()
            optimizer.step()

    model.eval()
    with torch.no_grad():
        logits = model(torch.tensor(x_normalized))
        probs = torch.sigmoid(logits)
        predictions = (probs >= 0.5).float()
        accuracy = float((predictions == torch.tensor(y)).float().mean().item())

    model_dir.mkdir(parents=True, exist_ok=True)
    filename = f"model_{version}.pt"
    checkpoint = {
        "version": version,
        "state_dict": model.state_dict(),
        "feature_names": FEATURE_NAMES,
        "reference_mean": reference_mean,
        "reference_std": reference_std,
        "threshold": 0.5,
        "training_accuracy": accuracy,
    }
    torch.save(checkpoint, model_dir / filename)
    return {"file": filename, "training_accuracy": accuracy}


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Train and register versioned PyTorch risk models")
    parser.add_argument("--model-dir", default="models")
    parser.add_argument("--versions", nargs="+", default=["v1", "v2"])
    parser.add_argument("--epochs", type=int, default=5)
    args = parser.parse_args(argv)

    model_dir = Path(args.model_dir)
    models: dict[str, object] = {}
    for offset, version in enumerate(args.versions):
        models[version] = train_one_version(version, model_dir, epochs=args.epochs, seed=42 + offset)

    registry = {
        "active_version": args.versions[-1],
        "deployment_history": list(args.versions),
        "models": models,
    }
    (model_dir / "registry.json").write_text(json.dumps(registry, indent=2), encoding="utf-8")
    print(json.dumps(registry, indent=2))


if __name__ == "__main__":
    main()
