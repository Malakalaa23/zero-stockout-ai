
import os
import sys
import io
from dotenv import load_dotenv

if sys.stdout.encoding != "utf-8":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8")

# ضيف سطرين دول عشان الملفات تلقى بعضها
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "src"))

from graph_mock import GraphMock
from chromadb_setup import get_collection, add_inventory_documents
from router_agent import RouterAgent
from llm_client import HuggingFaceLLM, MockLLM


load_dotenv()


def build_llm():
    try:
        if os.getenv("HF_API_KEY") or os.getenv("HUGGINGFACE_API_KEY"):
            print("Using HuggingFace Qwen LLM")
            return HuggingFaceLLM(
                model_name=os.getenv("HF_MODEL", "Qwen/Qwen2.5-1.5B-Instruct"),
                use_api=True,
            )
    except Exception as e:
        print(f"HuggingFace LLM failed: {e}")
    print("Using Mock LLM (set HF_API_KEY for real answers)")
    return MockLLM()


class ZeroStockoutAI:
    def __init__(self):
        print("=" * 60)
        print("ZERO-STOCKOUT AI SYSTEM")
        print("=" * 60)

        self.graph = GraphMock()
        print("GraphMock ready")

        self.chroma = get_collection("inventory_docs")
        add_inventory_documents(self.chroma)
        print(f"ChromaDB ready: {self.chroma.count()} docs")

        self.llm = build_llm()

        self.router = RouterAgent(self.graph, self.chroma, self.llm)
        print("Router Agent ready")
        print("=" * 60)

    def ask(self, question: str):
        return self.router.ask(question)

    def close(self):
        pass


if __name__ == "__main__":
    system = ZeroStockoutAI()

    test_questions = [
        "إيه المنتجات اللي هتنفد؟",
        "إيه سياسة إعادة الطلب؟",
        "اطلب كام وحدة من الهواتف؟",
    ]

    for q in test_questions:
        print(f"\n{'=' * 60}")
        print(f"سؤال: {q}")
        print("=" * 60)
        response = system.ask(q)
        print(f"التصنيف: {response.intent}")
        print(f"الإجابة:\n{response.answer}")
        if response.sources:
            print(f"\nالمصادر: {len(response.sources)} وثيقة")

    system.close()