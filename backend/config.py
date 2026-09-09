# backend/config.py
"""Configuration management using environment variables."""

import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env file from root directory
env_path = Path(__file__).parent.parent / ".env"
load_dotenv(dotenv_path=env_path)


class Config:
    """Application configuration with environment variable support."""
    
    # ===== Database =====
    POSTGRES_USER: str = os.getenv("POSTGRES_USER", "oracle")
    POSTGRES_PASSWORD: str = os.getenv("POSTGRES_PASSWORD", "oraclepass")
    POSTGRES_DB: str = os.getenv("POSTGRES_DB", "inventory")
    POSTGRES_HOST: str = os.getenv("POSTGRES_HOST", "localhost")
    POSTGRES_PORT: str = os.getenv("POSTGRES_PORT", "5432")
    
    @property
    def POSTGRES_URL(self) -> str:
        """PostgreSQL connection URL."""
        return f"postgresql://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
    
    # ===== Redis =====
    REDIS_HOST: str = os.getenv("REDIS_HOST", "localhost")
    REDIS_PORT: str = os.getenv("REDIS_PORT", "6379")
    
    @property
    def REDIS_URL(self) -> str:
        """Redis connection URL."""
        return f"redis://{self.REDIS_HOST}:{self.REDIS_PORT}"
    
    # ===== Neo4j =====
    NEO4J_URI: str = os.getenv("NEO4J_URI", "bolt://localhost:7687")
    NEO4J_USER: str = os.getenv("NEO4J_USER", "neo4j")
    NEO4J_PASSWORD: str = os.getenv("NEO4J_PASSWORD", "neo4jpass")
    
    # ===== ChromaDB =====
    CHROMA_HOST: str = os.getenv("CHROMA_HOST", "localhost")
    CHROMA_PORT: str = os.getenv("CHROMA_PORT", "8001")
    
    @property
    def CHROMA_URL(self) -> str:
        """ChromaDB connection URL."""
        return f"http://{self.CHROMA_HOST}:{self.CHROMA_PORT}"
    
    # ===== API =====
    SECRET_KEY: str = os.getenv("SECRET_KEY", "dev-secret-key-change-in-production")
    DEBUG: bool = os.getenv("DEBUG", "True").lower() == "true"
    API_VERSION: str = "1.0.0"
    
    # ===== Cost Parameters =====
    HOLDING_COST: float = float(os.getenv("HOLDING_COST", "2.0"))
    STOCKOUT_COST: float = float(os.getenv("STOCKOUT_COST", "100.0"))
    SHIPPING_BASE: float = float(os.getenv("SHIPPING_BASE", "50.0"))
    SHIPPING_PER_UNIT: float = float(os.getenv("SHIPPING_PER_UNIT", "5.0"))


# Singleton instance
config = Config()


# ============================================================
# VALIDATION
# ============================================================
def validate_config():
    """Validate that all required configuration is present."""
    missing = []
    
    # Check critical values
    if config.POSTGRES_PASSWORD == "oraclepass" and config.DEBUG is False:
        print("⚠️  WARNING: Using default PostgreSQL password in production!")
    
    if config.SECRET_KEY == "dev-secret-key-change-in-production" and config.DEBUG is False:
        print("⚠️  WARNING: Using default SECRET_KEY in production!")
    
    if config.POSTGRES_HOST == "localhost":
        print("ℹ️  INFO: Running with local PostgreSQL (development mode)")
    
    return True


# Run validation on import
validate_config()


# ============================================================
# EXPORTS
# ============================================================
__all__ = ["config", "validate_config"]