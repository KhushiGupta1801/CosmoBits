"""Cosmo Bites — Mission Control Header Component."""
from __future__ import annotations

from datetime import datetime, timezone
import streamlit as st
from components.cards import render_html, render_status_pill


def get_cosmobites_icon_svg(size: int = 28) -> str:
    """Return inline scalable SVG markup for the official Cosmo Bites logo icon."""
    return f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 120 120" width="{size}" height="{size}" fill="none">
  <defs>
    <linearGradient id="cbGrad_{size}" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#00D4FF" />
      <stop offset="50%" stop-color="#38BDF8" />
      <stop offset="100%" stop-color="#1D4ED8" />
    </linearGradient>
    <linearGradient id="cbOrbit_{size}" x1="0%" y1="100%" x2="100%" y2="0%">
      <stop offset="0%" stop-color="#1D4ED8" />
      <stop offset="70%" stop-color="#00D4FF" />
      <stop offset="100%" stop-color="#38BDF8" />
    </linearGradient>
    <linearGradient id="cbTop_{size}" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#1E293B" />
      <stop offset="100%" stop-color="#0F172A" />
    </linearGradient>
    <linearGradient id="cbLeft_{size}" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#0A101D" />
      <stop offset="100%" stop-color="#030712" />
    </linearGradient>
    <linearGradient id="cbRight_{size}" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#141E33" />
      <stop offset="100%" stop-color="#0B132B" />
    </linearGradient>
    <filter id="cbGlow_{size}" x="-20%" y="-20%" width="140%" height="140%">
      <feGaussianBlur stdDeviation="2.5" result="blur" />
      <feMerge>
        <feMergeNode in="blur" />
        <feMergeNode in="SourceGraphic" />
      </feMerge>
    </filter>
  </defs>

  <circle cx="60" cy="60" r="54" fill="rgba(11, 19, 43, 0.75)" stroke="rgba(0, 212, 255, 0.35)" stroke-width="1.5" />
  <line x1="32" y1="32" x2="44" y2="44" stroke="#00D4FF" stroke-width="0.75" stroke-dasharray="2 3" opacity="0.4" />
  <line x1="88" y1="30" x2="76" y2="44" stroke="#38BDF8" stroke-width="0.75" stroke-dasharray="2 3" opacity="0.4" />
  <circle cx="32" cy="32" r="1.5" fill="#00D4FF" opacity="0.9" />
  <circle cx="88" cy="30" r="1.5" fill="#38BDF8" opacity="0.9" />
  <circle cx="30" cy="88" r="1.5" fill="#1D4ED8" opacity="0.9" />
  <circle cx="92" cy="85" r="1.5" fill="#00D4FF" opacity="0.9" />

  <ellipse cx="60" cy="60" rx="46" ry="18" fill="none" stroke="url(#cbGrad_{size})" stroke-width="2.2" transform="rotate(-28 60 60)" stroke-dasharray="140 18" stroke-linecap="round" filter="url(#cbGlow_{size})" />
  <ellipse cx="60" cy="60" rx="44" ry="16" fill="none" stroke="url(#cbOrbit_{size})" stroke-width="1.6" transform="rotate(40 60 60)" stroke-dasharray="130 16" stroke-linecap="round" opacity="0.8" />

  <polygon points="60,34 78,44 60,54 42,44" fill="url(#cbTop_{size})" stroke="#00D4FF" stroke-width="1.5" stroke-linejoin="round" />
  <polygon points="42,44 60,54 60,76 42,66" fill="url(#cbLeft_{size})" stroke="#38BDF8" stroke-width="1.5" stroke-linejoin="round" />
  <polygon points="60,54 78,44 78,66 60,76" fill="url(#cbRight_{size})" stroke="#1D4ED8" stroke-width="1.5" stroke-linejoin="round" />

  <line x1="60" y1="36" x2="60" y2="52" stroke="#00D4FF" stroke-width="1" opacity="0.6" />
  <line x1="45" y1="46" x2="58" y2="53" stroke="#38BDF8" stroke-width="1" opacity="0.6" />
  <line x1="75" y1="46" x2="62" y2="53" stroke="#1D4ED8" stroke-width="1" opacity="0.6" />

  <line x1="60" y1="47" x2="60" y2="63" stroke="#FFFFFF" stroke-width="1.8" stroke-linecap="round" filter="url(#cbGlow_{size})" />
  <line x1="52" y1="55" x2="68" y2="55" stroke="#FFFFFF" stroke-width="1.8" stroke-linecap="round" filter="url(#cbGlow_{size})" />
  <circle cx="60" cy="55" r="3.5" fill="#FFFFFF" filter="url(#cbGlow_{size})" />
  <circle cx="60" cy="55" r="1.8" fill="#00D4FF" />

  <g transform="translate(94, 42)">
    <rect x="-4" y="-4" width="8" height="8" rx="2" fill="#00D4FF" stroke="#FFFFFF" stroke-width="1" filter="url(#cbGlow_{size})" />
    <line x1="-7" y1="0" x2="-4" y2="0" stroke="#00D4FF" stroke-width="1.5" />
    <line x1="4" y1="0" x2="7" y2="0" stroke="#00D4FF" stroke-width="1.5" />
  </g>
  <circle cx="26" cy="74" r="3.5" fill="#38BDF8" stroke="#FFFFFF" stroke-width="0.8" filter="url(#cbGlow_{size})" />
  <circle cx="78" cy="88" r="2.8" fill="#1D4ED8" stroke="#FFFFFF" stroke-width="0.6" filter="url(#cbGlow_{size})" />
