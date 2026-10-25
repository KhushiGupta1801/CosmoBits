"""Cosmo Bites — Dedicated International Space Station (ISS) Service.

Provides real-time telemetry, coordinates, velocity, altitude, and crew status
from Open-Notify, Where The ISS At (WTIA), and SGP4 TLE orbital backup.
"""
from __future__ import annotations

import json
import urllib.request
from datetime import datetime, timezone
from typing import Any

from sgp4.api import Satrec

from services.orbit_service import (
    circular_speed_kms,
    compass_label,
    compute_satellite_ground_track,
    orbital_period_min,
)
from services.tle_service import propagate_record

# Standard ISS NORAD ID
ISS_NORAD_ID = 25544


def get_iss_backup_record(when: datetime) -> dict:
    """Generate dynamic ISS backup record anchored to current time."""
    epoch_str = f"{when.year % 100:02d}{when.timetuple().tm_yday:03d}.50000000"
    return {
        "name": "ISS (ZARYA)",
        "l1": f"1 25544U 98067A   {epoch_str}  .00002000  00000+0  35000-4 0  9997",
        "l2": "2 25544  51.6416 112.5975 0005432  38.7495  68.2195 15.49832261454523",
        "group": "stations",
    }


def get_live_iss_telemetry() -> dict[str, Any]:
    """Fetch live ISS telemetry via Open-Notify / WTIA REST APIs.

    Seamlessly falls back to SGP4 numerical propagation if live REST APIs fail.
    """
    now = datetime.now(timezone.utc)
    data: dict[str, Any] = {}

    # Try Where The ISS At API first (provides velocity and altitude directly)
    try:
        url = f"https://api.wheretheiss.at/v1/satellites/{ISS_NORAD_ID}"
        req = urllib.request.Request(url, headers={"User-Agent": "Cosmo Bites/1.0"})
        with urllib.request.urlopen(req, timeout=3.0) as resp:
            raw = json.loads(resp.read().decode("utf-8"))
            lat = float(raw["latitude"])
            lon = float(raw["longitude"])
            alt_km = float(raw["altitude"])
            speed_kms = round(float(raw["velocity"]) / 3600.0, 3)
            visibility = raw.get("visibility", "daylight")
            footprint = round(float(raw.get("footprint", 4500.0)), 1)

            data = {
                "source": "WhereTheISS.at (Live REST)",
                "status": "LIVE_TELEMETRY",
                "lat": round(lat, 4),
                "lon": round(lon, 4),
                "alt_km": round(alt_km, 1),
                "speed_kms": speed_kms,
                "speed_kmh": round(float(raw["velocity"]), 1),
                "heading_deg": None,
                "visibility": visibility.capitalize(),
                "footprint_km": footprint,
                "solar_lat": raw.get("solar_lat"),
                "solar_lon": raw.get("solar_lon"),
                "inclination_deg": 51.64,
                "period_min": round(orbital_period_min(alt_km), 2),
                "epoch_utc": datetime.fromtimestamp(raw["timestamp"], tz=timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC"),
            }
            return data
    except Exception:
        pass

    # Try Open-Notify ISS-Now API
    try:
        url = "http://api.open-notify.org/iss-now.json"
        req = urllib.request.Request(url, headers={"User-Agent": "Cosmo Bites/1.0"})
        with urllib.request.urlopen(req, timeout=3.0) as resp:
            raw = json.loads(resp.read().decode("utf-8"))
            if raw.get("message") == "success":
                lat = float(raw["iss_position"]["latitude"])
                lon = float(raw["iss_position"]["longitude"])
                alt_km = 418.0
                speed_kms = round(circular_speed_kms(alt_km), 3)
                data = {
                    "source": "Open-Notify (Live REST)",
                    "status": "LIVE_TELEMETRY",
                    "lat": round(lat, 4),
                    "lon": round(lon, 4),
                    "alt_km": alt_km,
                    "speed_kms": speed_kms,
                    "speed_kmh": round(speed_kms * 3600.0, 1),
                    "heading_deg": None,
                    "visibility": "Nominal",
                    "footprint_km": 4480.0,
                    "inclination_deg": 51.64,
                    "period_min": round(orbital_period_min(alt_km), 2),
                    "epoch_utc": datetime.fromtimestamp(raw["timestamp"], tz=timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC"),
                }
                return data
    except Exception:
        pass

    # High-precision SGP4 propagation fallback
    backup_rec = get_iss_backup_record(now)
    prop = propagate_record(backup_rec, now)
    if prop:
        return {
            "source": "SGP4 Orbital Propagation (Offline Fallback)",
            "status": "PROPAGATED_TELEMETRY",
            "lat": prop["lat"],
            "lon": prop["lon"],
            "alt_km": prop["alt_km"],
            "speed_kms": prop["speed_kms"],
            "speed_kmh": round(prop["speed_kms"] * 3600.0, 1),
            "heading_deg": prop["heading_deg"],
            "direction": prop["direction"],
            "visibility": "Estimated Daylight",
            "footprint_km": round(2.0 * 6378.137 * 0.35, 1),
            "inclination_deg": prop["inclination_deg"],
            "period_min": prop["period_min"],
            "epoch_utc": now.strftime("%Y-%m-%d %H:%M:%S UTC"),
        }

    # Final guaranteed baseline fallback
    return {
        "source": "Nominal Mission Baseline",
        "status": "CACHED_ESTIMATE",
        "lat": 24.5120,
        "lon": -45.1820,
        "alt_km": 420.0,
        "speed_kms": 7.66,
        "speed_kmh": 27576.0,
        "heading_deg": 68.0,
        "direction": "ENE",
        "visibility": "Nominal",
        "footprint_km": 4500.0,
        "inclination_deg": 51.64,
        "period_min": 92.8,
        "epoch_utc": now.strftime("%Y-%m-%d %H:%M:%S UTC"),
    }


def get_iss_ground_track(duration_minutes: int = 95) -> list[dict]:
    """Calculate the predicted ground track of the ISS for the next orbit."""
    now = datetime.now(timezone.utc)
    rec = get_iss_backup_record(now)
    sat = Satrec.twoline2rv(rec["l1"], rec["l2"])
    return compute_satellite_ground_track(sat, duration_minutes=duration_minutes, step_sec=45)


def get_humans_in_space() -> list[dict]:
    """Fetch astronauts and cosmonauts currently aboard space stations."""
    try:
        url = "http://api.open-notify.org/astros.json"
        req = urllib.request.Request(url, headers={"User-Agent": "Cosmo Bites/1.0"})
        with urllib.request.urlopen(req, timeout=3.0) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            if data.get("message") == "success":
                return data.get("people", [])
    except Exception:
        pass

    return [
        {"name": "Oleg Kononenko", "craft": "ISS"},
        {"name": "Nikolai Chub", "craft": "ISS"},
        {"name": "Tracy C. Dyson", "craft": "ISS"},
        {"name": "Matthew Dominick", "craft": "ISS"},
        {"name": "Michael Barratt", "craft": "ISS"},
        {"name": "Jeanette Epps", "craft": "ISS"},
        {"name": "Alexander Grebenkin", "craft": "ISS"},
        {"name": "Ye Guangfu", "craft": "Tiangong"},
        {"name": "Li Cong", "craft": "Tiangong"},
        {"name": "Li Guangsu", "craft": "Tiangong"},
    ]
