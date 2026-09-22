from __future__ import annotations

import json
import unittest
from unittest.mock import patch

from radar.ced1d_source_probe import (
    END_MS,
    HOSTS,
    START_MS,
    SYMBOL,
    _validate_payload,
    ced1d_render_source_probe,
)


class CED1DRenderSourceProbeTests(unittest.TestCase):
    def test_exact_schema_validation(self):
        ok, n = _validate_payload([
            {"symbol": SYMBOL, "fundingTime": START_MS, "fundingRate": "0.0001", "markPrice": "100.0"},
            {"symbol": SYMBOL, "fundingTime": END_MS, "fundingRate": "-0.0002", "markPrice": "101.0"},
        ])
        self.assertTrue(ok)
        self.assertEqual(n, 2)

        self.assertFalse(_validate_payload([])[0])
        self.assertFalse(_validate_payload([{"symbol": SYMBOL}])[0])
        self.assertFalse(_validate_payload([
            {"symbol": SYMBOL, "fundingTime": START_MS, "fundingRate": "0.1", "markPrice": "0"}
        ])[0])
        self.assertFalse(_validate_payload([
            {"symbol": SYMBOL, "fundingTime": START_MS, "fundingRate": "0.1"}
        ])[0])
        self.assertFalse(_validate_payload([
            {"symbol": "BTCUSDT", "fundingTime": START_MS, "fundingRate": "0.1", "markPrice": "100"}
        ])[0])

    def test_aggregate_pass_requires_exact_schema_winner(self):
        side_effect = []
        for i, host in enumerate(HOSTS):
            side_effect.append({
                "host": host,
                "endpoint": "/fapi/v1/fundingRate",
                "http_status": 200 if i == 2 else 451,
                "schema_pass": i == 2,
                "row_count": 3 if i == 2 else None,
            })
        with patch("radar.ced1d_source_probe.probe_host", side_effect=side_effect):
            result = ced1d_render_source_probe()
        self.assertEqual(result["classification"], "OFFICIAL_ENDPOINT_EXACT_SCHEMA_PASS")
        self.assertEqual(result["accessible_exact_schema_hosts"], [HOSTS[2]])
        self.assertFalse(result["used_as_forward_evidence"])
        self.assertFalse(result["collector_adoption_authorized"])
        self.assertFalse(result["orders_created"])

    def test_all_blocked_remains_fail_closed(self):
        with patch(
            "radar.ced1d_source_probe.probe_host",
            side_effect=[
                {
                    "host": host,
                    "endpoint": "/fapi/v1/fundingRate",
                    "http_status": 202,
                    "schema_pass": False,
                    "row_count": None,
                }
                for host in HOSTS
            ],
        ):
            result = ced1d_render_source_probe()
        self.assertEqual(result["classification"], "OFFICIAL_ENDPOINT_EXACT_SCHEMA_BLOCKED")
        self.assertEqual(result["accessible_exact_schema_hosts"], [])


if __name__ == "__main__":
    unittest.main()
