"""Cosmo Bites — Space Debris Monitoring & Orbital Sustainability Page."""
from __future__ import annotations

import textwrap
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from components.cards import render_html, render_metric_card
from services.tle_service import get_space_objects


def render_space_debris() -> None:
    """Render space debris analytics, altitude clustering, and collision risk education."""
    st.markdown("## 🗑️ Space Debris Monitoring & Orbital Sustainability")
    st.caption("Tracking fragmentation debris, defunct upper stages, and assessing orbital conjunction risks.")

    # Honest Engineering Disclaimer
    st.warning(
        "⚠️ **Orbital Safety & Conjunction Screening**: "
        "Operational collision avoidance requires high-precision Covariance Matrices and Conjunction Data Messages (CDMs) "
        "issued by the 18th Space Defense Squadron. The spatial distributions below are derived from "
        "unclassified TLE/SGP4 elements for situational awareness and debris population monitoring."
    )

    # Ingest analyst and debris objects
    debris_objs, status = get_space_objects(groups=["analyst", "stations", "last-30-days"], max_objects=300)
    df_debris = pd.DataFrame([o for o in debris_objs if o["catalog"] == "analyst"])

    if len(df_debris) < 3:
        df_debris = pd.DataFrame(debris_objs)

    # Top KPI metrics
    c1, c2, c3, c4 = st.columns(4)
    render_metric_card("Tracked Debris", f"{len(df_debris):,}", "objects", subtext="Analyst Catalog Feed", col=c1)
    render_metric_card("High-Density Band", "750 – 900", "km", subtext="Sun-Synchronous LEO", col=c2)
    render_metric_card("Hypervelocity Speed", "~7.5", "km/s", subtext="~10-14 km/s head-on", col=c3)
    render_metric_card("Collision Warning", "10⁻⁴", "Pc Threshold", subtext="Triggers avoidance burn", col=c4)

    st.markdown("<div style='height: 12px;'></div>", unsafe_allow_html=True)

    # Debris Spatial Distribution Chart
    st.markdown("### 📊 Debris Altitude & Spatial Distribution")
    fig_deb = px.histogram(
        df_debris,
        x="alt_km",
        nbins=25,
        labels={"alt_km": "Altitude (km)", "count": "Debris Count"},
        color_discrete_sequence=["#EF233C"],
        title="Orbital Altitude Density of Tracked Debris & Analyst Objects",
    )
    fig_deb.update_layout(
        template="plotly_dark",
        paper_bgcolor="#0A0F1D",
        plot_bgcolor="#0F172A",
        height=380,
        margin=dict(l=20, r=20, t=40, b=20),
    )
    st.plotly_chart(fig_deb, use_container_width=True)

    # Action Banner: Jump to Collision Simulator
    banner_html = """
<div class="panel-card" style="border-color: #00D4FF; display: flex; align-items: center; justify-content: space-between; flex-wrap: wrap; gap: 12px;">
<div>
<h4 style="color: #00D4FF; margin: 0 0 4px 0;">⚡ Run High-Precision Conjunction Analysis</h4>
<p style="font-size: 0.85rem; color: #CBD5E1; margin: 0;">
Simulate hypervelocity collision scenarios between operational satellites and tracked debris fragments.
</p>
</div>
</div>
"""
    render_html(banner_html)

    if st.button("💥 Launch Collision Simulator Now", key="btn_goto_collision", use_container_width=False):
        st.session_state.current_page = "💥 Collision Simulator"
        st.rerun()

    st.markdown("<div style='height: 8px;'></div>", unsafe_allow_html=True)

    # Educational Sections
    col_kessler, col_remed = st.columns(2)

    with col_kessler:
        kessler_html = """
<div class="panel-card">
<h3 style="color: #00D4FF; font-size: 1.1rem; margin-bottom: 0.5rem;">
⚠️ The Kessler Syndrome Cascade
</h3>
<p style="font-size: 0.85rem; color: #E2E8F0; line-height: 1.5;">
Proposed by NASA scientist Donald J. Kessler in 1978, the <b>Kessler Syndrome</b> describes a threshold where the density of orbital objects in LEO reaches a critical level. 
Beyond this point, collisions between objects create fragments at a rate faster than natural atmospheric drag can clear them, triggering a self-sustaining cascade of catastrophic collisions.
</p>
<div style="font-size: 0.78rem; color: #94A3B8; margin-top: 0.5rem;">
<b>Historical Inflection Points:</b><br>
• <b>2007 Fengyun-1C ASAT:</b> Created over 3,500 trackable fragments, 80% of which remain in orbit.<br>
• <b>2009 Iridium 33 / Cosmos 2251:</b> First unintentional hypervelocity satellite-satellite collision at 789 km altitude.
</div>
</div>
"""
        render_html(kessler_html)

    with col_remed:
        remed_html = """
<div class="panel-card">
<h3 style="color: #00D4FF; font-size: 1.1rem; margin-bottom: 0.5rem;">
🛡️ Mitigation & Active Debris Removal (ADR)
</h3>
<p style="font-size: 0.85rem; color: #E2E8F0; line-height: 1.5;">
Global space agencies and commercial operators are enforcing strict orbital sustainability protocols to preserve low Earth orbit:
</p>
<div style="font-size: 0.78rem; color: #94A3B8; margin-top: 0.5rem;">
• <b>5-Year Deorbit Rule:</b> FCC and international guidelines mandate that satellites deorbit within 5 years after mission termination.<br>
• <b>Passivation:</b> Depleting residual propellants and discharging batteries to prevent explosive breakups.<br>
• <b>Robotic ADR:</b> Active capture missions (e.g. ClearSpace-1, Astroscale ELSA-d) using robotic arms and magnetic capture plates to deorbit dead rocket upper stages.
</div>
</div>
"""
        render_html(remed_html)
