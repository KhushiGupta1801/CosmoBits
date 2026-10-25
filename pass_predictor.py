"""CosmoBits — Ground Observer Satellite Pass Predictor."""
from __future__ import annotations

from datetime import datetime, timezone
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from sgp4.api import Satrec

from components.cards import render_metric_card
from services.orbit_service import predict_passes_sgp4
from services.tle_service import get_space_objects

# Global Ground Stations & City Presets
OBSERVER_PRESETS = {
    "Bengaluru, India (ISRO HQ)": (12.9716, 77.5946, 920.0),
    "Cape Canaveral, USA (KSC)": (28.3922, -80.6077, 3.0),
    "Houston, USA (NASA JSC)": (29.5593, -95.0900, 7.0),
    "London, United Kingdom": (51.5074, -0.1278, 25.0),
    "Tokyo, Japan": (35.6762, 139.6503, 40.0),
    "Sydney, Australia": (-33.8688, 151.2093, 19.0),
    "Kourou, French Guiana (CSG)": (5.2372, -52.7606, 15.0),
    "Custom Location": (0.0, 0.0, 0.0),
}


def render_pass_predictor() -> None:
    """Render topocentric horizon pass calculations and sky visibility predictions."""
    st.markdown("## 🔭 Satellite Pass Predictor & Ground Station Visibility")
    st.caption("Calculate upcoming orbital passes, azimuth/elevation angles, and optical visibility over your coordinates.")

    # Honest Physical Limitation Notice
    st.info(
        "ℹ️ **Pass Prediction Accuracy & Limitations**: "
        "Calculated using SGP4 analytical propagation against current TLE orbital elements. "
        "Predictions do not account for unplanned orbit-raising maneuvers or solar storm thermospheric drag surges. "
        "Atmospheric refraction is neglected for elevations below 10°."
    )

    # Observer Location Configuration Row
    col_preset, col_lat, col_lon, col_alt = st.columns([1.5, 1.0, 1.0, 1.0])

    with col_preset:
        preset_choice = st.selectbox("Ground Station Preset:", list(OBSERVER_PRESETS.keys()), index=0)
        p_lat, p_lon, p_alt = OBSERVER_PRESETS[preset_choice]

    with col_lat:
        obs_lat = st.number_input("Latitude (°)", value=p_lat, min_value=-90.0, max_value=90.0, format="%.4f")
    with col_lon:
        obs_lon = st.number_input("Longitude (°)", value=p_lon, min_value=-180.0, max_value=180.0, format="%.4f")
    with col_alt:
        obs_alt = st.number_input("Elevation (m)", value=p_alt, min_value=0.0, max_value=8848.0, format="%.1f")

    # Satellite Selection & Parameters Row
    objects, status = get_space_objects(groups=["stations", "visual", "weather", "science"], max_objects=250)
    sat_names = [o["name"] for o in objects]

    p1, p2, p3 = st.columns([2.0, 1.0, 1.0])
    with p1:
        def_idx = 0
        for i, n in enumerate(sat_names):
            if "ISS" in n:
                def_idx = i
                break
        selected_sat = st.selectbox("Select Target Satellite:", sat_names, index=def_idx if sat_names else 0)

    with p2:
        duration_hrs = st.slider("Prediction Horizon:", min_value=12, max_value=72, value=48, step=12)

    with p3:
        min_el = st.slider("Min Elevation (°):", min_value=5, max_value=30, value=10, step=5)

    sat_obj = next((o for o in objects if o["name"] == selected_sat), None)

    if not sat_obj or "l1" not in sat_obj or "l2" not in sat_obj:
        st.warning("Selected satellite does not contain valid TLE orbital elements.")
        return

    # Calculate passes
    with st.spinner("Propagating SGP4 topocentric horizon vectors..."):
        satrec = Satrec.twoline2rv(sat_obj["l1"], sat_obj["l2"])
        passes = predict_passes_sgp4(
            satrec=satrec,
            obs_lat=obs_lat,
            obs_lon=obs_lon,
            obs_alt_m=obs_alt,
            duration_hours=float(duration_hrs),
            min_elevation_deg=float(min_el),
        )

    st.markdown(f"### Upcoming Passes for **{sat_obj['name']}** ({len(passes)} detected in next {duration_hrs}h)")

    if not passes:
        st.info("No passes exceeding the minimum elevation threshold were detected over the specified window.")
        return

    # Display Next Pass Highlight
    next_pass = passes[0]
    np1, np2, np3, np4 = st.columns(4)
    render_metric_card(
        label="Next Pass Start (AOS)",
        value=next_pass["aos_utc"].strftime("%d %b %H:%M"),
        unit="UTC",
        subtext=f"Az: {next_pass['aos_az']:.0f}° ({next_pass['aos_dir']})",
        col=np1,
    )
    render_metric_card(
        label="Peak Elevation (TCA)",
        value=f"{next_pass['max_el']:.1f}",
        unit="°",
        subtext=f"Az: {next_pass['tca_az']:.0f}° ({next_pass['tca_dir']})",
        col=np2,
    )
    render_metric_card(
        label="Pass Duration",
        value=f"{next_pass['duration_min']:.1f}",
        unit="min",
        subtext=f"Closest Range: {next_pass['min_range_km']:,.0f} km",
        col=np3,
    )
    render_metric_card(
        label="Pass Quality",
        value=next_pass["quality"].split(" ")[0],
        unit="",
        subtext=next_pass["quality"],
        col=np4,
    )

    st.markdown("<div style='height: 12px;'></div>", unsafe_allow_html=True)

    # Polar Sky Chart of Next Pass
    col_sky, col_table = st.columns([1.5, 1.8])

    with col_sky:
        st.markdown("#### 🧭 Polar Sky Track (Observer Horizon)")
        if "points" in next_pass and next_pass["points"]:
            df_pts = pd.DataFrame(next_pass["points"])
            # In polar sky chart: r is (90 - el) so center is zenith (90) and edge is horizon (0)
            df_pts["r_zenith"] = 90.0 - df_pts["el"]

            fig_sky = go.Figure()
            fig_sky.add_trace(
                go.Scatterpolar(
                    r=df_pts["r_zenith"],
                    theta=df_pts["az"],
                    mode="lines+markers",
                    line=dict(color="#00F5D4", width=3),
                    marker=dict(size=5, color="#00D2FF"),
                    name="Trajectory",
                    hoverinfo="text",
                    hovertext=[f"El: {pt['el']}° | Az: {pt['az']}° | Range: {pt['range_km']} km" for pt in next_pass["points"]],
                )
            )

            fig_sky.update_layout(
                template="plotly_dark",
                paper_bgcolor="rgba(7, 11, 20, 0.6)",
                polar=dict(
                    bgcolor="rgba(15, 23, 42, 0.6)",
                    angularaxis=dict(
                        direction="clockwise",
                        rotation=90,  # North at top
                        period=360,
                        tickmode="array",
                        tickvals=[0, 45, 90, 135, 180, 225, 270, 315],
                        ticktext=["N (0°)", "NE", "E (90°)", "SE", "S (180°)", "SW", "W (270°)", "NW"],
                        tickfont=dict(color="#94A3B8", size=9),
                    ),
                    radialaxis=dict(
                        range=[90, 0],  # Zenith at center, horizon at rim
                        tickvals=[90, 60, 30, 0],
                        ticktext=["0° (Horizon)", "30°", "60°", "90° (Zenith)"],
                        tickfont=dict(color="#64748B", size=8),
                    ),
                ),
                height=360,
                margin=dict(l=20, r=20, t=20, b=20),
                showlegend=False,
            )
            st.plotly_chart(fig_sky, use_container_width=True)

    with col_table:
        st.markdown("#### 📋 Pass Schedule Table")
        sched = []
        for p in passes:
            sched.append({
                "Date (UTC)": p["aos_utc"].strftime("%Y-%m-%d"),
                "AOS Time": p["aos_utc"].strftime("%H:%M:%S"),
                "TCA Time": p["tca_utc"].strftime("%H:%M:%S"),
                "LOS Time": p["los_utc"].strftime("%H:%M:%S"),
                "Duration": f"{p['duration_min']:.1f} min",
                "Max El": f"{p['max_el']:.1f}°",
                "AOS Azimuth": f"{p['aos_az']:.0f}° ({p['aos_dir']})",
                "LOS Azimuth": f"{p['los_az']:.0f}° ({p['los_dir']})",
                "Quality": p["quality"],
            })
        st.dataframe(pd.DataFrame(sched), use_container_width=True, hide_index=True)
