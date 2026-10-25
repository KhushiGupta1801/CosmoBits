"""Cosmo Bites — Core Orbital Mechanics & Geodetic Services.

Orbital conversions, circular-orbit generation, topocentric horizon passes,
and trajectory geometry. Implements WGS-84 ellipsoid and TEME/ECEF transformations.
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from math import acos, asin, atan2, cos, degrees, hypot, radians, sin, sqrt
from typing import Any

import numpy as np

# Physical and geodetic constants (WGS-84 & Earth Gravitational Model)
WGS84_A = 6378.137  # Earth semi-major axis (km)
WGS84_F = 1.0 / 298.257223563  # Flattening
WGS84_E2 = WGS84_F * (2.0 - WGS84_F)  # First eccentricity squared
MU_EARTH = 398600.4418  # Earth gravitational parameter (km^3/s^2)
OMEGA_EARTH = 7.2921151467e-5  # Earth rotation rate (rad/s)
J2 = 1.08262668e-3  # Second zonal harmonic
OMEGA_SSO = 1.99096871e-7  # SSO nodal precession rate (rad/s, ~360 deg/year)


def julian_date_parts(dt: datetime) -> tuple[float, float]:
    """Split UTC datetime into whole Julian Date and fractional day part."""
    dt = dt.astimezone(timezone.utc)
    y, m, d = dt.year, dt.month, dt.day
    hour = dt.hour + dt.minute / 60.0 + dt.second / 3600.0 + dt.microsecond / 3.6e9
    if m <= 2:
        y -= 1
        m += 12
    a = y // 100
    b = 2 - a + a // 4
    jd = int(365.25 * (y + 4716)) + int(30.6001 * (m + 1)) + d + b - 1524.5
    return float(jd), hour / 24.0


def gmst_rad(jd: float, fr: float) -> float:
    """Greenwich Mean Sidereal Time in radians for given Julian Date parts."""
    dtt = (jd - 2451545.0) + fr
    t = dtt / 36525.0
    gmst_deg = (
        280.46061837
        + 360.98564736629 * dtt
        + 0.000387933 * t * t
        - (t ** 3) / 38710000.0
    )
    return radians(gmst_deg % 360.0)


def teme_to_ecef(r_teme: np.ndarray | list[float], v_teme: np.ndarray | list[float], gmst: float) -> tuple[np.ndarray, np.ndarray]:
    """Rotate TEME (True Equator, Mean Equinox) inertial state to ECEF."""
    c, s = cos(gmst), sin(gmst)
    x, y, z = r_teme
    vx, vy, vz = v_teme
    r_ecef = np.array([c * x + s * y, -s * x + c * y, z], dtype=float)
    v_rot = np.array([c * vx + s * vy, -s * vx + c * vy, vz], dtype=float)
    omega = np.array([0.0, 0.0, OMEGA_EARTH])
    v_ecef = v_rot - np.cross(omega, r_ecef)
    return r_ecef, v_ecef


def ecef_to_geodetic(x: float, y: float, z: float) -> tuple[float, float, float]:
    """Convert ECEF Cartesian coordinates (km) to Geodetic lat, lon (deg), and altitude (km).

    Uses Bowring's iterative method for high precision on WGS-84.
    """
    lon = atan2(y, x)
    p = hypot(x, y)
    lat = atan2(z, p * (1.0 - WGS84_E2))
    for _ in range(8):
        sin_lat = sin(lat)
        n = WGS84_A / sqrt(1.0 - WGS84_E2 * sin_lat * sin_lat)
        lat = atan2(z + n * WGS84_E2 * sin_lat, p)
    sin_lat = sin(lat)
    n = WGS84_A / sqrt(1.0 - WGS84_E2 * sin_lat * sin_lat)
    if abs(cos(lat)) > 1e-10:
        alt = p / cos(lat) - n
    else:
        alt = abs(z) / abs(sin_lat) - n * (1.0 - WGS84_E2)
    return degrees(lat), degrees(lon), alt


def geodetic_to_ecef(lat_deg: float, lon_deg: float, alt_km: float) -> np.ndarray:
    """Convert Geodetic coordinates (lat, lon in degrees, altitude in km) to ECEF (km)."""
    lat, lon = radians(lat_deg), radians(lon_deg)
    sin_lat = sin(lat)
    n = WGS84_A / sqrt(1.0 - WGS84_E2 * sin_lat * sin_lat)
    x = (n + alt_km) * cos(lat) * cos(lon)
    y = (n + alt_km) * cos(lat) * sin(lon)
    z = (n * (1.0 - WGS84_E2) + alt_km) * sin_lat
    return np.array([x, y, z], dtype=float)


def ecef_velocity_heading(lat_deg: float, lon_deg: float, v_ecef: np.ndarray | list[float]) -> tuple[float, float, float]:
    """Decompose ECEF velocity into ground heading (deg), ground speed (km/s), and vertical speed (km/s)."""
    lat, lon = radians(lat_deg), radians(lon_deg)
    slat, clat = sin(lat), cos(lat)
    slon, clon = sin(lon), cos(lon)
    vx, vy, vz = float(v_ecef[0]), float(v_ecef[1]), float(v_ecef[2])
    east = -slon * vx + clon * vy
    north = -slat * clon * vx - slat * slon * vy + clat * vz
    up = clat * clon * vx + clat * slon * vy + slat * vz
    heading = (degrees(atan2(east, north)) + 360.0) % 360.0
    ground_speed = hypot(east, north)
    return heading, ground_speed, up


def compass_label(heading_deg: float) -> str:
    """Convert heading in degrees (0-360) to 16-wind compass abbreviation."""
    dirs = ["N", "NNE", "NE", "ENE", "E", "ESE", "SE", "SSE",
            "S", "SSW", "SW", "WSW", "W", "WNW", "NW", "NNW"]
    idx = int((heading_deg + 11.25) // 22.5) % 16
    return dirs[idx]


def circular_speed_kms(alt_km: float) -> float:
    """Vis-viva circular orbital speed at given altitude (km/s)."""
    a = WGS84_A + alt_km
    return sqrt(MU_EARTH / a)


def orbital_period_min(alt_km: float) -> float:
    """Keplerian orbital period in minutes for a circular orbit at alt_km."""
    a = WGS84_A + alt_km
    return 2.0 * np.pi * sqrt(a ** 3 / MU_EARTH) / 60.0


def sso_inclination_deg(alt_km: float) -> float:
    """Sun-synchronous inclination for nodal regression matching mean solar motion."""
    a = WGS84_A + alt_km
    n_term = sqrt(MU_EARTH)
    cosi = -(2.0 * OMEGA_SSO * (a ** 3.5)) / (3.0 * J2 * (WGS84_A ** 2) * n_term)
    cosi = max(-1.0, min(1.0, cosi))
    return degrees(acos(cosi))


def wrap_lon(lon: float) -> float:
    """Wrap longitude to [-180, 180] degrees."""
    return ((lon + 180.0) % 360.0) - 180.0


# ---------------------------------------------------------------------------
# Topocentric Horizon Coordinates & Satellite Pass Prediction
# ---------------------------------------------------------------------------

def ecef_to_topocentric_aer(
    obs_lat_deg: float,
    obs_lon_deg: float,
    obs_alt_km: float,
    sat_ecef: np.ndarray | list[float],
) -> tuple[float, float, float]:
    """Calculate topocentric Azimuth, Elevation (degrees), and Slant Range (km)

    From an observer at (obs_lat_deg, obs_lon_deg, obs_alt_km) to a satellite.
    """
    obs_ecef = geodetic_to_ecef(obs_lat_deg, obs_lon_deg, obs_alt_km)
    dx = float(sat_ecef[0]) - float(obs_ecef[0])
    dy = float(sat_ecef[1]) - float(obs_ecef[1])
    dz = float(sat_ecef[2]) - float(obs_ecef[2])

    lat, lon = radians(obs_lat_deg), radians(obs_lon_deg)
    slat, clat = sin(lat), cos(lat)
    slon, clon = sin(lon), cos(lon)

    # Local East, North, Up (ENU) frame
    east = -slon * dx + clon * dy
    north = -slat * clon * dx - slat * slon * dy + clat * dz
    up = clat * clon * dx + clat * slon * dy + slat * dz

    range_km = hypot(hypot(east, north), up)
    if range_km < 1e-6:
        return 0.0, 90.0, 0.0

    el_deg = degrees(asin(max(-1.0, min(1.0, up / range_km))))
    az_deg = (degrees(atan2(east, north)) + 360.0) % 360.0

    return az_deg, el_deg, range_km


def predict_passes_sgp4(
    satrec: Any,
    obs_lat: float,
    obs_lon: float,
    obs_alt_m: float = 0.0,
    start_time: datetime | None = None,
    duration_hours: float = 48.0,
    min_elevation_deg: float = 10.0,
    time_step_sec: int = 45,
) -> list[dict]:
    """Calculate visible/radio satellite passes over an observer using SGP4.

    Returns a list of pass dictionaries with:
      - aos_utc: Acquisition of Signal timestamp
      - tca_utc: Time of Closest Approach (peak elevation)
      - los_utc: Loss of Signal timestamp
      - max_elevation: peak elevation in degrees
      - aos_azimuth / los_azimuth: entry and exit azimuths
      - duration_min: pass duration
      - trajectory: array of sample points during the pass
    """
    start_time = (start_time or datetime.now(timezone.utc)).astimezone(timezone.utc)
    end_time = start_time + timedelta(hours=duration_hours)
    obs_alt_km = obs_alt_m / 1000.0

    passes = []
    in_pass = False
    current_pass: dict[str, Any] = {}

    current_t = start_time
    while current_t <= end_time:
        # Convert time to SGP4 format
        from sgp4.api import jday
        jd, fr = jday(
            current_t.year, current_t.month, current_t.day,
            current_t.hour, current_t.minute,
            current_t.second + current_t.microsecond * 1e-6,
        )
        err, r_teme, v_teme = satrec.sgp4(jd, fr)
        if err == 0 and r_teme is not None:
            jd_w, fr_p = julian_date_parts(current_t)
            gmst = gmst_rad(jd_w, fr_p)
            r_ecef, _ = teme_to_ecef(r_teme, v_teme, gmst)

            az, el, rng = ecef_to_topocentric_aer(obs_lat, obs_lon, obs_alt_km, r_ecef)

            if el >= min_elevation_deg:
                pt = {
                    "time": current_t.strftime("%H:%M:%S"),
                    "az": round(az, 1),
                    "el": round(el, 1),
                    "range_km": round(rng, 1),
                }
                if not in_pass:
                    in_pass = True
                    current_pass = {
                        "aos_utc": current_t,
                        "aos_az": az,
                        "aos_dir": compass_label(az),
                        "max_el": el,
                        "tca_utc": current_t,
                        "tca_az": az,
                        "tca_dir": compass_label(az),
                        "min_range_km": rng,
                        "points": [pt],
                    }
                else:
                    current_pass["points"].append(pt)
                    if el > current_pass["max_el"]:
                        current_pass["max_el"] = el
                        current_pass["tca_utc"] = current_t
                        current_pass["tca_az"] = az
                        current_pass["tca_dir"] = compass_label(az)
                        current_pass["min_range_km"] = min(current_pass["min_range_km"], rng)
            else:
                if in_pass:
                    # Pass completed
                    in_pass = False
                    current_pass["los_utc"] = current_t
                    current_pass["los_az"] = az
                    current_pass["los_dir"] = compass_label(az)
                    duration_s = (current_pass["los_utc"] - current_pass["aos_utc"]).total_seconds()
                    current_pass["duration_min"] = round(duration_s / 60.0, 1)
                    current_pass["max_el"] = round(current_pass["max_el"], 1)
                    current_pass["min_range_km"] = round(current_pass["min_range_km"], 1)
                    current_pass["quality"] = (
                        "Superb (High Elevation)" if current_pass["max_el"] > 60
                        else "Good" if current_pass["max_el"] > 30
                        else "Low Pass"
                    )
                    passes.append(current_pass)
                    current_pass = {}

        current_t += timedelta(seconds=time_step_sec)

    return passes


def compute_satellite_ground_track(
    satrec: Any,
    start_time: datetime | None = None,
    duration_minutes: int = 95,
    step_sec: int = 60,
) -> list[dict]:
    """Compute future ground track points for a satellite over 1-2 orbits."""
    start_time = (start_time or datetime.now(timezone.utc)).astimezone(timezone.utc)
    steps = int(duration_minutes * 60 / step_sec)
    track = []

    from sgp4.api import jday
    for i in range(steps):
        t = start_time + timedelta(seconds=i * step_sec)
        jd, fr = jday(t.year, t.month, t.day, t.hour, t.minute, t.second + t.microsecond * 1e-6)
        err, r, v = satrec.sgp4(jd, fr)
        if err != 0 or r is None:
            continue
        jd_w, fr_p = julian_date_parts(t)
        gmst = gmst_rad(jd_w, fr_p)
        r_ecef, v_ecef = teme_to_ecef(r, v, gmst)
        lat, lon, alt = ecef_to_geodetic(*r_ecef)
        track.append({
            "lat": round(lat, 3),
            "lon": round(wrap_lon(lon), 3),
            "alt_km": round(alt, 1),
            "time_iso": t.strftime("%H:%M:%S UTC"),
            "x": float(r_ecef[0]),
            "y": float(r_ecef[1]),
            "z": float(r_ecef[2]),
        })
    return track


# ---------------------------------------------------------------------------
# Spacecraft Distance & Launch Geometry
# ---------------------------------------------------------------------------

def min_3d_distance_km(path_rows: list[dict], objects: list[dict]) -> tuple[float, str, dict | None]:
    """Find minimum 3D Euclidean distance between a candidate path and space objects."""
    if not path_rows or not objects:
        return float("inf"), "None", None
    path_xyz = np.array([[p["x"], p["y"], p["z"]] for p in path_rows], dtype=float)
    obj_xyz = np.array([[o["x"], o["y"], o["z"]] for o in objects], dtype=float)
    # Broadcasting: (P,1,3) - (1,O,3)
    d = np.linalg.norm(path_xyz[:, None, :] - obj_xyz[None, :, :], axis=2)
    idx = np.unravel_index(int(np.argmin(d)), d.shape)
    dist = float(d[idx])
    obj = objects[int(idx[1])]
    return dist, str(obj.get("name", "Tracked object")), obj


def launch_trajectory(
    lat0: float,
    lon0: float,
    azimuth_deg: float,
    target_alt_km: float,
    when: datetime,
    ascent_points: int = 24,
    orbit_points: int = 72,
) -> list[dict]:
    """Ascent to insertion, then one revolution of resulting circular orbit."""
    inc = degrees(acos(max(-1.0, min(1.0, cos(radians(lat0)) * sin(radians(azimuth_deg))))))
    a = WGS84_A + target_alt_km
    period_s = 2.0 * np.pi * sqrt(a ** 3 / MU_EARTH)
    v_ins = circular_speed_kms(target_alt_km)
    heading_ascent = azimuth_deg

    insert_range_km = min(1400.0, 350.0 + target_alt_km * 0.9)
    ang = insert_range_km / WGS84_A
    az = radians(azimuth_deg)
    lat0r, lon0r = radians(lat0), radians(lon0)
    insert_lat = asin(sin(lat0r) * cos(ang) + cos(lat0r) * sin(ang) * cos(az))
    insert_lon = lon0r + atan2(
        sin(az) * sin(ang) * cos(lat0r),
        cos(ang) - sin(lat0r) * sin(insert_lat),
    )
    insert_lat_d, insert_lon_d = degrees(insert_lat), degrees(insert_lon)

    jd, fr = julian_date_parts(when)
    gmst = gmst_rad(jd, fr)

    si = sin(radians(inc)) or 1e-9
    sin_u = max(-1.0, min(1.0, sin(insert_lat) / si))
    u0 = degrees(asin(sin_u))
    if 90 < (azimuth_deg % 360) < 270:
        u0 = 180.0 - u0

    inertial_lon = degrees(gmst) + insert_lon_d
    node_offset = degrees(atan2(cos(radians(inc)) * sin(radians(u0)), cos(radians(u0))))
    raan = (inertial_lon - node_offset) % 360.0

    rows = []
    # Ascent
    for i_pt, t in enumerate(np.linspace(0.0, 1.0, ascent_points, endpoint=False)):
        alt = target_alt_km * (t ** 2) * (3 - 2 * t)
        rng = insert_range_km * t
        ang_t = rng / WGS84_A
        lat = asin(sin(lat0r) * cos(ang_t) + cos(lat0r) * sin(ang_t) * cos(az))
        lon = lon0r + atan2(
            sin(az) * sin(ang_t) * cos(lat0r),
            cos(ang_t) - sin(lat0r) * sin(lat),
        )
        speed = 0.4 + (v_ins - 0.4) * (t ** 1.35)
        lat_d, lon_d = degrees(lat), wrap_lon(degrees(lon))
        r_ecef = geodetic_to_ecef(lat_d, lon_d, alt)
        rows.append({
            "lat": lat_d,
            "lon": lon_d,
            "alt_km": float(alt),
            "speed_kms": float(speed),
            "heading_deg": float(heading_ascent),
            "phase": "ascent",
            "step": i_pt,
            "x": float(r_ecef[0]),
            "y": float(r_ecef[1]),
            "z": float(r_ecef[2]),
            "alt_m": float(alt * 1000.0),
        })

    # One revolution after insertion
    i_rad, raan_rad = radians(inc), radians(raan)
    ci, si_val = cos(i_rad), sin(i_rad)
    cr, sr = cos(raan_rad), sin(raan_rad)

    for j, du in enumerate(np.linspace(0.0, 360.0, orbit_points, endpoint=False)):
        u = radians((u0 + du) % 360.0)
        elapsed = (du / 360.0) * period_s
        x_orb = a * cos(u)
        y_orb = a * sin(u)
        n = sqrt(MU_EARTH / a ** 3)
        vx_orb = -a * n * sin(u)
        vy_orb = a * n * cos(u)

        r_eci = np.array([
            cr * x_orb - sr * ci * y_orb,
            sr * x_orb + cr * ci * y_orb,
            si_val * y_orb,
        ])
        v_eci = np.array([
            cr * vx_orb - sr * ci * vy_orb,
            sr * vx_orb + cr * ci * vy_orb,
            si_val * vy_orb,
        ])

        gmst_t = gmst + OMEGA_EARTH * elapsed
        r_ecef, v_ecef = teme_to_ecef(r_eci, v_eci, gmst_t)
        lat, lon, alt = ecef_to_geodetic(*r_ecef)
        heading, gspd, _ = ecef_velocity_heading(lat, lon, v_ecef)
        rows.append({
            "lat": lat,
            "lon": wrap_lon(lon),
            "alt_km": float(alt),
            "speed_kms": float(np.linalg.norm(v_eci)),
            "heading_deg": heading,
            "phase": "orbit",
            "step": ascent_points + j,
            "x": float(r_ecef[0]),
            "y": float(r_ecef[1]),
            "z": float(r_ecef[2]),
            "alt_m": float(max(alt, 0.0) * 1000.0),
            "elapsed_s": elapsed,
        })
    return rows
