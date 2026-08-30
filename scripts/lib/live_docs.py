"""Fetch bounded, public HTTPS upstream docs for the grill stage.

The default transport is deliberately stricter than a general HTTP client:
public HTTPS only, DNS answers fail closed if any address is non-global, the
connection is pinned to a validated numeric IP while TLS still verifies the
original hostname, redirects are revalidated hop-by-hop, and response/time
budgets are bounded. A custom ``http_get`` is a trusted injection seam used by
tests/adapters; fetch_doc still enforces URL syntax/literal-IP policy first.

The public API never raises: stale cache remains available when a live fetch
fails, and cache I/O is best-effort.
"""
from __future__ import annotations

import hashlib
import http.client
import ipaddress
import json
import os
import queue
import re
import socket
import ssl
import tempfile
import threading
import time
from pathlib import Path
from typing import Callable
from urllib.parse import SplitResult, urljoin, urlsplit

TTL_SECONDS = 7 * 86400
_TIMEOUT = 15
_MAX_REDIRECTS = 5
_MAX_RESPONSE_BYTES = 2 * 1024 * 1024
_READ_CHUNK = 64 * 1024
_CACHE_POLICY = "public-https-pinned-v1"
_ALLOWED_CONTENT_TYPES = {
    "application/json",
    "application/markdown",
    "application/xml",
    "application/xhtml+xml",
}
_REDIRECT_STATUSES = {301, 302, 303, 307, 308}


def _cache_path(url: str, cache_dir: Path) -> Path:
    key = hashlib.sha256(url.encode("utf-8")).hexdigest()[:20]
    return Path(cache_dir) / "docs-cache" / f"{key}.json"


def _remaining(deadline: float) -> float:
    remaining = deadline - time.monotonic()
    if remaining <= 0:
        raise TimeoutError("live-docs total deadline exceeded")
    return remaining


def _is_public_address(value: str | ipaddress._BaseAddress) -> bool:
    address = value if isinstance(value, ipaddress._BaseAddress) else ipaddress.ip_address(value)
    if isinstance(address, ipaddress.IPv6Address):
        # Fail closed on IPv4-transition encodings. Their effective IPv4
        # destination can differ from the apparent globally-routable IPv6
        # address (for example IPv4-mapped or NAT64 forms).
        if address.ipv4_mapped is not None or address.sixtofour is not None or address.teredo is not None:
            return False
        if address in ipaddress.IPv6Network("::/96"):
            return False
        if address in ipaddress.IPv6Network("64:ff9b::/96"):
            return False
        if address in ipaddress.IPv6Network("64:ff9b:1::/48"):
            return False
    return bool(
        address.is_global
        and not address.is_private
        and not address.is_loopback
        and not address.is_link_local
        and not address.is_multicast
        and not address.is_reserved
        and not address.is_unspecified
    )


def _validate_target_url(url: str) -> tuple[SplitResult, str, int, str]:
    if any(ord(ch) < 0x20 or ord(ch) == 0x7f for ch in url):
        raise ValueError("live-docs URL contains control characters")
    try:
        parts = urlsplit(url)
    except ValueError as exc:
        raise ValueError(f"invalid live-docs URL: {exc}") from exc

    if parts.scheme.lower() != "https":
        raise ValueError("live-docs requires HTTPS")
    if not parts.hostname:
        raise ValueError("live-docs URL requires a hostname")
    if parts.username is not None or parts.password is not None:
        raise ValueError("live-docs URL credentials are not allowed")

    host = parts.hostname
    try:
        port = parts.port or 443
    except ValueError as exc:
        raise ValueError(f"invalid live-docs port: {exc}") from exc
    if not 1 <= port <= 65535:
        raise ValueError("invalid live-docs port")

    try:
        literal = ipaddress.ip_address(host)
    except ValueError:
        try:
            host = host.encode("idna").decode("ascii")
        except UnicodeError as exc:
            raise ValueError("invalid live-docs hostname") from exc
    else:
        if not _is_public_address(literal):
            raise ValueError(f"blocked live-docs target address: {literal}")
        host = str(literal)

    path = parts.path or "/"
    if parts.query:
        path += "?" + parts.query
    return parts, host, port, path