</svg>"""


# Alias for backward compatibility
get_cosmobits_icon_svg = get_cosmobites_icon_svg


def render_mission_header(active_objects_count: int = 0, feed_source: str = "LIVE") -> None:
    """Render the top mission-control banner with Cosmo Bites brand logo and status indicators."""
    now_utc = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")

    pill_mode = "live" if "live" in feed_source.lower() else "propagated"
    status_html = render_status_pill(f"{feed_source}", pill_mode)

    icon_28 = get_cosmobites_icon_svg(28)
    icon_34 = get_cosmobites_icon_svg(34)
    icon_24 = get_cosmobites_icon_svg(24)

    badge_html = f"""
<div class="cosmobits-top-right-badge" title="Cosmo Bites — Space Situational Awareness Platform">
<div class="badge-icon">{icon_24}</div>
<span style="font-family: var(--font-main); font-size: 0.82rem; font-weight: 800; color: #FFFFFF; letter-spacing: 0.06em;">
COSMO<span style="color: #00D4FF;"> BITES</span>
</span>
</div>
"""

    header_bar_html = f"""
<div class="mission-header">
<div style="display: flex; align-items: center; gap: 0.85rem;">
<div style="width: 34px; height: 34px; display: flex; align-items: center; justify-content: center; filter: drop-shadow(0 0 8px rgba(0, 212, 255, 0.45));">
{icon_34}
</div>
<div>
<span style="font-family: var(--font-main); font-size: 1.35rem; font-weight: 800; color: #FFFFFF; letter-spacing: 0.08em;">
✦ COSMO<span style="color: #00D4FF;"> BITES</span>
</span>
<span style="font-size: 0.8rem; color: #94A3B8; margin-left: 0.75rem;">
SPACE SITUATIONAL AWARENESS & TELEMETRY
</span>
</div>
</div>
<div style="display: flex; align-items: center; gap: 1rem;">
<div style="font-family: var(--font-mono); font-size: 0.85rem; color: #00D4FF; background: rgba(0, 212, 255, 0.08); padding: 0.3rem 0.7rem; border-radius: 6px; border: 1px solid rgba(0, 212, 255, 0.25);">
⏱ {now_utc}
</div>
<div>
{status_html}
</div>
<div class="cosmobits-header-logo" title="Cosmo Bites Mission Control v2.0">
<div style="width: 28px; height: 28px; display: flex; align-items: center; justify-content: center; filter: drop-shadow(0 0 6px rgba(0, 212, 255, 0.5));">
{icon_28}
</div>
<div style="display: flex; flex-direction: column; line-height: 1;">
<span style="font-family: var(--font-main); font-size: 0.88rem; font-weight: 800; letter-spacing: 0.06em; color: #FFFFFF;">
COSMO<span style="color: #00D4FF;"> BITES</span>
</span>
<span style="font-family: var(--font-main); font-size: 0.55rem; color: #94A3B8; letter-spacing: 0.12em; text-transform: uppercase;">
ORBITAL SSA
</span>
</div>
</div>
</div>
</div>
"""

    render_html(badge_html)
    render_html(header_bar_html)

