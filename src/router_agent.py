from dataclasses import dataclass
from typing import Dict, List, Optional


@dataclass
class RouterResponse:
    intent: str
    answer: str
    sources: Optional[List[Dict]] = None


class RouterAgent:
    KEYWORDS = {
        "forecast": ["تنبؤ", "نفاد", "نفد", "تنفد", "مخزون", "توقع", "future", "forecast", "inventory", "stockout"],
        "vision": ["صورة", "طرد", "تلف", "كاميرا", "image", "package", "damage"],
        "policy": ["سياسة", "مورد", "عقد", "قواعد", "policy", "supplier", "contract"],
        "decision": ["اطلب", "كمية", "شراء", "order", "quantity", "buy", "reorder"],
    }

    def __init__(self, graph, chroma_collection, llm=None):
        self.graph = graph
        self.chroma = chroma_collection
        self.llm = llm

    def classify(self, question: str) -> str:
        q = question.lower()
        scores = {intent: 0 for intent in self.KEYWORDS}
        for intent, words in self.KEYWORDS.items():
            scores[intent] = sum(1 for w in words if w in q)

        best = max(scores, key=scores.get)
        return best if scores[best] > 0 else "policy"

    def ask(self, question: str) -> RouterResponse:
        intent = self.classify(question)
        retrieved_docs = self._retrieve_from_chroma(question)
        graph_data = self._retrieve_from_graph(intent)

        if self.llm is not None:
            try:
                answer = self._generate_answer(question, retrieved_docs, graph_data)
            except Exception as exc:
                print(f"LLM unavailable; using grounded fallback: {exc}")
                answer = self._format_answer(intent, retrieved_docs, graph_data)
        else:
            answer = self._format_answer(intent, retrieved_docs, graph_data)

        return RouterResponse(intent=intent, answer=answer, sources=retrieved_docs)

    def _retrieve_from_chroma(self, question: str) -> List[Dict]:
        try:
            from .chromadb_setup import search
        except ImportError:
            from chromadb_setup import search
        return search(self.chroma, question, n_results=3)

    def _retrieve_from_graph(self, intent: str) -> Dict:
        if intent == "forecast":
            return {"low_inventory": self.graph.get_low_inventory()}
        elif intent == "decision":
            products = self.graph.get_all_products()
            return {"products": products[:5]}
        return {}

    def _format_answer(self, intent: str, docs: List[Dict], graph_data: Dict) -> str:
        parts = []

        if graph_data.get("low_inventory"):
            parts.append("منتجات على وشك النفاد:")
            for item in graph_data["low_inventory"][:3]:
                parts.append(f"  - {item['product']}: {item['current']}/{item['reorder_point']}")

        if docs:
            parts.append("\nمعلومات ذات صلة:")
            for d in docs[:2]:
                parts.append(f"  - {d['text']}")

        return "\n".join(parts) if parts else "لا توجد معلومات متاحة."

    def _generate_answer(self, question: str, docs: List[Dict], graph_data: Dict) -> str:
        context = "\n".join([d["text"] for d in docs])
        if graph_data.get("low_inventory"):
            context += "\n" + "\n".join(
                f"{i['product']}: {i['current']}/{i['reorder_point']}"
                for i in graph_data["low_inventory"]
            )

        prompt = f"""أنت مساعد ذكي لإدارة المخزون. أجب على السؤال بناءً على السياق فقط.

السياق:
{context}

السؤال: {question}

الإجابة (بالعربية):"""

        return self.llm.generate(prompt)