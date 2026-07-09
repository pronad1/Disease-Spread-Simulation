"""
ui/app.py — EpiSim interactive Streamlit dashboard.

Features:
  • SEIRD visualisation (Susceptible, Exposed, Infectious, Recovered, Deaths)
  • Hospitalization curve vs. ICU capacity line
  • R₀ live display
  • Monte Carlo confidence-interval shading
  • Comparison tab (Baseline vs. Intervention side-by-side)
  • CSV download
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

# Make sure the project root is on the path when running via `streamlit run`
ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from episim import run_scenario, simulate_seird  # noqa: E402

# ---------------------------------------------------------------------------
# Page config
# ---------------------------------------------------------------------------
st.set_page_config(
    page_title="EpiSim — Disease Spread Simulation",
    page_icon="🦠",
    layout="wide",
)

# ---------------------------------------------------------------------------
# Custom CSS
# ---------------------------------------------------------------------------
st.markdown(
    """
    <style>
    /* Hide Deploy button */
    button[title="Deploy"],
    [data-testid="deploy-button"] { display: none !important; }

    /* Metric card polish */
    [data-testid="metric-container"] {
        background: rgba(255,255,255,0.04);
        border: 1px solid rgba(255,255,255,0.08);
        border-radius: 12px;
        padding: 12px 16px;
    }

    /* Sidebar header */
    section[data-testid="stSidebar"] h2 {
        color: #7DF9FF;
        font-size: 1.05rem;
        letter-spacing: 0.05em;
        text-transform: uppercase;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# ---------------------------------------------------------------------------
# Header
# ---------------------------------------------------------------------------
st.title("🦠 EpiSim — Disease Spread Simulation")
st.markdown(
    "Interactive **SEIRD** epidemic modelling · Explore transmission, "
    "vaccination, social distancing, fatality rates, and ICU capacity."
)

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
# Sidebar controls
# ---------------------------------------------------------------------------
with st.sidebar:
    st.header("Simulation Controls")

    preset = st.selectbox("Disease preset", list(PRESETS.keys()))
    p = PRESETS[preset]

    st.markdown("---")
    st.subheader("Population")
    population = st.slider("Population size", 500, 200_000, 50_000, 500)
    initial_infected = st.slider("Initial infected", 1, 500, 10, 1)

    st.markdown("---")
    st.subheader("Epidemiological rates")
    beta  = st.slider("Transmission rate β", 0.05, 1.50, p.get("beta",  0.30), 0.01,
                      help="Higher β → faster spread")
    sigma = st.slider("Incubation rate σ",   0.05, 1.00, p.get("sigma", 0.20), 0.01,
                      help="1/σ = mean incubation days")
    gamma = st.slider("Recovery rate γ",     0.02, 0.50, p.get("gamma", 0.10), 0.01,
                      help="1/γ = mean infectious days")
    mu    = st.slider("Case fatality rate μ", 0.000, 0.10, p.get("mu", 0.005), 0.001,
                      help="Fraction of infectious-days that end in death")

    st.markdown("---")
    st.subheader("Interventions")
    vaccine_coverage      = st.slider("Vaccination coverage",   0.00, 0.95, 0.0,  0.05,
                                      help="Fraction immunised at day 0")
    distancing_reduction  = st.slider("Distancing reduction",   0.00, 0.90, 0.0,  0.05,
                                      help="Fractional reduction in β")

    st.markdown("---")
    st.subheader("Healthcare capacity")
    hospitalization_rate = st.slider("Hospitalisation rate",   0.00, 1.00, p.get("hospitalization_rate", 0.05), 0.01,
                                     help="Fraction of infectious who need a hospital bed")
    icu_capacity         = st.slider("ICU beds (per 100 k)",   10, 2000, 300, 10,
                                     help="Number of ICU beds per 100,000 population")
    icu_beds_abs = int(icu_capacity * population / 100_000)

    st.markdown("---")
    st.subheader("Simulation")
    days              = st.slider("Days to simulate", 30, 730, p.get("days", 150), 10)
    monte_carlo_runs  = st.number_input("Monte Carlo runs (0 = off)",
                                        min_value=0, max_value=500, value=0, step=10)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
COLOURS = {
    "Susceptible": "#4C9BE8",
    "Exposed":     "#F4A261",
    "Infectious":  "#E63946",
    "Recovered":   "#2EC4B6",
    "Deaths":      "#9B2335",
    "Hospitalised":"#FF9F43",
}


def build_df(times: np.ndarray, states: np.ndarray) -> pd.DataFrame:
    """Convert raw ODE output to a labelled DataFrame."""
    S, E, I, R, D = states.T
    return pd.DataFrame({
        "Day":          times,
        "Susceptible":  S,
        "Exposed":      E,
        "Infectious":   I,
        "Recovered":    R,
        "Deaths":       D,
        "Hospitalised": I * hospitalization_rate,
    })


def build_fig(
    df: pd.DataFrame,
    icu_line: int,
    title: str = "",
    mc_summary: dict | None = None,
) -> go.Figure:
    """Build the SEIRD Plotly figure."""
    fig = go.Figure()

    for col in ["Susceptible", "Exposed", "Infectious", "Recovered", "Deaths"]:
        fig.add_trace(go.Scatter(
            x=df["Day"], y=df[col],
            name=col,
            line=dict(color=COLOURS[col], width=2),
            hovertemplate=f"<b>{col}</b>: %{{y:,.0f}}<br>Day %{{x}}<extra></extra>",
        ))

    # Hospitalised (dashed)
    fig.add_trace(go.Scatter(
        x=df["Day"], y=df["Hospitalised"],
        name="Hospitalised",
        line=dict(color=COLOURS["Hospitalised"], width=1.5, dash="dot"),
        hovertemplate="<b>Hospitalised</b>: %{y:,.0f}<br>Day %{x}<extra></extra>",
    ))

    # ICU capacity line
    fig.add_hline(
        y=icu_beds_abs,
        line_color="rgba(255,80,80,0.7)",
        line_dash="dash",
        line_width=1.5,
        annotation_text=f"ICU capacity ({icu_beds_abs:,})",
        annotation_position="top right",
        annotation_font_color="rgba(255,80,80,0.9)",
    )

    # Monte Carlo band
    if mc_summary is not None:
        times_arr = df["Day"].values
        fig.add_trace(go.Scatter(
            x=times_arr, y=mc_summary["upper"],
            line=dict(color="rgba(230,57,70,0)"), showlegend=False,
        ))
        fig.add_trace(go.Scatter(
            x=times_arr, y=mc_summary["lower"],
            fill="tonexty",
            fillcolor="rgba(230,57,70,0.15)",
            line=dict(color="rgba(230,57,70,0)"),
            name="95% CI (MC)",
        ))
        fig.add_trace(go.Scatter(
            x=times_arr, y=mc_summary["mean"],
            line=dict(color="#E63946", dash="dash", width=1),
            name="Mean Infectious (MC)",
        ))

    fig.update_layout(
        template="plotly_dark",
        title=title,
        height=520,
        margin=dict(l=40, r=20, t=60 if title else 40, b=40),
        legend=dict(orientation="h", yanchor="bottom", y=1.01, xanchor="right", x=1),
        hovermode="x unified",
        xaxis_title="Day",
        yaxis_title="People",
    )
    return fig


def run_mc(n_runs: int) -> dict | None:
    """Run Monte Carlo simulations with ±5% parameter noise."""
    if n_runs <= 0:
        return None
    all_inf = []
    for _ in range(n_runs):
        def noise(v): return max(0, np.random.normal(v, 0.05 * v))
        _, s = simulate_seird(
            population=population,
            beta=noise(beta) * (1 - distancing_reduction),
            sigma=noise(sigma),
            gamma=noise(gamma),
            mu=noise(mu),
            initial_infected=initial_infected,
            days=days,
        )
        all_inf.append(s[:, 2])
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
    population=population,
    beta=beta,
    sigma=sigma,
    gamma=gamma,
    mu=mu,
    initial_infected=initial_infected,
    days=days,
    vaccine_coverage=vaccine_coverage,
    distancing_reduction=distancing_reduction,
    hospitalization_rate=hospitalization_rate,
)

