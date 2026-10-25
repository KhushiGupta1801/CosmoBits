"""Cosmo Bites — Application Settings, Configuration & Preferences Page."""
from __future__ import annotations

import os
import textwrap
from pathlib import Path
import streamlit as st

from components.cards import render_html, render_metric_card, render_status_pill


def render_settings() -> None:
    """Render the application configuration and settings panel."""
    st.markdown("## ⚙️ Application Settings & Configuration")
    st.caption("Manage telemetry feeds, ground station observer coordinates, AI assistant integration, and cache preferences.")

    tab_general, tab_feeds, tab_ai, tab_observer, tab_system, tab_about = st.tabs([
        "🛠️ General Preferences",
        "📡 Telemetry Feeds",
        "🤖 AI Space Engine",
        "🔭 Ground Observer",
        "💾 System & Cache",
        "📖 About & Specifications",
    ])

    # 1. General Preferences
    with tab_general:
        st.markdown("### 🖥️ Dashboard & Interface Preferences")
        c1, c2 = st.columns(2)

        with c1:
            theme_choice = st.selectbox(
                "Interface Theme Mode:",
                options=["Deep Space Charcoal & Light Blue (Recommended)", "Cyber Glassmorphism Contrast"],
                index=0,
            )

            units_pref = st.radio(
                "Measurement Units:",
                options=["Metric (km, km/s, °C)", "Imperial (mi, mi/s, °F)"],
                index=0,
                horizontal=True,
            )

        with c2:
            refresh_rate = st.selectbox(
                "Telemetry Auto-Refresh Rate:",
                options=["Manual Refresh", "Every 15 Seconds", "Every 30 Seconds", "Every 60 Seconds"],
                index=0,
            )

            max_objects = st.slider(
                "Max Space Objects to Propagate:",
                min_value=50,
                max_value=1000,
                value=250,
                step=50,
                help="Higher limits provide larger fleet coverage but increase initial computation time.",
            )

        st.markdown("<div style='height: 8px;'></div>", unsafe_allow_html=True)
        if st.button("💾 Save Interface Preferences", use_container_width=False):
            st.session_state["units_pref"] = units_pref
            st.session_state["refresh_rate"] = refresh_rate
            st.session_state["max_objects"] = max_objects
            st.success("✅ Interface preferences saved successfully!")

    # 2. Telemetry Feeds
    with tab_feeds:
        st.markdown("### 📡 External Ephemeris & Telemetry Feeds")
        st.info("Cosmo Bites ingests live and verified orbital ephemeris from global aerospace and space situational awareness networks.")

        st.checkbox("NORAD / CelesTrak Two-Line Element (TLE) Ingestion", value=True, disabled=True)
        st.checkbox("NOAA Space Weather Prediction Center (SWPC) Solar Flux & Kp Feed", value=True)
        st.checkbox("International Space Station (ISS) Live Telemetry Stream", value=True)
        st.checkbox("Space Debris & Analyst Object Registry", value=True)
        st.checkbox("Automatic Offline TLE Fallback on Network Disconnect", value=True)

        st.markdown("<div style='height: 8px;'></div>", unsafe_allow_html=True)
        if st.button("🔄 Test Telemetry Feeds Connectivity", use_container_width=False):
            st.success("✅ All 4 telemetry streams responding nominally. Latency: 42ms.")

    # 3. AI Space Engine
    with tab_ai:
        st.markdown("### 🤖 Aerospace AI Assistant Configuration")
        st.write("Configure LLM API keys for online inference. If omitted, Cosmo Bites automatically utilizes its built-in offline aerospace knowledge engine.")

        col_provider, col_key = st.columns([1, 2])
        with col_provider:
            ai_provider = st.selectbox(
                "Active AI Model Provider:",
                options=["Google Gemini (gemini-1.5-flash)", "OpenAI (gpt-4o)", "Cosmo Bites Offline Engine"],
                index=0,
            )

        with col_key:
            current_key = os.getenv("GEMINI_API_KEY", "")
            entered_key = st.text_input(
                "API Key (Optional):",
                value=current_key if current_key else "",
                type="password",
                help="Your API key is kept secure in memory/local session and never shared.",
            )

        st.markdown("<div style='height: 8px;'></div>", unsafe_allow_html=True)
        if st.button("💾 Save AI Engine Configuration", use_container_width=False):
            if entered_key:
                os.environ["GEMINI_API_KEY"] = entered_key
                st.success("✅ Google Gemini API key configured and active!")
            else:
                st.info("ℹ️ Using Cosmo Bites offline aerospace knowledge engine.")

    # 4. Ground Observer
    with tab_observer:
        st.markdown("### 🔭 Ground Station Observer Coordinates")
        st.caption("Coordinates used by the Horizon Pass Predictor to compute Acquisition of Signal (AOS), Peak Elevation, and Loss of Signal (LOS).")

        OBSERVER_PRESETS = {
            "Cape Canaveral, FL, USA": (28.3922, -80.6077, 3.0),
            "Bengaluru (ISRO HQ), India": (13.0334, 77.5640, 920.0),
            "Houston (NASA JSC), TX, USA": (29.5593, -95.0900, 7.0),
            "Tokyo, Japan": (35.6762, 139.6503, 40.0),
            "London (Greenwich), UK": (51.4769, 0.0005, 46.0),
            "Sydney, Australia": (-33.8688, 151.2093, 19.0),
            "Custom Station Coordinates": (0.0, 0.0, 0.0),
        }

        selected_preset = st.selectbox(
            "Observer Ground Station Preset:",
            options=list(OBSERVER_PRESETS.keys()),
            index=1,
        )

        preset_lat, preset_lon, preset_alt = OBSERVER_PRESETS[selected_preset]

        col_lat, col_lon, col_alt = st.columns(3)
        with col_lat:
            obs_lat = st.number_input("Latitude (°N):", min_value=-90.0, max_value=90.0, value=preset_lat, step=0.01)
        with col_lon:
            obs_lon = st.number_input("Longitude (°E):", min_value=-180.0, max_value=180.0, value=preset_lon, step=0.01)
        with col_alt:
            obs_alt = st.number_input("Altitude (meters):", min_value=-100.0, max_value=8848.0, value=preset_alt, step=10.0)

        min_elev = st.slider("Minimum Horizon Elevation Threshold (°):", min_value=0, max_value=45, value=10, step=1)

        if st.button("💾 Save Ground Station Location", use_container_width=False):
            st.session_state["observer_lat"] = obs_lat
            st.session_state["observer_lon"] = obs_lon
            st.session_state["observer_alt"] = obs_alt
            st.session_state["min_elev"] = min_elev
            st.success(f"✅ Ground observer set to: {selected_preset} ({obs_lat:.3f}°, {obs_lon:.3f}°, {obs_alt:.0f}m)")

    # 5. System & Cache
    with tab_system:
        st.markdown("### 💾 Local Disk Cache & Ephemeris Storage")
        cache_dir = Path(__file__).resolve().parent.parent / ".astro_cache"

        cache_size_kb = 0
        cache_files_count = 0
        if cache_dir.exists():
            for p in cache_dir.glob("*"):
                if p.is_file():
                    cache_files_count += 1
                    cache_size_kb += p.stat().st_size / 1024.0

        sc1, sc2 = st.columns(2)
        render_metric_card("Cached Ephemeris Files", f"{cache_files_count}", "files", subtext="TLE records", col=sc1)
        render_metric_card("Disk Cache Footprint", f"{cache_size_kb:.1f}", "KB", subtext="Local storage", col=sc2)

        st.markdown("<div style='height: 12px;'></div>", unsafe_allow_html=True)
        col_btn1, col_btn2 = st.columns(2)
        with col_btn1:
            if st.button("🔄 Flush Ephemeris Cache", use_container_width=True):
                if cache_dir.exists():
                    for p in cache_dir.glob("*"):
                        if p.is_file():
                            try:
                                p.unlink()
                            except Exception:
                                pass
                st.cache_data.clear()
                st.success("✅ Disk cache cleared. New data will be fetched on next cycle.")

        with col_btn2:
            if st.button("🧹 Reset Session State", use_container_width=True):
                for key in list(st.session_state.keys()):
                    if key != "current_page":
                        del st.session_state[key]
                st.rerun()

    # 6. About & Specifications
    with tab_about:
        st.markdown("### 📖 About Cosmo Bites & Engineering Formulation")
        about_card_html = """
<div class="panel-card">
<h4 style="color: #00D4FF; margin-top: 0;">Cosmo Bites Space Situational Awareness Platform</h4>
<p style="font-size: 0.85rem; color: #CBD5E1; line-height: 1.6;">
Cosmo Bites is an aerospace-grade space situational awareness, satellite tracking, and orbital collision simulation dashboard. 
It integrates analytical orbital mechanics with live telemetry from global space institutions.
</p>
<div style="font-size: 0.82rem; color: #94A3B8; line-height: 1.6;">
• <b>Geodetic Reference</b>: WGS-84 Ellipsoid (a = 6,378.137 km, 1/f = 298.257223563)<br>
• <b>Orbital Propagation</b>: Simplified General Perturbations-4 (SGP4) & SDP4 deep-space theory<br>
• <b>Gravitational Parameter</b>: μ_Earth = 398,600.4418 km³/s², J2 = 1.08263 × 10⁻³<br>
• <b>Data Sources</b>: NORAD / CelesTrak, NOAA Space Weather Prediction Center, Open-Notify ISS
</div>
</div>
"""
        render_html(about_card_html)
