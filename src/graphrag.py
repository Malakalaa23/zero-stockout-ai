"""
graphrag.py - Jumana's GraphRAG Pipeline (with Neo4j AuraDB)
"""

from neo4j import GraphDatabase
import chromadb
from chromadb.config import Settings
from typing import List, Dict, Any, Optional
import os
from dotenv import load_dotenv

# Load environment variables from .env
load_dotenv()

class GraphRAG:
    """
    GraphRAG system using:
    1. Neo4j AuraDB (cloud - no Docker needed!)
    2. ChromaDB (local vector database)
    """
    
    def __init__(self):
        # ===== CONNECT TO NEO4J AURADB =====
        # Get connection details from .env file
        self.neo4j_uri = os.getenv("NEO4J_URI")
        self.neo4j_user = os.getenv("NEO4J_USERNAME", "neo4j")
        self.neo4j_password = os.getenv("NEO4J_PASSWORD")
        
        if not self.neo4j_uri or not self.neo4j_password:
            raise ValueError("""
            ❌ Neo4j credentials not found!
            Create a .env file with:
            NEO4J_URI=neo4j+s://xxxxxx.databases.neo4j.io
            NEO4J_PASSWORD=your_password
            """)
        
        # Connect to Neo4j AuraDB
        try:
            self.neo4j_driver = GraphDatabase.driver(
                self.neo4j_uri,
                auth=(self.neo4j_user, self.neo4j_password)
            )
            # Test connection
            with self.neo4j_driver.session() as session:
                result = session.run("RETURN 1 AS test")
                test = result.single()["test"]
                print(f"✅ Neo4j AuraDB connected successfully! (test: {test})")
        except Exception as e:
            print(f"❌ Failed to connect to Neo4j AuraDB: {e}")
            raise
        
        # ===== CONNECT TO CHROMADB =====
        # ChromaDB in-process (no Docker needed)
        try:
            self.chroma_client = chromadb.PersistentClient(
                path="./chroma_data"
            )
            self.chroma_collection = self.chroma_client.get_or_create_collection(
                name="inventory_docs"
            )
            print(f"✅ ChromaDB connected! Collection: {self.chroma_collection.name}")
        except Exception as e:
            print(f"❌ Failed to connect to ChromaDB: {e}")
            raise
        
        print("✅ GraphRAG initialized with Neo4j AuraDB + ChromaDB")
    
    def close(self):
        """Close Neo4j connection"""
        if self.neo4j_driver:
            self.neo4j_driver.close()
            print("✅ Neo4j connection closed")
    
    # ===== NEO4J QUERIES =====
    def query_graph(self, cypher_query: str, params: Dict = None) -> List[Dict]:
        """
        Execute a Cypher query on Neo4j and return results.
        """
        with self.neo4j_driver.session() as session:
            result = session.run(cypher_query, params or {})
            return [record.data() for record in result]
    
    def create_knowledge_graph(self):
        """
        Create the complete Knowledge Graph in Neo4j AuraDB.
        Run this once to populate your cloud database.
        """
        print("📦 Creating Knowledge Graph in Neo4j AuraDB...")
        
        queries = [
            # === WAREHOUSES ===
            """
            MERGE (w1:Warehouse {id: 'WH001', name: 'العبور', location: 'القاهرة', capacity: 1000})
            MERGE (w2:Warehouse {id: 'WH002', name: 'أكتوبر', location: 'الجيزة', capacity: 800})
            MERGE (w3:Warehouse {id: 'WH003', name: 'العاصمة', location: 'القاهرة', capacity: 1200})
            MERGE (w4:Warehouse {id: 'WH004', name: 'الإسكندرية', location: 'الإسكندرية', capacity: 600})
            MERGE (w5:Warehouse {id: 'WH005', name: 'بورسعيد', location: 'بورسعيد', capacity: 400})
            """,
            
            # === PRODUCTS ===
            """
            MERGE (p1:Product {id: 'P001', name: 'حذاء رياضي', category: 'أحذية', base_price: 200})
            MERGE (p2:Product {id: 'P002', name: 'تلفزيون', category: 'إلكترونيات', base_price: 5000})
            MERGE (p3:Product {id: 'P003', name: 'ثلاجة', category: 'أجهزة منزلية', base_price: 8000})
            MERGE (p4:Product {id: 'P004', name: 'لابتوب', category: 'إلكترونيات', base_price: 25000})
            MERGE (p5:Product {id: 'P005', name: 'هاتف', category: 'إلكترونيات', base_price: 12000})
            MERGE (p6:Product {id: 'P006', name: 'جهاز لوحي', category: 'إلكترونيات', base_price: 8000})
            MERGE (p7:Product {id: 'P007', name: 'غسالة', category: 'أجهزة منزلية', base_price: 9000})
            MERGE (p8:Product {id: 'P008', name: 'مكيف', category: 'أجهزة منزلية', base_price: 7000})
            MERGE (p9:Product {id: 'P009', name: 'ساعة', category: 'إكسسوارات', base_price: 500})
            MERGE (p10:Product {id: 'P010', name: 'لعبة', category: 'ألعاب', base_price: 100})
            """,
            
            # === SUPPLIERS ===
            """
            MERGE (s1:Supplier {id: 'SUP001', name: 'المورد العربي', location: 'دبي'})
            MERGE (s2:Supplier {id: 'SUP002', name: 'Global Trade Co', location: 'الصين'})
            MERGE (s3:Supplier {id: 'SUP003', name: 'Fast Supply', location: 'تركيا'})
            MERGE (s4:Supplier {id: 'SUP004', name: 'مصر للمنتجات', location: 'القاهرة'})
            MERGE (s5:Supplier {id: 'SUP005', name: 'Tech Import', location: 'ألمانيا'})
            """,
            
            # === CARRIERS ===
            """
            MERGE (c1:Carrier {id: 'CAR001', name: 'DHL', avg_days: 2})
            MERGE (c2:Carrier {id: 'CAR002', name: 'FedEx', avg_days: 3})
            MERGE (c3:Carrier {id: 'CAR003', name: 'Aramex', avg_days: 2})
            MERGE (c4:Carrier {id: 'CAR004', name: 'UPS', avg_days: 4})
            MERGE (c5:Carrier {id: 'CAR005', name: 'النقل البري', avg_days: 1})
            """,
            
            # === INVENTORY ===
            """
            MERGE (i1:Inventory {product_id: 'P001', warehouse_id: 'WH001', quantity: 50, reorder_point: 30})
            MERGE (i2:Inventory {product_id: 'P002', warehouse_id: 'WH002', quantity: 20, reorder_point: 15})
            MERGE (i3:Inventory {product_id: 'P003', warehouse_id: 'WH003', quantity: 10, reorder_point: 8})
            MERGE (i4:Inventory {product_id: 'P004', warehouse_id: 'WH004', quantity: 35, reorder_point: 20})
            MERGE (i5:Inventory {product_id: 'P005', warehouse_id: 'WH005', quantity: 60, reorder_point: 40})
            MERGE (i6:Inventory {product_id: 'P006', warehouse_id: 'WH001', quantity: 25, reorder_point: 15})
            MERGE (i7:Inventory {product_id: 'P007', warehouse_id: 'WH002', quantity: 5, reorder_point: 10})
            MERGE (i8:Inventory {product_id: 'P008', warehouse_id: 'WH003', quantity: 45, reorder_point: 30})
            MERGE (i9:Inventory {product_id: 'P009', warehouse_id: 'WH004', quantity: 100, reorder_point: 50})
            MERGE (i10:Inventory {product_id: 'P010', warehouse_id: 'WH005', quantity: 80, reorder_point: 60})
            """,
            
            # === RELATIONSHIPS: Products → Warehouses ===
            """
            MATCH (p:Product {id: 'P001'}), (w:Warehouse {id: 'WH001'}) MERGE (p)-[:STORED_AT]->(w)
            MATCH (p:Product {id: 'P002'}), (w:Warehouse {id: 'WH002'}) MERGE (p)-[:STORED_AT]->(w)
            MATCH (p:Product {id: 'P003'}), (w:Warehouse {id: 'WH003'}) MERGE (p)-[:STORED_AT]->(w)
            MATCH (p:Product {id: 'P004'}), (w:Warehouse {id: 'WH004'}) MERGE (p)-[:STORED_AT]->(w)
            MATCH (p:Product {id: 'P005'}), (w:Warehouse {id: 'WH005'}) MERGE (p)-[:STORED_AT]->(w)
            MATCH (p:Product {id: 'P006'}), (w:Warehouse {id: 'WH001'}) MERGE (p)-[:STORED_AT]->(w)
            MATCH (p:Product {id: 'P007'}), (w:Warehouse {id: 'WH002'}) MERGE (p)-[:STORED_AT]->(w)
            MATCH (p:Product {id: 'P008'}), (w:Warehouse {id: 'WH003'}) MERGE (p)-[:STORED_AT]->(w)
            MATCH (p:Product {id: 'P009'}), (w:Warehouse {id: 'WH004'}) MERGE (p)-[:STORED_AT]->(w)
            MATCH (p:Product {id: 'P010'}), (w:Warehouse {id: 'WH005'}) MERGE (p)-[:STORED_AT]->(w)
            """,
            
            # === RELATIONSHIPS: Products → Suppliers ===
            """
            MATCH (p:Product {id: 'P001'}), (s:Supplier {id: 'SUP001'}) MERGE (p)-[:SUPPLIED_BY]->(s)
            MATCH (p:Product {id: 'P002'}), (s:Supplier {id: 'SUP002'}) MERGE (p)-[:SUPPLIED_BY]->(s)
            MATCH (p:Product {id: 'P003'}), (s:Supplier {id: 'SUP003'}) MERGE (p)-[:SUPPLIED_BY]->(s)
            MATCH (p:Product {id: 'P004'}), (s:Supplier {id: 'SUP005'}) MERGE (p)-[:SUPPLIED_BY]->(s)
            MATCH (p:Product {id: 'P005'}), (s:Supplier {id: 'SUP002'}) MERGE (p)-[:SUPPLIED_BY]->(s)
            MATCH (p:Product {id: 'P006'}), (s:Supplier {id: 'SUP005'}) MERGE (p)-[:SUPPLIED_BY]->(s)
            MATCH (p:Product {id: 'P007'}), (s:Supplier {id: 'SUP004'}) MERGE (p)-[:SUPPLIED_BY]->(s)
            MATCH (p:Product {id: 'P008'}), (s:Supplier {id: 'SUP003'}) MERGE (p)-[:SUPPLIED_BY]->(s)
            MATCH (p:Product {id: 'P009'}), (s:Supplier {id: 'SUP001'}) MERGE (p)-[:SUPPLIED_BY]->(s)
            MATCH (p:Product {id: 'P010'}), (s:Supplier {id: 'SUP004'}) MERGE (p)-[:SUPPLIED_BY]->(s)
            """,
            
            # === RELATIONSHIPS: Products → Carriers ===
            """
            MATCH (p:Product {id: 'P001'}), (c:Carrier {id: 'CAR001'}) MERGE (p)-[:SHIPPED_BY]->(c)
            MATCH (p:Product {id: 'P002'}), (c:Carrier {id: 'CAR002'}) MERGE (p)-[:SHIPPED_BY]->(c)
            MATCH (p:Product {id: 'P003'}), (c:Carrier {id: 'CAR003'}) MERGE (p)-[:SHIPPED_BY]->(c)
            MATCH (p:Product {id: 'P004'}), (c:Carrier {id: 'CAR004'}) MERGE (p)-[:SHIPPED_BY]->(c)
            MATCH (p:Product {id: 'P005'}), (c:Carrier {id: 'CAR005'}) MERGE (p)-[:SHIPPED_BY]->(c)
            """,
            
            # === RELATIONSHIPS: Inventory → Products ===
            """
            MATCH (i:Inventory {product_id: 'P001'}), (p:Product {id: 'P001'}) MERGE (i)-[:FOR_PRODUCT]->(p)
            MATCH (i:Inventory {product_id: 'P002'}), (p:Product {id: 'P002'}) MERGE (i)-[:FOR_PRODUCT]->(p)
            MATCH (i:Inventory {product_id: 'P003'}), (p:Product {id: 'P003'}) MERGE (i)-[:FOR_PRODUCT]->(p)
            MATCH (i:Inventory {product_id: 'P004'}), (p:Product {id: 'P004'}) MERGE (i)-[:FOR_PRODUCT]->(p)
            MATCH (i:Inventory {product_id: 'P005'}), (p:Product {id: 'P005'}) MERGE (i)-[:FOR_PRODUCT]->(p)
            MATCH (i:Inventory {product_id: 'P006'}), (p:Product {id: 'P006'}) MERGE (i)-[:FOR_PRODUCT]->(p)
            MATCH (i:Inventory {product_id: 'P007'}), (p:Product {id: 'P007'}) MERGE (i)-[:FOR_PRODUCT]->(p)
            MATCH (i:Inventory {product_id: 'P008'}), (p:Product {id: 'P008'}) MERGE (i)-[:FOR_PRODUCT]->(p)
            MATCH (i:Inventory {product_id: 'P009'}), (p:Product {id: 'P009'}) MERGE (i)-[:FOR_PRODUCT]->(p)
            MATCH (i:Inventory {product_id: 'P010'}), (p:Product {id: 'P010'}) MERGE (i)-[:FOR_PRODUCT]->(p)
            """,
            
            # === RELATIONSHIPS: Inventory → Warehouses ===
            """
            MATCH (i:Inventory {warehouse_id: 'WH001'}), (w:Warehouse {id: 'WH001'}) MERGE (i)-[:AT_WAREHOUSE]->(w)
            MATCH (i:Inventory {warehouse_id: 'WH002'}), (w:Warehouse {id: 'WH002'}) MERGE (i)-[:AT_WAREHOUSE]->(w)
            MATCH (i:Inventory {warehouse_id: 'WH003'}), (w:Warehouse {id: 'WH003'}) MERGE (i)-[:AT_WAREHOUSE]->(w)
            MATCH (i:Inventory {warehouse_id: 'WH004'}), (w:Warehouse {id: 'WH004'}) MERGE (i)-[:AT_WAREHOUSE]->(w)
            MATCH (i:Inventory {warehouse_id: 'WH005'}), (w:Warehouse {id: 'WH005'}) MERGE (i)-[:AT_WAREHOUSE]->(w)
            """
        ]
        
        # Execute each query
        for query in queries:
            try:
                self.query_graph(query)
                print("   ✅ Query executed successfully")
            except Exception as e:
                print(f"   ❌ Error: {e}")
        
        print("✅ Knowledge Graph created successfully in Neo4j AuraDB!")
    
    def get_all_products(self) -> List[Dict]:
        """Get all products with their details"""
        query = """
        MATCH (p:Product)
        OPTIONAL MATCH (p)-[:STORED_AT]->(w:Warehouse)
        OPTIONAL MATCH (p)-[:SUPPLIED_BY]->(s:Supplier)
        RETURN p, COLLECT(DISTINCT w.name) AS warehouses, 
               COLLECT(DISTINCT s.name) AS suppliers
        """
        return self.query_graph(query)
    
    def get_low_inventory_products(self) -> List[Dict]:
        """Get products where quantity < reorder_point"""
        query = """
        MATCH (i:Inventory)
        WHERE i.quantity < i.reorder_point
        MATCH (i)-[:FOR_PRODUCT]->(p:Product)
        RETURN p.name AS product, i.quantity AS current, i.reorder_point AS reorder_point
        """
        return self.query_graph(query)
    
    def get_products_by_warehouse(self, warehouse_id: str) -> List[Dict]:
        """Get all products in a specific warehouse"""
        query = """
        MATCH (w:Warehouse {id: $warehouse_id})<-[:STORED_AT]-(p:Product)
        RETURN p.name AS product, p.category AS category
        """
        return self.query_graph(query, {"warehouse_id": warehouse_id})


# ===== MAIN - CREATE KNOWLEDGE GRAPH =====
if __name__ == "__main__":
    print("="*60)
    print("🚀 Creating GraphRAG with Neo4j AuraDB")
    print("="*60)
    
    # Initialize GraphRAG
    graphrag = GraphRAG()
    
    try:
        # Create Knowledge Graph
        graphrag.create_knowledge_graph()
        
        # Test queries
        print("\n" + "="*50)
        print(" TESTING QUERIES")
        print("="*50)
        
        # Test 1: All products
        print("\n All Products:")
        products = graphrag.get_all_products()
        for item in products[:3]:  # Show first 3
            print(f"   - {item}")
        
        # Test 2: Low inventory
        print("\nLow Inventory Products:")
        low_inv = graphrag.get_low_inventory_products()
        for item in low_inv:
            print(f"   - {item}")
        
        # Test 3: Products in WH001
        print("\n🏭 Products in WH001:")
        wh_products = graphrag.get_products_by_warehouse("WH001")
        for item in wh_products:
            print(f"   - {item}")
        
        print("\n All tests completed successfully!")
        
    except Exception as e:
        print(f" Error: {e}")
    
    finally:
        graphrag.close()