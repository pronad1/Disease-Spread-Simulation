"""
ui/components/charts.py
========================
All Plotly chart builders for the EpiSim dashboard.

Every chart uses a consistent dark theme, hover tooltips, and
is interactive out of the box in Streamlit.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots


# ---------------------------------------------------------------------------
# Shared theme
# ---------------------------------------------------------------------------
DARK_TEMPLATE = "plotly_dark"
COMPARTMENT_COLORS = {
    "S": "#3498db",   # blue
    "E": "#f39c12",   # orange
    "I": "#e74c3c",   # red
    "R": "#2ecc71",   # green
    "D": "#95a5a6",   # grey
}
SCENARIO_PALETTE = [
    "#e74c3c", "#3498db", "#2ecc71", "#f39c12", "#9b59b6", "#1abc9c"
]


def make_seir_curve(df: pd.DataFrame, N: int, title: str = "SEIRD Epidemic Curve") -> go.Figure:
    """
    Animated SEIRD curve with hover tooltips showing raw numbers + percentages.
    """
    fig = go.Figure()

    compartments = [
        ("S", "Susceptible"),
        ("E", "Exposed"),
        ("I", "Infectious"),
        ("R", "Recovered"),
        ("D", "Deaths"),
    ]

    for col, label in compartments:
        if col not in df.columns:
            continue
        fig.add_trace(go.Scatter(
            x=df["day"],
            y=df[col],
            name=label,
            mode="lines",
            line=dict(color=COMPARTMENT_COLORS[col], width=2.5),
            fill="tozeroy" if col == "I" else None,
            fillcolor=f"rgba({_hex_to_rgb(COMPARTMENT_COLORS[col])}, 0.08)" if col == "I" else None,
            hovertemplate=(
                f"<b>{label}</b><br>"
                "Day %{x}<br>"
                "Count: %{y:,.0f}<br>"
                f"(%{{customdata:.2f}}%)<extra></extra>"
            ),
            customdata=df[col] / N * 100,
        ))

    fig.update_layout(
        title=dict(text=title, font=dict(size=16, color="#ecf0f1")),
        template=DARK_TEMPLATE,
        hovermode="x unified",
        xaxis=dict(title="Day", gridcolor="#2c3e50"),
        yaxis=dict(title="Population", gridcolor="#2c3e50"),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1,
        ),
        margin=dict(l=10, r=10, t=60, b=10),
        plot_bgcolor="#1a1a2e",
        paper_bgcolor="#16213e",
    )
    return fig


def make_seir_curve_with_ci(
    mean_df: pd.DataFrame,
    lower_df: pd.DataFrame,
    upper_df: pd.DataFrame,
    N: int,
) -> go.Figure:
    """SEIRD curve with 95% Monte Carlo confidence bands."""
    fig = go.Figure()

    # Confidence band (shaded area)
    fig.add_trace(go.Scatter(
        x=pd.concat([mean_df["day"], mean_df["day"][::-1]]),
        y=pd.concat([upper_df["I"], lower_df["I"][::-1]]),
        fill="toself",
        fillcolor="rgba(231, 76, 60, 0.15)",
        line=dict(color="rgba(255,255,255,0)"),
        name="95% CI (Monte Carlo)",
        showlegend=True,
    ))

    # Mean line
    fig.add_trace(go.Scatter(
        x=mean_df["day"],
        y=mean_df["I"],
        name="Infectious (mean)",
        line=dict(color="#e74c3c", width=2.5),
        hovertemplate="Day %{x}<br>Infectious: %{y:,.0f}<extra></extra>",
    ))
    fig.add_trace(go.Scatter(
        x=mean_df["day"],
        y=mean_df["R"],
        name="Recovered (mean)",
        line=dict(color="#2ecc71", width=2),
        hovertemplate="Day %{x}<br>Recovered: %{y:,.0f}<extra></extra>",
    ))
    fig.add_trace(go.Scatter(
        x=mean_df["day"],
        y=mean_df["D"],
        name="Deaths (mean)",
        line=dict(color="#95a5a6", width=2),
        hovertemplate="Day %{x}<br>Deaths: %{y:,.0f}<extra></extra>",
    ))

    fig.update_layout(
        title="SEIRD Curve — Monte Carlo Uncertainty (95% CI)",
        template=DARK_TEMPLATE,
        hovermode="x unified",
        xaxis=dict(title="Day", gridcolor="#2c3e50"),
        yaxis=dict(title="Population", gridcolor="#2c3e50"),
        plot_bgcolor="#1a1a2e",
        paper_bgcolor="#16213e",
        margin=dict(l=10, r=10, t=60, b=10),
    )
    return fig


def make_scenario_comparison(
    scenario_results: dict[str, pd.DataFrame],
    N: int,
    column: str = "I",
) -> go.Figure:
    """Overlay all scenario curves on a single chart."""
    label_map = {"I": "Infectious", "D": "Cumulative Deaths", "new_cases": "Daily New Cases"}
    fig = go.Figure()

    for (name, df), color in zip(scenario_results.items(), SCENARIO_PALETTE):
        if column not in df.columns:
            continue
        fig.add_trace(go.Scatter(
            x=df["day"],
            y=df[column],
            name=name,
            line=dict(color=color, width=2),
            mode="lines",
            hovertemplate=f"<b>{name}</b><br>Day %{{x}}<br>{label_map.get(column, column)}: %{{y:,.0f}}<extra></extra>",
        ))

    fig.update_layout(
        title=f"Scenario Comparison — {label_map.get(column, column)}",
        template=DARK_TEMPLATE,
        hovermode="x unified",
        xaxis=dict(title="Day", gridcolor="#2c3e50"),
        yaxis=dict(title=label_map.get(column, column), gridcolor="#2c3e50"),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, x=0),
        plot_bgcolor="#1a1a2e",
        paper_bgcolor="#16213e",
        margin=dict(l=10, r=10, t=70, b=10),
    )
    return fig


def make_daily_cases_bar(df: pd.DataFrame) -> go.Figure:
    """Bar chart of daily new cases with colour gradient by intensity."""
    max_cases = df["new_cases"].max()

    fig = go.Figure(go.Bar(
        x=df["day"],
        y=df["new_cases"],
        marker=dict(
            color=df["new_cases"],
            colorscale="Reds",
            showscale=True,
            colorbar=dict(title="Daily cases", tickfont=dict(color="#ecf0f1")),
        ),
        hovertemplate="Day %{x}<br>New Cases: %{y:,.0f}<extra></extra>",
        name="New Cases",
    ))

    fig.update_layout(
        title="Daily New Infections",
        template=DARK_TEMPLATE,
        xaxis=dict(title="Day", gridcolor="#2c3e50"),
        yaxis=dict(title="New cases", gridcolor="#2c3e50"),
        plot_bgcolor="#1a1a2e",
        paper_bgcolor="#16213e",
        margin=dict(l=10, r=10, t=60, b=10),
    )
    return fig


def make_sensitivity_chart(sensitivity_df: pd.DataFrame, param: str = "beta") -> go.Figure:
    """Sensitivity analysis: peak infected % vs parameter value."""
    x = sensitivity_df[param]
    y = sensitivity_df["peak_infected_pct"]

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=x, y=y,
        mode="lines+markers",
        line=dict(color="#e74c3c", width=2.5),
        marker=dict(size=8, color="#e74c3c"),
        hovertemplate=f"{param}=%{{x:.2f}}<br>Peak Infected: %{{y:.1f}}%<extra></extra>",
        name="Peak Infected %",
    ))
    # Herd immunity reference
    if param == "beta":
        fig.add_hline(
            y=30, line_dash="dash", line_color="#f39c12",
            annotation_text="Herd immunity (~30% threshold example)",
            annotation_font_color="#f39c12",
        )

    fig.update_layout(
        title=f"Sensitivity Analysis: Peak Infected % vs {param}",
        template=DARK_TEMPLATE,
        xaxis=dict(title=param, gridcolor="#2c3e50"),
        yaxis=dict(title="Peak Infected (%)", gridcolor="#2c3e50"),
        plot_bgcolor="#1a1a2e",
        paper_bgcolor="#16213e",
        margin=dict(l=10, r=10, t=60, b=10),
    )
    return fig


def make_age_stratified_chart(df: pd.DataFrame) -> go.Figure:
    """Stacked area chart showing infectious count per age group over time."""
    fig = go.Figure()
    colors = {"children": "#3498db", "adults": "#e74c3c", "elderly": "#9b59b6"}

    for group, color in colors.items():
        col = f"I_{group}"
        if col not in df.columns:
            continue
        fig.add_trace(go.Scatter(
            x=df["day"],
            y=df[col],
            name=group.capitalize(),
            mode="lines",
            stackgroup="one",
            line=dict(color=color, width=1.5),
            fillcolor=color,
            hovertemplate=f"<b>{group.capitalize()}</b><br>Day %{{x}}<br>Infectious: %{{y:,.0f}}<extra></extra>",
        ))

    fig.update_layout(
        title="Age-Stratified Infectious Population",
        template=DARK_TEMPLATE,
        xaxis=dict(title="Day", gridcolor="#2c3e50"),
        yaxis=dict(title="Infectious", gridcolor="#2c3e50"),
        plot_bgcolor="#1a1a2e",
        paper_bgcolor="#16213e",
        margin=dict(l=10, r=10, t=60, b=10),
    )
    return fig


def make_abm_comparison_chart(
    seir_df: pd.DataFrame,
    abm_df: pd.DataFrame,
    N_seir: int,
    N_abm: int,
) -> go.Figure:
    """
    Overlay SEIRD ODE curve and ABM curve on the same chart.
    Convergence of these two independent methods = cross-model validation.
    """
    fig = go.Figure()

    # Normalise both to percentage of population
    fig.add_trace(go.Scatter(
        x=seir_df["day"],
        y=seir_df["I"] / N_seir * 100,
        name="SEIRD ODE model",
        line=dict(color="#e74c3c", width=2.5, dash="solid"),
        hovertemplate="Day %{x}<br>ODE Infectious: %{y:.2f}%<extra></extra>",
    ))
    fig.add_trace(go.Scatter(
        x=abm_df["day"],
        y=abm_df["I"] / N_abm * 100,
        name="Agent-Based Model",
        line=dict(color="#3498db", width=2.5, dash="dot"),
        hovertemplate="Day %{x}<br>ABM Infectious: %{y:.2f}%<extra></extra>",
    ))

    fig.update_layout(
        title="Cross-Model Validation: ODE vs Agent-Based (convergence = scientific validity)",
        template=DARK_TEMPLATE,
        hovermode="x unified",
        xaxis=dict(title="Day", gridcolor="#2c3e50"),
        yaxis=dict(title="Infectious (% of population)", gridcolor="#2c3e50"),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, x=0),
        plot_bgcolor="#1a1a2e",
        paper_bgcolor="#16213e",
        margin=dict(l=10, r=10, t=70, b=10),
    )
    return fig


# ---------------------------------------------------------------------------
# Utility
# ---------------------------------------------------------------------------
def _hex_to_rgb(hex_color: str) -> str:
    """Convert #RRGGBB to 'R, G, B' string for rgba()."""
    h = hex_color.lstrip("#")
    r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
    return f"{r}, {g}, {b}"
