"""Offline regression suite for cost-neutral, one-way Telegram Radar alarms."""
import io
import os
import unittest
from unittest.mock import patch
from datetime import datetime, timedelta, timezone
from urllib.error import HTTPError
from urllib.request import Request

from radar_telegram_health_v01 import (
    RADAR_URL, classify_snapshot, inspect_remote, send_telegram, _message
)

NOW = datetime(2026, 10, 10, 14, 0, tzinfo=timezone.utc)


def valid_state():
    return {
        "mode": "PUBLIC_SHADOW_ONLY",
        "health": "OK",
        "checked_at_utc": NOW.isoformat().replace("+00:00", "Z"),
        "runtime_identity": {"service_id": "srv-dalqkpu1egvs73fhiehg"},
        "ced1d_render_shadow": {"status": "OK"},
        "runtime_gap_history": {
            "continuity_review_status": "NO_PERSISTED_GAPS",
            "persisted_gap_receipts": 0,
        },
        "orders_created": False,
        "authenticated_exchange_api_used": False,
        "exchange_mutation_performed": False,
        "live_capital_enabled": False,
    }


class FakeResponse:
    def __init__(self, text=b'{"ok": true}', url=None):
        self.text, self.url = text, url

    def __enter__(self):
        return self

    def __exit__(self, *unused):
        return False

    def read(self, max_bytes=None):
        return self.text[:max_bytes]

    def geturl(self):
        return self.url or RADAR_URL


class TelegramHealthTests(unittest.TestCase):
    def test_valid_snapshot_silent(self):
        r = classify_snapshot(valid_state(), now=NOW)
        self.assertEqual(r["status"], "OK")
        self.assertFalse(r["notify"])

    def test_failed_ced_visible_even_when_global_health_ok(self):
        state = valid_state()
        state["ced1d_render_shadow"]["status"] = "FAIL_CLOSED"
        self.assertIn("CED1D_COLLECTOR_FAIL_CLOSED_OR_UNVERIFIED",
                      classify_snapshot(state, now=NOW)["reason_codes"])

    def test_unreviewed_gaps_alert_without_retroactive_continuity(self):
        state = valid_state()
        state["runtime_gap_history"]["continuity_review_status"] = "HISTORICAL_GAPS_REVIEW_REQUIRED"
        self.assertTrue(classify_snapshot(state, now=NOW)["notify"])

    def test_legacy_unverified_history_is_not_green(self):
        state = valid_state()
        del state["runtime_gap_history"]
        self.assertIn("CONTINUITY_REVIEW_UNVERIFIED",
                      classify_snapshot(state, now=NOW)["reason_codes"])

    def test_stale_and_future_timestamp_block(self):
        for minutes in (-30, 5):
            state = valid_state()
            state["checked_at_utc"] = (NOW + timedelta(minutes=minutes)).isoformat()
            self.assertIn("SOURCE_STATE_STALE_OR_FUTURE",
                          classify_snapshot(state, now=NOW)["reason_codes"])

    def test_identity_and_safety_flags_fails_closed(self):
        state = valid_state()
        state["runtime_identity"]["service_id"] = "wrong-service"
        state["orders_created"] = True
        r = classify_snapshot(state, now=NOW)
        self.assertIn("CANONICAL_RUNTIME_IDENTITY_UNVERIFIED", r["reason_codes"])
        self.assertIn("SHADOW_SAFETY_FLAGS_UNVERIFIED", r["reason_codes"])

    def test_alert_fingerprint_is_repeatable_and_daily_bounded(self):
        same1 = classify_snapshot(None, now=NOW)
        same2 = classify_snapshot(None, now=NOW)
        nextday = classify_snapshot(None, now=NOW + timedelta(days=1))
        self.assertEqual(same1["incident_key"], same2["incident_key"])
        self.assertNotEqual(same1["incident_key"], nextday["incident_key"])

    def test_wrong_remote_origin_never_accessed(self):
        r = inspect_remote(url="http://127.0.0.1:8000/private", timeout=1, now=NOW)
        self.assertIn("PUBLIC_RADAR_UNREACHABLE_BAD_CONFIGURED_URL", r["reason_codes"])

    def test_503_json_still_classified_safely(self):
        state = valid_state()
        state["health"] = "DEGRADED_FAIL_CLOSED"
        data = __import__("json").dumps(state).encode()
        exc = HTTPError(RADAR_URL, 503, "Service Unavailable", {}, io.BytesIO(data))
        with patch("radar_telegram_health_v01.urlopen", side_effect=exc):
            r = inspect_remote(url=RADAR_URL, timeout=1, now=NOW)
        self.assertIn("PUBLIC_SHADOW_HEALTH_NOT_OK", r["reason_codes"])

    def test_missing_telegram_secret_cannot_send(self):
        with patch.dict(os.environ, {"TELEGRAM_BOT_TOKEN": "", "TELEGRAM_CHAT_ID": ""}):
            self.assertEqual(send_telegram({"status": "DEGRADED"}), "NOT_CONFIGURED")

    def test_mocked_send_only_no_secret_in_message(self):
        token = "123456789:" + "A" * 32
        def opener(req: Request, timeout):
            self.assertIn("/sendMessage", req.full_url)
            self.assertNotIn(token, _message({"utc_date": "2026-10-10",
                                                "status": "DEGRADED",
                                                "reason_codes": ["NO_VALID_JSON_STATE"]}))
            self.assertEqual(req.get_method(), "POST")
            return FakeResponse(b'{"ok":true}')
        with patch.dict(os.environ, {"TELEGRAM_BOT_TOKEN": token, "TELEGRAM_CHAT_ID": "-1001234567890"}):
            self.assertEqual(send_telegram({"utc_date": "2026-10-10",
                                            "status": "DEGRADED",
                                            "reason_codes": ["NO_VALID_JSON_STATE"]},
                                           opener=opener), "SENT")

    def test_http_error_does_not_reveal_token(self):
        token = "123456789:" + "A" * 32
        def opener(req, timeout):
            raise HTTPError(req.full_url, 403, "Forbidden", {}, None)
        with patch.dict(os.environ, {"TELEGRAM_BOT_TOKEN": token, "TELEGRAM_CHAT_ID": "-1001234567890"}):
            status = send_telegram({"utc_date": "2026-10-10"}, opener=opener)
            self.assertEqual(status, "HTTP_403")
            self.assertNotIn(token, status)


if __name__ == "__main__":
    unittest.main()
