"""
TFT-MPIR Neural Network — matches the trained decision_model.pth
Architecture:
  - Input: 19 features → 128
  - 3 residual blocks (128 → 128) with BatchNorm
  - Output: 128 → 64 with BatchNorm
  - 3 quantile heads: q10, q50, q90
"""

import torch
import torch.nn as nn


class ResidualBlock(nn.Module):
    """Single residual block: Linear → BatchNorm → ReLU → add identity."""

    def __init__(self, dim: int = 128, dropout: float = 0.1):
        super().__init__()
        self.fc = nn.Linear(dim, dim)
        self.bn = nn.BatchNorm1d(dim)
        self.relu = nn.ReLU()
        self.dropout = nn.Dropout(dropout)

    def forward(self, x):
        identity = x
        out = self.fc(x)
        out = self.bn(out)
        out = self.relu(out)
        out = self.dropout(out)
        return identity + out


class TFT_MPIR_Model(nn.Module):
    """
    TFT-MPIR decision model — 19 features → optimal order quantity.
    Returns three quantiles (10%, 50%, 90%) for uncertainty.
    """

    def __init__(self, input_dim: int = 19):
        super().__init__()

        # Input layer
        self.input_layer = nn.Linear(input_dim, 128)
        self.input_bn = nn.BatchNorm1d(128)

        # Three residual blocks
        self.res_blocks = nn.ModuleList([
            ResidualBlock(128) for _ in range(3)
        ])

        # Output layer
        self.output_layer = nn.Linear(128, 64)
        self.output_bn = nn.BatchNorm1d(64)

        # Quantile heads
        self.q10 = nn.Linear(64, 1)
        self.q50 = nn.Linear(64, 1)
        self.q90 = nn.Linear(64, 1)

        self.relu = nn.ReLU()

    def forward(self, x):
        # Input
        x = self.relu(self.input_bn(self.input_layer(x)))

        # Residual blocks
        for block in self.res_blocks:
            x = block(x)

        # Output
        x = self.relu(self.output_bn(self.output_layer(x)))

        # Quantiles
        q10 = self.q10(x)
        q50 = self.q50(x)
        q90 = self.q90(x)

        return q10, q50, q90

    def predict_point(self, x):
        """Return the median (q50) prediction — used as the point estimate."""
        _, q50, _ = self.forward(x)
        return q50