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
        import pages.collision_simulator
        import pages.dashboard
        import pages.globe_3d
        import pages.iss_tracker
        import pages.orbit_analytics
        import pages.pass_predictor
        import pages.satellite_tracker
        import pages.settings
        import pages.space_debris
        import pages.space_weather
        import services.ai_service
        import services.iss_service
        import services.orbit_service
        import services.space_weather_service
        import services.tle_service

        self.assertTrue(True)

    def test_sanitize_html_strips_indents(self):
        from components.cards import sanitize_html
        raw = """
        <div class="test">
            <p>Line with 4 spaces</p>
                <span>Line with 8 spaces</span>
        </div>
        """
        cleaned = sanitize_html(raw)
        for line in cleaned.splitlines():
            self.assertFalse(line.startswith(" "), f"Line should not start with spaces: {line}")
            self.assertFalse(line.startswith("\t"), f"Line should not start with tabs: {line}")

    def test_css_palette_tokens(self):
        from pathlib import Path
        css_path = Path(__file__).resolve().parent.parent / "assets" / "style.css"
        self.assertTrue(css_path.exists())
        content = css_path.read_text(encoding="utf-8")
        self.assertIn("#070A12", content)
        self.assertIn("#0B1120", content)
        self.assertIn("#00D4FF", content)
        self.assertIn("Space Grotesk", content)
        self.assertIn("JetBrains Mono", content)

if __name__ == "__main__":
    unittest.main()
