"""Reusable Flask request protection for sensitive routes."""

import base64
import hashlib
import hmac
import ipaddress
import json
import logging
import math
import os
import queue
import re
import secrets
import threading
import time
from concurrent_log_handler import ConcurrentRotatingFileHandler
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse

from flask import jsonify, request

try:
	import redis
	from redis.exceptions import RedisError
except ImportError:
	redis = None

	class RedisError(Exception):
		pass

from config import AutoBlockerConfig


_RATE_LIMIT_SCRIPT = """
local now = tonumber(ARGV[1])
local window = tonumber(ARGV[2])
local limit = tonumber(ARGV[3])
redis.call('ZREMRANGEBYSCORE', KEYS[1], '-inf', now - window)
local count = redis.call('ZCARD', KEYS[1])
if count >= limit then
	local oldest = redis.call('ZRANGE', KEYS[1], 0, 0, 'WITHSCORES')
	return {count, math.max(1, math.ceil(tonumber(oldest[2]) + window - now))}
end
redis.call('ZADD', KEYS[1], now, ARGV[4])
redis.call('EXPIRE', KEYS[1], ARGV[5])
return {count + 1, 0}
"""

_FAILED_LOGIN_SCRIPT = """
local count = redis.call('HINCRBY', KEYS[1], 'count', 1)
if count == 1 then redis.call('EXPIRE', KEYS[1], ARGV[1]) end
local delay = 0
if count >= tonumber(ARGV[2]) then
	local exponent = math.min(count - tonumber(ARGV[2]), 20)
	delay = tonumber(ARGV[3]) * (2 ^ exponent)
	if delay > tonumber(ARGV[4]) then delay = tonumber(ARGV[4]) end
	redis.call('HSET', KEYS[1], 'next_allowed', tonumber(ARGV[5]) + delay)
end
return {count, delay}
"""


class RedisUnavailableError(RuntimeError):
	"""Raised when Redis is required but unavailable in fail-closed mode."""


class _EventJsonFormatter(logging.Formatter):
	def format(self, record):
		return json.dumps(record.event, separators=(",", ":"))


