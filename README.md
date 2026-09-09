# Zero Stockout AI

A Graph RAG inventory assistant using Neo4j AuraDB for relationships and local persistent ChromaDB storage under `chroma_data/`.

## Run locally

Install dependencies and run from this directory:

```powershell
pip install -r requirements.txt
python -m src.main "Which items need reorder?"
```

## Configuration

Put the AuraDB connection values in `.env`:

```text
NEO4J_URI=neo4j+s://your-instance.databases.neo4j.io
NEO4J_USERNAME=neo4j
NEO4J_PASSWORD=your-password
NEO4J_DATABASE=neo4j
```

`chroma_data/` is created automatically when ChromaDB is initialized. Do not commit `.env` or database credentials.
