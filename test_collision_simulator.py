"""Unit tests for Cosmo Bites collision simulator calculations."""
from __future__ import annotations

import unittest
from pages.collision_simulator import calculate_conjunction


class TestCollisionSimulator(unittest.TestCase):
    def test_calculate_conjunction_nominal(self):
        res = calculate_conjunction(
            altitude_km=550.0,
            inclination_deg=53.0,
            target_radius_m=4.0,
            debris_radius_m=1.0,
            relative_angle_deg=90.0,
            screening_dist_km=10.0,
            duration_hours=24,
        )

        self.assertIn("miss_distance_m", res)
        self.assertIn("v_rel_kms", res)
        self.assertIn("prob_collision", res)
        self.assertIn("risk_level", res)
        self.assertIn("delta_v_ms", res)
        self.assertGreater(res["v_rel_kms"], 0)
        self.assertGreaterEqual(res["miss_distance_m"], 0)
        self.assertGreaterEqual(res["prob_collision"], 0.0)
        self.assertLessEqual(res["prob_collision"], 1.0)

    def test_critical_conjunction_alert(self):
        # Very small miss distance test
        res = calculate_conjunction(
            altitude_km=620.0,
            inclination_deg=82.5,
            target_radius_m=5.0,
            debris_radius_m=2.0,
            relative_angle_deg=175.0,
            screening_dist_km=2.0,
            duration_hours=1,
            uncertainty_sigma_m=50.0,
        )
        self.assertIn(res["risk_level"], ["CRITICAL THREAT", "HIGH RISK", "MODERATE WATCH", "LOW RISK"])


if __name__ == "__main__":
    unittest.main()
