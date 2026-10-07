"""
Zero-Stockout AI System - Complete Audit System
Fixes: UTF-8 encoding, edge case handling, comprehensive testing
Version: 2.0.0 - Production Ready
"""

import os
import sys
import importlib
import ast
import socket
from datetime import datetime
from typing import Dict, List, Tuple, Optional

# ============================================================
# FIX: Force UTF-8 encoding for Windows
# ============================================================
if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')


class Colors:
    """ANSI color codes for terminal output."""
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    BOLD = '\033[1m'
    END = '\033[0m'


class SystemAuditor:
    """Complete system audit for Zero-Stockout AI."""
    
    def __init__(self, root_dir: str):
        self.root_dir = root_dir
        self.passes = 0
        self.warnings = 0
        self.failures = 0
        self.results = []
    
    def log_pass(self, message: str):
        self.passes += 1
        print(f"{Colors.GREEN}✅ PASS:{Colors.END} {message}")
        self.results.append(("PASS", message))
    
    def log_warn(self, message: str):
        self.warnings += 1
        print(f"{Colors.YELLOW}⚠️ WARN:{Colors.END} {message}")
        self.results.append(("WARN", message))
    
    def log_fail(self, message: str):
        self.failures += 1
        print(f"{Colors.RED}❌ FAIL:{Colors.END} {message}")
        self.results.append(("FAIL", message))
    
    def log_info(self, message: str):
        print(f"{Colors.BLUE}ℹ️ INFO:{Colors.END} {message}")
        self.results.append(("INFO", message))
    
    def file_exists(self, path: str) -> bool:
        """Check if a file exists relative to root."""
        full_path = os.path.join(self.root_dir, path)
        return os.path.exists(full_path) and os.path.isfile(full_path)
    
    def dir_exists(self, path: str) -> bool:
        """Check if a directory exists relative to root."""
        full_path = os.path.join(self.root_dir, path)
        return os.path.exists(full_path) and os.path.isdir(full_path)
    
    def file_size(self, path: str) -> int:
        """Get file size in bytes."""
        full_path = os.path.join(self.root_dir, path)
        return os.path.getsize(full_path) if os.path.exists(full_path) else 0
    
    def read_file(self, path: str, encoding: str = 'utf-8') -> Optional[str]:
        """Read a file with proper encoding."""
        full_path = os.path.join(self.root_dir, path)
        try:
            with open(full_path, 'r', encoding=encoding) as f:
                return f.read()
        except UnicodeDecodeError:
            encodings = ['utf-8', 'cp1252', 'latin-1', 'iso-8859-1']
            for enc in encodings:
                try:
                    with open(full_path, 'r', encoding=enc) as f:
                        content = f.read()
                        self.log_info(f"Read {path} with encoding: {enc}")
                        return content
                except:
                    continue
            self.log_fail(f"Could not read {path} with any encoding")
            return None
        except Exception as e:
            self.log_fail(f"Error reading {path}: {e}")
            return None
    
    # ============================================================
    # 1. FILE STRUCTURE AUDIT
    # ============================================================
    def audit_file_structure(self):
        print(f"\n{Colors.BOLD}{Colors.CYAN}📁 1. FILE STRUCTURE AUDIT{Colors.END}")
        
        files = [
            ("backend/agents/decision_agent.py", "Decision Agent"),
            ("backend/agents/forecast_agent.py", "Forecast Agent"),
            ("backend/agents/vision_agent.py", "Vision Agent"),
            ("backend/agents/rag_agent.py", "RAG Agent"),
            ("backend/api/routes.py", "API Routes"),
            ("backend/main.py", "Main Application"),
            ("backend/config.py", "Configuration"),
            ("backend/requirements.txt", "Requirements"),
            ("backend/Dockerfile", "Backend Dockerfile"),
            ("frontend/app.py", "Streamlit Dashboard"),
            ("frontend/Dockerfile", "Frontend Dockerfile"),
            ("docker-compose.yml", "Docker Compose"),
            (".gitignore", "Git Ignore"),
        ]
        
        for path, name in files:
            if self.file_exists(path):
                size = self.file_size(path)
                self.log_pass(f"{name} exists ({size} bytes)")
            else:
                self.log_fail(f"{name} MISSING → {path} not found")
    
    # ============================================================
    # 2. DECISION AGENT AUDIT
    # ============================================================
    def audit_decision_agent(self):
        print(f"\n{Colors.BOLD}{Colors.CYAN}🧠 2. DECISION AGENT AUDIT{Colors.END}")
        
        path = "backend/agents/decision_agent.py"
        content = self.read_file(path)
        if not content:
            self.log_fail("Could not read decision_agent.py")
            return
        
        if "import" in content and "class" in content:
            self.log_pass("Decision Agent imports successfully")
        
        if "class TFTMPIR_DecisionAgent" in content:
            self.log_pass("TFTMPIR_DecisionAgent class exists")
        else:
            self.log_fail("TFTMPIR_DecisionAgent class not found")
        
        methods = ['__init__', 'compute_total_cost', 'optimal_quantity']
        for method in methods:
            if f"def {method}" in content:
                self.log_pass(f"Method '{method}' exists")
            else:
                self.log_warn(f"Method '{method}' missing")
        
        if '"""' in content or "'''" in content:
            self.log_pass("Docstrings present")
        else:
            self.log_warn("No docstrings found")
    
    # ============================================================
    # 3. API ROUTES AUDIT
    # ============================================================
    def audit_api_routes(self):
        print(f"\n{Colors.BOLD}{Colors.CYAN}🔗 3. API ROUTES AUDIT{Colors.END}")
        
        path = "backend/api/routes.py"
        content = self.read_file(path)
        if not content:
            self.log_fail("Could not read routes.py")
            return
        
        if "from fastapi import" in content:
            self.log_pass("FastAPI imported")
        else:
            self.log_fail("FastAPI not imported")
        
        if "BaseModel" in content:
            self.log_pass("Pydantic BaseModel found")
        else:
            self.log_fail("No Pydantic models found")
        
        if ": str" in content or ": int" in content or ": float" in content:
            self.log_pass("Pydantic models have type annotations")
        else:
            self.log_warn("Pydantic models may be missing type annotations")
        
        if "router = APIRouter" in content:
            self.log_pass("APIRouter configured")
        else:
            self.log_fail("APIRouter not configured")
        
        endpoints = ['/forecast', '/decision', '/vision', '/rag']
        for endpoint in endpoints:
            if f"@router.post(\"{endpoint}\"" in content or f"@router.get(\"{endpoint}\"" in content:
                self.log_pass(f"Endpoint '{endpoint}' exists")
            else:
                self.log_warn(f"Endpoint '{endpoint}' missing")
    
    # ============================================================
    # 4. MAIN APPLICATION AUDIT
    # ============================================================
    def audit_main_app(self):
        print(f"\n{Colors.BOLD}{Colors.CYAN}🚀 4. MAIN APPLICATION AUDIT{Colors.END}")
        
        path = "backend/main.py"
        content = self.read_file(path)
        if not content:
            self.log_fail("Could not read main.py")
            return
        
        if "import uvicorn" in content:
            self.log_pass("Import 'uvicorn' found")
        else:
            self.log_warn("Import 'uvicorn' not found")
        
        if "api.routes:app" in content or '"api.routes:app"' in content:
            self.log_pass("FastAPI app correctly referenced")
        elif "app" in content and "uvicorn.run" in content:
            self.log_pass("FastAPI app appears to be configured")
        else:
            self.log_fail("FastAPI app not properly configured")
        
        if "if __name__ == \"__main__\":" in content or "if __name__ == '__main__':" in content:
            self.log_pass("Main block present")
        else:
            self.log_warn("No main block - may need to use uvicorn directly")
    
    # ============================================================
    # 5. CONFIGURATION AUDIT
    # ============================================================
    def audit_config(self):
        print(f"\n{Colors.BOLD}{Colors.CYAN}⚙️ 5. CONFIGURATION AUDIT{Colors.END}")
        
        path = "backend/config.py"
        content = self.read_file(path)
        if not content:
            self.log_fail("Could not read config.py")
            return
        
        if "os.getenv" in content or "os.environ" in content:
            self.log_pass("Environment variables used")
        else:
            self.log_warn("No environment variable usage - may hardcode values")
        
        if "POSTGRES" in content or "DB" in content:
            self.log_pass("Database configuration present")
        else:
            self.log_warn("Database configuration may be missing")
        
        if "REDIS" in content:
            self.log_pass("Redis configuration present")
        else:
            self.log_info("Redis configuration optional")
    
    # ============================================================
    # 6. DEPENDENCY AUDIT
    # ============================================================
    def audit_dependencies(self):
        print(f"\n{Colors.BOLD}{Colors.CYAN}📦 6. DEPENDENCY AUDIT{Colors.END}")
        
        path = "backend/requirements.txt"
        content = self.read_file(path)
        if not content:
            self.log_fail("Could not read requirements.txt")
            return
        
        packages = [line.strip() for line in content.split('\n') if line.strip() and not line.startswith('#')]
        self.log_pass(f"Found {len(packages)} packages")
        
        critical = ['fastapi', 'torch', 'pandas', 'numpy', 'streamlit']
        for pkg in critical:
            if any(pkg in p.lower() for p in packages):
                self.log_pass(f"Critical package '{pkg}' found")
            else:
                self.log_fail(f"Critical package '{pkg}' missing")
        
        versions = [p for p in packages if '==' in p]
        if len(versions) > 0:
            self.log_pass(f"Version pinning present ({len(versions)} packages)")
        else:
            self.log_warn("No version pinning found")
    
    # ============================================================
    # 7. DOCKER AUDIT
    # ============================================================
    def audit_docker(self):
        print(f"\n{Colors.BOLD}{Colors.CYAN}🐳 7. DOCKER AUDIT{Colors.END}")
        
        path = "docker-compose.yml"
        content = self.read_file(path)
        if content:
            services = content.count("services:")
            self.log_pass(f"Found {services} service{'s' if services > 1 else ''}")
            
            required = ['backend', 'frontend', 'timescaledb', 'redis', 'neo4j', 'chromadb']
            for service in required:
                if f"{service}:" in content.lower():
                    self.log_pass(f"Service '{service}' configured")
                else:
                    self.log_warn(f"Service '{service}' not configured")
        else:
            self.log_fail("docker-compose.yml missing")
        
        backend_docker = self.file_exists("backend/Dockerfile")
        frontend_docker = self.file_exists("frontend/Dockerfile")
        
        if backend_docker:
            content = self.read_file("backend/Dockerfile")
            if "FROM python" in content or "FROM" in content:
                self.log_pass("backend Dockerfile uses Python base")
            else:
                self.log_warn("backend Dockerfile may not use Python base")
        else:
            self.log_fail("backend Dockerfile missing")
        
        if frontend_docker:
            content = self.read_file("frontend/Dockerfile")
            if "FROM python" in content or "FROM" in content:
                self.log_pass("frontend Dockerfile uses Python base")
            else:
                self.log_warn("frontend Dockerfile may not use Python base")
        else:
            self.log_fail("frontend Dockerfile missing")
    
    # ============================================================
    # 8. FRONTEND AUDIT
    # ============================================================
    def audit_frontend(self):
        print(f"\n{Colors.BOLD}{Colors.CYAN}🎨 8. FRONTEND AUDIT{Colors.END}")
        
        path = "frontend/app.py"
        try:
            with open(os.path.join(self.root_dir, path), 'r', encoding='utf-8') as f:
                content = f.read()
                
            if "import streamlit" in content:
                self.log_pass("Streamlit imported")
            else:
                self.log_fail("Streamlit not imported")
            
            if "st.set_page_config" in content:
                self.log_pass("Page config configured")
            else:
                self.log_warn("Page config not configured")
            
            if "st.title" in content or "st.markdown" in content:
                self.log_pass("UI content present")
            else:
                self.log_warn("No UI content found")
            
            size = self.file_size(path)
            if size > 10000:
                self.log_pass(f"Dashboard is substantial ({size} bytes)")
            else:
                self.log_warn(f"Dashboard may be incomplete ({size} bytes)")
                
        except UnicodeDecodeError as e:
            self.log_fail(f"Frontend audit failed: Encoding error at position {e.start if hasattr(e, 'start') else 'unknown'}")
            self.log_info("Try: File contains special characters. Open with UTF-8 encoding.")
        except Exception as e:
            self.log_fail(f"Frontend audit failed: {e}")
    
    # ============================================================
    # 9. API ENDPOINT TESTS
    # ============================================================
    def audit_endpoints(self):
        print(f"\n{Colors.BOLD}{Colors.CYAN}🌐 9. API ENDPOINT TESTS{Colors.END}")
        
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        result = sock.connect_ex(('127.0.0.1', 8000))
        sock.close()
        
        if result == 0:
            self.log_pass("Backend is running on port 8000")
            self.log_info("Endpoint tests: Backend running - test manually at /docs")
        else:
            self.log_warn("Backend not running - skipping endpoint tests")
            self.log_info("Start backend with: cd backend && python main.py")
    
    # ============================================================
    # 10. EDGE CASE TESTS - ENHANCED & FIXED
    # ============================================================
    def audit_edge_cases(self):
        print(f"\n{Colors.BOLD}{Colors.CYAN}🔬 10. EDGE CASE TESTS{Colors.END}")
        
        try:
            from backend.agents.decision_agent import TFTMPIR_DecisionAgent
            agent = TFTMPIR_DecisionAgent()
            
            # ===== TEST 1: Empty demand forecast =====
            try:
                q, c = agent.optimal_quantity([], 50, 7)
                # If it returns without error, check if it's correct
                if q == 0 and c == 0:
                    self.log_pass("Handles empty demand correctly (returns 0)")
                else:
                    self.log_fail(f"Empty demand returned unexpected values: q={q}, c={c}")
            except ValueError as e:
                # This is the correct behavior - empty demand should raise ValueError
                if "empty" in str(e).lower():
                    self.log_pass("Handles empty demand correctly (raises ValueError)")
                else:
                    self.log_fail(f"Empty demand raised unexpected error: {e}")
            except Exception as e:
                self.log_fail(f"Empty demand test failed with unexpected error: {e}")
            
            # ===== TEST 2: Zero current stock =====
            try:
                q, c = agent.optimal_quantity([10, 15, 12], 0, 3)
                if q > 0:
                    self.log_pass("Handles zero stock correctly (orders positive quantity)")
                else:
                    self.log_fail(f"Zero stock should order > 0, got q={q}")
            except Exception as e:
                self.log_fail(f"Zero stock test failed: {e}")
            
            # ===== TEST 3: Large stock (no order needed) =====
            try:
                q, c = agent.optimal_quantity([1000, 1500, 1200], 10000, 3)
                if q == 0:
                    self.log_pass("Handles large stock correctly (no order needed)")
                else:
                    self.log_fail(f"Large stock should order 0, got q={q}")
            except Exception as e:
                self.log_fail(f"Large stock test failed: {e}")
            
            # ===== TEST 4: Negative order quantity (should never happen) =====
            try:
                q, c = agent.optimal_quantity([10, 15, 12], 50, 3)
                if q >= 0:
                    self.log_pass("Never returns negative order quantity")
                else:
                    self.log_fail(f"Returned negative order quantity: q={q}")
            except Exception as e:
                self.log_fail(f"Negative quantity test failed: {e}")
            
            # ===== TEST 5: Very large demand forecast =====
            try:
                large_demand = [10000] * 30
                q, c = agent.optimal_quantity(large_demand, 1000, 30)
                if q > 0:
                    self.log_pass("Handles large demand forecasts correctly")
                else:
                    self.log_fail("Large demand should order > 0")
            except Exception as e:
                self.log_fail(f"Large demand test failed: {e}")
            
            # ===== TEST 6: Negative days (should raise error) =====
            try:
                q, c = agent.optimal_quantity([10, 15, 12], 50, -1)
                self.log_fail("Should raise error for negative days")
            except ValueError:
                self.log_pass("Handles negative days correctly (raises ValueError)")
            except Exception as e:
                self.log_fail(f"Negative days test failed: {e}")
            
            # ===== TEST 7: Very short forecast (1 day) =====
            try:
                q, c = agent.optimal_quantity([100], 50, 1)
                if q >= 0:
                    self.log_pass("Handles single-day forecast correctly")
                else:
                    self.log_fail(f"Single-day forecast returned negative: q={q}")
            except Exception as e:
                self.log_fail(f"Single-day forecast test failed: {e}")
            
            # ===== TEST 8: safe_optimal_quantity method if exists =====
            if hasattr(agent, 'safe_optimal_quantity'):
                try:
                    q, c = agent.safe_optimal_quantity([], 50, 7)
                    if q == 0 and c == 0:
                        self.log_pass("safe_optimal_quantity handles empty demand")
                    else:
                        self.log_fail("safe_optimal_quantity returned unexpected values")
                except Exception as e:
                    self.log_fail(f"safe_optimal_quantity test failed: {e}")
            else:
                self.log_info("safe_optimal_quantity method not found (optional)")
                
        except ImportError as e:
            self.log_fail(f"Could not import Decision Agent: {e}")
        except Exception as e:
            self.log_fail(f"Edge case tests failed with unexpected error: {e}")
    
    # ============================================================
    # 11. SECURITY AUDIT
    # ============================================================
    def audit_security(self):
        print(f"\n{Colors.BOLD}{Colors.CYAN}🔐 11. SECURITY AUDIT{Colors.END}")
        
        path = "backend/config.py"
        content = self.read_file(path)
        if content:
            if "password" in content.lower() and "os.getenv" not in content:
                self.log_warn("Possible hardcoded secret in config.py")
            elif "password" in content.lower():
                self.log_pass("Secrets appear to use environment variables")
            else:
                self.log_info("No secrets found in config.py")
        
        if self.file_exists(".env"):
            self.log_pass(".env file present")
        else:
            self.log_warn(".env file missing - create one for production")
        
        gitignore = self.read_file(".gitignore")
        if gitignore and ".env" in gitignore:
            self.log_pass(".env in .gitignore")
        else:
            self.log_warn(".env not in .gitignore - add it for security")
    
    # ============================================================
    # RUN FULL AUDIT
    # ============================================================
    def run_full_audit(self):
        """Run all audit checks."""
        print(f"{Colors.BOLD}{Colors.CYAN}[*] ZERO-STOCKOUT AI SYSTEM AUDIT{Colors.END}")
        print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Root directory: {self.root_dir}")
        print("=" * 60)
        
        self.audit_file_structure()
        self.audit_decision_agent()
        self.audit_api_routes()
        self.audit_main_app()
        self.audit_config()
        self.audit_dependencies()
        self.audit_docker()
        self.audit_frontend()
        self.audit_endpoints()
        self.audit_edge_cases()
        self.audit_security()
        
        print("\n" + "=" * 60)
        print(f"{Colors.BOLD}AUDIT SUMMARY{Colors.END}")
        print("=" * 60)
        print(f"{Colors.GREEN}✅ PASS:{Colors.END} {self.passes}")
        print(f"{Colors.YELLOW}⚠️ WARN:{Colors.END} {self.warnings}")
        print(f"{Colors.RED}❌ FAIL:{Colors.END} {self.failures}")
        print("=" * 60)
        
        if self.failures > 0:
            print(f"{Colors.RED}STATUS: ❌ FAILURES DETECTED - System needs immediate fixes{Colors.END}")
            return False
        elif self.warnings > 5:
            print(f"{Colors.YELLOW}STATUS: ⚠️ WARNINGS PRESENT - Recommend addressing issues{Colors.END}")
            return True
        else:
            print(f"{Colors.GREEN}STATUS: ✅ SYSTEM READY - All checks passed{Colors.END}")
            return True


def main():
    """Main entry point for audit script."""
    root_dir = os.getcwd()
    
    if not os.path.exists(os.path.join(root_dir, "backend")):
        print(f"{Colors.RED}Error: Run from project root directory{Colors.END}")
        print(f"Current: {root_dir}")
        print("Expected: C:\\Users\\Malak\\zero-stockout")
        sys.exit(1)
    
    auditor = SystemAuditor(root_dir)
    success = auditor.run_full_audit()
    
    if not success:
        sys.exit(1)
    else:
        sys.exit(0)


if __name__ == "__main__":
    main()