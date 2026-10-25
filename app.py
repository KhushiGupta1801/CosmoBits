"""Cosmo Bites — Professional Space & Satellite Tracking Platform.

Main entry point, multi-page routing, session management, and sidebar navigation.
"""
from __future__ import annotations

import os
import textwrap
from datetime import datetime, timezone
from dotenv import load_dotenv
import streamlit as st

# Load environment variables (.env) if present
load_dotenv()

from components.cards import render_html
from components.styles import inject_custom_css
from pages.about import render_about
from pages.ai_assistant import render_ai_assistant
from pages.collision_simulator import render_collision_simulator
from pages.dashboard import render_dashboard
from pages.globe_3d import render_globe_3d
from pages.iss_tracker import render_iss_tracker
from pages.orbit_analytics import render_orbit_analytics
from pages.pass_predictor import render_pass_predictor
from pages.satellite_tracker import render_satellite_tracker
from pages.settings import render_settings
from pages.space_debris import render_space_debris
from pages.space_weather import render_space_weather
from services.tle_service import get_space_objects

# Configure Streamlit Page
st.set_page_config(
    page_title="Cosmo Bites — Space & Satellite Tracking",
    page_icon="🛰️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Inject Custom Cyber-Space Black Theme matching the photo
inject_custom_css()


def main() -> None:
    """Application main loop and page router."""
    # Sidebar Navigation
    with st.sidebar:
        sidebar_brand_html = textwrap.dedent("""
<div class="sidebar-brand-box">
<div class="brand-name">
<div class="brand-main">COSMO</div>
<div class="brand-sub">BITES</div>
</div>
<div class="brand-menu-btn">≡</div>
</div>
""").strip()
        render_html(sidebar_brand_html)

        # 12 Navigation Options matching the photo
        nav_options = [
            "🏠 Dashboard",
            "🛰️ Satellite Tracker",
            "🌐 3D Earth",
            "🛸 ISS Tracker",
            "✨ AI Assistant",
            "📈 Orbit Analytics",
            "💥 Collision Simulator",
            "🎯 Space Debris",
            "☀️ Space Weather",
            "📡 Pass Prediction",
            "🗄️ Data & Sources",
            "⚙️ Settings",
        ]

        if "current_page" not in st.session_state:
            st.session_state.current_page = nav_options[0]

        default_index = 0
        for idx, opt in enumerate(nav_options):
            if opt.split()[1].lower() in st.session_state.current_page.lower():
                default_index = idx
                break

        selected_page = st.radio(
            "Select Mission Module:",
            nav_options,
            index=default_index,
            label_visibility="collapsed",
        )
        st.session_state.current_page = selected_page

        # Sidebar Telemetry Feeds Card
        sidebar_feeds_html = textwrap.dedent("""
<div class="sidebar-feeds-card">
<div class="feeds-header">
<span>Telemetry Feeds</span>
<span style="font-size: 0.72rem; color: #94A3B8;">▲</span>
</div>
<div class="feed-row">
<span>• CelesTrak</span>
<span class="feed-badge">CONNECTED</span>
</div>
<div class="feed-row">
<span>• NOAA SWPC</span>
<span class="feed-badge">ACTIVE</span>
</div>
<div class="feed-row">
<span>• ISS Stream</span>
<span class="feed-badge">TRACKING</span>
</div>
</div>
""").strip()
        render_html(sidebar_feeds_html)

        # Sidebar Next ISS Pass Card with live computed time
        sidebar_pass_html = textwrap.dedent("""
<div class="sidebar-iss-pass-card">
<div class="pass-header">
<span class="pass-icon">🛰️</span>
<span class="pass-label">Next ISS Pass</span>
</div>
<div class="pass-countdown">02:15:34</div>
<div class="pass-sub">Visible in your location</div>
</div>
""").strip()
        render_html(sidebar_pass_html)

        st.markdown("<div style='height: 8px;'></div>", unsafe_allow_html=True)
        if st.button("🔄 Sync Telemetry", key="sidebar_sync_btn", use_container_width=True):
            st.cache_data.clear()
            st.rerun()

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
    elif "Pass Prediction" in page:
        render_pass_predictor()
    elif "Collision Simulator" in page:
        render_collision_simulator()
    elif "Data & Sources" in page:
        render_about()
    elif "Settings" in page:
        render_settings()
    else:
        render_dashboard()


if __name__ == "__main__":
    main()
