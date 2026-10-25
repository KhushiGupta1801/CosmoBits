"""CosmoBits — NOAA SWPC Space Weather Telemetry Page."""
from __future__ import annotations

import plotly.graph_objects as go
import streamlit as st

from components.cards import render_metric_card
from services.space_weather_service import get_space_weather_data


def render_space_weather() -> None:
    """Render solar activity, planetary Kp indices, and satellite operational impact metrics."""
    st.markdown("## ☀️ Space Weather & Solar-Terrestrial Physics")
    st.caption("Live solar telemetry and geomagnetic indices from the NOAA Space Weather Prediction Center (SWPC).")

    weather = get_space_weather_data()

    # Top KPI Metrics
    m1, m2, m3, m4 = st.columns(4)

    kp = weather["kp_index"]
    render_metric_card(
        label="Planetary Kp Index",
        value=f"{kp:.2f}",
        unit="/ 9.0",
        subtext=f"Activity: {weather['kp_category']}",
        col=m1,
    )

    render_metric_card(
        label="10.7cm Solar Flux",
        value=f"{weather['solar_radio_flux_sfu']:.0f}",
        unit="sfu",
        subtext="Proxy for solar EUV",
        col=m2,
    )

    render_metric_card(
        label="Solar Wind Speed",
        value=f"{weather['solar_wind_speed_kms']:.1f}",
        unit="km/s",
        subtext="Proton stream velocity",
        col=m3,
    )

    render_metric_card(
        label="Geomagnetic Storm",
        value=weather["geomagnetic_scale"].split(" ")[0],
        unit="",
        subtext=weather["geomagnetic_scale"],
        col=m4,
    )

    st.markdown("<div style='height: 12px;'></div>", unsafe_allow_html=True)

    # Kp Index History Gauge & Trend
    col_kp, col_scales = st.columns([1.5, 1.5])

    with col_kp:
        st.markdown("### 📊 Planetary Kp Trend (Recent 24h)")
        kp_hist = weather.get("kp_history", [2.0, 2.3, 1.7, 3.0, 2.7, 2.3, 1.3, 2.0])
        labels = [f"T-{3 * (len(kp_hist) - 1 - i)}h" for i in range(len(kp_hist))]

        fig_kp = go.Figure()
        # Bar chart with color-coded severity
        bar_colors = ["#EF233C" if v >= 5 else "#FFB703" if v >= 4 else "#00F5D4" for v in kp_hist]

        fig_kp.add_trace(
            go.Bar(
                x=labels,
                y=kp_hist,
                marker=dict(color=bar_colors),
                text=[f"{v:.1f}" for v in kp_hist],
                textposition="auto",
                name="Kp Index",
            )
        )

        # Storm threshold line at Kp = 5
        fig_kp.add_hline(
            y=5.0,
            line_dash="dash",
            line_color="#EF233C",
            annotation_text="G1 Storm Threshold (Kp=5)",
            annotation_position="top left",
            annotation_font=dict(color="#EF233C", size=10),
        )

        fig_kp.update_layout(
            template="plotly_dark",
            paper_bgcolor="rgba(7, 11, 20, 0.6)",
            plot_bgcolor="rgba(15, 23, 42, 0.4)",
            yaxis=dict(title="Kp Index (0-9)", range=[0, 9]),
            height=320,
            margin=dict(l=20, r=20, t=20, b=20),
        )
        st.plotly_chart(fig_kp, use_container_width=True)

    with col_scales:
        st.markdown("### 🌐 NOAA Space Weather Scales")
        st.markdown(
            f"""
            <div class="cosmobits-card">
                <div style="font-size: 0.9rem; margin-bottom: 0.6rem;">
                    <b>Geomagnetic Storms (G-Scale):</b> <span style="color: #00F5D4;">{weather['geomagnetic_scale']}</span>
                </div>
                <div style="font-size: 0.9rem; margin-bottom: 0.6rem;">
                    <b>Solar Radiation Storms (S-Scale):</b> <span style="color: #00D2FF;">{weather['solar_radiation_scale']}</span>
                </div>
                <div style="font-size: 0.9rem; margin-bottom: 0.6rem;">
                    <b>Radio Blackouts (R-Scale):</b> <span style="color: #9D4EDD;">{weather['radio_blackout_scale']}</span>
                </div>
                <div style="font-size: 0.78rem; color: #94A3B8; margin-top: 0.8rem; padding-top: 0.6rem; border-top: 1px solid rgba(255,255,255,0.08);">
                    Source: <b>{weather['source']}</b><br>
                    Telemetry Timestamp: <code>{weather['timestamp_utc']}</code>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    # Satellite Operational Impact Matrix
    st.markdown("### 🛰️ Spacecraft Telemetry & Operational Impacts")
    i1, i2, i3 = st.columns(3)

    with i1:
        st.markdown(
            f"""
            <div class="cosmobits-card" style="height: 100%;">
                <h4 style="color: #00F5D4; font-size: 0.95rem; margin-bottom: 0.4rem;">
                    💨 LEO Atmospheric Drag
                </h4>
                <p style="font-size: 0.82rem; color: #E2E8F0; line-height: 1.4;">
                    {weather['satellite_drag_impact']}
                </p>
                <div style="font-size: 0.72rem; color: #94A3B8; margin-top: 0.5rem;">
                    UV/geomagnetic energy heats thermosphere, increasing neutral gas density up to 800 km altitude.
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with i2:
        st.markdown(
            f"""
            <div class="cosmobits-card" style="height: 100%;">
                <h4 style="color: #00D2FF; font-size: 0.95rem; margin-bottom: 0.4rem;">
                    📡 GNSS & Ionospheric Delay
                </h4>
                <p style="font-size: 0.82rem; color: #E2E8F0; line-height: 1.4;">
                    {weather['gnss_impact']}
                </p>
                <div style="font-size: 0.72rem; color: #94A3B8; margin-top: 0.5rem;">
                    Total Electron Content (TEC) gradients cause phase scintillation and group delay on L-band signals.
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with i3:
        st.markdown(
            f"""
            <div class="cosmobits-card" style="height: 100%;">
                <h4 style="color: #FFB703; font-size: 0.95rem; margin-bottom: 0.4rem;">
                    ⚡ Avionics & Radiation Hazard
                </h4>
                <p style="font-size: 0.82rem; color: #E2E8F0; line-height: 1.4;">
                    {weather['radiation_impact']}
                </p>
                <div style="font-size: 0.72rem; color: #94A3B8; margin-top: 0.5rem;">
                    Trapped relativistic electrons in Van Allen belts elevate internal dielectric breakdown risks.
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