class AutoBlocker:
	"""Enforce request limits and validations before sensitive Flask routes."""

	def __init__(self, app=None, config=None):
		self.config = config or AutoBlockerConfig()
		self.config.validate()
		self._lock = threading.RLock()
		self._memory_state = {}
		self._last_memory_cleanup = 0
		self._redis_degraded = False
		self._redis_retry_after = 0
		self.redis = None
		if self.config.REDIS_URL and redis is not None:
			self.redis = redis.Redis.from_url(
				self.config.REDIS_URL,
				socket_connect_timeout=self.config.REDIS_SOCKET_TIMEOUT_SECONDS,
				socket_timeout=self.config.REDIS_SOCKET_TIMEOUT_SECONDS,
				decode_responses=True,
			)
		self._log_queue = queue.Queue(maxsize=self.config.BLOCKED_LOG_QUEUE_SIZE)
		self._dropped_log_events = 0
		Path(self.config.BLOCKED_EVENTS_PATH).parent.mkdir(parents=True, exist_ok=True)
		self._log_handler = ConcurrentRotatingFileHandler(
			self.config.BLOCKED_EVENTS_PATH,
			maxBytes=self.config.BLOCKED_LOG_MAX_BYTES,
			backupCount=self.config.BLOCKED_LOG_BACKUP_COUNT,
			encoding="utf-8",
			delay=True,
		)
		self._log_worker_pid = None
		if app is not None:
			self.init_app(app)

	def init_app(self, app):
		app.before_request(self.protect_request)
		app.extensions["auto_blocker"] = self

	def deny(self, rule, reason, status=403, retry_after=None):
		ip = self.client_ip()
		self._log_block(ip, rule, request.path)
		response = jsonify({
			"blocked": True,
			"reason": reason,
			"code": rule,
			"retryAfter": retry_after,
		})
		response.status_code = status
		if retry_after is not None:
			response.headers["Retry-After"] = str(retry_after)
		return response

	def protect_request(self):
		try:
			return self._protect_request()
		except RedisUnavailableError:
			return self.redis_unavailable_response()

	def _protect_request(self):
		if request.path not in self.config.SENSITIVE_ROUTES:
			return None

		ip = self.client_ip()
		limited = self._check_rate_limit(ip, request.path)
		if limited:
			return self.deny(
				"RATE_LIMIT",
				"Too many requests. Please try again later.",
				status=429,
				retry_after=limited,
			)

		if self._is_ip_blocked(ip):
			return self.deny("IP_BLOCKLIST", "This IP address is blocked.")
		if self._is_country_blocked():
			return self.deny("COUNTRY_BLOCKLIST", "Requests from this country are blocked.")

		if request.path in self.config.LOGIN_ROUTES:
			payload = request.get_json(silent=True) or request.form
			retry_after = self.login_retry_after(payload.get("username"), ip)
			if retry_after:
				return self.deny(
					"LOGIN_DELAY",
					"Please wait briefly before trying that account from this IP again.",
					status=429,
					retry_after=retry_after,
				)

		if request.path in self.config.FORM_ROUTES:
			form = request.get_json(silent=True) or request.form
			if str(form.get(self.config.HONEYPOT_FIELD, "")).strip():
				return self.deny("HONEYPOT", "Automated form submission detected.")
			if not self._consume_form_token(form.get(self.config.FORM_TOKEN_FIELD, "")):
				return self.deny("FORM_TOO_FAST", "Please complete the form and try again.")

		if request.path in self.config.UPLOAD_ROUTES:
			upload_error = self._validate_uploads()
			if upload_error:
				rule, reason = upload_error
				return self.deny(rule, reason)

		payload = request.get_json(silent=True)
		if payload is None:
			payload = request.form.to_dict()
		unsafe = self._find_unsafe_input(payload)
		if unsafe:
			rule, reason = unsafe
			return self.deny(rule, reason)

		if self._contains_blocked_link(payload):
			return self.deny("LINK_BLOCKLIST", "A submitted link is not allowed.")
		return None

	def record_failed_login(self, account, ip=None):
		"""Track one IP/account pair and return its escalating retry delay, if any."""
		ip = ip or self.client_ip()
		key = self._state_key("login", f"{ip}\0{str(account or '').strip().casefold()}")
		now = time.time()
		if self._redis_available():
			try:
				count, delay = self.redis.eval(
					_FAILED_LOGIN_SCRIPT,
					1,
					key,
					self.config.LOGIN_STATE_TTL_SECONDS,
					self.config.LOGIN_FAILURE_LIMIT,
					self.config.LOGIN_DELAY_BASE_SECONDS,
					self.config.LOGIN_DELAY_MAX_SECONDS,
					now,
				)
				self._redis_succeeded()
				return int(math.ceil(delay)) if int(count) >= self.config.LOGIN_FAILURE_LIMIT else None
			except RedisError as exc:
				self._handle_redis_failure(exc)

		with self._lock:
			self._cleanup_memory_state(now)
			state = self._memory_state.get(key)
			if state is None:
				state = {"count": 0, "next_allowed": 0, "expires_at": now + self.config.LOGIN_STATE_TTL_SECONDS}
				self._store_memory_state(key, state)
			state["count"] += 1
			count = state["count"]
			if count < self.config.LOGIN_FAILURE_LIMIT:
				return None
			exponent = min(count - self.config.LOGIN_FAILURE_LIMIT, 20)
			delay = min(
				self.config.LOGIN_DELAY_MAX_SECONDS,
				self.config.LOGIN_DELAY_BASE_SECONDS * (2 ** exponent),
			)
			state["next_allowed"] = now + delay
			return int(math.ceil(delay))

	def record_successful_login(self, account, ip=None):
		ip = ip or self.client_ip()
		key = self._state_key("login", f"{ip}\0{str(account or '').strip().casefold()}")
		with self._lock:
			self._memory_state.pop(key, None)
		if self._redis_available():
			try:
				self.redis.delete(key)
				self._redis_succeeded()
			except RedisError as exc:
				self._handle_redis_failure(exc)

	def login_retry_after(self, account, ip=None):
		ip = ip or self.client_ip()
		key = self._state_key("login", f"{ip}\0{str(account or '').strip().casefold()}")
		now = time.time()
		if self._redis_available():
			try:
				next_allowed = self.redis.hget(key, "next_allowed")
				self._redis_succeeded()
				return max(1, int(math.ceil(float(next_allowed) - now))) if next_allowed and float(next_allowed) > now else None
			except RedisError as exc:
				self._handle_redis_failure(exc)
		with self._lock:
			self._cleanup_memory_state(now)
			state = self._memory_state.get(key)
			if not state or state["next_allowed"] <= now:
				return None
			return max(1, int(math.ceil(state["next_allowed"] - now)))

	def issue_form_token(self):
		payload = json.dumps(
			{"issued": time.time(), "nonce": secrets.token_urlsafe(16)},
			separators=(",", ":"),
		).encode("utf-8")
		encoded = base64.urlsafe_b64encode(payload).decode("ascii").rstrip("=")
		signature = hmac.new(
			self.config.FORM_TOKEN_SECRET.encode("utf-8"),
			encoded.encode("ascii"),
			hashlib.sha256,
		).hexdigest()
		return f"{encoded}.{signature}"

	def _consume_form_token(self, token):
		try:
			encoded, signature = str(token).split(".", 1)
			expected = hmac.new(
				self.config.FORM_TOKEN_SECRET.encode("utf-8"),
				encoded.encode("ascii"),
				hashlib.sha256,
			).hexdigest()
			if not hmac.compare_digest(signature, expected):
				return False
			payload_bytes = base64.urlsafe_b64decode(encoded + "=" * (-len(encoded) % 4))
			payload = json.loads(payload_bytes)
			issued = float(payload["issued"])
			nonce = str(payload["nonce"])
		except (ValueError, TypeError, KeyError, json.JSONDecodeError):
			return False

		now = time.time()
		if issued > now or now - issued < self.config.MIN_FORM_FILL_SECONDS:
			return False
		if now - issued > self.config.FORM_TOKEN_MAX_AGE_SECONDS:
			return False
		token_key = self._state_key("form-token", nonce)
		if self._redis_available():
			try:
				accepted = self.redis.set(
					token_key,
					"1",
					nx=True,
					ex=self.config.FORM_TOKEN_MAX_AGE_SECONDS,
				)
				self._redis_succeeded()
				return bool(accepted)
			except RedisError as exc:
				self._handle_redis_failure(exc)
		with self._lock:
			self._cleanup_memory_state(now)
			if token_key in self._memory_state:
				return False
			self._store_memory_state(token_key, {
				"expires_at": now + self.config.FORM_TOKEN_MAX_AGE_SECONDS,
			})
		return True

	def client_ip(self):
		"""Resolve X-Forwarded-For only when the direct peer is a trusted proxy."""
		remote = request.remote_addr or ""
		try:
			peer = ipaddress.ip_address(remote)
		except ValueError:
			return "unknown"
		if not self._is_trusted_proxy(peer):
			return str(peer)
		forwarded = request.headers.get("X-Forwarded-For", "")
		if not forwarded:
			return str(peer)
		try:
			chain = [ipaddress.ip_address(part.strip()) for part in forwarded.split(",")]
		except ValueError:
			return str(peer)
		chain.append(peer)
		for address in reversed(chain):
			if not self._is_trusted_proxy(address):
				return str(address)
		return str(chain[0])

	def _is_trusted_proxy(self, address):
		for proxy in self.config.TRUSTED_PROXIES:
			try:
				if address in ipaddress.ip_network(str(proxy), strict=False):
					return True
			except ValueError:
				continue
		return False

	def unblock_ip(self, ip):
		"""Remove an IP from the blocklist and clear any in-memory lock."""
		try:
			normalized = str(ipaddress.ip_address(ip))
		except ValueError:
			return False
		blocked = self._read_json(self.config.IP_BLOCKLIST_PATH, [])
		remaining = [entry for entry in blocked if str(entry) != normalized]
		self._write_json(self.config.IP_BLOCKLIST_PATH, remaining)
		return len(remaining) != len(blocked)

	def _check_rate_limit(self, ip, route):
		now = time.time()
		window = self.config.RATE_LIMIT_WINDOW_SECONDS
		limit_ttl = max(self.config.RATE_LIMIT_KEY_TTL_SECONDS, window + 1)
		general_key = self._state_key("rate", f"{ip}\0sensitive")
		retry_after = self._consume_rate_slot(
			general_key, self.config.RATE_LIMIT_PER_MINUTE, now, window, limit_ttl
		)
		if retry_after:
			return retry_after
		if route in self.config.AUTH_ROUTES:
			auth_key = self._state_key("rate", f"{ip}\0auth")
			retry_after = self._consume_rate_slot(
				auth_key, self.config.AUTH_RATE_LIMIT_PER_MINUTE, now, window, limit_ttl
			)
			if retry_after:
				return retry_after
		return None

	def check_form_token_rate_limit(self):
		ip = self.client_ip()
		now = time.time()
		window = self.config.RATE_LIMIT_WINDOW_SECONDS
		ttl = max(self.config.RATE_LIMIT_KEY_TTL_SECONDS, window + 1)
		key = self._state_key("rate", f"{ip}\0form-token")
		return self._consume_rate_slot(
			key,
			self.config.FORM_TOKEN_RATE_LIMIT_PER_MINUTE,
			now,
			window,
			ttl,
		)

	def _state_key(self, kind, identity):
		digest = hashlib.sha256(identity.encode("utf-8")).hexdigest()
		return f"{self.config.REDIS_KEY_PREFIX}:{kind}:{digest}"

	def _consume_rate_slot(self, key, limit, now, window, ttl):
		if self._redis_available():
			try:
				count, retry_after = self.redis.eval(
					_RATE_LIMIT_SCRIPT,
					1,
					key,
					now,
					window,
					limit,
					f"{now:.6f}:{secrets.token_hex(8)}",
					ttl,
				)
				self._redis_succeeded()
				return int(retry_after) or None
			except RedisError as exc:
				self._handle_redis_failure(exc)
		with self._lock:
			self._cleanup_memory_state(now)
			state = self._memory_state.get(key)
			if state is None:
				state = {"timestamps": [], "expires_at": now + ttl}
				self._store_memory_state(key, state)
			cutoff = now - window
			state["timestamps"] = [stamp for stamp in state["timestamps"] if stamp > cutoff]
			if len(state["timestamps"]) >= limit:
				return max(1, int(math.ceil(state["timestamps"][0] + window - now)))
			state["timestamps"].append(now)
			state["expires_at"] = now + ttl
			return None

	def _cleanup_memory_state(self, now):
		if now - self._last_memory_cleanup < self.config.MEMORY_STATE_CLEANUP_INTERVAL_SECONDS:
			return
		self._memory_state = {
			key: state for key, state in self._memory_state.items()
			if state["expires_at"] > now
		}
		self._last_memory_cleanup = now

	def _store_memory_state(self, key, state):
		if key not in self._memory_state and len(self._memory_state) >= self.config.MEMORY_STATE_MAX_ENTRIES:
			oldest_key = next(iter(self._memory_state))
			self._memory_state.pop(oldest_key, None)
		self._memory_state[key] = state

	def _disable_redis(self, error):
		with self._lock:
			if not self._redis_degraded:
				logging.getLogger(__name__).warning(
					"Auto Blocker Redis outage; failure mode=%s, per-process fallback may apply: %s",
					self.config.REDIS_FAILURE_MODE,
					error,
				)
			self._redis_degraded = True
			self._redis_retry_after = time.time() + self.config.REDIS_RETRY_SECONDS

	def _handle_redis_failure(self, error):
		self._disable_redis(error)
		if self.config.REDIS_FAILURE_MODE == "closed":
			raise RedisUnavailableError("Redis is required but unavailable.") from error

	def _redis_available(self):
		if self.redis is None:
			if self.config.REDIS_FAILURE_MODE == "closed":
				self._disable_redis("Redis client is not configured")
				raise RedisUnavailableError("Redis is required but not configured.")
			return False
		if self._redis_degraded and time.time() < self._redis_retry_after:
			if self.config.REDIS_FAILURE_MODE == "closed":
				raise RedisUnavailableError("Redis is unavailable.")
			return False
		return True

	def _redis_succeeded(self):
		with self._lock:
			if self._redis_degraded:
				logging.getLogger(__name__).warning(
					"Auto Blocker Redis recovered; shared protection state is active again."
				)
			self._redis_degraded = False
			self._redis_retry_after = 0

	def redis_unavailable_response(self):
		return self.deny(
			"REDIS_UNAVAILABLE",
			"Security checks are temporarily unavailable. Please retry shortly.",
			status=503,
			retry_after=max(1, self.config.REDIS_RETRY_SECONDS),
		)

	@property
	def dropped_log_events(self):
		with self._lock:
			return self._dropped_log_events

	def _write_log_events(self):
		self._log_handler.setFormatter(_EventJsonFormatter())
		while True:
			event = self._log_queue.get()
			try:
				if event is None:
					return
				record = logging.LogRecord(__name__, logging.INFO, "", 0, "", (), None)
				record.event = event
				self._log_handler.emit(record)
			except Exception:
				with self._lock:
					self._dropped_log_events += 1
			finally:
				self._log_queue.task_done()

	def flush_logs(self):
		"""Wait for queued events to reach the rotating log file."""
		self._log_queue.join()

	def _ensure_log_worker(self):
		process_id = os.getpid()
		if self._log_worker_pid == process_id:
			return
		with self._lock:
			if self._log_worker_pid == process_id:
				return
			if self._log_worker_pid is not None:
				self._log_queue = queue.Queue(maxsize=self.config.BLOCKED_LOG_QUEUE_SIZE)
			self._log_worker_pid = process_id
			self._log_worker = threading.Thread(target=self._write_log_events, daemon=True)
			self._log_worker.start()

	def _is_ip_blocked(self, ip):
		try:
			candidate = ipaddress.ip_address(ip)
		except ValueError:
			return False
		for item in self._read_json(self.config.IP_BLOCKLIST_PATH, []):
			try:
				if candidate in ipaddress.ip_network(str(item), strict=False):
					return True
			except ValueError:
				continue
		return False

	def _is_country_blocked(self):
		header_name = self.config.COUNTRY_CODE_HEADER
		if not header_name:
			return False
		country = request.headers.get(header_name, "").strip().upper()
		if not re.fullmatch(r"[A-Z]{2}", country):
			return False
		return country in self.config.COUNTRY_BLOCKED_CODES

	def _validate_uploads(self):
		uploads = [file for file in request.files.values() if file and file.filename]
		if not uploads:
			return "UPLOAD_REQUIRED", "Choose a file to upload."
		signatures = {
			".jpg": ("image/jpeg", lambda data: data.startswith(b"\xff\xd8\xff")),
			".jpeg": ("image/jpeg", lambda data: data.startswith(b"\xff\xd8\xff")),
			".png": ("image/png", lambda data: data.startswith(b"\x89PNG\r\n\x1a\n")),
			".pdf": ("application/pdf", lambda data: data.startswith(b"%PDF-")),
		}
		for uploaded in uploads:
			name = Path(uploaded.filename).name
			extension = Path(name).suffix.lower()
			if extension not in signatures:
				return "FILE_TYPE", "Only JPG, PNG, and PDF files are allowed."
			content = uploaded.stream.read(self.config.MAX_UPLOAD_BYTES + 1)
			uploaded.stream.seek(0)
			if len(content) > self.config.MAX_UPLOAD_BYTES:
				return "FILE_TOO_LARGE", "The maximum upload size is 5 MB."
			expected_mime, signature_check = signatures[extension]
			if not signature_check(content) or uploaded.mimetype != expected_mime:
				return "FILE_CONTENT", "The file type does not match its contents."
		return None

	def _find_unsafe_input(self, value):
		if isinstance(value, dict):
			for key, item in value.items():
				result = self._find_unsafe_input(key)
				if result:
					return result
				result = self._find_unsafe_input(item)
				if result:
					return result
		elif isinstance(value, (list, tuple)):
			for item in value:
				result = self._find_unsafe_input(item)
				if result:
					return result
		elif isinstance(value, str):
			if re.search(r"<\s*script\b|javascript\s*:|\bon\w+\s*=", value, re.I):
				return "UNSAFE_INPUT", "Script content is not allowed."
			if re.search(
				r"\bunion\s+select\b|\b(select|insert|update|delete|drop)\b.{0,30}\b(from|into|table)\b|(?:--|/\*|\*/)",
				value,
				re.I,
			):
				return "UNSAFE_INPUT", "Potentially unsafe input was rejected."
		return None

	def _contains_blocked_link(self, value):
		if isinstance(value, dict):
			return any(self._contains_blocked_link(item) for item in value.values())
		if isinstance(value, (list, tuple)):
			return any(self._contains_blocked_link(item) for item in value)
		if not isinstance(value, str):
			return False
		blocked = {str(domain).lower().lstrip(".") for domain in
				   self._read_json(self.config.DOMAIN_BLOCKLIST_PATH, [])}
		for match in re.findall(r"(?:https?://|www\.)[^\s<>'\"]+", value, re.I):
			parsed = urlparse(match if "://" in match else f"http://{match}")
			host = (parsed.hostname or "").lower().rstrip(".")
			if any(host == domain or host.endswith(f".{domain}") for domain in blocked):
				return True
		return False

	def _log_block(self, ip, rule, route):
		event = {
			"time": datetime.now(timezone.utc).isoformat(),
			"ip": ip,
			"rule": rule,
			"route": route,
		}
		self._ensure_log_worker()
		try:
			self._log_queue.put_nowait(event)
		except queue.Full:
			with self._lock:
				self._dropped_log_events += 1

	@staticmethod
	def _read_json(path, default):
		try:
			with Path(path).open(encoding="utf-8") as data_file:
				return json.load(data_file)
		except (OSError, json.JSONDecodeError):
			return default

	@staticmethod
	def _write_json(path, value):
		target = Path(path)
		target.parent.mkdir(parents=True, exist_ok=True)
		target.write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")
