"""
ui/app.py — EpiSim: Academic-Grade Epidemic Simulation Dashboard.

Professor-level edition featuring:
  • Animated day-by-day epidemic progression (Plotly frames)
  • Daily incidence (new cases) bar chart
  • Time-varying effective reproduction number Rt(t)
  • Phase-plane trajectory (S vs I — classic epidemiological portrait)
  • Sensitivity / tornado analysis (β, σ, γ, μ impact on peak)
  • Herd immunity threshold visualization
  • Comprehensive academic metrics (doubling time, serial interval, CFR, HIT)
  • Monte Carlo uncertainty bands
  • Scenario comparison with statistical breakdown
  • Full CSV export with all derived quantities
"""
from __future__ import annotations

import importlib
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import streamlit as st
import streamlit.components.v1 as components

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import episim
importlib.reload(episim)
from episim import (  # noqa: E402
    run_scenario,
    simulate_seird,
    compute_daily_incidence,
    compute_rt,
    herd_immunity_threshold,
    fit_parameters,
)

# ---------------------------------------------------------------------------
# Page config
# ---------------------------------------------------------------------------
st.set_page_config(
    page_title="EpiSim — Epidemic Simulation Platform",
    page_icon="🦠",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ---------------------------------------------------------------------------
# PREMIUM CSS
# ---------------------------------------------------------------------------
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&family=JetBrains+Mono:wght@400;600&family=Fira+Math&display=swap');

html, body, [class*="css"] { font-family: 'Inter', sans-serif !important; }

#MainMenu, footer, header,
button[title="Deploy"],
[data-testid="deploy-button"] { display: none !important; }

/* Sidebar always-visible toggle */
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
    color: #63b3ed !important; fill: #63b3ed !important;
    width: 16px !important; height: 16px !important;
}

