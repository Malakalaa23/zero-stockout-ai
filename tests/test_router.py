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
        self.assertEqual(self.agent.classify("What products will run out?"), "forecast")

    def test_classifies_reorder_decision(self):
        self.assertEqual(self.agent.classify("What quantity should I reorder?"), "decision")

    def test_classifies_tv_supplier_as_graph(self):
        self.assertEqual(self.agent.classify("Who is the supplier for the television?"), "graph")

    def test_returns_sources_and_answer(self):
        response = self.agent.ask("What is the reorder policy?")
        self.assertEqual(response.intent, "policy")
        self.assertTrue(response.sources)
        self.assertIn("What is the reorder policy?", response.answer)

    def test_rejects_out_of_scope_question(self):
        response = self.agent.ask("What is the weather today?")
        self.assertEqual(response.intent, "out_of_scope")
        self.assertIn("outside the scope", response.answer)
        self.assertEqual(response.sources, [])


if __name__ == "__main__":
    unittest.main()
