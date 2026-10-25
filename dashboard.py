"""CosmoBits — Mission Control Dashboard Page."""
from __future__ import annotations

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from components.cards import render_metric_card, render_nav_card, render_status_pill
from services.iss_service import get_live_iss_telemetry
from services.space_weather_service import get_space_weather_data
from services.tle_service import get_space_objects


def render_dashboard() -> None:
    """Render the central operations overview dashboard."""
    st.markdown("## 🛰️ Orbital Command Center")
    st.caption("Real-time telemetry, space environment indicators, and orbital fleet tracking.")

    # Fetch live telemetry datasets
    objects, status = get_space_objects()
    iss_data = get_live_iss_telemetry()
    weather_data = get_space_weather_data()

    # Metric Row 1
    m1, m2, m3, m4 = st.columns(4)

    total_sats = len(objects)
    render_metric_card(
        label="Tracked Fleet",
        value=f"{total_sats:,}",
        unit="Objects",
        subtext=f"Source: {status.get('source', 'SGP4')}",
        col=m1,
    )

    render_metric_card(
        label="ISS Velocity",
        value=f"{iss_data['speed_kms']:.2f}",
        unit="km/s",
        subtext=f"Alt: {iss_data['alt_km']:.1f} km",
        col=m2,
    )

    kp = weather_data["kp_index"]
    render_metric_card(
        label="Geomagnetic Kp",
        value=f"{kp:.1f}",
        unit="/ 9.0",
        subtext=f"Status: {weather_data['kp_category']}",
        col=m3,
    )

    render_metric_card(
        label="Solar 10.7cm Flux",
        value=f"{weather_data['solar_radio_flux_sfu']:.0f}",
        unit="sfu",
        subtext=weather_data["geomagnetic_scale"],
        col=m4,
    )

    st.markdown("<div style='height: 12px;'></div>", unsafe_allow_html=True)

    # Main 2D Interactive Tracking Map
    col_map, col_details = st.columns([2.2, 1.0])

    with col_map:
        st.markdown("### 🌍 Global Ground Track & Orbital Fleet")
        if objects:
            df = pd.DataFrame(objects)
            # Create interactive Scattergeo map
            fig = px.scatter_geo(
                df,
                lat="lat",
                lon="lon",
                hover_name="name",
                color="catalog",
                size="radius",
                hover_data={
                    "lat": ":.2f",
                    "lon": ":.2f",
                    "alt_km": ":.0f km",
                    "speed_kms": ":.2f km/s",
                    "catalog": True,
                    "radius": False,
                },
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

            # Add prominent ISS marker
            fig.add_trace(
                go.Scattergeo(
                    lat=[iss_data["lat"]],
                    lon=[iss_data["lon"]],
                    mode="markers+text",
                    marker=dict(size=14, color="#00F5D4", symbol="star", line=dict(width=2, color="#FFFFFF")),
                    text=["🛸 ISS"],
                    textposition="top right",
                    name="ISS Live",
                    hoverinfo="text",
                    hovertext=f"<b>ISS (International Space Station)</b><br>Lat: {iss_data['lat']:.2f}°, Lon: {iss_data['lon']:.2f}°<br>Alt: {iss_data['alt_km']} km | Speed: {iss_data['speed_kms']} km/s",
                )
            )

            fig.update_geos(
                projection_type="natural earth",
                showcoastlines=True,
                coastlinecolor="rgba(0, 245, 212, 0.35)",
                showland=True,
                landcolor="#0B132B",
                showocean=True,
                oceancolor="#040812",
                showlakes=True,
                lakecolor="#040812",
                showcountries=True,
                countrycolor="rgba(255, 255, 255, 0.08)",
                bgcolor="rgba(0,0,0,0)",
            )

            fig.update_layout(
                template="plotly_dark",
                paper_bgcolor="rgba(7, 11, 20, 0.6)",
                plot_bgcolor="rgba(0,0,0,0)",
                margin=dict(l=0, r=0, t=10, b=10),
                legend=dict(
                    orientation="h",
                    yanchor="bottom",
                    y=1.02,
                    xanchor="right",
                    x=1,
                    font=dict(size=10, color="#94A3B8"),
                ),
                height=480,
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.warning("No satellite objects available in the current propagation pass.")

    with col_details:
        st.markdown("### 📡 Selected Telemetry")

        # Satellite selection widget
        sat_names = [o["name"] for o in objects]
        default_index = 0
        # Prefer ISS if in list
        for i, name in enumerate(sat_names):
            if "ISS" in name:
                default_index = i
                break

        selected_name = st.selectbox("Select Spacecraft:", sat_names, index=default_index)
        selected_obj = next((o for o in objects if o["name"] == selected_name), objects[0] if objects else None)

        if selected_obj:
            st.markdown(
                f"""
                <div class="cosmobits-card">
                    <div style="font-family: 'Orbitron', sans-serif; font-size: 1.1rem; color: #00F5D4; font-weight: 700; margin-bottom: 0.5rem;">
                        {selected_obj['name']}
                    </div>
                    <div style="font-size: 0.75rem; color: #94A3B8; margin-bottom: 1rem;">
                        NORAD ID: <b style="color: #FFF;">{selected_obj.get('norad_id', 'N/A')}</b> · Catalog: <b style="color: #00D2FF;">{selected_obj['catalog'].upper()}</b>
                    </div>
                    <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 0.75rem; font-family: 'JetBrains Mono', monospace; font-size: 0.85rem;">
                        <div>
                            <span style="color: #64748B;">LAT:</span> <span style="color: #FFF;">{selected_obj['lat']:.3f}°</span>
                        </div>
                        <div>
                            <span style="color: #64748B;">LON:</span> <span style="color: #FFF;">{selected_obj['lon']:.3f}°</span>
                        </div>
                        <div>
                            <span style="color: #64748B;">ALT:</span> <span style="color: #00F5D4;">{selected_obj['alt_km']:.1f} km</span>
                        </div>
                        <div>
                            <span style="color: #64748B;">SPEED:</span> <span style="color: #00D2FF;">{selected_obj['speed_kms']:.2f} km/s</span>
                        </div>
                        <div>
                            <span style="color: #64748B;">INCL:</span> <span style="color: #FFF;">{selected_obj.get('inclination_deg', 'N/A')}°</span>
                        </div>
                        <div>
                            <span style="color: #64748B;">PERIOD:</span> <span style="color: #FFF;">{selected_obj.get('period_min', 'N/A')} m</span>
                        </div>
                    </div>
                    <div style="margin-top: 1rem; padding-top: 0.75rem; border-top: 1px solid rgba(255, 255, 255, 0.08); font-size: 0.72rem; color: #94A3B8;">
                        Epoch: {selected_obj['epoch_utc']}
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

        # Space Weather snapshot
        st.markdown(
            f"""
            <div class="cosmobits-card" style="margin-top: 0.5rem;">
                <div style="font-size: 0.8rem; font-weight: 700; color: #FFB703; text-transform: uppercase; letter-spacing: 0.05em; margin-bottom: 0.35rem;">
                    ☀️ Space Weather Environment
                </div>
                <div style="font-size: 0.85rem; color: #E2E8F0; line-height: 1.4;">
                    Geomagnetic Condition: <b>{weather_data['geomagnetic_scale']}</b>
                </div>
                <div style="font-size: 0.75rem; color: #94A3B8; margin-top: 0.35rem;">
                    {weather_data['satellite_drag_impact']}
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown("---")

    # Quick Navigation Cards
    st.markdown("### 🚀 Mission Navigation Hub")
    q1, q2, q3, q4 = st.columns(4)

    with q1:
        render_nav_card(
            title="3D Earth",
            description="Explore orbital trajectories on an interactive 3D digital globe.",
            icon="🌐",
        )
    with q2:
        render_nav_card(
            title="Satellite Tracker",
            description="Search 600+ satellites by NORAD ID or name with live pass prediction.",
            icon="🛰️",
        )
    with q3:
        render_nav_card(
            title="ISS Live",
            description="Dedicated Space Station telemetry, velocity, and onboard crew tracker.",
            icon="🛸",
        )
    with q4:
        render_nav_card(
            title="AI Space Assistant",
            description="Consult the AI aerospace specialist on orbits, space weather, and physics.",
            icon="🤖",
        )
