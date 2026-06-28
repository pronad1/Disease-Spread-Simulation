"""
ui/components/geo_map.py
=========================
Bangladesh district-level disease burden heatmap using Folium.

Uses synthetic simulation data distributed across 8 major divisions
(Dhaka, Chattogram, Sylhet, Rajshahi, Khulna, Barishal, Mymensingh, Rangpur).
When a GADM shapefile is available, renders a full choropleth.
Falls back to circle markers if geopandas is not available.
"""

from __future__ import annotations

import json
import numpy as np
import pandas as pd

try:
    import folium
    FOLIUM_AVAILABLE = True
except ImportError:
    FOLIUM_AVAILABLE = False

try:
    import plotly.express as px
    PLOTLY_AVAILABLE = True
except ImportError:
    PLOTLY_AVAILABLE = False


# Bangladesh division centroids (lat, lon) + population weights
BANGLADESH_DIVISIONS = {
    "Dhaka":       {"lat": 23.8103, "lon": 90.4125, "pop_weight": 0.32, "color": "#e74c3c"},
    "Chattogram":  {"lat": 22.3569, "lon": 91.7832, "pop_weight": 0.20, "color": "#e67e22"},
    "Sylhet":      {"lat": 24.8949, "lon": 91.8687, "pop_weight": 0.08, "color": "#f39c12"},
    "Rajshahi":    {"lat": 24.3636, "lon": 88.6241, "pop_weight": 0.10, "color": "#3498db"},
    "Khulna":      {"lat": 22.8456, "lon": 89.5403, "pop_weight": 0.10, "color": "#9b59b6"},
    "Barishal":    {"lat": 22.7010, "lon": 90.3535, "pop_weight": 0.07, "color": "#1abc9c"},
    "Mymensingh":  {"lat": 24.7471, "lon": 90.4203, "pop_weight": 0.07, "color": "#2ecc71"},
    "Rangpur":     {"lat": 25.7439, "lon": 89.2752, "pop_weight": 0.06, "color": "#e91e63"},
}


def generate_division_data(
    total_infected: int,
    total_deaths: int,
    simulation_day: int,
    seed: int = 42,
) -> pd.DataFrame:
    """
    Distribute simulated totals across Bangladesh divisions.
    Uses population weighting with small random variation.
    """
    rng = np.random.default_rng(seed + simulation_day)
    rows = []
    for div, info in BANGLADESH_DIVISIONS.items():
        weight = info["pop_weight"]
        # Add ±20% random variation around population weight
        noise = rng.uniform(0.80, 1.20)
        actual_weight = weight * noise

        infected = int(total_infected * actual_weight)
        deaths = int(total_deaths * actual_weight)
        infected_pct = round(infected / (total_infected + 1) * 100, 2)

        rows.append({
            "division": div,
            "lat": info["lat"],
            "lon": info["lon"],
            "infected": infected,
            "deaths": deaths,
            "infected_pct": infected_pct,
            "color": info["color"],
        })

    return pd.DataFrame(rows)


def build_folium_map(division_df: pd.DataFrame, zoom: int = 7) -> "folium.Map | None":
    """
    Build a Folium choropleth bubble map centred on Bangladesh.
    Circle radius scales with infection count.
    """
    if not FOLIUM_AVAILABLE:
        return None

    m = folium.Map(
        location=[23.7, 90.4],
        zoom_start=zoom,
        tiles="CartoDB dark_matter",
    )

    max_infected = division_df["infected"].max() or 1

    for _, row in division_df.iterrows():
        radius = 15 + 45 * (row["infected"] / max_infected)

        folium.CircleMarker(
            location=[row["lat"], row["lon"]],
            radius=radius,
            color=row["color"],
            fill=True,
            fill_color=row["color"],
            fill_opacity=0.6,
            popup=folium.Popup(
                f"""
                <b>{row['division']}</b><br>
                Infected: <b>{row['infected']:,}</b><br>
                Deaths: <b>{row['deaths']:,}</b><br>
                Share: <b>{row['infected_pct']:.1f}%</b>
                """,
                max_width=200,
            ),
            tooltip=f"{row['division']}: {row['infected']:,} infected",
        ).add_to(m)

        # Division label
        folium.Marker(
            location=[row["lat"] + 0.1, row["lon"]],
            icon=folium.DivIcon(
                html=f'<div style="font-size:10px;color:white;font-weight:bold;text-shadow:1px 1px 2px black">'
                     f'{row["division"]}</div>',
                icon_size=(100, 20),
                icon_anchor=(0, 0),
            ),
        ).add_to(m)

    return m


def build_plotly_bubble_map(division_df: pd.DataFrame) -> "px.Figure":
    """Plotly scatter_mapbox as a fallback / embedded option."""
    fig = px.scatter_mapbox(
        division_df,
        lat="lat",
        lon="lon",
        size="infected",
        color="infected_pct",
        color_continuous_scale="Reds",
        hover_name="division",
        hover_data={"infected": True, "deaths": True, "infected_pct": ":.2f"},
        size_max=50,
        zoom=6,
        center={"lat": 23.7, "lon": 90.4},
        mapbox_style="carto-darkmatter",
        title="Disease Burden by Bangladesh Division",
        labels={"infected_pct": "Infected %", "infected": "Infected", "deaths": "Deaths"},
    )
    fig.update_layout(
        paper_bgcolor="#16213e",
        font_color="#ecf0f1",
        margin=dict(l=0, r=0, t=40, b=0),
        coloraxis_colorbar=dict(tickfont=dict(color="#ecf0f1"), title_font=dict(color="#ecf0f1")),
    )
    return fig