/* App background */
.stApp {
    background: radial-gradient(ellipse at 20% 0%, #0d1b3e 0%, #060d1f 55%, #0a0a14 100%);
    min-height: 100vh;
}

/* ── Hero ───────────────────────────────────────────── */
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
    box-shadow: 0 0 60px rgba(56,128,255,0.08), 0 4px 40px rgba(0,0,0,0.5),
                inset 0 1px 0 rgba(255,255,255,0.07);
}
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
    display: inline-flex; align-items: center; gap: 6px;
    padding: 4px 12px;
    background: rgba(99,179,237,0.12);
    border: 1px solid rgba(99,179,237,0.3);
    border-radius: 100px;
    font-size: 0.72rem; font-weight: 600; color: #63b3ed;
    letter-spacing: 0.1em; text-transform: uppercase; margin-bottom: 1rem;
}
.hero-badge .dot {
    width: 6px; height: 6px; background: #63b3ed; border-radius: 50%;
    animation: pulse-dot 2s ease-in-out infinite;
}
@keyframes pulse-dot {
    0%, 100% { opacity: 1; transform: scale(1); }
    50%       { opacity: 0.4; transform: scale(0.7); }
}
.hero-title {
    font-size: 2.8rem; font-weight: 800; line-height: 1.1; margin: 0 0 0.75rem;
    background: linear-gradient(135deg, #ffffff 0%, #c3d9ff 40%, #7eb8ff 70%, #a78bfa 100%);
    -webkit-background-clip: text; -webkit-text-fill-color: transparent; background-clip: text;
}
.hero-sub {
    font-size: 0.95rem; color: rgba(180,210,255,0.7); font-weight: 400;
    max-width: 680px; line-height: 1.6; margin: 0 0 1.5rem;
}
.hero-pills { display: flex; flex-wrap: wrap; gap: 8px; }
.pill {
    padding: 5px 14px; border-radius: 100px; font-size: 0.78rem;
    font-weight: 500; letter-spacing: 0.02em; border: 1px solid;
}
.pill-blue   { color: #63b3ed; border-color: rgba(99,179,237,0.3);  background: rgba(99,179,237,0.07); }
.pill-green  { color: #68d391; border-color: rgba(104,211,145,0.3); background: rgba(104,211,145,0.07); }
.pill-purple { color: #b794f4; border-color: rgba(183,148,244,0.3); background: rgba(183,148,244,0.07); }
.pill-red    { color: #fc8181; border-color: rgba(252,129,129,0.3); background: rgba(252,129,129,0.07); }
.pill-orange { color: #f6ad55; border-color: rgba(246,173,85,0.3);  background: rgba(246,173,85,0.07); }
.pill-teal   { color: #4fd1c5; border-color: rgba(79,209,197,0.3);  background: rgba(79,209,197,0.07); }

/* ── Metric cards ────────────────────────────────────── */
.metric-grid {
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 12px;
    margin-bottom: 1.5rem;
}
.metric-grid-6 {
    display: grid;
    grid-template-columns: repeat(6, 1fr);
    gap: 12px;
    margin-bottom: 1.5rem;
}
.mcard {
    background: rgba(255,255,255,0.03);
    border: 1px solid rgba(255,255,255,0.08);
    border-radius: 16px; padding: 18px 16px 14px;
    position: relative; overflow: hidden;
    transition: transform 0.2s ease, box-shadow 0.2s ease;
}
.mcard:hover {
    transform: translateY(-2px);
    box-shadow: 0 8px 32px rgba(0,0,0,0.3);
}
.mcard::before {
    content: ''; position: absolute;
    top: 0; left: 0; right: 0; height: 2px; border-radius: 16px 16px 0 0;
}
.mcard-blue::before   { background: linear-gradient(90deg, #4C9BE8, transparent); }
.mcard-orange::before { background: linear-gradient(90deg, #F4A261, transparent); }
.mcard-red::before    { background: linear-gradient(90deg, #E63946, transparent); }
.mcard-crimson::before{ background: linear-gradient(90deg, #9B2335, transparent); }
.mcard-teal::before   { background: linear-gradient(90deg, #2EC4B6, transparent); }
.mcard-purple::before { background: linear-gradient(90deg, #a78bfa, transparent); }
.mcard-gold::before   { background: linear-gradient(90deg, #f6c90e, transparent); }
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
    font-size: 0.68rem; font-weight: 600; letter-spacing: 0.08em;
    text-transform: uppercase; color: rgba(180,200,255,0.55); margin-bottom: 6px;
}
.mcard-value {
    font-size: 1.55rem; font-weight: 700; color: #fff;
    font-family: 'JetBrains Mono', monospace; line-height: 1; margin-bottom: 5px;
}
.mcard-delta {
    font-size: 0.7rem; font-weight: 500; padding: 2px 8px;
    border-radius: 100px; display: inline-block;
}
.delta-danger  { background: rgba(230,57,70,0.2);  color: #fc8181; }
.delta-safe    { background: rgba(46,196,182,0.15); color: #68d391; }
.delta-neutral { background: rgba(180,200,255,0.1); color: rgba(180,200,255,0.6); }

/* ── Section header ──────────────────────────────────── */
.section-hdr {
    display: flex; align-items: center; gap: 10px; margin: 1.5rem 0 1rem;
}
.section-hdr-line {
    flex: 1; height: 1px;
    background: linear-gradient(90deg, rgba(99,179,237,0.3), transparent);
}
.section-hdr-text {
    font-size: 0.76rem; font-weight: 600; letter-spacing: 0.12em;
    text-transform: uppercase; color: rgba(99,179,237,0.7); white-space: nowrap;
}

/* ── Chart container ─────────────────────────────────── */
.chart-wrap {
    background: rgba(255,255,255,0.02);
    border: 1px solid rgba(255,255,255,0.07);
    border-radius: 20px; padding: 8px;
    box-shadow: 0 4px 40px rgba(0,0,0,0.3);
    margin-bottom: 1.4rem;
}

/* ── Equation box ────────────────────────────────────── */
.eq-box {
    background: rgba(99,179,237,0.05);
    border: 1px solid rgba(99,179,237,0.15);
    border-radius: 14px; padding: 1.1rem 1.4rem;
    margin-bottom: 1.2rem;
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.82rem; color: rgba(180,210,255,0.8);
    line-height: 2.1;
}
.eq-box b { color: #7eb8ff; }

/* ── Tabs ────────────────────────────────────────────── */
[data-testid="stTabs"] button {
    font-family: 'Inter', sans-serif !important;
    font-weight: 500 !important; font-size: 0.85rem !important;
    color: rgba(180,200,255,0.6) !important;
    border-radius: 8px 8px 0 0 !important;
    padding: 8px 18px !important; transition: color 0.2s !important;
}
[data-testid="stTabs"] button[aria-selected="true"] {
    color: #63b3ed !important;
    background: rgba(99,179,237,0.08) !important;
    border-bottom: 2px solid #63b3ed !important;
}

/* ── Sidebar ─────────────────────────────────────────── */
section[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #0a0f22 0%, #060d1f 100%) !important;
    border-right: 1px solid rgba(99,179,237,0.1) !important;
}
section[data-testid="stSidebar"] .stMarkdown h2,
section[data-testid="stSidebar"] h2 {
    color: #63b3ed !important; font-size: 0.72rem !important;
    font-weight: 700 !important; letter-spacing: 0.12em !important;
    text-transform: uppercase !important; margin-top: 1.2rem !important;
}
section[data-testid="stSidebar"] .stSlider > label,
section[data-testid="stSidebar"] .stNumberInput > label,
section[data-testid="stSidebar"] .stSelectbox > label {
    font-size: 0.82rem !important;
    color: rgba(180,210,255,0.8) !important; font-weight: 500 !important;
}

.sidebar-logo {
    text-align: center; padding: 1.2rem 0 0.5rem; margin-bottom: 0.5rem;
}
.sidebar-logo .logo-icon {
    font-size: 2.8rem; display: block;
    filter: drop-shadow(0 0 12px rgba(99,179,237,0.5));
}
.sidebar-logo .logo-text { font-size: 1.1rem; font-weight: 700; color: #fff; letter-spacing: 0.02em; }
.sidebar-logo .logo-version { font-size: 0.68rem; color: rgba(99,179,237,0.5); letter-spacing: 0.1em; }

/* ── Control Panel ───────────────────────────────────── */
.home-ctrl-panel {
    background: linear-gradient(180deg, rgba(14,23,48,0.92) 0%, rgba(8,13,30,0.95) 100%);
    border: 1px solid rgba(99,179,237,0.22);
    border-radius: 20px; padding: 1.3rem 1.2rem 1.6rem;
    box-shadow: 0 8px 48px rgba(0,0,0,0.45); margin-bottom: 1.5rem;
}
.home-ctrl-title {
    font-size: 1.0rem; font-weight: 800; color: #fff; margin-bottom: 0.2rem;
    display: flex; align-items: center; gap: 8px;
}
.home-ctrl-sub { font-size: 0.73rem; color: rgba(180,210,255,0.6); margin-bottom: 0.8rem; }

.sdivider {
    height: 1px;
    background: linear-gradient(90deg, transparent, rgba(99,179,237,0.15), transparent);
    margin: 0.8rem 0;
}

/* ── Comparison / Lives Banner ───────────────────────── */
.lives-banner {
    margin-top: 1rem; padding: 18px 24px; border-radius: 16px;
    background: linear-gradient(135deg, rgba(46,196,182,0.1) 0%, rgba(104,211,145,0.08) 100%);
    border: 1px solid rgba(46,196,182,0.25);
    font-size: 0.95rem; color: #68d391; font-weight: 500; text-align: center;
}
.lives-banner strong { font-size: 1.3rem; color: #fff; }
.lives-banner-warn {
    background: linear-gradient(135deg, rgba(230,57,70,0.1) 0%, rgba(252,129,129,0.06) 100%);
    border-color: rgba(230,57,70,0.25); color: #fc8181;
}

/* ── Insight boxes ───────────────────────────────────── */
.insight-box {
    background: rgba(183,148,244,0.06);
    border: 1px solid rgba(183,148,244,0.2);
    border-radius: 12px; padding: 14px 18px; margin-bottom: 1rem;
    font-size: 0.84rem; color: rgba(200,180,255,0.85); line-height: 1.7;
}
.insight-box b { color: #b794f4; }

/* ── Expander ────────────────────────────────────────── */
[data-testid="stExpander"] {
    background: rgba(255,255,255,0.02) !important;
    border: 1px solid rgba(255,255,255,0.07) !important;
    border-radius: 12px !important;
}

/* ── Download button ─────────────────────────────────── */
.stDownloadButton > button {
    background: linear-gradient(135deg, #1a3a6e 0%, #0f2347 100%) !important;
    border: 1px solid rgba(99,179,237,0.3) !important;
    color: #63b3ed !important; border-radius: 10px !important;
    font-weight: 600 !important; font-family: 'Inter', sans-serif !important;
    transition: all 0.2s !important;
}
.stDownloadButton > button:hover {
    background: linear-gradient(135deg, #1e4a8a 0%, #132d5c 100%) !important;
    box-shadow: 0 0 20px rgba(99,179,237,0.2) !important;
}

[data-testid="metric-container"] { display: none; }
</style>
""", unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# Floating sidebar toggle (JS injection)
# ---------------------------------------------------------------------------
components.html("""
<script>
(function() {
    var doc = window.parent.document;
    function injectBtn() {
        if (doc.getElementById('episim-sb-toggle')) return;
        var btn = doc.createElement('button');
        btn.id = 'episim-sb-toggle';
        btn.title = 'Toggle sidebar';
        btn.innerHTML = '&#9776;';
        btn.setAttribute('aria-label', 'Toggle sidebar');
        Object.assign(btn.style, {
            position: 'fixed', top: '12px', left: '12px', zIndex: '999999',
            width: '38px', height: '38px', borderRadius: '10px',
            border: '1px solid rgba(99,179,237,0.4)',
            background: 'rgba(6,12,30,0.88)', backdropFilter: 'blur(14px)',
            color: '#63b3ed', fontSize: '1.15rem', cursor: 'pointer',
            display: 'flex', alignItems: 'center', justifyContent: 'center',
            transition: 'background 0.2s, box-shadow 0.2s',
            boxShadow: '0 2px 14px rgba(0,0,0,0.45)', fontFamily: 'sans-serif',
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
    "COVID-19 (Omicron)": {
        "beta": 0.55, "sigma": 0.35, "gamma": 0.12, "mu": 0.002,
        "hospitalization_rate": 0.03, "days": 120,
    },
    "COVID-19 (Original strain)": {
        "beta": 0.30, "sigma": 0.20, "gamma": 0.07, "mu": 0.005,
        "hospitalization_rate": 0.06, "days": 180,
    },
    "Influenza (seasonal)": {
        "beta": 0.25, "sigma": 0.50, "gamma": 0.20, "mu": 0.001,
        "hospitalization_rate": 0.02, "days": 90,
    },
    "Ebola (West Africa 2014)": {
        "beta": 0.18, "sigma": 0.12, "gamma": 0.07, "mu": 0.04,
        "hospitalization_rate": 0.80, "days": 150,
    },
    "Measles (unvaccinated)": {
        "beta": 0.90, "sigma": 0.25, "gamma": 0.14, "mu": 0.0005,
        "hospitalization_rate": 0.01, "days": 120,
    },
    "SARS-CoV-1 (2003)": {
        "beta": 0.22, "sigma": 0.19, "gamma": 0.10, "mu": 0.010,
        "hospitalization_rate": 0.20, "days": 180,
    },
}

# ---------------------------------------------------------------------------
# Sidebar — Academic reference panel
# ---------------------------------------------------------------------------
with st.sidebar:
    st.markdown("""
    <div class="sidebar-logo">
        <span class="logo-icon">🦠</span>
        <div class="logo-text">EpiSim</div>
        <div class="logo-version">EPIDEMIC PLATFORM · v3.0</div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown('<div class="sdivider"></div>', unsafe_allow_html=True)

    st.markdown(r"""
    ### 📖 Compartmental Models

    **SEIRD** — Full dynamics with incubation ($E$) and mortality ($D$).
    **SEIR** — Classical incubation, zero fatalities ($\mu=0$).
    **SIR** — Kermack–McKendrick ($S \to I \to R$).
    **SIS** — Endemic, no permanent immunity ($S \to I \to S$).

    ---
    ### 📐 Core ODE System (SEIRD)
    """)

    st.markdown("""
    <div class="eq-box">
    <b>dS/dt</b> = −β·S·I / N<br>
    <b>dE/dt</b> = β·S·I / N − σ·E<br>
    <b>dI/dt</b> = σ·E − (γ + μ)·I<br>
    <b>dR/dt</b> = γ·I<br>
    <b>dD/dt</b> = μ·I
    </div>
    """, unsafe_allow_html=True)

    st.markdown(r"""
    ### 📊 Key Quantities

    | Symbol | Meaning |
    |--------|---------|
    | R₀ | Basic reproduction number = β/(γ+μ) |
    | Rt | Effective Rt = R₀·S(t)/N |
    | HIT | Herd immunity threshold = 1−1/R₀ |
    | CFR | Case fatality ratio = μ/(μ+γ) |
    | SI | Serial interval ≈ 1/σ + 0.5/γ |

    ---
    ### 🔗 References
    - Kermack & McKendrick (1927)
    - Anderson & May — *Infectious Diseases of Humans* (1991)
    - Heesterbeek *et al.* — *Science* 347 (2015)
    - WHO COVID-19 Technical Guidance (2020)
    """)

# ---------------------------------------------------------------------------
# Hero banner
# ---------------------------------------------------------------------------
st.markdown("""
<div class="hero-wrap">
  <div class="hero-content">
    <div class="hero-badge">
      <span class="dot"></span>
      Academic Simulation Platform — v3.0
    </div>
    <h1 class="hero-title">EpiSim — Disease Spread<br>Simulation Dashboard</h1>
    <p class="hero-sub">
      A rigorous compartmental epidemic modelling platform for academic analysis.
      Explore transmission dynamics, intervention effects, herd immunity thresholds,
      phase-plane trajectories, and sensitivity analysis — in real time.
    </p>
    <div class="hero-pills">
      <span class="pill pill-blue">🧬 SEIRD / SEIR / SIR / SIS</span>
      <span class="pill pill-purple">🎬 Animated Epidemic Curves</span>
      <span class="pill pill-teal">📈 Time-Varying Rt(t)</span>
      <span class="pill pill-orange">🔬 Phase Plane Analysis</span>
      <span class="pill pill-red">⚡ Sensitivity Analysis</span>
      <span class="pill pill-green">💉 Intervention Comparison</span>
    </div>
  </div>
</div>
""", unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# Layout: Left control panel + Right dashboard
# ---------------------------------------------------------------------------
col_ctrl, col_main = st.columns([1.1, 2.9], gap="large")

with col_ctrl:
    st.markdown("""
    <div class="home-ctrl-panel">
        <div class="home-ctrl-title">🎛️ SIMULATION CONTROLS</div>
        <div class="home-ctrl-sub">Configure epidemic model & parameters</div>
    </div>
    """, unsafe_allow_html=True)

    model_type = st.selectbox(
        "Epidemic Model Architecture",
        [
            "SEIRD (Full dynamics)",
            "SEIR (Classical incubation)",
            "SIR (Simple epidemic)",
            "SIS (No permanent immunity)",
        ],
        help="Select the mathematical compartmental structure to simulate"
    )

    st.markdown('<div class="sdivider"></div>', unsafe_allow_html=True)
    preset = st.selectbox("Disease Preset", list(PRESETS.keys()))
    p = PRESETS[preset]

    with st.expander("👥 Population", expanded=True):
        population       = st.slider("Population size N",    500, 500_000, p.get("population", 50_000), 500)
        initial_infected = st.slider("Initial infected I₀",  1, 1000, 10, 1)

    with st.expander("🦠 Epidemiological Rates", expanded=True):
        beta  = st.slider("Transmission rate β",  0.05, 2.00, p.get("beta",  0.30), 0.01,
                          help="β = contact rate × transmission probability. Higher → faster spread.")
        sigma = st.slider("Incubation rate σ",    0.05, 1.00, p.get("sigma", 0.20), 0.01,
                          help="σ = 1 / (mean incubation days). E.g. σ=0.2 → 5-day incubation.")
        gamma = st.slider("Recovery rate γ",      0.02, 0.50, p.get("gamma", 0.10), 0.01,
                          help="γ = 1 / (mean infectious days). E.g. γ=0.1 → 10-day illness.")
        mu    = st.slider("Case fatality rate μ", 0.000, 0.10, p.get("mu", 0.005), 0.001,
                          help="Fraction of infectious-days ending in death per day.")

    with st.expander("🛡️ Public Health Interventions", expanded=False):
        vaccine_coverage     = st.slider("Vaccination coverage",  0.00, 0.95, 0.0, 0.05,
                                         help="Fraction immunised at day 0 (pre-epidemic)")
        distancing_reduction = st.slider("Social distancing",     0.00, 0.90, 0.0, 0.05,
                                         help="Fractional reduction in β (0 = no distancing)")

    with st.expander("🏥 Healthcare & ICU Capacity", expanded=False):
        hospitalization_rate = st.slider("Hospitalisation rate", 0.00, 1.00,
                                         p.get("hospitalization_rate", 0.05), 0.01,
                                         help="Fraction of infectious needing a hospital bed")
        icu_capacity         = st.slider("ICU beds (per 100k)",  10, 2000, 300, 10,
                                         help="ICU beds per 100,000 people")
        icu_beds_abs = int(icu_capacity * population / 100_000)

    with st.expander("⚙️ Advanced", expanded=False):
        days             = st.slider("Days to simulate", 30, 730, p.get("days", 150), 10)
        monte_carlo_runs = st.number_input("Monte Carlo runs (0 = off)",
                                           min_value=0, max_value=200, value=0, step=10)
        animate_chart    = st.checkbox("🎬 Animated simulation", value=True,
                                       help="Show day-by-day animated epidemic progression")


# ---------------------------------------------------------------------------
# Colour palettes
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
    "Susceptible": "rgba(76,155,232,0.08)",
    "Exposed":     "rgba(246,173,85,0.08)",
    "Infectious":  "rgba(252,129,129,0.12)",
    "Recovered":   "rgba(104,211,145,0.09)",
    "Deaths":      "rgba(197,48,48,0.10)",
}

LAYOUT_BASE = dict(
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    font=dict(family="Inter", color="rgba(180,210,255,0.75)"),
    margin=dict(l=55, r=30, t=50, b=50),
    hovermode="x unified",
    hoverlabel=dict(
        bgcolor="rgba(10,15,35,0.95)",
        bordercolor="rgba(99,179,237,0.3)",
        font_family="Inter", font_size=12,
    ),
    legend=dict(
        orientation="h", yanchor="bottom", y=1.01,
        xanchor="right", x=1,
        font=dict(size=11), bgcolor="rgba(0,0,0,0)",
    ),
    xaxis=dict(
        showgrid=True, gridcolor="rgba(255,255,255,0.04)",
        zeroline=False, tickfont=dict(size=11),
    ),
    yaxis=dict(
        showgrid=True, gridcolor="rgba(255,255,255,0.04)",
        zeroline=False, tickfont=dict(size=11),
    ),
)


def model_columns(model_upper: str) -> list[str]:
    if model_upper == "SEIR":
        return ["Susceptible", "Exposed", "Infectious", "Recovered"]
    if model_upper == "SIR":
        return ["Susceptible", "Infectious", "Recovered"]
    if model_upper == "SIS":
        return ["Susceptible", "Infectious"]
    return ["Susceptible", "Exposed", "Infectious", "Recovered", "Deaths"]


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


def metric_card(label: str, value: str, delta: str,
                card_cls: str, delta_cls: str) -> str:
    return f"""
    <div class="mcard {card_cls}">
        <div class="mcard-label">{label}</div>
        <div class="mcard-value">{value}</div>
        <span class="mcard-delta {delta_cls}">{delta}</span>
    </div>"""


# ---------------------------------------------------------------------------
# Chart builders
# ---------------------------------------------------------------------------

def build_static_fig(df: pd.DataFrame, icu_line: int,
                     mc_summary: dict | None, model_upper: str,
                     peak_day: int, r0: float) -> go.Figure:
    """Full compartment chart with ICU line, MC bands, peak annotation."""
    fig = go.Figure()
    active_cols = model_columns(model_upper)

    for col in active_cols:
        fig.add_trace(go.Scatter(
            x=df["Day"], y=df[col], name=col, mode="lines",
            fill="tozeroy", fillcolor=FILL_COLOURS[col],
            line=dict(color=COLOURS[col], width=2.5),
            hovertemplate=f"<b>{col}</b>: %{{y:,.0f}}<br>Day %{{x:.0f}}<extra></extra>",
        ))

    fig.add_trace(go.Scatter(
        x=df["Day"], y=df["Hospitalised"], name="Hospitalised",
        mode="lines", line=dict(color="#F6AD55", width=1.5, dash="dot"),
        hovertemplate="<b>Hospitalised</b>: %{y:,.0f}<br>Day %{x:.0f}<extra></extra>",
    ))

    fig.add_hline(
        y=icu_line, line_color="rgba(252,129,129,0.7)",
        line_dash="dash", line_width=1.5,
        annotation_text=f"⚠ ICU capacity ({icu_line:,})",
        annotation_position="top right",
        annotation_font_color="rgba(252,129,129,0.9)",
        annotation_font_size=11,
    )

    # Peak annotation
    peak_inf_val = df["Infectious"].iloc[peak_day] if peak_day < len(df) else df["Infectious"].max()
    fig.add_annotation(
        x=peak_day, y=peak_inf_val,
        text=f"<b>Peak: Day {peak_day}</b>",
        showarrow=True, arrowhead=2, arrowcolor="rgba(252,129,129,0.8)",
        arrowwidth=2, ax=40, ay=-40,
        font=dict(color="#fc8181", size=11),
        bgcolor="rgba(10,15,35,0.85)",
        bordercolor="rgba(252,129,129,0.4)", borderwidth=1, borderpad=5,
    )

    # Monte Carlo bands
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

    layout = dict(**LAYOUT_BASE)
    layout["height"] = 480
    layout["xaxis"] = dict(title="Day", **LAYOUT_BASE["xaxis"])
    layout["yaxis"] = dict(title="Number of Individuals", **LAYOUT_BASE["yaxis"])
    layout["title"] = dict(
        text=f"<b>{model_upper} Epidemic Curve</b>  ·  R₀ = {r0:.2f}",
        font=dict(size=14, color="rgba(180,210,255,0.85)"),
    )
    fig.update_layout(**layout)
    return fig


def build_animated_fig(df: pd.DataFrame, icu_line: int, model_upper: str,
                       peak_day: int, r0: float, rt_series: np.ndarray) -> go.Figure:
    """Plotly animated chart — day-by-day epidemic progression with slider."""
    active_cols = model_columns(model_upper)
    n_frames = len(df)
    # Sample every 2 days for performance (up to 200 frames)
    step = max(1, n_frames // 150)
    frame_indices = list(range(0, n_frames, step))
    if (n_frames - 1) not in frame_indices:
        frame_indices.append(n_frames - 1)

    frames = []
    for fi in frame_indices:
        day_df = df.iloc[:fi + 1]
        frame_traces = []
        for col in active_cols:
            frame_traces.append(go.Scatter(
                x=day_df["Day"], y=day_df[col], name=col,
                mode="lines", fill="tozeroy",
                fillcolor=FILL_COLOURS[col],
                line=dict(color=COLOURS[col], width=2.5),
            ))
        frame_traces.append(go.Scatter(
            x=day_df["Day"], y=day_df["Hospitalised"],
            name="Hospitalised", mode="lines",
            line=dict(color="#F6AD55", width=1.5, dash="dot"),
        ))
        cur_rt = rt_series[fi] if fi < len(rt_series) else rt_series[-1]
        cur_I = day_df["Infectious"].iloc[-1]
        frame_traces.append(go.Scatter(
            x=[fi], y=[cur_I], mode="markers",
            marker=dict(color="#FC8181", size=10, symbol="circle",
                        line=dict(color="white", width=2)),
            name="Current Day", showlegend=False,
        ))
        frames.append(go.Frame(
            data=frame_traces,
            name=str(fi),
            layout=go.Layout(
                annotations=[
                    dict(
                        xref="paper", yref="paper",
                        x=0.01, y=0.98, showarrow=False,
                        text=f"<b>Day {fi}  |  Rt = {cur_rt:.2f}  |  Active: {int(cur_I):,}</b>",
                        font=dict(size=12, color="rgba(200,210,255,0.9)"),
                        bgcolor="rgba(6,12,30,0.8)",
                        bordercolor="rgba(99,179,237,0.3)",
                        borderwidth=1, borderpad=6,
                    )
                ]
            )
        ))

    # Initial traces
    initial_day = df.iloc[:1]
    fig = go.Figure(
        data=[
            *[go.Scatter(
                x=initial_day["Day"], y=initial_day[col], name=col,
                mode="lines", fill="tozeroy",
                fillcolor=FILL_COLOURS[col],
                line=dict(color=COLOURS[col], width=2.5),
                hovertemplate=f"<b>{col}</b>: %{{y:,.0f}}<br>Day %{{x:.0f}}<extra></extra>",
            ) for col in active_cols],
            go.Scatter(
                x=initial_day["Day"], y=initial_day["Hospitalised"],
                name="Hospitalised", mode="lines",
                line=dict(color="#F6AD55", width=1.5, dash="dot"),
            ),
            go.Scatter(x=[0], y=[initial_day["Infectious"].iloc[0]],
                       mode="markers",
                       marker=dict(color="#FC8181", size=10, symbol="circle",
                                   line=dict(color="white", width=2)),
                       name="Current Day", showlegend=False),
        ],
        frames=frames,
    )

    fig.add_hline(
        y=icu_line, line_color="rgba(252,129,129,0.65)",
        line_dash="dash", line_width=1.5,
        annotation_text=f"⚠ ICU ({icu_line:,})",
        annotation_position="top right",
        annotation_font_color="rgba(252,129,129,0.8)",
        annotation_font_size=10,
    )

    slider_steps = [
        dict(
            args=[[str(fi)], dict(
                frame=dict(duration=0, redraw=True),
                mode="immediate",
                transition=dict(duration=0),
            )],
            label=str(fi),
            method="animate",
        )
        for fi in frame_indices
    ]

    layout = dict(**LAYOUT_BASE)
    layout.update(dict(
        height=500,
        title=dict(
            text=f"<b>🎬 Animated {model_upper} Epidemic</b>  ·  R₀ = {r0:.2f}",
            font=dict(size=14, color="rgba(180,210,255,0.85)"),
        ),
        xaxis=dict(title="Day", range=[0, df["Day"].max()], **LAYOUT_BASE["xaxis"]),
        yaxis=dict(title="Number of Individuals",
                   range=[0, df[list(active_cols)].max().max() * 1.1],
                   **LAYOUT_BASE["yaxis"]),
        updatemenus=[dict(
            type="buttons",
            showactive=False,
            x=0.0, xanchor="left", y=-0.12, yanchor="top",
            bgcolor="rgba(6,12,30,0.88)",
            bordercolor="rgba(99,179,237,0.35)",
            font=dict(color="#63b3ed", size=12),
            buttons=[
                dict(label="▶  Play", method="animate",
                     args=[None, dict(
                         frame=dict(duration=60, redraw=True),
                         fromcurrent=True,
                         transition=dict(duration=0, easing="linear"),
                     )]),
                dict(label="⏸  Pause", method="animate",
                     args=[[None], dict(
                         frame=dict(duration=0, redraw=False),
                         mode="immediate",
                         transition=dict(duration=0),
                     )]),
            ],
        )],
        sliders=[dict(
            active=0,
            currentvalue=dict(
                prefix="Day: ", visible=True,
                font=dict(color="rgba(180,210,255,0.8)", size=12),
            ),
            pad=dict(t=40, b=10),
            bgcolor="rgba(6,12,30,0.6)",
            bordercolor="rgba(99,179,237,0.2)",
            tickcolor="rgba(99,179,237,0.4)",
            font=dict(color="rgba(180,210,255,0.5)", size=10),
            steps=slider_steps,
        )],
    ))
    fig.update_layout(**layout)
    return fig


def build_incidence_fig(df: pd.DataFrame, incidence: np.ndarray, peak_day: int) -> go.Figure:
    """Daily new cases (incidence) bar chart."""
    fig = go.Figure()
    colors = [
        "#FC8181" if i == peak_day else
        ("rgba(252,129,129,0.7)" if incidence[i] > np.percentile(incidence, 80) else
         "rgba(252,129,129,0.35)")
        for i in range(len(incidence))
    ]
    fig.add_trace(go.Bar(
        x=df["Day"], y=incidence,
        name="Daily New Cases",
        marker=dict(color=colors, line=dict(width=0)),
        hovertemplate="<b>Day %{x:.0f}</b><br>New cases: %{y:,.0f}<extra></extra>",
    ))
    fig.add_vline(
        x=peak_day, line_color="rgba(246,173,85,0.8)",
        line_dash="dash", line_width=1.5,
        annotation_text=f"Peak Day {peak_day}",
        annotation_position="top right",
        annotation_font_color="#F6AD55",
        annotation_font_size=11,
    )
    layout = dict(**LAYOUT_BASE)
    layout.update(dict(
        height=320,
        title=dict(text="<b>Daily New Cases (Incidence)</b>",
                   font=dict(size=13, color="rgba(180,210,255,0.85)")),
        xaxis=dict(title="Day", **LAYOUT_BASE["xaxis"]),
        yaxis=dict(title="New Infections per Day", **LAYOUT_BASE["yaxis"]),
        bargap=0.05,
    ))
    fig.update_layout(**layout)
    return fig


def build_rt_fig(times: np.ndarray, rt_series: np.ndarray, hit: float,
                 vaccine_coverage: float, peak_day: int) -> go.Figure:
    """Time-varying effective reproduction number Rt(t)."""
    fig = go.Figure()

    # Rt=1 threshold (epidemic turning point)
    fig.add_hline(
        y=1.0, line_color="rgba(104,211,145,0.8)",
        line_dash="dash", line_width=1.5,
        annotation_text="Rt = 1 (epidemic control threshold)",
        annotation_position="top right",
        annotation_font_color="#68D391", annotation_font_size=10,
    )

    # Shaded zone above 1 = epidemic growth
    fig.add_hrect(y0=1.0, y1=max(rt_series) * 1.05,
                  fillcolor="rgba(230,57,70,0.05)", line_width=0)
    fig.add_hrect(y0=0, y1=1.0,
                  fillcolor="rgba(46,196,182,0.04)", line_width=0)

    # Rt line
    fig.add_trace(go.Scatter(
        x=times, y=rt_series, name="Effective Rt(t)",
        mode="lines",
        fill="tozeroy", fillcolor="rgba(99,179,237,0.06)",
        line=dict(color="#63b3ed", width=2.5),
        hovertemplate="<b>Day %{x:.0f}</b><br>Rt = %{y:.3f}<extra></extra>",
    ))

    # Herd immunity effective coverage line
    hit_level = max(0.0, 1 - vaccine_coverage) * rt_series[0] if rt_series[0] > 0 else 0
    if hit > 0:
        fig.add_annotation(
            xref="paper", yref="paper",
            x=0.98, y=0.85, showarrow=False,
            text=f"<b>HIT = {hit*100:.1f}%</b><br>of pop. must be immune",
            font=dict(size=11, color="#b794f4"),
            bgcolor="rgba(6,12,30,0.8)", borderpad=6,
            bordercolor="rgba(183,148,244,0.3)", borderwidth=1,
        )

    # Mark peak day
    if peak_day < len(rt_series):
        fig.add_vline(x=peak_day, line_color="rgba(252,129,129,0.5)",
                      line_dash="dot", line_width=1.2)
        fig.add_annotation(
            x=peak_day, y=rt_series[peak_day],
            text=f"Peak Day {peak_day}", showarrow=True,
            arrowhead=2, arrowcolor="rgba(252,129,129,0.7)", arrowwidth=1.5,
            ax=30, ay=-30, font=dict(color="#fc8181", size=10),
            bgcolor="rgba(10,15,35,0.8)",
        )

    layout = dict(**LAYOUT_BASE)
    layout.update(dict(
        height=340,
        title=dict(text="<b>Time-Varying Effective Reproduction Number Rt(t)</b>",
                   font=dict(size=13, color="rgba(180,210,255,0.85)")),
        xaxis=dict(title="Day", **LAYOUT_BASE["xaxis"]),
        yaxis=dict(title="Effective Rt", **LAYOUT_BASE["yaxis"]),
    ))
    layout["legend"] = dict(
        orientation="h", yanchor="top", y=-0.15,
        xanchor="right", x=1, font=dict(size=11), bgcolor="rgba(0,0,0,0)",
    )
    fig.update_layout(**layout)
    return fig


def build_phase_plane_fig(df: pd.DataFrame, r0: float, population: int) -> go.Figure:
    """S-I phase plane — classic epidemic trajectory portrait."""
    S = df["Susceptible"].values
    I = df["Infectious"].values
    n = len(S)

    # Colour the trajectory by time (dark → bright)
    colorscale = px.colors.sequential.Plasma
    fig = go.Figure()

    # Trajectory line coloured by day
    fig.add_trace(go.Scatter(
        x=S, y=I, mode="lines+markers",
        marker=dict(
            color=np.arange(n),
            colorscale="Plasma",
            size=3,
            colorbar=dict(
                title="Day", thickness=10,
                tickfont=dict(size=9, color="rgba(180,210,255,0.6)"),
                title_font=dict(size=10, color="rgba(180,210,255,0.6)"),
                bgcolor="rgba(0,0,0,0)",
            ),
        ),
        line=dict(color="rgba(180,210,255,0.15)", width=1.2),
        hovertemplate="<b>S</b>: %{x:,.0f}<br><b>I</b>: %{y:,.0f}<extra></extra>",
        name="Epidemic trajectory",
    ))

    # Start and end markers
    fig.add_trace(go.Scatter(
        x=[S[0]], y=[I[0]], mode="markers",
        marker=dict(color="#68D391", size=12, symbol="circle",
                    line=dict(color="white", width=2)),
        name="Start (Day 0)",
    ))
    fig.add_trace(go.Scatter(
        x=[S[-1]], y=[I[-1]], mode="markers",
        marker=dict(color="#fc8181", size=12, symbol="square",
                    line=dict(color="white", width=2)),
        name="End",
    ))

    # Isocline: dI/dt = 0 when S = N/R₀ (vertical line)
    s_threshold = population / r0 if r0 > 0 else population
    i_max = I.max() * 1.1
    fig.add_vline(
        x=s_threshold, line_color="rgba(246,173,85,0.7)",
        line_dash="dash", line_width=1.5,
        annotation_text=f"S* = N/R₀ = {s_threshold:,.0f}<br>(dI/dt = 0 isocline)",
        annotation_position="top",
        annotation_font_color="#F6AD55", annotation_font_size=10,
    )

    layout = dict(**LAYOUT_BASE)
    layout.update(dict(
        height=420,
        title=dict(
            text="<b>Phase Plane Portrait (S–I Trajectory)</b>  ·  Epidemic spiral",
            font=dict(size=13, color="rgba(180,210,255,0.85)"),
        ),
        xaxis=dict(title="Susceptible S(t)", **LAYOUT_BASE["xaxis"]),
        yaxis=dict(title="Infectious I(t)", **LAYOUT_BASE["yaxis"]),
    ))
    layout["legend"] = dict(
        orientation="h", yanchor="bottom", y=1.01,
        xanchor="right", x=1, font=dict(size=11), bgcolor="rgba(0,0,0,0)",
    )
    fig.update_layout(**layout)
    return fig


def build_sensitivity_fig(
    population: int, beta: float, sigma: float, gamma: float, mu: float,
    initial_infected: int, days: int, vaccine_coverage: float,
    distancing_reduction: float, hospitalization_rate: float,
    model_type: str,
) -> go.Figure:
    """Tornado sensitivity chart: ±20% change in each parameter → Δ peak infections."""
    base_result = run_scenario(
        population=population, beta=beta, sigma=sigma, gamma=gamma, mu=mu,
        initial_infected=initial_infected, days=days,
        vaccine_coverage=vaccine_coverage, distancing_reduction=distancing_reduction,
        hospitalization_rate=hospitalization_rate, model_type=model_type,
    )
    base_peak = base_result["peak_infected"]
    delta_pct = 0.20  # ±20%

    params_to_sweep = {
        "β (Transmission rate)": ("beta", beta),
        "γ (Recovery rate)": ("gamma", gamma),
        "σ (Incubation rate)": ("sigma", sigma),
        "μ (Case fatality rate)": ("mu", mu),
        "Population N": ("population", population),
        "Initial infected I₀": ("initial_infected", initial_infected),
    }

    labels, lows, highs = [], [], []
    for label, (param_name, base_val) in params_to_sweep.items():
        kwargs = dict(
            population=population, beta=beta, sigma=sigma, gamma=gamma, mu=mu,
            initial_infected=initial_infected, days=days,
            vaccine_coverage=vaccine_coverage, distancing_reduction=distancing_reduction,
            hospitalization_rate=hospitalization_rate, model_type=model_type,
        )

        low_val = max(base_val * (1 - delta_pct), 1e-9 if param_name not in ("population", "initial_infected") else 1)
        high_val = base_val * (1 + delta_pct)

        if param_name == "population":
            low_val = max(int(low_val), initial_infected + 10)
            high_val = int(high_val)

        kwargs_low = dict(kwargs)
        kwargs_low[param_name] = low_val
        kwargs_high = dict(kwargs)
        kwargs_high[param_name] = high_val

        try:
            low_peak = run_scenario(**kwargs_low)["peak_infected"]
            high_peak = run_scenario(**kwargs_high)["peak_infected"]
        except Exception:
            low_peak = base_peak
            high_peak = base_peak

        labels.append(label)
        lows.append(low_peak - base_peak)
        highs.append(high_peak - base_peak)

    # Sort by absolute impact (largest first)
    abs_impact = [abs(h - l) for h, l in zip(highs, lows)]
    sorted_idx = np.argsort(abs_impact)
    labels = [labels[i] for i in sorted_idx]
    lows   = [lows[i]   for i in sorted_idx]
    highs  = [highs[i]  for i in sorted_idx]

    fig = go.Figure()
    fig.add_trace(go.Bar(
        y=labels, x=lows,
        orientation="h",
        name=f"−20% change",
        marker=dict(color="rgba(99,179,237,0.75)",
                    line=dict(color="rgba(99,179,237,0.9)", width=1)),
        hovertemplate="<b>%{y}</b><br>Δ Peak: %{x:+,.0f}<extra>−20%</extra>",
    ))
    fig.add_trace(go.Bar(
        y=labels, x=highs,
        orientation="h",
        name=f"+20% change",
        marker=dict(color="rgba(252,129,129,0.75)",
                    line=dict(color="rgba(252,129,129,0.9)", width=1)),
        hovertemplate="<b>%{y}</b><br>Δ Peak: %{x:+,.0f}<extra>+20%</extra>",
    ))

    layout = dict(**LAYOUT_BASE)
    layout.update(dict(
        height=380,
        barmode="overlay",
        title=dict(
            text="<b>Sensitivity Analysis — Tornado Chart</b>  ·  Impact of ±20% parameter change on Peak Infections",
            font=dict(size=13, color="rgba(180,210,255,0.85)"),
        ),
        xaxis=dict(**{**LAYOUT_BASE["xaxis"],
                       "title": "Change in Peak Infections (vs Baseline)",
                       "zeroline": True,
                       "zerolinecolor": "rgba(255,255,255,0.2)",
                       "zerolinewidth": 1.5}),
        yaxis=dict(title="", tickfont=dict(size=11, color="rgba(180,210,255,0.8)"),
                   showgrid=False),
    ))
    layout["legend"] = dict(
        orientation="h", yanchor="bottom", y=-0.2,
        xanchor="right", x=1, font=dict(size=11), bgcolor="rgba(0,0,0,0)",
    )
    fig.update_layout(**layout)
    return fig


def build_comparison_fig(bl_df: pd.DataFrame, sc_df: pd.DataFrame,
                         icu_line: int, model_type: str = "SEIRD") -> go.Figure:
    """Overlay of Baseline vs Intervention infectious curves."""
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=bl_df["Day"], y=bl_df["Infectious"],
        name="🔴 Baseline (No Intervention)",
        mode="lines", fill="tozeroy",
        fillcolor="rgba(252,129,129,0.06)",
        line=dict(color="#FC8181", width=2.5, dash="dash"),
        hovertemplate="<b>Baseline</b>: %{y:,.0f}<extra></extra>",
    ))
    fig.add_trace(go.Scatter(
        x=sc_df["Day"], y=sc_df["Infectious"],
        name="🟢 With Intervention",
        mode="lines", fill="tozeroy",
        fillcolor="rgba(104,211,145,0.10)",
        line=dict(color="#68D391", width=3.0),
        hovertemplate="<b>Intervention</b>: %{y:,.0f}<extra></extra>",
    ))
    fig.add_trace(go.Scatter(
        x=sc_df["Day"], y=sc_df["Hospitalised"],
        name="🟡 Intervention Hospitalised",
        mode="lines", line=dict(color="#F6AD55", width=1.8, dash="dot"),
        hovertemplate="<b>Hosp.</b>: %{y:,.0f}<extra></extra>",
    ))
    fig.add_hline(
        y=icu_line, line_color="rgba(252,129,129,0.65)",
        line_dash="dash", line_width=1.5,
        annotation_text=f"⚠ ICU Capacity ({icu_line:,})",
        annotation_position="top right",
        annotation_font_color="rgba(252,129,129,0.9)", annotation_font_size=11,
    )
    layout = dict(**LAYOUT_BASE)
    layout.update(dict(
        height=440,
        title=dict(text="<b>Flattening the Curve: Baseline vs. Intervention</b>",
                   font=dict(size=13, color="rgba(180,210,255,0.85)")),
        xaxis=dict(title="Day", **LAYOUT_BASE["xaxis"]),
        yaxis=dict(title="Active Infectious / Hospitalised", **LAYOUT_BASE["yaxis"]),
    ))
    fig.update_layout(**layout)
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


# ---------------------------------------------------------------------------
# Main simulation
# ---------------------------------------------------------------------------
result = run_scenario(
    population=population, beta=beta, sigma=sigma, gamma=gamma, mu=mu,
    initial_infected=initial_infected, days=days,
    vaccine_coverage=vaccine_coverage, distancing_reduction=distancing_reduction,
    hospitalization_rate=hospitalization_rate,
    model_type=model_type,
)

times         = result["times"]
states        = result["states"]
df            = build_df(times, states)
r0            = result["r0"]
peak_inf      = result["peak_infected"]
peak_day      = result["peak_day"]
final_rec     = result["final_recovered"]
total_dth     = result["total_deaths"]
peak_hosp     = result["peak_hospitalized"]
attack_rate   = result["attack_rate"]
incidence     = result["incidence"]
rt_series     = result["rt_series"]
hit           = result["herd_immunity_threshold"]
doubling_time = result["doubling_time"]
serial_int    = result["serial_interval"]
cfr           = result["cfr"]
icu_breached  = peak_hosp > icu_beds_abs
model_upper   = model_type.upper().split(" ")[0]
mc            = run_mc(int(monte_carlo_runs))


# ---------------------------------------------------------------------------
# Main dashboard
# ---------------------------------------------------------------------------
with col_main:
    tab_sim, tab_analysis, tab_compare, tab_data, tab_upload = st.tabs([
        "📈  Simulation",
        "🔬  Analysis",
        "⚖️  Comparison",
        "📋  Data & Export",
        "📂  Dataset Upload",
    ])

    # ── Tab 1: Simulation ─────────────────────────────────────────────────────
    with tab_sim:
        # Row 1: Core KPIs (4 cards across)
        kpi1 = '<div class="metric-grid">'
        r0_danger = r0 > 1
        kpi1 += metric_card(
            "R₀ Basic Reprod. No.", f"{r0:.2f}",
            "🔴 Epidemic grows" if r0_danger else "🟢 Dying out",
            "mcard mcard-blue" + (" mcard-danger" if r0_danger else " mcard-safe"),
            "delta-danger" if r0_danger else "delta-safe",
        )
        kpi1 += metric_card(
            "Peak Active Infections", f"{int(peak_inf):,}",
            f"Day {peak_day}",
            "mcard mcard-red", "delta-neutral",
        )
        kpi1 += metric_card(
            "Peak Hospitalisations", f"{int(peak_hosp):,}",
            "🔴 ICU EXCEEDED" if icu_breached else "🟢 Within capacity",
            "mcard mcard-orange" + (" mcard-danger" if icu_breached else " mcard-safe"),
            "delta-danger" if icu_breached else "delta-safe",
        )
        kpi1 += metric_card(
            "Total Deaths", f"{int(total_dth):,}",
            f"CFR {cfr*100:.2f}%",
            "mcard mcard-crimson" + (" mcard-danger" if total_dth > 0 else ""),
            "delta-danger" if total_dth > 0 else "delta-neutral",
        )
        kpi1 += "</div>"
        st.markdown(kpi1, unsafe_allow_html=True)

        # Row 2: Extended academic metrics (6 cards)
        kpi2 = '<div class="metric-grid-6">'
        kpi2 += metric_card(
            "Attack Rate", f"{attack_rate:.1f}%",
            "of population infected",
            "mcard mcard-purple", "delta-neutral",
        )
        kpi2 += metric_card(
            "Final Recovered", f"{int(final_rec):,}",
            f"{100*final_rec/population:.1f}% of pop.",
            "mcard mcard-teal mcard-safe", "delta-safe",
        )
        kpi2 += metric_card(
            "Herd Immunity Threshold", f"{hit*100:.1f}%",
            "≥ this fraction must be immune",
            "mcard mcard-purple" + (" mcard-danger" if vaccine_coverage < hit else " mcard-safe"),
            "delta-safe" if vaccine_coverage >= hit else "delta-danger",
        )
        kpi2 += metric_card(
            "Doubling Time",
            f"{doubling_time:.1f}d" if doubling_time < 999 else "N/A",
            "initial exponential phase",
            "mcard mcard-gold", "delta-neutral",
        )
        kpi2 += metric_card(
            "Serial Interval", f"{serial_int:.1f}d",
            "mean time between cases",
            "mcard mcard-blue", "delta-neutral",
        )
        kpi2 += metric_card(
            "Case Fatality Ratio", f"{cfr*100:.2f}%",
            f"μ/(μ+γ) = {mu:.3f}/{mu+gamma:.3f}",
            "mcard mcard-crimson" + (" mcard-danger" if cfr > 0.01 else ""),
            "delta-danger" if cfr > 0.01 else "delta-neutral",
        )
        kpi2 += "</div>"
        st.markdown(kpi2, unsafe_allow_html=True)

        # Epidemic curve
        st.markdown("""
        <div class="section-hdr">
          <span class="section-hdr-text">📈 Epidemic Curve</span>
          <div class="section-hdr-line"></div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown('<div class="chart-wrap">', unsafe_allow_html=True)
        if animate_chart:
            st.plotly_chart(
                build_animated_fig(df, icu_beds_abs, model_upper, peak_day, r0, rt_series),
                use_container_width=True,
            )
        else:
            st.plotly_chart(
                build_static_fig(df, icu_beds_abs, mc, model_upper, peak_day, r0),
                use_container_width=True,
            )
        st.markdown('</div>', unsafe_allow_html=True)

        # Insight box
        epidemic_phase = "growth phase 📈" if rt_series[min(peak_day + 5, len(rt_series) - 1)] > 1 else "decline phase 📉"
        vacc_needed = max(0, hit - vaccine_coverage)
        st.markdown(f"""
        <div class="insight-box">
        📌 <b>How to read this chart:</b> The epidemic begins with <b>{initial_infected:,} initial
        infections</b> in a population of <b>{population:,}</b>. With R₀ = <b>{r0:.2f}</b>,
        each infected person spreads the disease to ~{r0:.1f} others on average.
        The epidemic {'grows exponentially' if r0 > 1 else 'self-limits'} until herd immunity
        (~{hit*100:.1f}% immune) is reached.
        {f'<b>An additional {vacc_needed*100:.0f}% vaccination</b> would achieve herd immunity.' if vacc_needed > 0 else '<b>Current vaccination exceeds the herd immunity threshold.</b>'}
        </div>
        """, unsafe_allow_html=True)

        # Scenario parameters expander
        with st.expander("🔬 Scenario Parameters Summary"):
            pcols = st.columns(5)
            params_disp = {
                "Model": model_upper,
                "Population": f"{population:,}",
                "Initial I₀": str(initial_infected),
                "β (transmission)": f"{beta:.2f}",
                "σ (incubation)": f"{sigma:.2f}",
                "γ (recovery)": f"{gamma:.2f}",
                "μ (fatality)": f"{mu:.3f}",
                "Vaccination": f"{vaccine_coverage:.0%}",
                "Distancing": f"{distancing_reduction:.0%}",
                "ICU beds": f"{icu_beds_abs:,}",
            }
            for i, (k, v) in enumerate(params_disp.items()):
                pcols[i % 5].markdown(
                    f'<div style="padding:8px 0;border-bottom:1px solid rgba(255,255,255,0.05)">'
                    f'<span style="color:rgba(180,210,255,0.5);font-size:0.68rem;text-transform:uppercase;letter-spacing:0.06em">{k}</span><br>'
                    f'<span style="color:#fff;font-weight:600;font-size:0.92rem">{v}</span></div>',
                    unsafe_allow_html=True,
                )

    # ── Tab 2: Analysis ───────────────────────────────────────────────────────
    with tab_analysis:
        st.markdown("""
        <div class="section-hdr" style="margin-top:0.2rem">
          <span class="section-hdr-text">🔬 Advanced Epidemiological Analysis</span>
          <div class="section-hdr-line"></div>
        </div>
        """, unsafe_allow_html=True)

        # Daily incidence
        st.markdown("""
        <div class="section-hdr">
          <span class="section-hdr-text">📊 Daily New Cases (Incidence Curve)</span>
          <div class="section-hdr-line"></div>
        </div>
        """, unsafe_allow_html=True)
        st.markdown('<div class="chart-wrap">', unsafe_allow_html=True)
        st.plotly_chart(
            build_incidence_fig(df, incidence, peak_day),
            use_container_width=True,
        )
        st.markdown('</div>', unsafe_allow_html=True)
        st.markdown(f"""
        <div class="insight-box">
        📌 <b>Incidence curve</b> shows <b>new daily infections</b> (dS/dt). The epidemic peak
        occurs on <b>Day {peak_day}</b> with <b>{int(incidence[peak_day]):,} new cases per day</b>.
        This is what epidemiologists use to identify "waves" — each wave corresponds to a distinct
        peak in this chart. Notice how the curve is typically right-skewed during a natural epidemic.
        </div>
        """, unsafe_allow_html=True)

        # Time-varying Rt
        st.markdown("""
        <div class="section-hdr">
          <span class="section-hdr-text">📉 Time-Varying Effective Reproduction Number Rt(t)</span>
          <div class="section-hdr-line"></div>
        </div>
        """, unsafe_allow_html=True)
        st.markdown('<div class="chart-wrap">', unsafe_allow_html=True)
        st.plotly_chart(
            build_rt_fig(times, rt_series, hit, vaccine_coverage, peak_day),
            use_container_width=True,
        )
        st.markdown('</div>', unsafe_allow_html=True)
        st.markdown(f"""
        <div class="insight-box">
        📌 <b>Rt(t)</b> is the number of secondary infections caused by one infectious person
        <i>at time t</i>. It starts at <b>R₀ = {r0:.2f}</b> and falls as the susceptible
        population is depleted. When Rt crosses below <b>1.0</b> (green dashed line), the
        epidemic enters exponential decline. The herd immunity threshold is
        <b>HIT = 1 − 1/R₀ = {hit*100:.1f}%</b>.
        </div>
        """, unsafe_allow_html=True)

        # Phase plane
        st.markdown("""
        <div class="section-hdr">
          <span class="section-hdr-text">🌀 Phase Plane Portrait (S–I State Space)</span>
          <div class="section-hdr-line"></div>
        </div>
        """, unsafe_allow_html=True)
        st.markdown('<div class="chart-wrap">', unsafe_allow_html=True)
        st.plotly_chart(
            build_phase_plane_fig(df, r0, population),
            use_container_width=True,
        )
        st.markdown('</div>', unsafe_allow_html=True)
        st.markdown(f"""
        <div class="insight-box">
        📌 <b>Phase plane portrait</b> — a standard tool in mathematical epidemiology.
        The x-axis shows susceptibles S(t) and the y-axis shows infectious I(t).
        The trajectory spirals from the top-left (large S, small I) to the bottom-right
        (depleted S, zero I). The vertical dashed line at
        <b>S* = N/R₀ = {int(population/r0):,}</b> is the isocline where dI/dt = 0
        — the epidemic peak is exactly where the trajectory crosses this line.
        Colours indicate time progression (purple = early, yellow = late).
        </div>
        """, unsafe_allow_html=True)

        # Sensitivity / tornado
        st.markdown("""
        <div class="section-hdr">
          <span class="section-hdr-text">⚡ Sensitivity Analysis — Tornado Chart</span>
          <div class="section-hdr-line"></div>
        </div>
        """, unsafe_allow_html=True)
        with st.spinner("Computing sensitivity analysis (±20% parameter sweeps)..."):
            st.markdown('<div class="chart-wrap">', unsafe_allow_html=True)
            st.plotly_chart(
                build_sensitivity_fig(
                    population, beta, sigma, gamma, mu,
                    initial_infected, days, vaccine_coverage,
                    distancing_reduction, hospitalization_rate, model_type,
                ),
                use_container_width=True,
            )
            st.markdown('</div>', unsafe_allow_html=True)
        st.markdown(f"""
        <div class="insight-box">
        📌 <b>Sensitivity analysis</b> reveals which parameters have the greatest influence on
        the epidemic outcome (peak infections). Each bar shows the change in peak infections
        when a parameter is increased (🔴 right) or decreased (🔵 left) by 20%.
        The longest bars indicate the most <b>sensitive parameters</b> — these are the
        critical intervention targets for disease control.
        </div>
        """, unsafe_allow_html=True)

    # ── Tab 3: Comparison ─────────────────────────────────────────────────────
    with tab_compare:
        st.markdown("""
        <div class="section-hdr" style="margin-top:0.2rem">
          <span class="section-hdr-text">⚖️ Scenario Comparison: Flattening the Curve</span>
          <div class="section-hdr-line"></div>
        </div>
        """, unsafe_allow_html=True)

        baseline = run_scenario(
            population=population, beta=beta, sigma=sigma, gamma=gamma, mu=mu,
            initial_infected=initial_infected, days=days,
            vaccine_coverage=0.0, distancing_reduction=0.0,
            hospitalization_rate=hospitalization_rate,
            model_type=model_type,
        )
        bl_df = build_df(baseline["times"], baseline["states"])
        bm = baseline
        lives_saved        = int(bm["total_deaths"] - total_dth)
        infections_averted = int(bm["peak_infected"] - peak_inf)
        r0_delta_val  = r0 - bm["r0"]
        inf_delta_val = int(peak_inf - bm["peak_infected"])
        dth_delta_val = int(total_dth - bm["total_deaths"])

        # Impact banner
        if lives_saved > 0 or infections_averted > 0:
            st.markdown(f"""
            <div class="lives-banner" style="margin-bottom:1.2rem">
                ✅ Intervention saves an estimated <strong>{lives_saved:,} lives</strong>
                and averts <strong>{infections_averted:,} peak infections</strong> compared to no-intervention baseline.
            </div>""", unsafe_allow_html=True)
        elif lives_saved < 0:
            st.markdown(f"""
            <div class="lives-banner lives-banner-warn" style="margin-bottom:1.2rem">
                ⚠️ Intervention appears to <strong>increase deaths by {abs(lives_saved):,}</strong>.
                Review vaccination and distancing values.
            </div>""", unsafe_allow_html=True)
        else:
            st.markdown("""
            <div class="lives-banner" style="color:rgba(180,210,255,0.6);border-color:rgba(180,210,255,0.15);background:rgba(180,210,255,0.04);margin-bottom:1.2rem">
                ℹ️ No difference in outcomes — adjust vaccination or distancing in the left panel.
            </div>""", unsafe_allow_html=True)

        # KPI 4-card row
        cmp_cards = '<div class="metric-grid">'
        cmp_cards += metric_card(
            "Effective R₀", f"{r0:.2f}",
            f"{'▼' if r0_delta_val < 0 else '▲'} {abs(r0_delta_val):.2f} vs Baseline ({bm['r0']:.2f})",
            "mcard mcard-blue" + (" mcard-safe" if r0_delta_val < 0 else " mcard-danger"),
            "delta-safe" if r0_delta_val < 0 else "delta-danger",
        )
        cmp_cards += metric_card(
            "Peak Infected", f"{int(peak_inf):,}",
            f"{'▼' if inf_delta_val < 0 else '▲'} {abs(inf_delta_val):,} vs Baseline",
            "mcard mcard-red" + (" mcard-safe" if inf_delta_val < 0 else ""),
            "delta-safe" if inf_delta_val < 0 else "delta-danger",
        )
        cmp_cards += metric_card(
            "Peak Hospitalised", f"{int(peak_hosp):,}",
            f"Baseline: {int(bm['peak_hospitalized']):,}",
            "mcard mcard-orange" + (" mcard-danger" if icu_breached else " mcard-safe"),
            "delta-danger" if icu_breached else "delta-safe",
        )
        cmp_cards += metric_card(
            "Total Deaths", f"{int(total_dth):,}",
            f"{'▼' if dth_delta_val < 0 else '▲'} {abs(dth_delta_val):,} vs Baseline",
            "mcard mcard-crimson" + (" mcard-safe" if dth_delta_val < 0 else " mcard-danger"),
            "delta-safe" if dth_delta_val < 0 else "delta-danger",
        )
        cmp_cards += "</div>"
        st.markdown(cmp_cards, unsafe_allow_html=True)

        # Overlay chart
        st.markdown('<div class="chart-wrap" style="margin-bottom:1.5rem">', unsafe_allow_html=True)
        st.plotly_chart(
            build_comparison_fig(bl_df, df, icu_beds_abs, model_type=model_type),
            use_container_width=True,
        )
        st.markdown('</div>', unsafe_allow_html=True)

        # Rt comparison side by side
        st.markdown("""
        <div class="section-hdr">
          <span class="section-hdr-text">📉 Rt(t) Comparison: Baseline vs Intervention</span>
          <div class="section-hdr-line"></div>
        </div>
        """, unsafe_allow_html=True)
        rt_cmp_fig = go.Figure()
        rt_cmp_fig.add_trace(go.Scatter(
            x=baseline["times"], y=baseline["rt_series"],
            name="🔴 Baseline Rt",
            mode="lines", line=dict(color="#FC8181", width=2, dash="dash"),
        ))
        rt_cmp_fig.add_trace(go.Scatter(
            x=times, y=rt_series,
            name="🟢 Intervention Rt",
            mode="lines", line=dict(color="#68D391", width=2.5),
            fill="tozeroy", fillcolor="rgba(104,211,145,0.06)",
        ))
        rt_cmp_fig.add_hline(y=1.0, line_color="rgba(246,173,85,0.6)",
                              line_dash="dot", line_width=1.5,
                              annotation_text="Rt = 1",
                              annotation_font_color="#F6AD55", annotation_font_size=10)
        layout_cmp = dict(**LAYOUT_BASE)
        layout_cmp.update(dict(
            height=300,
            title=dict(text="<b>Baseline vs Intervention — Rt(t) Comparison</b>",
                       font=dict(size=13, color="rgba(180,210,255,0.85)")),
            xaxis=dict(title="Day", **LAYOUT_BASE["xaxis"]),
            yaxis=dict(title="Effective Rt(t)", **LAYOUT_BASE["yaxis"]),
        ))
        rt_cmp_fig.update_layout(**layout_cmp)
        st.markdown('<div class="chart-wrap">', unsafe_allow_html=True)
        st.plotly_chart(rt_cmp_fig, use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)

        # Detailed comparison table
        st.markdown("""
        <div class="section-hdr">
          <span class="section-hdr-text">📋 Detailed Scenario Breakdown</span>
          <div class="section-hdr-line"></div>
        </div>
        """, unsafe_allow_html=True)
        comp_table_df = pd.DataFrame({
            "Metric": [
                "Basic Reproduction Number R₀",
                "Peak Active Infections",
                "Peak Infection Day",
                "Peak Hospital Beds Needed",
                "Total Cumulative Deaths",
                "Case Fatality Ratio (CFR)",
                "Final Attack Rate (%)",
                "Herd Immunity Threshold",
                "Serial Interval (days)",
            ],
            "🔴 Baseline": [
                f"{bm['r0']:.2f}",
                f"{int(bm['peak_infected']):,}",
                f"Day {bm['peak_day']}",
                f"{int(bm['peak_hospitalized']):,}",
                f"{int(bm['total_deaths']):,}",
                f"{bm['cfr']*100:.2f}%",
                f"{bm['attack_rate']:.1f}%",
                f"{bm['herd_immunity_threshold']*100:.1f}%",
                f"{bm['serial_interval']:.1f}d",
            ],
            "🟢 Intervention": [
                f"{r0:.2f}",
                f"{int(peak_inf):,}",
                f"Day {peak_day}",
                f"{int(peak_hosp):,}",
                f"{int(total_dth):,}",
                f"{cfr*100:.2f}%",
                f"{attack_rate:.1f}%",
                f"{hit*100:.1f}%",
                f"{serial_int:.1f}d",
            ],
            "Change": [
                f"{r0_delta_val:+.2f}",
                f"{inf_delta_val:+,}",
                f"{int(peak_day - bm['peak_day']):+d} days",
                f"{int(peak_hosp - bm['peak_hospitalized']):+,}",
                f"{dth_delta_val:+,}",
                "—",
                f"{attack_rate - bm['attack_rate']:+.1f}%",
                "—",
                "—",
            ],
        })
        st.dataframe(comp_table_df, use_container_width=True, hide_index=True)

    # ── Tab 4: Data & Export ──────────────────────────────────────────────────
    with tab_data:
        st.markdown("""
        <div class="section-hdr" style="margin-top:0.2rem">
          <span class="section-hdr-text">📋 Simulation Data & Export</span>
          <div class="section-hdr-line"></div>
        </div>
        """, unsafe_allow_html=True)

        # Build full export dataframe
        export_df = df.copy()
        export_df["Incidence (new cases)"] = incidence
        export_df["Effective_Rt"] = rt_series
        export_df["Hospitalized"] = df["Hospitalised"]
        export_df = export_df.rename(columns={"Day": "Day"})
        export_df = export_df[[
            "Day", "Susceptible", "Exposed", "Infectious", "Recovered",
            "Deaths", "Hospitalized", "Incidence (new cases)", "Effective_Rt",
        ]]
        export_df["Day"] = export_df["Day"].astype(int)
        for col in export_df.columns[1:]:
            export_df[col] = export_df[col].round(2)

        meta_df = pd.DataFrame({
            "Parameter": ["Model", "Population (N)", "Initial Infected (I₀)",
                          "Transmission rate (β)", "Incubation rate (σ)", "Recovery rate (γ)",
                          "Case fatality rate (μ)", "Vaccination coverage",
                          "Social distancing reduction", "Hospitalisation rate",
                          "ICU beds (per 100k)", "Days simulated",
                          "R₀ (basic reproduction number)", "Peak infected",
                          "Peak day", "Total deaths", "Attack rate (%)",
                          "Herd immunity threshold (%)", "Doubling time (days)",
                          "Serial interval (days)", "Case fatality ratio (%)"],
            "Value": [model_upper, population, initial_infected,
                      beta, sigma, gamma, mu,
                      f"{vaccine_coverage:.0%}", f"{distancing_reduction:.0%}",
                      f"{hospitalization_rate:.0%}", icu_capacity, days,
                      f"{r0:.3f}", f"{int(peak_inf):,}", peak_day,
                      f"{int(total_dth):,}", f"{attack_rate:.1f}",
                      f"{hit*100:.1f}",
                      f"{doubling_time:.1f}" if doubling_time < 999 else "N/A",
                      f"{serial_int:.1f}", f"{cfr*100:.2f}"],
        })

        col_t, col_m = st.columns([2, 1])
        with col_t:
            st.markdown("**Time-Series Simulation Data** (all compartments + derived quantities)")
            st.dataframe(export_df, use_container_width=True, height=400)
        with col_m:
            st.markdown("**Scenario Summary Statistics**")
            st.dataframe(meta_df, use_container_width=True, hide_index=True, height=400)

        dl_col1, dl_col2 = st.columns(2)
        with dl_col1:
            csv_ts = export_df.to_csv(index=False)
            st.download_button(
                "⬇️ Download Time-Series CSV",
                csv_ts,
                file_name=f"episim_{model_upper}_timeseries.csv",
                mime="text/csv",
                use_container_width=True,
            )
        with dl_col2:
            csv_meta = meta_df.to_csv(index=False)
            st.download_button(
                "⬇️ Download Scenario Summary CSV",
                csv_meta,
                file_name=f"episim_{model_upper}_summary.csv",
                mime="text/csv",
                use_container_width=True,
            )

        st.markdown("""
        <div class="insight-box" style="margin-top:1.2rem">
        📌 <b>Export includes:</b> All compartment trajectories (S, E, I, R, D),
        daily hospitalisation estimates, daily incidence (new cases), and time-varying
        Rt(t). The summary table contains all scenario parameters and key
        epidemiological metrics suitable for a scientific report appendix.
        </div>
        """, unsafe_allow_html=True)

    # ── Tab 5: Dataset Upload ─────────────────────────────────────────────────
    with tab_upload:
        st.markdown("""
        <div class="section-hdr" style="margin-top:0.2rem">
          <span class="section-hdr-text">📂 Real-World Dataset — Upload & Fit</span>
          <div class="section-hdr-line"></div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("""
        <div class="insight-box">
        📌 Upload a <b>CSV file</b> containing real epidemic data (e.g. daily reported cases,
        deaths, or active infections). Map your columns below, then either
        <b>auto-fit model parameters</b> to your data using least-squares optimisation,
        or <b>manually overlay</b> your chosen simulation on the real observations.
        </div>
        """, unsafe_allow_html=True)

        # ── Sample CSV hint ──
        sample_csv = "Day,Active_Cases,Daily_Deaths,Recovered\n0,50,0,0\n1,75,1,2\n2,110,1,8\n3,158,2,15\n4,229,3,25\n5,318,4,40"
        st.download_button(
            "⬇️ Download Sample CSV Template",
            sample_csv,
            file_name="sample_epidemic_data.csv",
            mime="text/csv",
        )

        uploaded_file = st.file_uploader(
            "Upload epidemic CSV dataset",
            type=["csv"],
            help="CSV must have at least a Day/Date column and a case count column.",
        )

        if uploaded_file is not None:
            try:
                raw_df = pd.read_csv(uploaded_file)
            except Exception as e:
                st.error(f"❌ Could not read CSV: {e}")
                raw_df = None

            if raw_df is not None and len(raw_df) >= 5:
                st.markdown("**📄 Data Preview**")
                st.dataframe(raw_df.head(20), use_container_width=True)

                cols = raw_df.columns.tolist()
                num_cols = [c for c in cols if pd.api.types.is_numeric_dtype(raw_df[c])]

                st.markdown("""
                <div class="section-hdr">
                  <span class="section-hdr-text">🗺️ Column Mapping</span>
                  <div class="section-hdr-line"></div>
                </div>
                """, unsafe_allow_html=True)

                up_col1, up_col2, up_col3 = st.columns(3)
                with up_col1:
                    day_col = st.selectbox(
                        "Day / Time column",
                        num_cols,
                        index=0,
                        help="Column representing elapsed days (0, 1, 2 …) or sequential time index.",
                    )
                with up_col2:
                    case_col = st.selectbox(
                        "Active / Infectious cases column",
                        num_cols,
                        index=min(1, len(num_cols) - 1),
                        help="Column with active infectious counts to fit/compare against I(t).",
                    )
                with up_col3:
                    death_col = st.selectbox(
                        "Deaths column (optional)",
                        ["— None —"] + num_cols,
                        index=0,
                        help="Optional cumulative or daily deaths column.",
                    )

                up_col4, up_col5 = st.columns(2)
                with up_col4:
                    up_population = st.number_input(
                        "Total population N",
                        min_value=100, max_value=10_000_000,
                        value=population,
                        step=1000,
                        help="Total at-risk population size.",
                    )
                with up_col5:
                    up_model = st.selectbox(
                        "Model to fit",
                        ["SEIRD (Full dynamics)", "SEIR (Classical incubation)",
                         "SIR (Simple epidemic)"],
                        index=0,
                    )

                # Prepare observed arrays
                obs_days   = raw_df[day_col].values.astype(float)
                obs_cases  = raw_df[case_col].values.astype(float)

                # Normalise days to start from 0
                obs_days = obs_days - obs_days.min()

                # Remove NaN rows
                valid_mask = ~(np.isnan(obs_days) | np.isnan(obs_cases))
                obs_days  = obs_days[valid_mask]
                obs_cases = obs_cases[valid_mask]

                I0_guess = max(1, int(obs_cases[0]))

                st.markdown("""
                <div class="section-hdr">
                  <span class="section-hdr-text">⚙️ Fitting Options</span>
                  <div class="section-hdr-line"></div>
                </div>
                """, unsafe_allow_html=True)

                fit_opt_col1, fit_opt_col2, fit_opt_col3 = st.columns(3)
                with fit_opt_col1:
                    fix_sigma = st.checkbox("Fix σ (incubation rate)", value=False)
                    sigma_fixed_val = st.slider(
                        "σ fixed value", 0.05, 1.0, 0.20, 0.01,
                        disabled=not fix_sigma,
                    ) if fix_sigma else None
                with fit_opt_col2:
                    fix_mu = st.checkbox("Fix μ (case fatality rate)", value=False)
                    mu_fixed_val = st.slider(
                        "μ fixed value", 0.0, 0.10, 0.005, 0.001,
                        format="%.3f",
                        disabled=not fix_mu,
                    ) if fix_mu else None
                with fit_opt_col3:
                    fit_mode = st.radio(
                        "Mode",
                        ["🔧 Auto-fit parameters", "🎚️ Manual overlay"],
                        index=0,
                    )

                if fit_mode == "🔧 Auto-fit parameters":
                    if st.button("▶  Run Parameter Fitting", type="primary", use_container_width=True):
                        with st.spinner("🔄 Fitting model to data — running L-BFGS-B optimisation..."):
                            try:
                                fit_res = fit_parameters(
                                    observed_days=obs_days,
                                    observed_cases=obs_cases,
                                    population=int(up_population),
                                    model_type=up_model,
                                    initial_infected=I0_guess,
                                    fit_column="Infectious",
                                    mu_fixed=mu_fixed_val,
                                    sigma_fixed=sigma_fixed_val,
                                )
                                st.session_state["fit_result"] = fit_res
                                st.session_state["fit_obs_days"] = obs_days
                                st.session_state["fit_obs_cases"] = obs_cases
                                st.session_state["fit_death_col"] = death_col
                                st.session_state["fit_death_data"] = (
                                    raw_df[death_col].values[valid_mask] if death_col != "— None —" else None
                                )
                                st.session_state["fit_population"] = int(up_population)
                            except Exception as e:
                                st.error(f"❌ Fitting failed: {e}")

                    # Show fit results if available
                    if "fit_result" in st.session_state:
                        fr = st.session_state["fit_result"]
                        fit_obs_days  = st.session_state.get("fit_obs_days", obs_days)
                        fit_obs_cases = st.session_state.get("fit_obs_cases", obs_cases)
                        death_data    = st.session_state.get("fit_death_data", None)
                        fit_pop       = st.session_state.get("fit_population", int(up_population))

                        # ── Fit Quality KPIs ──
                        st.markdown("""
                        <div class="section-hdr">
                          <span class="section-hdr-text">📊 Fitted Parameter Results</span>
                          <div class="section-hdr-line"></div>
                        </div>
                        """, unsafe_allow_html=True)

                        converged_icon = "✅ Converged" if fr["converged"] else "⚠️ Not converged"
                        fit_kpi = '<div style="display:grid;grid-template-columns:repeat(4,1fr);gap:12px;margin-bottom:1.2rem">'
                        fit_kpi += metric_card("Fitted β", f"{fr['beta']:.4f}",
                                               "transmission rate", "mcard mcard-red", "delta-neutral")
                        fit_kpi += metric_card("Fitted γ", f"{fr['gamma']:.4f}",
                                               "recovery rate", "mcard mcard-teal", "delta-neutral")
                        fit_kpi += metric_card("Fitted R₀", f"{fr['r0']:.2f}",
                                               converged_icon,
                                               "mcard mcard-blue" + (" mcard-danger" if fr['r0'] > 1 else " mcard-safe"),
                                               "delta-danger" if fr['r0'] > 1 else "delta-safe")
                        r2_cls = "delta-safe" if fr["r_squared"] > 0.9 else ("delta-neutral" if fr["r_squared"] > 0.7 else "delta-danger")
                        fit_kpi += metric_card("R² Goodness of Fit", f"{fr['r_squared']:.4f}",
                                               f"RMSE = {fr['rmse']:.1f}",
                                               "mcard mcard-purple", r2_cls)
                        fit_kpi += '</div>'

                        if up_model.startswith("SEIRD") or up_model.startswith("SEIR"):
                            fit_kpi2 = '<div style="display:grid;grid-template-columns:repeat(2,1fr);gap:12px;margin-bottom:1.4rem">'
                            fit_kpi2 += metric_card("Fitted σ", f"{fr['sigma']:.4f}",
                                                    f"incubation period ≈ {1/fr['sigma']:.1f} days",
                                                    "mcard mcard-orange", "delta-neutral")
                            fit_kpi2 += metric_card("Fitted μ", f"{fr['mu']:.4f}",
                                                    f"CFR ≈ {fr['mu']/(fr['mu']+fr['gamma'])*100:.2f}%",
                                                    "mcard mcard-crimson", "delta-neutral")
                            fit_kpi2 += '</div>'
                            st.markdown(fit_kpi + fit_kpi2, unsafe_allow_html=True)
                        else:
                            st.markdown(fit_kpi, unsafe_allow_html=True)

                        # ── Overlay chart: Observed vs Fitted ──
                        st.markdown("""
                        <div class="section-hdr">
                          <span class="section-hdr-text">📈 Observed Data vs Fitted Model</span>
                          <div class="section-hdr-line"></div>
                        </div>
                        """, unsafe_allow_html=True)

                        fig_fit = go.Figure()

                        # Simulated fitted curve
                        fig_fit.add_trace(go.Scatter(
                            x=fr["fitted_times"],
                            y=fr["fitted_states"][:, 2],
                            name="🟢 Fitted model I(t)",
                            mode="lines",
                            line=dict(color="#68D391", width=2.5),
                            fill="tozeroy", fillcolor="rgba(104,211,145,0.08)",
                            hovertemplate="<b>Fitted I(t)</b>: %{y:,.0f}<br>Day %{x:.0f}<extra></extra>",
                        ))

                        # Observed data points
                        fig_fit.add_trace(go.Scatter(
                            x=fit_obs_days,
                            y=fit_obs_cases,
                            name="🔴 Observed cases",
                            mode="markers",
                            marker=dict(
                                color="#FC8181", size=7, symbol="circle",
                                line=dict(color="white", width=1.5),
                            ),
                            hovertemplate="<b>Observed</b>: %{y:,.0f}<br>Day %{x:.0f}<extra></extra>",
                        ))

                        # Deaths overlay if provided
                        if death_data is not None:
                            fig_fit.add_trace(go.Scatter(
                                x=fit_obs_days,
                                y=death_data,
                                name="💀 Observed deaths",
                                mode="markers",
                                marker=dict(color="#C53030", size=6, symbol="x"),
                                hovertemplate="<b>Deaths</b>: %{y:,.0f}<br>Day %{x:.0f}<extra></extra>",
                            ))
                            # Fitted D(t)
                            fig_fit.add_trace(go.Scatter(
                                x=fr["fitted_times"],
                                y=fr["fitted_states"][:, 4],
                                name="Fitted D(t)",
                                mode="lines",
                                line=dict(color="rgba(197,48,48,0.7)", width=1.5, dash="dash"),
                                hovertemplate="<b>Fitted D(t)</b>: %{y:,.0f}<br>Day %{x:.0f}<extra></extra>",
                            ))

                        layout_fit = dict(**LAYOUT_BASE)
                        layout_fit.update(dict(
                            height=460,
                            title=dict(
                                text=f"<b>Real Data vs Fitted {up_model.split(' ')[0]} Model</b>  ·  R² = {fr['r_squared']:.4f}  |  RMSE = {fr['rmse']:.1f}",
                                font=dict(size=13, color="rgba(180,210,255,0.85)"),
                            ),
                            xaxis=dict(title="Day", **LAYOUT_BASE["xaxis"]),
                            yaxis=dict(title="Number of Individuals", **LAYOUT_BASE["yaxis"]),
                        ))
                        fig_fit.update_layout(**layout_fit)
                        st.markdown('<div class="chart-wrap">', unsafe_allow_html=True)
                        st.plotly_chart(fig_fit, use_container_width=True)
                        st.markdown('</div>', unsafe_allow_html=True)

                        # ── Residual chart ──
                        st.markdown("""
                        <div class="section-hdr">
                          <span class="section-hdr-text">🔬 Residuals (Observed − Fitted)</span>
                          <div class="section-hdr-line"></div>
                        </div>
                        """, unsafe_allow_html=True)
                        fig_resid = go.Figure()
                        resid_colors = ["#FC8181" if r > 0 else "#68D391" for r in fr["residuals"]]
                        fig_resid.add_trace(go.Bar(
                            x=fit_obs_days,
                            y=fr["residuals"],
                            name="Residuals",
                            marker=dict(color=resid_colors, line=dict(width=0)),
                            hovertemplate="<b>Day %{x:.0f}</b><br>Residual: %{y:+,.0f}<extra></extra>",
                        ))
                        fig_resid.add_hline(y=0, line_color="rgba(255,255,255,0.25)",
                                            line_width=1)
                        layout_resid = dict(**LAYOUT_BASE)
                        layout_resid.update(dict(
                            height=280,
                            title=dict(text="<b>Model Residuals</b>  ·  Red = over-predicted, Green = under-predicted",
                                       font=dict(size=12, color="rgba(180,210,255,0.8)")),
                            xaxis=dict(title="Day", **LAYOUT_BASE["xaxis"]),
                            yaxis=dict(title="Residual (observed − fitted)", **LAYOUT_BASE["yaxis"]),
                            bargap=0.05,
                        ))
                        fig_resid.update_layout(**layout_resid)
                        st.markdown('<div class="chart-wrap">', unsafe_allow_html=True)
                        st.plotly_chart(fig_resid, use_container_width=True)
                        st.markdown('</div>', unsafe_allow_html=True)

                        # ── Apply fitted params to main sim button ──
                        st.markdown("""
                        <div class="insight-box" style="margin-top:0.6rem">
                        💡 <b>Tip:</b> Copy the fitted parameters below and enter them into
                        the <b>🎛️ Simulation Controls</b> panel on the left to run the full
                        simulation dashboard using these real-data-calibrated parameters.
                        </div>
                        """, unsafe_allow_html=True)
                        params_copy = (
                            f"β = {fr['beta']:.4f}   |   "
                            f"σ = {fr['sigma']:.4f}   |   "
                            f"γ = {fr['gamma']:.4f}   |   "
                            f"μ = {fr['mu']:.4f}   |   "
                            f"R₀ = {fr['r0']:.3f}"
                        )
                        st.code(params_copy, language=None)

                else:  # Manual overlay mode
                    st.markdown("""
                    <div class="section-hdr">
                      <span class="section-hdr-text">🎚️ Manual Overlay — Observed vs Simulation</span>
                      <div class="section-hdr-line"></div>
                    </div>
                    """, unsafe_allow_html=True)

                    man_col1, man_col2 = st.columns(2)
                    with man_col1:
                        man_beta  = st.slider("β (transmission)", 0.05, 2.0, beta, 0.01, key="man_beta")
                        man_sigma = st.slider("σ (incubation)",   0.05, 1.0, sigma, 0.01, key="man_sigma")
                    with man_col2:
                        man_gamma = st.slider("γ (recovery)",     0.02, 0.5, gamma, 0.01, key="man_gamma")
                        man_mu    = st.slider("μ (fatality)",     0.000, 0.10, mu, 0.001, key="man_mu", format="%.3f")

                    man_days = max(int(obs_days.max()) + 10, 30)
                    _, man_states = simulate_seird(
                        population=int(up_population),
                        beta=man_beta, sigma=man_sigma, gamma=man_gamma, mu=man_mu,
                        initial_infected=I0_guess, days=man_days,
                        model_type=up_model,
                    )
                    man_times = np.linspace(0, man_days, man_days + 1)

                    man_r0 = man_beta / (man_gamma + man_mu) if (man_gamma + man_mu) > 0 else 0

                    fig_man = go.Figure()
                    fig_man.add_trace(go.Scatter(
                        x=man_times, y=man_states[:, 2],
                        name=f"🟢 Simulated I(t)  [R₀={man_r0:.2f}]",
                        mode="lines", fill="tozeroy",
                        fillcolor="rgba(104,211,145,0.08)",
                        line=dict(color="#68D391", width=2.5),
                    ))
                    fig_man.add_trace(go.Scatter(
                        x=obs_days, y=obs_cases,
                        name="🔴 Observed cases (uploaded)",
                        mode="markers",
                        marker=dict(color="#FC8181", size=8, symbol="circle",
                                    line=dict(color="white", width=1.5)),
                    ))
                    if death_col != "— None —":
                        death_vals = raw_df[death_col].values[valid_mask]
                        fig_man.add_trace(go.Scatter(
                            x=obs_days, y=death_vals,
                            name="💀 Observed deaths",
                            mode="markers",
                            marker=dict(color="#C53030", size=6, symbol="x"),
                        ))
                        fig_man.add_trace(go.Scatter(
                            x=man_times, y=man_states[:, 4],
                            name="Simulated D(t)",
                            mode="lines",
                            line=dict(color="rgba(197,48,48,0.7)", width=1.5, dash="dash"),
                        ))

                    layout_man = dict(**LAYOUT_BASE)
                    layout_man.update(dict(
                        height=460,
                        title=dict(
                            text=f"<b>Observed Data vs Manual {up_model.split(' ')[0]} Model</b>  ·  R₀ = {man_r0:.2f}",
                            font=dict(size=13, color="rgba(180,210,255,0.85)"),
                        ),
                        xaxis=dict(title="Day", **LAYOUT_BASE["xaxis"]),
                        yaxis=dict(title="Number of Individuals", **LAYOUT_BASE["yaxis"]),
                    ))
                    fig_man.update_layout(**layout_man)
                    st.markdown('<div class="chart-wrap">', unsafe_allow_html=True)
                    st.plotly_chart(fig_man, use_container_width=True)
                    st.markdown('</div>', unsafe_allow_html=True)

                    # Quick goodness-of-fit metric
                    sim_at_obs = man_states[np.clip(obs_days.astype(int), 0, man_days), 2]
                    resid = sim_at_obs - obs_cases
                    man_rmse = float(np.sqrt(np.mean(resid ** 2)))
                    ss_res = float(np.sum(resid ** 2))
                    ss_tot = float(np.sum((obs_cases - np.mean(obs_cases)) ** 2))
                    man_r2 = float(1 - ss_res / ss_tot) if ss_tot > 0 else 0.0
                    st.markdown(
                        f'<div class="insight-box">📐 <b>Goodness of fit:</b> '
                        f'R² = <b>{man_r2:.4f}</b>  |  RMSE = <b>{man_rmse:.1f}</b>  '
                        f'— Adjust the sliders above to improve the fit.</div>',
                        unsafe_allow_html=True,
                    )

            elif raw_df is not None:
                st.warning("⚠️ Dataset has fewer than 5 rows — please upload a larger dataset.")

        else:
            # No file uploaded — show placeholder
            st.markdown("""
            <div style="text-align:center;padding:4rem 2rem;
                        border:2px dashed rgba(99,179,237,0.2);
                        border-radius:20px;color:rgba(180,210,255,0.45);margin-top:1rem">
                <div style="font-size:3rem;margin-bottom:1rem">📂</div>
                <div style="font-size:1.2rem;font-weight:600;margin-bottom:0.6rem">
                    Upload a CSV to begin</div>
                <div style="font-size:0.85rem;max-width:400px;margin:0 auto;line-height:1.7">
                    Drag and drop a CSV file above, or click <b>Browse files</b>.<br>
                    Your CSV needs at least a <b>Day</b> column and an <b>Active Cases</b> column.
                    Download the sample template to see the expected format.
                </div>
            </div>
            """, unsafe_allow_html=True)
