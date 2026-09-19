import json
from pathlib import Path
import tempfile
import unittest

from radar.render_sentinel import RenderSentinel, evaluate_remote_state


def healthy_payload():
    return {
        "health": "OK",
        "evidence_backend": "postgres",
        "evidence_chain_ok": True,
        "errors": {},
        "runtime_liveness": {"status": "CONTINUOUS"},
        "authenticated_exchange_api_used": False,
        "orders_created": False,
        "exchange_mutation_performed": False,
        "live_capital_enabled": False,
    }


class RenderSentinelTests(unittest.TestCase):
    def test_healthy_public_shadow_is_ok(self):
        out = evaluate_remote_state(healthy_payload())
        self.assertEqual(out["status"], "OK")
        self.assertEqual(out["hard_fail_reasons"], [])

    def test_any_remote_safety_flag_fails_closed(self):
        p = healthy_payload()
        p["orders_created"] = True
        out = evaluate_remote_state(p)
        self.assertEqual(out["status"], "REMOTE_FAIL_CLOSED")
        self.assertIn("safety_flag_true", out["hard_fail_reasons"])

    def test_recovered_gap_is_review_required_not_silently_ok(self):
        p = healthy_payload()
        p["runtime_liveness"]["status"] = "RECOVERED_GAP_REVIEW_REQUIRED"
        out = evaluate_remote_state(p)
        self.assertEqual(out["status"], "REMOTE_REVIEW_REQUIRED")

    def test_probe_persists_append_only_receipt(self):
        with tempfile.TemporaryDirectory() as td:
            def fetcher(url, timeout):
                self.assertTrue(url.endswith("/health"))
                return 200, healthy_payload()

            s = RenderSentinel(root=td, interval_seconds=300, fetcher=fetcher)
            out = s.probe_once()
            self.assertEqual(out["status"], "OK")
            self.assertTrue((Path(td) / "render_sentinel_status.json").exists())
            lines = (Path(td) / "render_sentinel_receipts.jsonl").read_text(encoding="utf-8").splitlines()
            self.assertEqual(len(lines), 1)
            persisted = json.loads(lines[0])
            self.assertEqual(persisted["receipt_sha256"], out["receipt_sha256"])

    def test_network_failure_is_remote_unreachable(self):
        with tempfile.TemporaryDirectory() as td:
            def fetcher(url, timeout):
                raise OSError("synthetic outage")

            s = RenderSentinel(root=td, interval_seconds=300, max_attempts=1, fetcher=fetcher)
            out = s.probe_once()
            self.assertEqual(out["status"], "REMOTE_UNREACHABLE")
            self.assertFalse(out["orders_created"])
            self.assertFalse(out["live_capital_enabled"])


if __name__ == "__main__":
    unittest.main()
