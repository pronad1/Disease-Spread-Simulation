"""
episim.py — Core SEIRD epidemic simulation engine.

Model compartments:
  S  — Susceptible
  E  — Exposed (incubating, not yet infectious)
  I  — Infectious
  R  — Recovered (immune)
  D  — Deceased

Differential equations:
  dS/dt = -β·S·I/N
  dE/dt =  β·S·I/N - σ·E
  dI/dt =  σ·E - γ·I - μ·I
  dR/dt =  γ·I
  dD/dt =  μ·I

Parameters:
  β  (beta)  — transmission rate (contacts × prob. of transmission per contact)
  σ  (sigma) — incubation rate (1/σ = mean incubation period in days)
  γ  (gamma) — recovery rate (1/γ = mean infectious period in days)
  μ  (mu)    — case fatality rate per infectious-day
               (mortality = μ/(μ+γ) of infections end in death)
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Optional, Tuple

import numpy as np
from scipy.integrate import odeint


# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------

@dataclass
class SimulationResult:
    times: np.ndarray
    states: np.ndarray          # shape (days+1, 5): S E I R D
    peak_infected: float
    peak_day: int
    final_recovered: float
    total_deaths: float
    peak_hospitalized: float    # peak_infected * hospitalization_rate


# ---------------------------------------------------------------------------
# Low-level ODE solver
# ---------------------------------------------------------------------------

def simulate_seird(
    population: int,
    beta: float,
    sigma: float,
    gamma: float,
    mu: float,
    initial_infected: int,
    days: int,
    initial_recovered: int = 0,
    model_type: str = "SEIRD",
) -> Tuple[np.ndarray, np.ndarray]:
    """Solve the epidemic ODE system and return (times, states).

    Supports model_type: 'SEIRD', 'SEIR', 'SIR', 'SIS'.
    states columns: [Susceptible, Exposed, Infectious, Recovered, Dead]
    """
    if population <= 0:
        raise ValueError("population must be positive")
    if initial_infected <= 0:
        raise ValueError("initial_infected must be positive")
    if initial_infected >= population:
        raise ValueError("initial_infected must be smaller than population")
    if initial_recovered < 0:
        raise ValueError("initial_recovered must be non-negative")
    if initial_recovered > population - initial_infected:
        raise ValueError("initial_recovered exceeds remaining population")
    if mu < 0:
        raise ValueError("mu (case fatality rate) must be non-negative")

    times = np.linspace(0, days, days + 1)
    S0 = population - initial_infected - initial_recovered
    E0 = 0.0
    I0 = float(initial_infected)
    R0_val = float(initial_recovered)
    D0 = 0.0

    initial_state = [S0, E0, I0, R0_val, D0]
    model_upper = model_type.upper().split(" ")[0]

    def epidemic_system(state, _t):
        S, E, I, R, D = state
        N = population
        infection_rate = beta * S * I / N

        if model_upper == "SEIR":
            dS = -infection_rate
            dE = infection_rate - sigma * E
            dI = sigma * E - gamma * I
            dR = gamma * I
            dD = 0.0
        elif model_upper == "SIR":
            dS = -infection_rate
            dE = 0.0
            dI = infection_rate - gamma * I
            dR = gamma * I
            dD = 0.0
        elif model_upper == "SIS":
            dS = -infection_rate + gamma * I
            dE = 0.0
            dI = infection_rate - gamma * I
            dR = 0.0
            dD = 0.0
        else:  # Default SEIRD
            dS = -infection_rate
            dE = infection_rate - sigma * E
            dI = sigma * E - (gamma + mu) * I
            dR = gamma * I
            dD = mu * I

        return [dS, dE, dI, dR, dD]

    solution = odeint(epidemic_system, initial_state, times)
    return times, solution


# ---------------------------------------------------------------------------
# Backwards-compatible SEIR wrapper (kept so existing tests don't break)
# ---------------------------------------------------------------------------

def simulate_seir(
    population: int,
    beta: float,
    sigma: float,
    gamma: float,
    initial_infected: int,
    days: int,
    initial_recovered: int = 0,
) -> Tuple[np.ndarray, np.ndarray]:
    """Legacy 4-compartment SEIR wrapper — returns (times, states[S,E,I,R]).

    Internally uses SEIRD with mu=0 and strips the Deaths column so callers
    that expect a (days+1, 4) array continue to work unchanged.
    """
    times, states5 = simulate_seird(
        population=population,
        beta=beta,
        sigma=sigma,
        gamma=gamma,
        mu=0.0,
        initial_infected=initial_infected,
        days=days,
        initial_recovered=initial_recovered,
    )
    return times, states5[:, :4]   # drop Deaths column


# ---------------------------------------------------------------------------
# Scenario runner
# ---------------------------------------------------------------------------

def run_scenario(
    population: int,
    beta: float,
    sigma: float,
    gamma: float,
    initial_infected: int,
    days: int,
    mu: float = 0.005,
    vaccine_coverage: float = 0.0,
    distancing_reduction: float = 0.0,
    hospitalization_rate: float = 0.05,
    model_type: str = "SEIRD",
) -> Dict:
    """Run one epidemic scenario with optional vaccination, distancing, and
    case fatality / hospitalization rates across any supported model structure.

    Returns a dict with times, states, and summary statistics.
    """
    effective_beta = beta * (1.0 - distancing_reduction)
    vaccinated = int(round(population * vaccine_coverage))

    times, states = simulate_seird(
        population=population,
        beta=effective_beta,
        sigma=sigma,
        gamma=gamma,
        mu=mu,
        initial_infected=initial_infected,
        days=days,
        initial_recovered=vaccinated,
        model_type=model_type,
    )

    S, E, I, R, D = states.T
    peak_idx = int(np.argmax(I))
    peak_infected = float(I[peak_idx])
    peak_day = int(times[peak_idx])
    final_recovered = float(R[-1])
    total_deaths = float(D[-1])
    peak_hospitalized = peak_infected * hospitalization_rate

    # Basic reproduction number (effective, accounting for distancing)
    r0 = effective_beta / (gamma + mu) if (gamma + mu) > 0 else 0.0

    return {
        "times": times,
        "states": states,           # (days+1, 5): S E I R D
        "peak_infected": peak_infected,
        "peak_day": peak_day,
        "final_recovered": final_recovered,
        "total_deaths": total_deaths,
        "peak_hospitalized": peak_hospitalized,
        "r0": r0,
        "model_type": model_type,
    }


# ---------------------------------------------------------------------------
# Result summarizer
# ---------------------------------------------------------------------------

def summarize_results(result: Dict) -> SimulationResult:
    return SimulationResult(
        times=result["times"],
        states=result["states"],
        peak_infected=result["peak_infected"],
        peak_day=result["peak_day"],
        final_recovered=result["final_recovered"],
        total_deaths=result["total_deaths"],
        peak_hospitalized=result["peak_hospitalized"],
    )
