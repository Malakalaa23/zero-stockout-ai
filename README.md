# 🎯 Zero-Stockout AI

> A multi-agent AI system that predicts inventory shortages before they happen — and recommends optimal order quantities.

**$1.7 trillion is lost annually to inventory distortion.** Zero-Stockout AI cuts that cost by **19%** through end-to-end optimization of demand forecasting and replenishment decisions.

---

## 🚀 What It Does

Zero-Stockout AI is a **4-agent system** that:

- 📊 **Forecasts demand** for the next 6–14 days using a Temporal Fusion Transformer (TFT)
- 🧠 **Calculates optimal order quantities** using a trained neural network that approximates cost minimization
- 📚 **Answers policy questions** via GraphRAG over suppliers, contracts, and returns
- 👁️ **Detects package damage** using YOLOv12

Everything runs **locally** — with **zero external AI APIs**.

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────┐
│  Frontend (Streamlit)  — port 8501          │
│  Cinematic dashboard + keyword router       │
└─────────────────────────────────────────────┘
                     ↓
┌─────────────────────────────────────────────┐
│  Backend (FastAPI)  — port 8000             │
│  6 REST endpoints                           │
└─────────────────────────────────────────────┘
                     ↓
┌─────────────────────────────────────────────┐
│  4 Independent Agents                       │
│  Decision  |  Forecast  |  RAG  |  Vision  │
└─────────────────────────────────────────────┘
                     ↓
┌─────────────────────────────────────────────┐
│  Data & Models                              │
│  TFT Model · Router Model · Neo4j · ChromaDB│
└─────────────────────────────────────────────┘
```

---

## 🧠 The Agents

| Agent | Role | Technology |
|-------|------|-----------|
| 🧠 **Decision** | Computes optimal order quantity | Cost-minimization loop + trained neural network |
| 📊 **Forecast** | Predicts demand (6–14 days) | Temporal Fusion Transformer (TFT) |
| 📚 **Knowledge** | Answers policy & contract questions | GraphRAG (Neo4j + ChromaDB) |
| 👁️ **Vision** | Detects packages and damage | YOLOv12 |

---

## 🔬 Core Innovation — TFT-MPIR

**TFT-MPIR** (Temporal Fusion Transformer with Multi-Period Inventory Replenishment) integrates demand forecasting and ordering into a **single framework**.

Traditional systems treat forecasting and ordering as two separate problems. TFT-MPIR solves them together — reducing total cost by **19%**.

### Decision Model — Training Pipeline

| Step | What We Did |
|------|-------------|
| 1 | Extracted 7 features: `current_stock`, `forecasted_demand`, `days`, `holding_cost`, `stockout_cost`, `unit_cost`, `confidence` |
| 2 | Generated 10,000 synthetic samples from the SAPiBench dataset |
| 3 | Computed the optimal quantity for each sample via exhaustive cost minimization |
| 4 | Trained a 3-layer MLP (128 → 64 → 32 → 1) with BatchNorm + Dropout |
| 5 | Achieved **MAE < 10 units**, **R² > 0.9** |
| 6 | Saved weights to `router_model.pkl` (88 KB) |
| 7 | Deployed with a classic cost-loop fallback for reliability |

---

## 📊 Results

| Metric | Value |
|--------|-------|
| Cost reduction | **19%** vs. traditional methods |
| Forecast accuracy | **11% MAPE** |
| Decision model MAE | **< 10 units** |
| Model size | 34K params (TFT) + 88 KB (NN) |
| REST endpoints | 6 |
| Agents | 4 independent |
| Latency | **< 1 second** per query |
| External AI APIs | **Zero** |

---

## 🛠️ Tech Stack

**Frontend**
- Streamlit
- Custom CSS (animations, glass morphism)

**Backend**
- FastAPI + Uvicorn
- Python 3.14

**Machine Learning**
- PyTorch
- PyTorch Forecasting
- PyTorch Lightning

**Data**
- Pandas
- NumPy
- Scikit-learn

**Databases (Docker)**
- TimescaleDB — time-series storage
- Redis — caching
- Neo4j — knowledge graph
- ChromaDB — vector store

**Deployment**
- Docker Compose

---

## 📁 Project Structure

```
zero-stockout/
│
├── backend/
│   ├── agents/
│   │   ├── decision_agent.py      # Cost-minimization logic
│   │   ├── forecast_agent.py      # TFT wrapper
│   │   ├── rag_agent.py           # Knowledge retrieval
│   │   ├── vision_agent.py        # YOLOv12 wrapper
│   │   └── tft_mpir_model.py      # Neural network definition
│   ├── api/
│   │   └── routes.py              # 6 REST endpoints
│   ├── models/
│   │   └── router_model.pkl       # Trained decision model
│   ├── main.py
│   ├── config.py
│   ├── Dockerfile
│   └── requirements.txt
│
├── frontend/
│   ├── app.py                     # Streamlit dashboard
│   └── Dockerfile
│
├── data/
│   └── SAPiBench-inventory-simulation-dataset-2026/
│
├── docker-compose.yml
├── README.md
└── .gitignore
```

---

## 🚀 Getting Started

### Prerequisites

- Python 3.12+ (3.14 works with wheel adjustments)
- Docker Desktop (for the full stack)
- 8 GB RAM recommended

### Option 1 — Local Development

**Terminal 1 — Backend:**
```bash
cd backend
pip install -r requirements.txt
python main.py
```

**Terminal 2 — Frontend:**
```bash
cd frontend
pip install streamlit requests plotly
streamlit run app.py
```

Open:
- API docs: `http://localhost:8000/docs`
- Dashboard: `http://localhost:8501`

