"""
generate_report.py
==================
Generates a fully self-contained, interactive static HTML simulation page
with a fixed sidebar layout (like Streamlit) and tabbed main content.

The SEIRD ODE is solved entirely in JavaScript (RK4) — no backend required.

Usage:
    python generate_report.py
Then open  report/index.html  in any browser.
"""
from pathlib import Path

HTML = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8"/>
<meta name="viewport" content="width=device-width, initial-scale=1.0"/>
<title>EpiSim — Disease Spread Simulation</title>
<meta name="description" content="Simulate any epidemic model in your browser. Adjust SEIRD parameters and watch the outbreak evolve in real time."/>
<script src="https://cdn.plot.ly/plotly-2.32.0.min.js"></script>
<link rel="preconnect" href="https://fonts.googleapis.com"/>
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin/>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&family=JetBrains+Mono:wght@400;600;700&display=swap" rel="stylesheet"/>
<style>
/* ═══ RESET ═══════════════════════════════════════════════════════════════ */
*,*::before,*::after{box-sizing:border-box;margin:0;padding:0}
html{font-size:16px}
body{font-family:'Inter',sans-serif;background:#0a0f1e;color:rgba(210,230,255,0.88);overflow-x:hidden}
::-webkit-scrollbar{width:5px}
::-webkit-scrollbar-track{background:#080d1a}
::-webkit-scrollbar-thumb{background:rgba(99,179,237,0.25);border-radius:3px}

/* ═══ APP SHELL ═══════════════════════════════════════════════════════════ */
/*  Fixed sidebar + scrollable main — mirrors Streamlit layout              */
.app-shell{display:flex;min-height:100vh}

/* ── Sidebar ──────────────────────────────────────────────────────────── */
.sidebar{
  width:290px;min-width:290px;
  background:linear-gradient(180deg,#080d1c 0%,#060b18 100%);
  border-right:1px solid rgba(99,179,237,0.1);
  position:fixed;top:0;left:0;bottom:0;
  overflow-y:auto;overflow-x:hidden;
  z-index:100;
  display:flex;flex-direction:column;
}
.sidebar::-webkit-scrollbar{width:4px}
.sidebar::-webkit-scrollbar-thumb{background:rgba(99,179,237,0.15)}

/* Sidebar header */
.sb-logo{
  padding:1.4rem 1.4rem 1rem;
  border-bottom:1px solid rgba(255,255,255,0.05);
  display:flex;align-items:center;gap:10px;
}
.sb-logo .icon{font-size:1.6rem;filter:drop-shadow(0 0 10px rgba(99,179,237,0.6))}
.sb-logo .brand{display:flex;flex-direction:column;gap:1px}
.sb-logo .name{font-weight:800;font-size:1rem;color:#fff}
.sb-logo .sub{font-size:0.65rem;font-weight:600;letter-spacing:0.1em;color:rgba(99,179,237,0.5);text-transform:uppercase}

/* Sidebar body */
.sb-body{padding:0.8rem 1.1rem 2rem;flex:1}

/* Section label */
.sb-section{
  font-size:0.65rem;font-weight:700;letter-spacing:0.14em;text-transform:uppercase;
  color:rgba(99,179,237,0.65);
  margin:1.2rem 0 0.6rem;
  padding-bottom:4px;
  border-bottom:1px solid rgba(99,179,237,0.1);
}

/* Select */
select{
  width:100%;padding:8px 10px;border-radius:8px;
  background:rgba(255,255,255,0.05);
  border:1px solid rgba(255,255,255,0.1);
  color:rgba(210,230,255,0.85);
  font-size:0.82rem;font-family:'Inter',sans-serif;
  cursor:pointer;outline:none;
  appearance:none;
  background-image:url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='12' height='12' fill='%2363b3ed' viewBox='0 0 16 16'%3E%3Cpath d='M7.247 11.14L2.451 5.658C1.885 5.013 2.345 4 3.204 4h9.592a1 1 0 0 1 .753 1.659l-4.796 5.48a1 1 0 0 1-1.506 0z'/%3E%3C/svg%3E");
  background-repeat:no-repeat;background-position:calc(100% - 10px) center;
  padding-right:28px;
  transition:border-color 0.2s,background-color 0.2s;
}
select:hover{border-color:rgba(99,179,237,0.35);background-color:rgba(255,255,255,0.07)}
select option{background:#0d1730;color:#fff}
.sb-select-wrap{margin-bottom:0.5rem}
.sb-select-label{font-size:0.75rem;color:rgba(180,210,255,0.55);margin-bottom:5px;font-weight:500}

/* Slider control */
.ctrl{display:flex;flex-direction:column;gap:4px;margin-bottom:0.9rem}
.ctrl-top{display:flex;justify-content:space-between;align-items:center}
.ctrl-label{
  font-size:0.76rem;color:rgba(180,210,255,0.65);font-weight:500;
  display:flex;align-items:center;gap:5px;
}
.ctrl-val{
  font-size:0.78rem;font-weight:700;
  font-family:'JetBrains Mono',monospace;
  color:#e05b5b;background:rgba(224,91,91,0.1);
  border-radius:4px;padding:1px 6px;min-width:50px;text-align:right;
}
input[type=range]{
  -webkit-appearance:none;appearance:none;
  width:100%;height:4px;border-radius:2px;outline:none;cursor:pointer;
  background:rgba(224,91,91,0.25);
  transition:background 0.2s;
}
input[type=range]:hover{background:rgba(224,91,91,0.35)}
input[type=range]::-webkit-slider-thumb{
  -webkit-appearance:none;width:14px;height:14px;border-radius:50%;
  background:#e05b5b;border:2px solid rgba(255,255,255,0.2);
  box-shadow:0 0 8px rgba(224,91,91,0.5);cursor:pointer;
  transition:transform 0.15s,box-shadow 0.15s;
}
input[type=range]::-webkit-slider-thumb:hover{
  transform:scale(1.3);box-shadow:0 0 14px rgba(224,91,91,0.7);
}
.ctrl-hint{font-size:0.67rem;color:rgba(180,210,255,0.28);margin-top:1px}

/* Divider */
.sb-divider{height:1px;background:rgba(255,255,255,0.05);margin:0.6rem 0}

/* Tooltip icon */
.tip{
  display:inline-flex;align-items:center;justify-content:center;
  width:14px;height:14px;border-radius:50%;
  border:1px solid rgba(180,210,255,0.3);
  font-size:0.6rem;color:rgba(180,210,255,0.4);cursor:help;
  font-style:normal;flex-shrink:0;
}

/* Status indicator at sidebar bottom */
.sb-status{
  padding:0.9rem 1.1rem;
  border-top:1px solid rgba(255,255,255,0.05);
  display:flex;align-items:center;gap:8px;
  font-size:0.72rem;color:rgba(104,211,145,0.7);font-weight:600;
}
.sb-dot{
  width:7px;height:7px;border-radius:50%;background:#68d391;flex-shrink:0;
  animation:sbpulse 2s ease-in-out infinite;
}
@keyframes sbpulse{0%,100%{opacity:1;transform:scale(1)}50%{opacity:0.3;transform:scale(0.6)}}

/* ── Main area ────────────────────────────────────────────────────────── */
.main{
  margin-left:290px;
  min-height:100vh;
  display:flex;flex-direction:column;
  background:radial-gradient(ellipse at 25% 0%,rgba(13,27,62,0.6) 0%,transparent 60%);
}

/* Top bar */
.topbar{
  padding:1.6rem 2rem 0;
}
.top-title{
  display:flex;align-items:center;gap:14px;
  margin-bottom:0.4rem;
}
.top-title h1{
  font-size:1.9rem;font-weight:800;letter-spacing:-0.02em;color:#fff;
}
.top-sub{
  font-size:0.88rem;color:rgba(180,210,255,0.45);margin-bottom:1.2rem;
}
.top-sub strong{color:rgba(180,210,255,0.65)}

/* ── Tabs ─────────────────────────────────────────────────────────────── */
.tabs{display:flex;gap:0;border-bottom:1px solid rgba(255,255,255,0.08);padding:0 2rem}
.tab{
  padding:10px 20px;font-size:0.82rem;font-weight:600;cursor:pointer;
  color:rgba(180,210,255,0.45);border-bottom:2px solid transparent;
  display:flex;align-items:center;gap:6px;margin-bottom:-1px;
  transition:color 0.2s,border-color 0.2s;user-select:none;
}
.tab:hover{color:rgba(180,210,255,0.75)}
.tab.active{color:#e05b5b;border-bottom-color:#e05b5b}

/* Tab content */
.tab-panel{display:none;padding:1.4rem 2rem 3rem}
.tab-panel.active{display:block}

/* ── Metric cards ─────────────────────────────────────────────────────── */
.metrics-row{display:grid;grid-template-columns:repeat(6,1fr);gap:10px;margin-bottom:1.4rem}
@media(max-width:1100px){.metrics-row{grid-template-columns:repeat(3,1fr)}}

.mcard{
  padding:0.9rem 1rem 0.8rem;
  border-radius:0;
  background:transparent;
  border-bottom:1px solid rgba(255,255,255,0.06);
}
.ml{font-size:0.68rem;color:rgba(180,210,255,0.42);font-weight:500;margin-bottom:5px}
.mv{
  font-size:1.65rem;font-weight:700;color:#fff;
  font-family:'JetBrains Mono',monospace;line-height:1;margin-bottom:5px;
}
.md{
  display:inline-flex;align-items:center;gap:4px;
  font-size:0.7rem;font-weight:600;padding:2px 7px;
  border-radius:4px;
}
.md-danger{background:rgba(252,129,129,0.12);color:#fc8181}
.md-safe  {background:rgba(104,211,145,0.1); color:#68d391}
.md-neutral{background:rgba(180,210,255,0.06);color:rgba(180,210,255,0.5)}

/* Alert banner */
.alert-bar{
  padding:10px 16px;border-radius:10px;font-size:0.82rem;font-weight:500;
  display:flex;align-items:center;gap:8px;margin-bottom:1.1rem;
}
.alert-danger{background:rgba(224,91,91,0.08);border:1px solid rgba(224,91,91,0.2);color:rgba(252,129,129,0.9)}
.alert-safe  {background:rgba(104,211,145,0.07);border:1px solid rgba(104,211,145,0.18);color:rgba(104,211,145,0.85)}
.alert-warn  {background:rgba(246,173,85,0.07);border:1px solid rgba(246,173,85,0.18);color:rgba(246,173,85,0.85)}

/* Section label inside main */
.section-hdr{
  display:flex;align-items:center;gap:10px;margin:0 0 0.75rem;
}
.section-hdr-txt{font-size:0.68rem;font-weight:700;letter-spacing:0.12em;text-transform:uppercase;color:rgba(99,179,237,0.55);white-space:nowrap}
.section-hdr-line{flex:1;height:1px;background:linear-gradient(90deg,rgba(99,179,237,0.2),transparent)}

/* Chart wrapper */
.chart-wrap{
  background:rgba(255,255,255,0.018);
  border:1px solid rgba(255,255,255,0.07);
  border-radius:16px;
  padding:1.2rem 1.2rem 0.4rem;
  margin-bottom:1.2rem;
}
.chart-hdr{display:flex;justify-content:space-between;align-items:flex-start;margin-bottom:0.7rem;flex-wrap:wrap;gap:0.5rem}
.chart-ttl{font-size:0.95rem;font-weight:700;color:#fff;margin-bottom:2px}
.chart-sub{font-size:0.72rem;color:rgba(180,210,255,0.35)}
.legend{display:flex;flex-wrap:wrap;gap:8px}
.li{display:flex;align-items:center;gap:5px;font-size:0.7rem;color:rgba(180,210,255,0.5);font-weight:500}
.ld{width:9px;height:9px;border-radius:50%}
.ldash{width:14px;height:0;border-top:2px dashed;opacity:0.75}

/* ── Comparison tab ─────────────────────────────────────────────────────── */
.compare-grid{display:grid;grid-template-columns:1fr 1fr;gap:1.4rem}
@media(max-width:900px){.compare-grid{grid-template-columns:1fr}}

.cmp-panel{
  background:rgba(255,255,255,0.02);
  border:1px solid rgba(255,255,255,0.07);
  border-radius:16px;padding:1.2rem;
}
.cmp-hdr{
  padding:10px 14px;border-radius:10px;
  font-size:0.82rem;font-weight:700;margin-bottom:1rem;
  display:flex;align-items:center;gap:8px;
}
.cmp-baseline{background:rgba(224,91,91,0.1);border:1px solid rgba(224,91,91,0.22);color:#fc8181}
.cmp-scenario{background:rgba(104,211,145,0.08);border:1px solid rgba(104,211,145,0.2);color:#68d391}

.cmp-stats{display:flex;flex-direction:column;gap:4px;margin-bottom:1rem}
.cmp-row{display:flex;justify-content:space-between;padding:6px 0;border-bottom:1px solid rgba(255,255,255,0.05)}
.cmp-row:last-child{border-bottom:none}
.cmp-lbl{font-size:0.75rem;color:rgba(180,210,255,0.45)}
.cmp-val{font-size:0.82rem;font-weight:700;font-family:'JetBrains Mono',monospace;color:#fff}

.lives-banner{
  margin-top:1.2rem;padding:16px 20px;border-radius:14px;text-align:center;
  font-size:0.9rem;font-weight:500;
}
.lives-banner strong{font-size:1.2rem;color:#fff}
.lbg{background:rgba(104,211,145,0.08);border:1px solid rgba(104,211,145,0.2);color:#68d391}
.lbd{background:rgba(224,91,91,0.08);border:1px solid rgba(224,91,91,0.2);color:#fc8181}
.lbi{background:rgba(180,210,255,0.05);border:1px solid rgba(180,210,255,0.1);color:rgba(180,210,255,0.5)}

/* ── Data table tab ─────────────────────────────────────────────────────── */
.data-table-wrap{overflow-x:auto;border-radius:12px;border:1px solid rgba(255,255,255,0.07);margin-bottom:1.2rem}
table{width:100%;border-collapse:collapse;font-size:0.78rem}
thead th{
  background:rgba(99,179,237,0.06);
  padding:10px 14px;text-align:right;font-weight:700;
  color:rgba(99,179,237,0.7);font-size:0.68rem;letter-spacing:0.08em;text-transform:uppercase;
  border-bottom:1px solid rgba(255,255,255,0.08);white-space:nowrap;
}
thead th:first-child{text-align:left}
tbody tr{border-bottom:1px solid rgba(255,255,255,0.04);transition:background 0.15s}
tbody tr:last-child{border-bottom:none}
tbody tr:hover{background:rgba(255,255,255,0.025)}
tbody td{padding:8px 14px;text-align:right;font-family:'JetBrains Mono',monospace;color:rgba(210,230,255,0.75)}
tbody td:first-child{text-align:left;color:rgba(99,179,237,0.7)}

/* Download button */
.dl-btn{
  display:inline-flex;align-items:center;gap:8px;
  padding:11px 22px;border-radius:10px;border:1px solid rgba(99,179,237,0.3);
  background:rgba(99,179,237,0.08);color:#63b3ed;
  font-size:0.82rem;font-weight:700;font-family:'Inter',sans-serif;
  cursor:pointer;text-decoration:none;transition:all 0.2s;
}
.dl-btn:hover{background:rgba(99,179,237,0.15);box-shadow:0 4px 20px rgba(99,179,237,0.15)}

/* ── Model info at bottom ─────────────────────────────────────────────── */
.model-section{
  padding:2rem 2rem 3rem;
  border-top:1px solid rgba(255,255,255,0.06);
  background:rgba(0,0,0,0.15);
}
.model-grid{display:grid;grid-template-columns:1fr 1fr;gap:2rem;align-items:start}
@media(max-width:860px){.model-grid{grid-template-columns:1fr}}

.comps{display:flex;flex-direction:column;gap:1px;border-radius:14px;overflow:hidden;border:1px solid rgba(255,255,255,0.06)}
.comp{padding:0.9rem 1.2rem;display:flex;align-items:center;gap:12px;background:rgba(255,255,255,0.02);transition:background 0.18s}
.comp:hover{background:rgba(255,255,255,0.04)}
.cl{width:38px;height:38px;border-radius:10px;display:flex;align-items:center;justify-content:center;font-size:1.1rem;font-weight:800;font-family:'JetBrains Mono',monospace;flex-shrink:0}
.cl-S{background:rgba(76,155,232,0.15);color:#4C9BE8}
.cl-E{background:rgba(246,173,85,0.15);color:#F6AD55}
.cl-I{background:rgba(252,129,129,0.15);color:#FC8181}
.cl-R{background:rgba(104,211,145,0.15);color:#68D391}
.cl-D{background:rgba(197,48,48,0.15);color:#C53030}
.cn{font-weight:700;color:#fff;font-size:0.85rem}
.cd{font-size:0.72rem;color:rgba(180,210,255,0.38);margin-top:1px}

.eqs{display:flex;flex-direction:column;gap:8px}
.eq{padding:0.85rem 1.1rem;background:rgba(255,255,255,0.02);border:1px solid rgba(255,255,255,0.06);border-radius:10px}
.eq-l{font-size:0.62rem;font-weight:700;letter-spacing:0.1em;text-transform:uppercase;color:rgba(99,179,237,0.5);margin-bottom:4px}
.eq-f{font-family:'JetBrains Mono',monospace;font-size:0.82rem;color:rgba(210,230,255,0.75);line-height:1.5}
.eh{color:#FC8181;font-weight:600}.eg{color:#68D391}.eo{color:#F6AD55}

/* Expander */
details{margin-bottom:0.5rem}
summary{
  cursor:pointer;padding:10px 14px;border-radius:10px;
  background:rgba(255,255,255,0.025);border:1px solid rgba(255,255,255,0.07);
  font-size:0.8rem;font-weight:600;color:rgba(180,210,255,0.65);
  list-style:none;display:flex;align-items:center;gap:8px;
  transition:background 0.18s;
}
summary:hover{background:rgba(255,255,255,0.04);color:rgba(180,210,255,0.85)}
details[open] summary{border-radius:10px 10px 0 0;border-bottom-color:transparent}
.exp-body{
  padding:1rem 1.2rem;
  background:rgba(255,255,255,0.015);
  border:1px solid rgba(255,255,255,0.07);border-top:none;
  border-radius:0 0 10px 10px;
}
.param-grid{display:grid;grid-template-columns:repeat(5,1fr);gap:8px}
.param-cell{padding:0.7rem 0.8rem;background:rgba(255,255,255,0.02);border-radius:8px;border:1px solid rgba(255,255,255,0.06)}
.param-sym{font-size:1.1rem;font-weight:700;font-family:'JetBrains Mono',monospace;color:#63b3ed;display:block;margin-bottom:2px}
.param-val{font-size:0.88rem;font-weight:700;color:#fff;font-family:'JetBrains Mono',monospace;display:block;margin-bottom:2px}
.param-name{font-size:0.65rem;color:rgba(180,210,255,0.38)}

/* Canvas behind main */
#bg-canvas{position:fixed;inset:0;pointer-events:none;z-index:0;opacity:0.35}
.app-shell{position:relative;z-index:1}
</style>
</head>
<body>
<canvas id="bg-canvas"></canvas>

<div class="app-shell">

<!-- ══════════════════════ SIDEBAR ══════════════════════ -->
<aside class="sidebar">

  <div class="sb-logo">
    <span class="icon">🦠</span>
    <div class="brand">
      <span class="name">EpiSim</span>
      <span class="sub">Disease Spread Sim</span>
    </div>
  </div>

  <div class="sb-body">
    <div class="sb-section">Simulation Controls</div>

    <!-- Preset -->
    <div class="sb-select-wrap">
      <div class="sb-select-label">Disease preset</div>
      <select id="s-preset" onchange="applyPreset(this.value)">
        <option value="custom">Custom</option>
        <option value="covid" selected>COVID-19 (baseline)</option>
        <option value="flu">Influenza</option>
        <option value="ebola">Ebola-like</option>
        <option value="measles">Measles (unvaccinated)</option>
        <option value="plague">Black Plague</option>
      </select>
    </div>

    <div class="sb-divider"></div>
    <div class="sb-section">Population</div>

    <div class="ctrl">
      <div class="ctrl-top">
        <span class="ctrl-label">Population size</span>
        <span class="ctrl-val" id="v-pop">100,000</span>
      </div>
      <input type="range" id="s-pop" min="1000" max="1000000" step="1000" value="100000" oninput="onSlider('pop',this.value)"/>
    </div>
    <div class="ctrl">
      <div class="ctrl-top">
        <span class="ctrl-label">Initial infected</span>
        <span class="ctrl-val" id="v-i0">10</span>
      </div>
      <input type="range" id="s-i0" min="1" max="1000" step="1" value="10" oninput="onSlider('i0',this.value)"/>
    </div>

    <div class="sb-divider"></div>
    <div class="sb-section">Epidemiological Rates</div>

    <div class="ctrl">
      <div class="ctrl-top">
        <span class="ctrl-label">Transmission rate β <i class="tip" title="Higher β = faster spread">?</i></span>
        <span class="ctrl-val" id="v-beta">0.30</span>
      </div>
      <input type="range" id="s-beta" min="0.01" max="2.00" step="0.01" value="0.30" oninput="onSlider('beta',this.value)"/>
      <span class="ctrl-hint">Higher β → faster spread</span>
    </div>
    <div class="ctrl">
      <div class="ctrl-top">
        <span class="ctrl-label">Incubation rate σ <i class="tip" title="1/σ = mean incubation days">?</i></span>
        <span class="ctrl-val" id="v-sigma">0.20</span>
      </div>
      <input type="range" id="s-sigma" min="0.01" max="1.00" step="0.01" value="0.20" oninput="onSlider('sigma',this.value)"/>
      <span class="ctrl-hint">1/σ = mean incubation days</span>
    </div>
    <div class="ctrl">
      <div class="ctrl-top">
        <span class="ctrl-label">Recovery rate γ <i class="tip" title="1/γ = mean infectious days">?</i></span>
        <span class="ctrl-val" id="v-gamma">0.07</span>
      </div>
      <input type="range" id="s-gamma" min="0.01" max="0.80" step="0.01" value="0.07" oninput="onSlider('gamma',this.value)"/>
      <span class="ctrl-hint">1/γ = mean infectious days</span>
    </div>
    <div class="ctrl">
      <div class="ctrl-top">
        <span class="ctrl-label">Case fatality rate μ <i class="tip" title="Fraction of I-days ending in death">?</i></span>
        <span class="ctrl-val" id="v-mu">0.005</span>
      </div>
      <input type="range" id="s-mu" min="0.000" max="0.15" step="0.001" value="0.005" oninput="onSlider('mu',this.value)"/>
    </div>

    <div class="sb-divider"></div>
    <div class="sb-section">Interventions</div>

    <div class="ctrl">
      <div class="ctrl-top">
        <span class="ctrl-label">Vaccination coverage <i class="tip" title="% immunised at day 0">?</i></span>
        <span class="ctrl-val" id="v-vax">0%</span>
      </div>
      <input type="range" id="s-vax" min="0" max="0.95" step="0.01" value="0" oninput="onSlider('vax',this.value)"/>
      <span class="ctrl-hint">Fraction immunised at day 0</span>
    </div>
    <div class="ctrl">
      <div class="ctrl-top">
        <span class="ctrl-label">Distancing reduction δ <i class="tip" title="Reduces β by δ fraction">?</i></span>
        <span class="ctrl-val" id="v-dist">0%</span>
      </div>
      <input type="range" id="s-dist" min="0" max="0.90" step="0.01" value="0" oninput="onSlider('dist',this.value)"/>
      <span class="ctrl-hint">Fractional reduction in β</span>
    </div>

    <div class="sb-divider"></div>
    <div class="sb-section">Healthcare Capacity</div>

    <div class="ctrl">
      <div class="ctrl-top">
        <span class="ctrl-label">Hospitalisation rate <i class="tip" title="Fraction of infectious needing a hospital bed">?</i></span>
        <span class="ctrl-val" id="v-hosp">6%</span>
      </div>
      <input type="range" id="s-hosp" min="0" max="1.00" step="0.01" value="0.06" oninput="onSlider('hosp',this.value)"/>
    </div>
    <div class="ctrl">
      <div class="ctrl-top">
        <span class="ctrl-label">ICU beds (per 100k) <i class="tip" title="ICU beds per 100,000 people">?</i></span>
        <span class="ctrl-val" id="v-icu">300</span>
      </div>
      <input type="range" id="s-icu" min="10" max="3000" step="10" value="300" oninput="onSlider('icu',this.value)"/>
    </div>

    <div class="sb-divider"></div>
    <div class="sb-section">Simulation</div>

    <div class="ctrl">
      <div class="ctrl-top">
        <span class="ctrl-label">Days to simulate</span>
        <span class="ctrl-val" id="v-days">180</span>
      </div>
      <input type="range" id="s-days" min="30" max="730" step="5" value="180" oninput="onSlider('days',this.value)"/>
    </div>
    <div class="ctrl">
      <div class="ctrl-top">
        <span class="ctrl-label">Monte Carlo runs <i class="tip" title="0 = disabled. Adds 95% CI band to infectious curve">?</i></span>
        <span class="ctrl-val" id="v-mc">0</span>
      </div>
      <input type="range" id="s-mc" min="0" max="200" step="10" value="0" oninput="onSlider('mc',this.value)"/>
      <span class="ctrl-hint">0 = off · adds 95% CI band</span>
    </div>

  </div><!-- sb-body -->

  <div class="sb-status"><span class="sb-dot"></span>Live Simulation Engine</div>
</aside>

<!-- ══════════════════════ MAIN ══════════════════════════ -->
<main class="main">

  <!-- Top bar -->
  <div class="topbar">
    <div class="top-title">
      <span style="font-size:2rem;filter:drop-shadow(0 0 10px rgba(99,179,237,0.6))">🦠</span>
      <h1>EpiSim — Disease Spread Simulation</h1>
    </div>
    <p class="top-sub">
      Interactive <strong>SEIRD</strong> epidemic modelling · Explore transmission, vaccination,
      social distancing, fatality rates, and ICU capacity.
    </p>
  </div>

  <!-- Tabs -->
  <div class="tabs">
    <div class="tab active" onclick="switchTab('sim',this)">📈 Simulation</div>
    <div class="tab" onclick="switchTab('cmp',this)">⚖️ Comparison</div>
    <div class="tab" onclick="switchTab('data',this)">📋 Data &amp; Export</div>
  </div>

  <!-- ── TAB: Simulation ─────────────────────────────────────────────── -->
  <div class="tab-panel active" id="tp-sim">

    <!-- Alert -->
    <div id="alert-bar" class="alert-bar alert-danger">
      🔴 <span id="alert-txt">Calculating…</span>
    </div>

    <!-- Metrics -->
    <div class="metrics-row">
      <div class="mcard">
        <div class="ml">R₀ (effective)</div>
        <div class="mv" id="mv-r0">—</div>
        <span class="md" id="md-r0">—</span>
      </div>
      <div class="mcard">
        <div class="ml">Peak infected</div>
        <div class="mv" id="mv-peak">—</div>
        <span class="md md-neutral" id="md-peak">—</span>
      </div>
      <div class="mcard">
        <div class="ml">Peak hospitalised</div>
        <div class="mv" id="mv-hosp2">—</div>
        <span class="md" id="md-hosp2">—</span>
      </div>
      <div class="mcard">
        <div class="ml">Total deaths</div>
        <div class="mv" id="mv-deaths">—</div>
        <span class="md md-neutral" id="md-deaths">—</span>
      </div>
      <div class="mcard">
        <div class="ml">Final recovered</div>
        <div class="mv" id="mv-rec">—</div>
        <span class="md md-neutral" id="md-rec">—</span>
      </div>
      <div class="mcard">
        <div class="ml">Attack rate</div>
        <div class="mv" id="mv-atk">—</div>
        <span class="md md-neutral">% of population</span>
      </div>
    </div>

    <!-- Chart -->
    <div class="section-hdr"><span class="section-hdr-txt">📈 SEIRD Epidemic Curve</span><div class="section-hdr-line"></div></div>
    <div class="chart-wrap">
      <div class="chart-hdr">
        <div>
          <div class="chart-ttl" id="chart-ttl">SEIRD Epidemic Curve</div>
          <div class="chart-sub" id="chart-sub">—</div>
        </div>
        <div class="legend">
          <span class="li"><span class="ld" style="background:#4C9BE8"></span>Susceptible</span>
          <span class="li"><span class="ld" style="background:#F6AD55"></span>Exposed</span>
          <span class="li"><span class="ld" style="background:#FC8181"></span>Infectious</span>
          <span class="li"><span class="ld" style="background:#68D391"></span>Recovered</span>
          <span class="li"><span class="ld" style="background:#C53030"></span>Deaths</span>
          <span class="li"><span class="ldash" style="border-color:#F6AD55"></span>Hospitalised</span>
        </div>
      </div>
      <div id="chart-main" style="height:460px"></div>
    </div>

    <!-- Scenario params expander -->
    <details>
      <summary>🔬 Scenario Parameters</summary>
      <div class="exp-body">
        <div class="param-grid" id="param-display"></div>
      </div>
    </details>

    <!-- Model info -->
    <div style="margin-top:1.5rem">
      <div class="section-hdr"><span class="section-hdr-txt">🔬 SEIRD Model</span><div class="section-hdr-line"></div></div>
      <div class="model-grid">
        <div class="comps">
          <div class="comp"><div class="cl cl-S">S</div><div><div class="cn">Susceptible</div><div class="cd">Not yet infected — can contract the disease.</div></div></div>
          <div class="comp"><div class="cl cl-E">E</div><div><div class="cn">Exposed</div><div class="cd">Incubating — infected but not yet infectious.</div></div></div>
          <div class="comp"><div class="cl cl-I">I</div><div><div class="cn">Infectious</div><div class="cd">Actively spreading to susceptible contacts.</div></div></div>
          <div class="comp"><div class="cl cl-R">R</div><div><div class="cn">Recovered</div><div class="cd">Recovered with immunity — removed from chain.</div></div></div>
          <div class="comp"><div class="cl cl-D">D</div><div><div class="cn">Deceased</div><div class="cd">Died — permanently removed from population.</div></div></div>
        </div>
        <div class="eqs">
          <div class="eq"><div class="eq-l">dS/dt</div><div class="eq-f">dS/dt = <span class="eh">−β·S·I / N</span></div></div>
          <div class="eq"><div class="eq-l">dE/dt</div><div class="eq-f">dE/dt = <span class="eh">+β·S·I/N</span> <span class="eo">− σ·E</span></div></div>
          <div class="eq"><div class="eq-l">dI/dt</div><div class="eq-f">dI/dt = <span class="eo">+σ·E</span> <span class="eh">− (γ+μ)·I</span></div></div>
          <div class="eq"><div class="eq-l">dR/dt</div><div class="eq-f">dR/dt = <span class="eg">+γ·I</span></div></div>
          <div class="eq"><div class="eq-l">dD/dt</div><div class="eq-f">dD/dt = <span style="color:#C53030;font-weight:600">+μ·I</span></div></div>
          <div class="eq" style="background:rgba(99,179,237,0.03);border-color:rgba(99,179,237,0.12)">
            <div class="eq-l" style="color:rgba(99,179,237,0.55)">Solver</div>
            <div class="eq-f" style="color:rgba(180,210,255,0.6)">4th-order Runge-Kutta (RK4) · Δt=0.5 day · in-browser</div>
          </div>
        </div>
      </div>
    </div>

  </div><!-- tp-sim -->

  <!-- ── TAB: Comparison ────────────────────────────────────────────────── -->
  <div class="tab-panel" id="tp-cmp">
    <p style="font-size:0.82rem;color:rgba(180,210,255,0.45);margin-bottom:1rem">
      Compares your current intervention settings against the no-intervention baseline.
      Adjust vaccination or distancing sliders in the sidebar.
    </p>
    <div class="compare-grid">
      <div class="cmp-panel">
        <div class="cmp-hdr cmp-baseline">🔴 Baseline (no intervention)</div>
        <div class="cmp-stats" id="cmp-left-stats"></div>
        <div class="chart-wrap" style="padding:0.8rem 0.8rem 0">
          <div id="chart-cmp-left" style="height:320px"></div>
        </div>
      </div>
      <div class="cmp-panel">
        <div class="cmp-hdr cmp-scenario">🟢 With Intervention</div>
        <div class="cmp-stats" id="cmp-right-stats"></div>
        <div class="chart-wrap" style="padding:0.8rem 0.8rem 0">
          <div id="chart-cmp-right" style="height:320px"></div>
        </div>
      </div>
    </div>
    <div id="lives-banner" class="lives-banner lbi">—</div>
  </div>

  <!-- ── TAB: Data & Export ─────────────────────────────────────────────── -->
  <div class="tab-panel" id="tp-data">
    <div class="section-hdr"><span class="section-hdr-txt">📋 Raw Simulation Data</span><div class="section-hdr-line"></div></div>
    <div class="data-table-wrap">
      <table id="data-table">
        <thead>
          <tr>
            <th>Day</th><th>Susceptible</th><th>Exposed</th>
            <th>Infectious</th><th>Recovered</th><th>Deaths</th><th>Hospitalised</th>
          </tr>
        </thead>
        <tbody id="data-tbody"></tbody>
      </table>
    </div>
    <a class="dl-btn" id="dl-csv" href="#" download="episim_results.csv">⬇ Download CSV</a>
  </div>

</main><!-- .main -->
</div><!-- .app-shell -->

<script>
// ═══════════════════════════════════════════════════════════
//  STATE
// ═══════════════════════════════════════════════════════════
const P = {
  pop:100000,i0:10,
  beta:0.30,sigma:0.20,gamma:0.07,mu:0.005,
  vax:0.0,dist:0.0,hosp:0.06,icu:300,days:180,mc:0,
};

// ═══════════════════════════════════════════════════════════
//  PRESETS
// ═══════════════════════════════════════════════════════════
const PRESETS = {
  covid:   {pop:100000,i0:10, beta:0.30,sigma:0.20,gamma:0.07,mu:0.005, vax:0,dist:0,hosp:0.06,icu:300,days:180},
  flu:     {pop:100000,i0:20, beta:0.25,sigma:0.50,gamma:0.20,mu:0.001, vax:0,dist:0,hosp:0.02,icu:300,days:90 },
  ebola:   {pop:50000, i0:5,  beta:0.18,sigma:0.12,gamma:0.07,mu:0.04,  vax:0,dist:0,hosp:0.80,icu:100,days:120},
  measles: {pop:200000,i0:5,  beta:0.90,sigma:0.25,gamma:0.14,mu:0.0005,vax:0,dist:0,hosp:0.01,icu:300,days:120},
  plague:  {pop:100000,i0:3,  beta:0.40,sigma:0.14,gamma:0.05,mu:0.06,  vax:0,dist:0,hosp:0.90,icu:80, days:365},
};

function applyPreset(key) {
  if (!PRESETS[key]) return;
  Object.assign(P, PRESETS[key]);
  const fmts = {
    pop: fmtNum, i0: x=>x, beta: x=>x.toFixed(2), sigma: x=>x.toFixed(2),
    gamma: x=>x.toFixed(2), mu: x=>x.toFixed(3),
    vax: pct, dist: pct, hosp: pct, icu: x=>x, days: x=>x, mc: x=>x,
  };
  Object.keys(fmts).forEach(k => {
    const s = document.getElementById('s-'+k);
    const v = document.getElementById('v-'+k);
    if (s) s.value = P[k];
    if (v) v.textContent = fmts[k](P[k]);
  });
  scheduleRun();
}

// ═══════════════════════════════════════════════════════════
//  SLIDER
// ═══════════════════════════════════════════════════════════
function onSlider(key, raw) {
  const v = parseFloat(raw);
  P[key] = v;
  const fmts = {
    pop: fmtNum, i0: x=>x, beta: x=>x.toFixed(2), sigma: x=>x.toFixed(2),
    gamma: x=>x.toFixed(2), mu: x=>x.toFixed(3),
    vax: pct, dist: pct, hosp: pct, icu: x=>x, days: x=>x, mc: x=>x,
  };
  document.getElementById('v-'+key).textContent = fmts[key](v);
  document.getElementById('s-preset').value = 'custom';
  scheduleRun();
}

let dbt = null;
function scheduleRun(){clearTimeout(dbt);dbt=setTimeout(runSim,80);}

// ═══════════════════════════════════════════════════════════
//  RK4 SEIRD SOLVER
// ═══════════════════════════════════════════════════════════
function solveSEIRD(N,I0,beta,sigma,gamma,mu,vaccinated,days,dt=0.5) {
  const steps = Math.round(days/dt)+1;
  const S0=N-I0-vaccinated, E0=0, R0v=vaccinated, D0=0;
  let S=S0,E=E0,I=parseFloat(I0),R=R0v,D=D0;
  const out={t:[],S:[],E:[],I:[],R:[],D:[]};

  function d(S,E,I) {
    const inf=beta*S*I/N;
    return {dS:-inf,dE:inf-sigma*E,dI:sigma*E-(gamma+mu)*I,dR:gamma*I,dD:mu*I};
  }
  for(let i=0;i<steps;i++){
    out.t.push(+(i*dt).toFixed(2));
    out.S.push(Math.max(0,S));out.E.push(Math.max(0,E));
    out.I.push(Math.max(0,I));out.R.push(Math.max(0,R));out.D.push(Math.max(0,D));
    const k1=d(S,E,I);
    const k2=d(S+dt/2*k1.dS,E+dt/2*k1.dE,I+dt/2*k1.dI);
    const k3=d(S+dt/2*k2.dS,E+dt/2*k2.dE,I+dt/2*k2.dI);
    const k4=d(S+dt*k3.dS,E+dt*k3.dE,I+dt*k3.dI);
    S+=dt/6*(k1.dS+2*k2.dS+2*k3.dS+k4.dS);
    E+=dt/6*(k1.dE+2*k2.dE+2*k3.dE+k4.dE);
    I+=dt/6*(k1.dI+2*k2.dI+2*k3.dI+k4.dI);
    R+=dt/6*(k1.dR+2*k2.dR+2*k3.dR+k4.dR);
    D+=dt/6*(k1.dD+2*k2.dD+2*k3.dD+k4.dD);
  }
  return out;
}

// Monte Carlo
function runMC(N,I0,beta,sigma,gamma,mu,days,n) {
  if(!n) return null;
  const runs=[];
  for(let i=0;i<n;i++){
    function noise(v){return Math.max(0,v*(1+(Math.random()*2-1)*0.05));}
    const r=solveSEIRD(N,I0,noise(beta),noise(sigma),noise(gamma),noise(mu),0,days);
    runs.push(r.I);
  }
  const len=runs[0].length;
  const mean=[],lo=[],hi=[];
  for(let j=0;j<len;j++){
    const col=runs.map(r=>r[j]).sort((a,b)=>a-b);
    mean.push(col.reduce((s,v)=>s+v,0)/col.length);
    lo.push(col[Math.floor(col.length*0.025)]);
    hi.push(col[Math.floor(col.length*0.975)]);
  }
  return {mean,lo,hi};
}

// ═══════════════════════════════════════════════════════════
//  CHART HELPERS
// ═══════════════════════════════════════════════════════════
const LAYOUT_BASE = {
  paper_bgcolor:'rgba(0,0,0,0)',plot_bgcolor:'rgba(0,0,0,0)',
  font:{family:'Inter,sans-serif',color:'rgba(180,210,255,0.6)',size:11},
  margin:{l:55,r:20,t:10,b:45},
  hovermode:'x unified',
  hoverlabel:{bgcolor:'rgba(6,12,30,0.96)',bordercolor:'rgba(99,179,237,0.25)',font:{family:'Inter',size:11}},
  xaxis:{title:'Day',showgrid:true,gridcolor:'rgba(255,255,255,0.04)',zeroline:false,linecolor:'rgba(255,255,255,0.07)'},
  yaxis:{title:'People',showgrid:true,gridcolor:'rgba(255,255,255,0.04)',zeroline:false,linecolor:'rgba(255,255,255,0.07)'},
  legend:{orientation:'h',yanchor:'bottom',y:1.01,xanchor:'right',x:1,bgcolor:'rgba(0,0,0,0)',font:{size:10}},
};

function mkTrace(x,y,name,color,fill,dash,w){
  return {x,y,name,type:'scatter',mode:'lines',
    fill:fill?'tozeroy':'none',fillcolor:fill||'rgba(0,0,0,0)',
    line:{color,width:w||2.3,dash:dash||'solid'},
    hovertemplate:`<b>${name}</b>: %{y:,.0f}<br>Day %{x:.1f}<extra></extra>`};
}

function icuShapes(icuAbs){
  return {
    shapes:[{type:'line',xref:'paper',x0:0,x1:1,yref:'y',y0:icuAbs,y1:icuAbs,
      line:{color:'rgba(252,129,129,0.45)',width:1.4,dash:'dash'}}],
    annotations:[{xref:'paper',x:0.99,yref:'y',y:icuAbs,
      text:`⚠ ICU (${fmtNum(icuAbs)})`,showarrow:false,
      font:{size:10,color:'rgba(252,129,129,0.7)'},xanchor:'right',yanchor:'bottom'}]
  };
}

let chartInitMain=false,chartInitL=false,chartInitR=false;

function plotMain(res, hospArr, icuAbs, mc){
  const traces=[
    mkTrace(res.t,res.S,'Susceptible','#4C9BE8','rgba(76,155,232,0.07)'),
    mkTrace(res.t,res.E,'Exposed','#F6AD55','rgba(246,173,85,0.07)'),
    mkTrace(res.t,res.I,'Infectious','#FC8181','rgba(252,129,129,0.11)'),
    mkTrace(res.t,res.R,'Recovered','#68D391','rgba(104,211,145,0.07)'),
    mkTrace(res.t,res.D,'Deaths','#C53030','rgba(197,48,48,0.09)'),
    mkTrace(res.t,hospArr,'Hospitalised','#F6AD55',null,'dot',1.7),
  ];
  if(mc){
    traces.push({x:res.t,y:mc.hi,type:'scatter',mode:'lines',line:{color:'rgba(252,129,129,0)'},showlegend:false});
    traces.push({x:res.t,y:mc.lo,type:'scatter',mode:'lines',fill:'tonexty',
      fillcolor:'rgba(252,129,129,0.1)',line:{color:'rgba(252,129,129,0)'},name:'95% CI'});
    traces.push(mkTrace(res.t,mc.mean,'MC Mean','#FC8181',null,'dash',1.2));
  }
  const layout=Object.assign({},LAYOUT_BASE,icuShapes(icuAbs),{height:460});
  if(!chartInitMain){Plotly.newPlot('chart-main',traces,layout,{responsive:true,displayModeBar:false});chartInitMain=true;}
  else Plotly.react('chart-main',traces,layout);
}

function plotCmpSide(elId, res, icuAbs, init, setInit){
  const traces=[
    mkTrace(res.t,res.S,'Susceptible','#4C9BE8','rgba(76,155,232,0.07)'),
    mkTrace(res.t,res.I,'Infectious','#FC8181','rgba(252,129,129,0.11)'),
    mkTrace(res.t,res.R,'Recovered','#68D391','rgba(104,211,145,0.07)'),
    mkTrace(res.t,res.D,'Deaths','#C53030','rgba(197,48,48,0.09)'),
  ];
  const layout=Object.assign({},LAYOUT_BASE,icuShapes(icuAbs),{height:320,margin:{l:45,r:14,t:8,b:40}});
  if(!init){Plotly.newPlot(elId,traces,layout,{responsive:true,displayModeBar:false});setInit(true);}
  else Plotly.react(elId,traces,layout);
}

let cmpLInit=false,cmpRInit=false;

// ═══════════════════════════════════════════════════════════
//  MAIN RUN
// ═══════════════════════════════════════════════════════════
let lastRes=null;

function runSim(){
  const N=P.pop;
  const I0=Math.min(P.i0,N-1);
  const effBeta=P.beta*(1-P.dist);
  const vacc=Math.min(Math.round(N*P.vax),N-I0-1);
  const icuAbs=Math.round(P.icu*N/100000);
  const hospR=P.hosp;

  const res=solveSEIRD(N,I0,effBeta,P.sigma,P.gamma,P.mu,vacc,P.days);
  lastRes=res;
  const hospArr=res.I.map(v=>v*hospR);
  const peakI=Math.max(...res.I);
  const peakIdx=res.I.indexOf(peakI);
  const peakDay=res.t[peakIdx];
  const peakH=peakI*hospR;
  const totD=res.D[res.D.length-1];
  const totR=res.R[res.R.length-1];
  const atk=100*(totR+totD)/N;
  const r0=effBeta/(P.gamma+P.mu);
  const icuOver=peakH>icuAbs;
  const cfr=100*P.mu/(P.mu+P.gamma);

  // MC
  const mc=runMC(N,I0,effBeta,P.sigma,P.gamma,P.mu,P.days,P.mc);

  // ── Metrics ──────────────────────────────────────────────
  setText('mv-r0',r0.toFixed(2));
  setText('mv-peak',fmtNum(Math.round(peakI)));
  setText('mv-hosp2',fmtNum(Math.round(peakH)));
  setText('mv-deaths',fmtNum(Math.round(totD)));
  setText('mv-rec',fmtNum(Math.round(totR)));
  setText('mv-atk',atk.toFixed(1)+'%');
  setText('md-peak','Day '+Math.round(peakDay));
  setText('md-deaths','CFR '+cfr.toFixed(1)+'%');
  setText('md-rec',+(100*totR/N).toFixed(1)+'% of pop');

  const r0el=document.getElementById('md-r0');
  if(r0>1){r0el.textContent='🔴 Epidemic grows';r0el.className='md md-danger';}
  else{r0el.textContent='🟢 Epidemic dies out';r0el.className='md md-safe';}

  const hel=document.getElementById('md-hosp2');
  if(icuOver){hel.textContent='🔴 ICU EXCEEDED';hel.className='md md-danger';}
  else{hel.textContent='🟢 Within capacity';hel.className='md md-safe';}

  // Alert
  const ab=document.getElementById('alert-bar');
  const at=document.getElementById('alert-txt');
  if(r0>1&&icuOver){
    ab.className='alert-bar alert-danger';
    at.textContent=`R₀ = ${r0.toFixed(2)} — Epidemic grows. ICU exceeded by ${fmtNum(Math.round(peakH-icuAbs))} beds at peak.`;
  } else if(r0>1){
    ab.className='alert-bar alert-warn';
    at.textContent=`⚠️ R₀ = ${r0.toFixed(2)} — Epidemic spreading but ICU not exceeded. Monitor closely.`;
  } else {
    ab.className='alert-bar alert-safe';
    at.textContent=`✅ R₀ = ${r0.toFixed(2)} — Epidemic is contained and will die out.`;
  }

  // Chart title
  setText('chart-ttl','SEIRD Epidemic Curve');
  setText('chart-sub',`N=${fmtNum(N)} · ${P.days} days · β=${P.beta} σ=${P.sigma} γ=${P.gamma} μ=${P.mu} · R₀=${r0.toFixed(2)}`);

  plotMain(res,hospArr,icuAbs,mc);

  // Param display
  const params={
    'N (population)':fmtNum(N),'I₀ (initial)':I0,
    'β':P.beta.toFixed(2),'σ':P.sigma.toFixed(2),'γ':P.gamma.toFixed(2),
    'μ':P.mu.toFixed(3),'Vaccination':pct(P.vax),'Distancing':pct(P.dist),
    'Hosp. rate':pct(P.hosp),'ICU beds':fmtNum(icuAbs),
  };
  const pg=document.getElementById('param-display');
  pg.innerHTML=Object.entries(params).map(([k,v])=>
    `<div class="param-cell"><span class="param-sym">${k}</span><span class="param-val">${v}</span></div>`
  ).join('');

  // Comparison tab
  updateComparison(N,I0,icuAbs,r0,peakI,peakDay,peakH,totD,totR,atk,res,icuOver);

  // Data table
  updateTable(res,hospArr);
}

// ── Comparison ──────────────────────────────────────────────────────────
function updateComparison(N,I0,icuAbs,r0,peakI,peakDay,peakH,totD,totR,atk,res,icuOver){
  // Baseline: same params, no interventions
  const effBetaBl=P.beta;
  const blRes=solveSEIRD(N,I0,effBetaBl,P.sigma,P.gamma,P.mu,0,P.days);
  const blPeak=Math.max(...blRes.I);
  const blPeakDay=blRes.t[blRes.I.indexOf(blPeak)];
  const blD=blRes.D[blRes.D.length-1];
  const blR=blRes.R[blRes.R.length-1];
  const blAtk=100*(blR+blD)/N;
  const blR0=effBetaBl/(P.gamma+P.mu);

  function statRow(lbl,val){return `<div class="cmp-row"><span class="cmp-lbl">${lbl}</span><span class="cmp-val">${val}</span></div>`}
  function statRowD(lbl,val,delta,good){
    const cls=good?'style="color:#68d391"':'style="color:#fc8181"';
    return `<div class="cmp-row"><span class="cmp-lbl">${lbl}</span><span class="cmp-val">${val} <span ${cls} style="font-size:0.7rem">${delta}</span></span></div>`;
  }

  document.getElementById('cmp-left-stats').innerHTML=
    statRow('R₀',blR0.toFixed(2))+
    statRow('Peak infected',fmtNum(Math.round(blPeak)))+
    statRow('Peak day','Day '+Math.round(blPeakDay))+
    statRow('Total deaths',fmtNum(Math.round(blD)))+
    statRow('Attack rate',blAtk.toFixed(1)+'%');

  const saved=Math.round(blD-totD);
  const infAverted=Math.round(blPeak-peakI);
  document.getElementById('cmp-right-stats').innerHTML=
    statRowD('R₀',r0.toFixed(2),`(${(r0-blR0>=0?'+':'')+(r0-blR0).toFixed(2)})`,r0<=blR0)+
    statRowD('Peak infected',fmtNum(Math.round(peakI)),`(${(infAverted>=0?'-':'+')+fmtNum(Math.abs(infAverted))})`,infAverted>=0)+
    statRow('Peak day','Day '+Math.round(peakDay))+
    statRowD('Total deaths',fmtNum(Math.round(totD)),`(${(saved>=0?'-':'+')+fmtNum(Math.abs(saved))})`,saved>=0)+
    statRowD('Attack rate',atk.toFixed(1)+'%',`(${(atk-blAtk>=0?'+':'')+(atk-blAtk).toFixed(1)}%)`,atk<=blAtk);

  // Lives banner
  const lb=document.getElementById('lives-banner');
  if(saved>0){
    lb.className='lives-banner lbg';
    lb.innerHTML=`✅ Intervention saves an estimated <strong>${fmtNum(saved)} lives</strong> and averts <strong>${fmtNum(Math.max(0,infAverted))} peak infections</strong>.`;
  } else if(saved<0){
    lb.className='lives-banner lbd';
    lb.innerHTML=`⚠️ Current settings appear to <strong>increase deaths by ${fmtNum(Math.abs(saved))}</strong>. Review parameters.`;
  } else {
    lb.className='lives-banner lbi';
    lb.innerHTML='ℹ️ No difference in outcomes — try adjusting vaccination or distancing sliders.';
  }

  // Charts
  plotCmpSide('chart-cmp-left',blRes,icuAbs,cmpLInit,v=>{cmpLInit=v});
  plotCmpSide('chart-cmp-right',res,icuAbs,cmpRInit,v=>{cmpRInit=v});
}

// ── Data table ──────────────────────────────────────────────────────────
function updateTable(res, hospArr){
  const N=res.t.length;
  const stride=Math.max(1,Math.floor(N/100)); // max 100 rows
  let rows='',csvLines='Day,Susceptible,Exposed,Infectious,Recovered,Deaths,Hospitalised\n';
  for(let i=0;i<N;i+=stride){
    rows+=`<tr>
      <td>${res.t[i].toFixed(0)}</td>
      <td>${fmtNum(Math.round(res.S[i]))}</td>
      <td>${fmtNum(Math.round(res.E[i]))}</td>
      <td>${fmtNum(Math.round(res.I[i]))}</td>
      <td>${fmtNum(Math.round(res.R[i]))}</td>
      <td>${fmtNum(Math.round(res.D[i]))}</td>
      <td>${fmtNum(Math.round(hospArr[i]))}</td>
    </tr>`;
    csvLines+=`${res.t[i].toFixed(1)},${Math.round(res.S[i])},${Math.round(res.E[i])},${Math.round(res.I[i])},${Math.round(res.R[i])},${Math.round(res.D[i])},${Math.round(hospArr[i])}\n`;
  }
  document.getElementById('data-tbody').innerHTML=rows;
  const blob=new Blob([csvLines],{type:'text/csv'});
  document.getElementById('dl-csv').href=URL.createObjectURL(blob);
}

// ═══════════════════════════════════════════════════════════
//  TABS
// ═══════════════════════════════════════════════════════════
function switchTab(id,el){
  document.querySelectorAll('.tab').forEach(t=>t.classList.remove('active'));
  document.querySelectorAll('.tab-panel').forEach(p=>p.classList.remove('active'));
  el.classList.add('active');
  document.getElementById('tp-'+id).classList.add('active');
}

// ═══════════════════════════════════════════════════════════
//  UTILS
// ═══════════════════════════════════════════════════════════
function setText(id,txt){const e=document.getElementById(id);if(e)e.textContent=txt;}
function fmtNum(n){return n.toLocaleString();}
function pct(v){return Math.round(v*100)+'%';}

// ═══════════════════════════════════════════════════════════
//  PARTICLE BACKGROUND
// ═══════════════════════════════════════════════════════════
(function(){
  const cv=document.getElementById('bg-canvas');
  const ctx=cv.getContext('2d');
  let W,H,pts=[];
  function resize(){W=cv.width=innerWidth;H=cv.height=innerHeight;}
  function init(){
    pts=[];
    const n=Math.floor(W*H/20000);
    for(let i=0;i<n;i++)
      pts.push({x:Math.random()*W,y:Math.random()*H,r:Math.random()*1.3+0.3,
                vx:(Math.random()-.5)*.14,vy:(Math.random()-.5)*.14,a:Math.random()*.35+.06});
  }
  function draw(){
    ctx.clearRect(0,0,W,H);
    pts.forEach(p=>{
      ctx.beginPath();ctx.arc(p.x,p.y,p.r,0,Math.PI*2);
      ctx.fillStyle=`rgba(99,179,237,${p.a})`;ctx.fill();
      p.x+=p.vx;p.y+=p.vy;
      if(p.x<0)p.x=W;if(p.x>W)p.x=0;if(p.y<0)p.y=H;if(p.y>H)p.y=0;
    });
    requestAnimationFrame(draw);
  }
  resize();init();draw();
  addEventListener('resize',()=>{resize();init();});
})();

// ═══════════════════════════════════════════════════════════
//  BOOT
// ═══════════════════════════════════════════════════════════
applyPreset('covid');
</script>
</body>
</html>
"""

if __name__ == "__main__":
    out = Path(__file__).parent / "report" / "index.html"
    out.parent.mkdir(exist_ok=True)
    out.write_text(HTML, encoding="utf-8")
    print(f"Interactive simulator written to: {out}")
    print("Open report/index.html in any browser — no server needed.")
