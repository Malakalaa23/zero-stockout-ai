"""Question router for the Zero Stockout assistant."""

from __future__ import annotations

from dataclasses import dataclass
from .graphrag import GraphRAG


@dataclass(frozen=True)
class RouterResponse:
    intent: str
    answer: str


class InventoryRouter:
    def __init__(self, graph: GraphRAG) -> None:
        self.graph = graph

    def classify(self, question: str) -> str:
        text = question.lower()
        if any(word in text for word in ("stock", "inventory", "available", "reorder", "sku")):
            return "inventory"
        if any(word in text for word in ("supplier", "vendor", "relationship", "depends")):
            return "graph"
        return "unknown"

    def ask(self, question: str) -> RouterResponse:
        intent = self.classify(question)
        if intent == "inventory":
            low_inventory = self.graph.get_low_inventory_products()
            if "low" in question.lower() or "reorder" in question.lower():
                answer = "\n".join(str(item) for item in low_inventory) or "No low inventory products found."
                return RouterResponse(intent, answer)
            return RouterResponse(intent, "Use a product, SKU, or warehouse query for inventory details.")
        if intent == "graph":
            return RouterResponse(intent, "Graph relationships are available through the Neo4j AuraDB knowledge graph.")
        return RouterResponse(intent, "Ask me about stock levels, reorder points, SKUs, or suppliers.")
