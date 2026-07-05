from __future__ import annotations

import sys
from pathlib import Path

import streamlit as st
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from episim import run_scenario

st.set_page_config(page_title="EpiSim", page_icon="🦠", layout="wide")
st.title("🦠 EpiSim — Disease Spread Simulation")
st.write("Interactive epidemic modeling for coursework and public health exploration.")

with st.sidebar:
    st.header("Simulation Controls")
    population = st.slider("Population", 500, 20000, 5000, 500)
    beta = st.slider("Transmission rate β", 0.1, 1.0, 0.3, 0.01)
    sigma = st.slider("Incubation rate σ", 0.05, 0.5, 0.2, 0.01)
    gamma = st.slider("Recovery rate γ", 0.02, 0.2, 0.1, 0.01)
    initial_infected = st.slider("Initial infected", 1, 100, 10, 1)
    days = st.slider("Simulation days", 30, 180, 120, 10)
    vaccine_coverage = st.slider("Vaccination coverage", 0.0, 0.8, 0.0, 0.05)
    distancing_reduction = st.slider("Distancing reduction", 0.0, 0.7, 0.0, 0.05)

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
susceptible, exposed, infectious, recovered = states.T

col1, col2, col3 = st.columns(3)
col1.metric("Peak infected", f"{int(np.max(infectious))}")
col2.metric("Peak day", f"{int(np.argmax(infectious))}")
col3.metric("Final recovered", f"{int(recovered[-1])}")

st.line_chart(pd.DataFrame({"Susceptible": susceptible, "Exposed": exposed, "Infectious": infectious, "Recovered": recovered}, index=times))

st.subheader("Scenario Summary")
st.dataframe(pd.DataFrame([{
    "Population": population,
    "Beta": beta,
    "Sigma": sigma,
    "Gamma": gamma,
    "Initial infected": initial_infected,
    "Vaccination coverage": vaccine_coverage,
    "Distancing reduction": distancing_reduction,
    "Peak infected": int(np.max(infectious)),
    "Peak day": int(np.argmax(infectious)),
    "Final recovered": int(recovered[-1]),
}]))
