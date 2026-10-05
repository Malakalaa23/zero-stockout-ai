import os
import json
from typing import Optional, List, Dict


def get_collection(name: str = "inventory_docs", data_dir: Optional[str] = None):
    try:
        import chromadb
        from chromadb.config import Settings
    except ImportError as exc:
        raise RuntimeError("ChromaDB not installed. Run: pip install chromadb") from exc

    if data_dir is None:
        data_dir = os.path.join(os.path.dirname(__file__), "..", "chroma_data")

    os.makedirs(data_dir, exist_ok=True)

    client = chromadb.PersistentClient(
        path=data_dir,
        settings=Settings(anonymized_telemetry=False)
    )
    return client.get_or_create_collection(
        name=name,
        metadata={"hnsw:space": "cosine"}
    )


def add_inventory_documents(collection) -> int:
    documents = [
        {"id": "policy_restock", "text": "Reorder policy: automatically reorder when stock reaches 30 units or less.", "type": "policy"},
        {"id": "carrier_dhl", "text": "DHL delivers in 2-3 business days. Shipping costs 50 dollars per shipment.", "type": "carrier"},
        {"id": "carrier_local", "text": "The local alternative supplier delivers within 24 hours and costs 100 dollars per shipment.", "type": "carrier"},
        {"id": "cost_shipping", "text": "Shipping cost: 50 dollars per shipment plus 5 dollars per unit.", "type": "cost"},
        {"id": "cost_storage", "text": "Storage cost: 2 dollars per unit per day.", "type": "cost"},
        {"id": "cost_stockout", "text": "Stockout cost: 100 dollars per lost unit.", "type": "cost"},
        {"id": "top_selling", "text": "Top-selling products: phones, laptops, and televisions.", "type": "sales"},
        {"id": "return_policy", "text": "Return policy: products can be returned within 14 days of purchase.", "type": "policy"},
        {"id": "safety_stock", "text": "Safety stock should be 30% of the maximum monthly demand.", "type": "policy"},
        {"id": "delivery_times", "text": "Delivery times: DHL 2-3 days, FedEx 3 days, Aramex 2 days.", "type": "carrier"},
    ]

    collection.upsert(
        documents=[d["text"] for d in documents],
        ids=[d["id"] for d in documents],
        metadatas=[{"type": d["type"]} for d in documents]
    )
    return collection.count()


def search(collection, query: str, n_results: int = 3) -> List[Dict]:
    results = collection.query(query_texts=[query], n_results=n_results)

    output = []
    if results and results.get("documents"):
        for doc, meta, dist in zip(
            results["documents"][0],
            results["metadatas"][0],
            results["distances"][0]
        ):
            output.append({
                "text": doc,
                "type": meta.get("type", "unknown"),
                "score": 1 - dist
            })
    return output