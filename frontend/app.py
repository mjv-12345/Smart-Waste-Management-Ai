"""
app.py — Smart Waste AI Frontend (Streamlit)
3 tabs: Water Demand · Waste Generation · Route Optimization
Enhanced UI v2 — dark green brutalist-industrial aesthetic
"""

import streamlit as st
import requests
import pandas as pd
import numpy as np
import math
from datetime import date

# ─── PAGE CONFIG ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="EcoMind — Smart Waste AI",
    page_icon="♻",
    layout="wide",
    initial_sidebar_state="expanded"
)

https://smart-waste-backend-vtop.onrender.com

# ─── GLOBAL CSS ────────────────────────────────────────────────────────────────
st.markdown("""
<style>
  @import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@300;400;500;600;700&family=JetBrains+Mono:wght@300;400;500;700&display=swap');

  /* ─ Base reset */
  html, body, [class*="css"] {
    font-family: 'JetBrains Mono', monospace !important;
    background: #060e08 !important;
    color: #c8f0c8 !important;
  }
  .stApp { background: #060e08 !important; }
  .block-container { padding: 2rem 2.5rem 3rem !important; max-width: 1400px !important; }

  /* ─ Sidebar */
  [data-testid="stSidebar"] {
    background: #0a1a0e !important;
    border-right: 1px solid #1a3a20 !important;
  }
  [data-testid="stSidebar"] > div { padding: 1.5rem 1rem !important; }

  /* ─ Tabs */
  .stTabs [data-baseweb="tab-list"] {
    background: transparent !important;
    border-bottom: 1px solid #1a3a20 !important;
    gap: 0 !important;
  }
  .stTabs [data-baseweb="tab"] {
    font-family: 'Space Grotesk', sans-serif !important;
    font-weight: 600 !important;
    font-size: 0.82rem !important;
    letter-spacing: 0.08em !important;
    text-transform: uppercase !important;
    color: rgba(200,240,200,0.35) !important;
    padding: 0.75rem 1.5rem !important;
    border: none !important;
    background: transparent !important;
    border-radius: 0 !important;
    transition: all 0.2s !important;
  }
  .stTabs [aria-selected="true"] {
    color: #6eff6e !important;
    background: rgba(110,255,110,0.06) !important;
    border-bottom: 2px solid #6eff6e !important;
  }
  .stTabs [data-baseweb="tab-panel"] { padding-top: 2rem !important; }

  /* ─ Buttons */
  .stButton > button {
    font-family: 'Space Grotesk', sans-serif !important;
    font-weight: 700 !important;
    font-size: 0.8rem !important;
    letter-spacing: 0.1em !important;
    text-transform: uppercase !important;
    background: transparent !important;
    color: #6eff6e !important;
    border: 1px solid #3a7a3a !important;
    border-radius: 2px !important;
    padding: 0.65rem 1.5rem !important;
    transition: all 0.2s !important;
  }
  .stButton > button:hover {
    background: rgba(110,255,110,0.1) !important;
    border-color: #6eff6e !important;
    color: #ffffff !important;
  }
  div[data-testid="stButton"] > button[kind="primary"] {
    background: #1a4a1a !important;
    border-color: #6eff6e !important;
    color: #6eff6e !important;
  }

  /* ─ Inputs */
  .stNumberInput input, .stTextInput input {
    background: #0a1a0e !important;
    border: 1px solid #1a3a20 !important;
    color: #c8f0c8 !important;
    border-radius: 2px !important;
    font-family: 'JetBrains Mono', monospace !important;
    font-size: 0.85rem !important;
  }
  .stNumberInput input:focus, .stTextInput input:focus {
    border-color: #3a7a3a !important;
    box-shadow: 0 0 0 2px rgba(110,255,110,0.08) !important;
  }
  [data-baseweb="select"] > div {
    background: #0a1a0e !important;
    border-color: #1a3a20 !important;
    color: #c8f0c8 !important;
    border-radius: 2px !important;
  }
  [data-baseweb="select"] svg { color: #3a7a3a !important; }
  [data-baseweb="popover"] { background: #0d2010 !important; border: 1px solid #1a3a20 !important; }
  [role="option"] { background: #0d2010 !important; color: #c8f0c8 !important; }
  [role="option"]:hover { background: #1a3a20 !important; }

  /* ─ Slider */
  [data-testid="stSlider"] > div > div > div > div { background: #3a7a3a !important; }
  [data-testid="stSlider"] > div > div > div { background: #1a3a20 !important; }

  /* ─ Data editor / dataframe */
  .stDataFrame, .stDataEditor { border: 1px solid #1a3a20 !important; border-radius: 2px !important; }
  [data-testid="stDataFrame"] th {
    background: #0d2010 !important;
    color: rgba(200,240,200,0.5) !important;
    font-size: 0.65rem !important;
    letter-spacing: 0.1em !important;
    text-transform: uppercase !important;
  }

  /* ─ Metrics */
  [data-testid="stMetricValue"] {
    font-family: 'Space Grotesk', sans-serif !important;
    font-size: 1.6rem !important;
    font-weight: 700 !important;
    color: #6eff6e !important;
  }
  [data-testid="stMetricLabel"] {
    font-size: 0.65rem !important;
    letter-spacing: 0.1em !important;
    text-transform: uppercase !important;
    color: rgba(200,240,200,0.4) !important;
  }
  [data-testid="stMetricDelta"] { font-size: 0.75rem !important; }

  /* ─ Spinner */
  .stSpinner > div { border-color: #3a7a3a #1a3a20 #1a3a20 !important; }

  /* ─ Alert / info */
  .stAlert { border-radius: 2px !important; border: 1px solid #1a3a20 !important; }

  /* ─ Divider */
  hr { border-color: #1a3a20 !important; }

  /* ─ Headings */
  h1, h2, h3, h4 { font-family: 'Space Grotesk', sans-serif !important; }

  /* ─ Custom components (injected via markdown) */
  .eco-section-label {
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.6rem;
    letter-spacing: 0.2em;
    text-transform: uppercase;
    color: #3a7a3a;
    margin-bottom: 4px;
  }
  .eco-section-title {
    font-family: 'Space Grotesk', sans-serif;
    font-size: 1.25rem;
    font-weight: 700;
    color: #c8f0c8;
    margin-bottom: 1.5rem;
    padding-bottom: 0.75rem;
    border-bottom: 1px solid #1a3a20;
  }
  .eco-card {
    background: #0a1a0e;
    border: 1px solid #1a3a20;
    border-radius: 2px;
    padding: 1.25rem 1.5rem;
    position: relative;
  }
  .eco-card-accent {
    position: absolute;
    top: 0; left: 0; right: 0; height: 2px;
    background: linear-gradient(90deg, #1a3a20, #3a7a3a, transparent);
  }
  .eco-kv-label { font-size: 0.6rem; letter-spacing: 0.15em; text-transform: uppercase; color: rgba(200,240,200,0.35); }
  .eco-kv-value { font-family: 'Space Grotesk', sans-serif; font-weight: 700; font-size: 1.8rem; color: #6eff6e; line-height: 1; margin: 4px 0; }
  .eco-kv-sub   { font-size: 0.68rem; color: rgba(200,240,200,0.4); }

  .eco-result-main {
    background: #0a1a0e;
    border: 1px solid #3a7a3a;
    border-radius: 2px;
    padding: 2.5rem;
    text-align: center;
    position: relative;
    overflow: hidden;
  }
  .eco-result-main::before {
    content: '';
    position: absolute;
    top: 0; left: 0; right: 0; height: 3px;
    background: linear-gradient(90deg, transparent, #6eff6e, transparent);
  }
  .eco-result-label { font-size: 0.62rem; letter-spacing: 0.18em; text-transform: uppercase; color: #3a7a3a; margin-bottom: 0.5rem; }
  .eco-result-num   { font-family: 'Space Grotesk', sans-serif; font-size: 3.5rem; font-weight: 700; color: #6eff6e; line-height: 1; }
  .eco-result-unit  { font-size: 0.8rem; color: rgba(200,240,200,0.45); margin-top: 0.4rem; }
  .eco-result-range { font-size: 0.68rem; color: rgba(200,240,200,0.3); margin-top: 1rem; border-top: 1px solid #1a3a20; padding-top: 0.75rem; }

  .eco-stat-row { display: grid; grid-template-columns: repeat(3, 1fr); gap: 10px; margin-top: 1rem; }
  .eco-stat-cell {
    background: #060e08;
    border: 1px solid #1a3a20;
    padding: 0.8rem 1rem;
    border-radius: 2px;
  }

  .eco-route-stop {
    display: flex;
    align-items: center;
    gap: 0.75rem;
    background: #0a1a0e;
    border: 1px solid #1a3a20;
    border-left: 3px solid #1a3a20;
    padding: 0.6rem 1rem;
    margin: 4px 0;
    border-radius: 0 2px 2px 0;
    transition: border-left-color 0.2s;
  }
  .eco-route-stop.depot { border-left-color: #6eff6e; }
  .eco-route-stop.high-fill { border-left-color: #e05a2b; }
  .eco-route-stop.med-fill  { border-left-color: #f5c842; }
  .eco-stop-num { font-family: 'Space Grotesk', sans-serif; font-weight: 700; font-size: 1rem; color: #6eff6e; min-width: 1.5rem; }
  .eco-stop-name { flex: 1; font-size: 0.8rem; color: #c8f0c8; }
  .eco-stop-coord { font-size: 0.65rem; color: rgba(200,240,200,0.3); }
  .eco-stop-fill { font-family: 'Space Grotesk', sans-serif; font-weight: 600; font-size: 0.8rem; }

  .eco-pill {
    display: inline-block;
    padding: 2px 10px;
    border-radius: 100px;
    font-size: 0.6rem;
    letter-spacing: 0.1em;
    text-transform: uppercase;
  }
  .eco-pill-green { background: rgba(110,255,110,0.1); border: 1px solid rgba(110,255,110,0.3); color: #6eff6e; }
  .eco-pill-amber { background: rgba(245,200,66,0.1); border: 1px solid rgba(245,200,66,0.3); color: #f5c842; }
  .eco-pill-red   { background: rgba(224,90,43,0.1); border: 1px solid rgba(224,90,43,0.3); color: #e05a2b; }
  .eco-pill-grey  { background: rgba(200,240,200,0.05); border: 1px solid rgba(200,240,200,0.15); color: rgba(200,240,200,0.4); }

  .eco-divider-label {
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.62rem;
    letter-spacing: 0.15em;
    text-transform: uppercase;
    color: #1e4a22;
    margin: 1.5rem 0 0.75rem;
    padding-bottom: 0.4rem;
    border-bottom: 1px solid #1a3a20;
  }

  .eco-empty-state {
    background: #0a1a0e;
    border: 1px dashed #1a3a20;
    border-radius: 2px;
    padding: 3.5rem 2rem;
    text-align: center;
    margin-top: 1rem;
  }
  .eco-empty-icon { font-size: 2.5rem; margin-bottom: 0.75rem; opacity: 0.4; }
  .eco-empty-msg { font-family: 'Space Grotesk', sans-serif; font-size: 0.85rem; font-weight: 600; color: rgba(200,240,200,0.3); }
  .eco-empty-sub { font-size: 0.68rem; color: rgba(200,240,200,0.2); margin-top: 0.4rem; }

  .eco-svg-wrap {
    background: #060e08;
    border: 1px solid #1a3a20;
    border-radius: 2px;
    padding: 1rem;
    margin-top: 1.25rem;
  }

  .form-group-title {
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.62rem;
    letter-spacing: 0.15em;
    text-transform: uppercase;
    color: #3a7a3a;
    margin: 1.25rem 0 0.6rem;
    padding-bottom: 0.4rem;
    border-bottom: 1px solid #1a3a20;
  }
</style>
""", unsafe_allow_html=True)


