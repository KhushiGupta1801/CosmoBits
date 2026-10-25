# ⚡ CosmoBits — Space Situational Awareness & Satellite Tracking Platform

[![Python 3.10+](https://img.shields.io/badge/Python-3.10%2B-00F5D4.svg)](https://www.python.org/)
[![Streamlit 1.35+](https://img.shields.io/badge/Streamlit-1.35%2B-FF007F.svg)](https://streamlit.io/)
[![Plotly 5.18+](https://img.shields.io/badge/Plotly-5.18%2B-00D2FF.svg)](https://plotly.com/)
[![SGP4 2.23+](https://img.shields.io/badge/SGP4-WGS84-9D4EDD.svg)](https://pypi.org/project/sgp4/)

**CosmoBits** is a professional, modern, aerospace-grade space situational awareness (SSA) and satellite tracking platform. Built with Python, Streamlit, and Plotly, it integrates analytical orbital mechanics with live telemetry from global space institutions: NORAD / CelesTrak, NOAA Space Weather Prediction Center, and the International Space Station live feed.

---

## 🌟 Core Features

- **🌐 Interactive 3D Earth Globe**: High-precision 3D digital Earth rendering orbital trajectories, satellite clusters, and sub-satellite points in ECEF Cartesian space.
- **🛰️ Satellite Fleet Search & Telemetry**: Search 600+ space objects by name or NORAD catalog ID. Real-time geodetic coordinates, speed, altitude, period, and inclination.
- **🛸 Dedicated Live ISS Tracking**: Real-time position, orbital speed (km/s and km/h), sub-satellite ground footprint, next 90-minute projected orbit track, and live astronauts currently in orbit.
- **🔭 Ground Observer Pass Predictor**: Compute topocentric horizon passes (Acquisition of Signal, Peak Elevation, Loss of Signal) over custom coordinates or global presets (Bengaluru, Cape Canaveral, Houston, Tokyo, etc.) with a 360° polar sky plot.
- **☀️ NOAA Space Weather Telemetry**: Live Planetary Kp-index trend, 10.7cm solar radio flux, solar wind proton speed, and automated operational impact assessment on LEO satellite atmospheric drag and GNSS signals.
- **💥 Space Debris & Sustainability**: Spatial density histograms, fragmentation analysis (Cosmos-2251, Fengyun-1C), and educational deep-dives on the Kessler Syndrome and Active Debris Removal (ADR).
- **📊 Orbit Analytics & Keplerian Dynamics**: Empirical parameter distributions illustrating Kepler's laws, LEO/MEO/GEO clustering, and orbital period comparisons.
- **🤖 AI Space Assistant**: Multi-turn chat interface for aerospace engineering, Keplerian elements, and launch mechanics with Google Gemini / OpenAI API support and an extensive offline educational knowledge engine.
- **🎨 Deep Space Glassmorphism Interface**: Cyber-themed dark navy palette with electric cyan, blue, and purple neon highlights, custom CosmoBits logo & icon badges, responsive metrics, and status pills.

---

## 📁 Project Architecture

```
cosmobits/
├── app.py                     # Main application entry point & sidebar navigation router
├── requirements.txt           # Core Python dependencies
├── README.md                  # Comprehensive documentation & deployment guide
├── RUN_COSMOBITS.bat          # 1-Click launcher script for Windows
├── .env.example               # Template for optional API keys (GEMINI_API_KEY)
├── .gitignore                 # Git ignore rules for venv, cache, and secrets
├── .streamlit/
│   └── config.toml            # Custom Streamlit space theme & server configuration
├── assets/
│   ├── cosmobits_logo.svg     # Official CosmoBits vector emblem
│   ├── cosmobits_icon.svg     # Scalable CosmoBits orbital icon
│   └── style.css              # Custom CSS: glassmorphism, glowing badges, monospace telemetry
├── components/
│   ├── header.py              # Mission control header with CosmoBits top-right logo & UTC clock
│   ├── cards.py               # Sleek glassmorphism metric tiles & glowing status pills
│   └── styles.py              # CSS injection and style loading utilities
├── services/
│   ├── orbit_service.py       # SGP4, WGS-84 ellipsoid, TEME/ECEF transformations, pass predictor
│   ├── tle_service.py         # CelesTrak NORAD TLE ingestion, multi-catalog management & disk caching
│   ├── iss_service.py         # Live ISS REST telemetry (WhereTheISS / Open-Notify) + SGP4 backup
│   ├── space_weather_service.py # NOAA SWPC live solar flux, Kp index, and geomagnetic storm scales
│   └── ai_service.py          # Gemini/OpenAI API caller + offline educational space knowledge engine
├── pages/
│   ├── dashboard.py           # Mission overview, 2D fleet ground track & quick actions
│   ├── satellite_tracker.py   # Satellite search, ephemeris table & orbital path inspector
│   ├── globe_3d.py            # Interactive 3D Earth globe with 3D orbit curves
│   ├── iss_tracker.py         # Dedicated ISS tracking, live coordinates & crew manifest
│   ├── ai_assistant.py        # AI Chat interface for orbital mechanics & space physics
│   ├── orbit_analytics.py     # Interactive Plotly charts: altitude, velocity, period, inclination
│   ├── space_debris.py        # Space debris distribution, collision risks & Kessler syndrome
│   ├── space_weather.py       # NOAA solar activity, Kp trends & LEO satellite drag impact
│   ├── pass_predictor.py      # Observer horizon pass prediction with polar sky chart
│   └── about.py               # Documentation, mathematical formulation & data attributions
└── tests/
    ├── test_orbit_math.py     # Unit tests for geodetics, Julian Date, ECEF/TEME, and pass geometry
    ├── test_tle_service.py    # Unit tests for TLE parsing, propagation & search
    ├── test_services.py       # Unit tests for ISS, weather, and AI services
    └── test_pages_smoke.py    # Smoke tests verifying imports across all modules
```

---

## 🚀 Installation & Running

### Quick start on Windows (1-Click)

1. Double-click **`RUN_COSMOBITS.bat`** in the project directory.
2. Wait for dependencies to install. CosmoBits will automatically open in your browser at `http://localhost:8501`.

---

### Manual Setup (Windows / macOS / Linux)

```bash
# 1. Create a virtual environment
python3 -m venv .venv

# 2. Activate the virtual environment
# Windows: .venv\Scripts\activate
# macOS/Linux:
source .venv/bin/activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. (Optional) Configure Google Gemini API key
cp .env.example .env
# Edit .env and paste your GEMINI_API_KEY

# 5. Launch CosmoBits
streamlit run app.py
```

Streamlit will print the local URL:
```
Local URL: http://localhost:8501
Network URL: http://192.168.x.x:8501
```
Open `http://localhost:8501` in your browser.

---

## 🧪 Running Automated Unit Tests

CosmoBits includes a unit test suite verifying orbital calculations, coordinate transformations, TLE parsing, and service fallbacks:

```bash
# Run all unit tests
python -m unittest discover -s tests -p "test_*.py" -v
```

---

## 📡 Data Sources & Technical Attribution

| Provider | Data Feed / Endpoint | Usage in CosmoBits |
|---|---|---|
| **CelesTrak (NORAD GP API)** | `https://celestrak.org/NORAD/elements/gp.php` | Two-Line Element (TLE) sets for Space Stations, Visual, Weather, GPS, Science, and Analyst debris objects. |
| **NOAA Space Weather Prediction Center (SWPC)** | `https://services.swpc.noaa.gov/products/` | Real-time Planetary K-index, 10.7cm solar radio flux, solar wind velocity, and geomagnetic storm severity scales. |
| **Where The ISS At (WTIA)** | `https://api.wheretheiss.at/v1/satellites/25544` | High-accuracy real-time ISS geodetic coordinates, orbital speed, and altitude. |
| **Open-Notify** | `http://api.open-notify.org/` | Real-time backup ISS coordinates and human spaceflight crew manifests. |
| **SGP4 / WGS-84** | Analytical Ephemeris Propagator | Validated mathematical propagation of TEME state vectors to ECEF/Geodetic coordinates. |

---

## 📤 Uploading to GitHub

To publish your project to GitHub:

```bash
# 1. Initialize git repository
git init

# 2. Add all project files
git add .

# 3. Commit files
git commit -m "Initial commit: CosmoBits Space Tracking Platform"

# 4. Link your remote GitHub repository
git remote add origin https://github.com/YOUR_USERNAME/cosmobits.git

# 5. Push to GitHub
git branch -M main
git push -u origin main
```

---

## ☁️ Deployment Instructions

### Method 1: Streamlit Community Cloud (Recommended & Free)
1. Push your repository to GitHub.
2. Visit [share.streamlit.io](https://share.streamlit.io/) and log in with GitHub.
3. Click **"New App"**.
4. Select your repository: `YOUR_USERNAME/cosmobits`, Branch: `main`, Main file path: `app.py`.
5. Under **Advanced Settings**, add any secrets (such as `GEMINI_API_KEY="your_key"`).
6. Click **Deploy!** Your platform is live worldwide in ~2 minutes.

### Method 2: Docker Container Deployment
Create a `Dockerfile` in the root directory:
```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
EXPOSE 8501
CMD ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]
```
Build and run:
```bash
docker build -t cosmobits .
docker run -p 8501:8501 -e GEMINI_API_KEY="your_key" cosmobits
```

---

## ⚖️ Engineering Disclaimer
CosmoBits is designed for civilian situational awareness, educational research, and space visualization. SGP4 propagation relies on unclassified TLE data and spherical Earth/TEME approximations; it does not replace certified mission flight-dynamics or Department of Defense operational Conjunction Data Messages (CDMs).
