import unittest
import json
from fastapi.testclient import TestClient
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from main import app

class TestAPIIntegration(unittest.TestCase):
    def setUp(self):
        """Set up test client"""
        self.client = TestClient(app)
    
    def test_health_endpoint(self):
        """Test health check"""
        response = self.client.get("/health")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"status": "healthy"})
    
    def test_decision_endpoint(self):
        """Test decision prediction"""
        test_data = {
            "demand_forecast": [10, 15, 12, 18, 20, 14, 16],
            "current_stock": 30,
            "days": 7,
            "cost_params": {
                "holding": 2.0,
                "stockout": 100.0,
                "shipping_base": 50.0,
                "shipping_per_unit": 5.0
            }
        }
        
        response = self.client.post("/predict/decision", json=test_data)
        self.assertEqual(response.status_code, 200)
        
        data = response.json()
        self.assertIn("optimal_quantity", data)
        self.assertIn("total_cost", data)
        self.assertIsInstance(data["optimal_quantity"], (int, float))
        self.assertIsInstance(data["total_cost"], (int, float))
    
    def test_decision_invalid_input(self):
        """Test decision with invalid input"""
        # Missing demand_forecast
        test_data = {
            "current_stock": 30,
            "days": 7
        }
        
        response = self.client.post("/predict/decision", json=test_data)
        self.assertEqual(response.status_code, 422)  # Validation error
    
    def test_forecast_endpoint(self):
        """Test forecast prediction"""
        test_data = {
            "product_id": "P001",
            "days": 7
        }
        
        response = self.client.post("/predict/forecast", json=test_data)
        self.assertEqual(response.status_code, 200)
        
        data = response.json()
        self.assertIn("forecast", data)
        self.assertIn("product_id", data)
    
    def test_full_pipeline(self):
        """Test full end-to-end pipeline"""
        test_data = {
            "product_id": "P001",
            "demand_forecast": [10, 15, 12, 18, 20, 14, 16],
            "current_stock": 30,
            "days": 7,
            "cost_params": {
                "holding": 2.0,
                "stockout": 100.0,
                "shipping_base": 50.0,
                "shipping_per_unit": 5.0
            }
        }
        
        response = self.client.post("/predict/full", json=test_data)
        self.assertEqual(response.status_code, 200)
        
        data = response.json()
        self.assertIn("forecast", data)
        self.assertIn("decision", data)

if __name__ == '__main__':
    unittest.main()