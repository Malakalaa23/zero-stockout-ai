#!/usr/bin/env python3
"""
Quick fixes for common issues
"""

import os
import sys
from pathlib import Path

def fix_imports():
    """Fix common import issues"""
    backend_path = Path("backend")
    
    # Ensure __init__.py exists in agents and api
    for dir_name in ["agents", "api", "models"]:
        init_file = backend_path / dir_name / "__init__.py"
        if not init_file.exists():
            init_file.write_text("# Auto-generated __init__.py")
            print(f"✅ Created {init_file}")

def fix_requirements():
    """Add missing packages to requirements"""
    req_file = Path("backend/requirements.txt")
    if req_file.exists():
        content = req_file.read_text()
        
        # Add missing packages
        required_packages = [
            "pytorch-forecasting",
            "pytorch-lightning",
            "plotly",
            "streamlit",
            "requests"
        ]
        
        added = []
        for pkg in required_packages:
            if pkg not in content:
                content += f"\n{pkg}"
                added.append(pkg)
        
        if added:
            req_file.write_text(content)
            print(f"✅ Added packages: {', '.join(added)}")

def main():
    print("🔧 Applying quick fixes...")
    fix_imports()
    fix_requirements()
    print("✅ Fixes applied")

if __name__ == "__main__":
    main()