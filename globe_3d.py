"""Cosmo Bites — Interactive 3D Earth & Orbital Constellation Globe."""
from __future__ import annotations

import numpy as np
import plotly.graph_objects as go
import streamlit as st
from sgp4.api import Satrec

from services.orbit_service import WGS84_A, compute_satellite_ground_track
from services.tle_service import CATALOGS, get_space_objects


def render_globe_3d() -> None:
    """Render the full interactive 3D Earth globe with real satellite positions and orbits."""
    st.markdown("## 🌐 3D Earth View & Orbital Globe")
    st.caption("Rotate, zoom, and inspect real-time satellite positions and orbital trajectories in 3D ECEF space.")

    # Controls row
    col_filter, col_select, col_toggle = st.columns([1.5, 2.0, 1.2])

    with col_filter:
        cat_choices = ["all"] + list(CATALOGS.keys())
        selected_cat = st.selectbox(
            "Filter Constellation:",
            cat_choices,
            format_func=lambda x: "All Active Objects" if x == "all" else CATALOGS.get(x, x),
        )

    groups = list(CATALOGS.keys()) if selected_cat == "all" else [selected_cat]
    objects, status = get_space_objects(groups=groups, max_objects=500)

    with col_select:
        sat_names = [o["name"] for o in objects]
        def_idx = 0
        for i, n in enumerate(sat_names):
            if "ISS" in n:
                def_idx = i
                break
        selected_sat_name = st.selectbox("Highlight Orbit Track:", sat_names, index=def_idx if sat_names else 0)

    with col_toggle:
        show_orbit_path = st.checkbox("Show 3D Orbit Path", value=True)
        scale_alt = st.checkbox("Exaggerate Altitude (2x)", value=False)

    if not objects:
        st.warning("No satellite objects available to render.")
        return

    selected_obj = next((o for o in objects if o["name"] == selected_sat_name), objects[0])

    # Build 3D Plotly Figure
    fig = go.Figure()

    # 1. Generate Earth Reference Sphere
    phi = np.linspace(0, 2 * np.pi, 50)
    theta = np.linspace(-np.pi / 2, np.pi / 2, 25)
    phi_grid, theta_grid = np.meshgrid(phi, theta)

    r_earth = WGS84_A
    x_earth = r_earth * np.cos(theta_grid) * np.cos(phi_grid)
    y_earth = r_earth * np.cos(theta_grid) * np.sin(phi_grid)
    z_earth = r_earth * np.sin(theta_grid)

    # Earth Surface (Deep Navy with translucent atmosphere glow)
    fig.add_trace(
        go.Surface(
            x=x_earth,
            y=y_earth,
            z=z_earth,
            colorscale=[[0, "#030611"], [0.5, "#081329"], [1, "#0D2244"]],
            showscale=False,
            opacity=0.92,
            hoverinfo="skip",
            name="Earth (WGS-84)",
        )
    )

    # Equator Wireframe Ring
    eq_phi = np.linspace(0, 2 * np.pi, 100)
    fig.add_trace(
        go.Scatter3d(
            x=(r_earth + 20) * np.cos(eq_phi),
            y=(r_earth + 20) * np.sin(eq_phi),
            z=np.zeros_like(eq_phi),
            mode="lines",
            line=dict(color="rgba(0, 210, 255, 0.4)", width=2),
            name="Equator",
            hoverinfo="skip",
        )
    )

    # 2. Add Satellites grouped by catalog
    catalogs_present = set(o["catalog"] for o in objects)
    color_map = {
        "stations": "#00D2FF",
        "visual": "#38BDF8",
        "weather": "#60A5FA",
        "gps-ops": "#818CF8",
        "science": "#34D399",
        "last-30-days": "#FFB703",
        "analyst": "#EF233C",
        "demo": "#94A3B8",
    }

    alt_mult = 2.0 if scale_alt else 1.0

    for cat in catalogs_present:
        cat_objs = [o for o in objects if o["catalog"] == cat]
        xs, ys, zs, texts, hovers = [], [], [], [], []

        for o in cat_objs:
            if scale_alt and o["alt_km"] > 0:
                scale_factor = (WGS84_A + o["alt_km"] * alt_mult) / (WGS84_A + o["alt_km"])
                xs.append(o["x"] * scale_factor)
                ys.append(o["y"] * scale_factor)
                zs.append(o["z"] * scale_factor)
            else:
                xs.append(o["x"])
                ys.append(o["y"])
                zs.append(o["z"])

            hovers.append(
                f"<b>{o['name']}</b><br>"
                f"Catalog: {o['catalog'].upper()}<br>"
                f"Alt: {o['alt_km']:.1f} km<br>"
                f"Speed: {o['speed_kms']:.2f} km/s<br>"
                f"Pos: {o['lat']:.2f}°, {o['lon']:.2f}°"
            )

        fig.add_trace(
            go.Scatter3d(
                x=xs,
                y=ys,
                z=zs,
                mode="markers",
                marker=dict(
                    size=4 if cat != "stations" else 7,
                    color=color_map.get(cat, "#00D2FF"),
                    opacity=0.9,
                ),
                name=cat.upper(),
                text=hovers,
                hoverinfo="text",
            )
        )

    # 3. Add Selected Satellite 3D Orbit Trajectory
    if show_orbit_path and selected_obj and "l1" in selected_obj and "l2" in selected_obj:
        try:
            satrec = Satrec.twoline2rv(selected_obj["l1"], selected_obj["l2"])
            track = compute_satellite_ground_track(satrec, duration_minutes=105, step_sec=60)
            if track:
                orb_x = [pt["x"] for pt in track]
                orb_y = [pt["y"] for pt in track]
                orb_z = [pt["z"] for pt in track]

                if scale_alt:
                    for i, pt in enumerate(track):
                        if pt["alt_km"] > 0:
                            sf = (WGS84_A + pt["alt_km"] * alt_mult) / (WGS84_A + pt["alt_km"])
                            orb_x[i] *= sf
                            orb_y[i] *= sf
                            orb_z[i] *= sf

                fig.add_trace(
                    go.Scatter3d(
                        x=orb_x,
                        y=orb_y,
                        z=orb_z,
                        mode="lines",
                        line=dict(color="#00D2FF", width=4),
                        name=f"Orbit: {selected_obj['name']}",
                        hoverinfo="skip",
                    )
                )
        except Exception:
            pass

    # Highlight Selected Satellite Marker
    sel_x = selected_obj["x"]
    sel_y = selected_obj["y"]
    sel_z = selected_obj["z"]
    if scale_alt and selected_obj["alt_km"] > 0:
        sf = (WGS84_A + selected_obj["alt_km"] * alt_mult) / (WGS84_A + selected_obj["alt_km"])
        sel_x *= sf
        sel_y *= sf
        sel_z *= sf

    fig.add_trace(
        go.Scatter3d(
            x=[sel_x],
            y=[sel_y],
            z=[sel_z],
            mode="markers+text",
            marker=dict(size=10, color="#38BDF8", symbol="diamond", line=dict(color="#FFFFFF", width=2)),
            text=[f"  ★ {selected_obj['name']}"],
            textposition="top center",
            name="Selected Target",
            hoverinfo="text",
            hovertext=f"<b>{selected_obj['name']}</b><br>Alt: {selected_obj['alt_km']:.1f} km<br>Speed: {selected_obj['speed_kms']:.2f} km/s",
        )
    )

    # Layout Configuration
    fig.update_layout(
        template="plotly_dark",
        paper_bgcolor="#050811",
        scene=dict(
            xaxis=dict(showgrid=False, showticklabels=False, title="", visible=False),
            yaxis=dict(showgrid=False, showticklabels=False, title="", visible=False),
            zaxis=dict(showgrid=False, showticklabels=False, title="", visible=False),
            aspectmode="data",
            bgcolor="#050811",
        ),
        margin=dict(l=0, r=0, t=10, b=10),
        height=680,
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=0.02,
            xanchor="center",
            x=0.5,
            font=dict(size=10, color="#94A3B8"),
        ),
    )

    st.plotly_chart(fig, use_container_width=True)

    # Technical note on propagation
    st.info(
        f"**SGP4 Ephemeris Propagation**: Satellite vectors are computed in TEME coordinates "
        f"and converted to ECEF (Earth-Centered Earth-Fixed) using Greenwich Mean Sidereal Time (GMST). "
        f"Data epoch: `{status.get('epoch_utc')}`. "
        f"Source: `{status.get('source')}`."
    )
