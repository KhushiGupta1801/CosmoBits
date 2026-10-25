"""CosmoBits — Dedicated International Space Station (ISS) Tracking Page."""
from __future__ import annotations

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from components.cards import render_metric_card, render_status_pill
from services.iss_service import get_humans_in_space, get_iss_ground_track, get_live_iss_telemetry


def render_iss_tracker() -> None:
    """Render the dedicated high-precision ISS live tracker page."""
    st.markdown("## 🛸 International Space Station (ISS) Live Mission Tracker")
    st.caption("Live orbital telemetry, sub-satellite footprint, ground track trajectory, and expedition crew status.")

    # Live ISS Telemetry
    iss = get_live_iss_telemetry()
    crew = get_humans_in_space()

    # Telemetry Badges Row
    t1, t2, t3, t4 = st.columns(4)

    render_metric_card(
        label="Orbital Speed",
        value=f"{iss['speed_kms']:.2f}",
        unit="km/s",
        subtext=f"{iss.get('speed_kmh', 0):,.0f} km/h",
        col=t1,
    )

    render_metric_card(
        label="Orbital Altitude",
        value=f"{iss['alt_km']:.1f}",
        unit="km",
        subtext="Low Earth Orbit",
        col=t2,
    )

    render_metric_card(
        label="Orbital Period",
        value=f"{iss['period_min']:.1f}",
        unit="min",
        subtext="~15.5 revs / day",
        col=t3,
    )

    render_metric_card(
        label="Orbital Inclination",
        value=f"{iss['inclination_deg']:.2f}",
        unit="°",
        subtext="Covers 90% of Earth population",
        col=t4,
    )

    st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)

    # Main Visual Layout: Map & Ground Track
    map_col, info_col = st.columns([2.2, 1.0])

    with map_col:
        st.markdown("### 🗺️ Real-Time Orbit & Ground Track")

        # Future 90 min ground track
        track = get_iss_ground_track(duration_minutes=95)

        fig = go.Figure()

        if track:
            df_track = pd.DataFrame(track)
            fig.add_trace(
                go.Scattergeo(
                    lat=df_track["lat"],
                    lon=df_track["lon"],
                    mode="lines",
                    line=dict(width=3, color="#00F5D4"),
                    name="Projected Orbit Path (Next 90m)",
                    hoverinfo="skip",
                )
            )

        # Current ISS position
        fig.add_trace(
            go.Scattergeo(
                lat=[iss["lat"]],
                lon=[iss["lon"]],
                mode="markers+text",
                marker=dict(size=16, color="#00F5D4", symbol="star", line=dict(width=2.5, color="#FFFFFF")),
                text=["🛸 ISS LIVE"],
                textposition="top right",
                name="ISS Sub-Satellite Point",
                hovertext=(
                    f"<b>International Space Station</b><br>"
                    f"Lat: {iss['lat']:.3f}°, Lon: {iss['lon']:.3f}°<br>"
                    f"Alt: {iss['alt_km']} km | Speed: {iss['speed_kms']} km/s<br>"
                    f"Visibility: {iss.get('visibility', 'Nominal')}"
                ),
                hoverinfo="text",
            )
        )

        fig.update_geos(
            projection_type="natural earth",
            showcoastlines=True,
            coastlinecolor="rgba(0, 245, 212, 0.4)",
            showland=True,
            landcolor="#0B132B",
            showocean=True,
            oceancolor="#040812",
            showcountries=True,
            countrycolor="rgba(255, 255, 255, 0.12)",
            bgcolor="rgba(0,0,0,0)",
        )

        fig.update_layout(
            template="plotly_dark",
            paper_bgcolor="rgba(7, 11, 20, 0.6)",
            plot_bgcolor="rgba(0,0,0,0)",
            margin=dict(l=0, r=0, t=10, b=10),
            height=480,
            legend=dict(orientation="h", y=1.03, x=1, xanchor="right", font=dict(size=10, color="#94A3B8")),
        )
        st.plotly_chart(fig, use_container_width=True)

    with info_col:
        st.markdown("### 📡 Telemetry State")

        pill_html = render_status_pill(iss["status"], "live" if "LIVE" in iss["status"] else "prop")
        st.markdown(
            f"""
            <div class="cosmobits-card">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.75rem;">
                    <span style="font-family: 'Orbitron', sans-serif; font-size: 1.1rem; color: #FFFFFF; font-weight: 700;">
                        ZARYA (ISS)
                    </span>
                    {pill_html}
                </div>
                <div style="font-size: 0.75rem; color: #94A3B8; margin-bottom: 0.75rem;">
                    NORAD ID: <b style="color: #FFF;">25544</b> · Source: <b style="color: #00D2FF;">{iss['source']}</b>
                </div>
                <div style="font-family: 'JetBrains Mono', monospace; font-size: 0.85rem; line-height: 1.8;">
                    <div>LAT: <span style="color: #00F5D4;">{iss['lat']:.4f}°</span></div>
                    <div>LON: <span style="color: #00F5D4;">{iss['lon']:.4f}°</span></div>
                    <div>ALTITUDE: <span style="color: #FFF;">{iss['alt_km']:.1f} km</span></div>
                    <div>GROUND FOOTPRINT: <span style="color: #FFF;">{iss.get('footprint_km', 4500):,.0f} km</span></div>
                    <div>DAY/NIGHT STATE: <span style="color: #FFB703;">{iss.get('visibility', 'Nominal')}</span></div>
                    <div>EPOCH: <span style="color: #94A3B8; font-size: 0.75rem;">{iss['epoch_utc']}</span></div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        # Crew Onboard
        st.markdown("### 👨‍🚀 Humans In Space")
        iss_crew = [p for p in crew if p.get("craft") == "ISS"]
        other_crew = [p for p in crew if p.get("craft") != "ISS"]

        st.markdown(f"**{len(iss_crew)}** onboard ISS · **{len(crew)}** total in orbit")
        for p in iss_crew[:5]:
            st.markdown(f"- 🚀 **{p['name']}** *(ISS)*")
        if other_crew:
            for p in other_crew[:3]:
                st.markdown(f"- 🛸 **{p['name']}** *({p.get('craft')})*")
