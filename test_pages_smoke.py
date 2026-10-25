"""Smoke test to verify all page modules and service endpoints import without error."""
from __future__ import annotations

import unittest

class TestImportsSmoke(unittest.TestCase):
    def test_import_all_modules(self):
        import app
        import components.cards
        import components.header
        import components.styles
        import pages.about
        import pages.ai_assistant
        import pages.dashboard
        import pages.globe_3d
        import pages.iss_tracker
        import pages.orbit_analytics
        import pages.pass_predictor
        import pages.satellite_tracker
        import pages.space_debris
        import pages.space_weather
        import services.ai_service
        import services.iss_service
        import services.orbit_service
        import services.space_weather_service
        import services.tle_service

        self.assertTrue(True)

if __name__ == "__main__":
    unittest.main()
