"""Cosmo Bites — Architecture, Mathematical Foundations & Data Attribution Page."""
from __future__ import annotations

import streamlit as st
from components.cards import render_html


def render_about() -> None:
    """Render technical documentation, mathematical models, and data source citations."""
    st.markdown("## 📖 About Cosmo Bites & Data Sources")
    st.caption("Platform architecture, mathematical formulations, geodetic reference systems, and live API attributions.")

    st.markdown(
        """### 🛰️ Platform Overview
**Cosmo Bites** is an aerospace-grade space situational awareness (SSA) and 
satellite tracking platform designed for engineers, researchers, and satellite enthusiasts. 
It integrates analytical orbital mechanics with live telemetry from public space data sources, 
rendering 3D Cartesian coordinates, topocentric horizon passes, and collision avoidance screening."""
    )

    c1, c2 = st.columns(2)

    with c1:
        feeds_html = """
<div class="panel-card">
<h4 style="color: #00D4FF; font-size: 1.05rem; margin-bottom: 0.5rem;">
📡 Live Data Feeds & Attribution
</h4>
<ul style="font-size: 0.82rem; color: #E2E8F0; line-height: 1.6; padding-left: 1.2rem;">
<li><b>CelesTrak (NORAD GP API):</b> Curated by Dr. T.S. Kelso. Source for general perturbations Two-Line Element (TLE) sets spanning active stations, weather, GPS, science, and analyst debris objects.</li>
<li><b>NOAA Space Weather Prediction Center (SWPC):</b> Real-time Planetary K-index, 10.7 cm Solar Radio Flux (F10.7), solar wind speed, and geomagnetic storm scales (G/S/R).</li>
<li><b>Where The ISS At (WTIA) & Open-Notify:</b> High-frequency REST telemetry endpoints providing calibrated ISS geodetic coordinates, speed, and astronaut manifests.</li>
<li><b>Space-Track.org / 18th SDS:</b> Reference baseline for unclassified space object catalog numbering and decay predictions.</li>
</ul>
</div>
"""
        render_html(feeds_html)

    with c2:
        math_html = """
<div class="panel-card">
<h4 style="color: #00D4FF; font-size: 1.05rem; margin-bottom: 0.5rem;">
📐 Mathematical Models & Frames
</h4>
<ul style="font-size: 0.82rem; color: #E2E8F0; line-height: 1.6; padding-left: 1.2rem;">
<li><b>SGP4 (Simplified General Perturbations 4):</b> Standard analytical propagator accounting for Earth oblateness ($J_2, J_3, J_4$), atmospheric drag (BSTAR), and gravitational luni-solar perturbations.</li>
<li><b>TEME to ECEF:</b> Rotates True Equator, Mean Equinox vectors to Earth-Centered, Earth-Fixed (ECEF) coordinates via Greenwich Mean Sidereal Time (GMST).</li>
<li><b>WGS-84 Ellipsoid:</b> Converts ECEF Cartesian vectors into Geodetic Latitude, Longitude, and Height using Bowring's high-precision closed-form iteration.</li>
<li><b>Topocentric Horizon (AER):</b> Transforms satellite ECEF position to local East-North-Up (ENU) frame to compute Azimuth, Elevation, and Slant Range over ground observers.</li>
</ul>
</div>
"""
        render_html(math_html)

    st.markdown("### 📜 System Architecture")
    st.code(
        """
        [CelesTrak TLEs]  ──>  [SGP4 Propagator]  ──>  [TEME / ECEF Math]  ──>  [WGS-84 Geodetic Engine]
                                                                                        │
        [NOAA SWPC API]   ──>  [Space Weather Service] ────────────────────────────────┤
                                                                                        ├──> [Plotly 2D/3D & Streamlit UI]
        [WTIA / Open-Notify] ─> [Live ISS Telemetry]  ─────────────────────────────────┤
                                                                                        │
        [Gemini / Offline KB] -> [AI Aerospace Assistant] ─────────────────────────────┘
        """,
        language="text",
    )

    st.markdown(
        """---
#### ⚖️ Educational & Research Disclaimer
Cosmo Bites is developed for educational, visualization, and civilian situational awareness purposes. 
It does not replace certified mission operations flight dynamics software, Department of Defense Conjunction Assessment systems, 
or safety-critical flight path planning tools."""
    )
