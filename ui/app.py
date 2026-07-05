from __future__ import annotations

import sys
from pathlib import Path

import streamlit as st
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from episim import run_scenario, simulate_seir
import plotly.graph_objects as go
import plotly.express as px
import io

st.set_page_config(page_title="EpiSim", page_icon="🦠", layout="wide")

# Hide the Streamlit Deploy button in the top bar if present
st.markdown(
    """
    <style>
    button[title="Deploy"],
    [data-testid="deploy-button"],
    button[data-testid="deploy-button"] {
        display: none !important;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

st.title("🦠 EpiSim — Disease Spread Simulation")
st.markdown("Interactive epidemic modeling for coursework and public health exploration.")

# Preset scenarios
PRESETS = {
    "Baseline": {},
    "Early Lockdown": {"distancing_reduction": 0.4},
    "Partial Vaccination (50%)": {"vaccine_coverage": 0.5},
}

with st.sidebar:
    st.header("Simulation Controls")
    preset = st.selectbox("Scenario preset", list(PRESETS.keys()))
    population = st.slider("Population", 500, 20000, 5000, 500)
    beta = st.slider("Transmission rate β", 0.1, 1.0, 0.3, 0.01)
    sigma = st.slider("Incubation rate σ", 0.05, 0.5, 0.2, 0.01)
    gamma = st.slider("Recovery rate γ", 0.02, 0.2, 0.1, 0.01)
    initial_infected = st.slider("Initial infected", 1, 100, 10, 1)
    days = st.slider("Simulation days", 30, 365, 120, 10)
    vaccine_coverage = st.slider("Vaccination coverage", 0.0, 0.95, PRESETS[preset].get("vaccine_coverage", 0.0), 0.05)
    distancing_reduction = st.slider("Distancing reduction", 0.0, 0.9, PRESETS[preset].get("distancing_reduction", 0.0), 0.05)
    monte_carlo_runs = st.number_input("Monte Carlo runs", min_value=0, max_value=1000, value=0, step=10)


def build_df(times, states):
    susceptible, exposed, infectious, recovered = states.T
    return pd.DataFrame({"time": times, "susceptible": susceptible, "exposed": exposed, "infectious": infectious, "recovered": recovered})


def plot_results(times, states, mc_summary=None):
    df = build_df(times, states)
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=df["time"], y=df["susceptible"], name="Susceptible", line=dict(color="#636EFA")))
    fig.add_trace(go.Scatter(x=df["time"], y=df["exposed"], name="Exposed", line=dict(color="#EF553B")))
    fig.add_trace(go.Scatter(x=df["time"], y=df["infectious"], name="Infectious", line=dict(color="#00CC96")))
    fig.add_trace(go.Scatter(x=df["time"], y=df["recovered"], name="Recovered", line=dict(color="#AB63FA")))

    # Monte Carlo shading
    if mc_summary is not None:
        mean_inf = mc_summary["mean"]
        lower = mc_summary["lower"]
        upper = mc_summary["upper"]
        fig.add_trace(go.Scatter(x=times, y=upper, line=dict(color="rgba(255,182,193,0)"), showlegend=False))
        fig.add_trace(go.Scatter(x=times, y=lower, fill="tonexty", fillcolor="rgba(255,182,193,0.2)", line=dict(color="rgba(255,182,193,0)"), name="95% CI"))
        fig.add_trace(go.Scatter(x=times, y=mean_inf, line=dict(color="#FF6692", dash="dash"), name="Mean Infectious"))

    fig.update_layout(template="plotly_dark", height=520, margin=dict(l=40, r=10, t=50, b=40))
    return fig


def run_and_render():
    result = run_scenario(
        population=population,
        beta=beta,
        sigma=sigma,
        gamma=gamma,
        initial_infected=initial_infected,
        days=days,
        vaccine_coverage=vaccine_coverage,
        distancing_reduction=distancing_reduction,
    )

    times = result["times"]
    states = result["states"]

    col1, col2, col3 = st.columns(3)
    col1.metric("Peak infected", f"{int(np.max(states[:,2]))}")
    col2.metric("Peak day", f"{int(times[np.argmax(states[:,2])])}")
    col3.metric("Final recovered", f"{int(states[-1,3])}")

    mc_summary = None
    if monte_carlo_runs and monte_carlo_runs > 0:
        all_inf = []
        for _ in range(int(monte_carlo_runs)):
            t_mc, s_mc = simulate_seir(
                population=population,
                beta=max(0, np.random.normal(beta, 0.05*beta)),
                sigma=max(0, np.random.normal(sigma, 0.05*sigma)),
                gamma=max(0, np.random.normal(gamma, 0.05*gamma)),
                initial_infected=initial_infected,
                days=days,
            )
            all_inf.append(s_mc[:,2])
        arr = np.vstack(all_inf)
        mc_summary = {
            "mean": arr.mean(axis=0),
            "lower": np.percentile(arr, 2.5, axis=0),
            "upper": np.percentile(arr, 97.5, axis=0),
        }

    fig = plot_results(times, states, mc_summary=mc_summary)
    st.plotly_chart(fig, use_container_width=True)

    # Data export
    df = build_df(times, states)
    csv = df.to_csv(index=False).encode("utf-8")
    st.download_button("Download results (CSV)", data=csv, file_name="episim_results.csv", mime="text/csv")

    # Scenario summary table
    summary = {
        "Population": population,
        "Beta": beta,
        "Sigma": sigma,
        "Gamma": gamma,
        "Initial infected": initial_infected,
        "Vaccination coverage": vaccine_coverage,
        "Distancing reduction": distancing_reduction,
        "Peak infected": int(np.max(states[:,2])),
        "Peak day": int(times[np.argmax(states[:,2])]),
        "Final recovered": int(states[-1,3]),
    }
    st.subheader("Scenario Summary")
    st.json(summary)


run_and_render()
