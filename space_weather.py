"""Cosmo Bites — Space Weather & Solar-Terrestrial Physics Page."""
from __future__ import annotations

import textwrap
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from components.cards import render_html, render_metric_card
from services.space_weather_service import get_space_weather_data


def render_space_weather() -> None:
    """Render NOAA SWPC space weather indicators and satellite operational impact models."""
    st.markdown("## ☀️ Space Weather & Solar-Terrestrial Physics")
    st.caption("Live solar flux, planetary geomagnetic activity, and atmospheric drag assessment from NOAA SWPC.")

    weather = get_space_weather_data()

    # KPI telemetry tiles
    c1, c2, c3, c4 = st.columns(4)

    kp = weather["kp_index"]
    render_metric_card(
        label="Planetary Kp Index",
        value=f"{kp:.1f}",
        unit="/ 9.0",
        subtext=f"Condition: {weather['kp_category']}",
        col=c1,
    )

    render_metric_card(
        label="Solar 10.7cm Radio Flux",
        value=f"{weather['solar_radio_flux_sfu']:.0f}",
        unit="sfu",
        subtext="Dominant LEO thermosphere heating",
        col=c2,
    )

    render_metric_card(
        label="Solar Wind Speed",
        value=f"{weather['solar_wind_speed_kms']:.0f}",
        unit="km/s",
        subtext="Interplanetary proton flux",
        col=c3,
    )

    render_metric_card(
        label="Geomagnetic Storm",
        value=weather["geomagnetic_scale"],
        unit="",
        subtext="NOAA G-Scale",
        col=c4,
    )

    st.markdown("<div style='height: 12px;'></div>", unsafe_allow_html=True)

    # 24h Kp Bar Chart
    col_kp, col_scales = st.columns([1.8, 1.2])

    with col_kp:
        st.markdown("### 📊 Planetary Kp Trend (Recent 24h)")
        kp_history = weather.get("kp_history_24h", [])
        if kp_history:
            df_kp = pd.DataFrame(kp_history)
            fig_kp = px.bar(
                df_kp,
                x="timestamp",
                y="kp",
                labels={"timestamp": "UTC Time", "kp": "Kp Index"},
                color="kp",
                color_continuous_scale=[[0, "#00D2FF"], [0.4, "#38BDF8"], [0.6, "#FFB703"], [1.0, "#EF233C"]],
            )
            fig_kp.update_layout(
                template="plotly_dark",
                paper_bgcolor="#0A0F1D",
                plot_bgcolor="#0F172A",
                yaxis=dict(title="Kp Index (0-9)", range=[0, 9]),
                height=320,
                margin=dict(l=20, r=20, t=20, b=20),
            )
            st.plotly_chart(fig_kp, use_container_width=True)

    with col_scales:
        st.markdown("### 🌐 NOAA Space Weather Scales")
        scales_card_html = f"""
<div class="panel-card">
<div style="font-size: 0.9rem; margin-bottom: 0.6rem;">
<b>Geomagnetic Storms (G-Scale):</b> <span style="color: #00D4FF;">{weather['geomagnetic_scale']}</span>
</div>
<div style="font-size: 0.9rem; margin-bottom: 0.6rem;">
<b>Solar Radiation Storms (S-Scale):</b> <span style="color: #38BDF8;">{weather['solar_radiation_scale']}</span>
</div>
<div style="font-size: 0.9rem; margin-bottom: 0.6rem;">
<b>Radio Blackouts (R-Scale):</b> <span style="color: #818CF8;">{weather['radio_blackout_scale']}</span>
</div>
<div style="font-size: 0.78rem; color: #94A3B8; margin-top: 0.8rem; padding-top: 0.6rem; border-top: 1px solid rgba(255,255,255,0.08);">
Source: <b>{weather['source']}</b><br>
Telemetry Timestamp: <code>{weather['timestamp_utc']}</code>
</div>
</div>
"""
        render_html(scales_card_html)

    # Satellite Operational Impact Matrix
    st.markdown("### 🛰️ Spacecraft Telemetry & Operational Impacts")
    i1, i2, i3 = st.columns(3)

    with i1:
        impact_1 = f"""
<div class="panel-card" style="height: 100%;">
<h4 style="color: #00D4FF; font-size: 0.95rem; margin-bottom: 0.4rem;">
💨 LEO Atmospheric Drag
</h4>
<p style="font-size: 0.82rem; color: #E2E8F0; line-height: 1.4;">
{weather['satellite_drag_impact']}
</p>
<div style="font-size: 0.72rem; color: #94A3B8; margin-top: 0.5rem;">
UV/geomagnetic energy heats thermosphere, increasing neutral gas density up to 800 km altitude.
</div>
</div>
"""
        render_html(impact_1)

    with i2:
        impact_2 = f"""
<div class="panel-card" style="height: 100%;">
<h4 style="color: #38BDF8; font-size: 0.95rem; margin-bottom: 0.4rem;">
📡 GNSS & Ionospheric Delay
</h4>
<p style="font-size: 0.82rem; color: #E2E8F0; line-height: 1.4;">
{weather['gnss_impact']}
</p>
<div style="font-size: 0.72rem; color: #94A3B8; margin-top: 0.5rem;">
Total Electron Content (TEC) gradients cause phase scintillation and group delay on L-band signals.
</div>
</div>
"""
        render_html(impact_2)

    with i3:
        impact_3 = f"""
<div class="panel-card" style="height: 100%;">
<h4 style="color: #F59E0B; font-size: 0.95rem; margin-bottom: 0.4rem;">
⚡ Avionics & Radiation Hazard
</h4>
<p style="font-size: 0.82rem; color: #E2E8F0; line-height: 1.4;">
{weather['radiation_impact']}
</p>
<div style="font-size: 0.72rem; color: #94A3B8; margin-top: 0.5rem;">
Trapped relativistic electrons in Van Allen belts elevate internal dielectric breakdown risks.
</div>
</div>
"""
        render_html(impact_3)
