from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Tuple

import numpy as np
from scipy.integrate import odeint


@dataclass
class SimulationResult:
    times: np.ndarray
    states: np.ndarray
    peak_infected: float
    peak_day: int
    final_recovered: float


def simulate_seir(
    population: int,
    beta: float,
    sigma: float,
    gamma: float,
    initial_infected: int,
    days: int,
    initial_recovered: int = 0,
) -> Tuple[np.ndarray, np.ndarray]:
    """Simulate the SEIR model over a number of days."""
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

    times = np.linspace(0, days, days + 1)
    susceptible0 = population - initial_infected - initial_recovered
    exposed0 = 0
    infectious0 = initial_infected
    recovered0 = initial_recovered

    initial_state = [susceptible0, exposed0, infectious0, recovered0]

    def seir_system(state, _t):
        susceptible, exposed, infectious, recovered = state
        d_susceptible = -beta * susceptible * infectious / population
        d_exposed = beta * susceptible * infectious / population - sigma * exposed
        d_infectious = sigma * exposed - gamma * infectious
        d_recovered = gamma * infectious
        return [d_susceptible, d_exposed, d_infectious, d_recovered]

    solution = odeint(seir_system, initial_state, times)
    return times, solution


def run_scenario(
    population: int,
    beta: float,
    sigma: float,
    gamma: float,
    initial_infected: int,
    days: int,
    vaccine_coverage: float = 0.0,
    distancing_reduction: float = 0.0,
) -> Dict[str, float]:
    """Run one scenario with optional vaccination and distancing."""
    effective_beta = beta * (1 - distancing_reduction)
    vaccinated = int(round(population * vaccine_coverage))

    times, states = simulate_seir(
        population=population,
        beta=effective_beta,
        sigma=sigma,
        gamma=gamma,
        initial_infected=initial_infected,
        days=days,
        initial_recovered=vaccinated,
    )

    susceptible, exposed, infectious, recovered = states.T
    peak_idx = int(np.argmax(infectious))
    peak_infected = float(infectious[peak_idx])
    peak_day = int(times[peak_idx])
    final_recovered = float(recovered[-1])

    return {
        "times": times,
        "states": states,
        "peak_infected": peak_infected,
        "peak_day": peak_day,
        "final_recovered": final_recovered,
    }


def summarize_results(result: Dict[str, float]) -> SimulationResult:
    return SimulationResult(
        times=result["times"],
        states=result["states"],
        peak_infected=result["peak_infected"],
        peak_day=result["peak_day"],
        final_recovered=result["final_recovered"],
    )