times  = result["times"]
states = result["states"]
df     = build_df(times, states)

r0          = result["r0"]
peak_inf    = result["peak_infected"]
peak_day    = result["peak_day"]
final_rec   = result["final_recovered"]
total_dth   = result["total_deaths"]
peak_hosp   = result["peak_hospitalized"]
icu_breached = peak_hosp > icu_beds_abs

# ---------------------------------------------------------------------------
# Tabs
# ---------------------------------------------------------------------------
tab_sim, tab_compare, tab_data = st.tabs(["📈 Simulation", "⚖️ Comparison", "📋 Data & Export"])

# ── Tab 1: Simulation ──────────────────────────────────────────────────────
with tab_sim:
    # Key metrics
    r0_delta = "🔴 Epidemic grows" if r0 > 1 else "🟢 Epidemic dies out"
    icu_label = "🔴 ICU EXCEEDED" if icu_breached else "🟢 Within capacity"

    c1, c2, c3, c4, c5, c6 = st.columns(6)
    c1.metric("R₀ (effective)", f"{r0:.2f}", r0_delta)
    c2.metric("Peak infected",  f"{int(peak_inf):,}",  f"Day {peak_day}")
    c3.metric("Peak hospitalised", f"{int(peak_hosp):,}", icu_label)
    c4.metric("Total deaths",   f"{int(total_dth):,}")
    c5.metric("Final recovered", f"{int(final_rec):,}")
    c6.metric("Attack rate",
              f"{100 * (final_rec + total_dth) / population:.1f}%",
              help="% of population infected")

    # Monte Carlo
    mc = run_mc(int(monte_carlo_runs))

    # Chart
    fig = build_fig(df, icu_beds_abs, mc_summary=mc)
    st.plotly_chart(fig, use_container_width=True)

    # Scenario parameters summary
    with st.expander("🔬 Scenario parameters"):
        pcols = st.columns(4)
        params = {
            "Population": f"{population:,}", "Initial infected": initial_infected,
            "β (transmission)": beta, "σ (incubation)": sigma,
            "γ (recovery)": gamma, "μ (fatality)": mu,
            "Vaccination coverage": f"{vaccine_coverage:.0%}",
            "Distancing reduction": f"{distancing_reduction:.0%}",
            "Hospitalisation rate": f"{hospitalization_rate:.0%}",
            "ICU beds": f"{icu_beds_abs:,}",
        }
        items = list(params.items())
        for i, (k, v) in enumerate(items):
            pcols[i % 4].markdown(f"**{k}:** {v}")

