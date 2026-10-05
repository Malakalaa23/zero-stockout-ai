"""Rebuild best.pt with correct ZIP structure for PyTorch.

PyTorch .pt files are ZIP archives where every entry must:
  - Use forward slashes (/) as path separators
  - Live inside a subdirectory (not at the archive root)

PowerShell's Compress-Archive violates both rules, so we rebuild manually.
"""

import os
import shutil
import zipfile

# --- Paths ---
MODELS_DIR = r"C:\Users\Malak\zero-stockout\backend\models"
SOURCE_ZIP = r"C:\Users\Malak\Downloads\best.pt.zip"
FINAL_PT = os.path.join(MODELS_DIR, "best.pt")
EXTRACTED = os.path.join(MODELS_DIR, "best")

# --- Step 1: Remove corrupted best.pt if it exists ---
if os.path.exists(FINAL_PT):
    os.remove(FINAL_PT)
    print(f"Deleted corrupted {FINAL_PT}")

# --- Step 2: Extract the source zip ---
if os.path.isdir(EXTRACTED):
    shutil.rmtree(EXTRACTED)

print(f"Extracting {SOURCE_ZIP}...")
with zipfile.ZipFile(SOURCE_ZIP, "r") as zf:
    zf.extractall(MODELS_DIR)

# --- Step 3: Find the folder that contains data.pkl ---
model_root = EXTRACTED
if not os.path.exists(os.path.join(model_root, "data.pkl")):
    for entry in os.listdir(EXTRACTED):
        candidate = os.path.join(EXTRACTED, entry)
        if os.path.isdir(candidate) and os.path.exists(
            os.path.join(candidate, "data.pkl")
        ):
            model_root = candidate
            break

if not os.path.exists(os.path.join(model_root, "data.pkl")):
    raise SystemExit(f"ERROR: data.pkl not found under {EXTRACTED}")

print(f"Model root: {model_root}")

# --- Step 4: Rebuild best.pt with proper structure ---
with zipfile.ZipFile(FINAL_PT, "w", zipfile.ZIP_STORED) as zf:
    for root, dirs, files in os.walk(model_root):
        for f in files:
            full_path = os.path.join(root, f)
            rel_path = os.path.relpath(full_path, model_root)
            # Forward slashes + prefix "best/" so files are in a subdirectory
            arcname = "best/" + rel_path.replace("\\", "/")
            zf.write(full_path, arcname)

size = os.path.getsize(FINAL_PT)
print(f"Created {FINAL_PT} ({size:,} bytes)")

# --- Step 5: Clean up extracted folder ---
shutil.rmtree(EXTRACTED)
print(f"Removed {EXTRACTED}")

# --- Step 6: Verify the rebuilt file loads in PyTorch ---
import torch

try:
    model = torch.load(FINAL_PT, map_location="cpu", weights_only=False)
    print("VALID MODEL")
    if isinstance(model, dict):
        print("Keys:", list(model.keys())[:8])
except Exception as e:
    print(f"TORCH LOAD FAILED: {e}")
    raise SystemExit(1)