# ─── HELPERS ───────────────────────────────────────────────────────────────────
def api_post(endpoint: str, payload: dict):
    try:
        r = requests.post(f"{API}{endpoint}", json=payload, timeout=20)
        r.raise_for_status()
        return r.json()
    except requests.exceptions.ConnectionError:
        return {"error": "Cannot connect to backend — make sure it's running:\n\nuvicorn backend.main:app --reload --port 8000"}
    except Exception as e:
        return {"error": str(e)}


def api_get(endpoint: str):
    try:
        r = requests.get(f"{API}{endpoint}", timeout=5)
        return r.json()
    except:
        return {"status": "offline"}


def section(label: str, title: str):
    st.markdown(f'<div class="eco-section-label">{label}</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="eco-section-title">{title}</div>', unsafe_allow_html=True)


def form_group(label: str):
    st.markdown(f'<div class="form-group-title">{label}</div>', unsafe_allow_html=True)


def empty_state(icon: str, msg: str, sub: str):
    st.markdown(f"""
    <div class="eco-empty-state">
      <div class="eco-empty-icon">{icon}</div>
      <div class="eco-empty-msg">{msg}</div>
      <div class="eco-empty-sub">{sub}</div>
    </div>""", unsafe_allow_html=True)


def render_result_box(label: str, value: str, unit: str, ci_low: str, ci_high: str):
    st.markdown(f"""
    <div class="eco-result-main">
      <div class="eco-result-label">{label}</div>
      <div class="eco-result-num">{value}</div>
      <div class="eco-result-unit">{unit}</div>
      <div class="eco-result-range">95% CI &nbsp;|&nbsp; {ci_low} &ndash; {ci_high}</div>
    </div>""", unsafe_allow_html=True)


