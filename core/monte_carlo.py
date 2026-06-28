"""
core/monte_carlo.py
===================
Monte Carlo uncertainty analysis for the SEIRD model.

Runs N simulations with normally-distributed parameter perturbations,
then computes mean trajectory + 95% confidence intervals.

This is what separates deterministic simulation from real epidemiological
modelling — every published WHO/CDC model includes uncertainty bands.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
from typing import Optional
from .seir_model import SEIRDModel, Intervention


class MonteCarloSimulator:
    """
    Run repeated SEIRD simulations with stochastic parameter sampling.

    Parameters
    ----------
    base_params : dict
        Central parameter estimates (same kwargs as SEIRDModel).
    n_runs : int
        Number of Monte Carlo iterations (200–1000 recommended).
    noise_level : float
        Coefficient of variation applied to beta, sigma, gamma, mu.
        Default 0.10 = ±10% standard deviation.
    """

    def __init__(
        self,
        base_params: dict,
        n_runs: int = 300,
        noise_level: float = 0.10,
    ):
        self.base_params = base_params
        self.n_runs = n_runs
        self.noise_level = noise_level

    def _sample_params(self) -> dict:
        """Sample one set of parameters from a truncated normal distribution."""
        rng = np.random
        p = dict(self.base_params)

        def perturb(val: float, low: float = 0.001) -> float:
            """Perturb a value ensuring it stays positive."""
            noise = rng.normal(0, self.noise_level * val)
            return max(low, val + noise)

        p["beta"] = perturb(p["beta"])
        p["sigma"] = perturb(p["sigma"])
        p["gamma"] = perturb(p["gamma"])
        p["mu"] = perturb(p.get("mu", 0.01), low=0.0)
        return p

    def run(
        self,
        days: int = 300,
        intervention: Optional[Intervention] = None,
    ) -> dict:
        """
        Run all Monte Carlo simulations.

        Returns
        -------
        dict with keys:
          'mean'  : pd.DataFrame — mean trajectory
          'lower' : pd.DataFrame — 2.5th percentile (lower CI bound)
          'upper' : pd.DataFrame — 97.5th percentile (upper CI bound)
          'all_runs' : list[pd.DataFrame] — individual run outputs
          'summary_stats' : pd.DataFrame — per-run summary metrics
        """
        columns = ["S", "E", "I", "R", "D", "new_cases"]
        all_I = np.zeros((self.n_runs, days + 1))
        all_D = np.zeros((self.n_runs, days + 1))
        all_new = np.zeros((self.n_runs, days + 1))
        all_S = np.zeros((self.n_runs, days + 1))
        all_R = np.zeros((self.n_runs, days + 1))
        all_E = np.zeros((self.n_runs, days + 1))

        summary_rows = []

        for i in range(self.n_runs):
            params = self._sample_params()
            model = SEIRDModel(**params)
            df = model.run(days=days, intervention=intervention)
            summary = model.compute_summary(df)

            all_S[i] = df["S"].values
            all_E[i] = df["E"].values
            all_I[i] = df["I"].values
            all_R[i] = df["R"].values
            all_D[i] = df["D"].values
            all_new[i] = df["new_cases"].values
            summary_rows.append(summary)

        t = np.arange(days + 1)

        def _build_df(arr: np.ndarray, col: str) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
            return (
                np.mean(arr, axis=0),
                np.percentile(arr, 2.5, axis=0),
                np.percentile(arr, 97.5, axis=0),
            )

        N = self.base_params["N"]

        mean_df = pd.DataFrame({
            "day": t,
            "S": np.mean(all_S, axis=0),
            "E": np.mean(all_E, axis=0),
            "I": np.mean(all_I, axis=0),
            "R": np.mean(all_R, axis=0),
            "D": np.mean(all_D, axis=0),
            "new_cases": np.mean(all_new, axis=0),
        })

        lower_df = pd.DataFrame({
            "day": t,
            "I": np.percentile(all_I, 2.5, axis=0),
            "D": np.percentile(all_D, 2.5, axis=0),
            "new_cases": np.percentile(all_new, 2.5, axis=0),
        })

        upper_df = pd.DataFrame({
            "day": t,
            "I": np.percentile(all_I, 97.5, axis=0),
            "D": np.percentile(all_D, 97.5, axis=0),
            "new_cases": np.percentile(all_new, 97.5, axis=0),
        })

        return {
            "mean": mean_df,
            "lower": lower_df,
            "upper": upper_df,
            "summary_stats": pd.DataFrame(summary_rows),
            "n_runs": self.n_runs,
        }
