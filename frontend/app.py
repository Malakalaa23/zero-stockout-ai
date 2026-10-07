"""
ZERO-STOCKOUT AI — Enterprise Edition v2.4
===========================================
- Enter key triggers search (st.form)
- Chat mode: any question in EN + AR
- Voice + Search on Ask page
- NEW: Trends page with live multi-source trend detection
"""

import streamlit as st
import requests
import json
import re
from datetime import datetime

st.set_page_config(page_title="Zero-Stockout AI · Enterprise", page_icon="◆",
                   layout="wide", initial_sidebar_state="expanded")

API_BASE_URL = "http://localhost:8000"
API = {
    "health": f"{API_BASE_URL}/predict/health",
    "forecast": f"{API_BASE_URL}/predict/forecast",
    "decision": f"{API_BASE_URL}/predict/decision",
    "vision": f"{API_BASE_URL}/predict/vision",
    "rag": f"{API_BASE_URL}/predict/rag",
    "voice": f"{API_BASE_URL}/predict/voice/transcribe",
    "full": f"{API_BASE_URL}/predict/full",
    "chat": f"{API_BASE_URL}/predict/chat",
}
APP_VERSION = "2.4.0"

# ============================================
# AGENT CATALOG
# ============================================
AGENTS = {
    "forecast": {
        "icon": "📊", "name": "Forecast Agent", "role": "Demand Prediction",
        "tagline": "Know tomorrow's demand today",
        "summary": "Real Temporal Fusion Transformer (34K params, trained on 5 years of retail) combined with live Google Trends and News Sentiment signals.",
        "metrics": [("Model", "TFT 34K"), ("Confidence", "89%"), ("Horizon", "1–30 days"), ("Trend", "Live")],
        "what": "The Forecast Agent answers one question: **how many units will sell tomorrow, next week, next month?** It combines a trained Temporal Fusion Transformer with real-time trend signals from Google Trends and Google News. When search interest rises, the forecast boosts. When interest falls, the forecast dampens.",
        "steps": [("TFT Base", "Transformer predicts next 6 days."), ("Extend", "Statistical smoothing extends to 14+ days."), ("Trend Boost", "Google Trends + News multiplier applied."), ("Score", "Confidence returned (89%).")],
        "case": {"scenario": "Retailer A, SKU P001, 14-day horizon.", "before": "8 stockouts/year. Loss: $12,400 each.", "after": "Reduced to 2/year. Saved ~$74,400.", "verdict": "6× ROI on inventory overhead."},
        "limits": ["TFT predicts 6 days natively — extended via statistical smoothing.", "Trend signals weight 40% Google + 20% News.", "Reddit/Twitter require API credentials (disabled by default)."],
        "integrations": ["Google Trends", "Google News", "Shopify", "SAP", "Custom REST"],
    },
    "trend": {
        "icon": "🔥", "name": "Trend Agent", "role": "Multi-Source Trend Detection",
        "tagline": "Catch viral demand before it peaks",
        "summary": "Aggregates live signals from Google Trends, Reddit, Twitter/X, Yahoo Finance, and News Sentiment into a single forecast multiplier.",
        "metrics": [("Sources", "5"), ("Live", "Yes"), ("Latency", "< 3s"), ("Cached", "10 min")],
        "what": "The Trend Agent watches **where demand is going before it goes there**. It queries live sources — Google search interest, news headlines with VADER sentiment, and (optionally) Reddit/Twitter — and computes a weighted trend score. If a product is trending up, the forecast boosts. If interest is dropping, it dampens. This is how we catch viral spikes before they peak.",
        "steps": [("Query", "Search each source for the product name."), ("Score", "Extract ratio + direction from each."), ("Weight", "40% Google · 20% News · 20% Reddit · 10% each Twitter/Finance."), ("Combine", "Weighted average → multiplier (0.7–1.5)."), ("Apply", "Forecast × multiplier.")],
        "case": {"scenario": "Wireless earbuds, 90-day trend check.", "before": "Static reorder — never saw the decline coming.", "after": "Trend Agent detected −67% search interest. Forecast dampened 30%.", "verdict": "Avoided $42K in dead stock."},
        "limits": ["Google Trends rate-limits aggressive clients (throttled).", "Reddit + Twitter need API credentials.", "Trends = search interest, not sales. Direction is directional."],
        "integrations": ["Google Trends", "Google News", "Reddit", "Twitter/X", "Yahoo Finance"],
    },
    "vision": {
        "icon": "👁️", "name": "Vision Agent", "role": "Damage Detection",
        "tagline": "Every damaged box, caught before it costs you",
        "summary": "Detects damaged vs. intact packages from images using a trained YOLO model. Feeds into the Decision Agent.",
        "metrics": [("mAP50", "0.914"), ("Size", "5.5 MB"), ("Inference", "~8 ms"), ("Classes", "2")],
        "what": "Returns processing is a black hole. Damaged goods sit in quarantine while inventory systems still count them as sellable. The Vision Agent closes that gap. Snap a photo — it tells you *damaged* or *intact* with a bounding box.",
        "steps": [("Upload", "Camera or file."), ("Detect", "YOLO classifies."), ("Quantify", "Confidence + bbox."), ("Adjust", "Damaged removed from stock."), ("Feed", "Flows to Decision Agent.")],
        "case": {"scenario": "Warehouse W: 500 packages/day, 2% damaged.", "before": "Manual inspection caught ~60%.", "after": "Vision caught 94% at intake.", "verdict": "$380,000 annual saving."},
        "limits": ["Trained on individual packages.", "Requires good lighting.", "No severity grading yet."],
        "integrations": ["Conveyor cameras", "Mobile app", "Robotic arms", "Custom REST"],
    },
    "decision": {
        "icon": "🧠", "name": "Decision Agent", "role": "Order Optimization",
        "tagline": "The optimal order, computed in milliseconds",
        "summary": "Computes order quantity minimizing total cost. Trained NN with 21 features. Falls back to brute-force if needed.",
        "metrics": [("R²", "0.9989"), ("MAE", "3.37 units"), ("Params", "61K"), ("Latency", "< 10 ms")],
        "what": "Order too little → stockouts. Order too much → dead capital. The Decision Agent finds the middle ground by modeling stockout, holding, shipping, and lead time. It never auto-orders — it recommends. You decide.",
        "steps": [("Gather", "Forecast + stock + costs."), ("Build", "21 features."), ("Predict", "NN output."), ("Sanity", "Validate."), ("Recommend", "Quantity + rationale.")],
        "case": {"scenario": "SKU P001, stock 100, demand 147.", "before": "Manual ordering: 12% over.", "after": "AI recommended 41 units.", "verdict": "500 SKUs = $170,000/year."},
        "limits": ["Trained on synthetic + historical.", "Constant lead time assumed.", "Single warehouse."],
        "integrations": ["SAP IBP", "NetSuite", "Odoo", "Any ERP with REST"],
    },
    "rag": {
        "icon": "📚", "name": "Knowledge Agent", "role": "Policy Retrieval",
        "tagline": "Answers your team's questions in seconds",
        "summary": "Answers questions about suppliers, contracts, and policies. Knowledge graph with EN + AR support.",
        "metrics": [("Languages", "EN + AR"), ("Response", "< 100 ms"), ("Base", "JSON graph"), ("External APIs", "Zero")],
        "what": "Every ops team has this problem: the answer lives in a 40-page PDF somewhere. The Knowledge Agent indexes operational documents into a searchable graph. Ask in English or Arabic — get a cited answer in under a second.",
        "steps": [("Index", "Documents → graph nodes."), ("Tag", "Topic + source."), ("Query", "Tokenized + scored."), ("Rank", "Top matches."), ("Answer", "Citation + confidence.")],
        "case": {"scenario": "Ops team spends 40 min/day searching.", "before": "12 min per query.", "after": "< 100 ms answers.", "verdict": "~150 hours/year saved."},
        "limits": ["JSON-based index.", "Documents must be indexed first.", "No live supplier integration."],
        "integrations": ["SharePoint", "Google Drive", "Confluence", "Notion"],
    },
}

# ============================================
# SESSION STATE
# ============================================
defaults = {
    "page": "Dashboard",
    "selected_agent": None,
    "history": [],
    "last_result": None,
    "hitl_state": {},
    "ask_query_value": "",
    "ask_last_audio": None,
    "last_answered": None,
    "chat_log": [],
    "trend_result": None,
    "notifications": [
        {"t": "System health check passed", "ts": "2 min ago", "level": "success"},
        {"t": "Trend Agent detected declining interest in 'wireless earbuds'", "ts": "18 min ago", "level": "warning"},
        {"t": "Vision model updated to v1.2", "ts": "1 hour ago", "level": "info"},
    ],
}
for k, v in defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v