def _resolve_public_ips(host: str, port: int, deadline: float) -> list[str]:
    try:
        literal = ipaddress.ip_address(host)
    except ValueError:
        literal = None
    if literal is not None:
        if not _is_public_address(literal):
            raise ValueError(f"blocked live-docs target address: {literal}")
        return [str(literal)]

    result_queue: queue.Queue = queue.Queue(maxsize=1)

    def resolve() -> None:
        try:
            result_queue.put((True, socket.getaddrinfo(
                host,
                port,
                family=socket.AF_UNSPEC,
                type=socket.SOCK_STREAM,
                proto=socket.IPPROTO_TCP,
            )))
        except BaseException as exc:  # hand result back to caller; daemon cannot escape
            try:
                result_queue.put((False, exc))
            except queue.Full:
                pass

    worker = threading.Thread(target=resolve, name="awiki-live-docs-dns", daemon=True)
    worker.start()
    try:
        ok, payload = result_queue.get(timeout=_remaining(deadline))
    except queue.Empty as exc:
        raise TimeoutError("live-docs DNS resolution exceeded total deadline") from exc
    if not ok:
        raise OSError(f"live-docs DNS resolution failed: {payload}") from payload

    addresses: list[str] = []
    seen: set[str] = set()
    for family, _socktype, _proto, _canonname, sockaddr in payload:
        if family not in (socket.AF_INET, socket.AF_INET6):
            continue
        value = sockaddr[0].split("%", 1)[0]
        try:
            address = ipaddress.ip_address(value)
        except ValueError as exc:
            raise ValueError(f"invalid DNS address for live-docs target: {value}") from exc
        if not _is_public_address(address):
            raise ValueError(f"blocked/non-global DNS target address: {address}")
        normalized = str(address)
        if normalized not in seen:
            seen.add(normalized)
            addresses.append(normalized)

    if not addresses:
        raise OSError("live-docs DNS returned no usable addresses")
    return addresses


class _PinnedHTTPSConnection(http.client.HTTPSConnection):
    """HTTPSConnection whose TCP destination is an already-validated IP."""

    def __init__(self, host: str, connect_ip: str, port: int, timeout: float):
        context = ssl.create_default_context()
        super().__init__(host=host, port=port, timeout=timeout, context=context)
        self._connect_ip = connect_ip

    def connect(self) -> None:  # pragma: no cover - exercised by process smoke/network seam
        raw_sock = socket.create_connection(
            (self._connect_ip, self.port),
            self.timeout,
            self.source_address,
        )
        try:
            self.sock = self._context.wrap_socket(raw_sock, server_hostname=self.host)
        except BaseException:
            raw_sock.close()
            raise


def _open_pinned_https(host: str, connect_ip: str, port: int,
                       target: str, timeout: float):
    conn = _PinnedHTTPSConnection(host, connect_ip, port, timeout)
    conn.request(
        "GET",
        target,
        headers={
            "Accept": "text/markdown, text/plain;q=0.9, application/json;q=0.5, application/xml;q=0.5",
            "User-Agent": "A-Wiki-live-docs/1",
        },
    )
    return conn, conn.getresponse()


def _validate_content_type(headers) -> str:
    if hasattr(headers, "get_content_type"):
        content_type = headers.get_content_type().lower()
    else:
        raw = headers.get("Content-Type", "") if headers is not None else ""
        content_type = raw.split(";", 1)[0].strip().lower()
    if not content_type:
        raise ValueError("live-docs response missing Content-Type")
    if not (content_type.startswith("text/") or content_type in _ALLOWED_CONTENT_TYPES):
        raise ValueError(f"live-docs disallowed content type: {content_type}")
    return content_type


def _read_limited_body(resp, deadline: float) -> bytes:
    declared = resp.headers.get("Content-Length") if getattr(resp, "headers", None) else None
    if declared:
        try:
            declared_size = int(declared)
        except (TypeError, ValueError) as exc:
            raise ValueError("invalid live-docs Content-Length") from exc
        if declared_size < 0 or declared_size > _MAX_RESPONSE_BYTES:
            raise ValueError("live-docs response size exceeds byte limit")

    body = bytearray()
    while True:
        remaining = _remaining(deadline)
        fp = getattr(resp, "fp", None)
        raw = getattr(fp, "raw", None)
        sock = getattr(raw, "_sock", None)
        if sock is not None:
            sock.settimeout(remaining)
        to_read = min(_READ_CHUNK, _MAX_RESPONSE_BYTES + 1 - len(body))
        chunk = resp.read(to_read)
        if not chunk:
            break
        body.extend(chunk)
        if len(body) > _MAX_RESPONSE_BYTES:
            raise ValueError("live-docs response size exceeds byte limit")
    return bytes(body)


