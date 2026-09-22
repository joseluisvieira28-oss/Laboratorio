from __future__ import annotations

import io
import json
from unittest import TestCase
from unittest.mock import patch

from radar.dls_solanafm_source_probe import (
    PROGRAMS,
    dls_solanafm_render_source_probe,
)


class _Response:
    def __init__(self, payload, status=200):
        self.status = status
        self._body = json.dumps(payload).encode()
    def __enter__(self):
        return self
    def __exit__(self, *args):
        return False
    def read(self):
        return self._body


class DLSSolanaFMRenderProbeTests(TestCase):
    def test_all_four_accessible_is_transport_only_not_source_data_pass(self):
        with patch(
            "radar.dls_solanafm_source_probe.urllib.request.urlopen",
            return_value=_Response({"data": []}),
        ):
            r = dls_solanafm_render_source_probe(timeout=1)
        self.assertEqual(len(r["accessible_protocols"]), 4)
        self.assertEqual(r["classification"], "TIME_BOUNDED_INDEXED_ROUTE_ACCESSIBLE")
        self.assertFalse(r["source_data_pass"])
        self.assertFalse(r["returns"])
        self.assertFalse(r["pnl"])
        self.assertFalse(r["market_response"])
        self.assertFalse(r["orders_created"])
        self.assertFalse(r["exchange_mutation_performed"])

    def test_http_errors_fail_closed(self):
        import urllib.error
        err = urllib.error.HTTPError(
            "https://example.invalid", 502, "bad gateway", {}, io.BytesIO(b"bad")
        )
        with patch(
            "radar.dls_solanafm_source_probe.urllib.request.urlopen",
            side_effect=err,
        ):
            r = dls_solanafm_render_source_probe(timeout=1)
        self.assertEqual(r["classification"], "INDEXED_ROUTE_ACCESS_BLOCKED")
        self.assertEqual(r["accessible_protocols"], [])
        self.assertEqual(len(r["results"]), len(PROGRAMS))
        self.assertTrue(all(x["http_status"] == 502 for x in r["results"]))


if __name__ == "__main__":
    import unittest
    unittest.main()
