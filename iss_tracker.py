"""Cosmo Bites — Dedicated International Space Station (ISS) Tracking Page."""
from __future__ import annotations

import textwrap
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
        lat_dir = "N" if iss["lat"] >= 0 else "S"
        lon_dir = "E" if iss["lon"] >= 0 else "W"
        spd = iss.get("speed_kms", 7.66)
        footprint = iss.get("footprint_km", 4500)
        vis = iss.get("visibility", "Nominal")

        telemetry_card_html = f"""
<div class="panel-card">
<div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.65rem;">
<div>
<div style="font-family: var(--font-main); font-size: 1.15rem; color: #FFFFFF; font-weight: 700;">
ZARYA (ISS)
</div>
<div style="font-size: 0.74rem; color: #94A3B8;">
NORAD ID: <b style="color: #FFF;">25544</b> · Source: <b style="color: #00D4FF;">{iss['source']}</b>
</div>
</div>
<div>{pill_html}</div>
</div>

<div class="telem-grid" style="margin: 0.5rem 0;">
<div>
<div class="telem-cell-label">LATITUDE</div>
<div class="telem-cell-val cyan">{abs(iss['lat']):.4f}° {lat_dir}</div>
</div>
<div>
<div class="telem-cell-label">LONGITUDE</div>
<div class="telem-cell-val cyan">{abs(iss['lon']):.4f}° {lon_dir}</div>
</div>
<div>
<div class="telem-cell-label">ALTITUDE</div>
<div class="telem-cell-val">{iss['alt_km']:.1f} km</div>
</div>
<div>
<div class="telem-cell-label">VELOCITY</div>
<div class="telem-cell-val">{spd:.2f} km/s</div>
</div>
<div>
<div class="telem-cell-label">FOOTPRINT</div>
<div class="telem-cell-val">{footprint:,.0f} km</div>
</div>
<div>
<div class="telem-cell-label">SOLAR STATE</div>
<div class="telem-cell-val amber">{vis}</div>
</div>
</div>

<div style="font-family: var(--font-mono); font-size: 0.7rem; color: #94A3B8; margin-top: 0.45rem; padding-top: 0.4rem; border-top: 1px solid rgba(255,255,255,0.06);">
EPOCH: <span style="color: #CBD5E1;">{iss['epoch_utc']}</span>
</div>
</div>
"""
        from components.cards import render_html
        render_html(telemetry_card_html)

        # Crew Onboard
        st.markdown("### 👨‍🚀 Humans In Space")
        iss_crew = [p for p in crew if p.get("craft") == "ISS"]
        other_crew = [p for p in crew if p.get("craft") != "ISS"]

        crew_items_html = ""
        for p in iss_crew[:5]:
            crew_items_html += f'<div style="padding: 3px 0; font-size: 0.8rem; color: #CBD5E1;">🚀 <b style="color: #FFF;">{p["name"]}</b> <span style="color: #00D4FF; font-size: 0.72rem;">(ISS)</span></div>'
        for p in other_crew[:3]:
            crew_items_html += f'<div style="padding: 3px 0; font-size: 0.8rem; color: #CBD5E1;">🛸 <b style="color: #FFF;">{p["name"]}</b> <span style="color: #94A3B8; font-size: 0.72rem;">({p.get("craft")})</span></div>'

        crew_card_html = f"""
<div class="panel-card">
<div style="font-size: 0.78rem; font-weight: 700; color: #00D4FF; margin-bottom: 0.45rem;">
ORBITAL EXPEDITION CREW ({len(iss_crew)} ISS · {len(crew)} Total)
</div>
{crew_items_html}
</div>
"""
        render_html(crew_card_html)
