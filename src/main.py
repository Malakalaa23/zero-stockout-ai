"""
main.py - Complete Zero-Stockout AI System
Jumana's RAG & Knowledge Graph Implementation (GraphMock Version)
"""

import io
import os
import sys
import tempfile
from dotenv import load_dotenv
import chromadb
import json
from graph_mock import GraphMock

load_dotenv()

class ZeroStockoutAI:
    """
    Complete system combining:
    1. GraphMock (بديل Neo4j)
    2. ChromaDB Vector Database
    3. Router Agent (NLP Classification)
    4. GraphRAG Pipeline
    """
    
    def __init__(self):
        
        
        # === 1. INITIALIZE GRAPHMOCK ===
        print("\n📊 Initializing GraphMock (No database needed!)")
        self.graph = GraphMock()
        print("✅ GraphMock ready!")
        
        # === 2. CONNECT TO CHROMADB ===
        try:
            # استخدام مجلد مؤقت عشان نوفر مساحة
            temp_dir = tempfile.mkdtemp()
            print(f"📁 Using temp directory: {temp_dir}")
            
            self.chroma_client = chromadb.PersistentClient(
                path=temp_dir
            )
            self.chroma_collection = self.chroma_client.get_or_create_collection(
                name="inventory_docs",
                metadata={"hnsw:space": "cosine"}
            )
            print(f"✅ ChromaDB: Connected! Collection: {self.chroma_collection.name}")
        except Exception as e:
            print(f"❌ ChromaDB error: {e}")
            sys.exit(1)
        
        print("✅ All systems initialized!\n")
    
    # =========================================
    # PART 1: KNOWLEDGE GRAPH (GraphMock)
    # =========================================
    def create_knowledge_graph(self):
        """Create the complete Knowledge Graph"""
        print("\n" + "="*60)
        print("📊 PART 1: CREATING KNOWLEDGE GRAPH")
        print("="*60)
        
        print("✅ Knowledge Graph already exists in GraphMock!")
        print("   ✅ 20 entities: 5 Warehouses, 10 Products, 5 Suppliers, 5 Carriers")
        print("   ✅ Relationships: STORED_AT, SUPPLIED_BY, SHIPPED_BY")
        
        # Show some stats
        all_nodes = self.graph.graph["nodes"]
        all_rels = self.graph.graph["relationships"]
        print(f"   📦 Nodes: {len(all_nodes)}")
        print(f"   🔗 Relationships: {len(all_rels)}")
    
    # =========================================
    # PART 2: ADD DOCUMENTS TO CHROMADB
    # =========================================
    def add_inventory_documents(self):
        """Add business rules and policies to ChromaDB"""
        print("\n" + "="*60)
        print("📄 PART 2: ADDING DOCUMENTS TO CHROMADB")
        print("="*60)
        
        documents = [
            "سياسة إعادة الطلب: يتم إعادة الطلب تلقائياً عندما يصل المخزون إلى 30 وحدة أو أقل",
            "المورد DHL: يوصل خلال 2-3 أيام عمل، تكلفة الشحن 50 دولار لكل شحنة",
            "المورد البديل المحلي: يوصل خلال 24 ساعة، تكلفة الشحن 100 دولار للشحنة",
            "تكلفة الشحن: 50 دولار لكل شحنة + 5 دولار لكل وحدة",
            "تكلفة التخزين: 2 دولار لكل وحدة في اليوم",
            "تكلفة نفاد المخزون: 100 دولار لكل وحدة مفقودة",
            "المنتجات الأكثر مبيعاً: الهواتف، اللابتوبات، وأجهزة التلفزيون",
            "سياسة الإرجاع: يمكن إرجاع المنتجات خلال 14 يوماً من الشراء",
            "المخزون الآمن: يجب أن يكون 30% من الحد الأقصى للطلب الشهري",
            "أوقات التسليم: DHL 2-3 أيام، FedEx 3 أيام، Aramex 2 أيام"
        ]
        
        existing = self.chroma_collection.count()
        
        if existing > 0:
            print(f"⚠️  ChromaDB already has {existing} documents")
            print("   Skipping re-add...")
            return
        
        ids = [f"doc_{i}" for i in range(len(documents))]
        self.chroma_collection.add(documents=documents, ids=ids)
        print(f"✅ Added {len(documents)} documents to ChromaDB")
    
    # =========================================
    # PART 3: ROUTER AGENT (NLP Classification)
    # =========================================
    def classify_query(self, query):
        """Router Agent - Classify user question"""
        print("\n" + "="*60)
        print("🤖 PART 3: ROUTER AGENT - NLP CLASSIFICATION")
        print("="*60)
        
        # Keywords for each agent
        keywords = {
            'forecast': ['تنبؤ', 'نفاد', 'مخزون', 'توقع', 'طلب', 'future', 'forecast', 'inventory'],
            'vision': ['صورة', 'طرد', 'تلف', 'كاميرا', 'image', 'package', 'damage'],
            'rag': ['سياسة', 'مورد', 'عقد', 'قواعد', 'policy', 'supplier', 'contract', 'info'],
            'decision': ['اطلب', 'كمية', 'طلب', 'شراء', 'order', 'quantity', 'buy', 'purchase']
        }
        
        query_lower = query.lower()
        scores = {}
        
        for agent, words in keywords.items():
            score = sum(1 for word in words if word in query_lower)
            scores[agent] = score
        
        best_agent = max(scores, key=scores.get)
        best_score = scores[best_agent]
        
        if best_score == 0:
            best_agent = 'rag'
            best_score = 0
        
        print(f"❓ Query: {query}")
        print(f"📊 Scores: {scores}")
        print(f"🎯 Routed to: {best_agent.upper()} (score: {best_score})")
        
        return best_agent
    
    # =========================================
    # PART 4: GRAPHRAG RETRIEVAL
    # =========================================
    def graphrag_retrieve(self, query):
        """GraphRAG: Combine GraphMock + ChromaDB retrieval"""
        print("\n" + "="*60)
        print("🔍 PART 4: GRAPHRAG RETRIEVAL")
        print("="*60)
        
        # === 4.1: ChromaDB Semantic Search ===
        print("\n📌 4.1: ChromaDB Semantic Search")
        chroma_results = self.chroma_collection.query(
            query_texts=[query],
            n_results=2
        )
        
        if chroma_results and chroma_results['documents']:
            for i, doc in enumerate(chroma_results['documents'][0]):
                print(f"   📄 Match {i+1}: {doc[:80]}...")
        else:
            print("   ❌ No ChromaDB results")
        
        # === 4.2: GraphMock Graph Queries ===
        print("\n📌 4.2: GraphMock Graph Queries")
        
        # Query 1: Low inventory products
        low_results = self.graph.get_low_inventory()
        
        if low_results:
            print("   ⚠️ Low Inventory Products:")
            for item in low_results[:3]:
                print(f"      - {item['product']}: {item['current']}/{item['reorder_point']}")
        else:
            print("   ✅ No low inventory products")
        
        # Query 2: Product relationships
        products = self.graph.get_all_products()
        if products:
            sample_product = products[0]
            product_id = sample_product['id']
            
            relationships = self.graph.get_product_relationships(product_id)
            print(f"\n   📦 Sample Product: {relationships['product']} ({product_id})")
            
            if relationships.get('suppliers'):
                print(f"      Suppliers: {', '.join(relationships['suppliers'])}")
            if relationships.get('warehouses'):
                print(f"      Warehouse: {', '.join(relationships['warehouses'])}")
            if relationships.get('carriers'):
                print(f"      Carriers: {', '.join(relationships['carriers'])}")
    
    # =========================================
    # PART 5: RUN COMPLETE DEMO
    # =========================================
    def run_demo(self):
        """Run the complete demonstration"""
        print("\n" + "="*60)
        print("🎯 PART 5: COMPLETE DEMONSTRATION")
        print("="*60)
        
        # Test queries
        test_queries = [
            "إيه المنتجات اللي هتنفد؟",
            "إيه سياسة إعادة الطلب؟",
            "اطلب كام وحدة من الهواتف؟"
        ]
        
        for query in test_queries:
            print("\n" + "-"*40)
            print(f"💬 User: {query}")
            
            # Step 1: Classify
            agent = self.classify_query(query)
            
            # Step 2: Retrieve using GraphRAG
            self.graphrag_retrieve(query)
            
            print(f"\n✅ Handled by: {agent.upper()} Agent")
    
    # =========================================
    # SYSTEM STATS
    # =========================================
    def get_system_stats(self):
        """Get system statistics"""
        print("\n" + "="*60)
        print("📊 SYSTEM STATISTICS")
        print("="*60)
        
        # GraphMock stats
        all_nodes = self.graph.graph["nodes"]
        all_rels = self.graph.graph["relationships"]
        
        print(f"📦 GraphMock Nodes: {len(all_nodes)}")
        print(f"🔗 GraphMock Relationships: {len(all_rels)}")
        
        # Count by type
        node_types = {}
        for node in all_nodes:
            node_type = node.get("type", "Unknown")
            node_types[node_type] = node_types.get(node_type, 0) + 1
        
        print("\n📂 Nodes by Type:")
        for node_type, count in node_types.items():
            print(f"   {node_type}: {count}")
        
        # Products by category
        products = self.graph.get_all_products()
        categories = {}
        for p in products:
            cat = p.get("category", "Unknown")
            categories[cat] = categories.get(cat, 0) + 1
        
        print("\n📂 Products by Category:")
        for cat, count in categories.items():
            print(f"   {cat}: {count}")
        
        # ChromaDB stats
        chroma_count = self.chroma_collection.count()
        print(f"\n📄 ChromaDB Documents: {chroma_count}")
    
    # =========================================
    # CLOSE
    # =========================================
    def close(self):
        """Close all connections"""
        if hasattr(self, 'graph') and self.graph:
            self.graph.close()
            print("\n✅ GraphMock closed")


# =========================================
# 🚀 MAIN EXECUTION
# =========================================
if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    print("🚀 Starting Zero-Stockout AI System...\n")
    
    # Initialize system
    system = ZeroStockoutAI()
    
    try:
        # Step 1: Create Knowledge Graph
        system.create_knowledge_graph()
        
        # Step 2: Add documents to ChromaDB
        system.add_inventory_documents()
        
        # Step 3: Show system stats
        system.get_system_stats()
        
        # Step 4: Run demo
        system.run_demo()
        
        print("\n" + "="*60)
        print("✅ DEMO COMPLETE!")
        print("="*60)
        print("""
        📚 WHAT WE BUILT:
        1. GraphMock (Neo4j replacement) with 20+ entities
        2. ChromaDB vector database with 10 documents
        3. Router Agent for NLP classification
        4. GraphRAG pipeline combining both systems
        
        🎯 KEY FEATURES:
        - Semantic search (ChromaDB)
        - Graph traversal (GraphMock)
        - NLP classification (Router Agent)
        - Arabic language support
        - No database installation required!
        """)
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        system.close()