# ⚡ Cosmo Bites — Space Situational Awareness & Satellite Tracking Platform

[![Python 3.10+](https://img.shields.io/badge/Python-3.10%2B-00D2FF.svg)](https://www.python.org/)
[![Streamlit 1.35+](https://img.shields.io/badge/Streamlit-1.35%2B-1D4ED8.svg)](https://streamlit.io/)
[![Plotly 5.18+](https://img.shields.io/badge/Plotly-5.18%2B-38BDF8.svg)](https://plotly.com/)
[![SGP4 2.23+](https://img.shields.io/badge/SGP4-WGS84-00D2FF.svg)](https://pypi.org/project/sgp4/)

**Cosmo Bites** is an aerospace-grade space situational awareness (SSA), satellite tracking, and orbital collision simulation platform. Built with Python, Streamlit, and Plotly, it integrates analytical orbital mechanics with live telemetry from global space institutions: NORAD / CelesTrak, NOAA Space Weather Prediction Center, and the International Space Station live feed.

---

## 🌟 Core Modules & Features

1. **🛰️ Dashboard**: Central mission command overview with real-time operational telemetry (tracked fleet count, live ISS velocity/altitude, NOAA planetary Kp-index, solar 10.7cm radio flux) and global 2D satellite ground track.
2. **📡 Satellite Tracking**: Search 600+ space objects by name or NORAD catalog ID. Real-time geodetic coordinates (Lat/Lon/Alt), speed, orbital period, inclination, and 2-orbit ground track projection.
3. **🌐 3D Earth View**: Interactive 3D digital Earth rendering orbital trajectories, satellite clusters, and sub-satellite points in Earth-Centered Earth-Fixed (ECEF) Cartesian space.
4. **📊 Orbit Analysis**: Empirical parameter distributions illustrating Kepler's laws ($v = \sqrt{\mu / r}$, $T^2 \propto a^3$), LEO/MEO/GEO clustering, and orbital inclination histograms.
5. **💥 Collision Simulator**: High-precision satellite collision & conjunction analysis engine. Computes Time of Closest Approach (TCA), closest encounter miss distance, relative velocity, collision probability ($P_c$), and automated Collision Avoidance Maneuver (CAM) $\Delta v$ solutions.
6. **🤖 AI Assistant**: Aerospace engineering and orbital mechanics conversational specialist powered by Google Gemini / OpenAI API or the built-in offline space knowledge engine.
7. **🗑️ Space Debris Monitoring**: Spatial debris altitude density histograms, fragmentation event analysis (Cosmos-2251, Fengyun-1C), and educational deep-dives on the Kessler Syndrome and Active Debris Removal (ADR).
8. **⚙️ Settings**: Full configuration hub for interface themes, telemetry sources, observer ground station coordinates, AI API keys, and local ephemeris cache management.

---

## 📁 Project Architecture

```
cosmo_bites/
├── app.py                         # Main application entry point & sidebar router
├── requirements.txt               # Core Python dependencies
├── README.md                      # Comprehensive documentation & deployment guide
├── run_cosmobites.sh              # 1-Click launcher script for Linux & macOS
├── run_cosmobites.bat             # 1-Click launcher script for Windows
├── RUN_COSMOBITS.bat              # Windows batch launcher (uppercase compatibility)
├── .env.example                   # Template for optional API keys (GEMINI_API_KEY)
├── .gitignore                     # Git ignore rules for venv, cache, and secrets
├── .streamlit/
│   └── config.toml                # Custom Streamlit space theme & server configuration
├── assets/
│   ├── cosmobits_logo.svg         # Official Cosmo Bites vector emblem
│   ├── cosmobits_icon.svg         # Scalable Cosmo Bites orbital icon
│   └── style.css                  # Custom CSS: black & charcoal canvas, white cards, light blue highlights
├── components/
│   ├── header.py                  # Mission control header with Cosmo Bites logo & UTC clock
│   ├── cards.py                   # Aerospace metric tiles, status pills & HTML helper
│   └── styles.py                  # CSS injection and style loading utilities
├── services/
│   ├── orbit_service.py           # SGP4, WGS-84 ellipsoid, TEME/ECEF transformations, pass predictor
│   ├── tle_service.py             # CelesTrak NORAD TLE ingestion, multi-catalog management & disk caching
│   ├── iss_service.py             # Live ISS REST telemetry (WhereTheISS / Open-Notify) + SGP4 backup
│   ├── space_weather_service.py   # NOAA SWPC live solar flux, Kp index, and geomagnetic storm scales
│   └── ai_service.py              # Gemini/OpenAI API caller + offline educational space knowledge engine
├── pages/
│   ├── dashboard.py               # Mission overview, 2D fleet ground track & quick action hub
│   ├── satellite_tracker.py       # Satellite search, ephemeris table & orbital path inspector
│   ├── globe_3d.py                # Interactive 3D Earth globe with 3D orbit curves
│   ├── orbit_analytics.py         # Plotly charts: altitude, velocity, period, inclination
│   ├── collision_simulator.py     # Interactive satellite collision & conjunction simulator
│   ├── ai_assistant.py            # AI Chat interface for orbital mechanics & space physics
│   ├── space_debris.py            # Space debris distribution, collision risks & Kessler syndrome
│   ├── settings.py                # System settings, observer coordinates, API keys, cache control
│   ├── iss_tracker.py             # Dedicated ISS tracking, live coordinates & crew manifest
│   ├── space_weather.py           # NOAA solar activity, Kp trends & LEO satellite drag impact
│   ├── pass_predictor.py          # Observer horizon pass prediction with polar sky chart
│   └── about.py                   # Documentation, mathematical formulation & data attributions
├── tests/
│   ├── test_orbit_math.py         # Unit tests for geodetics, Julian Date, ECEF/TEME, and pass geometry
│   ├── test_tle_service.py        # Unit tests for TLE parsing, propagation & search
│   ├── test_services.py           # Unit tests for ISS, weather, and AI services
│   └── test_pages_smoke.py        # Smoke tests verifying imports across all modules
└── legacy_prototype/              # Preserved prototype files (index.html, java.js, script.css)
```

---

## 🚀 Installation & Running

### Linux / macOS (1-Click)

```bash
# 1. Grant execute permissions (first time only)
chmod +x run_cosmobites.sh

# 2. Launch Cosmo Bites
./run_cosmobites.sh
```
*The script will verify your Python environment, create a virtual environment, install requirements, and open `http://localhost:8501` automatically.*

---

### Windows (1-Click)

1. Double-click **`RUN_COSMOBITS.bat`** (or `run_cosmobites.bat`).
2. Wait for dependencies to install. Cosmo Bites will automatically launch in your browser at `http://localhost:8501`.

---

### Manual Setup (Any OS)

```bash
# 1. Create a virtual environment
python3 -m venv .venv

# 2. Activate virtual environment
# Windows: .venv\Scripts\activate
# Linux/macOS:
source .venv/bin/activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. (Optional) Configure Google Gemini API key
cp .env.example .env

# 5. Launch Cosmo Bites
streamlit run app.py
```

---

## 🧪 Running Automated Unit Tests

Cosmo Bites includes a unit test suite verifying orbital calculations, coordinate transformations, TLE parsing, and service fallbacks:

```bash
python -m unittest discover -s tests -p "test_*.py" -v
```

---

## 📡 Data Sources & Attribution

| Provider | Data Feed / Endpoint | Usage in Cosmo Bites |
|---|---|---|
| **CelesTrak (NORAD GP API)** | `https://celestrak.org/NORAD/elements/gp.php` | Two-Line Element (TLE) sets for Space Stations, Visual, Weather, GPS, Science, and Analyst debris objects. |
| **NOAA Space Weather Prediction Center (SWPC)** | `https://services.swpc.noaa.gov/products/` | Real-time Planetary K-index, 10.7cm solar radio flux, solar wind velocity, and geomagnetic storm severity scales. |
| **Where The ISS At (WTIA)** | `https://api.wheretheiss.at/v1/satellites/25544` | High-accuracy real-time ISS geodetic coordinates, orbital speed, and altitude. |
| **Open-Notify** | `http://api.open-notify.org/` | Real-time backup ISS coordinates and human spaceflight crew manifests. |
| **SGP4 / WGS-84** | Analytical Ephemeris Propagator | Validated mathematical propagation of TEME state vectors to ECEF/Geodetic coordinates. |

---

## ⚖️ Engineering Disclaimer
Cosmo Bites is designed for space situational awareness, educational research, and mission visualization. SGP4 propagation relies on unclassified TLE data and spherical Earth/TEME approximations; it does not replace certified mission flight-dynamics or Department of Defense operational Conjunction Data Messages (CDMs).
