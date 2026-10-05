"""
Train TFT-MPIR Decision Model from synthetic data.

Uses 21 features (19 original + 'days' and 'expected_demand').
These two additions give the model everything it needs to learn
the closed-form optimum: q* = max(0, sum(demand[:days]) - stock).

Run from project root:
    python backend/train_decision_model.py
"""

import os
import pickle
import sys
from pathlib import Path

import numpy as np
import torch
import torch.nn as nn
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error, r2_score

# Ensure 'backend' is importable
sys.path.insert(0, str(Path(__file__).parent))
from agents.tft_mpir_model import TFT_MPIR_Model

# ---- Config ----
N_SAMPLES = 10_000
EPOCHS = 60
BATCH_SIZE = 128
LEARNING_RATE = 1e-3
SEED = 42

MODELS_DIR = Path(__file__).parent / "models"
MODELS_DIR.mkdir(exist_ok=True)

# ---- 21 features — MUST match decision_agent.py's feature_dict exactly ----
FEATURES = [
    "price",
    "cost",
    "stock",
    "days",
    "expected_demand",
    "lead_time_days",
    "sales_mean_7d",
    "sales_mean_14d",
    "sales_mean_30d",
    "sales_std_7d",
    "stock_ratio",
    "day_sin",
    "day_cos",
    "month_sin",
    "month_cos",
    "is_weekend",
    "price_change",
    "demand_lag_1",
    "demand_lag_3",
    "demand_lag_7",
    "lead_time_demand",
]

COST_PARAMS = {
    "holding": 2.0,
    "stockout": 100.0,
    "shipping_base": 50.0,
    "shipping_per_unit": 5.0,
}


def total_cost(q, demand, stock, days, cp):
    """Ground-truth cost function (matches decision_agent.py)."""
    expected = sum(demand[:days])
    stockout = max(0.0, expected - stock - q) * cp["stockout"]
    avg_inv = stock - expected + q / 2.0
    holding = max(0.0, avg_inv) * cp["holding"] * days
    shipping = cp["shipping_base"] + q * cp["shipping_per_unit"]
    return stockout + holding + shipping


def optimal_q(demand, stock, days, cp):
    """Brute-force optimal quantity."""
    max_q = max(1, int(sum(demand[:days]) * 1.5))
    best_q, best_cost = 0, float("inf")
    for q in range(max_q + 1):
        c = total_cost(q, demand, stock, days, cp)
        if c < best_cost:
            best_cost, best_q = c, q
    return best_q


def build_feature_dict(rng, demand, stock, days, unit_cost):
    """Build the 21-feature dict matching decision_agent.py exactly."""
    def mean_n(n):
        vals = demand[:n]
        return float(np.mean(vals)) if vals else 0.0

    def std_n(n):
        vals = demand[:n]
        return float(np.std(vals)) if vals else 0.0

    def lag(n):
        return float(demand[n - 1]) if len(demand) >= n else 0.0

    mean_7d = mean_n(7)
    mean_14d = mean_n(14)
    mean_30d = mean_n(30) if len(demand) >= 30 else mean_n(len(demand))
    std_7d = std_n(7)
    stock_ratio = stock / (mean_7d + 1.0) if mean_7d > 0 else 0.0
    lead_time_days = float(rng.integers(3, 8))
    lead_time_demand = mean_7d * lead_time_days / 7.0

    day_of_year = int(rng.integers(1, 366))
    month = int(rng.integers(1, 13))

    return {
        "price": float(unit_cost),
        "cost": float(unit_cost),
        "stock": float(stock),
        "days": float(days),
        "expected_demand": float(sum(demand[:days])),
        "lead_time_days": lead_time_days,
        "sales_mean_7d": mean_7d,
        "sales_mean_14d": mean_14d,
        "sales_mean_30d": mean_30d,
        "sales_std_7d": std_7d,
        "stock_ratio": stock_ratio,
        "day_sin": float(np.sin(2 * np.pi * day_of_year / 365.0)),
        "day_cos": float(np.cos(2 * np.pi * day_of_year / 365.0)),
        "month_sin": float(np.sin(2 * np.pi * month / 12.0)),
        "month_cos": float(np.cos(2 * np.pi * month / 12.0)),
        "is_weekend": float(rng.integers(0, 2)),
        "price_change": float(rng.normal(0, 0.05)),
        "demand_lag_1": lag(1),
        "demand_lag_3": lag(3),
        "demand_lag_7": lag(7),
        "lead_time_demand": lead_time_demand,
    }