### Option 2 — Docker Compose

```bash
docker-compose up -d
```

This starts 6 services: TimescaleDB, Redis, Neo4j, ChromaDB, Backend, Frontend.

---

## 🎯 Example Queries

Once the dashboard is running:

| Query | Agent | Response |
|-------|-------|----------|
| `reorder P001` | Decision | Recommends ~105 units at optimal cost |
| `when will product P001 be ready` | Forecast | 7-day demand prediction |
| `what is the return policy` | Knowledge | Policy answer from knowledge base |
| `detect package in image` | Vision | Package detection result |

---

## 🧪 Testing the API

```bash
# Health check
curl http://localhost:8000/predict/health

# Forecast
curl -X POST "http://localhost:8000/predict/forecast?sku_id=P001&days=14"

# Decision
curl -X POST "http://localhost:8000/predict/decision?sku_id=P001&current_stock=82&unit_cost=10.0&forecast_days=14"

# RAG
curl -X POST "http://localhost:8000/predict/rag?query=return+policy"
```

---

## 👥 Team

| Name | Role | Responsibilities |
|------|------|------------------|
| **Malak** | System Architect & Decision Lead | Decision Agent, API, Docker, Integration, Frontend |
| **Sara** | Forecast Lead | TFT Training, EDA, Feature Engineering |
| **Jumana** | RAG & Knowledge Lead | ChromaDB, Neo4j, GraphRAG, Router Agent |
| **Nada** | Vision Lead | YOLOv12 Training, Object Detection |
| **Hala** | NLP & Voice Lead | Router Agent, STT, TTS, Video, README |

---

## 📚 Course Context

Built for the **AI for Business** course — NTI Summer Internship Program.

Course topics applied:

- **Supervised Learning** → TFT, YOLOv12
- **Neural Networks** → TFT-MPIR Decision Model
- **Deep Learning** → Temporal Fusion Transformer
- **CNNs** → YOLOv12
- **NLP** → Router Agent, RAG
- **Model Deployment** → FastAPI, Docker
- **AI Tools & Platforms** → Streamlit

---

## 📄 License

This project is part of the NTI Summer Internship — AI for Business course. Free for educational use.

---

## 🙏 Acknowledgments

- **SAPiBench** — for the inventory simulation dataset
- **Kaggle** — for the DEPI retail dataset
- **PyTorch Forecasting** team — for the TFT implementation
- **NTI** — for the course structure and guidance

---

**Built with precision. Zero stockouts.**
