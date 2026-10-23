import base64
import hashlib
import hmac
import io
import json
import logging
import os
import secrets
import time
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from urllib.parse import urlencode

import pytest
import redis

from config import AutoBlockerConfig
from app import create_app


def make_client(tmp_path, **overrides):
    config = AutoBlockerConfig()
    config.IP_BLOCKLIST_PATH = tmp_path / "blocked-ips.json"
    config.DOMAIN_BLOCKLIST_PATH = tmp_path / "blocked-domains.json"
    config.BLOCKED_EVENTS_PATH = tmp_path / "blocked-events.jsonl"
    config.FORM_TOKEN_SECRET = "test-secret"
    config.MIN_FORM_FILL_SECONDS = 0
    config.ADMIN_TOKEN = "admin-test-token"
    config.DEMO_LOGIN_PASSWORD = "correct-test-password"
    config.IP_BLOCKLIST_PATH.write_text("[]", encoding="utf-8")
    config.DOMAIN_BLOCKLIST_PATH.write_text('["blocked.example"]', encoding="utf-8")
    for name, value in overrides.items():
        setattr(config, name, value)
    app = create_app(config)
    app.config.update(TESTING=True)
    return app.test_client(), config


def form_token(client):
    return client.get("/api/form-token").get_json()["token"]


def test_sensitive_route_rate_limit_returns_429(tmp_path):
    client, _ = make_client(tmp_path, RATE_LIMIT_PER_MINUTE=2, AUTH_RATE_LIMIT_PER_MINUTE=20)
    for _ in range(2):
        client.post("/api/contact", data={"form_token": form_token(client)})
    response = client.post("/api/contact", data={"form_token": form_token(client)})
    assert response.status_code == 429
    assert response.get_json()["code"] == "RATE_LIMIT"
    assert response.get_json()["retryAfter"] > 0


def test_rate_limit_runs_before_blocklist_check(tmp_path):
    client, config = make_client(tmp_path, RATE_LIMIT_PER_MINUTE=1)
    config.IP_BLOCKLIST_PATH.write_text('["127.0.0.1"]', encoding="utf-8")
    first = client.post("/api/contact", data={"form_token": form_token(client)})
    second = client.post("/api/contact", data={"form_token": form_token(client)})
    assert first.get_json()["code"] == "IP_BLOCKLIST"
    assert second.status_code == 429
    assert second.get_json()["code"] == "RATE_LIMIT"


def test_form_token_endpoint_has_a_configurable_ip_limit(tmp_path):
    client, _ = make_client(tmp_path, FORM_TOKEN_RATE_LIMIT_PER_MINUTE=2)
    assert client.get("/api/form-token").status_code == 200
    assert client.get("/api/form-token").status_code == 200
    blocked = client.get("/api/form-token")
    assert blocked.status_code == 429
    assert blocked.get_json()["code"] == "RATE_LIMIT"


@pytest.mark.parametrize(
    ("setting", "value"),
    [
        ("FORM_TOKEN_SECRET", ""),
        ("FORM_TOKEN_SECRET", "change-me"),
        ("ADMIN_TOKEN", ""),
        ("ADMIN_TOKEN", "placeholder"),
        ("REDIS_URL", ""),
        ("REDIS_URL", "changeme"),
    ],
)
def test_production_startup_requires_non_placeholder_secrets(tmp_path, setting, value):
    _, config = make_client(tmp_path)
    config.PRODUCTION = True
    config.FORM_TOKEN_SECRET = "a-real-form-secret"
    config.ADMIN_TOKEN = "a-real-admin-secret"
    config.REDIS_URL = "redis://redis.internal:6379/0"
    setattr(config, setting, value)
    with pytest.raises(ValueError, match="Production requires"):
        create_app(config)


def test_development_mode_generates_secret_and_uses_open_fallback(tmp_path):
    config = AutoBlockerConfig()
    config.PRODUCTION = False
    config.REDIS_URL = ""
    config.REDIS_FAILURE_MODE = "open"
    config.IP_BLOCKLIST_PATH = tmp_path / "blocked-ips.json"
    config.DOMAIN_BLOCKLIST_PATH = tmp_path / "blocked-domains.json"
    config.BLOCKED_EVENTS_PATH = tmp_path / "blocked-events.jsonl"
    assert config.FORM_TOKEN_SECRET
    client = create_app(config).test_client()
    assert config.FORM_TOKEN_SECRET
    assert client.get("/api/form-token").status_code == 200


