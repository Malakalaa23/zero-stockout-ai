"""
graph_mock.py - محاكاة Neo4j بـ JSON
بديل خفيف جداً مش محتاج مساحة ولا تثبيت!
"""

import json
import os

class GraphMock:
    """
    بديل لـ Neo4j باستخدام JSON
    نفس الوظيفة لكن من غير قاعدة بيانات!
    """
    
    def __init__(self):
        self.data_file = os.path.join(os.path.dirname(__file__), "knowledge_graph.json")
        self.graph = self.load_or_create()
        print("GraphMock initialized (no database needed!)")
    
    def load_or_create(self):
        """تحميل أو إنشاء الـ Knowledge Graph"""
        if os.path.exists(self.data_file):
            with open(self.data_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        else:
            return self.create_default_graph()
    
    def create_default_graph(self):
        """إنشاء الـ Graph الافتراضي"""
        graph = {
            "nodes": [
                # Warehouses
                {"id": "WH001", "type": "Warehouse", "name": "العبور", "location": "القاهرة"},
                {"id": "WH002", "type": "Warehouse", "name": "أكتوبر", "location": "الجيزة"},
                {"id": "WH003", "type": "Warehouse", "name": "العاصمة", "location": "القاهرة"},
                {"id": "WH004", "type": "Warehouse", "name": "الإسكندرية", "location": "الإسكندرية"},
                {"id": "WH005", "type": "Warehouse", "name": "بورسعيد", "location": "بورسعيد"},
                
                # Products
                {"id": "P001", "type": "Product", "name": "حذاء رياضي", "category": "أحذية"},
                {"id": "P002", "type": "Product", "name": "تلفزيون", "category": "إلكترونيات"},
                {"id": "P003", "type": "Product", "name": "ثلاجة", "category": "أجهزة منزلية"},
                {"id": "P004", "type": "Product", "name": "لابتوب", "category": "إلكترونيات"},
                {"id": "P005", "type": "Product", "name": "هاتف", "category": "إلكترونيات"},
                {"id": "P006", "type": "Product", "name": "جهاز لوحي", "category": "إلكترونيات"},
                {"id": "P007", "type": "Product", "name": "غسالة", "category": "أجهزة منزلية"},
                {"id": "P008", "type": "Product", "name": "مكيف", "category": "أجهزة منزلية"},
                {"id": "P009", "type": "Product", "name": "ساعة", "category": "إكسسوارات"},
                {"id": "P010", "type": "Product", "name": "لعبة", "category": "ألعاب"},
                
                # Suppliers
                {"id": "SUP001", "type": "Supplier", "name": "المورد العربي"},
                {"id": "SUP002", "type": "Supplier", "name": "Global Trade Co"},
                {"id": "SUP003", "type": "Supplier", "name": "Fast Supply"},
                {"id": "SUP004", "type": "Supplier", "name": "مصر للمنتجات"},
                {"id": "SUP005", "type": "Supplier", "name": "Tech Import"},
                
                # Carriers
                {"id": "CAR001", "type": "Carrier", "name": "DHL"},
                {"id": "CAR002", "type": "Carrier", "name": "FedEx"},
                {"id": "CAR003", "type": "Carrier", "name": "Aramex"},
                {"id": "CAR004", "type": "Carrier", "name": "UPS"},
                {"id": "CAR005", "type": "Carrier", "name": "النقل البري"},
                
                # Inventory
                {"id": "INV001", "type": "Inventory", "product_id": "P001", "warehouse_id": "WH001", "quantity": 50, "reorder_point": 30},
                {"id": "INV002", "type": "Inventory", "product_id": "P002", "warehouse_id": "WH002", "quantity": 20, "reorder_point": 15},
                {"id": "INV003", "type": "Inventory", "product_id": "P003", "warehouse_id": "WH003", "quantity": 10, "reorder_point": 8},
                {"id": "INV004", "type": "Inventory", "product_id": "P004", "warehouse_id": "WH004", "quantity": 35, "reorder_point": 20},
                {"id": "INV005", "type": "Inventory", "product_id": "P005", "warehouse_id": "WH005", "quantity": 60, "reorder_point": 40},
                {"id": "INV006", "type": "Inventory", "product_id": "P006", "warehouse_id": "WH001", "quantity": 25, "reorder_point": 15},
                {"id": "INV007", "type": "Inventory", "product_id": "P007", "warehouse_id": "WH002", "quantity": 5, "reorder_point": 10},
                {"id": "INV008", "type": "Inventory", "product_id": "P008", "warehouse_id": "WH003", "quantity": 45, "reorder_point": 30},
                {"id": "INV009", "type": "Inventory", "product_id": "P009", "warehouse_id": "WH004", "quantity": 100, "reorder_point": 50},
                {"id": "INV010", "type": "Inventory", "product_id": "P010", "warehouse_id": "WH005", "quantity": 80, "reorder_point": 60},
            ],
            "relationships": [
                # STORED_AT
                {"from": "P001", "to": "WH001", "type": "STORED_AT"},
                {"from": "P002", "to": "WH002", "type": "STORED_AT"},
                {"from": "P003", "to": "WH003", "type": "STORED_AT"},
                {"from": "P004", "to": "WH004", "type": "STORED_AT"},
                {"from": "P005", "to": "WH005", "type": "STORED_AT"},
                {"from": "P006", "to": "WH001", "type": "STORED_AT"},
                {"from": "P007", "to": "WH002", "type": "STORED_AT"},
                {"from": "P008", "to": "WH003", "type": "STORED_AT"},
                {"from": "P009", "to": "WH004", "type": "STORED_AT"},
                {"from": "P010", "to": "WH005", "type": "STORED_AT"},
                
                # SUPPLIED_BY
                {"from": "P001", "to": "SUP001", "type": "SUPPLIED_BY"},
                {"from": "P002", "to": "SUP002", "type": "SUPPLIED_BY"},
                {"from": "P003", "to": "SUP003", "type": "SUPPLIED_BY"},
                {"from": "P004", "to": "SUP005", "type": "SUPPLIED_BY"},
                {"from": "P005", "to": "SUP002", "type": "SUPPLIED_BY"},
                
                # SHIPPED_BY
                {"from": "P001", "to": "CAR001", "type": "SHIPPED_BY"},
                {"from": "P002", "to": "CAR002", "type": "SHIPPED_BY"},
                {"from": "P003", "to": "CAR003", "type": "SHIPPED_BY"},
                {"from": "P004", "to": "CAR004", "type": "SHIPPED_BY"},
                {"from": "P005", "to": "CAR005", "type": "SHIPPED_BY"},
            ]
        }
        
        # حفظ الملف
        with open(self.data_file, 'w', encoding='utf-8') as f:
            json.dump(graph, f, ensure_ascii=False, indent=2)
        
        return graph
    
    def query(self, query_type, params=None):
        """تنفيذ استعلامات"""
        if query_type == "get_low_inventory":
            results = []
            for node in self.graph["nodes"]:
                if node["type"] == "Inventory":
                    if node["quantity"] < node["reorder_point"]:
                        product = self.get_node(node["product_id"])
                        results.append({
                            "product": product["name"] if product else node["product_id"],
                            "current": node["quantity"],
                            "reorder_point": node["reorder_point"]
                        })
            return results
        
        elif query_type == "get_product_relationships":
            product_id = params.get("product_id")
            product = self.get_node(product_id)
            if not product:
                return {}
            
            suppliers = []
            warehouses = []
            carriers = []
            
            for rel in self.graph["relationships"]:
                if rel["from"] == product_id:
                    target = self.get_node(rel["to"])
                    if target:
                        if rel["type"] == "SUPPLIED_BY":
                            suppliers.append(target["name"])
                        elif rel["type"] == "STORED_AT":
                            warehouses.append(target["name"])
                        elif rel["type"] == "SHIPPED_BY":
                            carriers.append(target["name"])
            
            return {
                "product": product["name"],
                "suppliers": suppliers,
                "warehouses": warehouses,
                "carriers": carriers
            }
        
        return []
    
    def get_node(self, node_id):
        """جيب عقدة بالـ ID"""
        for node in self.graph["nodes"]:
            if node["id"] == node_id:
                return node
        return None
    
    def get_all_products(self):
        return [n for n in self.graph["nodes"] if n["type"] == "Product"]
    
    def get_all_warehouses(self):
        return [n for n in self.graph["nodes"] if n["type"] == "Warehouse"]
    
    def get_low_inventory(self):
        return self.query("get_low_inventory")
    
    def get_product_relationships(self, product_id):
        return self.query("get_product_relationships", {"product_id": product_id})
    
    def close(self):
        """إغلاق (مش محتاج)"""
        pass