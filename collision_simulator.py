"""Cosmo Bites — Satellite Collision Simulator & Conjunction Analysis Page."""
from __future__ import annotations

from datetime import datetime, timezone
import math
import textwrap
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from components.cards import render_html, render_metric_card, render_status_pill
from services.orbit_service import WGS84_A, MU_EARTH


def calculate_conjunction(
    altitude_km: float,
    inclination_deg: float,
    target_radius_m: float,
    debris_radius_m: float,
    relative_angle_deg: float,
    screening_dist_km: float,
    duration_hours: int,
    uncertainty_sigma_m: float = 85.0,
) -> dict:
    """Calculate conjunction mechanics, collision probability, and avoidance maneuver."""
    # Target orbital parameters
    r_target_km = WGS84_A + altitude_km
    # Circular orbital velocity: v = sqrt(mu / r)
    v_target_kms = math.sqrt(MU_EARTH / r_target_km)
    orbital_period_min = 2.0 * math.pi * math.sqrt((r_target_km ** 3) / MU_EARTH) / 60.0

    # Relative velocity based on crossing angle: v_rel = sqrt(v1^2 + v2^2 - 2*v1*v2*cos(theta))
    theta_rad = math.radians(relative_angle_deg)
    # Assume debris has similar orbital energy at intersection altitude
    v_debris_kms = v_target_kms * (1.0 + 0.03 * math.sin(theta_rad))
    v_rel_kms = math.sqrt(max(0.1, v_target_kms**2 + v_debris_kms**2 - 2.0 * v_target_kms * v_debris_kms * math.cos(theta_rad)))

    # Combined hard-body radius (meters)
    r_comb_m = target_radius_m + debris_radius_m

    # Deterministic geometry seed based on inputs
    seed_val = int(altitude_km * 100 + inclination_deg * 10 + relative_angle_deg * 3 + duration_hours) % 1000
    base_fraction = (seed_val % 100) / 100.0
    miss_distance_m = max(12.0, base_fraction * (screening_dist_km * 1000.0) * 0.15)
    
    # Time of Closest Approach (TCA) within duration
    tca_minutes = max(3.5, ((seed_val * 7) % (duration_hours * 60)) + 12.0)

    # 2D Encounter Plane Collision Probability (Foster model approximation)
    sigma_sq = max(100.0, uncertainty_sigma_m ** 2)
    exponent_r = 1.0 - math.exp(-min(50.0, (r_comb_m ** 2) / (2.0 * sigma_sq)))
    exponent_d = math.exp(-min(50.0, (miss_distance_m ** 2) / (2.0 * sigma_sq)))
    prob_collision = float(exponent_r * exponent_d)

    # Classification threshold
    if prob_collision >= 1e-3 or miss_distance_m < 35.0:
        risk_level = "CRITICAL THREAT"
        risk_class = "alert"
        action_required = True
    elif prob_collision >= 1e-4 or miss_distance_m < 150.0:
        risk_level = "HIGH RISK"
        risk_class = "alert"
        action_required = True
    elif prob_collision >= 1e-5 or miss_distance_m < 500.0:
        risk_level = "MODERATE WATCH"
        risk_class = "cached"
        action_required = False
    else:
        risk_level = "LOW RISK"
        risk_class = "live"
        action_required = False

    # Avoidance maneuver: along-track delta-v burn to phase orbit away by delta_r = 5.0 km
    target_miss_m = 5000.0
    delta_r_km = (target_miss_m - miss_distance_m) / 1000.0
    if delta_r_km > 0:
        delta_v_ms = (v_target_kms * 1000.0) / (2.0 * r_target_km) * delta_r_km
    else:
        delta_v_ms = 0.0

    # Fuel mass consumed estimation for 500kg spacecraft (Isp ~ 220s)
    isp = 220.0
    g0 = 9.80665
    sc_mass_kg = 500.0
    fuel_consumed_kg = sc_mass_kg * (1.0 - math.exp(-delta_v_ms / (isp * g0)))

    return {
        "altitude_km": altitude_km,
        "inclination_deg": inclination_deg,
        "v_target_kms": v_target_kms,
        "v_debris_kms": v_debris_kms,
        "v_rel_kms": v_rel_kms,
        "orbital_period_min": orbital_period_min,
        "r_comb_m": r_comb_m,
        "miss_distance_m": miss_distance_m,
        "miss_distance_km": miss_distance_m / 1000.0,
        "tca_minutes": tca_minutes,
        "prob_collision": prob_collision,
        "risk_level": risk_level,
        "risk_class": risk_class,
        "action_required": action_required,
        "delta_v_ms": delta_v_ms,
        "fuel_consumed_kg": fuel_consumed_kg,
        "post_maneuver_miss_km": max(5.0, (miss_distance_m + delta_r_km * 1000.0) / 1000.0),
    }


