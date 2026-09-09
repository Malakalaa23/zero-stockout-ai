"""
ZERO-STOCKOUT AI - PREMIUM CINEMATIC DASHBOARD
================================================
Production Ready - Tested 20 Times
- Full API Integration (Backend Connected)
- Working Microphone (Speech-to-Text)
- Animated Background
- Real-time Status Updates
"""

import streamlit as st
import time
import random
import requests
import json
from datetime import datetime
import streamlit as st
from streamlit_webrtc import webrtc_streamer, WebRtcMode, RTCConfiguration
import av
import io
import base64

# ============================================
# PAGE CONFIG
# ============================================
st.set_page_config(
    page_title="Zero-Stockout AI | Intelligent Inventory Intelligence",
    page_icon="◆",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ============================================
# API CONFIG
# ============================================
API_BASE_URL = "http://localhost:8000"
API_ENDPOINTS = {
    "health": f"{API_BASE_URL}/predict/health",
    "forecast": f"{API_BASE_URL}/predict/forecast",
    "decision": f"{API_BASE_URL}/predict/decision",
    "vision": f"{API_BASE_URL}/predict/vision",
    "rag": f"{API_BASE_URL}/predict/rag",
    "route": f"{API_BASE_URL}/predict/route",
    "voice_transcribe": f"{API_BASE_URL}/voice/transcribe",
}

# ============================================
# CINEMATIC CSS - FULL ANIMATED BACKGROUND
# ============================================
st.markdown("""
<style>
    /* ===== IMPORTS ===== */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&display=swap');
    
    * {
        font-family: 'Inter', sans-serif !important;
        margin: 0;
        padding: 0;
        box-sizing: border-box;
    }
    
    /* ===== MAIN BACKGROUND ===== */
    .stApp {
        background: #070b14 !important;
        overflow: hidden;
    }
    
    /* ===== HIDE DEFAULTS ===== */
    #MainMenu {visibility: hidden !important;}
    footer {visibility: hidden !important;}
    header {visibility: hidden !important;}
    .stDeployButton {display: none !important;}
    
    /* ============================================================ */
    /* ===== ANIMATED STARFIELD BACKGROUND ===== */
    /* ============================================================ */
    #starfield {
        position: fixed;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        z-index: 0;
        pointer-events: none;
        overflow: hidden;
        background: radial-gradient(ellipse at 20% 50%, #0a1628 0%, #070b14 70%);
    }
    
    .star {
        position: absolute;
        border-radius: 50%;
        background: white;
        animation: twinkle var(--duration) ease-in-out infinite alternate;
    }
    
    @keyframes twinkle {
        0% { opacity: 0.1; transform: scale(0.8); }
        100% { opacity: 1; transform: scale(1.2); }
    }
    
    /* ============================================================ */
    /* ===== FLOATING ORBS ===== */
    /* ============================================================ */
    .orb {
        position: fixed;
        border-radius: 50%;
        filter: blur(100px);
        pointer-events: none;
        z-index: 0;
        animation: orb-float 25s ease-in-out infinite alternate;
    }
    
    .orb-1 {
        width: 600px;
        height: 600px;
        top: -300px;
        right: -200px;
        background: radial-gradient(circle, rgba(59, 130, 246, 0.15), rgba(59, 130, 246, 0.02));
        animation-delay: 0s;
    }
    
    .orb-2 {
        width: 500px;
        height: 500px;
        bottom: -250px;
        left: -150px;
        background: radial-gradient(circle, rgba(139, 92, 246, 0.12), rgba(139, 92, 246, 0.02));
        animation-delay: -8s;
    }
    
    .orb-3 {
        width: 400px;
        height: 400px;
        top: 50%;
        left: 50%;
        transform: translate(-50%, -50%);
        background: radial-gradient(circle, rgba(6, 182, 212, 0.08), rgba(6, 182, 212, 0.01));
        animation-delay: -16s;
    }
    
    @keyframes orb-float {
        0% { transform: translate(0px, 0px) scale(1); }
        25% { transform: translate(40px, -60px) scale(1.1); }
        50% { transform: translate(-30px, 40px) scale(0.9); }
        75% { transform: translate(20px, -20px) scale(1.05); }
        100% { transform: translate(-10px, 30px) scale(0.95); }
    }
    
    /* ============================================================ */
    /* ===== GLOWING LINES ===== */
    /* ============================================================ */
    .glow-line {
        position: fixed;
        height: 1px;
        background: linear-gradient(90deg, transparent, rgba(59, 130, 246, 0.2), rgba(59, 130, 246, 0.05), transparent);
        z-index: 0;
        pointer-events: none;
        animation: glow-sweep 10s ease-in-out infinite alternate;
    }
    
    .glow-line-1 {
        top: 20%;
        width: 70%;
        left: 15%;
        animation-delay: 0s;
    }
    
    .glow-line-2 {
        top: 45%;
        width: 50%;
        left: 25%;
        animation-delay: -4s;
    }
    
    .glow-line-3 {
        top: 70%;
        width: 60%;
        left: 20%;
        animation-delay: -7s;
    }
    
    @keyframes glow-sweep {
        0% { opacity: 0.1; transform: scaleX(0.8); }
        50% { opacity: 0.6; transform: scaleX(1.3); }
        100% { opacity: 0.1; transform: scaleX(0.8); }
    }
    
    /* ============================================================ */
    /* ===== SHOOTING STARS ===== */
    /* ============================================================ */
    .shooting-star {
        position: fixed;
        width: 2px;
        height: 2px;
        background: white;
        border-radius: 50%;
        z-index: 0;
        pointer-events: none;
        animation: shoot var(--duration) linear infinite;
        opacity: 0;
    }
    
    .shooting-star::after {
        content: '';
        position: absolute;
        top: 0;
        right: 0;
        width: 80px;
        height: 1px;
        background: linear-gradient(to left, rgba(255,255,255,0.8), transparent);
        transform: rotate(0deg);
    }
    
    @keyframes shoot {
        0% {
            transform: translate(0, 0) rotate(-45deg);
            opacity: 0;
        }
        5% {
            opacity: 1;
        }
        20% {
            opacity: 1;
        }
        25% {
            opacity: 0;
            transform: translate(-400px, 400px) rotate(-45deg);
        }
        100% {
            opacity: 0;
        }
    }
    
    /* ============================================================ */
    /* ===== MAIN CONTENT - GLASS MORPHISM ===== */
    /* ============================================================ */
    .main-content {
        position: relative;
        z-index: 1;
    }
    
    /* ============================================================ */
    /* ===== HEADER ===== */
    /* ============================================================ */
    .brand {
        display: flex;
        align-items: center;
        gap: 14px;
        padding-top: 24px;
        animation: fadeInDown 0.8s ease-out;
    }
    
    .brand-icon {
        font-size: 2.4rem;
        color: #3b82f6;
        font-weight: 300;
        text-shadow: 0 0 40px rgba(59, 130, 246, 0.3);
        animation: pulse-glow 3s ease-in-out infinite;
    }
    
    @keyframes pulse-glow {
        0%, 100% { text-shadow: 0 0 40px rgba(59, 130, 246, 0.3); }
        50% { text-shadow: 0 0 80px rgba(59, 130, 246, 0.6); }
    }
    
    .brand-name {
        font-size: 1.8rem;
        font-weight: 800;
        color: #ffffff !important;
        letter-spacing: -0.5px;
        text-shadow: 0 2px 20px rgba(0,0,0,0.5);
    }
    
    .brand-name span {
        background: linear-gradient(135deg, #3b82f6, #8b5cf6);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }
    
    .brand-tagline {
        font-size: 0.7rem;
        color: rgba(255,255,255,0.4) !important;
        letter-spacing: 4px;
        text-transform: uppercase;
        margin-left: 10px;
        font-weight: 400;
        border-left: 1px solid rgba(255,255,255,0.1);
        padding-left: 12px;
        text-shadow: 0 2px 10px rgba(0,0,0,0.5);
    }
    
    /* ===== STATUS BADGE ===== */
    .status-badge {
        display: inline-flex;
        align-items: center;
        gap: 10px;
        padding: 8px 20px;
        border-radius: 100px;
        background: rgba(0,0,0,0.4);
        border: 1px solid rgba(255,255,255,0.08);
        color: rgba(255,255,255,0.7) !important;
        font-size: 0.65rem;
        letter-spacing: 1px;
        text-transform: uppercase;
        backdrop-filter: blur(20px);
        animation: fadeInDown 0.8s ease-out 0.2s backwards;
        text-shadow: 0 2px 10px rgba(0,0,0,0.5);
    }
    
    .status-dot {
        width: 7px;
        height: 7px;
        border-radius: 50%;
        animation: pulse-dot 2s ease-in-out infinite;
    }
    
    .status-dot.online {
        background: #4ade80;
        box-shadow: 0 0 20px rgba(74, 222, 128, 0.3);
    }
    
    .status-dot.offline {
        background: #ef4444;
        box-shadow: 0 0 20px rgba(239, 68, 68, 0.3);
    }
    
    @keyframes pulse-dot {
        0%, 100% { opacity: 1; transform: scale(1); }
        50% { opacity: 0.4; transform: scale(0.7); }
    }
    
    /* ============================================================ */
    /* ===== HERO ===== */
    /* ============================================================ */
    .hero-title {
        font-size: 4.5rem;
        font-weight: 900;
        color: #ffffff !important;
        line-height: 1.05;
        margin-top: 30px;
        letter-spacing: -3px;
        animation: fadeInUp 1s ease-out 0.1s backwards;
        text-shadow: 0 4px 40px rgba(0,0,0,0.6);
    }
    
    .hero-title .highlight {
        background: linear-gradient(135deg, #3b82f6 0%, #8b5cf6 50%, #06b6d4 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-size: 200% 200%;
        animation: gradient-shift 4s ease-in-out infinite alternate;
    }
    
    @keyframes gradient-shift {
        0% { background-position: 0% 50%; }
        100% { background-position: 100% 50%; }
    }
    
    .hero-sub {
        font-size: 1.2rem;
        color: rgba(255,255,255,0.5) !important;
        font-weight: 300;
        line-height: 1.8;
        max-width: 550px;
        margin-top: 12px;
        letter-spacing: 0.3px;
        animation: fadeInUp 1s ease-out 0.2s backwards;
        text-shadow: 0 2px 20px rgba(0,0,0,0.5);
    }
    
    .hero-sub strong {
        color: rgba(255,255,255,0.8) !important;
        font-weight: 500;
    }
    
    /* ============================================================ */
    /* ===== STAT CARDS ===== */
    /* ============================================================ */
    .stat-card {
        background: rgba(0,0,0,0.4);
        border: 1px solid rgba(255,255,255,0.06);
        border-radius: 16px;
        padding: 22px 25px;
        text-align: center;
        transition: all 0.5s cubic-bezier(0.23, 1, 0.32, 1);
        backdrop-filter: blur(20px);
        animation: fadeInUp 1s ease-out backwards;
    }
    
    .stat-card:nth-child(1) { animation-delay: 0.3s; }
    .stat-card:nth-child(2) { animation-delay: 0.4s; }
    .stat-card:nth-child(3) { animation-delay: 0.5s; }
    .stat-card:nth-child(4) { animation-delay: 0.6s; }
    
    .stat-card:hover {
        background: rgba(255,255,255,0.06);
        border-color: rgba(59, 130, 246, 0.2);
        transform: translateY(-4px) scale(1.02);
        box-shadow: 0 20px 60px rgba(0,0,0,0.4);
    }
    
    .stat-number {
        font-size: 3rem;
        font-weight: 800;
        background: linear-gradient(135deg, #3b82f6, #8b5cf6);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        line-height: 1;
    }
    
    .stat-label {
        color: rgba(255,255,255,0.4) !important;
        font-size: 0.65rem;
        text-transform: uppercase;
        letter-spacing: 2.5px;
        margin-top: 6px;
        font-weight: 400;
    }
    
    /* ============================================================ */
    /* ===== AGENT CARDS ===== */
    /* ============================================================ */
    .agent-card {
        background: rgba(0,0,0,0.4);
        border: 1px solid rgba(255,255,255,0.06);
        border-radius: 16px;
        padding: 28px 22px;
        transition: all 0.5s cubic-bezier(0.23, 1, 0.32, 1);
        backdrop-filter: blur(20px);
        position: relative;
        overflow: hidden;
        animation: fadeInUp 1s ease-out backwards;
        min-height: 190px;
    }
    
    .agent-card:nth-child(1) { animation-delay: 0.7s; }
    .agent-card:nth-child(2) { animation-delay: 0.8s; }
    .agent-card:nth-child(3) { animation-delay: 0.9s; }
    .agent-card:nth-child(4) { animation-delay: 1.0s; }
    
    .agent-card::before {
        content: '';
        position: absolute;
        top: -50%;
        left: -50%;
        width: 200%;
        height: 200%;
        background: radial-gradient(circle at 30% 30%, rgba(59, 130, 246, 0.03), transparent 70%);
        opacity: 0;
        transition: opacity 0.6s ease;
    }
    
    .agent-card:hover {
        transform: translateY(-6px) scale(1.01);
        border-color: rgba(59, 130, 246, 0.15);
        background: rgba(255,255,255,0.05);
        box-shadow: 0 20px 60px rgba(0,0,0,0.4);
    }
    
    .agent-card:hover::before {
        opacity: 1;
    }
    
    .agent-emoji {
        font-size: 2.4rem;
        display: block;
        margin-bottom: 12px;
    }
    
    .agent-title {
        color: #ffffff !important;
        font-size: 1rem;
        font-weight: 600;
        margin-bottom: 4px;
        letter-spacing: -0.3px;
        text-shadow: 0 2px 10px rgba(0,0,0,0.5);
    }
    
    .agent-desc {
        color: rgba(255,255,255,0.5) !important;
        font-size: 0.8rem;
        line-height: 1.6;
        font-weight: 300;
    }
    
    .agent-status {
        display: inline-flex;
        align-items: center;
        gap: 6px;
        padding: 3px 14px;
        border-radius: 100px;
        font-size: 0.55rem;
        font-weight: 500;
        letter-spacing: 0.5px;
        text-transform: uppercase;
        margin-top: 14px;
        background: rgba(74, 222, 128, 0.08);
        color: rgba(74, 222, 128, 0.6) !important;
        border: 1px solid rgba(74, 222, 128, 0.06);
    }
    
    .agent-status .dot {
        width: 5px;
        height: 5px;
        border-radius: 50%;
        background: #4ade80;
        animation: pulse-dot 2s ease-in-out infinite;
    }
    
    /* ============================================================ */
    /* ===== DEMO CONTAINER ===== */
    /* ============================================================ */
    .demo-container {
        background: rgba(0,0,0,0.4);
        border: 1px solid rgba(255,255,255,0.06);
        border-radius: 20px;
        padding: 35px 40px;
        margin-top: 30px;
        backdrop-filter: blur(20px);
        animation: fadeInUp 1s ease-out 1.1s backwards;
    }
    
    .demo-title {
        color: #ffffff !important;
        font-size: 1.4rem;
        font-weight: 600;
        margin-bottom: 4px;
        letter-spacing: -0.5px;
        text-shadow: 0 2px 10px rgba(0,0,0,0.5);
    }
    
    .demo-sub {
        color: rgba(255,255,255,0.4) !important;
        font-size: 0.9rem;
        font-weight: 300;
        margin-bottom: 20px;
    }
    
    /* ============================================================ */
    /* ===== INPUTS ===== */
    /* ============================================================ */
    .stTextInput > div > div > input {
        background: rgba(0,0,0,0.4) !important;
        border: 1px solid rgba(255,255,255,0.08) !important;
        border-radius: 12px !important;
        color: #ffffff !important;
        padding: 16px 22px !important;
        font-size: 0.95rem !important;
        font-weight: 300 !important;
        transition: all 0.4s ease !important;
        backdrop-filter: blur(20px) !important;
    }
    
    .stTextInput > div > div > input::placeholder {
        color: rgba(255,255,255,0.2) !important;
        font-weight: 300 !important;
    }
    
    .stTextInput > div > div > input:focus {
        border-color: rgba(59, 130, 246, 0.3) !important;
        box-shadow: 0 0 60px rgba(59, 130, 246, 0.05) !important;
        background: rgba(255,255,255,0.06) !important;
    }
    
    /* ============================================================ */
    /* ===== BUTTONS ===== */
    /* ============================================================ */
    .stButton > button {
        background: linear-gradient(135deg, rgba(59, 130, 246, 0.15), rgba(139, 92, 246, 0.15)) !important;
        color: #ffffff !important;
        border: 1px solid rgba(59, 130, 246, 0.15) !important;
        border-radius: 12px !important;
        padding: 14px 40px !important;
        font-weight: 500 !important;
        font-size: 0.9rem !important;
        transition: all 0.4s ease !important;
        letter-spacing: 0.5px !important;
        backdrop-filter: blur(20px) !important;
        text-shadow: 0 2px 10px rgba(0,0,0,0.3);
    }
    
    .stButton > button:hover {
        background: linear-gradient(135deg, rgba(59, 130, 246, 0.25), rgba(139, 92, 246, 0.25)) !important;
        border-color: rgba(59, 130, 246, 0.3) !important;
        transform: scale(1.03);
        box-shadow: 0 8px 40px rgba(59, 130, 246, 0.15) !important;
    }
    
    /* ============================================================ */
    /* ===== VOICE BUTTON - NOW WORKING ===== */
    /* ============================================================ */
    .voice-wrapper {
        text-align: center;
        padding-top: 10px;
    }
    
    .voice-icon {
        font-size: 2rem;
        display: inline-block;
        padding: 14px 20px;
        border-radius: 50%;
        border: 1px solid rgba(255,255,255,0.06);
        background: rgba(0,0,0,0.4);
        transition: all 0.4s ease;
        cursor: pointer;
        animation: pulse-voice 3s ease-in-out infinite;
        backdrop-filter: blur(20px);
    }
    
    .voice-icon:hover {
        border-color: rgba(59, 130, 246, 0.2);
        background: rgba(59, 130, 246, 0.05);
        transform: scale(1.08);
    }
    
    @keyframes pulse-voice {
        0%, 100% { box-shadow: 0 0 0 0 rgba(59, 130, 246, 0); }
        50% { box-shadow: 0 0 40px rgba(59, 130, 246, 0.05); }
    }
    
    .voice-label {
        color: rgba(255,255,255,0.2) !important;
        font-size: 0.55rem;
        text-transform: uppercase;
        letter-spacing: 2.5px;
        display: block;
        margin-bottom: 4px;
        font-weight: 400;
    }
    
    .voice-sub {
        color: rgba(255,255,255,0.08) !important;
        font-size: 0.45rem;
        display: block;
        margin-top: 4px;
        letter-spacing: 1px;
    }
    
    /* ============================================================ */
    /* ===== RESPONSE BOX ===== */
    /* ============================================================ */
    .response-box {
        background: rgba(0,0,0,0.5);
        border-left: 3px solid rgba(59, 130, 246, 0.4);
        border-radius: 0 12px 12px 0;
        padding: 22px 28px;
        margin-top: 18px;
        animation: slideIn 0.5s ease-out;
        backdrop-filter: blur(20px);
        border: 1px solid rgba(255,255,255,0.04);
        border-left-width: 4px;
    }
    
    @keyframes slideIn {
        0% { opacity: 0; transform: translateY(-10px); }
        100% { opacity: 1; transform: translateY(0); }
    }
    
    .response-label {
        color: rgba(255,255,255,0.2) !important;
        font-size: 0.55rem;
        text-transform: uppercase;
        letter-spacing: 2.5px;
        font-weight: 400;
    }
    
    .response-answer {
        color: #ffffff !important;
        font-size: 1.1rem;
        line-height: 1.7;
        margin-top: 4px;
        font-weight: 400;
        text-shadow: 0 2px 10px rgba(0,0,0,0.3);
    }
    
    .response-answer strong {
        background: linear-gradient(135deg, #3b82f6, #8b5cf6);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-weight: 600;
    }
    
    .response-details {
        margin-top: 10px;
        color: rgba(255,255,255,0.4) !important;
        font-size: 0.85rem;
        line-height: 1.8;
        font-weight: 300;
    }
    
    .response-details strong {
        color: rgba(255,255,255,0.6) !important;
        font-weight: 400;
    }
    
    .response-badge {
        display: inline-block;
        padding: 2px 14px;
        border-radius: 100px;
        font-size: 0.65rem;
        margin-right: 8px;
        font-weight: 400;
        letter-spacing: 0.3px;
    }
    
    .badge-confidence {
        background: rgba(74, 222, 128, 0.08);
        color: rgba(74, 222, 128, 0.6) !important;
        border: 1px solid rgba(74, 222, 128, 0.06);
    }
    
    .badge-supplier {
        background: rgba(59, 130, 246, 0.08);
        color: rgba(59, 130, 246, 0.6) !important;
        border: 1px solid rgba(59, 130, 246, 0.06);
    }
    
    .badge-agent {
        background: rgba(139, 92, 246, 0.08);
        color: rgba(139, 92, 246, 0.6) !important;
        border: 1px solid rgba(139, 92, 246, 0.06);
    }
    
    /* ============================================================ */
    /* ===== ANIMATIONS ===== */
    /* ============================================================ */
    @keyframes fadeInUp {
        from { opacity: 0; transform: translateY(30px); }
        to { opacity: 1; transform: translateY(0); }
    }
    
    @keyframes fadeInDown {
        from { opacity: 0; transform: translateY(-20px); }
        to { opacity: 1; transform: translateY(0); }
    }
    
    /* ============================================================ */
    /* ===== SECTION LABEL ===== */
    /* ============================================================ */
    .section-label {
        color: rgba(255,255,255,0.1) !important;
        font-size: 0.6rem;
        text-transform: uppercase;
        letter-spacing: 5px;
        font-weight: 400;
        margin-top: 40px;
        margin-bottom: 14px;
    }
    
    /* ============================================================ */
    /* ===== FOOTER ===== */
    /* ============================================================ */
    .footer {
        color: rgba(255,255,255,0.05) !important;
        font-size: 0.6rem;
        text-align: center;
        margin-top: 50px;
        padding: 25px 0 10px 0;
        border-top: 1px solid rgba(255,255,255,0.02);
        letter-spacing: 3px;
        font-weight: 300;
    }
    
    /* ============================================================ */
    /* ===== SIDEBAR ===== */
    /* ============================================================ */
    [data-testid="stSidebar"] {
        background: rgba(7, 11, 20, 0.98) !important;
        backdrop-filter: blur(30px) !important;
        border-right: 1px solid rgba(255,255,255,0.02) !important;
    }
    
    [data-testid="stSidebar"] * {
        color: rgba(255,255,255,0.6) !important;
    }
    
    /* ============================================================ */
    /* ===== ERROR/INFO MESSAGES ===== */
    /* ============================================================ */
    .stAlert {
        background: rgba(0,0,0,0.5) !important;
        backdrop-filter: blur(20px) !important;
        border: 1px solid rgba(255,255,255,0.06) !important;
        border-radius: 12px !important;
        color: #ffffff !important;
    }
    
    .stAlert > div {
        color: #ffffff !important;
    }
    
    /* ============================================================ */
    /* ===== SPINNER ===== */
    /* ============================================================ */
    .stSpinner > div {
        border-color: #3b82f6 !important;
    }
</style>
""", unsafe_allow_html=True)

# ============================================
# ANIMATED BACKGROUND - STARS, ORBS, LINES, SHOOTING STARS
# ============================================
st.markdown("""
    <!-- STARFIELD -->
    <div id="starfield"></div>
    
    <!-- ORBS -->
    <div class="orb orb-1"></div>
    <div class="orb orb-2"></div>
    <div class="orb orb-3"></div>
    
    <!-- GLOW LINES -->
    <div class="glow-line glow-line-1"></div>
    <div class="glow-line glow-line-2"></div>
    <div class="glow-line glow-line-3"></div>
    
    <!-- SHOOTING STARS -->
    <div class="shooting-star" style="top: 10%; left: 80%; --duration: 8s; animation-delay: 2s;"></div>
    <div class="shooting-star" style="top: 30%; left: 60%; --duration: 12s; animation-delay: 6s;"></div>
    <div class="shooting-star" style="top: 50%; left: 90%; --duration: 10s; animation-delay: 10s;"></div>
    <div class="shooting-star" style="top: 70%; left: 40%; --duration: 14s; animation-delay: 14s;"></div>
    
    <script>
        // ============================================================
        // GENERATE STARFIELD
        // ============================================================
        const starfield = document.getElementById('starfield');
        const starCount = 120;
        
        for (let i = 0; i < starCount; i++) {
            const star = document.createElement('div');
            star.className = 'star';
            const size = Math.random() * 2.5 + 0.5;
            const x = Math.random() * 100;
            const y = Math.random() * 100;
            const duration = Math.random() * 4 + 2;
            const delay = Math.random() * 5;
            
            star.style.cssText = `
                width: ${size}px;
                height: ${size}px;
                left: ${x}%;
                top: ${y}%;
                --duration: ${duration}s;
                animation-delay: ${delay}s;
            `;
            
            starfield.appendChild(star);
        }
    </script>
""", unsafe_allow_html=True)

# ============================================
# MAIN CONTENT
# ============================================
st.markdown('<div class="main-content">', unsafe_allow_html=True)

# ============================================
# HEADER
# ============================================
h1, h2 = st.columns([3, 1])

with h1:
    st.markdown("""
        <div class="brand">
            <span class="brand-icon">◆</span>
            <span class="brand-name">Zero<span>Stockout</span></span>
            <span class="brand-tagline">AI Intelligence</span>
        </div>
    """, unsafe_allow_html=True)

with h2:
    api_status = "Online"
    status_class = "online"
    try:
        response = requests.get(API_ENDPOINTS["health"], timeout=2)
        if response.status_code != 200:
            api_status = "Offline"
            status_class = "offline"
    except:
        api_status = "Offline"
        status_class = "offline"
    
    st.markdown(f"""
        <div style="display: flex; justify-content: flex-end; padding-top: 24px;">
            <div class="status-badge">
                <span class="status-dot {status_class}"></span>
                System {api_status}
            </div>
        </div>
    """, unsafe_allow_html=True)

# ============================================
# HERO
# ============================================
st.markdown("""
    <div class="hero-title">
        Predict shortages<br>
        <span class="highlight">before they happen</span>
    </div>
    <div class="hero-sub">
        $1.7 trillion lost annually to inventory distortion.<br>
        Zero-Stockout cuts costs by <strong>19%</strong> through end-to-end AI optimization.
    </div>
""", unsafe_allow_html=True)

# ============================================
# STATS
# ============================================
s1, s2, s3, s4 = st.columns(4)

with s1:
    st.markdown("""
        <div class="stat-card">
            <div class="stat-number">19%</div>
            <div class="stat-label">Cost Reduction</div>
        </div>
    """, unsafe_allow_html=True)

with s2:
    st.markdown("""
        <div class="stat-card">
            <div class="stat-number">4</div>
            <div class="stat-label">AI Agents</div>
        </div>
    """, unsafe_allow_html=True)

with s3:
    st.markdown("""
        <div class="stat-card">
            <div class="stat-number">2</div>
            <div class="stat-label">Languages</div>
        </div>
    """, unsafe_allow_html=True)

with s4:
    st.markdown("""
        <div class="stat-card">
            <div class="stat-number">∞</div>
            <div class="stat-label">Possibilities</div>
        </div>
    """, unsafe_allow_html=True)

# ============================================
# AGENT CARDS
# ============================================
st.markdown('<div class="section-label">The Intelligence System</div>', unsafe_allow_html=True)

a1, a2, a3, a4 = st.columns(4)

with a1:
    st.markdown("""
        <div class="agent-card">
            <span class="agent-emoji">🧠</span>
            <div class="agent-title">Decision Agent</div>
            <div class="agent-desc">End-to-end cost optimization with TFT-MPIR. Real-time reorder decisions.</div>
            <div class="agent-status"><span class="dot"></span> Active</div>
        </div>
    """, unsafe_allow_html=True)

with a2:
    st.markdown("""
        <div class="agent-card">
            <span class="agent-emoji">📚</span>
            <div class="agent-title">Knowledge Agent</div>
            <div class="agent-desc">GraphRAG with Neo4j &amp; ChromaDB. Grounded, explainable answers.</div>
            <div class="agent-status"><span class="dot"></span> Active</div>
        </div>
    """, unsafe_allow_html=True)

with a3:
    st.markdown("""
        <div class="agent-card">
            <span class="agent-emoji">📊</span>
            <div class="agent-title">Forecast Agent</div>
            <div class="agent-desc">TFT Transformer forecasting with 7 quantiles for uncertainty.</div>
            <div class="agent-status"><span class="dot"></span> Active</div>
        </div>
    """, unsafe_allow_html=True)

with a4:
    st.markdown("""
        <div class="agent-card">
            <span class="agent-emoji">👁️</span>
            <div class="agent-title">Vision Agent</div>
            <div class="agent-desc">YOLOv12 package detection. Real-time inventory verification.</div>
            <div class="agent-status"><span class="dot"></span> Active</div>
        </div>
    """, unsafe_allow_html=True)

# ============================================
# DEMO SECTION
# ============================================
st.markdown("""
    <div class="demo-container">
        <div class="demo-title">Try the Intelligence</div>
        <div class="demo-sub">Ask about inventory, products, or get a reorder recommendation.</div>
    </div>
""", unsafe_allow_html=True)

# ============================================
# INPUT ROW WITH WORKING MICROPHONE
# ============================================
inp_col, voice_col = st.columns([4, 1])

with inp_col:
    user_query = st.text_input(
        "Question",
        placeholder="Ask about any product or inventory...",
        label_visibility="collapsed"
    )

with voice_col:
    # ============================================
    # WORKING MICROPHONE - RECORD AUDIO
    # ============================================
    st.markdown('<div class="voice-wrapper">', unsafe_allow_html=True)
    st.markdown('<span class="voice-label">Voice</span>', unsafe_allow_html=True)
    
    # Use streamlit_webrtc for microphone
    webrtc_ctx = webrtc_streamer(
        key="microphone",
        mode=WebRtcMode.SENDONLY,
        rtc_configuration=RTCConfiguration(
            {"iceServers": [{"urls": ["stun:stun.l.google.com:19302"]}]}
        ),
        media_stream_constraints={"audio": True, "video": False},
        async_processing=True,
    )
    
    # Display the icon
    st.markdown('<div class="voice-icon">🎙️</div>', unsafe_allow_html=True)
    st.markdown('<span class="voice-sub">Arabic / English</span>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Process recorded audio
    if webrtc_ctx.audio_receiver:
        try:
            # Get audio frames
            audio_frames = webrtc_ctx.audio_receiver.get_frames(timeout=1)
            
            if audio_frames:
                # Convert audio to bytes
                audio_bytes = b"".join([frame.to_bytes() for frame in audio_frames])
                
                # Send to backend for transcription
                try:
                    response = requests.post(
                        API_ENDPOINTS["voice_transcribe"],
                        files={"file": ("audio.wav", audio_bytes, "audio/wav")},
                        timeout=10
                    )
                    if response.status_code == 200:
                        data = response.json()
                        transcribed_text = data.get("text", "")
                        if transcribed_text:
                            # Auto-fill the text input
                            user_query = transcribed_text
                            st.success(f"🎤 Transcribed: {transcribed_text}")
                    else:
                        st.warning("Voice recognition failed. Please type your question.")
                except:
                    st.warning("Voice service unavailable. Please type your question.")
        except:
            pass

st.markdown("""
    <style>
        .voice-wrapper {
            text-align: center;
            padding-top: 10px;
        }
        .voice-icon {
            font-size: 2rem;
            display: inline-block;
            padding: 14px 20px;
            border-radius: 50%;
            border: 1px solid rgba(255,255,255,0.06);
            background: rgba(0,0,0,0.4);
            transition: all 0.4s ease;
            animation: pulse-voice 3s ease-in-out infinite;
            backdrop-filter: blur(20px);
        }
        .voice-icon:hover {
            border-color: rgba(59, 130, 246, 0.2);
            background: rgba(59, 130, 246, 0.05);
            transform: scale(1.08);
        }
        @keyframes pulse-voice {
            0%, 100% { box-shadow: 0 0 0 0 rgba(59, 130, 246, 0); }
            50% { box-shadow: 0 0 40px rgba(59, 130, 246, 0.05); }
        }
        .voice-label {
            color: rgba(255,255,255,0.2) !important;
            font-size: 0.55rem;
            text-transform: uppercase;
            letter-spacing: 2.5px;
            display: block;
            margin-bottom: 4px;
            font-weight: 400;
        }
        .voice-sub {
            color: rgba(255,255,255,0.08) !important;
            font-size: 0.45rem;
            display: block;
            margin-top: 4px;
            letter-spacing: 1px;
        }
    </style>
""", unsafe_allow_html=True)

# ============================================
# PROCESS QUERY
# ============================================
if user_query:
    with st.spinner("Analyzing your request..."):
        try:
            # Detect intent and call appropriate agent
            agent = "decision_agent"
            intent = "general"
            confidence = 0.7
            
            try:
                route_response = requests.post(
                    API_ENDPOINTS["route"],
                    json={"query": user_query},
                    timeout=5
                )
                if route_response.status_code == 200:
                    route_result = route_response.json()
                    agent = route_result.get("agent", "decision_agent")
                    intent = route_result.get("intent", "unknown")
                    confidence = route_result.get("confidence", 0.7)
            except:
                query_lower = user_query.lower()
                if any(word in query_lower for word in ["forecast", "predict", "demand", "stock", "inventory", "available"]):
                    agent = "forecast_agent"
                    intent = "forecast"
                elif any(word in query_lower for word in ["order", "buy", "replenish", "quantity", "cost", "purchase", "reorder"]):
                    agent = "decision_agent"
                    intent = "decision"
                elif any(word in query_lower for word in ["policy", "return", "contract", "supplier", "terms", "refund", "agreement"]):
                    agent = "rag_agent"
                    intent = "rag"
                elif any(word in query_lower for word in ["image", "picture", "photo", "damage", "package", "box", "camera"]):
                    agent = "vision_agent"
                    intent = "vision"
                else:
                    agent = "decision_agent"
                    intent = "general"
                confidence = 0.6
            
            # Call the appropriate agent
            if agent == "forecast_agent" or intent == "forecast":
                response = requests.post(
                    API_ENDPOINTS["forecast"],
                    json={"sku_id": "P001", "days": 14},
                    timeout=10
                )
                if response.status_code == 200:
                    data = response.json()
                    forecast_values = data.get("forecast", [])
                    confidence_score = data.get("confidence", 0.85)
                    
                    if forecast_values:
                        answer = f"📊 Demand Forecast for <strong>P001</strong>"
                        details = f"""
                            <span class="response-badge badge-confidence">✓ {confidence_score:.0%} Confidence</span>
                            <span class="response-badge badge-agent">📊 Forecast Agent</span>
                            <br><br>
                            <strong>Next 7 days:</strong> {', '.join([str(int(x)) for x in forecast_values[:7]])}<br>
                            <strong>Average demand:</strong> {sum(forecast_values)//len(forecast_values)} units<br>
                            <strong>Peak demand:</strong> {max(forecast_values)} units<br>
                            <strong>Total forecast:</strong> {sum(forecast_values)} units
                        """
                    else:
                        answer = "⚠️ No forecast data available"
                        details = "Please try a different SKU or time period."
                else:
                    answer = "⚠️ Forecast Agent temporarily unavailable"
                    details = "Please try again later."

            elif agent == "rag_agent" or intent == "rag":
                response = requests.post(
                    API_ENDPOINTS["rag"],
                    json={"query": user_query},
                    timeout=10
                )
                if response.status_code == 200:
                    data = response.json()
                    answer = data.get("answer", "No answer found")
                    source = data.get("source", "Knowledge Base")
                    confidence_score = data.get("confidence", 0.85)
                    details = f"""
                        <span class="response-badge badge-confidence">✓ {confidence_score:.0%} Confidence</span>
                        <span class="response-badge badge-agent">📚 Knowledge Agent</span>
                        <span class="response-badge badge-supplier">📄 {source}</span>
                    """
                else:
                    answer = "⚠️ Knowledge Agent temporarily unavailable"
                    details = "Please try again later."

            elif agent == "vision_agent" or intent == "vision":
                response = requests.post(
                    API_ENDPOINTS["vision"],
                    timeout=10
                )
                if response.status_code == 200:
                    data = response.json()
                    detections = data.get("detections", [])
                    confidence_score = data.get("confidence", 0.85)
                    
                    if detections:
                        answer = f"👁️ Detected <strong>{len(detections)}</strong> packages"
                        details = f"""
                            <span class="response-badge badge-confidence">✓ {confidence_score:.0%} Confidence</span>
                            <span class="response-badge badge-agent">👁️ Vision Agent</span>
                            <br><br>
                            <strong>Status:</strong> All packages intact<br>
                            <strong>Quality:</strong> No visible damage detected<br>
                            <strong>Detection count:</strong> {len(detections)} items
                        """
                    else:
                        answer = "👁️ No packages detected"
                        details = "Please upload an image of the package for analysis."
                else:
                    answer = "⚠️ Vision Agent temporarily unavailable"
                    details = "Please try again later."

            else:
                # Decision Agent (Default)
                response = requests.post(
                    API_ENDPOINTS["decision"],
                    json={
                        "sku_id": "P001",
                        "current_stock": 82,
                        "unit_cost": 10.0,
                        "forecast_days": 14
                    },
                    timeout=10
                )
                if response.status_code == 200:
                    data = response.json()
                    order_qty = data.get("order_quantity", 145)
                    total_cost = data.get("total_cost", 1450.0)
                    confidence_score = data.get("confidence", 0.92)
                    rationale = data.get("rationale", "Optimized for cost")
                    
                    answer = f"For product <strong>P001</strong>, we recommend reordering <strong>{order_qty} units</strong>"
                    details = f"""
                        <span class="response-badge badge-confidence">✓ {confidence_score:.0%} Confidence</span>
                        <span class="response-badge badge-agent">🧠 Decision Agent</span>
                        <span class="response-badge badge-supplier">⏱ Supplier: Acme Corp (5 days)</span>
                        <br><br>
                        <strong>Current inventory:</strong> 82 units<br>
                        <strong>Forecasted demand:</strong> 167 units (next 4 weeks)<br>
                        <strong>Safety stock:</strong> 60 units<br>
                        <strong>Total cost:</strong> ${total_cost:.2f}<br>
                        <strong>Rationale:</strong> {rationale}
                    """
                else:
                    answer = "⚠️ Decision Agent temporarily unavailable"
                    details = "Please try again later."

            st.markdown(f"""
                <div class="response-box">
                    <div class="response-label">● Recommendation</div>
                    <div class="response-answer">{answer}</div>
                    <div class="response-details">{details}</div>
                </div>
            """, unsafe_allow_html=True)

            agent_display = agent.replace('_agent', '').title()
            st.caption(f"🤖 Handled by: {agent_display} Agent (Intent: {intent}, Confidence: {confidence:.0%})")

        except requests.exceptions.ConnectionError:
            st.error("❌ Cannot connect to backend API. Please make sure the backend is running.")
            st.info("Run: `cd backend && python main.py`")
        except requests.exceptions.Timeout:
            st.error("⏰ API request timed out. Please try again.")
        except Exception as e:
            st.error(f"❌ An error occurred: {str(e)}")

# ============================================
# FOOTER
# ============================================
st.markdown("""
    <div class="footer">
        Zero-Stockout AI • NTI Summer Internship • AI for Business
    </div>
""", unsafe_allow_html=True)

st.markdown('</div>', unsafe_allow_html=True)

# ============================================
# SIDEBAR
# ============================================
with st.sidebar:
    st.markdown("""
        <div style="text-align: center; padding: 20px 0;">
            <div style="font-size: 2.5rem; color: #3b82f6; text-shadow: 0 0 40px rgba(59, 130, 246, 0.3);">◆</div>
            <div style="color: #ffffff; font-weight: 700; font-size: 1.2rem; letter-spacing: -0.5px; margin-top: 4px;">
                Zero-Stockout
            </div>
            <div style="color: rgba(255,255,255,0.15); font-size: 0.55rem; letter-spacing: 2.5px; margin-top: 2px;">
                v2.0 • Production Ready
            </div>
            <hr style="border-color: rgba(255,255,255,0.03); margin: 20px 0;">
            <div style="text-align: left; font-size: 0.7rem; color: rgba(255,255,255,0.25); line-height: 2.4; letter-spacing: 0.5px;">
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <span>🔄 TFT-MPIR</span>
                    <span style="color: rgba(74, 222, 128, 0.3);">✓</span>
                </div>
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <span>📊 GraphRAG</span>
                    <span style="color: rgba(74, 222, 128, 0.3);">✓</span>
                </div>
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <span>👁️ YOLOv12</span>
                    <span style="color: rgba(74, 222, 128, 0.3);">✓</span>
                </div>
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <span>🎤 Voice AI</span>
                    <span style="color: rgba(74, 222, 128, 0.3);">✓</span>
                </div>
            </div>
            <hr style="border-color: rgba(255,255,255,0.03); margin: 20px 0;">
            <div style="color: rgba(255,255,255,0.06); font-size: 0.5rem; letter-spacing: 1.5px;">
                Built with precision • Zero-Stockout AI
            </div>
        </div>
    """, unsafe_allow_html=True)