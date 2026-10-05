
import os
import sys
import io
from dotenv import load_dotenv

if sys.stdout.encoding != "utf-8":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8")


sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "src"))

from graph_mock import GraphMock
from chromadb_setup import get_collection, add_inventory_documents
from router_agent import RouterAgent
from llm_client import HuggingFaceLLM


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
    print("Using grounded RAG fallback (LLM unavailable)")
    return None


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

    if len(sys.argv) > 1 and sys.argv[1] == "--demo":
        questions = [
            "What products are currently below their reorder point?",
            "What is the reorder policy?",
            "What is the shipping cost?",
            "What is the storage cost per unit?",
            "How long does DHL take to deliver?",
            "Who is the supplier for the TV?",
            "How many units should I order for phones?",
        ]
    else:
        question = " ".join(sys.argv[1:]).strip()
        questions = [question or input("Inventory question: ").strip()]

    for q in questions:
        if not q:
            continue
        print(f"\n{'=' * 60}")
        print(f"Question: {q}")
        print("=" * 60)
        response = system.ask(q)
        print(f"Intent: {response.intent}")
        print(f"Answer:\n{response.answer}")
        if response.sources:
            print(f"\nSources: {len(response.sources)} documents")

    system.close()