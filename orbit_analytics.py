"""CosmoBits — Orbital Analytics & Fleet Statistical Profiler."""
from __future__ import annotations

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from components.cards import render_metric_card
from services.tle_service import CATALOGS, get_space_objects


def render_orbit_analytics() -> None:
    """Render interactive statistical charts and orbital parameter distributions."""
    st.markdown("## 📊 Orbit Analytics & Fleet Dynamics")
    st.caption("Empirical distributions of orbital parameters across active satellite constellations.")

    # Load multi-group dataset
    objects, status = get_space_objects(groups=list(CATALOGS.keys()), max_objects=800)

    if not objects:
        st.warning("No orbital dataset available for analysis.")
        return

    df = pd.DataFrame(objects)

    # Classify Orbital Regimes
    def classify_regime(alt: float) -> str:
        if alt < 2000:
            return "LEO (Low Earth Orbit, <2000 km)"
        elif alt < 35000:
            return "MEO (Medium Earth Orbit, 2000-35000 km)"
        elif alt < 36500:
            return "GEO (Geostationary Orbit, ~35786 km)"
        else:
            return "HEO / High Orbit (>36500 km)"

    df["regime"] = df["alt_km"].apply(classify_regime)

    # Top KPI Metrics
    k1, k2, k3, k4 = st.columns(4)
    leo_count = len(df[df["alt_km"] < 2000])
    meo_count = len(df[(df["alt_km"] >= 2000) & (df["alt_km"] < 35000)])
    geo_count = len(df[df["alt_km"] >= 35000])

    render_metric_card("Total Analyzed", f"{len(df):,}", "sats", col=k1)
    render_metric_card("LEO Fleet", f"{leo_count:,}", f"({leo_count/len(df)*100:.1f}%)", subtext="< 2,000 km", col=k2)
    render_metric_card("MEO Constellation", f"{meo_count:,}", "sats", subtext="GPS, Galileo, Glonass", col=k3)
    render_metric_card("GEO / High", f"{geo_count:,}", "sats", subtext="Telecom & Weather", col=k4)

    st.markdown("<div style='height: 12px;'></div>", unsafe_allow_html=True)

    # Chart 1: Velocity vs Altitude Scatter (Vis-viva demonstration)
    st.markdown("### ⚡ Orbital Speed vs. Altitude (Vis-Viva Relation)")
    st.caption("Illustrates Kepler's laws: orbital speed decreases with orbital radius: $v = \\sqrt{\\mu / r}$.")

    fig_vv = px.scatter(
        df,
        x="alt_km",
        y="speed_kms",
        color="catalog",
        hover_name="name",
        hover_data={"alt_km": ":.1f km", "speed_kms": ":.2f km/s", "inclination_deg": True, "catalog": True},
        labels={"alt_km": "Altitude (km)", "speed_kms": "Orbital Speed (km/s)"},
        color_discrete_map={
            "stations": "#00F5D4",
            "visual": "#00D2FF",
            "weather": "#4DD0E1",
            "gps-ops": "#9D4EDD",
            "science": "#34D399",
            "last-30-days": "#FFB703",
            "analyst": "#EF233C",
            "demo": "#94A3B8",
        },
    )
    fig_vv.update_layout(
        template="plotly_dark",
        paper_bgcolor="rgba(7, 11, 20, 0.6)",
        plot_bgcolor="rgba(15, 23, 42, 0.4)",
        height=420,
        margin=dict(l=20, r=20, t=20, b=20),
    )
    st.plotly_chart(fig_vv, use_container_width=True)

    # Row 2: Altitude Distribution & Inclination Distribution
    col_alt, col_inc = st.columns(2)

    with col_alt:
        st.markdown("### 📈 Altitude Distribution")
        fig_alt = px.histogram(
            df[df["alt_km"] < 2500],  # Zoom to LEO cluster
            x="alt_km",
            nbins=35,
            color="catalog",
            labels={"alt_km": "Altitude (km)", "count": "Satellite Count"},
            title="LEO Altitude Clustering (<2,500 km)",
        )
        fig_alt.update_layout(
            template="plotly_dark",
            paper_bgcolor="rgba(7, 11, 20, 0.6)",
            plot_bgcolor="rgba(15, 23, 42, 0.4)",
            height=360,
            margin=dict(l=10, r=10, t=40, b=10),
            showlegend=False,
        )
        st.plotly_chart(fig_alt, use_container_width=True)

    with col_inc:
        st.markdown("### 🧭 Orbital Inclination Distribution")
        fig_inc = px.histogram(
            df,
            x="inclination_deg",
            nbins=36,
            color="catalog",
            labels={"inclination_deg": "Inclination (°)", "count": "Satellite Count"},
            title="Clustering at Key Orbit Angles (ISS 51.6°, SSO ~98°)",
        )
        fig_inc.update_layout(
            template="plotly_dark",
            paper_bgcolor="rgba(7, 11, 20, 0.6)",
            plot_bgcolor="rgba(15, 23, 42, 0.4)",
            height=360,
            margin=dict(l=10, r=10, t=40, b=10),
            showlegend=False,
        )
        st.plotly_chart(fig_inc, use_container_width=True)

    # Row 3: Orbital Period Distribution
    st.markdown("### ⏱️ Orbital Period Distribution")
    fig_period = px.box(
        df[df["period_min"] < 200],  # Filter out GEO for boxplot readability
        x="catalog",
        y="period_min",
        color="catalog",
        points="all",
        labels={"period_min": "Orbital Period (minutes)", "catalog": "Mission Catalog"},
    )
    fig_period.update_layout(
        template="plotly_dark",
        paper_bgcolor="rgba(7, 11, 20, 0.6)",
        plot_bgcolor="rgba(15, 23, 42, 0.4)",
        height=380,
        margin=dict(l=20, r=20, t=20, b=20),
        showlegend=False,
    )
    st.plotly_chart(fig_period, use_container_width=True)
