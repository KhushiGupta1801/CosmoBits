"""CosmoBits — Satellite Tracking & Ephemeris Inspector Page."""
from __future__ import annotations

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from sgp4.api import Satrec

from components.cards import render_metric_card
from services.orbit_service import compute_satellite_ground_track
from services.tle_service import CATALOGS, get_space_objects, search_satellites


def render_satellite_tracker() -> None:
    """Render the detailed satellite search, tracking, and ephemeris analysis page."""
    st.markdown("## 🛰️ Satellite Tracker & Ephemeris Inspector")
    st.caption("Search across active constellations, inspect real orbital parameters, and visualize projected ground tracks.")

    # Catalog Filter & Search Row
    c1, c2 = st.columns([1.5, 2.5])
    with c1:
        cat_options = ["all"] + list(CATALOGS.keys())
        cat_labels = ["All Loaded Catalogs"] + [CATALOGS[k] for k in CATALOGS.keys()]
        selected_cat = st.selectbox("Filter by Mission Group:", cat_options, format_func=lambda x: "All Catalogs" if x == "all" else CATALOGS.get(x, x))
    with c2:
        search_query = st.text_input("🔍 Search Satellite Name or NORAD Catalog ID:", placeholder="e.g. ISS, HUBBLE, 25544, STARLINK, NOAA...")

    # Load space objects
    groups = list(CATALOGS.keys()) if selected_cat == "all" else [selected_cat]
    objects, status = get_space_objects(groups=groups, max_objects=800)

    # Filter by query
    filtered = search_satellites(search_query, objects) if search_query else objects

    if not filtered:
        st.warning(f"No satellites matching query '{search_query}' found in loaded catalogs.")
        return

    st.markdown(f"Found **{len(filtered)}** satellites matching criteria.")

    # Layout: Selection & Metrics on Left, Ground Track on Right
    s_col, m_col = st.columns([1.2, 2.0])

    with s_col:
        sat_names = [o["name"] for o in filtered]
        selected_sat_name = st.selectbox("Select Spacecraft:", sat_names)
        sat = next((o for o in filtered if o["name"] == selected_sat_name), filtered[0])

        # Telemetry panel
        st.markdown(
            f"""
            <div class="cosmobits-card">
                <div style="font-family: 'Orbitron', sans-serif; font-size: 1.25rem; color: #00F5D4; font-weight: 800;">
                    {sat['name']}
                </div>
                <div style="color: #94A3B8; font-size: 0.8rem; margin-bottom: 0.8rem;">
                    NORAD ID: <b style="color: #FFF;">{sat.get('norad_id', 'Unavailable')}</b> · Class: <b style="color: #00D2FF;">{sat['catalog'].upper()}</b>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        r1, r2 = st.columns(2)
        render_metric_card("Latitude", f"{sat['lat']:.3f}", "°", col=r1)
        render_metric_card("Longitude", f"{sat['lon']:.3f}", "°", col=r2)

        r3, r4 = st.columns(2)
        render_metric_card("Altitude", f"{sat['alt_km']:.1f}", "km", col=r3)
        render_metric_card("Velocity", f"{sat['speed_kms']:.2f}", "km/s", col=r4)

        r5, r6 = st.columns(2)
        render_metric_card("Inclination", f"{sat.get('inclination_deg', 'N/A')}", "°", col=r5)
        render_metric_card("Period", f"{sat.get('period_min', 'N/A')}", "min", col=r6)

        st.caption(f"⏱ Telemetry Epoch: **{sat['epoch_utc']}** (Propagation: SGP4 WGS-84)")

    with m_col:
        st.markdown("### 🗺️ Projected Orbital Ground Track")
        
        # Calculate ground track using SGP4
        ground_track = []
        if "l1" in sat and "l2" in sat:
            try:
                satrec = Satrec.twoline2rv(sat["l1"], sat["l2"])
                ground_track = compute_satellite_ground_track(satrec, duration_minutes=120, step_sec=60)
            except Exception:
                pass

        fig = go.Figure()

        # Add ground track if available
        if ground_track:
            df_track = pd.DataFrame(ground_track)
            fig.add_trace(
                go.Scattergeo(
                    lat=df_track["lat"],
                    lon=df_track["lon"],
                    mode="lines",
                    line=dict(width=2.5, color="#00F5D4"),
                    name="Future Ground Track (2 Orbits)",
                    hoverinfo="skip",
                )
            )

        # Current position marker
        fig.add_trace(
            go.Scattergeo(
                lat=[sat["lat"]],
                lon=[sat["lon"]],
                mode="markers+text",
                marker=dict(size=14, color="#FF007F", symbol="circle", line=dict(width=2, color="#FFFFFF")),
                text=[f"📍 {sat['name']}"],
                textposition="top center",
                name="Current Sub-Satellite Point",
                hovertext=f"<b>{sat['name']}</b><br>Lat: {sat['lat']:.2f}°, Lon: {sat['lon']:.2f}°<br>Alt: {sat['alt_km']} km",
                hoverinfo="text",
            )
        )

        fig.update_geos(
            projection_type="equirectangular",
            showcoastlines=True,
            coastlinecolor="rgba(0, 245, 212, 0.4)",
            showland=True,
            landcolor="#0B132B",
            showocean=True,
            oceancolor="#040812",
            showcountries=True,
            countrycolor="rgba(255, 255, 255, 0.1)",
            bgcolor="rgba(0,0,0,0)",
        )

        fig.update_layout(
            template="plotly_dark",
            paper_bgcolor="rgba(7, 11, 20, 0.6)",
            plot_bgcolor="rgba(0,0,0,0)",
            margin=dict(l=0, r=0, t=10, b=10),
            height=400,
            showlegend=True,
            legend=dict(orientation="h", y=1.05, x=0.5, xanchor="center", font=dict(size=10, color="#94A3B8")),
        )
        st.plotly_chart(fig, use_container_width=True)

    # Detailed Table of Filtered Satellites
    st.markdown("### 📋 Orbit Telemetry Callset")
    table_data = []
    for s in filtered[:100]:
        table_data.append({
            "Name": s["name"],
            "NORAD ID": s.get("norad_id", "N/A"),
            "Catalog": s["catalog"].upper(),
            "Latitude (°)": f"{s['lat']:.3f}",
            "Longitude (°)": f"{s['lon']:.3f}",
            "Altitude (km)": f"{s['alt_km']:.1f}",
            "Speed (km/s)": f"{s['speed_kms']:.2f}",
            "Inclination (°)": f"{s.get('inclination_deg', 'N/A')}",
            "Period (min)": f"{s.get('period_min', 'N/A')}",
            "Epoch (UTC)": s["epoch_utc"],
        })
    df_table = pd.DataFrame(table_data)
    st.dataframe(df_table, use_container_width=True, hide_index=True)
