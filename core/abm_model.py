"""
core/abm_model.py
=================
Agent-Based Model using a Barabási–Albert scale-free social network.

Why scale-free networks?
  Real human social contact patterns follow a power-law degree distribution
  (Barabási & Albert, 1999). A few "super-spreader" nodes have many connections;
  most people have few. This is impossible to capture with a flat grid or ODE.

Key features:
  • NetworkX Barabási-Albert graph for realistic contact structure
  • SEIRD states on each node
  • Disease spreads only along network edges
  • Interventions: remove random edges (social distancing), isolate nodes (quarantine)
  • Runs step-by-step so Streamlit can animate it
"""

from __future__ import annotations

import numpy as np
import networkx as nx
import pandas as pd
from dataclasses import dataclass
from typing import Optional


# Node states
S, E, I, R, D = "S", "E", "I", "R", "D"
STATE_COLORS = {S: "#3498db", E: "#f39c12", I: "#e74c3c", R: "#2ecc71", D: "#7f8c8d"}
STATE_ORDER = [S, E, I, R, D]


@dataclass
class ABMParams:
    """Parameters for the Agent-Based Model."""
    N: int = 2_000            # number of agents (nodes)
    m: int = 3                # BA graph: edges per new node (controls avg. degree)
    beta: float = 0.12        # transmission probability per contact per step
    sigma_days: int = 5       # mean incubation period (days until infectious)
    gamma_days: int = 10      # mean infectious period (days until recovery)
    mu: float = 0.015         # case fatality rate
    initial_infected: int = 3 # seed infections at start
    social_distance: float = 0.0  # fraction of edges removed (0 = no distancing)
    seed: Optional[int] = 42


class ABMSimulation:
    """
    Stochastic agent-based epidemic simulation on a scale-free network.

    Each call to step() advances the simulation by one day.
    """

    def __init__(self, params: ABMParams):
        self.params = params
        rng = np.random.default_rng(params.seed)
        self.rng = rng

        # Build Barabási-Albert scale-free graph
        self.G = nx.barabasi_albert_graph(params.N, params.m, seed=params.seed)

        # Apply social distancing — remove a fraction of edges
        if params.social_distance > 0:
            edges = list(self.G.edges())
            n_remove = int(len(edges) * params.social_distance)
            remove_idx = rng.choice(len(edges), size=n_remove, replace=False)
            for idx in remove_idx:
                u, v = edges[idx]
                if self.G.has_edge(u, v):
                    self.G.remove_edge(u, v)

        # Initialise states
        self.states = np.full(params.N, S, dtype=object)
        self.exposure_day = np.full(params.N, -1, dtype=int)   # day first exposed
        self.infection_day = np.full(params.N, -1, dtype=int)  # day became infectious

        # Seed initial infections
        seeds = rng.choice(params.N, size=params.initial_infected, replace=False)
        for node in seeds:
            self.states[node] = I
            self.infection_day[node] = 0

        self.day = 0
        self.history: list[dict] = []
        self._record()

    def _record(self):
        counts = {state: int(np.sum(self.states == state)) for state in STATE_ORDER}
        counts["day"] = self.day
        self.history.append(counts)

    def step(self):
        """Advance simulation by one day."""
        p = self.params
        new_states = self.states.copy()

        for node in range(p.N):
            state = self.states[node]

            if state == S:
                # Check neighbours — any infectious neighbour can transmit
                for nb in self.G.neighbors(node):
                    if self.states[nb] == I:
                        if self.rng.random() < p.beta:
                            new_states[node] = E
                            self.exposure_day[node] = self.day
                            break  # one transmission event per day

            elif state == E:
                # Incubation complete?
                days_exposed = self.day - self.exposure_day[node]
                if days_exposed >= p.sigma_days:
                    new_states[node] = I
                    self.infection_day[node] = self.day

            elif state == I:
                # Recovery or death
                days_infectious = self.day - self.infection_day[node]
                if days_infectious >= p.gamma_days:
                    if self.rng.random() < p.mu:
                        new_states[node] = D
                    else:
                        new_states[node] = R

            # R and D are absorbing states

        self.states = new_states
        self.day += 1
        self._record()

    def run(self, days: int = 150) -> pd.DataFrame:
        """Run for a fixed number of days and return history DataFrame."""
        for _ in range(days):
            self.step()
            # Early stop if no more infectious agents
            if np.sum(self.states == I) == 0 and np.sum(self.states == E) == 0:
                break
        return self.get_history()

    def get_history(self) -> pd.DataFrame:
        return pd.DataFrame(self.history)

    def get_node_data(self) -> pd.DataFrame:
        """Return per-node data for network visualisation."""
        degree = dict(self.G.degree())
        rows = []
        for node in range(self.params.N):
            pos = None  # layout computed separately
            rows.append({
                "node": node,
                "state": self.states[node],
                "degree": degree[node],
                "color": STATE_COLORS[self.states[node]],
            })
        return pd.DataFrame(rows)

    def get_graph_layout(self) -> dict[int, tuple[float, float]]:
        """Compute and cache spring layout positions (expensive — call once)."""
        if not hasattr(self, "_layout"):
            self._layout = nx.spring_layout(self.G, seed=self.params.seed, k=0.5)
        return self._layout

    def get_degree_distribution(self) -> pd.DataFrame:
        """Return degree distribution to demonstrate power-law structure."""
        degrees = [d for _, d in self.G.degree()]
        degree_counts = pd.Series(degrees).value_counts().reset_index()
        degree_counts.columns = ["degree", "count"]
        degree_counts = degree_counts.sort_values("degree")
        return degree_counts

    @property
    def super_spreaders(self) -> list[int]:
        """Nodes in the top 5% by degree — the most connected 'hubs'."""
        degrees = dict(self.G.degree())
        threshold = np.percentile(list(degrees.values()), 95)
        return [n for n, d in degrees.items() if d >= threshold]