# ── Tab 2: Comparison ──────────────────────────────────────────────────────
with tab_compare:
    st.markdown("### Baseline vs. Intervention comparison")
    st.caption("Adjust intervention sliders in the sidebar, then compare against the no-intervention baseline below.")

    baseline = run_scenario(
        population=population, beta=beta, sigma=sigma, gamma=gamma, mu=mu,
        initial_infected=initial_infected, days=days,
        vaccine_coverage=0.0, distancing_reduction=0.0,
        hospitalization_rate=hospitalization_rate,
    )
    bl_df = build_df(baseline["times"], baseline["states"])

    left, right = st.columns(2)

    with left:
        st.subheader("🔴 Baseline (no intervention)")
        bl_m = baseline
        st.metric("R₀", f"{bl_m['r0']:.2f}")
        st.metric("Peak infected", f"{int(bl_m['peak_infected']):,}")
        st.metric("Total deaths",  f"{int(bl_m['total_deaths']):,}")
        st.plotly_chart(
            build_fig(bl_df, icu_beds_abs, title="No Intervention"),
            use_container_width=True,
        )

    with right:
        st.subheader("🟢 With intervention")
        st.metric("R₀", f"{r0:.2f}",
                  delta=f"{r0 - bl_m['r0']:+.2f}", delta_color="inverse")
        st.metric("Peak infected", f"{int(peak_inf):,}",
                  delta=f"{int(peak_inf - bl_m['peak_infected']):+,}", delta_color="inverse")
        st.metric("Total deaths",  f"{int(total_dth):,}",
                  delta=f"{int(total_dth - bl_m['total_deaths']):+,}", delta_color="inverse")
        st.plotly_chart(
            build_fig(df, icu_beds_abs, title="With Intervention"),
            use_container_width=True,
        )

    # Lives saved summary
    lives_saved = int(bl_m["total_deaths"] - total_dth)
    if lives_saved > 0:
        st.success(f"✅ Intervention saves an estimated **{lives_saved:,} lives** and reduces peak infections by **{int(bl_m['peak_infected'] - peak_inf):,}** people.")
    elif lives_saved == 0:
        st.info("No difference in outcomes — try adjusting vaccination or distancing.")
    else:
        st.warning("Intervention appears to increase deaths — check parameter values.")

# ── Tab 3: Data & Export ───────────────────────────────────────────────────
with tab_data:
    st.markdown("### Raw simulation data")
    st.dataframe(
        df.style.format({c: "{:,.1f}" for c in df.columns if c != "Day"}),
        use_container_width=True,
        height=400,
    )

    csv_bytes = df.to_csv(index=False).encode("utf-8")
    st.download_button(
        label="⬇️ Download CSV",
        data=csv_bytes,
        file_name="episim_results.csv",
        mime="text/csv",
    )
