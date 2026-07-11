"""
episim.py — Core SEIRD epidemic simulation engine.

Model compartments:
  S  — Susceptible
  E  — Exposed (incubating, not yet infectious)
  I  — Infectious
  R  — Recovered (immune)
  D  — Deceased

Differential equations (SEIRD):
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
# Derived epidemiological quantities
# ---------------------------------------------------------------------------

def compute_daily_incidence(times: np.ndarray, states: np.ndarray) -> np.ndarray:
    """Compute new daily infections as the decline in S each day.

    Returns an array of length len(times) with daily new case counts.
    Index 0 is set to the initial infected count (I₀).
    """
    S = states[:, 0]
    # New infections = decrease in susceptibles (negative gradient of S)
    incidence = np.zeros(len(times))
    incidence[0] = states[0, 2]  # I₀ as baseline
    incidence[1:] = np.maximum(0, -np.diff(S))
    return incidence


def compute_rt(
    times: np.ndarray,
    states: np.ndarray,
    population: int,
    beta: float,
    gamma: float,
    mu: float = 0.0,
) -> np.ndarray:
    """Compute the time-varying effective reproduction number Rt(t).

    Rt(t) = R₀ × S(t)/N  where R₀ = β / (γ + μ)

    At the start Rt = R₀ (all susceptible); as S falls, Rt falls.
    Epidemic peaks when Rt crosses 1.0.
    """
    S = states[:, 0]
    removal_rate = gamma + mu if (gamma + mu) > 0 else gamma
    r0_basic = beta / removal_rate if removal_rate > 0 else 0.0
    rt = r0_basic * S / population
    return rt


def herd_immunity_threshold(r0: float) -> float:
    """Return the herd immunity threshold: fraction of population that must
    be immune to prevent sustained epidemic growth.

    HIT = 1 - 1/R₀    (only meaningful when R₀ > 1)
    """
    if r0 <= 1.0:
        return 0.0
    return 1.0 - 1.0 / r0


def compute_doubling_time(times: np.ndarray, states: np.ndarray) -> float:
    """Estimate the initial exponential doubling time of infections (days).

    Uses log-linear regression on the early growth phase (while I < 1% of pop).
    Returns inf if no clear exponential growth detected.
    """
    I = states[:, 2]
    N = np.sum(states[0])
    threshold = 0.01 * N  # 1% of population

    # Find indices where I is still in early growth (< 1% of pop)
    early_mask = I < threshold
    # Need at least 5 points showing clear growth
    if early_mask.sum() < 5:
        early_mask = np.ones(len(I), dtype=bool)

    early_times = times[early_mask]
    early_I = I[early_mask]

    # Filter out zeros or non-positive values
    pos_mask = early_I > 0
    if pos_mask.sum() < 3:
        return float("inf")

    t_fit = early_times[pos_mask]
    log_I = np.log(early_I[pos_mask])

    if len(t_fit) < 2:
        return float("inf")

    try:
        slope, _ = np.polyfit(t_fit, log_I, 1)
        if slope <= 0:
            return float("inf")
        return float(np.log(2) / slope)
    except Exception:
        return float("inf")


def compute_serial_interval(sigma: float, gamma: float) -> float:
    """Estimate the serial interval (mean time between successive cases).

    Serial interval ≈ 1/σ (incubation) + 1/γ (half of infectious period).
    """
    incubation = 1.0 / sigma if sigma > 0 else 0
    infectious = 0.5 / gamma if gamma > 0 else 0
    return incubation + infectious


def compute_cfr(mu: float, gamma: float) -> float:
    """Case fatality ratio: fraction of infected individuals who die.

    CFR = μ / (μ + γ)
    """
    total = mu + gamma
    if total <= 0:
        return 0.0
    return mu / total


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

    Returns a dict with times, states, and comprehensive summary statistics.
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
    removal_rate = gamma + mu
    r0 = effective_beta / removal_rate if removal_rate > 0 else 0.0

    # Derived epidemiological quantities
    incidence = compute_daily_incidence(times, states)
    rt_series = compute_rt(times, states, population, effective_beta, gamma, mu)
    hit = herd_immunity_threshold(r0)
    doubling = compute_doubling_time(times, states)
    serial_interval = compute_serial_interval(sigma, gamma)
    cfr = compute_cfr(mu, gamma)
    attack_rate = 100.0 * (final_recovered + total_deaths) / population

    return {
        # Raw simulation output
        "times": times,
        "states": states,           # (days+1, 5): S E I R D
        "model_type": model_type,

        # Core epidemic metrics
        "peak_infected": peak_infected,
        "peak_day": peak_day,
        "final_recovered": final_recovered,
        "total_deaths": total_deaths,
        "peak_hospitalized": peak_hospitalized,
        "r0": r0,
        "attack_rate": attack_rate,

        # Extended derived quantities (professor-level)
        "incidence": incidence,                  # daily new cases
        "rt_series": rt_series,                  # time-varying Rt(t)
        "herd_immunity_threshold": hit,           # fraction of pop needed immune
        "doubling_time": doubling,               # initial doubling time in days
        "serial_interval": serial_interval,      # mean days between cases
        "cfr": cfr,                              # case fatality ratio 0-1

        # Parameters echo (useful for comparisons)
        "params": {
            "beta": effective_beta,
            "sigma": sigma,
            "gamma": gamma,
            "mu": mu,
            "vaccine_coverage": vaccine_coverage,
            "distancing_reduction": distancing_reduction,
            "hospitalization_rate": hospitalization_rate,
        },
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


# ---------------------------------------------------------------------------
# Parameter fitting from real data
# ---------------------------------------------------------------------------

def fit_parameters(
    observed_days: np.ndarray,
    observed_cases: np.ndarray,
    population: int,
    model_type: str = "SEIRD",
    initial_infected: int = 1,
    fit_column: str = "Infectious",
    mu_fixed: float | None = None,
    sigma_fixed: float | None = None,
    max_iter: int = 1000,
) -> Dict:
    """Fit compartmental model parameters to observed epidemic data.

    Uses scipy.optimize.minimize (L-BFGS-B) with least-squares residuals
    between simulated I(t) and the observed case time-series.

    Parameters
    ----------
    observed_days   : 1-D array of day indices (0, 1, 2, ...)
    observed_cases  : 1-D array of observed infectious/active case counts
    population      : total population N
    model_type      : 'SEIRD', 'SEIR', 'SIR', or 'SIS'
    initial_infected: I₀ used for simulation during fitting
    fit_column      : which compartment to compare ('Infectious', 'Deaths', etc.)
    mu_fixed        : if provided, μ is not optimised and held at this value
    sigma_fixed     : if provided, σ is not optimised and held at this value
    max_iter        : maximum optimiser iterations

    Returns
    -------
    dict with keys: beta, sigma, gamma, mu, r0, rmse, r_squared, fitted_times,
    fitted_states, residuals
    """
    from scipy.optimize import minimize

    model_upper = model_type.upper().split(" ")[0]
    days_sim = int(observed_days.max())

    # Normalise observed to simulation time grid
    # Map observed days → nearest integer index
    obs_days_int = np.round(observed_days).astype(int)
    obs_days_int = np.clip(obs_days_int, 0, days_sim)

    def _column_index(col: str) -> int:
        mapping = {"Susceptible": 0, "Exposed": 1, "Infectious": 2, "Recovered": 3, "Deaths": 4}
        return mapping.get(col, 2)

    col_idx = _column_index(fit_column)

    def _residuals(params):
        """Sum of squared residuals between simulated and observed."""
        # Unpack params (log-space to keep positive)
        if mu_fixed is not None and sigma_fixed is not None:
            beta_p, gamma_p = params
            sigma_p = sigma_fixed
            mu_p = mu_fixed
        elif mu_fixed is not None:
            beta_p, sigma_p, gamma_p = params
            mu_p = mu_fixed
        elif sigma_fixed is not None:
            beta_p, gamma_p, mu_p = params
            sigma_p = sigma_fixed
        else:
            beta_p, sigma_p, gamma_p, mu_p = params

        beta_p  = max(1e-6, beta_p)
        sigma_p = max(1e-6, sigma_p)
        gamma_p = max(1e-6, gamma_p)
        mu_p    = max(0.0,  mu_p)

        try:
            _, states = simulate_seird(
                population=population,
                beta=beta_p, sigma=sigma_p, gamma=gamma_p, mu=mu_p,
                initial_infected=max(1, initial_infected),
                days=days_sim,
                model_type=model_type,
            )
            simulated = states[:, col_idx]
            sim_at_obs = simulated[obs_days_int]
            residuals = sim_at_obs - observed_cases
            return float(np.sum(residuals ** 2))
        except Exception:
            return 1e18

    # Initial parameter guess (based on typical epidemic values)
    beta0, sigma0, gamma0, mu0 = 0.30, 0.20, 0.10, 0.005

    # Build bounds and x0 based on which parameters are free
    if mu_fixed is not None and sigma_fixed is not None:
        x0 = [beta0, gamma0]
        bounds = [(0.01, 2.0), (0.01, 0.80)]
    elif mu_fixed is not None:
        x0 = [beta0, sigma0, gamma0]
        bounds = [(0.01, 2.0), (0.05, 1.0), (0.01, 0.80)]
    elif sigma_fixed is not None:
        x0 = [beta0, gamma0, mu0]
        bounds = [(0.01, 2.0), (0.01, 0.80), (0.0, 0.10)]
    else:
        x0 = [beta0, sigma0, gamma0, mu0]
        bounds = [(0.01, 2.0), (0.05, 1.0), (0.01, 0.80), (0.0, 0.10)]

    result_opt = minimize(
        _residuals, x0, method="L-BFGS-B",
        bounds=bounds,
        options={"maxiter": max_iter, "ftol": 1e-12, "gtol": 1e-8},
    )

    # Extract fitted parameters
    if mu_fixed is not None and sigma_fixed is not None:
        beta_fit, gamma_fit = result_opt.x
        sigma_fit, mu_fit = sigma_fixed, mu_fixed
    elif mu_fixed is not None:
        beta_fit, sigma_fit, gamma_fit = result_opt.x
        mu_fit = mu_fixed
    elif sigma_fixed is not None:
        beta_fit, gamma_fit, mu_fit = result_opt.x
        sigma_fit = sigma_fixed
    else:
        beta_fit, sigma_fit, gamma_fit, mu_fit = result_opt.x

    # Final simulation with fitted parameters
    fitted_times, fitted_states = simulate_seird(
        population=population,
        beta=beta_fit, sigma=sigma_fit, gamma=gamma_fit, mu=mu_fit,
        initial_infected=max(1, initial_infected),
        days=days_sim,
        model_type=model_type,
    )

    sim_at_obs = fitted_states[obs_days_int, col_idx]
    residuals = sim_at_obs - observed_cases
    rmse = float(np.sqrt(np.mean(residuals ** 2)))

    ss_res = float(np.sum(residuals ** 2))
    ss_tot = float(np.sum((observed_cases - np.mean(observed_cases)) ** 2))
    r_squared = float(1 - ss_res / ss_tot) if ss_tot > 0 else 0.0

    removal_rate = gamma_fit + mu_fit
    r0_fit = beta_fit / removal_rate if removal_rate > 0 else 0.0

    return {
        "beta":          float(beta_fit),
        "sigma":         float(sigma_fit),
        "gamma":         float(gamma_fit),
        "mu":            float(mu_fit),
        "r0":            r0_fit,
        "rmse":          rmse,
        "r_squared":     r_squared,
        "fitted_times":  fitted_times,
        "fitted_states": fitted_states,
        "residuals":     residuals,
        "converged":     result_opt.success,
        "message":       result_opt.message,
    }

