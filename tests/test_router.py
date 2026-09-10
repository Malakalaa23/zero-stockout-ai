import unittest

from src.chromadb_setup import add_inventory_documents, get_collection
from src.graph_mock import GraphMock
from src.llm_client import MockLLM
from src.router_agent import RouterAgent


class RouterAgentTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        collection = get_collection("test_inventory_docs")
        add_inventory_documents(collection)
        cls.agent = RouterAgent(GraphMock(), collection, MockLLM())

    def test_classifies_inventory_forecast(self):
        self.assertEqual(self.agent.classify("ما المنتجات التي ستنفد؟"), "forecast")

    def test_classifies_reorder_decision(self):
        self.assertEqual(self.agent.classify("كمية الشراء وإعادة الطلب؟"), "decision")

    def test_returns_sources_and_answer(self):
        response = self.agent.ask("ما سياسة إعادة الطلب؟")
        self.assertEqual(response.intent, "policy")
        self.assertTrue(response.sources)
        self.assertIn("ما سياسة إعادة الطلب؟", response.answer)


if __name__ == "__main__":
    unittest.main()