def render_stat_row(stats: list):
    """stats = [(label, value, sub), ...]"""
    cells = ""
    for label, value, sub in stats:
        cells += f"""
        <div class="eco-stat-cell">
          <div class="eco-kv-label">{label}</div>
          <div class="eco-kv-value" style="font-size:1.3rem;">{value}</div>
          <div class="eco-kv-sub">{sub}</div>
        </div>"""
    st.markdown(f'<div class="eco-stat-row">{cells}</div>', unsafe_allow_html=True)


def render_route_svg(stops_data: list, ordered_stops: list, W=580, H=300):
    """Simple SVG map of route stops with connecting lines."""
    if not ordered_stops or len(ordered_stops) < 2:
        return ""
    lats = [s["lat"] for s in ordered_stops]
    lons = [s["lon"] for s in ordered_stops]
    min_lat, max_lat = min(lats), max(lats)
    min_lon, max_lon = min(lons), max(lons)
    pad = 40

    def to_xy(lat, lon):
        if max_lat == min_lat or max_lon == min_lon:
            return W // 2, H // 2
        x = pad + (lon - min_lon) / (max_lon - min_lon) * (W - 2 * pad)
        y = H - pad - (lat - min_lat) / (max_lat - min_lat) * (H - 2 * pad)
        return int(x), int(y)

    coords = [to_xy(s["lat"], s["lon"]) for s in ordered_stops]

    # Build path
    path_d = f"M {coords[0][0]} {coords[0][1]} " + " ".join(
        f"L {x} {y}" for x, y in coords[1:]
    ) + f" L {coords[0][0]} {coords[0][1]}"

    # Stop circles
    circles = ""
    for i, (stop, (x, y)) in enumerate(zip(ordered_stops, coords)):
        fill_pct = stop.get("fill_percent", stop.get("fill", 0))
        is_depot = i == 0 or i == len(ordered_stops) - 1
        if is_depot:
            color = "#6eff6e"
            r = 8
        elif fill_pct >= 85:
            color = "#e05a2b"
            r = 6
        elif fill_pct >= 70:
            color = "#f5c842"
            r = 6
        else:
            color = "#3a7a3a"
            r = 6

        short = stop.get("name", f"#{i+1}")[:12]
        circles += f"""
        <circle cx="{x}" cy="{y}" r="{r}" fill="{color}" stroke="#060e08" stroke-width="2"/>
        <text x="{x}" y="{y - r - 4}" text-anchor="middle"
              font-family="JetBrains Mono" font-size="9" fill="rgba(200,240,200,0.5)">{i+1}</text>"""

    svg = f"""
    <svg width="{W}" height="{H}" xmlns="http://www.w3.org/2000/svg">
      <defs>
        <marker id="arr" markerWidth="8" markerHeight="6" refX="8" refY="3" orient="auto">
          <polygon points="0 0, 8 3, 0 6" fill="#3a7a3a"/>
        </marker>
      </defs>
      <rect width="{W}" height="{H}" fill="#060e08"/>
      <!-- grid lines -->
      {''.join(f'<line x1="0" y1="{int(H*i/5)}" x2="{W}" y2="{int(H*i/5)}" stroke="#0e2812" stroke-width="1"/>' for i in range(6))}
      {''.join(f'<line x1="{int(W*i/8)}" y1="0" x2="{int(W*i/8)}" y2="{H}" stroke="#0e2812" stroke-width="1"/>' for i in range(9))}
      <!-- route path -->
      <path d="{path_d}" stroke="#2a5a2a" stroke-width="1.5" fill="none" stroke-dasharray="4 3"/>
      <!-- optimized path bold -->
      <path d="{path_d}" stroke="#3a7a3a" stroke-width="1" fill="none"
            marker-end="url(#arr)" opacity="0.7"/>
      {circles}
      <!-- legend -->
      <circle cx="12" cy="{H-24}" r="5" fill="#6eff6e"/>
      <text x="22" y="{H-20}" font-family="JetBrains Mono" font-size="8" fill="rgba(200,240,200,0.4)">Depot</text>
      <circle cx="60" cy="{H-24}" r="5" fill="#e05a2b"/>
      <text x="70" y="{H-20}" font-family="JetBrains Mono" font-size="8" fill="rgba(200,240,200,0.4)">&gt;85% full</text>
      <circle cx="115" cy="{H-24}" r="5" fill="#f5c842"/>
      <text x="125" y="{H-20}" font-family="JetBrains Mono" font-size="8" fill="rgba(200,240,200,0.4)">&gt;70% full</text>
    </svg>"""
    return svg


