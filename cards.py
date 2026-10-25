"""CosmoBits — Glassmorphism UI Cards & Visual Badges."""
from __future__ import annotations

import streamlit as st


def render_metric_card(
    label: str,
    value: str | int | float,
    unit: str = "",
    subtext: str = "",
    col=None,
) -> None:
    """Render a sleek, cyber-styled telemetry metric card."""
    html = f"""
    <div class="metric-tile">
        <div class="metric-label">{label}</div>
        <div class="metric-value">
            {value}<span class="metric-unit">{unit}</span>
        </div>
        {f'<div class="metric-sub">{subtext}</div>' if subtext else ''}
    </div>
    """
    if col:
        col.markdown(html, unsafe_allow_html=True)
    else:
        st.markdown(html, unsafe_allow_html=True)


def render_status_pill(status: str, mode: str = "live") -> str:
    """Generate HTML for a glowing status pill."""
    mode_class = mode.lower()
    if "live" in mode_class:
        cls = "live"
    elif "prop" in mode_class:
        cls = "propagated"
    elif "alert" in mode_class or "storm" in mode_class:
        cls = "alert"
    else:
        cls = "cached"

    return f"""
    <span class="status-pill {cls}">
        <span class="pulsing-dot"></span>
        {status}
    </span>
    """


def render_nav_card(
    title: str,
    description: str,
    icon: str,
    col=None,
) -> None:
    """Render a clickable-looking navigation preview card."""
    html = f"""
    <div class="nav-card">
        <div class="nav-card-icon">{icon}</div>
        <div class="nav-card-title">{title}</div>
        <div class="nav-card-desc">{description}</div>
    </div>
    """
    if col:
        col.markdown(html, unsafe_allow_html=True)
    else:
        st.markdown(html, unsafe_allow_html=True)
