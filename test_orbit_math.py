"""Unit tests for Cosmo Bites orbital calculations & geodetics."""
from __future__ import annotations

import unittest
from datetime import datetime, timezone
import numpy as np

from services.orbit_service import (
    WGS84_A,
    circular_speed_kms,
    compass_label,
    ecef_to_geodetic,
    ecef_to_topocentric_aer,
    geodetic_to_ecef,
    gmst_rad,
    julian_date_parts,
    orbital_period_min,
    sso_inclination_deg,
    wrap_lon,
)


class TestOrbitMath(unittest.TestCase):
    def test_julian_date_parts(self):
        dt = datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
        jd, fr = julian_date_parts(dt)
        self.assertAlmostEqual(jd + fr, 2460311.0, places=4)

    def test_geodetic_ecef_roundtrip(self):
        lat_in, lon_in, alt_in = 28.5721, -80.6480, 420.0
        ecef = geodetic_to_ecef(lat_in, lon_in, alt_in)
        lat_out, lon_out, alt_out = ecef_to_geodetic(*ecef)

        self.assertAlmostEqual(lat_in, lat_out, places=4)
        self.assertAlmostEqual(lon_in, lon_out, places=4)
        self.assertAlmostEqual(alt_in, alt_out, places=2)

    def test_circular_speed(self):
        v = circular_speed_kms(400.0)
        self.assertTrue(7.6 < v < 7.8, f"Unexpected speed: {v}")

    def test_orbital_period(self):
        p = orbital_period_min(400.0)
        self.assertTrue(90.0 < p < 95.0, f"Unexpected period: {p}")

    def test_sso_inclination(self):
        inc = sso_inclination_deg(700.0)
        self.assertTrue(97.0 < inc < 99.0, f"Unexpected SSO inclination: {inc}")

    def test_compass_label(self):
        self.assertEqual(compass_label(0.0), "N")
        self.assertEqual(compass_label(90.0), "E")
        self.assertEqual(compass_label(180.0), "S")
        self.assertEqual(compass_label(270.0), "W")

    def test_wrap_lon(self):
        self.assertAlmostEqual(wrap_lon(190.0), -170.0)
        self.assertAlmostEqual(wrap_lon(-190.0), 170.0)
        self.assertAlmostEqual(wrap_lon(45.0), 45.0)

    def test_topocentric_aer_zenith(self):
        obs_lat, obs_lon, obs_alt_km = 0.0, 0.0, 0.0
        sat_ecef = geodetic_to_ecef(0.0, 0.0, 400.0)
        az, el, rng = ecef_to_topocentric_aer(obs_lat, obs_lon, obs_alt_km, sat_ecef)
        self.assertAlmostEqual(el, 90.0, places=2)
        self.assertAlmostEqual(rng, 400.0, places=1)


if __name__ == "__main__":
    unittest.main()
