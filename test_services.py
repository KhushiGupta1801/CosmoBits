"""Unit tests for ISS, Space Weather, and AI Knowledge services."""
from __future__ import annotations

import unittest
from services.ai_service import offline_knowledge_engine, query_ai_assistant
from services.iss_service import get_humans_in_space, get_live_iss_telemetry
from services.space_weather_service import get_space_weather_data


class TestServices(unittest.TestCase):
    def test_iss_telemetry_fallback(self):
        data = get_live_iss_telemetry()
        self.assertIn("lat", data)
        self.assertIn("lon", data)
        self.assertIn("alt_km", data)
        self.assertIn("speed_kms", data)
        self.assertTrue(350 <= data["alt_km"] <= 460)

    def test_space_weather_structure(self):
        data = get_space_weather_data()
        self.assertIn("kp_index", data)
        self.assertIn("solar_radio_flux_sfu", data)
        self.assertIn("geomagnetic_scale", data)
        self.assertTrue(0.0 <= data["kp_index"] <= 9.0)

    def test_offline_ai_knowledge(self):
        res1 = offline_knowledge_engine("Explain sun-synchronous orbit")
        self.assertIn("Sun-Synchronous", res1)

        res2 = offline_knowledge_engine("What are Keplerian orbital elements?")
        self.assertIn("Semi-Major Axis", res2)

        res3 = offline_knowledge_engine("Explain Kessler syndrome")
        self.assertIn("Kessler", res3)

    def test_query_ai_assistant_offline(self):
        answer, provider = query_ai_assistant("Hello")
        self.assertIn("Cosmo Bites", provider)


if __name__ == "__main__":
    unittest.main()
