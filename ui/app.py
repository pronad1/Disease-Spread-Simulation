"""
ui/app.py — EpiSim interactive Streamlit dashboard.
Premium UI edition with glassmorphism, animated hero, glow metrics, and rich charts.
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st
import streamlit.components.v1 as components

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import importlib
import episim
importlib.reload(episim)
from episim import run_scenario, simulate_seird  # noqa: E402

# ---------------------------------------------------------------------------
# Page config
# ---------------------------------------------------------------------------
st.set_page_config(
    page_title="EpiSim — Disease Spread Simulation",
    page_icon="🦠",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ---------------------------------------------------------------------------
# Premium CSS — glassmorphism, animated hero, glowing cards
# ---------------------------------------------------------------------------
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&family=JetBrains+Mono:wght@400;600&display=swap');

/* ── Global reset ─────────────────────────────────────── */
html, body, [class*="css"] {
    font-family: 'Inter', sans-serif !important;
}

/* Hide default Streamlit chrome */
#MainMenu, footer, header,
button[title="Deploy"],
[data-testid="deploy-button"]  { display: none !important; }

/* ── Sidebar toggle — always visible ──────────────────── */
/* Streamlit's built-in collapsed-sidebar arrow button */
[data-testid="collapsedControl"] {
    display: flex !important;
    visibility: visible !important;
    opacity: 1 !important;
    position: fixed !important;
    top: 50% !important;
    left: 0 !important;
    transform: translateY(-50%) !important;
    z-index: 9999 !important;
    background: rgba(99,179,237,0.15) !important;
    border: 1px solid rgba(99,179,237,0.35) !important;
    border-left: none !important;
    border-radius: 0 10px 10px 0 !important;
    width: 28px !important;
    height: 56px !important;
    align-items: center !important;
    justify-content: center !important;
    cursor: pointer !important;
    backdrop-filter: blur(8px) !important;
    transition: background 0.2s, width 0.2s !important;
}
[data-testid="collapsedControl"]:hover {
    background: rgba(99,179,237,0.3) !important;
    width: 34px !important;
}
[data-testid="collapsedControl"] svg {
    color: #63b3ed !important;
    fill: #63b3ed !important;
    width: 16px !important;
    height: 16px !important;
}

/* App background */
.stApp {
    background: radial-gradient(ellipse at 20% 0%, #0d1b3e 0%, #060d1f 55%, #0a0a14 100%);
    min-height: 100vh;
}

/* ── Hero banner ──────────────────────────────────────── */
.hero-wrap {
    position: relative;
    padding: 2.5rem 2rem 2rem;
    margin-bottom: 1.5rem;
    border-radius: 20px;
    overflow: hidden;
    background: linear-gradient(135deg,
        rgba(14,26,64,0.95) 0%,
        rgba(10,15,35,0.97) 60%,
        rgba(20,8,40,0.95) 100%);
    border: 1px solid rgba(99,179,237,0.18);
    box-shadow:
        0 0 60px rgba(56,128,255,0.08),
        0 4px 40px rgba(0,0,0,0.5),
        inset 0 1px 0 rgba(255,255,255,0.07);
}

/* Animated grid lines */
.hero-wrap::before {
    content: '';
    position: absolute;
    inset: 0;
    background-image:
        linear-gradient(rgba(99,179,237,0.04) 1px, transparent 1px),
        linear-gradient(90deg, rgba(99,179,237,0.04) 1px, transparent 1px);
    background-size: 40px 40px;
    animation: gridMove 20s linear infinite;
}

/* Glowing orbs */
.hero-wrap::after {
    content: '';
    position: absolute;
    top: -60px; left: -60px;
    width: 320px; height: 320px;
    background: radial-gradient(circle, rgba(56,128,255,0.12) 0%, transparent 70%);
    border-radius: 50%;
    pointer-events: none;
}

@keyframes gridMove {
    0%   { transform: translateY(0); }
    100% { transform: translateY(40px); }
}

.hero-content { position: relative; z-index: 2; }

.hero-badge {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    padding: 4px 12px;
    background: rgba(99,179,237,0.12);
    border: 1px solid rgba(99,179,237,0.3);
    border-radius: 100px;
    font-size: 0.72rem;
    font-weight: 600;
    color: #63b3ed;
    letter-spacing: 0.1em;
    text-transform: uppercase;
    margin-bottom: 1rem;
}

.hero-badge .dot {
    width: 6px; height: 6px;
    background: #63b3ed;
    border-radius: 50%;
    animation: pulse-dot 2s ease-in-out infinite;
}

@keyframes pulse-dot {
    0%, 100% { opacity: 1; transform: scale(1); }
    50%       { opacity: 0.4; transform: scale(0.7); }
}

.hero-title {
    font-size: 3rem;
    font-weight: 800;
    line-height: 1.1;
    margin: 0 0 0.75rem;
    background: linear-gradient(135deg, #ffffff 0%, #c3d9ff 40%, #7eb8ff 70%, #a78bfa 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
}

.hero-sub {
    font-size: 1.0rem;
    color: rgba(180,210,255,0.7);
    font-weight: 400;
    max-width: 640px;
    line-height: 1.6;
    margin: 0 0 1.5rem;
}

.hero-pills {
    display: flex;
    flex-wrap: wrap;
    gap: 8px;
}

.pill {
    padding: 5px 14px;
    border-radius: 100px;
    font-size: 0.78rem;
    font-weight: 500;
    letter-spacing: 0.02em;
    border: 1px solid;
}
.pill-blue  { color: #63b3ed; border-color: rgba(99,179,237,0.3);  background: rgba(99,179,237,0.07); }
.pill-green { color: #68d391; border-color: rgba(104,211,145,0.3); background: rgba(104,211,145,0.07); }
.pill-purple{ color: #b794f4; border-color: rgba(183,148,244,0.3); background: rgba(183,148,244,0.07); }
.pill-red   { color: #fc8181; border-color: rgba(252,129,129,0.3); background: rgba(252,129,129,0.07); }
.pill-orange{ color: #f6ad55; border-color: rgba(246,173,85,0.3);  background: rgba(246,173,85,0.07); }

/* ── Glassy metric cards ──────────────────────────────── */
.metric-grid {
    display: grid;
    grid-template-columns: repeat(6, 1fr);
    gap: 12px;
    margin-bottom: 1.5rem;
}

.mcard {
    background: rgba(255,255,255,0.03);
    border: 1px solid rgba(255,255,255,0.08);
    border-radius: 16px;
    padding: 18px 16px 14px;
    position: relative;
    overflow: hidden;
    transition: transform 0.2s ease, box-shadow 0.2s ease;
}
.mcard:hover {
    transform: translateY(-2px);
    box-shadow: 0 8px 32px rgba(0,0,0,0.3);
}

.mcard::before {
    content: '';
    position: absolute;
    top: 0; left: 0; right: 0;
    height: 2px;
    border-radius: 16px 16px 0 0;
}
.mcard-blue::before   { background: linear-gradient(90deg, #4C9BE8, transparent); }
.mcard-orange::before { background: linear-gradient(90deg, #F4A261, transparent); }
.mcard-red::before    { background: linear-gradient(90deg, #E63946, transparent); }
.mcard-crimson::before{ background: linear-gradient(90deg, #9B2335, transparent); }
.mcard-teal::before   { background: linear-gradient(90deg, #2EC4B6, transparent); }
.mcard-purple::before { background: linear-gradient(90deg, #a78bfa, transparent); }

.mcard-danger {
    background: rgba(230,57,70,0.08) !important;
    border-color: rgba(230,57,70,0.25) !important;
    box-shadow: 0 0 20px rgba(230,57,70,0.08);
}
.mcard-safe {
    background: rgba(46,196,182,0.06) !important;
    border-color: rgba(46,196,182,0.2) !important;
}

.mcard-label {
    font-size: 0.7rem;
    font-weight: 600;
    letter-spacing: 0.08em;
    text-transform: uppercase;
    color: rgba(180,200,255,0.55);
    margin-bottom: 8px;
}

.mcard-value {
    font-size: 1.65rem;
    font-weight: 700;
    color: #fff;
    font-family: 'JetBrains Mono', monospace;
    line-height: 1;
    margin-bottom: 6px;
}

.mcard-delta {
    font-size: 0.72rem;
    font-weight: 500;
    padding: 2px 8px;
    border-radius: 100px;
    display: inline-block;
}
.delta-danger  { background: rgba(230,57,70,0.2);  color: #fc8181; }
.delta-safe    { background: rgba(46,196,182,0.15); color: #68d391; }
.delta-neutral { background: rgba(180,200,255,0.1); color: rgba(180,200,255,0.6); }

/* ── Section header ───────────────────────────────────── */
.section-hdr {
    display: flex;
    align-items: center;
    gap: 10px;
    margin: 1.5rem 0 1rem;
}
.section-hdr-line {
    flex: 1;
    height: 1px;
    background: linear-gradient(90deg, rgba(99,179,237,0.3), transparent);
}
.section-hdr-text {
    font-size: 0.78rem;
    font-weight: 600;
    letter-spacing: 0.12em;
    text-transform: uppercase;
    color: rgba(99,179,237,0.7);
    white-space: nowrap;
}

/* ── Chart container ──────────────────────────────────── */
.chart-wrap {
    background: rgba(255,255,255,0.02);
    border: 1px solid rgba(255,255,255,0.07);
    border-radius: 20px;
    padding: 8px;
    box-shadow: 0 4px 40px rgba(0,0,0,0.3);
}

/* ── Tabs styling ─────────────────────────────────────── */
[data-testid="stTabs"] button {
    font-family: 'Inter', sans-serif !important;
    font-weight: 500 !important;
    font-size: 0.85rem !important;
    color: rgba(180,200,255,0.6) !important;
    border-radius: 8px 8px 0 0 !important;
    padding: 8px 18px !important;
    transition: color 0.2s !important;
}
[data-testid="stTabs"] button[aria-selected="true"] {
    color: #63b3ed !important;
    background: rgba(99,179,237,0.08) !important;
    border-bottom: 2px solid #63b3ed !important;
}

/* ── Sidebar ──────────────────────────────────────────── */
section[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #0a0f22 0%, #060d1f 100%) !important;
    border-right: 1px solid rgba(99,179,237,0.1) !important;
}

section[data-testid="stSidebar"] .stMarkdown h2,
section[data-testid="stSidebar"] h2 {
    color: #63b3ed !important;
    font-size: 0.72rem !important;
    font-weight: 700 !important;
    letter-spacing: 0.12em !important;
    text-transform: uppercase !important;
    margin-top: 1.2rem !important;
}

section[data-testid="stSidebar"] .stSlider > label,
section[data-testid="stSidebar"] .stNumberInput > label,
section[data-testid="stSidebar"] .stSelectbox > label {
    font-size: 0.82rem !important;
    color: rgba(180,210,255,0.8) !important;
    font-weight: 500 !important;
}

/* Sidebar logo */
.sidebar-logo {
    text-align: center;
    padding: 1.2rem 0 0.5rem;
    margin-bottom: 0.5rem;
}
.sidebar-logo .logo-icon {
    font-size: 2.8rem;
    display: block;
    filter: drop-shadow(0 0 12px rgba(99,179,237,0.5));
}
.sidebar-logo .logo-text {
    font-size: 1.1rem;
    font-weight: 700;
    color: #fff;
    letter-spacing: 0.02em;
}
.sidebar-logo .logo-version {
    font-size: 0.68rem;
    color: rgba(99,179,237,0.5);
    letter-spacing: 0.1em;
}

/* ── Home Page Embedded Sidebar Panel ──────────────────── */
.home-ctrl-panel {
    background: linear-gradient(180deg, rgba(14,23,48,0.92) 0%, rgba(8,13,30,0.95) 100%);
    border: 1px solid rgba(99,179,237,0.22);
    border-radius: 20px;
    padding: 1.3rem 1.2rem 1.6rem;
    box-shadow: 0 8px 48px rgba(0,0,0,0.45);
    margin-bottom: 1.5rem;
}
.home-ctrl-title {
    font-size: 1.05rem;
    font-weight: 800;
    color: #fff;
    margin-bottom: 0.2rem;
    display: flex;
    align-items: center;
    gap: 8px;
}
.home-ctrl-sub {
    font-size: 0.75rem;
    color: rgba(180,210,255,0.6);
    margin-bottom: 0.8rem;
}

/* Divider */
.sdivider {
    height: 1px;
    background: linear-gradient(90deg, transparent, rgba(99,179,237,0.15), transparent);
    margin: 0.8rem 0;
}

/* ── Comparison cards ─────────────────────────────────── */
.cmp-header {
    display: flex;
    align-items: center;
    gap: 10px;
    padding: 14px 18px;
    border-radius: 12px;
    margin-bottom: 1rem;
    font-weight: 600;
    font-size: 0.95rem;
}
.cmp-baseline  { background: rgba(230,57,70,0.1);  border: 1px solid rgba(230,57,70,0.25);  color: #fc8181; }
.cmp-scenario  { background: rgba(46,196,182,0.08); border: 1px solid rgba(46,196,182,0.22); color: #68d391; }

/* ── Lives saved banner ───────────────────────────────── */
.lives-banner {
    margin-top: 1.5rem;
    padding: 20px 24px;
    border-radius: 16px;
    background: linear-gradient(135deg, rgba(46,196,182,0.1) 0%, rgba(104,211,145,0.08) 100%);
    border: 1px solid rgba(46,196,182,0.25);
    font-size: 1rem;
    color: #68d391;
    font-weight: 500;
    text-align: center;
}
.lives-banner strong { font-size: 1.4rem; color: #fff; }

.lives-banner-warn {
    background: linear-gradient(135deg, rgba(230,57,70,0.1) 0%, rgba(252,129,129,0.06) 100%);
    border-color: rgba(230,57,70,0.25);
    color: #fc8181;
}

/* ── Expander ─────────────────────────────────────────── */
[data-testid="stExpander"] {
    background: rgba(255,255,255,0.02) !important;
    border: 1px solid rgba(255,255,255,0.07) !important;
    border-radius: 12px !important;
}

/* ── Streamlit overrides ──────────────────────────────── */
[data-testid="metric-container"] { display: none; }  /* hide native metrics */

.stDownloadButton > button {
    background: linear-gradient(135deg, #1a3a6e 0%, #0f2347 100%) !important;
    border: 1px solid rgba(99,179,237,0.3) !important;
    color: #63b3ed !important;
    border-radius: 10px !important;
    font-weight: 600 !important;
    font-family: 'Inter', sans-serif !important;
    transition: all 0.2s !important;
}
.stDownloadButton > button:hover {
    background: linear-gradient(135deg, #1e4a8a 0%, #132d5c 100%) !important;
    box-shadow: 0 0 20px rgba(99,179,237,0.2) !important;
}
</style>

<script>
// Create a floating sidebar toggle button injected into document.body
(function injectSidebarBtn() {
    function create() {
        if (document.getElementById('episim-sb-toggle')) return;
        var btn = document.createElement('button');
        btn.id = 'episim-sb-toggle';
        btn.title = 'Toggle sidebar';
        btn.innerHTML = '&#9776;';
        btn.setAttribute('aria-label', 'Toggle sidebar');
        Object.assign(btn.style, {
            position: 'fixed', top: '12px', left: '12px',
            zIndex: '999999',
            width: '38px', height: '38px',
            borderRadius: '10px',
            border: '1px solid rgba(99,179,237,0.4)',
            background: 'rgba(6,12,30,0.88)',
            backdropFilter: 'blur(14px)',
            color: '#63b3ed',
            fontSize: '1.15rem',
            cursor: 'pointer',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            transition: 'background 0.2s, box-shadow 0.2s',
            boxShadow: '0 2px 14px rgba(0,0,0,0.45)',
            fontFamily: 'sans-serif',
        });
        btn.onmouseenter = function() {
            btn.style.background = 'rgba(99,179,237,0.2)';
            btn.style.boxShadow = '0 4px 22px rgba(99,179,237,0.25)';
        };
        btn.onmouseleave = function() {
            btn.style.background = 'rgba(6,12,30,0.88)';
            btn.style.boxShadow = '0 2px 14px rgba(0,0,0,0.45)';
        };
        btn.onclick = function() {
            // 1. Try Streamlit's native collapsed-control button
            var native =
                document.querySelector('[data-testid="collapsedControl"]') ||
                document.querySelector('button[aria-label="Open sidebar"]') ||
                document.querySelector('button[aria-label="Close sidebar"]');
            if (native) { native.click(); return; }
            // 2. Direct toggle fallback
            var sb = document.querySelector('section[data-testid="stSidebar"]');
            if (sb) {
                sb.style.display = (sb.style.display === 'none') ? '' : 'none';
            }
        };
        document.body.appendChild(btn);
    }
    // Run on load and after Streamlit re-renders
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', create);
    } else {
        create();
    }
    new MutationObserver(create).observe(document.body, {childList: true, subtree: false});
})();
</script>
""", unsafe_allow_html=True)