def test_signup_has_stricter_five_per_minute_limit(tmp_path):
    client, _ = make_client(tmp_path, MIN_FORM_FILL_SECONDS=0)
    for _ in range(5):
        response = client.post("/api/signup", data={"form_token": form_token(client)})
        assert response.status_code == 201
    response = client.post("/api/signup", data={"form_token": form_token(client)})
    assert response.status_code == 429
    assert response.get_json()["code"] == "RATE_LIMIT"


def test_five_wrong_logins_trigger_a_short_pair_delay(tmp_path):
    client, _ = make_client(tmp_path)
    responses = [
        client.post(
            "/api/login",
            json={
                "username": "alice",
                "password": "wrong",
                "form_token": form_token(client),
            },
        )
        for _ in range(5)
    ]
    assert [response.status_code for response in responses] == [401, 401, 401, 401, 403]
    assert responses[-1].get_json()["code"] == "LOGIN_DELAY"
    assert responses[-1].get_json()["retryAfter"] == 1


def test_failed_logins_from_different_ips_do_not_lock_the_account(tmp_path):
    client, _ = make_client(tmp_path)
    responses = [
        client.post(
            "/api/login",
            json={"username": "alice", "password": "wrong", "form_token": form_token(client)},
            environ_base={"REMOTE_ADDR": f"192.0.2.{index}"},
        )
        for index in range(1, 6)
    ]
    assert [response.status_code for response in responses] == [401] * 5
    repeat = client.post(
        "/api/login",
        json={"username": "alice", "password": "wrong", "form_token": form_token(client)},
        environ_base={"REMOTE_ADDR": "192.0.2.1"},
    )
    assert repeat.status_code == 401


def test_trusted_proxy_uses_each_forwarded_client_for_limits(tmp_path):
    client, _ = make_client(
        tmp_path,
        RATE_LIMIT_PER_MINUTE=2,
        TRUSTED_PROXIES=("10.0.0.0/8",),
    )
    responses = [
        client.post(
            "/api/contact",
            data={"form_token": form_token(client)},
            environ_base={"REMOTE_ADDR": "10.0.0.8"},
            headers={"X-Forwarded-For": f"198.51.100.{index}"},
        )
        for index in range(1, 6)
    ]
    assert [response.status_code for response in responses] == [202] * 5


def test_untrusted_forwarded_header_cannot_bypass_ip_limit(tmp_path):
    client, _ = make_client(tmp_path, RATE_LIMIT_PER_MINUTE=1)
    first = client.post(
        "/api/contact",
        data={"form_token": form_token(client)},
        environ_base={"REMOTE_ADDR": "198.51.100.20"},
        headers={"X-Forwarded-For": "203.0.113.1"},
    )
    second = client.post(
        "/api/contact",
        data={"form_token": form_token(client)},
        environ_base={"REMOTE_ADDR": "198.51.100.20"},
        headers={"X-Forwarded-For": "203.0.113.2"},
    )
    assert first.status_code == 202
    assert second.status_code == 429


def test_rolling_rate_window_blocks_boundary_bursts(tmp_path):
    client, _ = make_client(tmp_path)
    blocker = client.application.extensions["auto_blocker"]
    key = blocker._state_key("rate-test", "client")
    assert blocker._consume_rate_slot(key, 2, 100, 60, 120) is None
    assert blocker._consume_rate_slot(key, 2, 159, 60, 120) is None
    assert blocker._consume_rate_slot(key, 2, 159.5, 60, 120) == 1
    assert blocker._consume_rate_slot(key, 2, 160, 60, 120) is None


def test_redis_open_mode_warns_once_falls_back_and_logs_recovery(tmp_path, caplog):
    client, _ = make_client(
        tmp_path,
        RATE_LIMIT_PER_MINUTE=1,
        REDIS_FAILURE_MODE="open",
    )
    blocker = client.application.extensions["auto_blocker"]
    tokens = [form_token(client) for _ in range(3)]

    class RedisFlaky:
        unavailable = True

        def eval(self, *_args):
            if self.unavailable:
                raise redis.exceptions.ConnectionError("Redis is unavailable")
            return [1, 0]

        def set(self, *_args, **_kwargs):
            return True

    fake_redis = RedisFlaky()
    blocker.redis = fake_redis
    with caplog.at_level(logging.WARNING):
        first = client.post("/api/contact", data={"form_token": tokens[0]})
        second = client.post("/api/contact", data={"form_token": tokens[1]})
        assert first.status_code == 202
        assert second.status_code == 429
        assert blocker._redis_degraded is True

        fake_redis.unavailable = False
        blocker._redis_retry_after = 0
        recovered = client.post("/api/contact", data={"form_token": tokens[2]})

    assert recovered.status_code == 202
    messages = [record.getMessage() for record in caplog.records]
    assert sum("Redis outage" in message for message in messages) == 1
    assert sum("Redis recovered" in message for message in messages) == 1


