# backend/agents/forecast_agent.py
# SARA'S FORECAST AGENT

class ForecastAgent:
    def __init__(self):
        self.model = None
        self.load_model()
    
    def load_model(self):
        self.model = None
    
    def predict(self, product_id, days):
        return [10, 15, 12, 18, 20, 14, 16][:days]
    
    def predict_vlt(self, product_id):
        return 3
