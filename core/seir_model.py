"""
core/seir_model.py
==================
SEIRD Differential Equation Model with interventions.

Compartments:
  S – Susceptible
  E – Exposed (incubating, not yet infectious)
  I – Infectious
  R – Recovered (immune)
  D – Deceased

Key extensions over basic SIR:
  • Time-varying β (lockdown / mask mandate interventions)
  • Vaccination (ν): moves S → R at accelerated rate
  • Mortality (μ): case fatality rate moves I → D
  • scipy.integrate.odeint for adaptive Runge-Kutta stepping

Reference: Kermack & McKendrick (1927), Ferguson et al. (2020)
"""

from __future__ import annotations

import numpy as np
from scipy.integrate import odeint
from dataclasses import dataclass, field
from typing import Optional
import pandas as pd


# ---------------------------------------------------------------------------
# Disease parameter presets (published epidemiological values)
# ---------------------------------------------------------------------------
DISEASE_PRESETS: dict[str, dict] = {
    "COVID-19 (Alpha)": {
        "beta": 0.30,      # transmission rate (1/day)
        "sigma": 0.20,     # incubation rate: 1/5 day incubation period
        "gamma": 0.10,     # recovery rate: 1/10 day infectious period
        "mu": 0.015,       # case fatality rate (~1.5% Bangladesh 2021)
        "R0_ref": 2.9,
        "color": "#e74c3c",
        "description": "SARS-CoV-2 Alpha variant — Bangladesh 2021 parameters",
    },
    "COVID-19 (Omicron)": {
        "beta": 0.55,
        "sigma": 0.33,     # ~3 day incubation
        "gamma": 0.20,     # shorter infectious period
        "mu": 0.004,       # lower CFR
        "R0_ref": 8.0,
        "color": "#e67e22",
        "description": "SARS-CoV-2 Omicron — highly transmissible, lower severity",
    },
    "Influenza (Seasonal)": {
        "beta": 0.20,
        "sigma": 0.50,     # 2-day incubation
        "gamma": 0.14,     # 7-day infectious period
        "mu": 0.001,       # ~0.1% CFR
        "R0_ref": 1.4,
        "color": "#3498db",
        "description": "Seasonal influenza — moderate transmissibility",
    },
    "Measles": {
        "beta": 0.90,
        "sigma": 0.067,    # 15-day incubation
        "gamma": 0.071,    # 14-day infectious period
        "mu": 0.002,       # 0.2% CFR in developing countries
        "R0_ref": 15.0,
        "color": "#9b59b6",
        "description": "Measles — highest known R₀ of common diseases",
    },
    "Dengue": {
        "beta": 0.25,
        "sigma": 0.143,    # 7-day incubation
        "gamma": 0.067,    # 15-day infectious period
        "mu": 0.025,       # 2.5% CFR without treatment
        "R0_ref": 3.0,
        "color": "#f39c12",
        "description": "Dengue fever — Bangladesh context (2021 outbreak data)",
    },
    "Custom": {
        "beta": 0.30,
        "sigma": 0.20,
        "gamma": 0.10,
        "mu": 0.01,
        "R0_ref": None,
        "color": "#1abc9c",
        "description": "User-defined parameters",
    },
}


# ---------------------------------------------------------------------------
# Intervention definitions
# ---------------------------------------------------------------------------
@dataclass
class Intervention:
    """Represents a public-health intervention applied at a given day."""
    name: str
    start_day: int
    beta_reduction: float        # fraction reduction in β (0.0 – 1.0)
    vaccination_boost: float = 0.0   # additional daily vaccination fraction


INTERVENTION_PRESETS: dict[str, Intervention] = {
    "None": Intervention("No intervention", 0, 0.0),
    "Lockdown (strict)": Intervention("Strict lockdown", 15, 0.60),
    "Lockdown (moderate)": Intervention("Moderate lockdown", 15, 0.35),
    "Mask mandate": Intervention("Mask mandate", 10, 0.30),
    "Vaccination campaign": Intervention("Vaccination campaign", 0, 0.0, 0.005),
}


