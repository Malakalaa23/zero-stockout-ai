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
        {"id": "policy_restock", "text": "سياسة إعادة الطلب: يتم إعادة الطلب تلقائياً عندما يصل المخزون إلى 30 وحدة أو أقل", "type": "policy"},
        {"id": "carrier_dhl", "text": "المورد DHL: يوصل خلال 2-3 أيام عمل، تكلفة الشحن 50 دولار لكل شحنة", "type": "carrier"},
        {"id": "carrier_local", "text": "المورد البديل المحلي: يوصل خلال 24 ساعة، تكلفة الشحن 100 دولار للشحنة", "type": "carrier"},
        {"id": "cost_shipping", "text": "تكلفة الشحن: 50 دولار لكل شحنة + 5 دولار لكل وحدة", "type": "cost"},
        {"id": "cost_storage", "text": "تكلفة التخزين: 2 دولار لكل وحدة في اليوم", "type": "cost"},
        {"id": "cost_stockout", "text": "تكلفة نفاد المخزون: 100 دولار لكل وحدة مفقودة", "type": "cost"},
        {"id": "top_selling", "text": "المنتجات الأكثر مبيعاً: الهواتف، اللابتوبات، وأجهزة التلفزيون", "type": "sales"},
        {"id": "return_policy", "text": "سياسة الإرجاع: يمكن إرجاع المنتجات خلال 14 يوماً من الشراء", "type": "policy"},
        {"id": "safety_stock", "text": "المخزون الآمن: يجب أن يكون 30% من الحد الأقصى للطلب الشهري", "type": "policy"},
        {"id": "delivery_times", "text": "أوقات التسليم: DHL 2-3 أيام، FedEx 3 أيام، Aramex 2 أيام", "type": "carrier"},
    ]

    if collection.count() == 0:
        collection.add(
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