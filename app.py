"""Small Flask integration example for the reusable AutoBlocker middleware."""

import hmac
import json
import os
from pathlib import Path

from flask import Flask, jsonify, render_template, request
from werkzeug.exceptions import RequestEntityTooLarge

from auto_blocker import AutoBlocker, RedisUnavailableError
from config import AutoBlockerConfig


def create_app(blocker_config=None):
    app = Flask(__name__)
    config = blocker_config or AutoBlockerConfig()
    app.config["MAX_CONTENT_LENGTH"] = config.MAX_UPLOAD_BYTES + 64 * 1024
    blocker = AutoBlocker(app, config)

    @app.errorhandler(RedisUnavailableError)
    def redis_unavailable(_error):
        return blocker.redis_unavailable_response()

    @app.errorhandler(RequestEntityTooLarge)
    def upload_too_large(_error):
        return blocker.deny("FILE_TOO_LARGE", "The maximum upload size is 5 MB.")

    @app.get("/")
    def home():
        return render_template("index.html")

    @app.get("/api/form-token")
    def form_token():
        retry_after = blocker.check_form_token_rate_limit()
        if retry_after:
            return blocker.deny(
                "RATE_LIMIT",
                "Too many form-token requests. Please try again later.",
                status=429,
                retry_after=retry_after,
            )
        return jsonify({"token": blocker.issue_form_token()})

    @app.post("/api/login")
    def login():
        payload = request.get_json(silent=True) or request.form
        username = str(payload.get("username", ""))
        password = str(payload.get("password", ""))
        valid_password = config.DEMO_LOGIN_PASSWORD
        if valid_password and hmac.compare_digest(password, valid_password):
            blocker.record_successful_login(username)
            return jsonify({"ok": True, "message": "Signed in."})
        retry_after = blocker.record_failed_login(username)
        if retry_after:
            return blocker.deny(
                "LOGIN_DELAY",
                "Please wait briefly before trying that account from this IP again.",
                status=403,
                retry_after=retry_after,
            )
        return jsonify({"ok": False, "message": "Invalid username or password."}), 401

    @app.post("/api/signup")
    def signup():
        return jsonify({"ok": True, "message": "Signup request accepted."}), 201

    @app.post("/api/contact")
    def contact():
        return jsonify({"ok": True, "message": "Contact request accepted."}), 202

    @app.post("/api/comments")
    def comments():
        return jsonify({"ok": True, "message": "Comment accepted."}), 201

    @app.post("/api/upload")
    def upload():
        return jsonify({"ok": True, "message": "Upload accepted."}), 201

    def require_admin():
        expected = config.ADMIN_TOKEN
        supplied = request.headers.get("X-Admin-Token", "")
        authorization = request.headers.get("Authorization", "")
        if authorization.lower().startswith("bearer "):
            supplied = authorization[7:].strip()
        if not expected or not hmac.compare_digest(supplied, expected):
            return jsonify({"error": "Admin authentication required."}), 401
        return None

    @app.get("/admin/events")
    def blocked_events():
        denied = require_admin()
        if denied:
            return denied
        blocker.flush_logs()
        path = Path(config.BLOCKED_EVENTS_PATH)
        try:
            with path.open(encoding="utf-8") as event_file:
                events = [json.loads(line) for line in event_file if line.strip()]
        except (OSError, json.JSONDecodeError):
            events = []
        return jsonify({"events": events[-200:], "droppedLogEvents": blocker.dropped_log_events})

    @app.post("/admin/unblock")
    def unblock_ip():
        denied = require_admin()
        if denied:
            return denied
        payload = request.get_json(silent=True) or {}
        ip = str(payload.get("ip", ""))
        try:
            import ipaddress
            ipaddress.ip_address(ip)
        except ValueError:
            return jsonify({"error": "A valid IP address is required."}), 400
        removed = blocker.unblock_ip(ip)
        return jsonify({"ip": ip, "removed": removed})

    return app


app = create_app()


if __name__ == "__main__":
    if not app.extensions["auto_blocker"].config.ADMIN_TOKEN:
        print("Warning: set AUTO_BLOCKER_ADMIN_TOKEN before exposing the admin endpoints.")
    app.run(host=os.getenv("HOST", "127.0.0.1"), port=int(os.getenv("PORT", "5000")))