# ---------------------------------------------------------------------------
# SEIRD Model
# ---------------------------------------------------------------------------
class SEIRDModel:
    """
    SEIRD Ordinary Differential Equation model.

    Parameters
    ----------
    N : int
        Total population size.
    beta : float
        Transmission rate (contacts × probability per day).
    sigma : float
        Incubation rate (1 / mean incubation period in days).
    gamma : float
        Recovery rate (1 / mean infectious period in days).
    mu : float
        Case fatality rate (daily mortality from I compartment).
    nu : float
        Baseline daily vaccination fraction (S → R).
    E0, I0, R0_init, D0 : int
        Initial counts in each compartment (S = N − E0 − I0 − R0_init).
    """

    def __init__(
        self,
        N: int = 100_000,
        beta: float = 0.30,
        sigma: float = 0.20,
        gamma: float = 0.10,
        mu: float = 0.015,
        nu: float = 0.0,
        E0: int = 0,
        I0: int = 1,
        R0_init: int = 0,
        D0: int = 0,
    ):
        self.N = N
        self.beta = beta
        self.sigma = sigma
        self.gamma = gamma
        self.mu = mu
        self.nu = nu
        self.E0 = E0
        self.I0 = I0
        self.R0_init = R0_init
        self.D0 = D0
        self.S0 = N - E0 - I0 - R0_init - D0

        # Derived quantities
        self.R0: float = beta / gamma
        self.herd_immunity_threshold: float = 1.0 - (1.0 / self.R0) if self.R0 > 1 else 0.0

    # ------------------------------------------------------------------
    # ODE system
    # ------------------------------------------------------------------
    def _ode_system(
        self,
        y: list[float],
        t: float,
        beta_t: float,
        nu_t: float,
    ) -> list[float]:
        """SEIRD differential equations (called by odeint at each timestep)."""
        S, E, I, R, D = y
        N = self.N

        # Force of infection
        lambda_t = beta_t * I / N

        dS = -lambda_t * S - nu_t * S
        dE = lambda_t * S - self.sigma * E
        dI = self.sigma * E - self.gamma * I - self.mu * I
        dR = self.gamma * I + nu_t * S
        dD = self.mu * I

        return [dS, dE, dI, dR, dD]

    # ------------------------------------------------------------------
    # Run simulation
    # ------------------------------------------------------------------
    def run(
        self,
        days: int = 365,
        intervention: Optional[Intervention] = None,
    ) -> pd.DataFrame:
        """
        Integrate the SEIRD system over [0, days].

        Returns
        -------
        pd.DataFrame with columns: day, S, E, I, R, D, new_cases, beta_t
        """
        t = np.linspace(0, days, days + 1)
        y0 = [self.S0, self.E0, self.I0, self.R0_init, self.D0]

        # Build time-varying beta array (one value per day)
        beta_arr = np.full(days + 1, self.beta)
        nu_arr = np.full(days + 1, self.nu)

        if intervention is not None:
            start = intervention.start_day
            if start < days + 1:
                beta_arr[start:] *= (1.0 - intervention.beta_reduction)
                nu_arr[start:] += intervention.vaccination_boost

        # Solve — odeint handles variable beta by solving day-by-day segments
        results = []
        y_current = y0
        prev_S = y0[0]

        for day in range(days + 1):
            if day > 0:
                sol = odeint(
                    self._ode_system,
                    y_current,
                    [0, 1],
                    args=(beta_arr[day], nu_arr[day]),
                    rtol=1e-8,
                    atol=1e-8,
                )
                y_current = sol[-1]
                # Clamp to prevent floating-point negatives
                y_current = np.maximum(y_current, 0)

            S, E, I, R, D = y_current
            new_cases = max(0.0, prev_S - S)
            results.append({
                "day": day,
                "S": S,
                "E": E,
                "I": I,
                "R": R,
                "D": D,
                "new_cases": new_cases,
                "beta_t": beta_arr[day],
                "nu_t": nu_arr[day],
            })
            prev_S = S

        df = pd.DataFrame(results)
        df["total_affected_pct"] = (df["R"] + df["D"]) / self.N * 100
        return df

    # ------------------------------------------------------------------
    # Summary statistics
    # ------------------------------------------------------------------
    def compute_summary(self, df: pd.DataFrame) -> dict:
        """Return key epidemiological metrics from a simulation DataFrame."""
        peak_row = df.loc[df["I"].idxmax()]
        epidemic_end_day_raw = df[df["I"] < 1]["day"].min()
        epidemic_end_day = int(epidemic_end_day_raw) if pd.notna(epidemic_end_day_raw) else len(df)

        return {
            "R0": round(self.R0, 2),
            "herd_immunity_threshold_pct": round(self.herd_immunity_threshold * 100, 1),
            "peak_infected": int(peak_row["I"]),
            "peak_infected_pct": round(peak_row["I"] / self.N * 100, 2),
            "peak_day": int(peak_row["day"]),
            "epidemic_end_day": epidemic_end_day,
            "total_deaths": int(df["D"].iloc[-1]),
            "total_recovered": int(df["R"].iloc[-1]),
            "total_affected_pct": round(df["total_affected_pct"].iloc[-1], 1),
        }

    # ------------------------------------------------------------------
    # Scenario comparison helper
    # ------------------------------------------------------------------
    @staticmethod
    def run_scenario_comparison(
        base_params: dict,
        days: int = 300,
    ) -> dict[str, pd.DataFrame]:
        """
        Run all 5 standard intervention scenarios and return a dict of DataFrames.

        Scenarios:
          1. No intervention (baseline)
          2. Early lockdown  — Day 15
          3. Late lockdown   — Day 45
          4. 50% vaccination rate
          5. 70% vaccination + herd immunity
        """
        scenarios: dict[str, Intervention] = {
            "No Intervention": Intervention("No intervention", 0, 0.0),
            "Early Lockdown (Day 15)": Intervention("Early lockdown", 15, 0.60),
            "Late Lockdown (Day 45)": Intervention("Late lockdown", 45, 0.60),
            "Mask Mandate (Day 10)": Intervention("Mask mandate", 10, 0.30),
            "50% Vaccination": Intervention("50% vaccination", 0, 0.0, 0.003),
            "70% Vaccination (Herd)": Intervention("70% vaccination", 0, 0.0, 0.005),
        }
        results = {}
        for name, interv in scenarios.items():
            model = SEIRDModel(**base_params)
            results[name] = model.run(days=days, intervention=interv)
        return results


# ---------------------------------------------------------------------------
# Sensitivity analysis helper
# ---------------------------------------------------------------------------
def sensitivity_analysis(
    base_params: dict,
    param_name: str = "beta",
    values: Optional[list[float]] = None,
    days: int = 200,
) -> pd.DataFrame:
    """
    Vary one parameter across a range and return peak infected % for each value.

    Returns a DataFrame with columns: [param_name, peak_infected_pct, R0]
    """
    if values is None:
        values = np.round(np.arange(0.10, 0.65, 0.05), 2).tolist()

    rows = []
    for v in values:
        params = {**base_params, param_name: v}
        m = SEIRDModel(**params)
        df = m.run(days=days)
        summary = m.compute_summary(df)
        rows.append({
            param_name: v,
            "peak_infected_pct": summary["peak_infected_pct"],
            "R0": summary["R0"],
            "total_affected_pct": summary["total_affected_pct"],
            "total_deaths": summary["total_deaths"],
        })
    return pd.DataFrame(rows)
