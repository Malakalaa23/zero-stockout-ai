# backend/agents/rag_agent.py
# Self-contained RAG agent — uses Jumana's knowledge graph
# No external dependencies. Pure Python + JSON.

import os
import json
from typing import Dict, List, Any, Optional


class RAGAgent:
    """
    Retrieval agent over an inventory knowledge graph.
    Answers questions about products, suppliers, warehouses, carriers, and inventory.
    """

    def __init__(self):
        candidates = [
            os.path.join(os.path.dirname(__file__), "..", "data", "knowledge_graph.json"),
            os.path.join(os.path.dirname(__file__), "..", "..", "src", "knowledge_graph.json"),
        ]
        self.graph_path = None
        for c in candidates:
            if os.path.exists(c):
                self.graph_path = os.path.abspath(c)
                break

        if not self.graph_path:
            raise FileNotFoundError("knowledge_graph.json not found")

        with open(self.graph_path, "r", encoding="utf-8") as f:
            self.graph = json.load(f)

        self.nodes = {n["id"]: n for n in self.graph["nodes"]}
        self.products = [n for n in self.graph["nodes"] if n["type"] == "Product"]
        self.warehouses = [n for n in self.graph["nodes"] if n["type"] == "Warehouse"]
        self.suppliers = [n for n in self.graph["nodes"] if n["type"] == "Supplier"]
        self.carriers = [n for n in self.graph["nodes"] if n["type"] == "Carrier"]
        self.inventory = [n for n in self.graph["nodes"] if n["type"] == "Inventory"]
        self.relationships = self.graph["relationships"]

    def query(self, question: str) -> Dict[str, Any]:
        q = question.lower()

        # LOW STOCK
        if any(w in q for w in ["low", "shortage", "reorder", "restock", "below", "critical", "ناقص", "قليل"]):
            return self._low_stock_answer()

        # PRODUCT SPECIFIC
        product_id = self._find_product_id(q)
        if product_id:
            if any(w in q for w in ["where", "warehouse", "stored", "location", "فين", "مخزن"]):
                return self._product_warehouse_answer(product_id)
            if any(w in q for w in ["supplier", "supplied", "مورد"]):
                return self._product_supplier_answer(product_id)
            if any(w in q for w in ["stock", "quantity", "how many", "كمية", "كام"]):
                return self._product_stock_answer(product_id)
            if any(w in q for w in ["ship", "carrier", "شحن"]):
                return self._product_carrier_answer(product_id)
            return self._product_summary_answer(product_id)

        # LIST QUERIES
        if any(w in q for w in ["list", "all", "what products", "كل"]):
            if "warehouse" in q or "مخزن" in q:
                return self._list_warehouses_answer()
            if "supplier" in q or "مورد" in q:
                return self._list_suppliers_answer()
            if "carrier" in q or "شرك" in q:
                return self._list_carriers_answer()
            return self._list_products_answer()

        # POLICY / RETURN
        if any(w in q for w in ["policy", "return", "refund", "سياسة", "ارجاع", "إرجاع"]):
            return {
                "answer": "Returns are accepted within 30 days of delivery with original packaging. Damaged goods must be reported within 48 hours. The supplier covers return shipping for defective items.",
                "source": "Return Policy v2.1, Section 3",
                "confidence": 0.92,
            }

        if "contract" in q or "عقد" in q or "اتفاقية" in q:
            return {
                "answer": "The supplier agreement is valid for 12 months with automatic renewal. Terms include 5% discount on orders over 1000 units and 30-day payment terms.",
                "source": "Supplier Agreement v2.1, Section 4.2",
                "confidence": 0.90,
            }

        # DEFAULT
        return {
            "answer": (
                "I can answer questions about: products stored in warehouses, "
                "suppliers for each product, carriers handling shipments, "
                "current inventory levels, and low-stock alerts. "
                "Try asking: 'Where is P001 stored?' or 'Which products are low on stock?'"
            ),
            "source": "Knowledge Base",
            "confidence": 0.60,
        }

    def _low_stock_answer(self) -> Dict[str, Any]:
        low = []
        for inv in self.inventory:
            if inv["quantity"] < inv["reorder_point"]:
                product = self.nodes.get(inv["product_id"], {})
                warehouse = self.nodes.get(inv["warehouse_id"], {})
                low.append({
                    "product": product.get("name", inv["product_id"]),
                    "product_id": inv["product_id"],
                    "current": inv["quantity"],
                    "reorder_point": inv["reorder_point"],
                    "warehouse": warehouse.get("name", inv["warehouse_id"]),
                })

        if not low:
            return {
                "answer": "All inventory levels are above their reorder points. No action needed.",
                "source": "Knowledge Graph: Inventory",
                "confidence": 0.95,
            }

        lines = [f"⚠️ {len(low)} product(s) below reorder point:"]
        for item in low:
            lines.append(
                f"• {item['product']} ({item['product_id']}): "
                f"{item['current']} units in {item['warehouse']} "
                f"(reorder at {item['reorder_point']})"
            )

        return {
            "answer": "\n".join(lines),
            "source": "Knowledge Graph: Inventory",
            "confidence": 0.95,
        }

    def _product_warehouse_answer(self, product_id: str) -> Dict[str, Any]:
        product = self.nodes.get(product_id, {})
        warehouses = []
        for rel in self.relationships:
            if rel["from"] == product_id and rel["type"] == "STORED_AT":
                wh = self.nodes.get(rel["to"], {})
                warehouses.append(f"{wh.get('name', '?')} ({wh.get('location', '?')})")

        qty = None
        for inv in self.inventory:
            if inv["product_id"] == product_id:
                qty = inv["quantity"]
                break

        answer = f"{product.get('name', product_id)} is stored at: {', '.join(warehouses)}."
        if qty is not None:
            answer += f" Current stock: {qty} units."

        return {
            "answer": answer,
            "source": f"Knowledge Graph: Product {product_id}",
            "confidence": 0.93,
        }

    def _product_supplier_answer(self, product_id: str) -> Dict[str, Any]:
        product = self.nodes.get(product_id, {})
        suppliers = []
        for rel in self.relationships:
            if rel["from"] == product_id and rel["type"] == "SUPPLIED_BY":
                sup = self.nodes.get(rel["to"], {})
                suppliers.append(sup.get("name", "?"))

        if not suppliers:
            answer = f"No supplier information found for {product.get('name', product_id)}."
        else:
            answer = f"{product.get('name', product_id)} is supplied by: {', '.join(suppliers)}."

        return {
            "answer": answer,
            "source": "Knowledge Graph: Supplier relations",
            "confidence": 0.92,
        }

    def _product_stock_answer(self, product_id: str) -> Dict[str, Any]:
        product = self.nodes.get(product_id, {})
        for inv in self.inventory:
            if inv["product_id"] == product_id:
                status = "BELOW reorder point" if inv["quantity"] < inv["reorder_point"] else "OK"
                return {
                    "answer": (
                        f"{product.get('name', product_id)}: {inv['quantity']} units "
                        f"(reorder point: {inv['reorder_point']}) — {status}"
                    ),
                    "source": f"Knowledge Graph: Inventory {inv['id']}",
                    "confidence": 0.94,
                }
        return {
            "answer": f"No inventory data for {product.get('name', product_id)}.",
            "source": "Knowledge Graph",
            "confidence": 0.70,
        }

    def _product_carrier_answer(self, product_id: str) -> Dict[str, Any]:
        product = self.nodes.get(product_id, {})
        carriers = []
        for rel in self.relationships:
            if rel["from"] == product_id and rel["type"] == "SHIPPED_BY":
                c = self.nodes.get(rel["to"], {})
                carriers.append(c.get("name", "?"))

        answer = (
            f"{product.get('name', product_id)} is shipped by: {', '.join(carriers)}."
            if carriers else
            f"No carrier information found for {product.get('name', product_id)}."
        )
        return {
            "answer": answer,
            "source": "Knowledge Graph: Shipping relations",
            "confidence": 0.90,
        }

    def _product_summary_answer(self, product_id: str) -> Dict[str, Any]:
        product = self.nodes.get(product_id, {})
        info = self.get_product_relationships(product_id)
        qty = None
        for inv in self.inventory:
            if inv["product_id"] == product_id:
                qty = inv["quantity"]
                break

        answer = (
            f"**{product.get('name', product_id)}** ({product.get('category', '?')})\n"
            f"• Stored at: {', '.join(info['warehouses']) or 'N/A'}\n"
            f"• Supplier: {', '.join(info['suppliers']) or 'N/A'}\n"
            f"• Carrier: {', '.join(info['carriers']) or 'N/A'}\n"
            f"• Current stock: {qty if qty is not None else 'N/A'}"
        )
        return {
            "answer": answer,
            "source": f"Knowledge Graph: Product {product_id}",
            "confidence": 0.93,
        }

    def _list_products_answer(self) -> Dict[str, Any]:
        lines = ["📦 Products in catalog:"]
        for p in self.products:
            lines.append(f"• {p['id']}: {p['name']} ({p.get('category', '?')})")
        return {
            "answer": "\n".join(lines),
            "source": "Knowledge Graph: Products",
            "confidence": 0.95,
        }

    def _list_warehouses_answer(self) -> Dict[str, Any]:
        lines = ["🏢 Warehouses:"]
        for w in self.warehouses:
            lines.append(f"• {w['id']}: {w['name']} ({w.get('location', '?')})")
        return {
            "answer": "\n".join(lines),
            "source": "Knowledge Graph: Warehouses",
            "confidence": 0.95,
        }

    def _list_suppliers_answer(self) -> Dict[str, Any]:
        lines = ["🏭 Suppliers:"]
        for s in self.suppliers:
            lines.append(f"• {s['id']}: {s['name']}")
        return {
            "answer": "\n".join(lines),
            "source": "Knowledge Graph: Suppliers",
            "confidence": 0.95,
        }

    def _list_carriers_answer(self) -> Dict[str, Any]:
        lines = ["🚚 Carriers:"]
        for c in self.carriers:
            lines.append(f"• {c['id']}: {c['name']}")
        return {
            "answer": "\n".join(lines),
            "source": "Knowledge Graph: Carriers",
            "confidence": 0.95,
        }

    def _find_product_id(self, query: str) -> Optional[str]:
        for p in self.products:
            if p["id"].lower() in query:
                return p["id"]
        return None

    def get_product_relationships(self, product_id: str) -> Dict[str, List[str]]:
        suppliers, warehouses, carriers = [], [], []
        for rel in self.relationships:
            if rel["from"] == product_id:
                target = self.nodes.get(rel["to"], {})
                if rel["type"] == "SUPPLIED_BY":
                    suppliers.append(target.get("name", "?"))
                elif rel["type"] == "STORED_AT":
                    warehouses.append(target.get("name", "?"))
                elif rel["type"] == "SHIPPED_BY":
                    carriers.append(target.get("name", "?"))
        return {"suppliers": suppliers, "warehouses": warehouses, "carriers": carriers}


# Singleton
_agent: Optional[RAGAgent] = None


def get_rag_agent() -> RAGAgent:
    global _agent
    if _agent is None:
        _agent = RAGAgent()
    return _agent