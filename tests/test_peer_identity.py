"""A forwarded header is not a trusted identity without a configured proxy."""
import unittest
from server import Handler


class PeerIdentityTests(unittest.TestCase):
    def test_forwarded_header_cannot_change_rate_limit_key(self):
        handler = object.__new__(Handler)
        handler.client_address = ("127.0.0.1", 1234)
        for forged in ("", "198.51.100.1", "198.51.100.2, 127.0.0.1"):
            handler.headers = {"X-Forwarded-For": forged}
            self.assertEqual(handler._client_key(), "127.0.0.1")
