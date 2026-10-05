"""Optional Neo4j integration."""

from __future__ import annotations

import os


def get_driver():
    try:
        from neo4j import GraphDatabase
    except ImportError as exc:
        raise RuntimeError("Install neo4j to use the graph database integration.") from exc
    return GraphDatabase.driver(
        os.getenv("NEO4J_URI", "bolt://localhost:7687"),
        auth=(os.getenv("NEO4J_USER", "neo4j"), os.getenv("NEO4J_PASSWORD", "inventory")),
    )
