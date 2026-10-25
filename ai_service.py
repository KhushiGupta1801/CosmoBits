"""Cosmo Bites — AI Space Assistant & Orbital Knowledge Engine.

Supports real-time LLM inference via Google Gemini API / OpenAI API
with an extensive built-in educational space mechanics knowledge engine
when operating offline or without an API key configured.
"""
from __future__ import annotations

import json
import os
import re
import urllib.error
import urllib.request
from typing import Any

SYSTEM_PROMPT = """You are Cosmo Bites, an expert aerospace mission control AI assistant specializing in:
- Satellite tracking, NORAD catalogs, and TLE formats
- Orbital mechanics (Kepler's laws, SGP4/SDP4, Hohmann transfers, delta-v, perturbations J2/drag)
- Space weather and its impact on satellites (solar flares, geomagnetic storms, Kp index, thermospheric expansion)
- Space debris mitigation, Kessler Syndrome, and conjunction assessment
- Space exploration missions (ISS, Artemis, Tiangong, James Webb, GPS constellations)

Provide clear, technically precise, and engaging answers. Include mathematical formulas in LaTeX when explaining orbital concepts."""


def get_configured_ai_provider() -> tuple[str | None, str | None]:
    """Check environment for configured AI API keys."""
    gemini_key = os.getenv("GEMINI_API_KEY")
    openai_key = os.getenv("OPENAI_API_KEY")
    if gemini_key:
        return "gemini", gemini_key
    if openai_key:
        return "openai", openai_key
    return None, None


def query_ai_assistant(prompt: str, conversation_history: list[dict] | None = None) -> tuple[str, str]:
    """Query AI Assistant. Returns (response_text, provider_name)."""
    provider, api_key = get_configured_ai_provider()

    if provider == "gemini" and api_key:
        try:
            return call_gemini_api(prompt, api_key, conversation_history), "Google Gemini 1.5 Flash (Online)"
        except Exception as e:
            fallback = offline_knowledge_engine(prompt)
            return f"*(Gemini API encountered an error: {e}. Switching to offline knowledge engine)*\n\n{fallback}", "Cosmo Bites Knowledge Engine (Fallback)"

    if provider == "openai" and api_key:
        try:
            return call_openai_api(prompt, api_key, conversation_history), "OpenAI GPT-4o (Online)"
        except Exception as e:
            fallback = offline_knowledge_engine(prompt)
            return f"*(OpenAI API encountered an error: {e}. Switching to offline knowledge engine)*\n\n{fallback}", "Cosmo Bites Knowledge Engine (Fallback)"

    # Educational offline fallback
    return offline_knowledge_engine(prompt), "Cosmo Bites Educational Knowledge Engine (Offline Mode)"


def call_gemini_api(prompt: str, api_key: str, history: list[dict] | None = None) -> str:
    """Call Google Gemini REST API without external SDK requirement."""
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={api_key}"
    contents = []

    # Include system instructions
    contents.append({
        "role": "user",
        "parts": [{"text": f"[System Context: {SYSTEM_PROMPT}]\n\nUser Question: {prompt}"}]
    })

    payload = json.dumps({"contents": contents}).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST"
    )

    with urllib.request.urlopen(req, timeout=12.0) as resp:
        res = json.loads(resp.read().decode("utf-8"))
        candidates = res.get("candidates", [])
        if candidates:
            parts = candidates[0].get("content", {}).get("parts", [])
            if parts:
                return parts[0].get("text", "No response generated.")
    return "No response received from Gemini API."


def call_openai_api(prompt: str, api_key: str, history: list[dict] | None = None) -> str:
    """Call OpenAI Chat Completions REST API."""
    url = "https://api.openai.com/v1/chat/completions"
    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    messages.append({"role": "user", "content": prompt})

    payload = json.dumps({
        "model": "gpt-4o-mini",
        "messages": messages,
        "temperature": 0.5,
    }).encode("utf-8")

    req = urllib.request.Request(
        url,
        data=payload,
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}",
        },
        method="POST"
    )

    with urllib.request.urlopen(req, timeout=12.0) as resp:
        res = json.loads(resp.read().decode("utf-8"))
        return res["choices"][0]["message"]["content"]