# Sidebar toggle button — uses components.html() so JS actually executes
components.html("""
<script>
(function() {
    // Access the parent Streamlit document
    var doc = window.parent.document;

    function injectBtn() {
        if (doc.getElementById('episim-sb-toggle')) return;
        var btn = doc.createElement('button');
        btn.id = 'episim-sb-toggle';
        btn.innerHTML = '&#9776;';
        btn.title = 'Toggle Sidebar';
        btn.setAttribute('aria-label', 'Toggle sidebar');
        Object.assign(btn.style, {
            position: 'fixed',
            top: '50%',
            left: '0px',
            transform: 'translateY(-50%)',
            zIndex: '9999999',
            width: '30px',
            height: '60px',
            borderRadius: '0 12px 12px 0',
            border: '1px solid rgba(99,179,237,0.45)',
            borderLeft: 'none',
            background: 'rgba(6,12,30,0.92)',
            backdropFilter: 'blur(14px)',
            color: '#63b3ed',
            fontSize: '1.1rem',
            cursor: 'pointer',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            transition: 'width 0.2s, background 0.2s, box-shadow 0.2s',
            boxShadow: '3px 0 18px rgba(0,0,0,0.5)',
            fontFamily: 'sans-serif',
            lineHeight: '1',
        });
        btn.onmouseenter = function() {
            btn.style.width = '36px';
            btn.style.background = 'rgba(99,179,237,0.22)';
            btn.style.boxShadow = '4px 0 24px rgba(99,179,237,0.25)';
        };
        btn.onmouseleave = function() {
            btn.style.width = '30px';
            btn.style.background = 'rgba(6,12,30,0.92)';
            btn.style.boxShadow = '3px 0 18px rgba(0,0,0,0.5)';
        };
        btn.onclick = function() {
            var native =
                doc.querySelector('[data-testid="collapsedControl"]') ||
                doc.querySelector('button[aria-label="Open sidebar"]') ||
                doc.querySelector('button[aria-label="Close sidebar"]');
            if (native) { native.click(); return; }
            var sb = doc.querySelector('section[data-testid="stSidebar"]');
            if (sb) sb.style.display = (sb.style.display === 'none') ? '' : 'none';
        };
        doc.body.appendChild(btn);
    }

    // Run immediately and re-check on DOM changes
    injectBtn();
    new MutationObserver(injectBtn).observe(doc.body, {childList: true, subtree: false});
})();
</script>
""", height=0)