def _request_once(url: str, deadline: float) -> tuple[int, dict[str, str], bytes]:
    _parts, host, port, target = _validate_target_url(url)
    addresses = _resolve_public_ips(host, port, deadline)
    connect_ip = addresses[0]
    conn = None
    resp = None
    try:
        conn, resp = _open_pinned_https(host, connect_ip, port, target, _remaining(deadline))
        sock = getattr(conn, "sock", None)
        if sock is not None:
            peer_value = sock.getpeername()[0].split("%", 1)[0]
            peer = ipaddress.ip_address(peer_value)
            if not _is_public_address(peer):
                raise ValueError(f"blocked live-docs connected peer: {peer}")
            if peer != ipaddress.ip_address(connect_ip):
                raise ValueError("live-docs connected peer differs from pinned address")

        status = int(resp.status)
        headers = {str(k): str(v) for k, v in resp.headers.items()}
        if status in _REDIRECT_STATUSES:
            return status, headers, b""
        if not 200 <= status < 300:
            raise OSError(f"live-docs HTTP status {status}")
        _validate_content_type(resp.headers)
        body = _read_limited_body(resp, deadline)
        return status, headers, body
    finally:
        if resp is not None:
            try:
                resp.close()
            except Exception:
                pass
        if conn is not None:
            try:
                conn.close()
            except Exception:
                pass


def _decode_body(body: bytes, content_type_header: str) -> str:
    match = re.search(r"charset\s*=\s*[\"']?([^;\s\"']+)", content_type_header or "", re.I)
    encoding = match.group(1) if match else "utf-8"
    try:
        return body.decode(encoding, errors="replace")
    except LookupError:
        return body.decode("utf-8", errors="replace")


def _default_get(url: str, timeout: int) -> str:
    deadline = time.monotonic() + max(0, timeout)
    current = url
    for hop in range(_MAX_REDIRECTS + 1):
        _remaining(deadline)
        _validate_target_url(current)
        status, headers, body = _request_once(current, deadline)
        if status in _REDIRECT_STATUSES:
            location = headers.get("Location") or headers.get("location")
            if not location:
                raise ValueError("live-docs redirect missing Location")
            if hop >= _MAX_REDIRECTS:
                raise ValueError("live-docs redirect limit exceeded")
            current = urljoin(current, location)
            _validate_target_url(current)
            continue
        return _decode_body(body, headers.get("Content-Type", ""))
    raise ValueError("live-docs redirect limit exceeded")


def _read_cache(cp: Path) -> dict | None:
    try:
        data = json.loads(cp.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError, TypeError):
        return None
    if not isinstance(data, dict):
        return None
    if not isinstance(data.get("content"), str):
        return None
    if not isinstance(data.get("fetched_at"), (int, float)):
        return None
    return data


def _write_cache_atomic(cp: Path, payload: dict) -> None:
    cp.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp_name = tempfile.mkstemp(prefix=cp.name + ".", suffix=".tmp", dir=str(cp.parent))
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as handle:
            json.dump(payload, handle, ensure_ascii=False)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(tmp_name, cp)
    except BaseException:
        try:
            os.unlink(tmp_name)
        except OSError:
            pass
        raise


def fetch_doc(url: str, cache_dir: Path,
              http_get: Callable[[str, int], str] | None = None) -> dict:
    """Fetch one public HTTPS document with cache/stale-cache fallback.

    ``http_get`` is an intentionally trusted injection seam. It receives only a
    URL that passed scheme/hostname/literal-IP policy; network DNS/IP guarantees
    are provided by the default transport only.
    """
    try:
        _validate_target_url(url)
    except Exception as exc:
        return {"source": "unavailable", "content": "", "url": url,
                "reason": f"fetch failed: {exc}"}

    get = http_get or _default_get
    cp = _cache_path(url, cache_dir)
    cached = _read_cache(cp)
    if cached is not None and (
        cached.get("policy") != _CACHE_POLICY or cached.get("url") != url
    ):
        cached = None

    fresh = cached is not None and (
        time.time() - cached.get("fetched_at", 0) <= TTL_SECONDS)
    if fresh:
        return {"source": "cache", "content": cached["content"],
                "url": url, "fetched_at": cached["fetched_at"]}

    try:
        content = get(url, _TIMEOUT)
    except Exception as exc:
        if cached:
            return {"source": "cache-stale", "content": cached["content"],
                    "url": url, "fetched_at": cached["fetched_at"],
                    "reason": f"fetch failed: {exc}"}
        return {"source": "unavailable", "content": "", "url": url,
                "reason": f"fetch failed: {exc}"}

    now = round(time.time(), 3)
    payload = {"policy": _CACHE_POLICY, "url": url, "content": content, "fetched_at": now}
    try:
        _write_cache_atomic(cp, payload)
    except Exception:
        pass
    return {"source": "live", "content": content, "url": url,
            "fetched_at": now}


def skill_docs_url(skill_md: Path) -> str | None:
    """Return the ``docs:`` frontmatter field of a SKILL.md, when present."""
    try:
        text = Path(skill_md).read_text(encoding="utf-8")
    except OSError:
        return None
    m = re.match(r"^---\n(.*?)\n---", text, re.S)
    if not m:
        return None
    for line in m.group(1).splitlines():
        mm = re.match(r"^docs:\s*(\S+)\s*$", line.strip())
        if mm:
            return mm.group(1)
    return None
