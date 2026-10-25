"""Cosmo Bites — UI Cards, Metrics & Visual Badges."""
from __future__ import annotations

import streamlit as st


def sanitize_html(html_str: str) -> str:
    """Neutralize all leading whitespace line-by-line to guarantee CommonMark never emits <pre><code> blocks."""
    lines = [line.strip() for line in html_str.strip().splitlines() if line.strip()]
    return "\n".join(lines)


def render_html(html_str: str, col=None) -> None:
    """Render raw HTML safely into Streamlit with complete indentation neutralization."""
    clean_html = sanitize_html(html_str)
    if col:
        col.markdown(clean_html, unsafe_allow_html=True)
    else:
        st.markdown(clean_html, unsafe_allow_html=True)


def render_metric_card(
    label: str,
    value: str | int | float,
    unit: str = "",
    subtext: str = "",
    col=None,
) -> None:
    """Render a sleek, aerospace telemetry metric card."""
    sub_html = f'<div class="metric-sub">{subtext}</div>' if subtext else ""
    html = f"""<div class="metric-tile">
<div class="metric-label">{label}</div>
<div class="metric-value">{value}<span class="metric-unit">{unit}</span></div>
{sub_html}
</div>"""
    render_html(html, col=col)


def render_status_pill(status: str, mode: str = "live") -> str:
    """Generate HTML for a status badge without indentation."""
    mode_class = mode.lower()
    if "live" in mode_class:
        cls = "live"
    elif "prop" in mode_class:
        cls = "propagated"
    elif "alert" in mode_class or "storm" in mode_class:
        cls = "alert"
    else:
        cls = "cached"

    return f'<span class="status-pill {cls}"><span class="pulsing-dot"></span>{status}</span>'


def render_nav_card(
    title: str,
    description: str,
    icon: str,
    col=None,
) -> None:
    """Render a navigation preview card with zero indentation."""
    html = f"""<div class="nav-card">
<div class="nav-card-icon">{icon}</div>
<div class="nav-card-title">{title}</div>
<div class="nav-card-desc">{description}</div>
</div>"""
    render_html(html, col=col)

