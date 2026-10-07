# check_project.py
# MALAK'S PROJECT CHECK - See everything we built

import os
import sys
import json
import subprocess
import requests
from pathlib import Path

print("=" * 60)
print("🔍 ZERO-STOCKOUT PROJECT CHECK")
print("=" * 60)
print()

# ============================================
# 1. CHECK FOLDER STRUCTURE
# ============================================

print("📂 1. PROJECT FOLDER STRUCTURE")
print("-" * 40)

base_path = Path.cwd()
print(f"📍 Location: {base_path}")
print()

files_to_check = [
    "backend/agents/decision_agent.py",
    "backend/agents/forecast_agent.py",
    "backend/agents/vision_agent.py",
    "backend/agents/rag_agent.py",
    "backend/api/routes.py",
    "backend/main.py",
    "backend/config.py",
    "backend/requirements.txt",
    "backend/Dockerfile",
    "frontend/app.py",
    "frontend/Dockerfile",
    "docker-compose.yml",
    ".gitignore",
    "README.md"
]

print("📄 Files Found:")
for file in files_to_check:
    if Path(file).exists():
        size = Path(file).stat().st_size
        print(f"  ✅ {file} ({size} bytes)")
    else:
        print(f"  ❌ {file} - MISSING")
print()


# ============================================
# 2. CHECK YOUR DECISION AGENT CODE
# ============================================

print("🧠 2. MALAK'S DECISION AGENT")
print("-" * 40)

try:
    with open("backend/agents/decision_agent.py", "r", encoding="utf-8") as f:
        decision_code = f.read()
        lines = len(decision_code.splitlines())
        print(f"  📄 Lines of code: {lines}")
        
        # Check key functions
        if "compute_total_cost" in decision_code:
            print("  ✅ compute_total_cost() found")
        if "optimal_quantity" in decision_code:
            print("  ✅ optimal_quantity() found")
        if "TFTMPIR_DecisionAgent" in decision_code:
            print("  ✅ TFTMPIR_DecisionAgent class found")
            
        # Count methods
        method_count = decision_code.count("def ")
        print(f"  🔧 Methods: {method_count}")
        
except FileNotFoundError:
    print("  ❌ decision_agent.py not found")
print()


# ============================================
# 3. CHECK API ROUTES
# ============================================

print("🔗 3. API ROUTES (MALAK'S INTEGRATION)")
print("-" * 40)

try:
    with open("backend/api/routes.py", "r", encoding="utf-8") as f:
        routes_code = f.read()
        lines = len(routes_code.splitlines())
        print(f"  📄 Lines of code: {lines}")
        
        endpoints = [
            ("@app.get('/')", "GET /"),
            ("@app.get('/health')", "GET /health"),
            ("@app.post('/predict/forecast')", "POST /predict/forecast"),
            ("@app.post('/predict/vision')", "POST /predict/vision"),
            ("@app.post('/predict/rag')", "POST /predict/rag"),
            ("@app.post('/predict/decision')", "POST /predict/decision"),
            ("@app.post('/predict/full')", "POST /predict/full"),
        ]
        
        print("  🚀 Endpoints found:")
        for code, name in endpoints:
            if code in routes_code:
                print(f"    ✅ {name}")
            else:
                print(f"    ❌ {name} - MISSING")
                
except FileNotFoundError:
    print("  ❌ routes.py not found")
print()


# ============================================
# 4. CHECK DOCKER SERVICES
# ============================================

print("🐳 4. DOCKER SERVICES")
print("-" * 40)

try:
    with open("docker-compose.yml", "r", encoding="utf-8") as f:
        docker_code = f.read()
        
        services = [
            "timescaledb",
            "redis",
            "neo4j",
            "chromadb",
            "backend",
            "frontend"
        ]
        
        print("  Services defined:")
        for service in services:
            if service in docker_code:
                print(f"    ✅ {service}")
            else:
                print(f"    ❌ {service} - MISSING")
                
except FileNotFoundError:
    print("  ❌ docker-compose.yml not found")
print()


# ============================================
# 5. CHECK REQUIREMENTS
# ============================================

print("📦 5. REQUIREMENTS.TXT")
print("-" * 40)

try:
    with open("backend/requirements.txt", "r", encoding="utf-8") as f:
        reqs = f.read()
        packages = [line.strip() for line in reqs.splitlines() if line.strip() and not line.startswith("#")]
        print(f"  📦 Packages: {len(packages)}")
        print(f"  📄 First 5 packages:")
        for pkg in packages[:5]:
            print(f"    - {pkg}")
        if len(packages) > 5:
            print(f"    ... and {len(packages) - 5} more")
