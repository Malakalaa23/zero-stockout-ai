# backend/main.py

"""Zero-Stockout AI - Main Application Entry Point"""

import uvicorn
import os
import sys

# Add current directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))
    host = os.getenv("HOST", "0.0.0.0")
    
    print("=" * 60)
    print("🔷 ZERO-STOCKOUT AI SYSTEM")
    print("=" * 60)
    print(f"📡 Starting server at: http://{host}:{port}")
    print(f"📚 API Documentation: http://{host}:{port}/docs")
    print("=" * 60)
    
    uvicorn.run(
        "api.routes:app",
        host=host,
        port=port,
        reload=True,
        log_level="info"
    )