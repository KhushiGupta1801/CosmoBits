"""Format live debris calculations for a web frontend.

Each record contains:
- name: object name from the source data
- latitude: decimal degrees, valid range -90 to 90
- longitude: decimal degrees, valid range -180 to 180
- altitude: kilometers above the Earth's surface, must be positive
"""

import json
import logging
from datetime import datetime, timezone

from space_data import fetch_debris, propagate_record


logger = logging.getLogger(__name__)
logger.addHandler(logging.NullHandler())

VALID_KEYS = {"name", "latitude", "longitude", "altitude"}


def _validate_record(record):
    """Ensure a record matches the expected schema and valid numeric ranges."""
    if not isinstance(record, dict):
        return False, "not a dictionary"

    if set(record.keys()) != VALID_KEYS:
        return False, "unexpected keys"

    name = record.get("name")
    if not isinstance(name, str) or not name.strip():
        return False, "missing name"

    try:
        latitude = float(record["latitude"])
        longitude = float(record["longitude"])
        altitude = float(record["altitude"])
    except (TypeError, ValueError):
        return False, "non-numeric value"

    if not -90.0 <= latitude <= 90.0:
        return False, "latitude out of range"
    if not -180.0 <= longitude <= 180.0:
        return False, "longitude out of range"
    if not altitude > 0:
        return False, "altitude must be positive"

    return True, None


def _collect_formatted_data():
    """Build the list of validated objects and count skipped records."""
    formatted = []
    skipped = 0
    now = datetime.now(timezone.utc)

    try:
        debris_records = fetch_debris()
    except Exception as exc:
        logger.warning("Skipped debris fetch: %s", exc)
        return formatted, skipped

    for record in debris_records:
        name = str(record.get("OBJECT_NAME", "Unknown"))

        try:
            latitude, longitude, altitude = propagate_record(record, now)
            candidate = {
                "name": name,
                "latitude": round(float(latitude), 4),
                "longitude": round(float(longitude), 4),
                "altitude": round(float(altitude), 2),
            }
        except (TypeError, ValueError, KeyError, OverflowError) as exc:
            logger.warning("Skipped object %s: %s", name, exc)
            skipped += 1
            continue

        is_valid, reason = _validate_record(candidate)
        if not is_valid:
            logger.warning("Skipped object %s: %s", name, reason)
            skipped += 1
            continue

        formatted.append(candidate)

    return formatted, skipped


def get_formatted_data():
    """Return the cleaned, validated debris objects for frontend display."""
    formatted, _ = _collect_formatted_data()
    return formatted


def get_json():
    """Return the formatted debris list as a pretty-printed JSON string."""
    return json.dumps(get_formatted_data(), indent=2)


if __name__ == "__main__":
    logging.basicConfig(level=logging.WARNING, format="%(levelname)s: %(message)s")
    data, skipped = _collect_formatted_data()
    print(json.dumps(data, indent=2))
    print(f"Formatted {len(data)} objects, skipped {skipped}")
