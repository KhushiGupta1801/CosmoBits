"""Print current geodetic positions for the first 20 debris objects on CelesTrak."""

import math
import sys
from datetime import datetime, timezone

import requests
from sgp4.api import Satrec, jday
from sgp4.propagation import gstime
from sgp4.omm import initialize


CELESTRAK_URL = "https://celestrak.org/NORAD/elements/gp.php"
DEBRIS_LIMIT = 20
REQUEST_TIMEOUT_SECONDS = 30

# WGS-84 ellipsoid constants, in kilometers.
EARTH_EQUATORIAL_RADIUS_KM = 6378.137
EARTH_FLATTENING = 1.0 / 298.257223563
EARTH_ECCENTRICITY_SQUARED = EARTH_FLATTENING * (
    2.0 - EARTH_FLATTENING
)


def fetch_debris():
    """Fetch GP/OMM records whose CelesTrak object names contain 'DEB'."""
    response = requests.get(
        CELESTRAK_URL,
        params={"NAME": "DEB", "FORMAT": "JSON"},
        timeout=REQUEST_TIMEOUT_SECONDS,
    )
    response.raise_for_status()

    try:
        records = response.json()
    except ValueError as exc:
        raise RuntimeError("CelesTrak returned a non-JSON response.") from exc

    if not isinstance(records, list):
        raise RuntimeError("CelesTrak returned an unexpected data format.")

    return [
        record
        for record in records
        if isinstance(record, dict)
        and "DEB" in str(record.get("OBJECT_NAME", "")).upper()
    ]


def geodetic_coordinates(position_teme_km, julian_date):
    """Convert a TEME position in km to WGS-84 latitude, longitude, altitude."""
    x_teme, y_teme, z_teme = position_teme_km

    # Rotate TEME into Earth-fixed coordinates using Greenwich mean sidereal time.
    theta = gstime(julian_date)
    cos_theta = math.cos(theta)
    sin_theta = math.sin(theta)
    x = cos_theta * x_teme + sin_theta * y_teme
    y = -sin_theta * x_teme + cos_theta * y_teme
    z = z_teme

    longitude = math.atan2(y, x)
    p = math.hypot(x, y)
    latitude = math.atan2(z, p * (1.0 - EARTH_ECCENTRICITY_SQUARED))

    # Iterate latitude to account for the Earth's oblate shape.
    for _ in range(10):
        sin_latitude = math.sin(latitude)
        prime_vertical_radius = EARTH_EQUATORIAL_RADIUS_KM / math.sqrt(
            1.0 - EARTH_ECCENTRICITY_SQUARED * sin_latitude**2
        )
        latitude = math.atan2(
            z + EARTH_ECCENTRICITY_SQUARED
            * prime_vertical_radius
            * sin_latitude,
            p,
        )

    sin_latitude = math.sin(latitude)
    prime_vertical_radius = EARTH_EQUATORIAL_RADIUS_KM / math.sqrt(
        1.0 - EARTH_ECCENTRICITY_SQUARED * sin_latitude**2
    )
    if abs(math.cos(latitude)) > 1e-10:
        altitude = p / math.cos(latitude) - prime_vertical_radius
    else:
        altitude = (
            z / math.sin(latitude)
            - prime_vertical_radius * (1.0 - EARTH_ECCENTRICITY_SQUARED)
        )

    return math.degrees(latitude), math.degrees(longitude), altitude


def propagate_record(record, now):
    """Return one object's current latitude, longitude, and altitude."""
    satellite = Satrec()
    initialize(satellite, record)

    seconds = now.second + now.microsecond / 1_000_000.0
    jd, fraction = jday(
        now.year,
        now.month,
        now.day,
        now.hour,
        now.minute,
        seconds,
    )
    error, position, _velocity = satellite.sgp4(jd, fraction)
    if error:
        raise ValueError(f"SGP4 propagation failed with error code {error}.")

    return geodetic_coordinates(position, jd + fraction)


def main():
    try:
        debris = fetch_debris()
    except (requests.RequestException, RuntimeError) as exc:
        print(f"Could not fetch debris data: {exc}", file=sys.stderr)
        return 1

    if not debris:
        print("CelesTrak returned no debris records.", file=sys.stderr)
        return 1

    now = datetime.now(timezone.utc)
    print(f"Debris positions at {now:%Y-%m-%d %H:%M:%S UTC}")
    print("-" * 91)
    print(f"{'OBJECT NAME':<32} {'NORAD ID':>9} {'LATITUDE':>12} "
          f"{'LONGITUDE':>13} {'ALTITUDE (km)':>16}")
    print("-" * 91)

    displayed = 0
    for record in debris:
        if displayed >= DEBRIS_LIMIT:
            break

        name = str(record.get("OBJECT_NAME", "Unknown"))
        catalog_id = record.get("NORAD_CAT_ID", "Unknown")
        try:
            latitude, longitude, altitude = propagate_record(record, now)
        except (KeyError, TypeError, ValueError, OverflowError) as exc:
            print(
                f"Skipping {name} (NORAD {catalog_id}): {exc}",
                file=sys.stderr,
            )
            continue

        print(
            f"{name[:32]:<32} {str(catalog_id):>9} "
            f"{latitude:>11.4f}° {longitude:>12.4f}° {altitude:>14.2f}"
        )
        displayed += 1

    if displayed == 0:
        print("No debris records could be propagated.", file=sys.stderr)
        return 1

    print("-" * 91)
    print(f"Displayed {displayed} of the first {DEBRIS_LIMIT} debris objects.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())