# ─── SIDEBAR ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("""
    <div style="padding: 0.75rem 0 1.25rem;">
      <div style="font-family:'Space Grotesk',sans-serif;font-size:1.5rem;font-weight:700;
                  color:#6eff6e;letter-spacing:-0.03em;line-height:1;">♻ EcoMind</div>
      <div style="font-size:0.58rem;letter-spacing:0.2em;text-transform:uppercase;
                  color:rgba(200,240,200,0.25);margin-top:4px;">Smart Waste AI · v2.0</div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown('<hr style="border-color:#1a3a20;margin:0 0 1rem;">', unsafe_allow_html=True)

    # Backend health check
    health = api_get("/health")
    status = health.get("status", "offline")
    if status == "ready":
        st.markdown('<span class="eco-pill eco-pill-green">● Backend Online</span>', unsafe_allow_html=True)
    elif status == "models_not_trained":
        st.markdown('<span class="eco-pill eco-pill-amber">⚠ Models Not Trained</span>', unsafe_allow_html=True)
    else:
        st.markdown('<span class="eco-pill eco-pill-red">✕ Backend Offline</span>', unsafe_allow_html=True)
        st.markdown("""
        <div style="font-size:0.65rem;color:rgba(200,240,200,0.3);margin-top:0.6rem;
                    font-family:'JetBrains Mono',monospace;line-height:1.7;">
          Start backend:<br>
          <span style="color:#3a7a3a;">uvicorn backend.main:app<br>--reload --port 8000</span>
        </div>""", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # Model metrics
    metrics_data = health.get("metrics", {})
    if metrics_data:
        st.markdown('<div class="eco-section-label">Model Performance</div>', unsafe_allow_html=True)
        for name, m in metrics_data.items():
            r2 = m.get("r2", 0)
            c = "#6eff6e" if r2 > 0.9 else "#f5c842" if r2 > 0.7 else "#e05a2b"
            st.markdown(f"""
            <div style="background:#060e08;border:1px solid #1a3a20;padding:0.75rem 1rem;
                        margin:5px 0;border-radius:2px;">
              <div style="font-size:0.58rem;letter-spacing:0.15em;text-transform:uppercase;
                          color:rgba(200,240,200,0.3);">{name}</div>
              <div style="font-family:'Space Grotesk',sans-serif;font-weight:700;
                          font-size:1.1rem;color:{c};margin:3px 0;">R² {r2:.3f}</div>
              <div style="font-size:0.62rem;color:rgba(200,240,200,0.25);">
                MAE {m.get('mae',0):.2f} &nbsp;·&nbsp; RMSE {m.get('rmse',0):.2f}
              </div>
            </div>""", unsafe_allow_html=True)

    st.markdown('<hr style="border-color:#1a3a20;margin:1rem 0;">', unsafe_allow_html=True)

    # Dataset info
    st.markdown("""
    <div style="font-size:0.6rem;color:rgba(200,240,200,0.2);font-family:'JetBrains Mono',monospace;line-height:2;">
      <span style="color:#1e4a22;">DATASET</span> Eco_ML_Dataset<br>
      Records &nbsp;&nbsp;&nbsp;10,000<br>
      Areas &nbsp;&nbsp;&nbsp;&nbsp; 100<br>
      Vehicles &nbsp;&nbsp;50<br>
      Period &nbsp;&nbsp;&nbsp;&nbsp;Jan–Dec 2024
    </div>""", unsafe_allow_html=True)


# ─── PAGE HEADER ───────────────────────────────────────────────────────────────
st.markdown("""
<div style="background:#0a1a0e;border:1px solid #1a3a20;border-radius:2px;
            padding:2rem 2.5rem;margin-bottom:2rem;position:relative;overflow:hidden;">
  <div style="position:absolute;top:0;left:0;right:0;height:3px;
              background:linear-gradient(90deg,#0a1a0e,#6eff6e 40%,#3a7a3a 70%,#0a1a0e);"></div>
  <div style="position:absolute;bottom:-60px;right:-30px;width:200px;height:200px;
              border-radius:50%;border:1px solid rgba(110,255,110,0.05);pointer-events:none;"></div>
  <div style="position:absolute;bottom:-40px;right:-10px;width:140px;height:140px;
              border-radius:50%;border:1px solid rgba(110,255,110,0.07);pointer-events:none;"></div>
  <div style="font-family:'Space Grotesk',sans-serif;font-size:1.8rem;font-weight:700;
              color:#6eff6e;letter-spacing:-0.03em;line-height:1;margin-bottom:0.4rem;">
    Smart Waste AI
  </div>
  <div style="font-size:0.7rem;letter-spacing:0.15em;text-transform:uppercase;
              color:rgba(200,240,200,0.3);">
    Water Demand &nbsp;·&nbsp; Waste Generation &nbsp;·&nbsp; Route Optimization
  </div>
</div>
""", unsafe_allow_html=True)


# ─── TABS ──────────────────────────────────────────────────────────────────────
tab1, tab2, tab3 = st.tabs([
    "▸ 01 &nbsp; Water Demand",
    "▸ 02 &nbsp; Waste Generation",
    "▸ 03 &nbsp; Route Optimization",
])


# ══════════════════════════════════════════════════════════════════════════════
#  TAB 1 — WATER DEMAND
# ══════════════════════════════════════════════════════════════════════════════
with tab1:
    section("Prediction Model · XGBoost", "Water Demand Forecast")

    col_form, col_gap, col_result = st.columns([1.05, 0.05, 1])

    with col_form:
        form_group("Area & Demographics")
        c1, c2 = st.columns(2)
        area_id = c1.number_input("Area ID", 1, 100, 18, key="w1_area")
        pop     = c2.number_input("Population", 1000, 1000000, 27836, step=1000, key="w1_pop")
        pop_den = c1.number_input("Pop. Density /km²", 100.0, 50000.0, 22342.0, step=100.0, key="w1_pd")
        hh_size = c2.number_input("Household Size", 1, 12, 6, key="w1_hh")
        income  = c1.number_input("Per Capita Income ₹", 50000, 1000000, 355551, step=10000, key="w1_inc")
        urban   = c2.selectbox("Urban / Rural", ["Urban", "Rural"], key="w1_ur")

        form_group("Climate & Season")
        c3, c4 = st.columns(2)
        temp     = c3.slider("Temperature °C", 5.0, 50.0, 35.4, key="w1_t")
        rain     = c4.slider("Rainfall mm", 0.0, 400.0, 182.5, key="w1_r")
        humidity = c3.slider("Humidity %", 10.0, 100.0, 71.6, key="w1_h")
        season   = c4.selectbox("Season", ["Summer", "Monsoon", "Winter"], key="w1_s")

        form_group("Events & History")
        c5, c6 = st.columns(2)
        day_type   = c5.selectbox("Day Type", ["Weekday", "Weekend"], key="w1_dt")
        festival   = c6.selectbox("Festival", ["None", "Diwali", "Holi", "Eid", "Christmas"], key="w1_fest")
        past_water = st.number_input("Past Water Usage L", 50.0, 800.0, 399.29, key="w1_pw")
        recycle    = st.slider("Recycling Rate %", 0.0, 100.0, 30.7, key="w1_rec")
        sel_date   = st.date_input("Forecast Date", date.today(), key="w1_date")

        st.markdown("<br>", unsafe_allow_html=True)
        predict_water = st.button("▸ Predict Water Demand", use_container_width=True, key="w1_btn")

    with col_result:
        if predict_water:
            d = sel_date
            payload = {
                "Area_ID": area_id, "Population": pop,
                "Population_Density": pop_den, "Household_Size": hh_size,
                "Per_Capita_Income": income, "Urban_Rural_Type": urban,
                "Temperature_C": temp, "Rainfall_mm": rain,
                "Humidity_percent": humidity, "Season": season,
                "Day_Type": day_type, "Festival_Event": festival,
                "Disaster_Event": "None", "Past_Water_Usage": past_water,
                "Recycling_Rate_percent": recycle,
                "month": d.month, "dayofweek": d.weekday(), "dayofyear": d.timetuple().tm_yday
            }
            with st.spinner("Running model inference…"):
                resp = api_post("/predict/water", payload)

            if "error" in resp:
                st.error(resp["error"])
            else:
                pred = resp["prediction"]
                val  = pred["water_demand_liters"]
                lo   = pred["lower_bound"]
                hi   = pred["upper_bound"]

                render_result_box(
                    "Predicted Water Demand",
                    f"{val:,.0f}",
                    "Litres / Day",
                    f"{lo:,.0f} L",
                    f"{hi:,.0f} L"
                )

                per_cap  = val / pop * 1000
                delta_pct = ((val / (past_water + 1e-6)) - 1) * 100

                render_stat_row([
                    ("Per Capita", f"{per_cap:.1f} mL", "per person / day"),
                    ("CI Width",   f"{hi - lo:,.0f} L", "uncertainty band"),
                    ("vs Past",    f"{delta_pct:+.1f}%", "vs past water usage"),
                ])

                st.markdown("<br>", unsafe_allow_html=True)
                st.markdown('<div class="eco-section-label">Feature Sensitivity</div>', unsafe_allow_html=True)
                factors = {
                    "Past Water": past_water / 500,
                    "Population": pop / 100000,
                    "Temperature": temp / 50,
                    "Rainfall": rain / 400,
                    "Humidity": humidity / 100,
                    "Income": income / 500000,
                }
                chart_df = pd.DataFrame.from_dict(factors, orient="index", columns=["score"])
                st.bar_chart(chart_df, color="#3a7a3a", height=200)
        else:
            empty_state("💧", "Set parameters and run prediction", "XGBoost · LightGBM · GBR ensemble on 10K records")


# ══════════════════════════════════════════════════════════════════════════════
#  TAB 2 — WASTE GENERATION
# ══════════════════════════════════════════════════════════════════════════════
with tab2:
    section("Prediction Model · Stacked Ensemble", "Waste Generation Forecast")

    col_wf, col_wg, col_wr = st.columns([1.05, 0.05, 1])

    with col_wf:
        form_group("Area & Demographics")
        w_c1, w_c2 = st.columns(2)
        w_area  = w_c1.number_input("Area ID", 1, 100, 63, key="w2_area")
        w_pop   = w_c2.number_input("Population", 1000, 1000000, 122028, step=1000, key="w2_pop")
        w_pd    = w_c1.number_input("Pop. Density /km²", 100.0, 50000.0, 20969.0, step=100.0, key="w2_pd")
        w_urban = w_c2.selectbox("Urban / Rural", ["Urban", "Rural"], key="w2_ur")

        form_group("Climate & Season")
        w_c3, w_c4 = st.columns(2)
        w_temp   = w_c3.slider("Temperature °C", 5.0, 50.0, 40.4, key="w2_t")
        w_rain   = w_c4.slider("Rainfall mm", 0.0, 400.0, 190.8, key="w2_r")
        w_season = w_c3.selectbox("Season", ["Summer", "Monsoon", "Winter"], key="w2_s")
        w_day    = w_c4.selectbox("Day Type", ["Weekday", "Weekend"], key="w2_d")
        w_fest   = w_c3.selectbox("Festival", ["None", "Diwali", "Holi", "Eid", "Christmas"], key="w2_f")

        form_group("Historical Waste (tons)")
        wh1, wh2, wh3 = st.columns(3)
        w_t1  = wh1.number_input("Yesterday", 10.0, 600.0, 481.94, key="w2_t1")
        w_t7  = wh2.number_input("Last 7d", 100.0, 5000.0, 3201.32, key="w2_t7")
        w_t30 = wh3.number_input("Last 30d", 500.0, 20000.0, 6325.58, key="w2_t30")

        form_group("Waste Composition %")
        wo1, wo2 = st.columns(2)
        w_org = wo1.slider("Organic",  0.0, 100.0, 45.8, key="w2_org")
        w_pla = wo2.slider("Plastic",  0.0, 100.0, 27.3, key="w2_pla")
        w_pap = wo1.slider("Paper",    0.0, 100.0,  9.8, key="w2_pap")
        w_oth = wo2.slider("Other",    0.0, 100.0, 12.1, key="w2_oth")

        form_group("Collection Parameters")
        w_coll   = st.number_input("Collection Frequency / week", 1, 7, 5, key="w2_coll")
        w_rec    = st.slider("Recycling Rate %", 0.0, 100.0, 25.1, key="w2_rec")
        w_date   = st.date_input("Forecast Date", date.today(), key="w2_date")

        st.markdown("<br>", unsafe_allow_html=True)
        predict_waste_btn = st.button("▸ Predict Waste Generation", use_container_width=True, key="w2_btn")

    with col_wr:
        if predict_waste_btn:
            d = w_date
            payload = {
                "Area_ID": w_area, "Population": w_pop,
                "Population_Density": w_pd, "Household_Size": 4,
                "Per_Capita_Income": 250000, "Urban_Rural_Type": w_urban,
                "Temperature_C": w_temp, "Rainfall_mm": w_rain,
                "Humidity_percent": 60.0, "Season": w_season,
                "Day_Type": w_day, "Festival_Event": w_fest,
                "Disaster_Event": "None",
                "Past_Waste_t1_tons": w_t1, "Past_Waste_t7_tons": w_t7,
                "Past_Waste_t30_tons": w_t30,
                "Organic_Waste_percent": w_org, "Plastic_Waste_percent": w_pla,
                "Paper_Waste_percent": w_pap, "Other_Waste_percent": w_oth,
                "Collection_Frequency_per_week": w_coll,
                "Recycling_Rate_percent": w_rec,
                "month": d.month, "dayofweek": d.weekday(), "dayofyear": d.timetuple().tm_yday
            }
            with st.spinner("Running stacked ensemble…"):
                resp = api_post("/predict/waste", payload)

            if "error" in resp:
                st.error(resp["error"])
            else:
                pred  = resp["prediction"]
                waste = pred["waste_generated_tons"]
                lo    = pred["lower_bound"]
                hi    = pred["upper_bound"]
                trend = ((waste / (w_t1 + 1e-6)) - 1) * 100

                render_result_box(
                    "Predicted Waste Generation",
                    f"{waste:.2f}",
                    "Tonnes / Day",
                    f"{lo:.2f} t",
                    f"{hi:.2f} t"
                )

                render_stat_row([
                    ("Weekly",    f"{waste * 7:.1f} t",   "7-day projection"),
                    ("Monthly",   f"{waste * 30:.0f} t",  "30-day projection"),
                    ("Day Trend", f"{trend:+.1f}%",       "vs yesterday"),
                ])

                st.markdown("<br>", unsafe_allow_html=True)
                st.markdown('<div class="eco-section-label">Waste Breakdown (projected)</div>', unsafe_allow_html=True)
                total = w_org + w_pla + w_pap + w_oth + 1e-6
                comp_df = pd.DataFrame({
                    "Category": ["Organic", "Plastic", "Paper", "Other"],
                    "Tons": [
                        waste * w_org / total,
                        waste * w_pla / total,
                        waste * w_pap / total,
                        waste * w_oth / total,
                    ]
                })
                st.bar_chart(comp_df.set_index("Category"), color="#3a7a3a", height=220)
        else:
            empty_state("🗑️", "Configure parameters and run forecast", "XGBoost + LightGBM + RandomForest · Ridge meta-learner")


# ══════════════════════════════════════════════════════════════════════════════
#  TAB 3 — ROUTE OPTIMIZATION
# ══════════════════════════════════════════════════════════════════════════════
with tab3:
    section("2-Opt + ML Cost Scoring", "Waste Collection Route Optimizer")

    # Vehicle config
    form_group("Vehicle Configuration")
    rv1, rv2, rv3 = st.columns(3)
    v_cap  = rv1.number_input("Capacity kg", 1000, 10000, 5000, step=500, key="rt_cap")
    v_load = rv2.number_input("Current Load kg", 0, 10000, 0, step=100, key="rt_load")
    v_fuel = rv3.number_input("Fuel Efficiency km/L", 1.0, 20.0, 5.0, step=0.5, key="rt_fuel")

    form_group("Collection Stops  ·  First row = Depot")

    # Session state for stops
    if "route_stops" not in st.session_state:
        st.session_state.route_stops = [
            {"id": "DEPOT",  "name": "Municipal Depot",       "lat": 17.385, "lon": 78.487, "waste_kg": 0,   "fill": 0,  "traffic": "Low",    "road": "Highway",     "cond": "Good"},
            {"id": "ZONE-A", "name": "Zone A — Jubilee Hills", "lat": 17.431, "lon": 78.409, "waste_kg": 620, "fill": 85, "traffic": "High",   "road": "Main_Road",   "cond": "Good"},
            {"id": "ZONE-B", "name": "Zone B — Banjara Hills", "lat": 17.415, "lon": 78.441, "waste_kg": 480, "fill": 72, "traffic": "Medium", "road": "Main_Road",   "cond": "Average"},
            {"id": "ZONE-C", "name": "Zone C — Madhapur",      "lat": 17.449, "lon": 78.390, "waste_kg": 730, "fill": 91, "traffic": "High",   "road": "Highway",     "cond": "Good"},
            {"id": "ZONE-D", "name": "Zone D — Gachibowli",    "lat": 17.440, "lon": 78.347, "waste_kg": 290, "fill": 58, "traffic": "Medium", "road": "Highway",     "cond": "Good"},
            {"id": "ZONE-E", "name": "Zone E — Kondapur",      "lat": 17.471, "lon": 78.356, "waste_kg": 410, "fill": 68, "traffic": "Low",    "road": "Residential", "cond": "Average"},
            {"id": "PLANT",  "name": "Recycling Plant",        "lat": 17.360, "lon": 78.480, "waste_kg": 0,   "fill": 0,  "traffic": "Low",    "road": "Highway",     "cond": "Good"},
        ]

    col_add, _ = st.columns([1, 5])
    if col_add.button("＋ Add Stop", key="rt_add"):
        n = len(st.session_state.route_stops)
        if n < 15:
            st.session_state.route_stops.append({
                "id": f"ZONE-{n}", "name": f"New Zone {n}",
                "lat": round(17.385 + np.random.uniform(-0.06, 0.06), 4),
                "lon": round(78.487 + np.random.uniform(-0.12, 0.12), 4),
                "waste_kg": 400, "fill": 65, "traffic": "Medium",
                "road": "Main_Road", "cond": "Average"
            })

    stop_df = pd.DataFrame(st.session_state.route_stops)
    edited  = st.data_editor(
        stop_df[["id","name","lat","lon","waste_kg","fill","traffic","road","cond"]],
        use_container_width=True,
        num_rows="dynamic",
        column_config={
            "id":       st.column_config.TextColumn("Stop ID", width="small"),
            "name":     st.column_config.TextColumn("Name"),
            "lat":      st.column_config.NumberColumn("Latitude",   format="%.4f"),
            "lon":      st.column_config.NumberColumn("Longitude",  format="%.4f"),
            "waste_kg": st.column_config.NumberColumn("Waste kg",   min_value=0),
            "fill":     st.column_config.NumberColumn("Fill %",     min_value=0, max_value=100),
            "traffic":  st.column_config.SelectboxColumn("Traffic", options=["Low","Medium","High"]),
            "road":     st.column_config.SelectboxColumn("Road",    options=["Residential","Main_Road","Highway"]),
            "cond":     st.column_config.SelectboxColumn("Condition",options=["Poor","Average","Good"]),
        },
        key="rt_editor"
    )

    st.markdown("<br>", unsafe_allow_html=True)
    optimize_btn = st.button("▸ Run 2-Opt + ML Route Optimization", use_container_width=True, key="rt_run")

    if optimize_btn:
        stops_payload = []
        for _, row in edited.iterrows():
            stops_payload.append({
                "id": str(row["id"]), "name": str(row["name"]),
                "lat": float(row["lat"]), "lon": float(row["lon"]),
                "waste_kg": float(row.get("waste_kg", 400)),
                "fill_percent": float(row.get("fill", 65)),
                "traffic": str(row.get("traffic", "Medium")),
                "road_type_str": str(row.get("road", "Main_Road")),
                "road_condition": str(row.get("cond", "Average")),
                "one_way": 0, "toll": 0,
                "population_density": 5000, "collection_freq": 3
            })

        with st.spinner("Running greedy NN → 2-opt → ML cost scoring…"):
            resp = api_post("/optimize", {
                "stops": stops_payload,
                "vehicle": {"capacity_kg": v_cap, "current_load_kg": v_load, "fuel_km_per_l": v_fuel},
                "depot_index": 0
            })

        if "error" in resp:
            st.error(resp["error"])
        else:
            opt = resp["optimization"]

            st.markdown('<hr style="border-color:#1a3a20;margin:1.5rem 0;">', unsafe_allow_html=True)
            section("Optimization Results", "Optimized Route")

            # KPI row
            k1, k2, k3, k4 = st.columns(4)
            k1.metric("Total Distance",    f"{opt['total_distance_km']} km")
            k2.metric("Est. Travel Time",  f"{opt['total_time_min']:.0f} min")
            k3.metric("2-opt Improvement", f"{opt.get('improvement_percent', opt.get('saved_percent', 0)):.1f}%",
          delta=f"saved {opt.get('saved_km', 0):.2f} km")
            k4.metric("Stops",             str(opt['num_stops']))

            col_seq, col_map = st.columns([1, 1.4])

            with col_seq:
                st.markdown('<div class="eco-section-label">Stop Sequence</div>', unsafe_allow_html=True)
                ordered = opt.get("ordered_stops", [])
                for i, stop in enumerate(ordered):
                    fill  = stop.get("fill_percent", stop.get("fill", 0))
                    is_depot = i == 0 or i == len(ordered) - 1
                    if is_depot:
                        cls = "eco-route-stop depot"
                        fill_color = "#6eff6e"
                    elif fill >= 85:
                        cls = "eco-route-stop high-fill"
                        fill_color = "#e05a2b"
                    elif fill >= 70:
                        cls = "eco-route-stop med-fill"
                        fill_color = "#f5c842"
                    else:
                        cls = "eco-route-stop"
                        fill_color = "#3a7a3a"

                    st.markdown(f"""
                    <div class="{cls}">
                      <span class="eco-stop-num">{i+1}</span>
                      <div style="flex:1;">
                        <div class="eco-stop-name">{stop['name']}</div>
                        <div class="eco-stop-coord">{stop['lat']:.4f}, {stop['lon']:.4f}</div>
                      </div>
                      <span class="eco-stop-fill" style="color:{fill_color};">{fill:.0f}%</span>
                    </div>""", unsafe_allow_html=True)

            with col_map:
                st.markdown('<div class="eco-section-label">Route Map</div>', unsafe_allow_html=True)
                svg = render_route_svg(stops_payload, ordered, W=520, H=320)
                if svg:
                    st.markdown(f'<div class="eco-svg-wrap">{svg}</div>', unsafe_allow_html=True)

            # Comparison chart
            st.markdown("<br>", unsafe_allow_html=True)
            st.markdown('<div class="eco-section-label">Greedy vs 2-Opt Comparison</div>', unsafe_allow_html=True)
            comp_df = pd.DataFrame({
                "Method":     ["Greedy (Initial)", "2-Opt (Optimized)"],
                "Cost Score": [opt.get("greedy_cost", 0), opt.get("total_cost_score", 0)],
            })
            st.bar_chart(comp_df.set_index("Method"), color="#3a7a3a", height=180)
    else:
        empty_state("🗺️", "Configure stops and run route optimization", "Haversine distance · Greedy NN · 2-opt · ML cost scoring")