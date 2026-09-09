"""
TFT-MPIR Neural Network Model Definition
Malak's TFT-MPIR Decision Model

This is the neural network that learns optimal order quantities
from historical inventory data.
"""

import torch
import torch.nn as nn


class TFT_MPIR_Model(nn.Module):
    """
    Simplified TFT-MPIR neural network.
    Learns optimal order quantities from historical data.
    
    Architecture:
    - 3 hidden layers with batch normalization
    - ReLU activation
    - Dropout for regularization (0.3)
    - Single output (order quantity)
    """
    
    def __init__(self, input_dim: int):
        super().__init__()
        
        # Layer 1: input → 128 neurons
        self.fc1 = nn.Linear(input_dim, 128)
        self.bn1 = nn.BatchNorm1d(128)
        
        # Layer 2: 128 → 64 neurons
        self.fc2 = nn.Linear(128, 64)
        self.bn2 = nn.BatchNorm1d(64)
        
        # Layer 3: 64 → 32 neurons
        self.fc3 = nn.Linear(64, 32)
        
        # Layer 4: 32 → 1 (output)
        self.fc4 = nn.Linear(32, 1)
        
        # Activation and regularization
        self.relu = nn.ReLU()
        self.dropout = nn.Dropout(0.3)
        
    def forward(self, x):
        x = self.relu(self.bn1(self.fc1(x)))
        x = self.dropout(x)
        x = self.relu(self.bn2(self.fc2(x)))
        x = self.dropout(x)
        x = self.relu(self.fc3(x))
        x = self.fc4(x)
        return x