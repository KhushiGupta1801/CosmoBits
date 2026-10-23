# Auto Blocker

A small Flask reference implementation with server-side protection for login,
signup, contact, comments, and uploads. The existing space-tracking scripts are
independent of this web demo.

## Run

Use Python 3.10 or newer. Install and start the app from the repository root:

```sh
python -m pip install -r requirements.txt
export AUTO_BLOCKER_ADMIN_TOKEN='use-a-long-random-secret'
export AUTO_BLOCKER_FORM_SECRET='use-a-different-long-random-secret'
python app.py
```

Open `http://127.0.0.1:5000`. The demo login only accepts the password configured
in `AUTO_BLOCKER_DEMO_PASSWORD`; when it is unset, every password is rejected
and the lockout example remains testable. Replace the demo handler with your
real authentication and persistence logic before production use.

## Configuration

Edit `config.py` to change the default limits, route sets, form fields, and
storage locations. Defaults are 60 sensitive requests per IP per minute, 5
login/signup requests per minute, a 2-minute failed-login tracking window, and
an escalating 1-to-30-second delay for repeated failures from the same IP and
account pair. A 2-second minimum form-fill time and a 5 MB upload limit also
apply. Rate-limit, login, and form-token Redis keys have expirations. When Redis
is unset, the development fallback uses expiring, capped per-process state.
Form tokens are HMAC-signed, expire after 30 minutes, and can only be used once.
Set `AUTO_BLOCKER_FORM_SECRET` to a unique secret in each production environment.

`blocked-domains.json` lists blocked hostnames; matching includes subdomains.
`blocked-ips.json` accepts IP addresses and CIDR ranges. Set country codes in
`config.py` (`COUNTRY_BLOCKED_CODES`) or the comma-separated
`AUTO_BLOCKER_BLOCKED_COUNTRIES` environment variable. Country checks are disabled unless
`AUTO_BLOCKER_COUNTRY_HEADER` names a header supplied by a trusted proxy or
geolocation service. Configure the proxy to overwrite that header; never trust a
country header directly from public clients. `AUTO_BLOCKER_TRUSTED_PROXIES` is a
comma-separated list of trusted IPs or CIDRs. Only requests whose direct peer
matches that list can supply `X-Forwarded-For` for client-IP resolution.

Blocked events are queued without blocking requests and written as rotating JSON
Lines. Defaults are a 10 MB active file plus 5 backups, with a bounded queue;
`/admin/events` reports events dropped when the queue is full. Override paths with `AUTO_BLOCKER_IP_BLOCKLIST`,
`AUTO_BLOCKER_DOMAIN_BLOCKLIST`, and `AUTO_BLOCKER_LOG`. Blocklist JSON files should be provisioned consistently on
all hosts. Use Redis for shared rate-limit, login-delay, and replay state across
workers and hosts; without Redis, memory fallback is per-process only.

The admin endpoints require `X-Admin-Token: <AUTO_BLOCKER_ADMIN_TOKEN>` or a
Bearer token:

```sh
curl -H "X-Admin-Token: $AUTO_BLOCKER_ADMIN_TOKEN" http://127.0.0.1:5000/admin/events
curl -X POST -H "X-Admin-Token: $AUTO_BLOCKER_ADMIN_TOKEN" \
	-H 'Content-Type: application/json' -d '{"ip":"203.0.113.8"}' \
	http://127.0.0.1:5000/admin/unblock
```

## Production Checklist

- Set `ENV=production`; startup rejects missing or placeholder values for
	`AUTO_BLOCKER_FORM_SECRET`, `AUTO_BLOCKER_ADMIN_TOKEN`, and `REDIS_URL`.
- Generate unique secrets and keep them in your deployment secret manager, not
	source control.
- Keep `REDIS_FAILURE_MODE=open` for development (the default). Set it to
	`closed` only when production should return 503 rather than use per-process
	memory during a Redis outage.
- Set `AUTO_BLOCKER_TRUSTED_PROXIES` to the exact proxy IPs/CIDRs in front of
	Gunicorn. Configure the proxy to replace/append forwarding headers safely.
- Configure Nginx/TLS, then run the protected-route load test using the same
	form secret and demo password as the running server.

## Production: Gunicorn Behind Nginx

Run Redis separately, then set the Redis URL and the direct Nginx peer address
before starting Gunicorn. Example for Nginx on the same host:

```sh
export REDIS_URL='redis://127.0.0.1:6379/0'
export AUTO_BLOCKER_TRUSTED_PROXIES='127.0.0.1/32,::1/128'
gunicorn --workers 4 --worker-class gthread --threads 8 --bind 127.0.0.1:8000 app:app
```

In the Nginx `location /`, proxy to `http://127.0.0.1:8000` and set
`Host $host`, `X-Real-IP $remote_addr`, `X-Forwarded-For $proxy_add_x_forwarded_for`,
and `X-Forwarded-Proto $scheme`. Keep Gunicorn bound to loopback and make
`AUTO_BLOCKER_TRUSTED_PROXIES` match the actual peer address Nginx uses. Do not
trust forwarded headers from arbitrary clients.

## Testing

Run `python -m pytest -q`. Tests cover rate limits, escalating pair-specific
login delays, proxy identity separation and spoof rejection, Redis-down fallback,
upload validation, blocked links, honeypots, token replay, log rotation, and the
admin endpoints. The browser page also has a convenience-only file extension/
size check; the backend independently checks size, extension, claimed MIME type,
and file signatures.

The opt-in HTTP load test posts valid signed login forms to the protected
`/api/login` route. It reports 200 and 429 counts separately and fails if no
requests are rate-limited. It targets **100 requests/second** over 1,000
requests with 50 concurrent clients. Start Gunicorn as above with the same
`AUTO_BLOCKER_FORM_SECRET` and `AUTO_BLOCKER_DEMO_PASSWORD`, then run:

```sh
export AUTO_BLOCKER_LOAD_TEST_URL='http://127.0.0.1:8000/api/login'
RUN_LOAD_TEST=1 python -m pytest -q tests/test_auto_blocker.py::test_gunicorn_http_load_target
```

The test reports failure if the configured target is not reached; it is a local
baseline, not a capacity guarantee for a particular deployment.

## Security notes

The `AutoBlocker` in `auto_blocker.py` is registered as Flask `before_request`
middleware and can be reused with an app. Its input checks reject common script
and SQL-injection patterns; they are not a substitute for context-aware output
encoding, parameterized database queries, CSRF protection, or application-level
validation. Keep secrets out of source control, use HTTPS, and use a production
WSGI server behind a correctly configured proxy. The example login/signup and
contact handlers do not persist user data.