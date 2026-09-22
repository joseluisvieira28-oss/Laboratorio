from __future__ import annotations

import base64
import hashlib
import json
from datetime import date, datetime, timezone
from pathlib import Path
from unittest import TestCase
from unittest.mock import patch

from radar import ced1d_render_shadow_collector_v03 as m


class CED1DRenderShadowV03Tests(TestCase):
    def test_new_boundary_is_strictly_prospective(self):
        self.assertEqual(m.FIRST_SIGNAL_DAY, date(2026, 9, 22))
        self.assertEqual(
            m.FIRST_SIGNAL_COMPLETION,
            datetime(2026, 9, 23, 0, 0, tzinfo=timezone.utc),
        )
        self.assertEqual(
            m.FIRST_ENTRY_TS,
            int(datetime(2026, 9, 23, 0, 1, tzinfo=timezone.utc).timestamp() * 1000),
        )

    def test_scientific_constants_are_unchanged(self):
        self.assertEqual(m.SYMBOL, "AVAXUSDT")
        self.assertEqual(m.TARGET, "CED1D-0031")
        self.assertEqual(m.LOOKBACK, 20)
        self.assertEqual(m.HORIZON, 1)
        self.assertEqual(m.BASE_REFERENCE_COST_BPS, 14.0)
        self.assertEqual(m.STRESS_REFERENCE_COST_BPS, 20.0)
        self.assertEqual(m.RESEARCH_NOTIONAL_USDT, 100.0)
        self.assertEqual(m.AGG_WINDOW_MS, 5000)
        self.assertEqual(m.BASE_EXEC_FEE_RT_BPS, 8.0)
        self.assertEqual(m.STRESS_EXEC_FEE_RT_BPS, 10.0)
        self.assertEqual(m.BOOKDEPTH_MAX_AGE_MS, 60000)
        self.assertEqual(m.BOOKDEPTH_BUY_PCT, 1.0)
        self.assertEqual(m.BOOKDEPTH_SELL_PCT, -1.0)
        self.assertEqual(
            m.V03_ZIP_SHA,
            "df625d0d4a05c55ba34ca51514d31fd61636ff0a823567585c2d02afa0877958",
        )

    def test_funding_transport_is_exact_official_render_validated_endpoint(self):
        self.assertEqual(m.PUBLIC_API, "https://fapi.binance.com")

    def test_public_funding_requires_markprice_but_does_not_feed_it_into_math(self):
        start = 1_800_000_000_000
        end = start + 1000
        good = [{
            "symbol": "AVAXUSDT",
            "fundingTime": start + 100,
            "fundingRate": "0.0001",
            "markPrice": "12.34",
        }]
        with patch.object(m, "fetch", return_value=json.dumps(good).encode()):
            rows, meta = m.public_funding(start, end)
        self.assertEqual(rows, [{"fundingTime": start + 100, "fundingRate": 0.0001}])
        self.assertEqual(meta["records"], 1)
        self.assertIn("https://fapi.binance.com/fapi/v1/fundingRate", meta["url"])

        bad_missing = [{
            "symbol": "AVAXUSDT",
            "fundingTime": start + 100,
            "fundingRate": "0.0001",
        }]
        with patch.object(m, "fetch", return_value=json.dumps(bad_missing).encode()):
            with self.assertRaisesRegex(m.GateError, "FUNDING_MARKPRICE_MISSING"):
                m.public_funding(start, end)

        bad_zero = [{
            "symbol": "AVAXUSDT",
            "fundingTime": start + 100,
            "fundingRate": "0.0001",
            "markPrice": "0",
        }]
        with patch.object(m, "fetch", return_value=json.dumps(bad_zero).encode()):
            with self.assertRaisesRegex(m.GateError, "FUNDING_MARKPRICE_NUMERIC"):
                m.public_funding(start, end)

    def test_pinned_runner_asset_hash_is_exact(self):
        root = Path(__file__).resolve().parents[1]
        b64 = (root / "assets" / "CED-1D-V1-RUNNER-FREEZE-V0.3.zip.b64").read_text().strip()
        raw = base64.b64decode(b64, validate=True)
        self.assertEqual(
            hashlib.sha256(raw).hexdigest(),
            "df625d0d4a05c55ba34ca51514d31fd61636ff0a823567585c2d02afa0877958",
        )

    def test_source_readiness_guard_is_preserved_in_code(self):
        source = Path(m.__file__).read_text()
        self.assertIn("if through>today-timedelta(days=3)", source)

    def test_no_trading_surfaces_are_added(self):
        source = Path(m.__file__).read_text().lower()
        for forbidden in ("create_order", "place_order", "private_key", "api_secret"):
            self.assertNotIn(forbidden, source)


if __name__ == "__main__":
    import unittest
    unittest.main()