except FileNotFoundError:
    print("  ❌ requirements.txt not found")
print()


# ============================================
# 6. CHECK FRONTEND
# ============================================

print("🎨 6. FRONTEND APP")
print("-" * 40)

try:
    with open("frontend/app.py", "r", encoding="utf-8") as f:
        frontend_code = f.read()
        lines = len(frontend_code.splitlines())
        print(f"  📄 Lines of code: {lines}")
        
        features = [
            ("import plotly", "Plotly charts"),
            ("st.set_page_config", "Page config"),
            ("st.markdown", "Custom CSS"),
            ("st.tabs", "Tab layout"),
            ("st.button", "Buttons"),
            ("st.file_uploader", "File upload"),
        ]
        
        for code, name in features:
            if code in frontend_code:
                print(f"    ✅ {name}")
            else:
                print(f"    ❌ {name} - MISSING")
                
except FileNotFoundError:
    print("  ❌ app.py not found")
print()


# ============================================
# 7. CHECK GIT
# ============================================

print("📝 7. GIT STATUS")
print("-" * 40)

try:
    git_status = subprocess.run(["git", "status", "--porcelain"], capture_output=True, text=True)
    changed = git_status.stdout.strip().splitlines() if git_status.stdout else []
    print(f"  📝 Changed files: {len(changed)}")
    if changed:
        print("  📄 Modified files:")
        for f in changed[:5]:
            print(f"    - {f}")
        if len(changed) > 5:
            print(f"    ... and {len(changed) - 5} more")
except FileNotFoundError:
    print("  ⚠️ Git not initialized")
print()


# ============================================
# 8. CHECK DOCKER STATUS
# ============================================

print("🐳 8. DOCKER STATUS")
print("-" * 40)

try:
    # Check if Docker is running
    docker_ps = subprocess.run(["docker", "ps", "--format", "table {{.Names}}\t{{.Status}}"], 
                               capture_output=True, text=True)
    containers = docker_ps.stdout.strip().splitlines()
    
    if len(containers) > 1:
        print("  ✅ Docker is running")
        print("  📊 Running containers:")
        for line in containers[1:]:
            print(f"    - {line}")
    else:
        print("  ⚠️ No containers running")
        print("  🔧 Run: docker-compose up -d")
        
except FileNotFoundError:
    print("  ❌ Docker not found")
print()


# ============================================
# 9. CHECK API RESPONSE
# ============================================

print("🌐 9. API STATUS")
print("-" * 40)

try:
    response = requests.get("http://localhost:8000/health", timeout=3)
    if response.status_code == 200:
        print("  ✅ Backend is running")
        print(f"  📊 Response: {response.json()}")
    else:
        print(f"  ⚠️ Backend returned: {response.status_code}")
except requests.exceptions.ConnectionError:
    print("  ❌ Backend not running")
    print("  🔧 Run: docker-compose up -d")
except Exception as e:
    print(f"  ❌ Error: {e}")
print()


# ============================================
# 10. SUMMARY
# ============================================

print("=" * 60)
print("📊 SUMMARY")
print("=" * 60)

# Count what's done
done = 0
total = 0

for file in files_to_check:
    total += 1
    if Path(file).exists():
        done += 1

print(f"  📄 Files: {done}/{total} created")

# Check critical components
critical = {
    "decision_agent.py": Path("backend/agents/decision_agent.py").exists(),
    "routes.py": Path("backend/api/routes.py").exists(),
    "docker-compose.yml": Path("docker-compose.yml").exists(),
    "app.py": Path("frontend/app.py").exists()
}

critical_done = sum(critical.values())
critical_total = len(critical)

print(f"  🧠 Critical components: {critical_done}/{critical_total} ready")

# Print what's missing
if critical_done < critical_total:
    print()
    print("  ❌ Missing critical files:")
    for name, exists in critical.items():
        if not exists:
            print(f"    - {name}")

print()
print("=" * 60)
if done == total:
    print("🎉 ALL FILES CREATED! PROJECT IS COMPLETE!")
elif done > total * 0.8:
    print("✅ MOST FILES CREATED! PROJECT IS ALMOST READY!")
elif done > total * 0.5:
    print("⏳ SOME FILES CREATED! KEEP GOING!")
else:
    print("❌ MANY FILES MISSING! NEED TO CREATE THEM!")
print("=" * 60)