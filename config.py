"""Single place to configure Auto Blocker rules and storage paths."""

import os
import secrets
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent


class AutoBlockerConfig:
    ENV = os.getenv("ENV", "development").strip().lower()
    PRODUCTION = ENV == "production"
    RATE_LIMIT_PER_MINUTE = 60
    RATE_LIMIT_WINDOW_SECONDS = 60
    RATE_LIMIT_KEY_TTL_SECONDS = 120
    AUTH_RATE_LIMIT_PER_MINUTE = 5
    FORM_TOKEN_RATE_LIMIT_PER_MINUTE = 30
    LOGIN_FAILURE_LIMIT = 5
    LOGIN_FAILURE_WINDOW_SECONDS = 15 * 60
    LOGIN_DELAY_BASE_SECONDS = 1
    LOGIN_DELAY_MAX_SECONDS = 30
    LOGIN_STATE_TTL_SECONDS = 15 * 60
    MEMORY_STATE_CLEANUP_INTERVAL_SECONDS = 30
    MEMORY_STATE_MAX_ENTRIES = 100000
    REDIS_URL = os.getenv("REDIS_URL", "")
    REDIS_SOCKET_TIMEOUT_SECONDS = 0.5
    REDIS_RETRY_SECONDS = 5
    REDIS_FAILURE_MODE = os.getenv("REDIS_FAILURE_MODE", "open").strip().lower()
    REDIS_KEY_PREFIX = "auto-blocker"
    TRUSTED_PROXIES = tuple(
        proxy.strip()
        for proxy in os.getenv("AUTO_BLOCKER_TRUSTED_PROXIES", "").split(",")
        if proxy.strip()
    )
    MIN_FORM_FILL_SECONDS = 2
    FORM_TOKEN_MAX_AGE_SECONDS = 30 * 60
    MAX_UPLOAD_BYTES = 5 * 1024 * 1024
    HONEYPOT_FIELD = "website"
    FORM_TOKEN_FIELD = "form_token"
    FORM_STARTED_FIELD = "form_started_at"
    SENSITIVE_ROUTES = frozenset({
        "/api/login",
        "/api/signup",
        "/api/contact",
        "/api/comments",
        "/api/upload",
    })
    AUTH_ROUTES = frozenset({"/api/login", "/api/signup"})
    LOGIN_ROUTES = frozenset({"/api/login"})
    FORM_ROUTES = frozenset({"/api/login", "/api/signup", "/api/contact", "/api/comments", "/api/upload"})
    UPLOAD_ROUTES = frozenset({"/api/upload"})
    IP_BLOCKLIST_PATH = Path(os.getenv("AUTO_BLOCKER_IP_BLOCKLIST", BASE_DIR / "blocked-ips.json"))
    DOMAIN_BLOCKLIST_PATH = Path(os.getenv("AUTO_BLOCKER_DOMAIN_BLOCKLIST", BASE_DIR / "blocked-domains.json"))
    COUNTRY_BLOCKED_CODES = frozenset(
        code.strip().upper()
        for code in os.getenv("AUTO_BLOCKER_BLOCKED_COUNTRIES", "").split(",")
        if code.strip()
    )
    BLOCKED_EVENTS_PATH = Path(os.getenv("AUTO_BLOCKER_LOG", BASE_DIR / "blocked-events.jsonl"))
    BLOCKED_LOG_MAX_BYTES = 10 * 1024 * 1024
    BLOCKED_LOG_BACKUP_COUNT = 5
    BLOCKED_LOG_QUEUE_SIZE = 10000
    COUNTRY_CODE_HEADER = os.getenv("AUTO_BLOCKER_COUNTRY_HEADER", "")
    FORM_TOKEN_SECRET = os.getenv(
        "AUTO_BLOCKER_FORM_SECRET",
        "" if PRODUCTION else secrets.token_urlsafe(32),
    )
    ADMIN_TOKEN = os.getenv("AUTO_BLOCKER_ADMIN_TOKEN", "")
    DEMO_LOGIN_PASSWORD = os.getenv("AUTO_BLOCKER_DEMO_PASSWORD", "")
    LOAD_TEST_TARGET_RPS = 100
    LOAD_TEST_REQUESTS = 1000
    LOAD_TEST_WORKERS = 50
    LOAD_TEST_URL = os.getenv("AUTO_BLOCKER_LOAD_TEST_URL", "http://127.0.0.1:8000/api/login")

    def validate(self):
        if self.REDIS_FAILURE_MODE not in {"open", "closed"}:
            raise ValueError("REDIS_FAILURE_MODE must be 'open' or 'closed'.")
        if not self.PRODUCTION:
            return

        required = {
            "AUTO_BLOCKER_FORM_SECRET": self.FORM_TOKEN_SECRET,
            "AUTO_BLOCKER_ADMIN_TOKEN": self.ADMIN_TOKEN,
            "REDIS_URL": self.REDIS_URL,
        }
        placeholders = {"change-me", "changeme", "placeholder", "development-only-change-me"}
        missing = [
            name for name, value in required.items()
            if not value or value.strip().lower() in placeholders
        ]
        if missing:
            raise ValueError(
                "Production requires non-placeholder settings: " + ", ".join(missing)
            )