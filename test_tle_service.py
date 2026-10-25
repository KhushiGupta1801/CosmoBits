"""Unit tests for TLE parsing and SGP4 propagation service."""
from __future__ import annotations

import unittest
from datetime import datetime, timezone
from services.tle_service import (
    OFFLINE_TLE_RAW,
    get_offline_records,
    parse_tles,
    propagate_record,
    search_satellites,
)


class TestTLEService(unittest.TestCase):
    def test_parse_tles(self):
        sample = """ISS (ZARYA)
1 25544U 98067A   24143.51860046  .00014878  00000+0  26859-3 0  9997
2 25544  51.6416 112.5975 0005432  38.7495  68.2195 15.49832261454523
"""
        records = parse_tles(sample, "stations")
        self.assertEqual(len(records), 1)
        self.assertEqual(records[0]["name"], "ISS (ZARYA)")
        self.assertEqual(records[0]["group"], "stations")

    def test_propagate_iss(self):
        now = datetime.now(timezone.utc)
        epoch_str = f"{now.year % 100:02d}{now.timetuple().tm_yday:03d}.50000000"
        rec = {
            "name": "ISS (ZARYA)",
            "l1": f"1 25544U 98067A   {epoch_str}  .00002000  00000+0  35000-4 0  9997",
            "l2": "2 25544  51.6416 112.5975 0005432  38.7495  68.2195 15.49832261454523",
            "group": "stations",
        }
        res = propagate_record(rec, now)
        self.assertIsNotNone(res)
        self.assertEqual(res["name"], "ISS (ZARYA)")
        self.assertEqual(res["norad_id"], 25544)
        # Verify geodetic range
        self.assertTrue(-90 <= res["lat"] <= 90)
        self.assertTrue(-180 <= res["lon"] <= 180)
        self.assertTrue(380 <= res["alt_km"] <= 450)
        self.assertTrue(7.4 <= res["speed_kms"] <= 7.8)
        self.assertTrue(90 <= res["period_min"] <= 95)

    def test_search_satellites(self):
        mock_objects = [
            {"name": "ISS (ZARYA)", "norad_id": 25544},
            {"name": "TIANGONG (CSS)", "norad_id": 48274},
            {"name": "HUBBLE", "norad_id": 20580},
        ]
        res1 = search_satellites("hubble", mock_objects)
        self.assertEqual(len(res1), 1)
        self.assertEqual(res1[0]["norad_id"], 20580)

        res2 = search_satellites("25544", mock_objects)
        self.assertEqual(len(res2), 1)
        self.assertEqual(res2[0]["name"], "ISS (ZARYA)")


if __name__ == "__main__":
    unittest.main()