# ---------------------------------------------------------------------------
# Scenario presets
# ---------------------------------------------------------------------------
PRESETS: dict[str, dict] = {
    "Custom": {},
    "COVID-19 (baseline)": {
        "beta": 0.30, "sigma": 0.20, "gamma": 0.07, "mu": 0.005,
        "hospitalization_rate": 0.06, "days": 180,
    },
    "Influenza": {
        "beta": 0.25, "sigma": 0.50, "gamma": 0.20, "mu": 0.001,
        "hospitalization_rate": 0.02, "days": 90,
    },
    "Ebola-like": {
        "beta": 0.18, "sigma": 0.12, "gamma": 0.07, "mu": 0.04,
        "hospitalization_rate": 0.80, "days": 120,
    },
    "Measles (unvaccinated)": {
        "beta": 0.90, "sigma": 0.25, "gamma": 0.14, "mu": 0.0005,
        "hospitalization_rate": 0.01, "days": 120,
    },
}

# ---------------------------------------------------------------------------
# Sidebar (Model Documentation & Equations)
# ---------------------------------------------------------------------------
with st.sidebar:
    st.markdown("""
    <div class="sidebar-logo">
        <span class="logo-icon">🦠</span>
        <div class="logo-text">EpiSim</div>
        <div class="logo-version">EPIDEMIC PLATFORM · v2.1</div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown('<div class="sdivider"></div>', unsafe_allow_html=True)
    st.markdown(r"""
    ### 📖 Compartmental Models
    EpiSim simulates multi-compartment differential equation models:

    - **SEIRD**: Full dynamics with Incubation ($E$) and Disease Fatality ($D$).
    - **SEIR**: Classical incubation model assuming zero fatalities ($\mu=0$).
    - **SIR**: Kermack-McKendrick standard epidemic ($S \to I \to R$).
    - **SIS**: Endemic spread without permanent immunity ($S \to I \to S$).

    ---
    ### 📐 Differential Equations (SEIRD)
    $$\frac{dS}{dt} = -\frac{\beta S I}{N}$$
    $$\frac{dE}{dt} = \frac{\beta S I}{N} - \sigma E$$
    $$\frac{dI}{dt} = \sigma E - (\gamma + \mu) I$$
    $$\frac{dR}{dt} = \gamma I$$
    $$\frac{dD}{dt} = \mu I$$
    """)

# ---------------------------------------------------------------------------
# Hero banner
# ---------------------------------------------------------------------------
st.markdown("""
<div class="hero-wrap">
  <div class="hero-content">
    <div class="hero-badge">
      <span class="dot"></span>
      Live Simulation Active
    </div>
    <h1 class="hero-title">EpiSim — Disease Spread<br>Simulation Dashboard</h1>
    <p class="hero-sub">
      An interactive compartmental epidemic modelling platform. Explore how transmission,
      vaccination, social distancing, and healthcare capacity shape the course of an outbreak
      — in real time.
    </p>
    <div class="hero-pills">
      <span class="pill pill-blue">🧬 Multi-Model (SEIRD/SEIR/SIR/SIS)</span>
      <span class="pill pill-green">💉 Vaccination</span>
      <span class="pill pill-purple">📊 Monte Carlo CI</span>
      <span class="pill pill-red">🏥 ICU Capacity</span>
      <span class="pill pill-orange">⚖️ Scenario Comparison</span>
    </div>
  </div>
</div>
""", unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# Home Page Layout: Always-Visible Left Control Panel + Right Dashboard
# ---------------------------------------------------------------------------
col_ctrl, col_main = st.columns([1.1, 2.9], gap="large")

with col_ctrl:
    st.markdown("""
    <div class="home-ctrl-panel">
        <div class="home-ctrl-title">🎛️ SIMULATION CONTROLS</div>
        <div class="home-ctrl-sub">Custom simulation with different model</div>
    </div>
    """, unsafe_allow_html=True)

    model_type = st.selectbox(
        "Epidemic Model Architecture",
        [
            "SEIRD (COVID / Ebola dynamics)",
            "SEIR (Classical Incubation)",
            "SIR (Simple Epidemic)",
            "SIS (No Permanent Immunity)",
        ],
        help="Select the mathematical compartmental structure to simulate"
    )

    st.markdown('<div class="sdivider"></div>', unsafe_allow_html=True)
    preset = st.selectbox("Disease Preset", list(PRESETS.keys()))
    p = PRESETS[preset]

    with st.expander("👥 Population Settings", expanded=True):
        population       = st.slider("Population size N",    500, 200_000, 50_000, 500)
        initial_infected = st.slider("Initial infected I₀",  1, 500, 10, 1)

    with st.expander("🦠 Epidemiological Rates", expanded=True):
        beta  = st.slider("Transmission rate β", 0.05, 1.50, p.get("beta",  0.30), 0.01,
                          help="Higher β → faster spread")
        sigma = st.slider("Incubation rate σ",   0.05, 1.00, p.get("sigma", 0.20), 0.01,
                          help="1/σ = mean incubation days")
        gamma = st.slider("Recovery rate γ",     0.02, 0.50, p.get("gamma", 0.10), 0.01,
                          help="1/γ = mean infectious days")
        mu    = st.slider("Case fatality rate μ", 0.000, 0.10, p.get("mu", 0.005), 0.001,
                          help="Fraction of infectious-days ending in death")

    with st.expander("🛡️ Public Health Interventions", expanded=False):
        vaccine_coverage     = st.slider("Vaccination coverage",  0.00, 0.95, 0.0, 0.05,
                                         help="Fraction immunised at day 0")
        distancing_reduction = st.slider("Distancing reduction",  0.00, 0.90, 0.0, 0.05,
                                         help="Fractional reduction in β")

    with st.expander("🏥 Healthcare & ICU Capacity", expanded=False):
        hospitalization_rate = st.slider("Hospitalisation rate", 0.00, 1.00,
                                         p.get("hospitalization_rate", 0.05), 0.01,
                                         help="Fraction of infectious needing a hospital bed")
        icu_capacity         = st.slider("ICU beds (per 100k)",  10, 2000, 300, 10,
                                         help="ICU beds per 100,000 people")
        icu_beds_abs = int(icu_capacity * population / 100_000)

    with st.expander("⏱️ Simulation & Monte Carlo", expanded=False):
        days             = st.slider("Days to simulate",        30, 730, p.get("days", 150), 10)
        monte_carlo_runs = st.number_input("Monte Carlo runs (0 = off)",
                                           min_value=0, max_value=500, value=0, step=10)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
COLOURS = {
    "Susceptible": "#4C9BE8",
    "Exposed":     "#F6AD55",
    "Infectious":  "#FC8181",
    "Recovered":   "#68D391",
    "Deaths":      "#C53030",
    "Hospitalised":"#F6AD55",
}

FILL_COLOURS = {
    "Susceptible": "rgba(76,155,232,0.07)",
    "Exposed":     "rgba(246,173,85,0.07)",
    "Infectious":  "rgba(252,129,129,0.10)",
    "Recovered":   "rgba(104,211,145,0.08)",
    "Deaths":      "rgba(197,48,48,0.10)",
}


def build_df(times: np.ndarray, states: np.ndarray) -> pd.DataFrame:
    n_cols = states.shape[1]
    S = states[:, 0]
    E = states[:, 1] if n_cols >= 4 else np.zeros_like(S)
    I = states[:, 2] if n_cols >= 4 else states[:, 1]
    R = states[:, 3] if n_cols >= 4 else (states[:, 2] if n_cols == 3 else np.zeros_like(S))
    D = states[:, 4] if n_cols >= 5 else np.zeros_like(S)
    return pd.DataFrame({
        "Day": times, "Susceptible": S, "Exposed": E,
        "Infectious": I, "Recovered": R, "Deaths": D,
        "Hospitalised": I * hospitalization_rate,
    })


def build_fig(
    df: pd.DataFrame,
    icu_line: int,
    title: str = "",
    mc_summary: dict | None = None,
    model_type: str = "SEIRD",
) -> go.Figure:
    fig = go.Figure()

    model_upper = model_type.upper().split(" ")[0]
    if model_upper == "SEIR":
        active_cols = ["Susceptible", "Exposed", "Infectious", "Recovered"]
    elif model_upper == "SIR":
        active_cols = ["Susceptible", "Infectious", "Recovered"]
    elif model_upper == "SIS":
        active_cols = ["Susceptible", "Infectious"]
    else:
        active_cols = ["Susceptible", "Exposed", "Infectious", "Recovered", "Deaths"]

    for col in active_cols:
        fig.add_trace(go.Scatter(
            x=df["Day"], y=df[col],
            name=col,
            mode="lines",
            fill="tozeroy",
            fillcolor=FILL_COLOURS[col],
            line=dict(color=COLOURS[col], width=2.5),
            hovertemplate=f"<b>{col}</b>: %{{y:,.0f}}<br>Day %{{x:.0f}}<extra></extra>",
        ))

    # Hospitalised (dashed, no fill)
    fig.add_trace(go.Scatter(
        x=df["Day"], y=df["Hospitalised"],
        name="Hospitalised",
        mode="lines",
        line=dict(color="#F6AD55", width=1.5, dash="dot"),
        hovertemplate="<b>Hospitalised</b>: %{y:,.0f}<br>Day %{x:.0f}<extra></extra>",
    ))

    # ICU capacity
    fig.add_hline(
        y=icu_line,
        line_color="rgba(252,129,129,0.6)",
        line_dash="dash",
        line_width=1.5,
        annotation_text=f"⚠ ICU capacity ({icu_line:,})",
        annotation_position="top right",
        annotation_font_color="rgba(252,129,129,0.85)",
        annotation_font_size=11,
    )

    # Monte Carlo band
    if mc_summary is not None:
        t = df["Day"].values
        fig.add_trace(go.Scatter(x=t, y=mc_summary["upper"],
                                 line=dict(color="rgba(252,129,129,0)"), showlegend=False))
        fig.add_trace(go.Scatter(x=t, y=mc_summary["lower"],
                                 fill="tonexty", fillcolor="rgba(252,129,129,0.12)",
                                 line=dict(color="rgba(252,129,129,0)"), name="95% CI"))
        fig.add_trace(go.Scatter(x=t, y=mc_summary["mean"],
                                 line=dict(color="#FC8181", dash="dash", width=1.2),
                                 name="Mean Infectious (MC)"))

    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Inter", color="rgba(180,210,255,0.75)"),
        title=dict(text=title, font=dict(size=15, color="rgba(180,210,255,0.8)")) if title else None,
        height=500,
        margin=dict(l=50, r=30, t=60 if title else 20, b=50),
        legend=dict(
            orientation="h",
            yanchor="bottom", y=1.01,
            xanchor="right",  x=1,
            font=dict(size=11),
            bgcolor="rgba(0,0,0,0)",
        ),
        hovermode="x unified",
        hoverlabel=dict(
            bgcolor="rgba(10,15,35,0.95)",
            bordercolor="rgba(99,179,237,0.3)",
            font_family="Inter",
            font_size=12,
        ),
        xaxis=dict(
            title="Day", showgrid=True,
            gridcolor="rgba(255,255,255,0.04)",
            zeroline=False,
            tickfont=dict(size=11),
        ),
        yaxis=dict(
            title="People", showgrid=True,
            gridcolor="rgba(255,255,255,0.04)",
            zeroline=False,
            tickfont=dict(size=11),
        ),
    )
    return fig


def build_comparison_fig(
    bl_df: pd.DataFrame,
    sc_df: pd.DataFrame,
    icu_line: int,
    model_type: str = "SEIRD",
) -> go.Figure:
    fig = go.Figure()

    # 1. Baseline Infectious Curve (Dashed red/coral)
    fig.add_trace(go.Scatter(
        x=bl_df["Day"], y=bl_df["Infectious"],
        name="Baseline Infections (No Intervention)",
        mode="lines",
        line=dict(color="#FC8181", width=2.5, dash="dash"),
        hovertemplate="<b>Baseline Infected</b>: %{y:,.0f}<br>Day %{x:.0f}<extra></extra>",
    ))

    # 2. Intervention Infectious Curve (Solid glowing emerald/green with fill)
    fig.add_trace(go.Scatter(
        x=sc_df["Day"], y=sc_df["Infectious"],
        name="Intervention Infections (Flattened Curve)",
        mode="lines",
        fill="tozeroy",
        fillcolor="rgba(104,211,145,0.12)",
        line=dict(color="#68D391", width=3.0),
        hovertemplate="<b>Intervention Infected</b>: %{y:,.0f}<br>Day %{x:.0f}<extra></extra>",
    ))

    # 3. Hospitalisation comparison
    fig.add_trace(go.Scatter(
        x=sc_df["Day"], y=sc_df["Hospitalised"],
        name="Intervention Hospitalised",
        mode="lines",
        line=dict(color="#F6AD55", width=1.8, dash="dot"),
        hovertemplate="<b>Intervention Hosp.</b>: %{y:,.0f}<br>Day %{x:.0f}<extra></extra>",
    ))

    # 4. ICU capacity threshold
    fig.add_hline(
        y=icu_line,
        line_color="rgba(252,129,129,0.65)",
        line_dash="dash",
        line_width=1.5,
        annotation_text=f"⚠ ICU Bed Capacity ({icu_line:,})",
        annotation_position="top right",
        annotation_font_color="rgba(252,129,129,0.9)",
        annotation_font_size=11,
    )

    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Inter", color="rgba(180,210,255,0.75)"),
        height=450,
        margin=dict(l=50, r=30, t=30, b=50),
        legend=dict(
            orientation="h",
            yanchor="bottom", y=1.02,
            xanchor="right",  x=1,
            font=dict(size=11),
            bgcolor="rgba(0,0,0,0)",
        ),
        hovermode="x unified",
        hoverlabel=dict(
            bgcolor="rgba(10,15,35,0.95)",
            bordercolor="rgba(99,179,237,0.3)",
            font_family="Inter",
            font_size=12,
        ),
        xaxis=dict(
            title="Day", showgrid=True,
            gridcolor="rgba(255,255,255,0.04)",
            zeroline=False,
            tickfont=dict(size=11),
        ),
        yaxis=dict(
            title="Active Infections / Hospitalised", showgrid=True,
            gridcolor="rgba(255,255,255,0.04)",
            zeroline=False,
            tickfont=dict(size=11),
        ),
    )
    return fig


def run_mc(n_runs: int) -> dict | None:
    if n_runs <= 0:
        return None
    all_inf = []
    for _ in range(n_runs):
        def noise(v): return max(0, np.random.normal(v, 0.05 * v))
        _, s = simulate_seird(
            population=population,
            beta=noise(beta) * (1 - distancing_reduction),
            sigma=noise(sigma), gamma=noise(gamma), mu=noise(mu),
            initial_infected=initial_infected, days=days,
        )
        inf_idx = 2 if s.shape[1] >= 4 else 1
        all_inf.append(s[:, inf_idx])
    arr = np.vstack(all_inf)
    return {
        "mean":  arr.mean(axis=0),
        "lower": np.percentile(arr, 2.5, axis=0),
        "upper": np.percentile(arr, 97.5, axis=0),
    }


def metric_card(label: str, value: str, delta: str,
                card_cls: str, delta_cls: str) -> str:
    return f"""
    <div class="mcard {card_cls}">
        <div class="mcard-label">{label}</div>
        <div class="mcard-value">{value}</div>
        <span class="mcard-delta {delta_cls}">{delta}</span>
    </div>"""


# ---------------------------------------------------------------------------
# Main simulation calculation
# ---------------------------------------------------------------------------
result = run_scenario(
    population=population, beta=beta, sigma=sigma, gamma=gamma, mu=mu,
    initial_infected=initial_infected, days=days,
    vaccine_coverage=vaccine_coverage, distancing_reduction=distancing_reduction,
    hospitalization_rate=hospitalization_rate,
    model_type=model_type,
)

times  = result["times"]
states = result["states"]
df     = build_df(times, states)

r0           = result["r0"]
peak_inf     = result["peak_infected"]
peak_day     = result["peak_day"]
final_rec    = result["final_recovered"]
total_dth    = result["total_deaths"]
peak_hosp    = result["peak_hospitalized"]
attack_rate  = 100 * (final_rec + total_dth) / population
icu_breached = peak_hosp > icu_beds_abs


with col_main:
    # ---------------------------------------------------------------------------
    # Tabs
    # ---------------------------------------------------------------------------
    tab_sim, tab_compare, tab_data = st.tabs(["📈  Simulation", "⚖️  Comparison", "📋  Data & Export"])

    # ── Tab 1: Simulation ──────────────────────────────────────────────────────
    with tab_sim:

        # Metric cards
        r0_danger    = r0 > 1
        icu_danger   = icu_breached

        cards_html = '<div class="metric-grid">'
        cards_html += metric_card(
            "R₀ Effective", f"{r0:.2f}",
            "🔴 Epidemic grows" if r0_danger else "🟢 Dying out",
            "mcard mcard-blue" + (" mcard-danger" if r0_danger else " mcard-safe"),
            "delta-danger" if r0_danger else "delta-safe",
        )
        cards_html += metric_card(
            "Peak Infected", f"{int(peak_inf):,}",
            f"Day {peak_day}",
            "mcard mcard-red",
            "delta-neutral",
        )
        cards_html += metric_card(
            "Peak Hospitalised", f"{int(peak_hosp):,}",
            "🔴 ICU EXCEEDED" if icu_danger else "🟢 Within capacity",
            "mcard mcard-orange" + (" mcard-danger" if icu_danger else " mcard-safe"),
            "delta-danger" if icu_danger else "delta-safe",
        )
        cards_html += metric_card(
            "Total Deaths", f"{int(total_dth):,}",
            f"CFR {100*mu/(mu+gamma):.1f}%",
            "mcard mcard-crimson",
            "delta-danger" if total_dth > 0 else "delta-neutral",
        )
        cards_html += metric_card(
            "Final Recovered", f"{int(final_rec):,}",
            f"{100*final_rec/population:.1f}% of pop.",
            "mcard mcard-teal mcard-safe",
            "delta-safe",
        )
        cards_html += metric_card(
            "Attack Rate", f"{attack_rate:.1f}%",
            "% of population infected",
            "mcard mcard-purple",
            "delta-neutral",
        )
        cards_html += "</div>"
        st.markdown(cards_html, unsafe_allow_html=True)

        # Section header
        st.markdown(f"""
        <div class="section-hdr">
          <span class="section-hdr-text">📈 {model_type.split(' ')[0]} Epidemic Curve</span>
          <div class="section-hdr-line"></div>
        </div>
        """, unsafe_allow_html=True)

        # Monte Carlo
        mc = run_mc(int(monte_carlo_runs))

        # Chart
        st.markdown('<div class="chart-wrap">', unsafe_allow_html=True)
        st.plotly_chart(build_fig(df, icu_beds_abs, mc_summary=mc, model_type=model_type), use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)

        # Parameters expander
        with st.expander("🔬 Scenario Parameters"):
            pcols = st.columns(5)
            params = {
                "Model": model_type.split(' ')[0],
                "Population": f"{population:,}",
                "Initial infected": str(initial_infected),
                "β (transmission)": str(beta),
                "σ (incubation)": str(sigma),
                "γ (recovery)": str(gamma),
                "μ (fatality)": str(mu),
                "Vaccination": f"{vaccine_coverage:.0%}",
                "Distancing": f"{distancing_reduction:.0%}",
                "ICU beds": f"{icu_beds_abs:,}",
            }
            for i, (k, v) in enumerate(params.items()):
                pcols[i % 5].markdown(
                    f'<div style="padding:8px 0;border-bottom:1px solid rgba(255,255,255,0.05)">'
                    f'<span style="color:rgba(180,210,255,0.5);font-size:0.72rem;text-transform:uppercase;letter-spacing:0.06em">{k}</span><br>'
                    f'<span style="color:#fff;font-weight:600;font-size:0.95rem">{v}</span></div>',
                    unsafe_allow_html=True,
                )

    # ── Tab 2: Comparison ──────────────────────────────────────────────────────
    with tab_compare:

        st.markdown("""
        <div class="section-hdr" style="margin-top:0.5rem">
          <span class="section-hdr-text">⚖️ Baseline vs. Intervention</span>
          <div class="section-hdr-line"></div>
        </div>
        <p style="color:rgba(180,210,255,0.55);font-size:0.85rem;margin-bottom:1rem">
          Adjust vaccination or distancing sliders in the sidebar, then compare outcomes side-by-side.
        </p>
        """, unsafe_allow_html=True)

        baseline = run_scenario(
            population=population, beta=beta, sigma=sigma, gamma=gamma, mu=mu,
            initial_infected=initial_infected, days=days,
            vaccine_coverage=0.0, distancing_reduction=0.0,
            hospitalization_rate=hospitalization_rate,
            model_type=model_type,
        )
        bl_df = build_df(baseline["times"], baseline["states"])

        left, right = st.columns(2)

        with left:
            st.markdown('<div class="cmp-header cmp-baseline">🔴 &nbsp; Baseline (no intervention)</div>',
                        unsafe_allow_html=True)
            bm = baseline
            bl_cards = '<div style="display:grid;grid-template-columns:1fr 1fr 1fr;gap:10px;margin-bottom:1rem">'
            bl_cards += metric_card("R₀", f"{bm['r0']:.2f}", "No intervention", "mcard mcard-blue mcard-danger", "delta-danger")
            bl_cards += metric_card("Peak Infected", f"{int(bm['peak_infected']):,}", f"Day {bm['peak_day']}", "mcard mcard-red", "delta-neutral")
            bl_cards += metric_card("Total Deaths", f"{int(bm['total_deaths']):,}", "Baseline", "mcard mcard-crimson", "delta-danger")
            bl_cards += "</div>"
            st.markdown(bl_cards, unsafe_allow_html=True)
            st.markdown('<div class="chart-wrap">', unsafe_allow_html=True)
            st.plotly_chart(build_fig(bl_df, icu_beds_abs, title="No Intervention", model_type=model_type),
                            use_container_width=True)
            st.markdown('</div>', unsafe_allow_html=True)

        with right:
            st.markdown('<div class="cmp-header cmp-scenario">🟢 &nbsp; With Intervention</div>',
                        unsafe_allow_html=True)
            r0_delta_val  = r0 - bm['r0']
            inf_delta_val = int(peak_inf - bm['peak_infected'])
            dth_delta_val = int(total_dth - bm['total_deaths'])

            sc_cards = '<div style="display:grid;grid-template-columns:1fr 1fr 1fr;gap:10px;margin-bottom:1rem">'
            sc_cards += metric_card("R₀", f"{r0:.2f}",
                                    f"{'▼' if r0_delta_val < 0 else '▲'} {abs(r0_delta_val):.2f}",
                                    "mcard mcard-blue" + (" mcard-safe" if r0_delta_val < 0 else " mcard-danger"),
                                    "delta-safe" if r0_delta_val < 0 else "delta-danger")
            sc_cards += metric_card("Peak Infected", f"{int(peak_inf):,}",
                                    f"{'▼' if inf_delta_val < 0 else '▲'} {abs(inf_delta_val):,}",
                                    "mcard mcard-red" + (" mcard-safe" if inf_delta_val < 0 else ""),
                                    "delta-safe" if inf_delta_val < 0 else "delta-danger")
            sc_cards += metric_card("Total Deaths", f"{int(total_dth):,}",
                                f"{'▼' if dth_delta_val < 0 else '▲'} {abs(dth_delta_val):,}",
                                "mcard mcard-crimson" + (" mcard-safe" if dth_delta_val < 0 else " mcard-danger"),
                                "delta-safe" if dth_delta_val < 0 else "delta-danger")
            sc_cards += "</div>"
            st.markdown(sc_cards, unsafe_allow_html=True)
            st.markdown('<div class="chart-wrap">', unsafe_allow_html=True)
            st.plotly_chart(build_fig(df, icu_beds_abs, title="With Intervention", model_type=model_type),
                            use_container_width=True)
            st.markdown('</div>', unsafe_allow_html=True)

        # Summary banner
        lives_saved = int(bm["total_deaths"] - total_dth)
        infections_averted = int(bm["peak_infected"] - peak_inf)
        if lives_saved > 0:
            st.markdown(f"""
            <div class="lives-banner">
                ✅ Intervention saves an estimated <strong>{lives_saved:,} lives</strong>
                and averts <strong>{infections_averted:,}</strong> peak infections.
            </div>""", unsafe_allow_html=True)
        elif lives_saved < 0:
            st.markdown(f"""
            <div class="lives-banner lives-banner-warn">
                ⚠️ Current intervention parameters appear to <strong>increase deaths by {abs(lives_saved):,}</strong>.
                Review vaccination and distancing values.
            </div>""", unsafe_allow_html=True)
        else:
            st.markdown("""
            <div class="lives-banner" style="color:rgba(180,210,255,0.6);border-color:rgba(180,210,255,0.15);background:rgba(180,210,255,0.04)">
                ℹ️ No difference in outcomes with current settings — try adjusting vaccination or distancing.
            </div>""", unsafe_allow_html=True)

    # ── Tab 3: Data & Export ───────────────────────────────────────────────────
    with tab_data:

        st.markdown("""
        <div class="section-hdr" style="margin-top:0.5rem">
          <span class="section-hdr-text">📋 Raw Simulation Data</span>
          <div class="section-hdr-line"></div>
        </div>
        """, unsafe_allow_html=True)

        st.dataframe(
            df.style.format({c: "{:,.1f}" for c in df.columns if c != "Day"}),
            use_container_width=True,
            height=400,
        )

        csv_bytes = df.to_csv(index=False).encode("utf-8")
        st.download_button(
            label="⬇️  Download CSV",
            data=csv_bytes,
            file_name="episim_results.csv",
            mime="text/csv",
        )
