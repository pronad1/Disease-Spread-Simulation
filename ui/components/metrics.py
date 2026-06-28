"""
ui/components/metrics.py
=========================
Streamlit metric cards for the EpiSim dashboard.
"""

from __future__ import annotations
import streamlit as st


def render_summary_metrics(summary: dict, prev_summary: dict | None = None):
    """
    Render 6 metric cards in a 3+3 grid.
    Shows delta from previous scenario if provided.
    """
    col1, col2, col3 = st.columns(3)

    def _delta(key: str, fmt="{:+,.0f}") -> str | None:
        if prev_summary and key in prev_summary:
            diff = summary[key] - prev_summary[key]
            return fmt.format(diff)
        return None

    with col1:
        st.metric(
            label="🦠 Basic Reproduction Number (R₀)",
            value=f"{summary['R0']:.2f}",
            help="R₀ > 1 → epidemic grows. R₀ < 1 → disease dies out. Formula: β / γ",
        )
    with col2:
        st.metric(
            label="📈 Peak Infectious",
            value=f"{summary['peak_infected']:,}",
            delta=_delta("peak_infected"),
            delta_color="inverse",
            help="Maximum number of simultaneously infectious individuals.",
        )
    with col3:
        st.metric(
            label="📅 Peak Day",
            value=f"Day {summary['peak_day']}",
            help="Day on which the infectious peak occurs.",
        )

    col4, col5, col6 = st.columns(3)

    with col4:
        st.metric(
            label="💉 Herd Immunity Threshold",
            value=f"{summary['herd_immunity_threshold_pct']:.1f}%",
            help="Fraction of population needing immunity to halt epidemic spread. Formula: 1 − 1/R₀",
        )
    with col5:
        st.metric(
            label="💀 Total Deaths",
            value=f"{summary['total_deaths']:,}",
            delta=_delta("total_deaths"),
            delta_color="inverse",
        )
    with col6:
        st.metric(
            label="🌍 Total Affected",
            value=f"{summary['total_affected_pct']:.1f}%",
            delta=_delta("total_affected_pct", "{:+.1f}%"),
            delta_color="inverse",
            help="Percentage of population that was ever infected or died.",
        )


def render_herd_immunity_progress(current_immune_pct: float, threshold_pct: float):
    """Visual progress bar toward herd immunity threshold."""
    progress = min(current_immune_pct / threshold_pct, 1.0) if threshold_pct > 0 else 0.0

    st.markdown("#### 💉 Herd Immunity Progress")
    col_a, col_b = st.columns([3, 1])
    with col_a:
        st.progress(progress, text=f"{current_immune_pct:.1f}% immune (target: {threshold_pct:.1f}%)")
    with col_b:
        status = "✅ Achieved" if progress >= 1.0 else f"{progress*100:.0f}%"
        st.markdown(f"**{status}**")


def render_r0_gauge(R0: float) -> None:
    """Simple coloured R0 indicator."""
    if R0 < 1.0:
        color, status = "🟢", "Epidemic declining"
    elif R0 < 2.0:
        color, status = "🟡", "Slow spread"
    elif R0 < 5.0:
        color, status = "🟠", "Moderate spread"
    else:
        color, status = "🔴", "Rapid outbreak"

    st.markdown(f"{color} **R₀ = {R0:.2f}** — {status}")