def offline_knowledge_engine(query: str) -> str:
    """Educational rule-based space mechanics knowledge engine."""
    q = query.lower()

    if any(k in q for k in ["sso", "sun-synchronous", "sun synchronous"]):
        return """### 🛰️ Sun-Synchronous Orbit (SSO)

A **Sun-Synchronous Orbit (SSO)** is a quasi-polar orbit where the satellite's orbital plane precesses at the exact same rate at which the Earth orbits the Sun (~0.9856° per day or 360° per year).

#### Key Mechanics:
1. **Constant Sun Angle**: The satellite passes over any given point on the Earth's surface at the same local solar time, providing identical lighting and shadow conditions crucial for optical imaging, weather monitoring, and environmental tracking.
2. **Nodal Regression via Earth Oblateness ($J_2$)**:
   $$\\dot{\\Omega} = -\\frac{3}{2} J_2 \\left(\\frac{R_E}{p}\\right)^2 n \\cos(i)$$
   Because we need $\\dot{\\Omega} > 0$ (eastward precession of ~0.9856°/day), $\\cos(i)$ must be negative, requiring a retrograde inclination:
   $$i \\approx 97^\\circ - 98^\\circ \\quad \\text{for LEO altitudes (500–800 km)}$$
3. **Examples**: Landsat series, Sentinel-2, NOAA-20, and WorldView imaging satellites."""

    elif any(k in q for k in ["kepler", "element", "orbital elements"]):
        return """### 📐 Classical Keplerian Orbital Elements

An orbit in 3D space is uniquely described by six classical Keplerian orbital elements:

| Element | Symbol | Definition & Physical Meaning |
|---|---|---|
| **Semi-Major Axis** | $a$ | Specifies the size of the orbit; determines the orbital period $T = 2\\pi\\sqrt{a^3/\\mu}$. |
| **Eccentricity** | $e$ | Specifies the shape of the ellipse ($e=0$: circular, $0 < e < 1$: elliptical, $e=1$: parabolic). |
| **Inclination** | $i$ | Tilt of the orbital plane relative to the Earth's equatorial plane ($0^\\circ \\le i \\le 180^\\circ$). |
| **Right Ascension of Ascending Node** | $\\Omega$ (RAAN) | Angle from the First Point of Aries (Vernal Equinox) to the point where orbit crosses equator northbound. |
| **Argument of Perigee** | $\\omega$ | Angle measured in orbital plane from the ascending node to the point of closest approach (perigee). |
| **True Anomaly** | $\\nu$ or $\\theta$ | Angle measured from perigee to the satellite's current physical position along its orbit. |"""

    elif any(k in q for k in ["tle", "norad", "two line element", "two-line"]):
        return """### 📜 Understanding TLE (Two-Line Element Sets)

A Two-Line Element (TLE) set encodes a spacecraft's state vector and drag properties formatted for the **SGP4 (Simplified General Perturbations 4)** propagator.

#### Example: ISS (ZARYA)
```
1 25544U 98067A   24143.51860046  .00014878  00000+0  26859-3 0  9997
2 25544  51.6416 112.5975 0005432  38.7495  68.2195 15.49832261454523
```

#### Line 1 Breakdown:
- **`25544`**: NORAD Catalog Number (Satellite identifier).
- **`U`**: Security Classification (`U` = Unclassified).
- **`98067A`**: International Designator (Year 1998, Launch #67, Piece A).
- **`24143.51860046`**: Epoch (Year 2024, Day 143.5186 UTC).
- **`.00014878`**: First derivative of Mean Motion divided by 2 (ballistic coefficient).
- **`26859-3`**: BSTAR drag term ($0.26859 \\times 10^{-3}$ Earth radii$^{-1}$).

#### Line 2 Breakdown:
- **`51.6416`**: Inclination ($i$) in degrees.
- **`112.5975`**: Right Ascension of the Ascending Node ($\\Omega$) in degrees.
- **`0005432`**: Eccentricity ($e = 0.0005432$, leading decimal assumed).
- **`38.7495`**: Argument of Perigee ($\\omega$) in degrees.
- **`68.2195`**: Mean Anomaly ($M$) in degrees.
- **`15.49832261`**: Mean Motion ($n$) in revolutions per day (~92.9 min/orbit).
- **`45452`**: Revolution number at epoch."""

    elif any(k in q for k in ["kessler", "debris", "collision"]):
        return """### 💥 Kessler Syndrome & Space Debris Dynamics

The **Kessler Syndrome**, proposed by NASA astrophysicist Donald J. Kessler in 1978, describes a theoretical scenario where the density of objects in Low Earth Orbit (LEO) becomes high enough that collisions produce a cascading chain reaction of catastrophic fragmentations.

#### Critical Concepts:
1. **Hypervelocity Impacts**: At orbital velocities (~7.5 km/s in LEO), mutual collision speeds can reach **10–14 km/s**. Even a 1 cm aluminum fragment carries the kinetic energy of a hand grenade!
2. **Debris Peak Altitudes**: The highest debris concentrations reside between **750 km and 1,000 km** (e.g. 2007 Fengyun-1C ASAT test and 2009 Iridium 33 / Cosmos 2251 collision).
3. **Conjunction Assessment**: Satellite operators receive **Conjunction Data Messages (CDMs)** from the 18th Space Defense Squadron whenever a Miss Distance < 1 km and Probability of Collision ($P_c$) exceeds $10^{-4}$, triggering an autonomous collision-avoidance maneuver.
4. **Remediation**:
   - **Post-Mission Disposal (PMD)**: 5-year deorbit rule (updated from the 25-year rule by FCC/NASA).
   - **Active Debris Removal (ADR)**: Robotic harpoons, nets, and magnetic docking tugs (e.g., ClearSpace-1)."""

    elif any(k in q for k in ["space weather", "solar flare", "geomagnetic", "kp"]):
        return """### ☀️ Space Weather & Satellite Impacts

Space weather originates from solar activity (solar wind, coronal mass ejections, and solar flares) interacting with the Earth's magnetosphere and upper atmosphere.

#### Major Metrics:
- **Planetary Kp-Index (0 to 9)**: Measures planetary geomagnetic disturbance over 3-hour intervals. Kp $\\ge 5$ indicates a geomagnetic storm.
- **Solar 10.7 cm Radio Flux (F10.7)**: Proxy for solar extreme ultraviolet (EUV) emissions, driving thermospheric density.

#### Operational Impacts on Satellites:
1. **Thermospheric Expansion & Aerodynamic Drag**:
   During solar storms, UV and geomagnetic heating causes the upper atmosphere to expand outwards. Satellites in LEO experience up to **300–800% higher atmospheric drag**, leading to sudden orbital decay, loss of altitude, and tracking errors.
2. **Single-Event Upsets (SEU)**:
   High-energy solar protons pierce satellite shielding, flipping memory bits in flight computers, corrupting star tracker telemetry, or causing latch-up burnout.
3. **Spacecraft Charging**:
   Plasma immersion causes differential electrical potential between shaded and sunlit spacecraft panels, resulting in dangerous electrostatic discharge (ESD)."""

    elif any(k in q for k in ["hohmann", "transfer", "delta-v", "delta v"]):
        return """### 🚀 Hohmann Transfer Orbit & $\\Delta v$

A **Hohmann Transfer** is the most fuel-efficient two-impulse orbital maneuver between two coplanar, circular orbits of radii $r_1$ and $r_2$.

#### Equations:
1. **Semi-Major Axis of Transfer Ellipse**:
   $$a_{\\text{tx}} = \\frac{r_1 + r_2}{2}$$
2. **First Burn (Injection at Perigee)**:
   $$\\Delta v_1 = \\sqrt{\\frac{\\mu}{r_1}} \\left( \\sqrt{\\frac{2 r_2}{r_1 + r_2}} - 1 \\right)$$
3. **Second Burn (Circularization at Apogee)**:
   $$\\Delta v_2 = \\sqrt{\\frac{\\mu}{r_2}} \\left( 1 - \\sqrt{\\frac{2 r_1}{r_1 + r_2}} \\right)$$
4. **Total Mission $\\Delta v$**:
   $$\\Delta v_{\\text{total}} = \\Delta v_1 + \\Delta v_2$$
5. **Transfer Time**:
   $$t_{\\text{tx}} = \\pi \\sqrt{\\frac{a_{\\text{tx}}^3}{\\mu}}$$"""

    elif any(k in q for k in ["iss", "space station"]):
        return """### 🛰️ International Space Station (ISS) Mission Profile

- **Orbital Altitude**: ~415 – 425 km (Low Earth Orbit).
- **Orbital Speed**: ~7.66 km/s (27,600 km/h or 17,150 mph).
- **Orbital Period**: ~92.8 minutes (~15.5 orbits per day).
- **Orbital Inclination**: **51.64°** (chosen so launches from both Baikonur Cosmodrome in Kazakhstan and Kennedy Space Center in Florida could reach the station).
- **Dimensions**: 109 meters end-to-end (larger than a football field), mass ~450 metric tons.
- **Microgravity Science**: Serves as a continuous human-tended laboratory for crystallization, combustion physics, fluid dynamics, and biological effects of long-duration spaceflight."""

    else:
        return f"""### 🌌 Cosmo Bites Mission Assistant

I received your inquiry regarding **"{query}"**. 

Here is what you can ask me about:
- **Orbital Mechanics**: Keplerian elements, Hohmann transfers, vis-viva equation, circular velocity, delta-v.
- **Orbital Regimes**: LEO, MEO, GEO, Sun-Synchronous (SSO), Molniya, and Lagrange points (L1–L5).
- **Space Telemetry**: Two-Line Element (TLE) format breakdown, SGP4 propagation mechanics, ephemeris data.
- **Space Hazards**: Space debris, Kessler Syndrome, conjunction assessment, and collision avoidance maneuvers.
- **Space Weather**: NOAA Kp-index, solar flares, solar wind, and atmospheric drag inflation on LEO satellites.
- **Space Missions**: ISS, Tiangong, GPS constellations, Starlink, Hubble, and deep space observatories.

> **Online AI Mode**: To enable open-ended natural conversation with Google Gemini, set your free API key in the `.env` file or sidebar: `GEMINI_API_KEY=your_key_here`."""
