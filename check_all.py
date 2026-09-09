#!/usr/bin/env python3
"""
Complete Project Check - Runs all audits and tests
"""

import subprocess
import sys
from pathlib import Path

def run_command(cmd, description):
    print(f"\n▶️ {description}")
    print("-" * 40)
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    print(result.stdout)
    if result.stderr:
        print(f"⚠️ {result.stderr}")
    return result.returncode == 0

def main():
    print("🧪 ZERO-STOCKOUT AI - COMPLETE SYSTEM CHECK")
    print("=" * 60)
    
    # 1. Run the audit
    print("\n📋 STEP 1: System Audit")
    success = run_command("python audit_system.py", "Running system audit")
    if not success:
        print("❌ Audit failed - check errors above")
        return
    
    # 2. Run unit tests
    print("\n🧪 STEP 2: Unit Tests")
    success = run_command("python -m unittest backend/tests/test_decision_agent.py", 
                         "Running Decision Agent tests")
    if success:
        print("✅ Unit tests passed")
    else:
        print("⚠️ Unit tests have failures")
    
    # 3. Check if services are running
    print("\n🌐 STEP 3: Service Health Check")
    
    # Check backend
    try:
        import requests
        resp = requests.get("http://localhost:8000/health", timeout=2)
        if resp.status_code == 200:
            print("✅ Backend is running")
        else:
            print(f"⚠️ Backend returned {resp.status_code}")
    except:
        print("⚠️ Backend not running - start with: cd backend && python main.py")
    
    # 4. Check for frontend
    if (Path.cwd() / "frontend" / "app.py").exists():
        print("✅ Frontend exists")
    else:
        print("❌ Frontend missing")
    
    # 5. Final summary
    print("\n" + "=" * 60)
    print("📊 CHECK COMPLETE")
    print("=" * 60)
    print("\nTo start the system:")
    print("  Option 1: docker-compose up -d")
    print("  Option 2: cd backend && python main.py (in one terminal)")
    print("           cd frontend && streamlit run app.py (in another)")
    print("\nAccess:")
    print("  API: http://localhost:8000/docs")
    print("  Frontend: http://localhost:8501")

if __name__ == "__main__":
    main()