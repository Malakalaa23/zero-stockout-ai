"""Persistent local ChromaDB setup."""

from __future__ import annotations

import os
from pathlib import Path


def get_collection(name: str = "inventory_docs", data_dir: str | Path | None = None):
    try:
        import chromadb
    except ImportError as exc:
        raise RuntimeError("Install chromadb to use the vector store integration.") from exc
    storage_path = Path(data_dir or os.getenv("CHROMA_DATA_DIR", "chroma_data"))
    storage_path.mkdir(parents=True, exist_ok=True)
    client = chromadb.PersistentClient(path=str(storage_path))
    return client.get_or_create_collection(name)