def test_redis_closed_mode_returns_structured_503(tmp_path):
    client, _ = make_client(tmp_path, REDIS_FAILURE_MODE="closed")
    blocker = client.application.extensions["auto_blocker"]

    class RedisFlaky:
        unavailable = False

        def eval(self, *_args):
            if self.unavailable:
                raise redis.exceptions.ConnectionError("Redis is unavailable")
            return [1, 0]

        def set(self, *_args, **_kwargs):
            return True

    fake_redis = RedisFlaky()
    blocker.redis = fake_redis
    token = form_token(client)
    fake_redis.unavailable = True
    response = client.post(
        "/api/contact",
        data={"form_token": token},
    )
    assert response.status_code == 503
    assert response.get_json()["blocked"] is True
    assert response.get_json()["code"] == "REDIS_UNAVAILABLE"


def test_executable_upload_is_rejected(tmp_path):
    client, _ = make_client(tmp_path)
    response = client.post(
        "/api/upload",
        data={
            "form_token": form_token(client),
            "website": "",
            "file": (io.BytesIO(b"MZ fake executable"), "payload.exe", "application/octet-stream"),
        },
        content_type="multipart/form-data",
    )
    assert response.status_code == 403
    assert response.get_json()["code"] == "FILE_TYPE"


def test_blocked_domain_link_is_rejected(tmp_path):
    client, _ = make_client(tmp_path)
    response = client.post(
        "/api/contact",
        data={"form_token": form_token(client), "message": "Visit https://sub.blocked.example/path"},
    )
    assert response.status_code == 403
    assert response.get_json()["code"] == "LINK_BLOCKLIST"


def test_honeypot_submission_is_rejected(tmp_path):
    client, _ = make_client(tmp_path)
    response = client.post(
        "/api/contact",
        data={"form_token": form_token(client), "website": "bot-filled"},
    )
    assert response.status_code == 403
    assert response.get_json()["code"] == "HONEYPOT"


def test_form_token_enforces_minimum_fill_time(tmp_path):
    client, _ = make_client(tmp_path, MIN_FORM_FILL_SECONDS=2)
    response = client.post(
        "/api/contact",
        data={"form_token": form_token(client), "message": "Hello"},
    )
    assert response.status_code == 403
    assert response.get_json()["code"] == "FORM_TOO_FAST"


def test_form_token_is_one_time_across_repeated_submissions(tmp_path):
    client, _ = make_client(tmp_path)
    token = form_token(client)
    first = client.post("/api/contact", data={"form_token": token})
    replay = client.post("/api/contact", data={"form_token": token})
    assert first.status_code == 202
    assert replay.status_code == 403
    assert replay.get_json()["code"] == "FORM_TOO_FAST"


def test_upload_checks_file_signature_not_only_extension(tmp_path):
    client, _ = make_client(tmp_path)
    response = client.post(
        "/api/upload",
        data={
            "form_token": form_token(client),
            "file": (io.BytesIO(b"MZ not a PNG"), "image.png", "image/png"),
        },
        content_type="multipart/form-data",
    )
    assert response.status_code == 403
    assert response.get_json()["code"] == "FILE_CONTENT"


def test_trusted_country_header_blocklist(tmp_path):
    client, config = make_client(
        tmp_path,
        COUNTRY_CODE_HEADER="X-Trusted-Country",
        COUNTRY_BLOCKED_CODES=frozenset({"ZZ"}),
    )
    response = client.post(
        "/api/contact",
        data={"form_token": form_token(client)},
        headers={"X-Trusted-Country": "ZZ"},
    )
    assert response.status_code == 403
    assert response.get_json()["code"] == "COUNTRY_BLOCKLIST"