def generate_dataset(n):
    rng = np.random.default_rng(SEED)
    X = np.zeros((n, len(FEATURES)), dtype=np.float32)
    y = np.zeros((n, 1), dtype=np.float32)

    for i in range(n):
        days = int(rng.integers(7, 31))
        base_demand = float(rng.uniform(5, 30))
        demand = list(np.clip(rng.normal(base_demand, 3.0, size=days), 0, None))
        stock = int(rng.integers(0, int(base_demand * days * 1.2) + 1))
        unit_cost = float(rng.uniform(5, 50))

        feats = build_feature_dict(rng, demand, stock, days, unit_cost)
        X[i] = [feats[f] for f in FEATURES]
        y[i, 0] = float(optimal_q(demand, stock, days, COST_PARAMS))

    return X, y


def main():
    print("=" * 70)
    print("TRAINING TFT-MPIR DECISION MODEL (21 features, synthetic data)")
    print("=" * 70)

    print("\n[1/6] Generating synthetic samples...")
    X, y = generate_dataset(N_SAMPLES)
    print(f"      X: {X.shape}   y: {y.shape}")
    print(f"      Target range: {y.min():.0f} - {y.max():.0f} (mean {y.mean():.1f})")

    print("\n[2/6] Splitting data...")
    X_tv, X_test, y_tv, y_test = train_test_split(
        X, y, test_size=0.15, random_state=SEED
    )
    X_train, X_val, y_train, y_val = train_test_split(
        X_tv, y_tv, test_size=0.15, random_state=SEED
    )
    print(f"      train={len(X_train)}  val={len(X_val)}  test={len(X_test)}")

    print("\n[3/6] Scaling features...")
    scaler = StandardScaler().fit(X_train)
    X_train_s = scaler.transform(X_train).astype(np.float32)
    X_val_s = scaler.transform(X_val).astype(np.float32)
    X_test_s = scaler.transform(X_test).astype(np.float32)

    print("\n[4/6] Building model...")
    model = TFT_MPIR_Model(input_dim=len(FEATURES))
    n_params = sum(p.numel() for p in model.parameters())
    print(f"      Parameters: {n_params:,}")

    X_train_t = torch.from_numpy(X_train_s)
    y_train_t = torch.from_numpy(y_train)
    X_val_t = torch.from_numpy(X_val_s)
    y_val_t = torch.from_numpy(y_val)

    optimizer = torch.optim.Adam(model.parameters(), lr=LEARNING_RATE)
    loss_fn = nn.MSELoss()

    print(f"\n[5/6] Training for {EPOCHS} epochs...")
    best_val = float("inf")
    best_state = None

    for epoch in range(EPOCHS):
        model.train()
        perm = torch.randperm(len(X_train_t))
        for i in range(0, len(X_train_t), BATCH_SIZE):
            idx = perm[i:i + BATCH_SIZE]
            xb, yb = X_train_t[idx], y_train_t[idx]

            optimizer.zero_grad()
            _, q50, _ = model(xb)
            loss = loss_fn(q50, yb)
            loss.backward()
            optimizer.step()

        if (epoch + 1) % 10 == 0 or epoch == 0:
            model.eval()
            with torch.no_grad():
                _, val_pred, _ = model(X_val_t)
                val_loss = loss_fn(val_pred, y_val_t).item()
            print(f"      Epoch {epoch + 1:3d}/{EPOCHS}   val MSE: {val_loss:.2f}")

            if val_loss < best_val:
                best_val = val_loss
                best_state = {k: v.clone() for k, v in model.state_dict().items()}

    # Restore best weights
    if best_state is not None:
        model.load_state_dict(best_state)
        print(f"      Restored best weights (val MSE: {best_val:.2f})")

    print("\n[6/6] Evaluating and saving...")
    model.eval()
    with torch.no_grad():
        _, y_pred, _ = model(torch.from_numpy(X_test_s))
        y_pred = y_pred.numpy().flatten()

    mae = mean_absolute_error(y_test.flatten(), y_pred)
    r2 = r2_score(y_test.flatten(), y_pred)
    print(f"      MAE: {mae:.2f} units")
    print(f"      R² : {r2:.4f}")

    torch.save(model.state_dict(), MODELS_DIR / "decision_model.pth")
    with open(MODELS_DIR / "decision_scaler.pkl", "wb") as f:
        pickle.dump(scaler, f)
    with open(MODELS_DIR / "decision_features.pkl", "wb") as f:
        pickle.dump(FEATURES, f)

    print(f"\n      Saved to {MODELS_DIR}")
    print("        - decision_model.pth")
    print("        - decision_scaler.pkl")
    print("        - decision_features.pkl")
    print("\n" + "=" * 70)
    print("TRAINING COMPLETE")
    print("=" * 70)


if __name__ == "__main__":
    main()