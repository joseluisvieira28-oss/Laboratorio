from __future__ import annotations

import json
import unittest
from unittest.mock import patch
from urllib.error import URLError

from radar.strategies.tfg_donchian_regime_forward import MEXCSpotKlineFeed, TFGSourceError


class _Response:
    status = 200
    def __enter__(self):
        return self
    def __exit__(self, exc_type, exc, tb):
        return False
    def read(self):
        return json.dumps([]).encode("utf-8")


class MEXCTransportRetryTests(unittest.TestCase):
    def test_transient_transport_failure_retries_then_succeeds(self):
        feed = MEXCSpotKlineFeed(timeout=1, max_attempts=3, retry_backoff_seconds=0)
        calls = {"n": 0}

        def fake_urlopen(*args, **kwargs):
            calls["n"] += 1
            if calls["n"] == 1:
                raise URLError("synthetic tls reset")
            return _Response()

        with patch(
            "radar.strategies.tfg_donchian_regime_forward.urlopen",
            side_effect=fake_urlopen,
        ):
            self.assertEqual(feed._get_json({"symbol": "BTCUSDT"}), [])
        self.assertEqual(calls["n"], 2)

    def test_persistent_transport_failure_remains_fail_closed(self):
        feed = MEXCSpotKlineFeed(timeout=1, max_attempts=3, retry_backoff_seconds=0)
        with patch(
            "radar.strategies.tfg_donchian_regime_forward.urlopen",
            side_effect=URLError("synthetic persistent tls failure"),
        ):
            with self.assertRaisesRegex(TFGSourceError, "after 3 attempts"):
                feed._get_json({"symbol": "BTCUSDT"})


if __name__ == "__main__":
    unittest.main()
