"""
Train TFT-MPIR Decision Model
Malak's Training Script
"""

import pandas as pd
import numpy as np
import torch
import torch.nn as nn
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error, r2_score
import pickle
import os
import warnings
warnings.filterwarnings('ignore')

print("=" * 70)
print("🧠 TRAINING TFT-MPIR DECISION MODEL")
print("=" * 70)

# ============================================================
# 1. CHECK DATA
# ============================================================
print("\n📂 1. CHECKING DATA")
print("-" * 40)

data_path = 'data/inventory_history.csv'

if not os.path.exists(data_path):
    print(f"❌ Data file not found: {data_path}")
    print("\n📥 Create data using:")
    print("   python export_walmart_data.py")
    exit()

df = pd.read_csv(data_path)
print(f"✅ Loaded {len(df)} records")

# ============================================================
# 2. FEATURE ENGINEERING
# ============================================================
print("\n🔧 2. FEATURE ENGINEERING")
print("-" * 40)

# Convert date
df['date'] = pd.to_datetime(df['date'])

# Rolling averages
df['sales_7d'] = df.groupby('sku_id')['sales'].transform(
    lambda x: x.rolling(7, min_periods=1).mean()
)
df['sales_30d'] = df.groupby('sku_id')['sales'].transform(
    lambda x: x.rolling(30, min_periods=1).mean()
)
df['demand_7d'] = df.groupby('sku_id')['demand'].transform(
    lambda x: x.rolling(7, min_periods=1).mean()
)

# Stock ratio
df['stock_ratio'] = df['stock'] / (df['sales_7d'] + 1)

# Future demand (target)
df['future_demand'] = df.groupby('sku_id')['demand'].shift(-7).fillna(0)

# Seasonality
df['day_of_week'] = df['date'].dt.dayofweek
df['month'] = df['date'].dt.month
df['quarter'] = df['date'].dt.quarter

# Price change
df['price_change'] = df.groupby('sku_id')['price'].pct_change().fillna(0)

df = df.dropna()
print(f"✅ {len(df)} records after feature engineering")

# ============================================================
# 3. CALCULATE TARGET
# ============================================================
print("\n📊 3. CALCULATING OPTIMAL QUANTITIES")
print("-" * 40)

def calculate_optimal_qty(row, holding=2.0, stockout=100.0):
    demand = row['future_demand']
    stock = row['stock']
    if demand <= 0 or stock >= demand:
        return 0
    critical_ratio = stockout / (stockout + holding * 7)
    deficit = demand - stock
    return max(0, int(deficit * min(1.5, 1 + (1 - critical_ratio) * 0.5)))

df['optimal_qty'] = df.apply(calculate_optimal_qty, axis=1)
print(f"✅ Target calculated")

# ============================================================
# 4. PREPARE TRAINING DATA
# ============================================================
print("\n🧠 4. PREPARING TRAINING DATA")
print("-" * 40)

feature_cols = ['price', 'cost', 'stock', 'sales_7d', 'sales_30d',
                'demand_7d', 'stock_ratio', 'day_of_week', 'month', 
                'quarter', 'price_change']

available_features = [col for col in feature_cols if col in df.columns]
X = df[available_features].values
y = df['optimal_qty'].values

# Scale
scaler = StandardScaler()
X_scaled = scaler.fit_transform(X)

# Split
X_train, X_temp, y_train, y_temp = train_test_split(
    X_scaled, y, test_size=0.3, random_state=42
)
X_val, X_test, y_val, y_test = train_test_split(
    X_temp, y_temp, test_size=0.5, random_state=42
)

print(f"   Training: {len(X_train)}, Validation: {len(X_val)}, Test: {len(X_test)}")

# ============================================================
# 5. DEFINE MODEL
# ============================================================
print("\n🏗️ 5. DEFINING MODEL")
print("-" * 40)

# CORRECT IMPORT: from backend.agents.tft_mpir_model
from backend.agents.tft_mpir_model import TFT_MPIR_Model

model = TFT_MPIR_Model(input_dim=len(available_features))
print(f"✅ Model created: {sum(p.numel() for p in model.parameters()):,} parameters")

# ============================================================
# 6. TRAIN
# ============================================================
print("\n🏋️ 6. TRAINING")
print("-" * 40)

criterion = nn.MSELoss()
optimizer = torch.optim.Adam(model.parameters(), lr=0.001)
scheduler = torch.optim.lr_scheduler.ReduceLROnPlateau(optimizer, patience=10, factor=0.5)

X_train_t = torch.FloatTensor(X_train)
y_train_t = torch.FloatTensor(y_train).reshape(-1, 1)
X_val_t = torch.FloatTensor(X_val)
y_val_t = torch.FloatTensor(y_val).reshape(-1, 1)

epochs = 100
batch_size = 64

for epoch in range(epochs):
    model.train()
    total_loss = 0
    
    perm = torch.randperm(len(X_train_t))
    X_shuffled = X_train_t[perm]
    y_shuffled = y_train_t[perm]
    
    for i in range(0, len(X_shuffled), batch_size):
        batch_X = X_shuffled[i:i+batch_size]
        batch_y = y_shuffled[i:i+batch_size]
        
        optimizer.zero_grad()
        pred = model(batch_X)
        loss = criterion(pred, batch_y)
        loss.backward()
        optimizer.step()
        total_loss += loss.item()
    
    avg_loss = total_loss / max(1, len(X_shuffled) / batch_size)
    
    model.eval()
    with torch.no_grad():
        val_pred = model(X_val_t)
        val_loss = criterion(val_pred, y_val_t).item()
    
    scheduler.step(val_loss)
    
    if (epoch + 1) % 20 == 0:
        print(f"   Epoch {epoch+1}/{epochs} - Train: {avg_loss:.4f}, Val: {val_loss:.4f}")

print("✅ Training complete")

# ============================================================
# 7. EVALUATE
# ============================================================
print("\n📊 7. EVALUATING")
print("-" * 40)

model.eval()
with torch.no_grad():
    X_test_t = torch.FloatTensor(X_test)
    y_pred = model(X_test_t).numpy().flatten()
    
    mae = mean_absolute_error(y_test, y_pred)
    r2 = r2_score(y_test, y_pred)
    print(f"   MAE: {mae:.2f} units")
    print(f"   R²: {r2:.4f}")

# ============================================================
# 8. SAVE
# ============================================================
print("\n💾 8. SAVING MODEL")
print("-" * 40)

os.makedirs('models', exist_ok=True)

torch.save(model.state_dict(), 'models/decision_model.pth')

with open('models/decision_scaler.pkl', 'wb') as f:
    pickle.dump(scaler, f)

with open('models/decision_features.pkl', 'wb') as f:
    pickle.dump(available_features, f)

print("✅ Saved to: models/")
print("   - decision_model.pth")
print("   - decision_scaler.pkl")
print("   - decision_features.pkl")

print("\n" + "=" * 70)
print("✅ TRAINING COMPLETE!")
print("=" * 70)