import unittest
from datetime import date
from email.message import Message
from urllib.error import URLError

from tuke_canteen.client import MenuFetchError, build_menu_url, fetch_html


class FakeResponse:
    def __init__(self, payload: bytes, *, status: int = 200, content_type: str = "text/html; charset=utf-8"):
        self.payload = payload
        self.status = status
        self.headers = Message()
        self.headers["Content-Type"] = content_type
        self.headers["Content-Length"] = str(len(payload))

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False

    def read(self, limit: int):
        return self.payload[:limit]


class ClientTests(unittest.TestCase):
    def test_builds_dated_url(self):
        url = build_menu_url("https://example.test/menu/", date(2026, 8, 17))
        self.assertEqual(url, "https://example.test/menu/2026-08-17")

    def test_rejects_relative_url(self):
        with self.assertRaises(ValueError):
            build_menu_url("/menu")

    def test_fetches_and_decodes_html(self):
        def opener(request, timeout):
            self.assertEqual(timeout, 2)
            self.assertIn("tuke-canteen", request.headers["User-agent"])
            return FakeResponse("ľahké".encode())

        self.assertEqual(fetch_html("https://example.test/menu", timeout=2, opener=opener), "ľahké")

    def test_non_200_status_is_controlled(self):
        def opener(request, timeout):
            return FakeResponse(b"error", status=503)

        with self.assertRaisesRegex(MenuFetchError, "HTTP 503"):
            fetch_html("https://example.test/menu", opener=opener)

    def test_oversized_response_is_rejected(self):
        def opener(request, timeout):
            return FakeResponse(b"123456")

        with self.assertRaisesRegex(MenuFetchError, "size limit"):
            fetch_html("https://example.test/menu", max_bytes=5, opener=opener)

    def test_network_error_is_controlled(self):
        def opener(request, timeout):
            raise URLError("offline")

        with self.assertRaisesRegex(MenuFetchError, "offline"):
            fetch_html("https://example.test/menu", opener=opener)

    def test_timeout_must_be_positive(self):
        with self.assertRaises(ValueError):
            fetch_html("https://example.test/menu", timeout=0)


if __name__ == "__main__":
    unittest.main()

