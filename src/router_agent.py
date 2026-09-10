"""Intent routing and grounded retrieval for inventory questions."""

from dataclasses import dataclass
import re
from typing import Dict, List, Optional


@dataclass
class RouterResponse:
    intent: str
    answer: str
    sources: Optional[List[Dict]] = None


class RouterAgent:
    KEYWORDS = {
        "forecast": (
            "future", "forecast", "inventory", "stockout", "run out", "running out",
            "low stock", "low inventory", "below reorder point", "below the reorder point",
            "shortage", "out of stock",
        ),
        "vision": ("image", "package", "damage", "picture", "photo"),
        "policy": (
            "policy", "contract", "rule", "cost", "shipping", "storage",
            "stockout cost", "delivery", "return", "dhl",
        ),
        "decision": ("order", "quantity", "buy", "how many", "reorder"),
        "graph": ("supplier", "vendor", "who supplies"),
    }

    def __init__(self, graph, chroma_collection, llm=None):
        self.graph = graph
        self.chroma = chroma_collection
        self.llm = llm

    def classify(self, question: str) -> str:
        q = question.lower()
        if any(self._contains_term(q, word) for word in self.KEYWORDS["vision"]):
            return "vision"
        if any(self._contains_term(q, word) for word in self.KEYWORDS["graph"]):
            return "graph"
        if any(self._contains_term(q, word) for word in self.KEYWORDS["policy"]):
            return "policy"
        if any(self._contains_term(q, word) for word in self.KEYWORDS["forecast"]):
            return "forecast"
        if any(self._contains_term(q, word) for word in self.KEYWORDS["decision"]):
            return "decision"
        return "out_of_scope"

    @staticmethod
    def _contains_term(text: str, term: str) -> bool:
        return re.search(rf"(?<!\w){re.escape(term.lower())}(?!\w)", text) is not None

    def ask(self, question: str) -> RouterResponse:
        intent = self.classify(question)
        if intent == "out_of_scope":
            return RouterResponse(
                intent=intent,
                answer="This question is outside the scope of the inventory system. Ask about stock, suppliers, costs, delivery, or reorder policies.",
                sources=[],
            )
        retrieved_docs = self._retrieve_from_chroma(question)
        graph_data = self._retrieve_from_graph(intent, question)
        if intent == "forecast" and graph_data.get("low_inventory"):
            return RouterResponse(
                intent=intent,
                answer=self._format_answer(retrieved_docs, graph_data),
                sources=retrieved_docs,
            )
        if self.llm is not None:
            try:
                answer = self._generate_answer(question, retrieved_docs, graph_data)
            except Exception as exc:
                print(f"LLM unavailable; using grounded fallback: {exc}")
                answer = self._format_answer(retrieved_docs, graph_data)
        else:
            answer = self._format_answer(retrieved_docs, graph_data)
        return RouterResponse(intent=intent, answer=answer, sources=retrieved_docs)

    def _retrieve_from_chroma(self, question: str) -> List[Dict]:
        try:
            from .chromadb_setup import search
        except ImportError:
            from chromadb_setup import search
        return search(self.chroma, question, n_results=5)

    def _retrieve_from_graph(self, intent: str, question: str) -> Dict:
        if intent == "forecast":
            return {"low_inventory": self.graph.get_low_inventory()}
        if intent == "decision":
            return {"products": self.graph.get_all_products()[:5]}
        if intent == "graph":
            product_id = self._product_id(question)
            if product_id:
                return {"relationship": self.graph.get_product_relationships(product_id)}
        return {}

    @staticmethod
    def _product_id(question: str) -> Optional[str]:
        q = question.lower()
        products = {
            "P001": ("shoe",),
            "P002": ("tv", "television"),
            "P003": ("fridge",),
            "P004": ("laptop",),
            "P005": ("phone", "phones"),
        }
        for product_id, names in products.items():
            if any(name in q for name in names):
                return product_id
        return None

    def _format_answer(self, docs: List[Dict], graph_data: Dict) -> str:
        parts = []
        if graph_data.get("low_inventory"):
            parts.append("Low inventory products:")
            parts.extend(
                f"- {item['product']}: {item['current']}/{item['reorder_point']}"
                for item in graph_data["low_inventory"]
            )
        relationship = graph_data.get("relationship")
        if relationship:
            parts.append(f"{relationship['product']} suppliers: {', '.join(relationship['suppliers']) or 'none'}")
        if docs:
            parts.append("Relevant information:")
            parts.extend(f"- {doc['text']}" for doc in docs[:2])
        return "\n".join(parts) if parts else "No grounded information found."

    def _generate_answer(self, question: str, docs: List[Dict], graph_data: Dict) -> str:
        context_parts = []
        if graph_data.get("low_inventory"):
            context_parts.append("LOW INVENTORY DATA:")
            context_parts.extend(
                f"{item['product']}: current={item['current']}, reorder_point={item['reorder_point']}"
                for item in graph_data["low_inventory"]
            )
        if graph_data.get("relationship"):
            relationship = graph_data["relationship"]
            context_parts.append(
                f"GRAPH: {relationship['product']} suppliers={', '.join(relationship['suppliers'])}"
            )
        context_parts.extend(f"REFERENCE: {doc['text']}" for doc in docs)
        context = "\n".join(context_parts) or "No data."
        prompt = f"""You are an inventory assistant. Answer only from this context. Do not invent facts.
    Always answer in English and include exact numbers and names when present.

CONTEXT:
{context}

QUESTION: {question}

ANSWER:"""
        return self.llm.generate(prompt)