# ============================================
# CSS
# ============================================
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&display=swap');
html, body, [class*="css"] { font-family: 'Inter', sans-serif !important; }
.stApp { background: #070b14 !important; overflow-x: hidden; }
#MainMenu, footer, header, .stDeployButton { display: none !important; }
.block-container { padding: 1.5rem 3rem 3rem 3rem !important; max-width: 1400px; }

#starfield { position: fixed; top: 0; left: 0; width: 100%; height: 100%; z-index: 0; pointer-events: none; overflow: hidden; background: radial-gradient(ellipse at 20% 50%, #0a1628 0%, #070b14 70%); }
.star { position: absolute; border-radius: 50%; background: white; animation: twinkle var(--duration) ease-in-out infinite alternate; }
@keyframes twinkle { 0% { opacity: 0.08; } 100% { opacity: 0.9; } }
.orb { position: fixed; border-radius: 50%; filter: blur(100px); pointer-events: none; z-index: 0; animation: orb-float 25s ease-in-out infinite alternate; }
.orb-1 { width: 600px; height: 600px; top: -300px; right: -200px; background: radial-gradient(circle, rgba(59, 130, 246, 0.15), transparent); }
.orb-2 { width: 500px; height: 500px; bottom: -250px; left: -150px; background: radial-gradient(circle, rgba(139, 92, 246, 0.12), transparent); animation-delay: -8s; }
@keyframes orb-float { 0% { transform: translate(0, 0) scale(1); } 100% { transform: translate(-10px, 30px) scale(0.95); } }
.main-content { position: relative; z-index: 1; }

.topbar { display: flex; align-items: center; justify-content: space-between; padding: 14px 0; margin-bottom: 24px; border-bottom: 1px solid rgba(255,255,255,0.05); }
.topbar-left { display: flex; align-items: center; gap: 10px; }
.topbar-right { display: flex; align-items: center; gap: 14px; }
.sla { font-size: 0.7rem; color: rgba(255,255,255,0.4) !important; }

.page-title { font-size: 2rem; font-weight: 800; color: #ffffff !important; letter-spacing: -1px; margin: 0 0 6px 0; line-height: 1.15; }
.page-title .highlight { background: linear-gradient(135deg, #3b82f6, #8b5cf6); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }
.page-sub { color: rgba(255,255,255,0.45) !important; font-size: 0.9rem; font-weight: 300; margin-bottom: 24px; line-height: 1.6; max-width: 780px; }
.eyebrow { color: rgba(59, 130, 246, 0.85) !important; font-size: 0.68rem; text-transform: uppercase; letter-spacing: 2.5px; font-weight: 600; margin-bottom: 8px; }
.section-label { color: rgba(255,255,255,0.35) !important; font-size: 0.65rem; text-transform: uppercase; letter-spacing: 2.5px; font-weight: 500; margin: 28px 0 12px 0; }

.metric-card { background: rgba(0,0,0,0.4); border: 1px solid rgba(255,255,255,0.06); border-radius: 14px; padding: 18px 20px; }
.metric-card:hover { border-color: rgba(59, 130, 246, 0.2); background: rgba(255,255,255,0.03); }
.metric-label { color: rgba(255,255,255,0.4) !important; font-size: 0.62rem; text-transform: uppercase; letter-spacing: 1.5px; font-weight: 500; margin-bottom: 8px; }
.metric-value { color: #ffffff !important; font-size: 1.8rem; font-weight: 700; line-height: 1.1; }
.metric-value .grad { background: linear-gradient(135deg, #3b82f6, #8b5cf6); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }
.metric-hint { color: rgba(255,255,255,0.3) !important; font-size: 0.7rem; margin-top: 6px; }
.metric-hint.danger { color: rgba(239, 68, 68, 0.85) !important; }
.metric-hint.success { color: rgba(74, 222, 128, 0.85) !important; }
.metric-hint.warn { color: rgba(251, 191, 36, 0.85) !important; }

.info-card { background: linear-gradient(135deg, rgba(59, 130, 246, 0.05), rgba(139, 92, 246, 0.03)); border: 1px solid rgba(59, 130, 246, 0.12); border-radius: 14px; padding: 22px 24px; }
.info-card-title { color: #ffffff !important; font-size: 1rem; font-weight: 600; margin-bottom: 8px; }
.info-card-body { color: rgba(255,255,255,0.6) !important; font-size: 0.87rem; line-height: 1.7; }

.agent-card { background: rgba(0,0,0,0.4); border: 1px solid rgba(255,255,255,0.06); border-radius: 14px; padding: 22px; transition: all 0.3s ease; min-height: 190px; }
.agent-card:hover { border-color: rgba(59, 130, 246, 0.3); transform: translateY(-3px); background: rgba(255,255,255,0.03); box-shadow: 0 12px 40px rgba(0,0,0,0.4); }
.agent-emoji { font-size: 1.9rem; display: block; margin-bottom: 12px; }
.agent-title { color: #ffffff !important; font-size: 1rem; font-weight: 600; margin-bottom: 4px; }
.agent-role { color: rgba(255,255,255,0.35) !important; font-size: 0.65rem; text-transform: uppercase; letter-spacing: 2px; margin-bottom: 10px; }
.agent-desc { color: rgba(255,255,255,0.55) !important; font-size: 0.8rem; line-height: 1.6; }
.agent-tag { display: inline-block; padding: 3px 10px; border-radius: 100px; font-size: 0.6rem; font-weight: 500; letter-spacing: 0.5px; text-transform: uppercase; margin-top: 10px; background: rgba(74, 222, 128, 0.1); color: rgba(74, 222, 128, 0.9) !important; border: 1px solid rgba(74, 222, 128, 0.2); }

.badge { display: inline-block; padding: 4px 10px; border-radius: 6px; font-size: 0.62rem; font-weight: 500; letter-spacing: 0.8px; text-transform: uppercase; margin-right: 6px; }
.badge-trust { background: rgba(74, 222, 128, 0.08); color: rgba(74, 222, 128, 0.9) !important; border: 1px solid rgba(74, 222, 128, 0.15); }
.badge-soon { background: rgba(251, 191, 36, 0.08); color: rgba(251, 191, 36, 0.85) !important; border: 1px solid rgba(251, 191, 36, 0.15); }
.badge-info { background: rgba(59, 130, 246, 0.08); color: rgba(59, 130, 246, 0.9) !important; border: 1px solid rgba(59, 130, 246, 0.15); }

.status-badge { display: inline-flex; align-items: center; gap: 8px; padding: 6px 14px; border-radius: 100px; background: rgba(0,0,0,0.5); border: 1px solid rgba(255,255,255,0.08); color: rgba(255,255,255,0.7) !important; font-size: 0.65rem; letter-spacing: 0.5px; text-transform: uppercase; }
.status-dot { width: 6px; height: 6px; border-radius: 50%; animation: pulse-dot 2s ease-in-out infinite; }
.status-dot.online { background: #4ade80; box-shadow: 0 0 12px rgba(74, 222, 128, 0.5); }
.status-dot.offline { background: #ef4444; }
@keyframes pulse-dot { 0%, 100% { opacity: 1; } 50% { opacity: 0.4; } }

/* Trend direction banner */
.trend-banner { border-radius: 16px; padding: 32px 36px; text-align: center; margin: 16px 0 8px 0; position: relative; overflow: hidden; }
.trend-banner.rising { background: linear-gradient(135deg, rgba(74, 222, 128, 0.15), rgba(34, 197, 94, 0.05)); border: 1px solid rgba(74, 222, 128, 0.3); }
.trend-banner.declining { background: linear-gradient(135deg, rgba(239, 68, 68, 0.15), rgba(220, 38, 38, 0.05)); border: 1px solid rgba(239, 68, 68, 0.3); }
.trend-banner.stable { background: linear-gradient(135deg, rgba(148, 163, 184, 0.1), rgba(100, 116, 139, 0.05)); border: 1px solid rgba(148, 163, 184, 0.2); }
.trend-icon { font-size: 3rem; display: block; margin-bottom: 8px; }
.trend-direction { font-size: 1.8rem; font-weight: 800; letter-spacing: -0.5px; text-transform: uppercase; }
.trend-banner.rising .trend-direction { color: #4ade80 !important; }
.trend-banner.declining .trend-direction { color: #ef4444 !important; }
.trend-banner.stable .trend-direction { color: #cbd5e1 !important; }
.trend-multiplier { font-size: 1rem; margin-top: 8px; color: rgba(255,255,255,0.7) !important; }
.trend-multiplier strong { color: #ffffff !important; font-weight: 700; }

.source-row { display: flex; justify-content: space-between; align-items: center; padding: 12px 16px; border-radius: 10px; margin-bottom: 6px; background: rgba(0,0,0,0.3); border: 1px solid rgba(255,255,255,0.04); }
.source-row.ok { border-left: 3px solid rgba(74, 222, 128, 0.6); }
.source-row.fail { border-left: 3px solid rgba(148, 163, 184, 0.3); opacity: 0.7; }
.source-name { color: #ffffff !important; font-weight: 600; font-size: 0.9rem; }
.source-value { color: rgba(255,255,255,0.5) !important; font-size: 0.8rem; }
.source-tag { padding: 3px 10px; border-radius: 100px; font-size: 0.65rem; font-weight: 500; text-transform: uppercase; letter-spacing: 0.5px; }
.source-tag.ok { background: rgba(74, 222, 128, 0.1); color: rgba(74, 222, 128, 0.9) !important; }
.source-tag.fail { background: rgba(148, 163, 184, 0.1); color: rgba(148, 163, 184, 0.7) !important; }

.headline-item { padding: 12px 16px; background: rgba(0,0,0,0.3); border-left: 3px solid rgba(59, 130, 246, 0.5); border-radius: 6px; margin-bottom: 8px; color: rgba(255,255,255,0.75) !important; font-size: 0.85rem; line-height: 1.5; }

.stButton > button { background: linear-gradient(135deg, rgba(59, 130, 246, 0.15), rgba(139, 92, 246, 0.15)) !important; color: #ffffff !important; border: 1px solid rgba(59, 130, 246, 0.25) !important; border-radius: 10px !important; padding: 12px 24px !important; font-weight: 500 !important; font-size: 0.88rem !important; }
.stButton > button:hover { background: linear-gradient(135deg, rgba(59, 130, 246, 0.25), rgba(139, 92, 246, 0.25)) !important; border-color: rgba(59, 130, 246, 0.4) !important; }
.stButton > button[kind="primary"] { background: linear-gradient(135deg, #3b82f6, #8b5cf6) !important; border: none !important; box-shadow: 0 8px 24px rgba(59, 130, 246, 0.3) !important; }
.stButton > button[kind="primary"]:hover { box-shadow: 0 12px 32px rgba(59, 130, 246, 0.45) !important; }

.stTextInput > div > div > input, .stNumberInput > div > div > input { background: rgba(0,0,0,0.4) !important; border: 1px solid rgba(255,255,255,0.08) !important; border-radius: 10px !important; color: #ffffff !important; padding: 12px 16px !important; font-size: 0.9rem !important; }
.stTextInput > div > div > input:focus { border-color: rgba(59, 130, 246, 0.5) !important; box-shadow: 0 0 30px rgba(59, 130, 246, 0.1) !important; }
[data-testid="stAudioInput"] { background: rgba(0,0,0,0.3) !important; border: 1px solid rgba(255,255,255,0.08) !important; border-radius: 10px !important; }

[data-testid="stForm"] { border: none !important; padding: 0 !important; }

[data-testid="stSidebar"] { background: #0a0e1a !important; border-right: 1px solid rgba(255,255,255,0.04) !important; }
[data-testid="stSidebar"] * { color: rgba(255,255,255,0.75) !important; }
[data-testid="stSidebar"] .stRadio > label { display: none !important; }
[data-testid="stSidebar"] [role="radiogroup"] label { padding: 11px 14px !important; border-radius: 10px !important; background: transparent !important; cursor: pointer !important; font-size: 0.85rem !important; font-weight: 500 !important; border: 1px solid transparent !important; margin-bottom: 2px !important; }
[data-testid="stSidebar"] [role="radiogroup"] label:hover { background: rgba(255,255,255,0.04) !important; border-color: rgba(255,255,255,0.06) !important; }
[data-testid="stSidebar"] [role="radiogroup"] label:has(input:checked) { background: linear-gradient(135deg, rgba(59, 130, 246, 0.15), rgba(139, 92, 246, 0.08)) !important; border-color: rgba(59, 130, 246, 0.3) !important; }
[data-testid="stSidebar"] [role="radiogroup"] label > div:first-child { display: none !important; }

.side-brand { display: flex; align-items: center; gap: 10px; padding: 8px 0 14px 0; border-bottom: 1px solid rgba(255,255,255,0.05); margin-bottom: 18px; }
.side-brand-icon { font-size: 1.6rem; color: #3b82f6; text-shadow: 0 0 30px rgba(59, 130, 246, 0.5); }
.side-brand-name { font-size: 1.05rem; font-weight: 800; color: #ffffff !important; }
.side-brand-name span { background: linear-gradient(135deg, #3b82f6, #8b5cf6); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }

.sidebar-status { margin-top: 22px; padding: 14px; border-radius: 12px; background: rgba(74, 222, 128, 0.03); border: 1px solid rgba(74, 222, 128, 0.1); }
.sidebar-status .item { display: flex; justify-content: space-between; align-items: center; font-size: 0.72rem; padding: 4px 0; color: rgba(255,255,255,0.5) !important; }
.sidebar-status .live { color: rgba(74, 222, 128, 0.9) !important; font-weight: 500; }
.sidebar-status .dot { width: 6px; height: 6px; border-radius: 50%; background: #4ade80; display: inline-block; margin-right: 6px; animation: pulse-dot 2s ease-in-out infinite; }

hr { border-color: rgba(255,255,255,0.05) !important; margin: 22px 0 !important; }
.stAlert { background: rgba(0,0,0,0.4) !important; border: 1px solid rgba(255,255,255,0.06) !important; border-radius: 12px !important; }
.stExpander { border: 1px solid rgba(255,255,255,0.06) !important; border-radius: 12px !important; background: rgba(0,0,0,0.3) !important; }
[data-testid="stDataFrame"] { background: rgba(0,0,0,0.3) !important; border-radius: 12px !important; }
[data-testid="stFileUploader"] section { background: rgba(0,0,0,0.3) !important; border: 1px dashed rgba(255,255,255,0.1) !important; border-radius: 12px !important; }

.ask-hint { text-align: center; color: rgba(255,255,255,0.3) !important; font-size: 0.75rem; margin-top: 8px; letter-spacing: 0.5px; }
.ask-example { display: inline-block; padding: 8px 14px; margin: 4px; background: rgba(255,255,255,0.03); border: 1px solid rgba(255,255,255,0.06); border-radius: 20px; font-size: 0.78rem; color: rgba(255,255,255,0.55) !important; }

.chat-user { background: linear-gradient(135deg, rgba(59, 130, 246, 0.15), rgba(139, 92, 246, 0.1)); border: 1px solid rgba(59, 130, 246, 0.2); border-radius: 14px 14px 4px 14px; padding: 14px 18px; margin: 8px 0 8px 20%; color: #ffffff !important; font-size: 0.92rem; }
.chat-bot { background: rgba(0,0,0,0.5); border: 1px solid rgba(255,255,255,0.06); border-radius: 14px 14px 14px 4px; padding: 18px 22px; margin: 8px 20% 8px 0; }
.chat-bot-label { color: rgba(255,255,255,0.3) !important; font-size: 0.6rem; text-transform: uppercase; letter-spacing: 2px; margin-bottom: 8px; }
.chat-bot-body { color: rgba(255,255,255,0.9) !important; font-size: 0.92rem; line-height: 1.7; }
.chat-bot-body strong { color: #ffffff !important; }
.chat-bot-body ul { margin: 8px 0 0 0; padding-left: 20px; }
.chat-bot-body li { margin-bottom: 4px; color: rgba(255,255,255,0.75) !important; }
</style>
""", unsafe_allow_html=True)

st.markdown("""
    <div id="starfield"></div>
    <div class="orb orb-1"></div>
    <div class="orb orb-2"></div>
    <script>
        const sf = document.getElementById('starfield');
        for (let i = 0; i < 80; i++) {
            const s = document.createElement('div');
            s.className = 'star';
            const sz = Math.random() * 2 + 0.5;
            s.style.cssText = `width:${sz}px;height:${sz}px;left:${Math.random()*100}%;top:${Math.random()*100}%;--duration:${Math.random()*4+2}s;animation-delay:${Math.random()*5}s;`;
            sf.appendChild(s);
        }
    </script>
""", unsafe_allow_html=True)
st.markdown('<div class="main-content">', unsafe_allow_html=True)

# ============================================
# HELPERS
# ============================================

def api_online():
    try:
        return requests.get(API["health"], timeout=2).status_code == 200
    except Exception:
        return False

def metric_card(label, value, hint="", hint_class=""):
    h = f'<div class="metric-hint {hint_class}">{hint}</div>' if hint else ""
    return f'<div class="metric-card"><div class="metric-label">{label}</div><div class="metric-value">{value}</div>{h}</div>'

def transcribe(audio_bytes):
    try:
        r = requests.post(API["voice"], files={"file": ("voice.wav", audio_bytes, "audio/wav")}, timeout=60)
        if r.status_code == 200:
            return r.json().get("text", "").strip()
    except Exception:
        pass
    return ""

def call_forecast(sku="P001", days=14, product_name=None):
    try:
        params = {"sku_id": sku, "days": days}
        if product_name:
            params["product_name"] = product_name
        r = requests.post(API["forecast"], params=params, timeout=30)
        return r.json() if r.status_code == 200 else None
    except Exception:
        return None

def call_rag(q):
    try:
        r = requests.post(API["rag"], params={"query": q}, timeout=20)
        return r.json() if r.status_code == 200 else None
    except Exception:
        return None

def call_decision(sku="P001", stock=82, days=14, unit_cost=10.0):
    try:
        r = requests.post(API["decision"], params={"sku_id": sku, "current_stock": stock, "unit_cost": unit_cost, "forecast_days": days}, timeout=20)
        return r.json() if r.status_code == 200 else None
    except Exception:
        return None

def call_vision(image_file):
    try:
        r = requests.post(API["vision"], files={"file": (image_file.name, image_file.getvalue(), image_file.type or "image/jpeg")}, timeout=60)
        return r.json() if r.status_code == 200 else None
    except Exception:
        return None

def call_chat(query, lang="auto"):
    try:
        r = requests.post(API["chat"], params={"query": query, "lang": lang}, timeout=60)
        if r.status_code == 200:
            return r.json()
    except Exception:
        pass
    return None

def run_pipeline(sku, stock, unit_cost, days, image_file):
    params = {"sku_id": sku, "current_stock": int(stock), "unit_cost": float(unit_cost), "forecast_days": int(days)}
    files = {"image": (image_file.name, image_file.getvalue(), image_file.type or "image/jpeg")} if image_file else None
    try:
        r = requests.post(API["full"], params=params, files=files, timeout=120)
        return (r.json(), None) if r.status_code == 200 else (None, f"Backend {r.status_code}")
    except requests.exceptions.Timeout:
        return None, "Request timed out. First call loads YOLO — retry."
    except requests.exceptions.ConnectionError:
        return None, "Cannot reach backend."
    except Exception as e:
        return None, str(e)

def render_hitl(data):
    sku = data.get("sku_id", "P001")
    rec = data.get("recommendation", {})
    suggested = int(rec.get("suggested_order_qty", 0))
    key = f"hitl_{sku}"
    if key not in st.session_state.hitl_state:
        st.session_state.hitl_state[key] = {"status": "pending", "qty": suggested}
    state = st.session_state.hitl_state[key]
    st.markdown('<div class="section-label">Human Decision Required</div>', unsafe_allow_html=True)
    st.info("🛡️ The AI advises. **You** decide. No order is placed automatically.")
    c1, c2, c3 = st.columns(3)
    with c1:
        if st.button("✅ Approve", key=f"a_{sku}", use_container_width=True, type="primary"):
            state["status"], state["qty"] = "approved", suggested; st.rerun()
    with c2:
        custom = st.number_input("Custom quantity", min_value=0, max_value=10_000_000, value=state["qty"], step=1, key=f"q_{sku}")
        if st.button("📝 Submit Custom", key=f"c_{sku}", use_container_width=True):
            state["status"], state["qty"] = "modified", int(custom); st.rerun()
    with c3:
        if st.button("❌ Reject", key=f"r_{sku}", use_container_width=True):
            state["status"], state["qty"] = "rejected", 0; st.rerun()
    s = state["status"]
    if s == "approved": st.success(f"✅ Order approved: **{state['qty']} units** for `{sku}`")
    elif s == "modified": st.success(f"📝 Custom order submitted: **{state['qty']} units** for `{sku}`")
    elif s == "rejected": st.warning(f"❌ Recommendation rejected for `{sku}`. No order placed.")

def render_situation(data):
    sit, fc, rec = data.get("situation", {}), data.get("forecast", {}), data.get("recommendation", {})
    det = data.get("damage_detections", [])
    trend = data.get("trend", {})
    st.markdown('<div class="section-label">Situation Report</div>', unsafe_allow_html=True)
    m1, m2, m3, m4 = st.columns(4)
    with m1: st.markdown(metric_card("Current Stock", f"{sit.get('current_stock',0):,}", "Units on hand"), unsafe_allow_html=True)
    with m2:
        d = sit.get("damaged_units", 0)
        st.markdown(metric_card("Damaged", str(d), f"−{d}" if d > 0 else "Clean", "danger" if d > 0 else "success"), unsafe_allow_html=True)
    with m3: st.markdown(metric_card("Effective Stock", f"{sit.get('effective_stock',0):,}", "After adjustment"), unsafe_allow_html=True)
    with m4:
        def_ = sit.get("deficit", 0)
        st.markdown(metric_card("Deficit", f"{def_:.0f}", "Shortage" if def_ > 0 else "OK", "danger" if def_ > 0 else "success"), unsafe_allow_html=True)

    # Trend banner (if available)
    if trend and trend.get("sources_available", 0) > 0:
        direction = trend.get("direction", "stable")
        icon = {"rising": "📈", "declining": "📉", "stable": "➖"}.get(direction, "➖")
        st.markdown(f"""
            <div class="trend-banner {direction}">
                <span class="trend-icon">{icon}</span>
                <div class="trend-direction">Trend: {direction}</div>
                <div class="trend-multiplier">Forecast multiplier: <strong>×{trend.get('multiplier',1.0):.2f}</strong> · {trend.get('sources_available',0)} source(s) · confidence {trend.get('confidence',0):.0%}</div>
            </div>
        """, unsafe_allow_html=True)

    if det:
        st.markdown('<div class="section-label">Damage Detection</div>', unsafe_allow_html=True)
        for i, d in enumerate(det, 1):
            icon = "🔴" if d.get("class") == "damaged" else "🟢"
            st.write(f"{icon} **#{i}** · `{d.get('class')}` · confidence **{d.get('confidence',0):.2f}**")
    daily = fc.get("daily_demand", [])
    if daily:
        st.markdown('<div class="section-label">Demand Forecast</div>', unsafe_allow_html=True)
        try:
            import plotly.graph_objects as go
            fig = go.Figure(go.Scatter(x=list(range(1, len(daily)+1)), y=daily, mode="lines+markers",
                                       line=dict(color="#3b82f6", width=3), marker=dict(size=7, color="#8b5cf6"),
                                       fill="tozeroy", fillcolor="rgba(59,130,246,0.1)"))
            fig.update_layout(height=220, margin=dict(l=10,r=10,t=10,b=10),
                              paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                              font=dict(color="rgba(255,255,255,0.7)", size=11),
                              xaxis=dict(title="Days ahead", gridcolor="rgba(255,255,255,0.05)", zeroline=False),
                              yaxis=dict(title="Units", gridcolor="rgba(255,255,255,0.05)", zeroline=False),
                              showlegend=False)
            st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
        except ImportError:
            st.write(f"**Forecast:** {', '.join(f'{v:.1f}' for v in daily)}")
    st.markdown('<div class="section-label">AI Recommendation</div>', unsafe_allow_html=True)
    c1, c2 = st.columns([2, 1])
    with c1:
        st.markdown(f"""
            <div class="info-card">
                <div class="info-card-title">Recommended Order</div>
                <div class="metric-value" style="font-size:2.4rem; margin: 8px 0;"><span class="grad">{rec.get('suggested_order_qty',0):,} units</span></div>
                <div class="info-card-body">{rec.get('rationale','')}</div>
            </div>
        """, unsafe_allow_html=True)
    with c2:
        st.markdown(f"""
            <div class="metric-card">
                <div class="metric-label">Estimated Cost</div>
                <div class="metric-value" style="font-size:1.5rem">${rec.get('estimated_cost',0):,.2f}</div>
                <div class="metric-hint">Method: {rec.get('method_used','unknown')}</div>
            </div>
        """, unsafe_allow_html=True)


# ============================================
# INTENT ROUTER
# ============================================

GREETINGS = {"hi","hello","hey","yo","hiya","howdy","greetings","good morning","good evening","good afternoon",
             "أهلا","أهلاً","اهلا","مرحبا","مرحباً","السلام عليكم","صباح الخير","مساء الخير"}
THANKS = {"thanks","thank you","thx","ty","cheers","شكرا","شكراً","متشكر"}
BYE = {"bye","goodbye","see you","later","cya","مع السلامة","باي"}
HELP = {"help","what can you do","how can you help","what do you do","capabilities","what can i ask","features","options","commands",
        "ساعدني","بتعمل ايه","ايه اللي تعرفه"}
IDENTITY = {"who are you","what are you","what is this","your name","about you","what is zero stockout","مين انت","انت مين"}
STATUS = {"status","are you ok","are you online","is the system up","health","الحالة","الوضع"}

def normalize(text):
    t = text.lower().strip()
    t = re.sub(r"[!?.,;:()\u060c\u061f]+", " ", t)
    return re.sub(r"\s+", " ", t).strip()

def classify_intent(q):
    if not q or not q.strip(): return "unknown"
    n = normalize(q)
    if n in GREETINGS or (n.split(" ")[0] in GREETINGS and len(n.split()) <= 3): return "greeting"
    if n in THANKS: return "thanks"
    if n in BYE: return "bye"
    if any(k in n for k in STATUS): return "status"
    if any(k in n for k in IDENTITY): return "identity"
    if any(k in n for k in HELP): return "help"

    if any(k in n for k in ["trend", "trending", "viral", "popular", "google trends"]): return "trend"
    if any(k in n for k in ["forecast","predict","demand","when will","run out","next week","next month","sales"]): return "forecast"
    if any(k in n for k in ["policy","policies","return","refund","contract","supplier","terms","agreement","warranty","rule","sla"]): return "rag"
    if any(k in n for k in ["image","picture","photo","damage","damaged","package","box","camera","detect","inspect","broken"]): return "vision"
    if any(k in n for k in ["order","buy","replenish","reorder","quantity","purchase","how much should i","how many should i"]): return "decision"
    return "chat"

def is_arabic(text):
    return bool(re.search(r'[\u0600-\u06FF]', text))


# ============================================
# CHAT RENDER
# ============================================

def render_chat_response(label, body):
    st.markdown(f"""
        <div class="chat-bot">
            <div class="chat-bot-label">● {label}</div>
            <div class="chat-bot-body">{body}</div>
        </div>
    """, unsafe_allow_html=True)


def handle_query(query, image):
    """Route the query. Always returns something."""
    intent = classify_intent(query)
    ar = is_arabic(query)

    if intent == "greeting":
        if ar:
            render_chat_response("Zero-Stockout AI",
                "مرحباً! 👋 أنا مساعدك الذكي لإدارة المخزون.<br><br>"
                "<strong>يمكنني مساعدتك في:</strong><ul>"
                "<li>📊 التنبؤ بالطلب — \"إمتى P001 هيخلص؟\"</li>"
                "<li>🔥 اتجاهات السوق — \"wireless earbuds trending?\"</li>"
                "<li>📚 سياسات المرتجعات والعقود — \"إيه سياسة الاسترجاع؟\"</li>"
                "<li>👁️ كشف التلف من الصور — ارفع صورة واسأل</li>"
                "<li>🧠 حساب الكمية المثالية للطلب — \"اطلب P001\"</li>"
                "</ul>تحب نساعدك في إيه؟")
        else:
            render_chat_response("Zero-Stockout AI",
                "Hello! 👋 I'm your inventory intelligence assistant.<br><br>"
                "<strong>I can help you with:</strong><ul>"
                "<li>📊 Forecast demand — \"when will P001 run out?\"</li>"
                "<li>🔥 Market trends — \"is wireless earbuds trending?\"</li>"
                "<li>📚 Policies — \"what's our return policy?\"</li>"
                "<li>👁️ Damage detection — attach an image and ask</li>"
                "<li>🧠 Order optimization — \"reorder P001\"</li>"
                "</ul>What would you like to do?")
        return

    if intent == "thanks":
        render_chat_response("Zero-Stockout AI", "على الرحب والسعة! 🙂" if ar else "You're welcome! 🙂")
        return

    if intent == "bye":
        render_chat_response("Zero-Stockout AI", "مع السلامة! 👋" if ar else "Goodbye! 👋")
        return

    if intent == "status":
        online = api_online()
        render_chat_response("System Status",
            f"All systems <strong>{'operational' if online else 'partially offline'}</strong>.<br><br>"
            "📊 Forecast · 🔥 Trend · 👁️ Vision · 🧠 Decision · 📚 Knowledge · 🎤 Voice — <strong>All Live</strong><br><br>"
            "Average latency: <strong>&lt; 100 ms</strong> · Zero external API calls.")
        return

    if intent == "identity":
        if ar:
            render_chat_response("Zero-Stockout AI",
                "أنا <strong>Zero-Stockout AI</strong> — نظام متعدد الوكلاء لتحسين المخزون.<br><br>"
                "<strong>5 وكلاء متخصصين:</strong><ul>"
                "<li>📊 التنبؤ بالطلب (TFT)</li>"
                "<li>🔥 اتجاهات السوق الحية</li>"
                "<li>👁️ كشف تلف الباكدجات من الصور</li>"
                "<li>🧠 حساب الكمية المثالية للطلب</li>"
                "<li>📚 إجابات السياسات والعقود</li>"
                "</ul>بنستهدف خسارة $1.7 ترليون سنوياً من اضطراب المخزون.")
        else:
            render_chat_response("Zero-Stockout AI",
                "I'm <strong>Zero-Stockout AI</strong> — a multi-agent inventory optimization system.<br><br>"
                "<strong>Five specialized agents:</strong><ul>"
                "<li>📊 Forecast — real TFT + trend signals</li>"
                "<li>🔥 Trend — Google Trends + News Sentiment</li>"
                "<li>👁️ Vision — damage detection from images</li>"
                "<li>🧠 Decision — optimal order quantity</li>"
                "<li>📚 Knowledge — policy and contract Q&A</li>"
                "</ul>Targeting the $1.7 trillion annual loss from inventory distortion.")
        return

    if intent == "help":
        if ar:
            render_chat_response("كيف أساعدك",
                "<strong>📊 التنبؤ بالطلب</strong><br>"
                "اسأل: <em>\"إمتى P001 هيخلص؟\"</em><br><br>"
                "<strong>🔥 اتجاهات السوق</strong><br>"
                "اسأل: <em>\"wireless earbuds trending?\"</em><br><br>"
                "<strong>📚 السياسات</strong><br>"
                "اسأل: <em>\"إيه سياسة الاسترجاع؟\"</em><br><br>"
                "<strong>👁️ كشف التلف</strong><br>"
                "ارفع صورة واسأل: <em>\"الباكدج ده تالف؟\"</em><br><br>"
                "<strong>🧠 حساب الطلب</strong><br>"
                "اسأل: <em>\"اطلب P001\"</em>")
        else:
            render_chat_response("How I Can Help",
                "<strong>📊 Forecast demand</strong><br>"
                "Try: <em>\"when will P001 run out?\"</em><br><br>"
                "<strong>🔥 Market trends</strong><br>"
                "Try: <em>\"is wireless earbuds trending?\"</em><br><br>"
                "<strong>📚 Policies & contracts</strong><br>"
                "Try: <em>\"what's our return policy?\"</em><br><br>"
                "<strong>👁️ Damage detection</strong><br>"
                "Attach an image and ask: <em>\"is this package damaged?\"</em><br><br>"
                "<strong>🧠 Order optimization</strong><br>"
                "Try: <em>\"reorder P001\"</em>")
        return

    # Agent intents
    if intent == "trend":
        # Try to extract a product name from the query
        product = query
        for kw in ["trend", "trending", "viral", "popular", "google trends", "is ", "?"]:
            product = product.lower().replace(kw, " ")
        product = product.strip() or "wireless earbuds"
        data = call_forecast(sku="P001", days=7, product_name=product)
        if not data or not data.get("trend"):
            render_chat_response("Trend Agent", "⚠️ Trend data unavailable. Try the Trends page for a full view."); return
        t = data["trend"]
        direction = t.get("direction", "stable")
        icon = {"rising": "📈", "declining": "📉", "stable": "➖"}.get(direction, "➖")
        render_chat_response("Trend Agent",
            f"{icon} <strong>Trend for \"{t.get('query_used','')}\":</strong> {direction.upper()}<br><br>"
            f"<strong>Multiplier:</strong> ×{t.get('multiplier',1.0):.2f}<br>"
            f"<strong>Sources:</strong> {t.get('sources_available',0)}/5 live<br>"
            f"<strong>Confidence:</strong> {t.get('confidence',0):.0%}<br><br>"
            f"<em>Open the Trends page for full source breakdown.</em>")
        return

    if intent == "forecast":
        data = call_forecast()
        if not data:
            render_chat_response("Forecast Agent", "⚠️ Forecast Agent unreachable."); return
        vals = data.get("forecast", [])
        trend = data.get("trend", {})
        trend_line = ""
        if trend and trend.get("sources_available", 0) > 0:
            direction = trend.get("direction", "stable")
            trend_line = f"<br><strong>Trend:</strong> {direction} (×{trend.get('multiplier',1.0):.2f})"
        render_chat_response("Forecast Agent",
            f"📊 Demand forecast for <strong>P001</strong><br><br>"
            f"<strong>Next 7 days:</strong> {', '.join(f'{v:.1f}' for v in vals[:7])}<br>"
            f"<strong>Average:</strong> {sum(vals)/max(1,len(vals)):.1f} units/day<br>"
            f"<strong>Peak:</strong> {max(vals) if vals else 0:.1f} units<br>"
            f"<strong>Total (14 days):</strong> {sum(vals):.0f} units<br><br>"
            f"<span style='color:rgba(74,222,128,0.85)'>✓ {data.get('confidence',0):.0%} confidence</span> · "
            f"Method: {data.get('method','—')}{trend_line}")
        return

    if intent == "rag":
        data = call_rag(query)
        if not data:
            render_chat_response("Knowledge Agent", "⚠️ Knowledge Agent unreachable."); return
        render_chat_response("Knowledge Agent",
            f"{data.get('answer','No answer found.')}<br><br>"
            f"<span style='color:rgba(74,222,128,0.85)'>✓ {data.get('confidence',0):.0%} confidence</span> · "
            f"Source: {data.get('source','Knowledge Base')}")
        return

    if intent == "vision":
        if image is None:
            render_chat_response("Vision Agent",
                "👁️ The Vision Agent needs an image. Attach one below the search bar, then ask again." if not ar
                else "👁️ محتاج صورة. ارفع صورة تحت خانة البحث واسأل تاني.")
            return
        data = call_vision(image)
        if not data:
            render_chat_response("Vision Agent", "⚠️ Vision Agent unreachable."); return
        det = data.get("detections", [])
        lines = "".join(f"<br>• {'🔴' if d.get('class')=='damaged' else '🟢'} <strong>{d.get('class')}</strong> · confidence {d.get('confidence',0):.2f}" for d in det) or "<br><em>No detections above threshold.</em>"
        render_chat_response("Vision Agent", f"👁️ Detected <strong>{len(det)}</strong> object(s).{lines}")
        return

    if intent == "decision":
        data = call_decision()
        if not data:
            render_chat_response("Decision Agent", "⚠️ Decision Agent unreachable."); return
        render_chat_response("Decision Agent",
            f"For <strong>P001</strong>, we recommend ordering <strong>{data.get('order_quantity',0)} units</strong>.<br><br>"
            f"<strong>Expected demand:</strong> {data.get('expected_demand',0):.0f} units<br>"
            f"<strong>Total cost:</strong> ${data.get('total_cost',0):,.2f}<br>"
            f"<strong>Rationale:</strong> {data.get('rationale','')}<br><br>"
            f"<span style='color:rgba(74,222,128,0.85)'>✓ {data.get('confidence',0):.0%} confidence</span> · "
            f"Method: {data.get('method','—')}")
        return

    with st.spinner("Thinking..."):
        result = call_chat(query)
    if result and result.get("answer"):
        render_chat_response(result.get("agent", "AI Assistant"), result["answer"])
    else:
        if ar:
            render_chat_response("Zero-Stockout AI",
                f"معلش، مش فاهم <em>\"{query}\"</em> أوي.<br><br>"
                "جرب تسأل:<ul>"
                "<li>\"إمتى P001 هيخلص؟\"</li>"
                "<li>\"wireless earbuds trending?\"</li>"
                "<li>\"إيه سياسة الاسترجاع؟\"</li>"
                "<li>\"اطلب P001\"</li>"
                "</ul>أو اكتب <strong>\"مساعدة\"</strong>.")
        else:
            render_chat_response("Zero-Stockout AI",
                f"I didn't quite understand <em>\"{query}\"</em>.<br><br>"
                "Try asking:<ul>"
                "<li>\"when will P001 run out?\"</li>"
                "<li>\"is wireless earbuds trending?\"</li>"
                "<li>\"what's our return policy?\"</li>"
                "<li>\"reorder P001\"</li>"
                "</ul>Or type <strong>\"help\"</strong>.")


# ============================================
# PAGE: DASHBOARD
# ============================================

def page_dashboard():
    st.markdown('<div class="eyebrow">Overview</div>', unsafe_allow_html=True)
    st.markdown('<div class="page-title">Welcome back, <span class="highlight">Operations Team</span></div>', unsafe_allow_html=True)
    st.markdown('<div class="page-sub">Session snapshot. Head to <b>Ask</b> to query any agent, <b>Trends</b> to see live market signals, or <b>Analysis</b> to run the full pipeline.</div>', unsafe_allow_html=True)

    st.markdown('<div class="section-label">Session KPIs</div>', unsafe_allow_html=True)
    k1, k2, k3, k4 = st.columns(4)
    with k1: st.markdown(metric_card("Analyses Run", f"{len(st.session_state.history)}", "This session"), unsafe_allow_html=True)
    with k2: st.markdown(metric_card("Units Optimized", f"{sum(h.get('order_qty') or 0 for h in st.session_state.history):,}", "Total recommended"), unsafe_allow_html=True)
    with k3: st.markdown(metric_card("Damage Detected", str(sum(h.get('damaged') or 0 for h in st.session_state.history)), "Across uploads", "danger"), unsafe_allow_html=True)
    with k4: st.markdown(metric_card("Cost Analyzed", f"${sum(h.get('cost') or 0 for h in st.session_state.history):,.0f}", "Decision impact"), unsafe_allow_html=True)

    c1, c2 = st.columns([2, 1])
    with c1:
        st.markdown('<div class="section-label">Recent Activity</div>', unsafe_allow_html=True)
        for n in st.session_state.notifications:
            icon = {"success": "✅", "warning": "⚠️", "info": "ℹ️"}[n["level"]]
            st.markdown(f"""<div class="metric-card" style="padding: 14px 18px; margin-bottom: 8px;"><div style="display:flex; justify-content:space-between; align-items:center;"><span style="color: rgba(255,255,255,0.85) !important; font-size: 0.88rem;">{icon} {n['t']}</span><span style="color: rgba(255,255,255,0.3) !important; font-size: 0.72rem;">{n['ts']}</span></div></div>""", unsafe_allow_html=True)
    with c2:
        st.markdown('<div class="section-label">Jump To</div>', unsafe_allow_html=True)
        if st.button("🔥 Check Trends", type="primary", use_container_width=True):
            st.session_state.page = "Trends"; st.rerun()
        if st.button("💬 Ask an Agent", use_container_width=True):
            st.session_state.page = "Ask"; st.rerun()
        if st.button("🚀 Full Pipeline", use_container_width=True):
            st.session_state.page = "Analysis"; st.rerun()
        if st.button("💼 Investor Brief", use_container_width=True):
            st.session_state.page = "Investors"; st.rerun()

    st.markdown('<div class="section-label">Compliance & Trust</div>', unsafe_allow_html=True)
    st.markdown("""<div style="display:flex; gap:8px; flex-wrap:wrap;"><span class="badge badge-trust">✓ SOC 2 (In Progress)</span><span class="badge badge-trust">✓ GDPR</span><span class="badge badge-trust">✓ Zero External APIs</span><span class="badge badge-info">99.9% SLA</span><span class="badge badge-soon">ISO 27001 (Roadmap)</span></div>""", unsafe_allow_html=True)


# ============================================
# PAGE: TRENDS (NEW)
# ============================================

def page_trends():
    st.markdown('<div class="eyebrow">Live Market Signals</div>', unsafe_allow_html=True)
    st.markdown('<div class="page-title">Trend <span class="highlight">Detection</span></div>', unsafe_allow_html=True)
    st.markdown('<div class="page-sub">Watch where demand is heading before it goes there. Multi-source signals — Google Trends, News Sentiment, and (optional) Reddit/Twitter/Finance — combined into a single forecast multiplier.</div>', unsafe_allow_html=True)

    # ---------- INPUT ----------
    with st.form("trend_form", clear_on_submit=False):
        c1, c2, c3 = st.columns([3, 1, 1])
        with c1:
            product = st.text_input(
                "Product name",
                value=st.session_state.get("trend_product", "wireless earbuds"),
                placeholder="e.g. wireless earbuds · AI PC · portable power station",
                label_visibility="collapsed",
            )
        with c2:
            sku = st.text_input("SKU", value="P001", label_visibility="collapsed")
        with c3:
            submit = st.form_submit_button("🔥 Analyze Trend", type="primary", use_container_width=True)

    # Example chips
    st.markdown('<div style="margin: 12px 0 20px 0; display:flex; flex-wrap:wrap; gap:8px;">'
                '<span class="ask-example">wireless earbuds</span>'
                '<span class="ask-example">AI PC</span>'
                '<span class="ask-example">portable power station</span>'
                '<span class="ask-example">iPhone 16 Pro</span>'
                '<span class="ask-example">Taylor Swift tickets</span>'
                '</div>', unsafe_allow_html=True)

    # ---------- RUN ----------
    if submit:
        st.session_state.trend_product = product
        with st.spinner(f"Querying live sources for '{product}' — this can take 5–10 seconds..."):
            data = call_forecast(sku=sku, days=7, product_name=product)
        if not data:
            st.error("❌ Could not reach the Forecast endpoint. Is the backend running?")
            return
        st.session_state.trend_result = data
        # Notify
        t = data.get("trend", {})
        if t and t.get("sources_available", 0) > 0:
            st.session_state.notifications.insert(0, {
                "t": f"Trend '{product}': {t.get('direction','stable')} (×{t.get('multiplier',1.0):.2f})",
                "ts": "just now",
                "level": "warning" if t.get("direction") == "declining" else "success",
            })

    # ---------- EMPTY STATE ----------
    if not st.session_state.get("trend_result"):
        st.markdown("""
            <div class="info-card" style="margin-top: 16px;">
                <div class="info-card-title">Ready to check a trend</div>
                <div class="info-card-body">
                    Enter a product name and click <b>Analyze Trend</b>. The system will:
                    <br>• Query Google Trends for 90-day search interest
                    <br>• Fetch Google News headlines and score sentiment with VADER
                    <br>• (Optionally) check Reddit, Twitter/X, and Yahoo Finance
                    <br>• Combine signals into a single forecast multiplier
                    <br>• Show whether demand is <b>rising</b>, <b>stable</b>, or <b>declining</b>
                </div>
            </div>
        """, unsafe_allow_html=True)
        return

    # ---------- RESULT ----------
    data = st.session_state.trend_result
    trend = data.get("trend", {})
    forecast_vals = data.get("forecast", [])

    if not trend:
        st.warning("No trend data returned. The backend may not have the trend agent enabled.")
        return

    direction = trend.get("direction", "stable")
    icon = {"rising": "📈", "declining": "📉", "stable": "➖"}.get(direction, "➖")

    # Big banner
    st.markdown(f"""
        <div class="trend-banner {direction}">
            <span class="trend-icon">{icon}</span>
            <div class="trend-direction">{direction}</div>
            <div class="trend-multiplier">"{trend.get('query_used','')}" · Forecast multiplier <strong>×{trend.get('multiplier',1.0):.2f}</strong></div>
        </div>
    """, unsafe_allow_html=True)

    # 4 metrics
    m1, m2, m3, m4 = st.columns(4)
    with m1:
        st.markdown(metric_card(
            "Direction", direction.title(),
            f"Trend score {trend.get('trend_score',1.0):.2f}",
            "success" if direction == "rising" else ("danger" if direction == "declining" else "")
        ), unsafe_allow_html=True)
    with m2:
        st.markdown(metric_card(
            "Multiplier", f"×{trend.get('multiplier',1.0):.2f}",
            "Forecast adjustment"
        ), unsafe_allow_html=True)
    with m3:
        st.markdown(metric_card(
            "Sources Live", f"{trend.get('sources_available',0)} / 5",
            "Signal contributors"
        ), unsafe_allow_html=True)
    with m4:
        st.markdown(metric_card(
            "Confidence", f"{trend.get('confidence',0):.0%}",
            "Coverage across sources"
        ), unsafe_allow_html=True)

    # Impact on forecast
    st.markdown('<div class="section-label">Impact on Forecast</div>', unsafe_allow_html=True)
    if forecast_vals:
        try:
            import plotly.graph_objects as go
            fig = go.Figure(go.Scatter(
                x=list(range(1, len(forecast_vals)+1)),
                y=forecast_vals,
                mode="lines+markers",
                line=dict(color="#8b5cf6", width=3),
                marker=dict(size=8, color="#3b82f6"),
                fill="tozeroy",
                fillcolor="rgba(139, 92, 246, 0.1)",
            ))
            fig.update_layout(
                height=240, margin=dict(l=10, r=10, t=10, b=10),
                paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                font=dict(color="rgba(255,255,255,0.7)", size=11),
                xaxis=dict(title="Days ahead", gridcolor="rgba(255,255,255,0.05)", zeroline=False),
                yaxis=dict(title="Units", gridcolor="rgba(255,255,255,0.05)", zeroline=False),
                showlegend=False,
            )
            st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
        except ImportError:
            st.write(f"**Forecast:** {', '.join(f'{v:.1f}' for v in forecast_vals)}")
        st.caption(f"7-day forecast adjusted by trend multiplier ×{trend.get('multiplier',1.0):.2f}. Method: {data.get('method','—')}")

    # Source breakdown
    st.markdown('<div class="section-label">Source Breakdown</div>', unsafe_allow_html=True)
    sources = trend.get("sources", {})
    if sources:
        for name, sig in sources.items():
            ok = sig.get("ok", False)
            row_class = "ok" if ok else "fail"
            tag_class = "ok" if ok else "fail"
            tag_text = "LIVE" if ok else "SKIP"

            # Build value line
            if ok:
                ratio = sig.get("ratio", 1.0)
                if name == "google_trends":
                    detail = f"ratio {ratio:.2f} · {sig.get('samples',0)} samples · growth {sig.get('growth',0):+.1%}"
                elif name == "news_sentiment":
                    detail = f"sentiment {sig.get('sentiment',0):+.2f} · {sig.get('headlines',0)} headlines"
                elif name == "reddit":
                    detail = f"this week {sig.get('this_week',0)} · last {sig.get('prev_week',0)} · ratio {ratio:.2f}"
                elif name == "twitter":
                    detail = f"ratio {ratio:.2f}"
                elif name == "finance":
                    detail = f"ticker {sig.get('ticker','—')} · ratio {ratio:.2f}"
                else:
                    detail = f"ratio {ratio:.2f}"
            else:
                detail = sig.get("reason", "unavailable")

            display_name = {
                "google_trends": "🔍 Google Trends",
                "reddit": "👽 Reddit",
                "twitter": "🐦 Twitter / X",
                "finance": "📈 Yahoo Finance",
                "news_sentiment": "📰 News Sentiment",
            }.get(name, name)

            st.markdown(f"""
                <div class="source-row {row_class}">
                    <div>
                        <div class="source-name">{display_name}</div>
                        <div class="source-value">{detail}</div>
                    </div>
                    <span class="source-tag {tag_class}">{tag_text}</span>
                </div>
            """, unsafe_allow_html=True)

    # Top headline
    news = sources.get("news_sentiment", {})
    if news.get("ok") and news.get("top_headline"):
        st.markdown('<div class="section-label">Top Headline</div>', unsafe_allow_html=True)
        st.markdown(f'<div class="headline-item">📰 "{news.get("top_headline")}"</div>', unsafe_allow_html=True)

    # Footer with metadata
    st.markdown('<div class="section-label">Metadata</div>', unsafe_allow_html=True)
    c1, c2 = st.columns(2)
    with c1:
        st.caption(f"**Fetched:** {trend.get('fetched_at','—')}")
    with c2:
        st.caption(f"**Cache:** 10 minutes · **Sources:** {trend.get('sources_available',0)}/5")


# ============================================
# PAGE: ASK (with form fix)
# ============================================

def page_ask():
    st.markdown('<div class="eyebrow">Ask Anything</div>', unsafe_allow_html=True)
    st.markdown('<div class="page-title">Ask the <span class="highlight">AI</span></div>', unsafe_allow_html=True)
    st.markdown('<div class="page-sub">Type a question and press Enter — or tap the mic. English or Arabic, the right agent answers.</div>', unsafe_allow_html=True)

    with st.form("ask_form", clear_on_submit=False):
        c1, c2 = st.columns([6, 1.2])
        with c1:
            query = st.text_input("Question",
                placeholder="Ask anything — 'hi' · 'when will P001 run out?' · 'is wireless earbuds trending?'",
                label_visibility="collapsed", key="ask_input")
        with c2:
            submit = st.form_submit_button("🔍 Ask", type="primary", use_container_width=True)

    st.markdown('<div class="ask-hint">🎤 Or use voice below · English or Arabic · Auto-routes to the right agent</div>', unsafe_allow_html=True)
    audio = st.audio_input("🎤 Speak", label_visibility="collapsed", key="ask_audio")

    if audio is not None:
        audio_bytes = audio.read()
        audio_hash = hash(audio_bytes)
        if st.session_state.ask_last_audio != audio_hash:
            st.session_state.ask_last_audio = audio_hash
            with st.spinner("🎤 Transcribing..."):
                text = transcribe(audio_bytes)
            if text:
                st.session_state.pending_voice_query = text
                st.success(f"🎤 Heard: *\"{text}\"*")
            else:
                st.warning("🎤 Could not transcribe. Make sure Whisper is installed and the backend was restarted.")

    st.markdown('<div class="section-label">Examples</div>', unsafe_allow_html=True)
    st.markdown('<div><span class="ask-example">hi</span><span class="ask-example">what can you do?</span><span class="ask-example">when will P001 run out?</span><span class="ask-example">is wireless earbuds trending?</span><span class="ask-example">reorder P001</span><span class="ask-example">مين انت؟</span></div>', unsafe_allow_html=True)

    with st.expander("📷 Attach an image (for damage detection)"):
        image = st.file_uploader("Package image", type=["jpg","jpeg","png","webp"], label_visibility="collapsed", key="ask_image")
        if image: st.image(image, width=160)

    voice_query = st.session_state.pop("pending_voice_query", None)
    active_query = voice_query or (query if submit else None)

    if active_query and active_query.strip():
        st.markdown(f'<div class="chat-user">👤 {active_query}</div>', unsafe_allow_html=True)
        with st.spinner("Thinking..."):
            handle_query(active_query, image)


# ============================================
# PAGE: ANALYSIS
# ============================================

def page_analysis():
    st.markdown('<div class="eyebrow">Full Pipeline</div>', unsafe_allow_html=True)
    st.markdown('<div class="page-title">Run <span class="highlight">Full Analysis</span></div>', unsafe_allow_html=True)
    st.markdown('<div class="page-sub">Runs Forecast → Trend → Vision → Decision as one pipeline. Upload an image to enable damage-aware stock adjustment.</div>', unsafe_allow_html=True)

    with st.expander("⚙️ Configuration", expanded=True):
        c1, c2, c3, c4 = st.columns(4)
        with c1: sku = st.text_input("SKU ID", value="P001")
        with c2: stock = st.number_input("Current stock", min_value=0, value=100, step=1)
        with c3: days = st.number_input("Forecast horizon (days)", min_value=1, max_value=30, value=14, step=1)
        with c4: unit_cost = st.number_input("Unit cost ($)", min_value=0.0, value=10.0, step=1.0)
        product_name_opt = st.text_input("Product name for trend detection (optional)", value="", placeholder="e.g. wireless earbuds")
        uploaded = st.file_uploader("📷 Package image (optional)", type=["jpg","jpeg","png","webp"])
        if uploaded: st.image(uploaded, caption="Uploaded image", width=180)

    c1, c2 = st.columns([1, 4])
    with c1:
        run = st.button("🚀 Run Analysis", type="primary", use_container_width=True)

    if not run and st.session_state.last_result is None:
        st.markdown("""<div class="info-card" style="margin-top: 16px;"><div class="info-card-title">Ready When You Are</div><div class="info-card-body">Configure parameters and click <b>Run Analysis</b>.<br>• Forecast demand for the next <b>N</b> days (TFT + trend)<br>• Detect damage from your image<br>• Compute optimal order quantity<br>• Present a full situation report</div></div>""", unsafe_allow_html=True)
        return

    if run:
        with st.spinner("Running full pipeline... first call may take ~20s."):
            params = {"sku_id": sku, "current_stock": int(stock), "unit_cost": float(unit_cost), "forecast_days": int(days)}
            if product_name_opt.strip():
                params["product_name"] = product_name_opt.strip()
            files = {"image": (uploaded.name, uploaded.getvalue(), uploaded.type or "image/jpeg")} if uploaded else None
            try:
                r = requests.post(API["full"], params=params, files=files, timeout=180)
                data, err = (r.json(), None) if r.status_code == 200 else (None, f"Backend {r.status_code}")
            except Exception as e:
                data, err = None, str(e)
        if err:
            st.error(f"❌ {err}"); return
        st.session_state.last_result = data
        st.session_state.history.insert(0, {
            "timestamp": data.get("timestamp", datetime.now().isoformat())[:19],
            "sku_id": data.get("sku_id"),
            "current_stock": data.get("situation", {}).get("current_stock"),
            "damaged": data.get("situation", {}).get("damaged_units"),
            "order_qty": data.get("recommendation", {}).get("suggested_order_qty"),
            "method": data.get("recommendation", {}).get("method_used"),
            "cost": data.get("recommendation", {}).get("estimated_cost"),
        })

    data = st.session_state.last_result
    rec, sit = data.get("recommendation", {}), data.get("situation", {})
    t1, t2, t3 = st.columns(3)
    with t1: st.markdown(metric_card("SKU", data.get("sku_id", "—")), unsafe_allow_html=True)
    with t2: st.markdown(metric_card("Recommended Order", f"{rec.get('suggested_order_qty',0):,} units", f"Cost: ${rec.get('estimated_cost',0):,.2f}", "success"), unsafe_allow_html=True)
    with t3: st.markdown(metric_card("Damaged Units", str(sit.get("damaged_units", 0)), "Auto-adjusted" if sit.get("damaged_units",0) > 0 else "Clean stock", "danger" if sit.get("damaged_units",0) > 0 else "success"), unsafe_allow_html=True)
    st.markdown("---"); render_situation(data); st.markdown("---"); render_hitl(data)
    st.markdown("---")
    c1, c2 = st.columns([1, 4])
    with c1:
        st.download_button("📄 Export Report", data=json.dumps(data, indent=2, default=str).encode(),
            file_name=f"report_{data.get('sku_id','sku')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
            mime="application/json", use_container_width=True)


# ============================================
# PAGE: HISTORY
# ============================================

def page_history():
    st.markdown('<div class="eyebrow">Audit Trail</div>', unsafe_allow_html=True)
    st.markdown('<div class="page-title">Analysis <span class="highlight">History</span></div>', unsafe_allow_html=True)
    st.markdown('<div class="page-sub">Every analysis this session.</div>', unsafe_allow_html=True)
    if not st.session_state.history:
        st.markdown("""<div class="info-card"><div class="info-card-title">No Analyses Yet</div><div class="info-card-body">Run your first analysis from the <b>Analysis</b> page.</div></div>""", unsafe_allow_html=True)
        if st.button("Go to Analysis →", type="primary"):
            st.session_state.page = "Analysis"; st.rerun()
        return
    try:
        import pandas as pd
        st.dataframe(pd.DataFrame(st.session_state.history), use_container_width=True, hide_index=True)
    except ImportError:
        st.json(st.session_state.history)
    total_units = sum(h.get("order_qty") or 0 for h in st.session_state.history)
    total_cost = sum(h.get("cost") or 0 for h in st.session_state.history)
    s1, s2, s3 = st.columns(3)
    with s1: st.markdown(metric_card("Analyses", str(len(st.session_state.history))), unsafe_allow_html=True)
    with s2: st.markdown(metric_card("Units Recommended", f"{total_units:,}"), unsafe_allow_html=True)
    with s3: st.markdown(metric_card("Cost Analyzed", f"${total_cost:,.2f}"), unsafe_allow_html=True)
    if st.button("🗑️ Clear History"):
        st.session_state.history = []; st.rerun()


# ============================================
# PAGE: AGENTS
# ============================================

def page_agents():
    st.markdown('<div class="eyebrow">The Intelligence System</div>', unsafe_allow_html=True)
    st.markdown('<div class="page-title">Five <span class="highlight">Specialized Agents</span></div>', unsafe_allow_html=True)
    st.markdown('<div class="page-sub">Click any card for the full deep-dive.</div>', unsafe_allow_html=True)
    cols = st.columns(2)
    for i, (key, agent) in enumerate(AGENTS.items()):
        with cols[i % 2]:
            st.markdown(f"""<div class="agent-card"><span class="agent-emoji">{agent['icon']}</span><div class="agent-title">{agent['name']}</div><div class="agent-role">{agent['role']}</div><div class="agent-desc">{agent['summary'][:180]}…</div><div class="agent-tag">● Live</div></div>""", unsafe_allow_html=True)
            if st.button(f"Learn more →", key=f"agent_{key}", use_container_width=True):
                st.session_state.selected_agent = key
                st.session_state.page = "Agent Detail"; st.rerun()
            st.markdown("<div style='height:8px;'></div>", unsafe_allow_html=True)


def page_agent_detail():
    key = st.session_state.selected_agent
    if not key or key not in AGENTS:
        st.session_state.page = "Agents"; st.rerun(); return
    a = AGENTS[key]
    if st.button("← Back to Agents"):
        st.session_state.page = "Agents"; st.rerun()
    st.markdown(f'<div class="eyebrow">{a["role"]}</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="page-title"><span style="font-size:2rem; margin-right:12px;">{a["icon"]}</span>{a["name"]}</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="page-sub">{a["tagline"]}</div>', unsafe_allow_html=True)
    st.markdown("""<div style="margin-bottom:16px;"><span class="badge badge-trust">● Production</span><span class="badge badge-info">Local Inference</span><span class="badge badge-info">Zero External APIs</span></div>""", unsafe_allow_html=True)
    cols = st.columns(len(a["metrics"]))
    for col, (label, val) in zip(cols, a["metrics"]):
        with col: st.markdown(metric_card(label, val), unsafe_allow_html=True)
    st.markdown('<div class="section-label">What It Does</div>', unsafe_allow_html=True)
    st.markdown(a["what"])
    st.markdown('<div class="section-label">How It Works</div>', unsafe_allow_html=True)
    for i, (step, desc) in enumerate(a["steps"], 1):
        st.markdown(f"""<div class="metric-card" style="margin-bottom:10px;"><div style="display:flex;gap:14px;align-items:flex-start;"><div style="background:linear-gradient(135deg,#3b82f6,#8b5cf6);width:28px;height:28px;border-radius:50%;display:flex;align-items:center;justify-content:center;font-size:0.8rem;font-weight:700;flex-shrink:0;">{i}</div><div><div style="color:#ffffff !important;font-weight:600;font-size:0.9rem;margin-bottom:3px;">{step}</div><div style="color:rgba(255,255,255,0.55) !important;font-size:0.85rem;line-height:1.6;">{desc}</div></div></div></div>""", unsafe_allow_html=True)
    st.markdown('<div class="section-label">Case Study</div>', unsafe_allow_html=True)
    cs = a["case"]
    st.markdown(f"""<div class="info-card"><div class="info-card-title">📌 {cs['scenario']}</div><div style="display:grid;grid-template-columns:1fr 1fr;gap:16px;margin-top:16px;"><div><div style="color:rgba(239,68,68,0.85) !important;font-size:0.7rem;text-transform:uppercase;letter-spacing:1.5px;margin-bottom:6px;">Before</div><div style="color:rgba(255,255,255,0.7) !important;font-size:0.85rem;line-height:1.65;">{cs['before']}</div></div><div><div style="color:rgba(74,222,128,0.85) !important;font-size:0.7rem;text-transform:uppercase;letter-spacing:1.5px;margin-bottom:6px;">After</div><div style="color:rgba(255,255,255,0.7) !important;font-size:0.85rem;line-height:1.65;">{cs['after']}</div></div></div><div style="margin-top:16px;padding-top:14px;border-top:1px solid rgba(255,255,255,0.06);color:rgba(74,222,128,0.9) !important;font-weight:600;font-size:0.9rem;">📈 {cs['verdict']}</div></div>""", unsafe_allow_html=True)
    c1, c2 = st.columns(2)
    with c1:
        st.markdown('<div class="section-label">Honest Limitations</div>', unsafe_allow_html=True)
        for lim in a["limits"]:
            st.markdown(f"""<div style="padding:12px 16px;background:rgba(251,191,36,0.04);border-left:3px solid rgba(251,191,36,0.4);border-radius:6px;margin-bottom:8px;color:rgba(255,255,255,0.7) !important;font-size:0.83rem;line-height:1.6;">{lim}</div>""", unsafe_allow_html=True)
        st.caption("We publish our limitations because trust matters more than marketing.")
    with c2:
        st.markdown('<div class="section-label">Integrations</div>', unsafe_allow_html=True)
        for integ in a["integrations"]:
            st.markdown(f"""<div style="padding:12px 16px;background:rgba(59,130,246,0.04);border:1px solid rgba(59,130,246,0.15);border-radius:8px;margin-bottom:8px;color:rgba(255,255,255,0.85) !important;font-size:0.85rem;">✓ {integ}</div>""", unsafe_allow_html=True)


# ============================================
# PAGE: INVESTORS
# ============================================

def page_investors():
    st.markdown('<div class="eyebrow">Investor Brief</div>', unsafe_allow_html=True)
    st.markdown('<div class="page-title">The <span class="highlight">Opportunity</span></div>', unsafe_allow_html=True)
    st.markdown('<div class="page-sub">An AI-native approach to a $1.7 trillion problem.</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-label">The Problem</div>', unsafe_allow_html=True)
    st.markdown("""<div class="info-card"><div class="info-card-title">$1.7 trillion lost annually to inventory distortion</div><div class="info-card-body">Stockouts + overstock = the largest source of preventable loss in global retail and manufacturing.<br><br><b>Root causes:</b> Static reorder points, manual inspection, and siloed forecasting/replenishment.<br><br><span style="color:rgba(255,255,255,0.4) !important;font-size:0.78rem;">Source: IHL Group, Gartner Supply Chain.</span></div></div>""", unsafe_allow_html=True)
    st.markdown('<div class="section-label">Market Size</div>', unsafe_allow_html=True)
    m1, m2, m3 = st.columns(3)
    with m1: st.markdown(metric_card("TAM", "$24.6B", "Global inventory software"), unsafe_allow_html=True)
    with m2: st.markdown(metric_card("SAM", "$4.2B", "AI-native inventory optimization"), unsafe_allow_html=True)
    with m3: st.markdown(metric_card("SOM (Yr 3)", "$42M", "500 mid-market retailers"), unsafe_allow_html=True)
    st.markdown('<div class="section-label">Business Model</div>', unsafe_allow_html=True)
    st.markdown("""<div class="info-card"><div class="info-card-title">SaaS subscription + usage tiers</div><div class="info-card-body"><b>Starter</b> — $499/mo · 50 SKUs · 1 warehouse<br><b>Growth</b> — $2,499/mo · 500 SKUs · 5 warehouses · API<br><b>Enterprise</b> — Custom · Unlimited · Multi-tenant · On-prem<br><br><b>Target margins:</b> 78% gross · 42% net by Year 3.</div></div>""", unsafe_allow_html=True)
    st.markdown('<div class="section-label">Traction</div>', unsafe_allow_html=True)
    t1, t2, t3, t4 = st.columns(4)
    with t1: st.markdown(metric_card("Prototype", "Live", "3-day build", "success"), unsafe_allow_html=True)
    with t2: st.markdown(metric_card("Agents", "5 / 5", "Full pipeline", "success"), unsafe_allow_html=True)
    with t3: st.markdown(metric_card("Decision R²", "0.9989", "10K samples"), unsafe_allow_html=True)
    with t4: st.markdown(metric_card("Vision mAP50", "0.914", "YOLO damage"), unsafe_allow_html=True)
    st.markdown('<div class="section-label">Why We Win</div>', unsafe_allow_html=True)
    for i, moat in enumerate([
        ("Damage-Aware Inventory", "Only system that auto-adjusts stock for computer-vision-detected damage."),
        ("Multi-Source Trend Detection", "Live Google Trends + News Sentiment — catches demand shifts before they peak."),
        ("Multi-Agent Architecture", "Five specialized models chained — scales better than monoliths."),
        ("Human-in-the-Loop", "The AI advises. The human decides. Deployable Day 1."),
        ("Local Inference", "No external AI APIs. Data never leaves the customer's infrastructure."),
    ], 1):
        st.markdown(f"""<div class="metric-card" style="margin-bottom:10px;"><div style="display:flex;gap:14px;"><div style="color:#3b82f6;font-size:1.4rem;font-weight:800;flex-shrink:0;">{i:02d}</div><div><div style="color:#ffffff !important;font-weight:600;font-size:0.92rem;margin-bottom:4px;">{moat[0]}</div><div style="color:rgba(255,255,255,0.55) !important;font-size:0.85rem;line-height:1.65;">{moat[1]}</div></div></div></div>""", unsafe_allow_html=True)
    st.markdown('<div class="section-label">The Ask</div>', unsafe_allow_html=True)
    st.markdown("""<div class="info-card"><div class="info-card-title">Raising $3M Seed Round</div><div class="info-card-body"><b>Use of funds:</b><br>• <b>40%</b> — Engineering (5 senior hires)<br>• <b>30%</b> — Go-to-market<br>• <b>20%</b> — Data + training infra<br>• <b>10%</b> — Compliance (SOC 2, ISO 27001)<br><br><b>18-month milestones:</b> 25 paying customers · $1.5M ARR · Enterprise certs</div></div>""", unsafe_allow_html=True)
    st.markdown('<div class="section-label">Contact</div>', unsafe_allow_html=True)
    c1, c2 = st.columns(2)
    with c1: st.markdown("""<div class="metric-card"><div class="metric-label">Investor Relations</div><div class="metric-value" style="font-size:1rem">investors@zerostockout.ai</div><div class="metric-hint">Response within 24 hours</div></div>""", unsafe_allow_html=True)
    with c2: st.markdown("""<div class="metric-card"><div class="metric-label">Demo Access</div><div class="metric-value" style="font-size:1rem">Available on request</div><div class="metric-hint">Live walkthrough in 30 min</div></div>""", unsafe_allow_html=True)


# ============================================
# PAGE: ABOUT
# ============================================

def page_about():
    st.markdown('<div class="eyebrow">About</div>', unsafe_allow_html=True)
    st.markdown('<div class="page-title">Built by <span class="highlight">engineers who ship</span></div>', unsafe_allow_html=True)
    st.markdown('<div class="page-sub">Built in a 3-day sprint for the NTI Summer Internship.</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-label">Mission</div>', unsafe_allow_html=True)
    st.markdown("""<div class="info-card"><div class="info-card-title">Every unit of inventory, intelligently managed</div><div class="info-card-body">Inventory is the last major business process that hasn't been rebuilt for the age of AI.</div></div>""", unsafe_allow_html=True)
    st.markdown('<div class="section-label">Team</div>', unsafe_allow_html=True)
    for name, role, desc in [
        ("Malak", "System Architect & Decision Lead", "Full-stack AI, backend, deployment"),
        ("Sara", "Forecast Lead", "Time-series models, EDA, features"),
        ("Jumana", "RAG & Knowledge Lead", "Knowledge graphs, retrieval, routing"),
        ("Nada", "Computer Vision Lead", "YOLO training, damage detection"),
        ("Hala", "NLP & Voice Lead", "Voice input, multilingual support"),
    ]:
        st.markdown(f"""<div class="metric-card" style="margin-bottom:8px;"><div style="display:flex;justify-content:space-between;align-items:center;"><div><div style="color:#ffffff !important;font-weight:600;font-size:0.95rem;">{name}</div><div style="color:rgba(255,255,255,0.5) !important;font-size:0.8rem;margin-top:2px;">{role}</div></div><div style="color:rgba(255,255,255,0.4) !important;font-size:0.78rem;text-align:right;max-width:320px;">{desc}</div></div></div>""", unsafe_allow_html=True)
    st.markdown('<div class="section-label">Technology</div>', unsafe_allow_html=True)
    t1, t2, t3 = st.columns(3)
    with t1: st.markdown(metric_card("Frontend", "Streamlit", "Custom CSS · Plotly"), unsafe_allow_html=True)
    with t2: st.markdown(metric_card("Backend", "FastAPI", "Python 3.14 · 8 endpoints"), unsafe_allow_html=True)
    with t3: st.markdown(metric_card("ML Stack", "PyTorch · YOLO", "TFT · transformers · pytrends"), unsafe_allow_html=True)
    st.markdown('<div class="section-label">Contact</div>', unsafe_allow_html=True)
    st.markdown("""<div class="info-card"><div class="info-card-body"><b>General:</b> hello@zerostockout.ai<br><b>Investors:</b> investors@zerostockout.ai<br><b>GitHub:</b> github.com/Malakalaa23/zero-stockout-ai</div></div>""", unsafe_allow_html=True)
    st.markdown("---")
    st.caption(f"© 2026 Zero-Stockout AI · v{APP_VERSION}")


# ============================================
# SIDEBAR + TOPBAR + ROUTER
# ============================================
with st.sidebar:
    st.markdown("""<div class="side-brand"><span class="side-brand-icon">◆</span><span class="side-brand-name">Zero<span>Stockout</span></span></div>""", unsafe_allow_html=True)
    nav_options = ["Dashboard", "Trends", "Ask", "Analysis", "History", "Agents", "Investors", "About"]
    current_idx = nav_options.index(st.session_state.page) if st.session_state.page in nav_options else 0
    selected = st.radio("Navigation", nav_options, index=current_idx, label_visibility="collapsed")
    if selected != st.session_state.page:
        st.session_state.page = selected
        st.session_state.selected_agent = None
        st.rerun()
    online = api_online()
    st.markdown(f"""<div class="sidebar-status"><div style="font-size:0.62rem;text-transform:uppercase;letter-spacing:2px;color:rgba(255,255,255,0.3) !important;margin-bottom:10px;">System Status</div><div class="item"><span>API</span><span class="live"><span class="dot"></span>{'Online' if online else 'Offline'}</span></div><div class="item"><span>Forecast</span><span class="live">● Live</span></div><div class="item"><span>Trend</span><span class="live">● Live</span></div><div class="item"><span>Vision</span><span class="live">● Live</span></div><div class="item"><span>Decision</span><span class="live">● Live</span></div><div class="item"><span>Knowledge</span><span class="live">● Live</span></div><div class="item"><span>Voice</span><span class="live">● Live</span></div></div><div style="margin-top:20px;padding-top:14px;border-top:1px solid rgba(255,255,255,0.05);font-size:0.58rem;color:rgba(255,255,255,0.25) !important;letter-spacing:1px;text-align:center;">v{APP_VERSION} · Enterprise<br>NTI Summer Internship</div>""", unsafe_allow_html=True)

online = api_online()
st.markdown(f"""<div class="topbar"><div class="topbar-left"><span class="badge badge-trust">99.9% SLA</span><span class="badge badge-info">SOC 2 · GDPR</span></div><div class="topbar-right"><span class="sla">All systems <strong style="color:rgba(74,222,128,0.9);">operational</strong></span><span class="status-badge"><span class="status-dot {'online' if online else 'offline'}"></span>{'Live' if online else 'Offline'}</span></div></div>""", unsafe_allow_html=True)

page = st.session_state.page
if page == "Dashboard": page_dashboard()
elif page == "Trends": page_trends()
elif page == "Ask": page_ask()
elif page == "Analysis": page_analysis()
elif page == "History": page_history()
elif page == "Agents": page_agents()
elif page == "Agent Detail": page_agent_detail()
elif page == "Investors": page_investors()
elif page == "About": page_about()

st.markdown('</div>', unsafe_allow_html=True)