# backend/agents/rag_agent.py
# JUMANA'S RAG AGENT

class RAGAgent:
    def __init__(self):
        self.router = RouterAgent()
    
    def query(self, question):
        return f'Answer from RAG system for: {question}'
    
    def get_context(self, product_id):
        return {'product': product_id, 'details': 'Context here'}

class RouterAgent:
    def classify(self, query):
        query_lower = query.lower()
        keywords = {
            'forecast': ['تنبؤ', 'نفاد', 'forecast', 'stockout', 'inventory'],
            'vision': ['صورة', 'طرد', 'image', 'package', 'damage'],
            'decision': ['اطلب', 'كمية', 'order', 'quantity', 'buy']
        }
        scores = {agent: 0 for agent in keywords}
        for agent, words in keywords.items():
            for word in words:
                if word in query_lower:
                    scores[agent] += 1
        best = max(scores, key=scores.get)
        return best if scores[best] > 0 else 'forecast'