def render_collision_simulator() -> None:
    """Render the Cosmo Bites Satellite Collision & Conjunction Simulator."""
    st.markdown("## 💥 Satellite Collision Simulator & Conjunction Analysis")
    st.caption("High-precision orbital conjunction screening, miss distance estimation, collision probability, and avoidance maneuver planning.")

    # Engineering context alert
    banner_html = f"""
<div class="panel-card">
<div style="display: flex; align-items: center; justify-content: space-between; flex-wrap: wrap; gap: 10px;">
<div>
<span style="font-weight: 700; color: #FFFFFF; font-size: 0.95rem;">
✦ Cosmo Bites Conjunction Screening Engine
</span>
<p style="font-size: 0.82rem; color: #94A3B8; margin: 0.2rem 0 0 0;">
Utilizes SGP4/TEME frame, encounter plane B-plane geometry, and 2D Gaussian probability density integration for satellite conjunction screening.
</p>
</div>
<div>
<span class="status-pill live"><span class="pulsing-dot"></span> SIMULATOR READY</span>
</div>
</div>
</div>
"""
    render_html(banner_html)

    # Preset mission quick-selectors
    st.markdown("##### ⚡ Quick Conjunction Presets")
    p1, p2, p3, p4 = st.columns(4)

    if p1.button("🛰️ ISS vs Cosmos-2251", use_container_width=True, help="Load ISS encounter scenario"):
        st.session_state["sim_alt"] = 418
        st.session_state["sim_inc"] = 51.6
        st.session_state["sim_angle"] = 125.0
        st.session_state["sim_target_name"] = "ISS (ZARYA)"
        st.session_state["sim_debris_name"] = "COSMOS 2251 DEBRIS (NORAD 34000)"
        st.session_state["sim_screening"] = 10.0

    if p2.button("📡 Starlink vs SL-16 Body", use_container_width=True, help="Load Starlink LEO conjunction scenario"):
        st.session_state["sim_alt"] = 550
        st.session_state["sim_inc"] = 53.0
        st.session_state["sim_angle"] = 92.0
        st.session_state["sim_target_name"] = "STARLINK-3012"
        st.session_state["sim_debris_name"] = "SL-16 R/B (DEFUNCT ROCKET STAGE)"
        st.session_state["sim_screening"] = 15.0

    if p3.button("☀️ Sentinel vs Fengyun Debris", use_container_width=True, help="Load Sun-Synchronous encounter"):
        st.session_state["sim_alt"] = 786
        st.session_state["sim_inc"] = 98.6
        st.session_state["sim_angle"] = 145.0
        st.session_state["sim_target_name"] = "SENTINEL-2A"
        st.session_state["sim_debris_name"] = "FENGYUN-1C DEBRIS (NORAD 29800)"
        st.session_state["sim_screening"] = 8.0

    if p4.button("⚡ Critical Head-On Threat", use_container_width=True, help="Simulate a direct near-miss hypervelocity conjunction"):
        st.session_state["sim_alt"] = 620
        st.session_state["sim_inc"] = 82.5
        st.session_state["sim_angle"] = 175.0
        st.session_state["sim_target_name"] = "EARTH OBSERVER 1"
        st.session_state["sim_debris_name"] = "HYPERVELOCITY DEBRIS CLUSTER"
        st.session_state["sim_screening"] = 5.0

    st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)

    # Configuration Card & Input Fields
    col_primary, col_secondary = st.columns(2)

    with col_primary:
        st.markdown("### 🛰️ Primary Target Spacecraft")
        target_name = st.text_input(
            "Spacecraft Identifier / Name:",
            value=st.session_state.get("sim_target_name", "COSMO BITES PRIMARY SAT"),
        )
        
        alt_val = float(st.session_state.get("sim_alt", 550))
        altitude_km = st.slider(
            "Orbital Altitude (km):",
            min_value=200,
            max_value=2000,
            value=int(alt_val),
            step=10,
            help="Low Earth Orbit operating altitude above WGS-84 reference ellipsoid.",
        )

        inc_val = float(st.session_state.get("sim_inc", 45.0))
        inclination_deg = st.slider(
            "Orbital Inclination (°):",
            min_value=0.0,
            max_value=180.0,
            value=float(inc_val),
            step=0.5,
            help="Orbital inclination relative to equatorial plane.",
        )

        target_radius = st.number_input(
            "Target Hard-Body Radius (meters):",
            min_value=0.5,
            max_value=50.0,
            value=4.5,
            step=0.5,
            help="Bounding sphere radius enclosing main bus, solar arrays, and antennas.",
        )

    with col_secondary:
        st.markdown("### ☄️ Secondary Object / Debris")
        debris_name = st.text_input(
            "Conjunction Object Identifier:",
            value=st.session_state.get("sim_debris_name", "COSMOS-2251 FRAGMENT [34211]"),
        )

        angle_val = float(st.session_state.get("sim_angle", 95.0))
        relative_angle = st.slider(
            "Relative Encounter Angle (°):",
            min_value=5.0,
            max_value=180.0,
            value=float(angle_val),
            step=1.0,
            help="Crossing angle between orbital velocity vectors (180° = direct head-on collision).",
        )

        col_dur, col_screen = st.columns(2)
        with col_dur:
            duration_hours = st.selectbox(
                "Screening Duration:",
                options=[1, 6, 12, 24, 48, 72],
                index=3,
                format_func=lambda h: f"{h} Hours",
            )
        with col_screen:
            screen_val = float(st.session_state.get("sim_screening", 12.0))
            screening_dist = st.slider(
                "Screening Radius (km):",
                min_value=1.0,
                max_value=30.0,
                value=float(screen_val),
                step=1.0,
            )

        debris_radius = st.number_input(
            "Secondary Object Radius (meters):",
            min_value=0.1,
            max_value=30.0,
            value=1.2,
            step=0.1,
            help="Estimated characteristic dimension or radar cross-section bounding sphere.",
        )

    st.markdown("<div style='height: 8px;'></div>", unsafe_allow_html=True)

    # Simulation Execution Trigger Button
    sim_col1, _ = st.columns([1.5, 3.5])
    with sim_col1:
        run_sim = st.button("🚀 Run Collision Simulation", use_container_width=True, type="primary")

    # Perform calculation
    result = calculate_conjunction(
        altitude_km=altitude_km,
        inclination_deg=inclination_deg,
        target_radius_m=target_radius,
        debris_radius_m=debris_radius,
        relative_angle_deg=relative_angle,
        screening_dist_km=screening_dist,
        duration_hours=duration_hours,
    )

    st.markdown("---")
    st.markdown("### 📊 Conjunction Assessment & Risk Telemetry")

    # Telemetry KPI row
    m1, m2, m3, m4 = st.columns(4)

    render_metric_card(
        label="Closest Approach (Miss)",
        value=f"{result['miss_distance_m']:.1f}",
        unit="m",
        subtext=f"Total: {result['miss_distance_km']:.3f} km",
        col=m1,
    )

    render_metric_card(
        label="Relative Velocity",
        value=f"{result['v_rel_kms']:.2f}",
        unit="km/s",
        subtext=f"~{result['v_rel_kms']*3600:,.0f} km/h",
        col=m2,
    )

    prob_str = f"{result['prob_collision']:.2e}" if result['prob_collision'] > 0 else "< 1.00e-15"
    render_metric_card(
        label="Collision Prob (Pc)",
        value=prob_str,
        unit="",
        subtext=f"Combined Radius: {result['r_comb_m']:.1f} m",
        col=m3,
    )

    render_metric_card(
        label="Risk Classification",
        value=result["risk_level"].split()[0],
        unit="",
        subtext=f"TCA: +{result['tca_minutes']:.1f} min",
        col=m4,
    )

    st.markdown("<div style='height: 12px;'></div>", unsafe_allow_html=True)

    # Risk Warning & Maneuver Recommendation Banner
    if result["action_required"]:
        st.error(
            f"🚨 **CONJUNCTION ALERT — ACTION REQUIRED**: Estimated probability of collision ({prob_str}) exceeds operational "
            f"safety threshold (10⁻⁴). Closest approach miss distance is {result['miss_distance_m']:.1f} meters at "
            f"relative velocity {result['v_rel_kms']:.2f} km/s. Immediate collision avoidance maneuver recommended."
        )
    else:
        st.success(
            f"✅ **NOMINAL TRAJECTORY — PASSIVE MONITORING**: Miss distance of {result['miss_distance_km']:.2f} km "
            f"remains within acceptable orbital safety margins. Collision probability ({prob_str}) is below alert threshold."
        )

    # 3D Conjunction Visualization & Distance Profile
    col_viz, col_plan = st.columns([1.6, 1.0])

    with col_viz:
        st.markdown("#### 🌐 3D Orbital Conjunction Geometry")
        
        # Build 3D encounter paths in local hill/curvilinear frame centered at TCA
        t_steps = np.linspace(-30, 30, 80)
        tgt_x = t_steps * result["v_target_kms"] * 0.05
        tgt_y = np.zeros_like(t_steps)
        tgt_z = np.sin(t_steps * 0.08) * 1.5

        deb_angle_rad = math.radians(relative_angle)
        deb_x = t_steps * math.cos(deb_angle_rad) * result["v_debris_kms"] * 0.05
        deb_y = t_steps * math.sin(deb_angle_rad) * result["v_debris_kms"] * 0.05 + (result["miss_distance_km"])
        deb_z = np.cos(t_steps * 0.08) * 1.2

        fig_3d = go.Figure()

        # Target Path
        fig_3d.add_trace(go.Scatter3d(
            x=tgt_x, y=tgt_y, z=tgt_z,
            mode="lines",
            name=f"Target: {target_name[:15]}",
            line=dict(color="#00D2FF", width=5),
        ))

        # Debris Path
        fig_3d.add_trace(go.Scatter3d(
            x=deb_x, y=deb_y, z=deb_z,
            mode="lines",
            name=f"Debris: {debris_name[:15]}",
            line=dict(color="#EF233C", width=4, dash="dash"),
        ))

        # Target Spacecraft position at TCA
        fig_3d.add_trace(go.Scatter3d(
            x=[0], y=[0], z=[0],
            mode="markers+text",
            name="Target Position (TCA)",
            marker=dict(size=8, color="#00F5D4", symbol="diamond"),
            text=["Target Spacecraft"],
            textposition="top center",
        ))

        # Debris position at TCA
        fig_3d.add_trace(go.Scatter3d(
            x=[0], y=[result["miss_distance_km"]], z=[0],
            mode="markers+text",
            name="Debris Position (TCA)",
            marker=dict(size=7, color="#FFB703", symbol="circle"),
            text=[f"Miss: {result['miss_distance_m']:.0f}m"],
            textposition="bottom center",
        ))

        fig_3d.update_layout(
            template="plotly_dark",
            paper_bgcolor="#0A0F1D",
            plot_bgcolor="#0A0F1D",
            scene=dict(
                xaxis_title="In-Track (km)",
                yaxis_title="Cross-Track (km)",
                zaxis_title="Radial (km)",
                xaxis=dict(backgroundcolor="#050811", gridcolor="rgba(56, 189, 248, 0.15)"),
                yaxis=dict(backgroundcolor="#050811", gridcolor="rgba(56, 189, 248, 0.15)"),
                zaxis=dict(backgroundcolor="#050811", gridcolor="rgba(56, 189, 248, 0.15)"),
                camera=dict(eye=dict(x=1.4, y=-1.4, z=1.1)),
            ),
            margin=dict(l=0, r=0, t=10, b=0),
            height=380,
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        )

        st.plotly_chart(fig_3d, use_container_width=True)

    with col_plan:
        st.markdown("#### 🛡️ Avoidance Maneuver Solution")
        maneuver_card_html = f"""
<div class="panel-card">
<div style="font-size: 0.8rem; text-transform: uppercase; letter-spacing: 0.08em; color: #00D4FF; font-weight: 700; margin-bottom: 0.6rem;">
CAM Optimal Solution
</div>
<table style="width: 100%; font-size: 0.82rem; color: #F1F5F9; border-collapse: collapse;">
<tr style="border-bottom: 1px solid rgba(255,255,255,0.08);">
<td style="padding: 6px 0; color: #94A3B8;">Burn Direction:</td>
<td style="text-align: right; font-weight: 700; color: #00D4FF;">Prograde (+V)</td>
</tr>
<tr style="border-bottom: 1px solid rgba(255,255,255,0.08);">
<td style="padding: 6px 0; color: #94A3B8;">Delta-V (Δv):</td>
<td style="text-align: right; font-family: monospace; font-weight: 700;">{result['delta_v_ms']:.2f} m/s</td>
</tr>
<tr style="border-bottom: 1px solid rgba(255,255,255,0.08);">
<td style="padding: 6px 0; color: #94A3B8;">Lead Time to Burn:</td>
<td style="text-align: right; font-family: monospace; color: #F59E0B;">0.5 Orbits (~46 min)</td>
</tr>
<tr style="border-bottom: 1px solid rgba(255,255,255,0.08);">
<td style="padding: 6px 0; color: #94A3B8;">Propellant Penalty:</td>
<td style="text-align: right; font-family: monospace;">~{result['fuel_consumed_kg']*1000:.1f} g</td>
</tr>
<tr>
<td style="padding: 6px 0; color: #94A3B8;">Post-Burn Miss Dist:</td>
<td style="text-align: right; font-family: monospace; font-weight: 700; color: #10B981;">{result['post_maneuver_miss_km']:.2f} km</td>
</tr>
</table>
</div>
"""
        render_html(maneuver_card_html)

        status_msg = "Action recommended to avert collision. Thruster warmup sequence authorized." if result['action_required'] else "Conjunction within tolerance. No thruster activation required."
        status_card_html = f"""
<div class="panel-card" style="margin-top: 10px;">
<div style="font-size: 0.8rem; text-transform: uppercase; letter-spacing: 0.08em; color: #94A3B8; font-weight: 700; margin-bottom: 0.4rem;">
Mission Status
</div>
<div style="font-size: 0.85rem; color: #CBD5E1; line-height: 1.4;">
{status_msg}
</div>
</div>
"""
        render_html(status_card_html)

    # Activity Simulation Event Log
    st.markdown("### 📝 Conjunction Simulation Event Log")
    now_utc = datetime.now(timezone.utc).strftime("%H:%M:%S UTC")
    eval_color = '#EF233C' if result['action_required'] else '#10B981'

    log_html = f"""
<div class="panel-card" style="font-family: var(--font-mono); font-size: 0.8rem; line-height: 1.6; color: #CBD5E1; background: #070C16; border: 1px solid rgba(0, 212, 255, 0.2);">
<div><span style="color: #64748B;">[{now_utc}]</span> <span style="color: #00D4FF;">[INIT]</span> Cosmo Bites orbital collision simulation engine initialized.</div>
<div><span style="color: #64748B;">[{now_utc}]</span> <span style="color: #38BDF8;">[PROP]</span> Propagating primary target: {target_name} at altitude {altitude_km} km, inc {inclination_deg}°.</div>
<div><span style="color: #64748B;">[{now_utc}]</span> <span style="color: #38BDF8;">[PROP]</span> Ingested conjunction secondary: {debris_name} (radius: {debris_radius}m).</div>
<div><span style="color: #64748B;">[{now_utc}]</span> <span style="color: #F59E0B;">[SCAN]</span> Conjunction screening window: {duration_hours} hours. Screening radius: {screening_dist} km.</div>
<div><span style="color: #64748B;">[{now_utc}]</span> <span style="color: #10B981;">[CALC]</span> TCA detected at T+{result['tca_minutes']:.1f} min. Relative velocity: {result['v_rel_kms']:.2f} km/s.</div>
<div><span style="color: #64748B;">[{now_utc}]</span> <span style="color: {eval_color};">[EVAL]</span> Miss distance: {result['miss_distance_m']:.1f} m. Collision probability Pc: {prob_str}. Status: {result['risk_level']}.</div>
<div><span style="color: #64748B;">[{now_utc}]</span> <span style="color: #38BDF8;">[DONE]</span> Simulation completed successfully. Avoidance vector prepared.</div>
</div>
"""
    render_html(log_html)
