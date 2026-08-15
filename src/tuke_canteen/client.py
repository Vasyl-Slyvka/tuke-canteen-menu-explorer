"""Small HTTP client with explicit limits and controlled failure modes."""

from __future__ import annotations

from datetime import date
from typing import Callable
from urllib.error import HTTPError, URLError
from urllib.parse import urlparse
from urllib.request import Request, urlopen

from .models import MenuSnapshot
from .parser import parse_menu

DEFAULT_MENU_URL = "https://jedalen.tuke.sk/jedalny-listok"
DEFAULT_TIMEOUT = 10.0
DEFAULT_MAX_BYTES = 2_000_000
USER_AGENT = "tuke-canteen-menu-explorer/1.0 (+public-menu-reader)"


class MenuFetchError(RuntimeError):
    """Raised when a public menu page cannot be downloaded safely."""


def build_menu_url(base_url: str = DEFAULT_MENU_URL, menu_date: date | None = None) -> str:
    parsed = urlparse(base_url)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        raise ValueError("menu URL must be an absolute HTTP or HTTPS URL")
    clean_url = base_url.rstrip("/")
    if menu_date is not None:
        clean_url = f"{clean_url}/{menu_date.isoformat()}"
    return clean_url


def fetch_html(
    url: str,
    *,
    timeout: float = DEFAULT_TIMEOUT,
    max_bytes: int = DEFAULT_MAX_BYTES,
    opener: Callable[..., object] = urlopen,
) -> str:
    """Download an HTML document while enforcing timeout and size limits."""
    if timeout <= 0:
        raise ValueError("timeout must be positive")
    if max_bytes <= 0:
        raise ValueError("max_bytes must be positive")
    build_menu_url(url)
    request = Request(
        url,
        headers={
            "User-Agent": USER_AGENT,
            "Accept": "text/html,application/xhtml+xml",
        },
    )
    try:
        with opener(request, timeout=timeout) as response:
            status = getattr(response, "status", 200)
            if status != 200:
                raise MenuFetchError(f"menu server returned HTTP {status}")
            length_header = response.headers.get("Content-Length")
            if length_header and int(length_header) > max_bytes:
                raise MenuFetchError("menu response exceeds the configured size limit")
            payload = response.read(max_bytes + 1)
            if len(payload) > max_bytes:
                raise MenuFetchError("menu response exceeds the configured size limit")
            charset = response.headers.get_content_charset() or "utf-8"
    except MenuFetchError:
        raise
    except HTTPError as exc:
        raise MenuFetchError(f"menu server returned HTTP {exc.code}") from exc
    except (URLError, TimeoutError, OSError) as exc:
        reason = getattr(exc, "reason", exc)
        raise MenuFetchError(f"could not download the menu: {reason}") from exc
    try:
        return payload.decode(charset)
    except (LookupError, UnicodeDecodeError) as exc:
        raise MenuFetchError("menu response has an unsupported text encoding") from exc


def fetch_menu(
    url: str = DEFAULT_MENU_URL,
    *,
    timeout: float = DEFAULT_TIMEOUT,
    max_bytes: int = DEFAULT_MAX_BYTES,
) -> MenuSnapshot:
    resolved_url = build_menu_url(url)
    return parse_menu(
        fetch_html(resolved_url, timeout=timeout, max_bytes=max_bytes),
        source_url=resolved_url,
    )

