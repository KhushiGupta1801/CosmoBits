"""Check a proposed latitude/longitude route against tracked space debris."""

import math
from datetime import datetime, timezone

from space_data import DEBRIS_LIMIT, fetch_debris, propagate_record


COLLISION_DISTANCE_KM = 100.0
EARTH_MEAN_RADIUS_KM = 6371.0088
COLLISION_WARNING = "CRITICAL COLLISION RISK DETECTED"


def _great_circle_distance_km(first, second):
    """Return the Haversine distance between two latitude/longitude pairs."""
    latitude_1, longitude_1 = map(math.radians, first)
    latitude_2, longitude_2 = map(math.radians, second)

    latitude_delta = latitude_2 - latitude_1
    longitude_delta = longitude_2 - longitude_1
    haversine = (
        math.sin(latitude_delta / 2) ** 2
        + math.cos(latitude_1)
        * math.cos(latitude_2)
        * math.sin(longitude_delta / 2) ** 2
    )
    haversine = min(1.0, max(0.0, haversine))
    central_angle = 2 * math.atan2(
        math.sqrt(haversine),
        math.sqrt(1 - haversine),
    )
    return EARTH_MEAN_RADIUS_KM * central_angle


def _validated_path(path):
    try:
        coordinates = tuple(path)
    except TypeError as exc:
        raise ValueError(
            "The satellite path must be an iterable of (latitude, longitude) pairs."
        ) from exc

    if not coordinates:
        raise ValueError("The satellite path must contain at least one coordinate.")

    validated = []
    for index, coordinate in enumerate(coordinates):
        try:
            latitude, longitude = coordinate
            latitude = float(latitude)
            longitude = float(longitude)
        except (TypeError, ValueError) as exc:
            raise ValueError(
                f"Path coordinate {index} must contain numeric latitude and longitude."
            ) from exc

        if not math.isfinite(latitude) or not -90 <= latitude <= 90:
            raise ValueError(f"Path coordinate {index} has an invalid latitude.")
        if not math.isfinite(longitude) or not -180 <= longitude <= 180:
            raise ValueError(f"Path coordinate {index} has an invalid longitude.")
        validated.append((latitude, longitude))

    return validated


def check_satellite_path(path):
    """Return (warning, debris name) for a route within 100 km of debris.

    Coordinates are compared by surface distance because the proposed path only
    provides latitude and longitude; altitude is not included in this check.
    Returns (None, None) when no tracked object is within the threshold.
    """
    route = _validated_path(path)
    debris_records = fetch_debris()
    if not debris_records:
        raise RuntimeError("No debris records were returned by the tracking source.")

    now = datetime.now(timezone.utc)
    for record in debris_records[:DEBRIS_LIMIT]:
        latitude, longitude, _altitude = propagate_record(record, now)
        debris_position = (latitude, longitude)
        if any(
            _great_circle_distance_km(point, debris_position)
            < COLLISION_DISTANCE_KM
            for point in route
        ):
            name = str(record.get("OBJECT_NAME", "Unknown"))
            return COLLISION_WARNING, name

    return None, None


if __name__ == "__main__":
    fake_satellite_path = [(10.0, 20.0), (10.1, 20.1)]
    result = check_satellite_path(fake_satellite_path)
    print(result)