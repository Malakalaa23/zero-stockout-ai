# backend/agents/vision_agent.py
# NADA'S VISION AGENT

class VisionAgent:
    def __init__(self):
        self.model = None
        self.load_model()
    
    def load_model(self):
        self.model = None
    
    async def detect(self, image_file):
        return [{'class': 'package', 'confidence': 0.95}]
