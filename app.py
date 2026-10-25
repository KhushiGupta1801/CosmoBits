"""CosmoBits — Professional Space & Satellite Tracking Platform.

Main entry point, multi-page routing, session management, and sidebar navigation.
"""
from __future__ import annotations

import os
from datetime import datetime, timezone
from dotenv import load_dotenv
import streamlit as st

# Load environment variables (.env) if present
load_dotenv()

from components.cards import render_status_pill
from components.header import get_cosmobits_icon_svg, render_mission_header
from components.styles import inject_custom_css
from pages.about import render_about
from pages.ai_assistant import render_ai_assistant
from pages.dashboard import render_dashboard
from pages.globe_3d import render_globe_3d
from pages.iss_tracker import render_iss_tracker
from pages.orbit_analytics import render_orbit_analytics
from pages.pass_predictor import render_pass_predictor
from pages.satellite_tracker import render_satellite_tracker
from pages.space_debris import render_space_debris
from pages.space_weather import render_space_weather
from services.tle_service import get_space_objects

# Configure Streamlit Page
st.set_page_config(
    page_title="CosmoBits — Space & Satellite Tracking",
    page_icon="🛰️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Inject Custom Cyber-Space Theme
inject_custom_css()


def main() -> None:
    """Application main loop and page router."""
    # Pre-fetch or inspect cached telemetry status
    try:
        _, status = get_space_objects(max_objects=10)
        feed_source = status.get("source", "SGP4 LIVE")
    except Exception:
        feed_source = "OFFLINE TLE"

    # Top Mission Control Header
    render_mission_header(feed_source=feed_source)

    # Sidebar Navigation
    sidebar_icon = get_cosmobits_icon_svg(36)
    with st.sidebar:
        st.markdown(
            f"""
            <div style="padding: 0.5rem 0 1rem 0; display: flex; align-items: center; gap: 0.75rem;">
                <div style="width: 36px; height: 36px; flex-shrink: 0; filter: drop-shadow(0 0 8px rgba(0, 245, 212, 0.45));">
                    {sidebar_icon}
                </div>
                <div>
                    <div style="font-family: 'Orbitron', sans-serif; font-size: 1.35rem; font-weight: 900; letter-spacing: 0.08em; color: #FFFFFF; line-height: 1.1;">
                        COSMO<span style="color: #00F5D4;">BITS</span>
                    </div>
                    <div style="font-size: 0.68rem; color: #94A3B8; text-transform: uppercase; letter-spacing: 0.1em; margin-top: 0.2rem;">
                        Mission Control System v2.0
                    </div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        st.markdown("---")

        nav_options = [
            "🛰️ Dashboard",
            "🔍 Satellite Tracker",
            "🌐 3D Earth",
            "🛸 ISS Tracker",
            "🤖 AI Assistant",
            "📊 Orbit Analytics",
            "💥 Space Debris",
            "☀️ Space Weather",
            "🔭 Pass Predictor",
            "📖 About & Data Sources",
        ]

        # Read or initialize active navigation page
        if "current_page" not in st.session_state:
            st.session_state.current_page = nav_options[0]

        selected_page = st.radio(
            "Select Mission Module:",
            nav_options,
            index=nav_options.index(st.session_state.current_page) if st.session_state.current_page in nav_options else 0,
            label_visibility="collapsed",
        )
        st.session_state.current_page = selected_page

        st.markdown("---")

        # Telemetry & System Diagnostics in Sidebar
        st.markdown("##### 📡 Telemetry Feeds")
        st.markdown(f"• **CelesTrak**: {render_status_pill('Connected', 'live')}", unsafe_allow_html=True)
        st.markdown(f"• **NOAA SWPC**: {render_status_pill('Active', 'live')}", unsafe_allow_html=True)
        st.markdown(f"• **ISS Stream**: {render_status_pill('Tracking', 'live')}", unsafe_allow_html=True)

        st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)

        if st.button("🔄 Refresh Orbital Ephemeris", use_container_width=True):
            st.cache_data.clear()
            st.rerun()

        st.markdown(
            """
            <div style="font-size: 0.7rem; color: #64748B; margin-top: 1.5rem; text-align: center;">
                CosmoBits Platform<br>
                WGS-84 & SGP4 Orbital Framework
            </div>
            """,
            unsafe_allow_html=True,
        )

    # Route Page Execution
    page = st.session_state.current_page

    if "Dashboard" in page:
        render_dashboard()
    elif "Satellite Tracker" in page:
        render_satellite_tracker()
    elif "3D Earth" in page:
        render_globe_3d()
    elif "ISS Tracker" in page:
        render_iss_tracker()
    elif "AI Assistant" in page:
        render_ai_assistant()
    elif "Orbit Analytics" in page:
        render_orbit_analytics()
    elif "Space Debris" in page:
        render_space_debris()
    elif "Space Weather" in page:
        render_space_weather()
    elif "Pass Predictor" in page:
        render_pass_predictor()
    elif "About" in page:
        render_about()


if __name__ == "__main__":
    main()
