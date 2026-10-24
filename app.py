"""Flask API for serving live debris data to a web frontend."""

import time
from datetime import datetime, timezone

from flask import Flask, jsonify
from flask_cors import CORS

from data_formatter import get_formatted_data


app = Flask(__name__)
CORS(app, resources={r"/api/*": {"origins": "*"}})

CACHE_TTL_SECONDS = 30
CACHE = {
    "objects": [],
    "updated": None,
    "expires_at": 0.0,
}


def _refresh_cache(force=False):
    """Load fresh data when the cache is expired; otherwise return cached data."""
    now = time.time()

    if not force and CACHE["expires_at"] > now:
        return CACHE["objects"]

    try:
        objects = get_formatted_data() or []
        CACHE["objects"] = objects
        CACHE["updated"] = datetime.now(timezone.utc).isoformat()
        CACHE["expires_at"] = now + CACHE_TTL_SECONDS
        return objects
    except Exception:
        # If the live feed fails, fall back to the last known good data.
        if CACHE["objects"]:
            return CACHE["objects"]
        raise


@app.get("/api/debris")
def get_debris():
    """Return the cached or freshly fetched debris objects as JSON."""
    try:
        objects = _refresh_cache()
    except Exception:
        if CACHE["objects"]:
            return jsonify(
                {
                    "count": len(CACHE["objects"]),
                    "updated": CACHE["updated"],
                    "objects": CACHE["objects"],
                }
            )
        return jsonify({"error": "Debris feed unavailable."}), 503

    payload = {
        "count": len(objects),
        "updated": CACHE["updated"],
        "objects": objects,
    }
    return jsonify(payload)


@app.get("/api/health")
def health():
    """Return the service status for health checks."""
    return jsonify({"status": "ok"})


if __name__ == "__main__":
    app.run(debug=True, port=5000)