def test_block_events_are_logged_and_admin_can_unblock_ip(tmp_path):
    client, config = make_client(tmp_path)
    config.IP_BLOCKLIST_PATH.write_text('["192.0.2.4"]', encoding="utf-8")
    blocked = client.post(
        "/api/contact",
        data={"form_token": form_token(client)},
        environ_base={"REMOTE_ADDR": "192.0.2.4"},
    )
    assert blocked.status_code == 403
    client.application.extensions["auto_blocker"].flush_logs()
    events = [json.loads(line) for line in config.BLOCKED_EVENTS_PATH.read_text().splitlines()]
    assert events[-1]["rule"] == "IP_BLOCKLIST"
    unauthorized = client.get("/admin/events")
    assert unauthorized.status_code == 401
    unblocked = client.post(
        "/admin/unblock",
        json={"ip": "192.0.2.4"},
        headers={"X-Admin-Token": "admin-test-token"},
    )
    assert unblocked.get_json()["removed"] is True


def test_blocked_event_log_rotates(tmp_path):
    client, config = make_client(
        tmp_path,
        BLOCKED_LOG_MAX_BYTES=180,
        BLOCKED_LOG_BACKUP_COUNT=1,
    )
    config.IP_BLOCKLIST_PATH.write_text('["192.0.2.9"]', encoding="utf-8")
    for _ in range(6):
        client.post(
            "/api/contact",
            data={"form_token": form_token(client)},
            environ_base={"REMOTE_ADDR": "192.0.2.9"},
        )
    client.application.extensions["auto_blocker"].flush_logs()
    rotated = config.BLOCKED_EVENTS_PATH.with_name(config.BLOCKED_EVENTS_PATH.name + ".1")
    assert config.BLOCKED_EVENTS_PATH.exists()
    assert rotated.exists()


@pytest.mark.skipif(os.getenv("RUN_LOAD_TEST") != "1", reason="set RUN_LOAD_TEST=1 to run the HTTP load test")
def test_gunicorn_http_load_target():
    url = AutoBlockerConfig.LOAD_TEST_URL
    form_secret = os.getenv("AUTO_BLOCKER_FORM_SECRET")
    password = os.getenv("AUTO_BLOCKER_DEMO_PASSWORD")
    assert form_secret and password, (
        "Set AUTO_BLOCKER_FORM_SECRET and AUTO_BLOCKER_DEMO_PASSWORD to the same "
        "values used by the running server."
    )

    def request_once(index):
        payload = json.dumps({
            "issued": time.time() - AutoBlockerConfig.MIN_FORM_FILL_SECONDS - 1,
            "nonce": secrets.token_urlsafe(16),
        }, separators=(",", ":")).encode("utf-8")
        encoded = base64.urlsafe_b64encode(payload).decode("ascii").rstrip("=")
        signature = hmac.new(form_secret.encode("utf-8"), encoded.encode("ascii"), hashlib.sha256).hexdigest()
        form = urlencode({
            "username": f"load-user-{index}",
            "password": password,
            "form_token": f"{encoded}.{signature}",
        }).encode("ascii")
        request = urllib.request.Request(
            url,
            data=form,
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            method="POST",
        )
        try:
            with urllib.request.urlopen(request, timeout=10) as response:
                if response.status != 200:
                    raise AssertionError(f"Unexpected HTTP {response.status}")
                return response.status, None
        except urllib.error.HTTPError as error:
            body = json.loads(error.read().decode("utf-8"))
            if error.code == 429 and body.get("code") == "RATE_LIMIT":
                return error.code, body["code"]
            raise AssertionError(f"Unexpected HTTP {error.code}: {body}") from error

    started = time.perf_counter()
    with ThreadPoolExecutor(max_workers=AutoBlockerConfig.LOAD_TEST_WORKERS) as pool:
        results = list(pool.map(request_once, range(AutoBlockerConfig.LOAD_TEST_REQUESTS)))
    elapsed = time.perf_counter() - started
    achieved_rps = AutoBlockerConfig.LOAD_TEST_REQUESTS / elapsed
    successes = sum(status == 200 for status, _ in results)
    rate_limited = sum(status == 429 for status, _ in results)
    print(
        f"Load test: {achieved_rps:.1f} requests/second; "
        f"200s={successes}, 429s={rate_limited}; "
        f"target {AutoBlockerConfig.LOAD_TEST_TARGET_RPS}."
    )
    assert successes > 0
    assert rate_limited > 0, "Expected rate limiting after exceeding the configured limit."
    assert achieved_rps >= AutoBlockerConfig.LOAD_TEST_TARGET_RPS, (
        f"Achieved {achieved_rps:.1f} RPS; target is "
        f"{AutoBlockerConfig.LOAD_TEST_TARGET_RPS} RPS"
    )