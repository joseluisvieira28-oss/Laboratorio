from __future__ import annotations

import hashlib
import json
import tempfile
from datetime import datetime, timezone
from pathlib import Path
import unittest

from radar.operator_risk_v02 import (
    DAILY_REALIZED_LOSS_KILL_USDT,
    MAX_INITIAL_MARGIN_USDT,
    MAX_NOTIONAL_USDT,
    REQUIRED_LEVERAGE,
    ROLLING_7D_REALIZED_LOSS_KILL_USDT,
    build_operator_risk_state,
    realized_loss_state,
)


class FakePrivate:
    def __init__(self, *, positions=None, orders=None, tpsl=None, equity=112.0, available=100.0):
        self._positions = positions or []
        self._orders = orders or []
        self._tpsl = tpsl or []
        self._equity = equity
        self._available = available

    def open_positions(self, symbol=None):
        return list(self._positions)

    def open_orders(self, symbol=None):
        return list(self._orders)

    def open_tpsl_orders(self, symbol=None):
        return list(self._tpsl)

    def assets(self):
        return [{
            "currency": "USDT",
            "equity": self._equity,
            "availableBalance": self._available,
        }]


class OperatorRiskV02Tests(unittest.TestCase):
    def test_frozen_envelope(self):
        self.assertEqual(MAX_INITIAL_MARGIN_USDT, 10.0)
        self.assertEqual(MAX_NOTIONAL_USDT, 50.0)
        self.assertEqual(REQUIRED_LEVERAGE, 5)
        self.assertEqual(DAILY_REALIZED_LOSS_KILL_USDT, 5.0)
        self.assertEqual(ROLLING_7D_REALIZED_LOSS_KILL_USDT, 5.0)

    def test_pass_when_account_is_clean(self):
        with tempfile.TemporaryDirectory() as td:
            state = build_operator_risk_state(
                private_client=FakePrivate(),
                receipt_root=td,
                now=datetime(2026, 9, 29, 12, 0, tzinfo=timezone.utc),
            )
            self.assertTrue(state["pass"])
            self.assertEqual(state["status"], "PASS")

    def test_open_position_occupies_only_slot(self):
        with tempfile.TemporaryDirectory() as td:
            state = build_operator_risk_state(
                private_client=FakePrivate(positions=[{"symbol": "BTC_USDT"}]),
                receipt_root=td,
                now=datetime(2026, 9, 29, 12, 0, tzinfo=timezone.utc),
            )
            self.assertFalse(state["pass"])
            self.assertIn("GLOBAL_POSITION_SLOT_OCCUPIED", state["blockers"])

    def test_daily_realized_loss_kill_at_5(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td) / "s"
            root.mkdir()
            (root / "POST_TRADE_RECONCILIATION.json").write_text(json.dumps({
                "closed_at_utc": "2026-09-29T10:00:00Z",
                "realized_net_pnl_usdt": -5.01,
            }), encoding="utf-8")
            state = build_operator_risk_state(
                private_client=FakePrivate(),
                receipt_root=td,
                now=datetime(2026, 9, 29, 12, 0, tzinfo=timezone.utc),
            )
            self.assertFalse(state["pass"])
            self.assertIn("DAILY_5_USDT_REALIZED_LOSS_KILL_ACTIVE", state["blockers"])

    def test_corrected_pnl_has_precedence(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td) / "s"
            root.mkdir()
            (root / "POST_TRADE_RECONCILIATION.json").write_text(json.dumps({
                "closed_at_utc": "2026-09-29T10:00:00Z",
                "realized_net_pnl_usdt": 1.0,
                "corrected_realized_net_pnl_usdt": -2.0,
            }), encoding="utf-8")
            loss = realized_loss_state(
                td,
                now=datetime(2026, 9, 29, 12, 0, tzinfo=timezone.utc),
            )
            self.assertEqual(loss["daily_realized_loss_usdt"], 2.0)


    def test_corrupt_reconciliation_fails_closed(self):
        with tempfile.TemporaryDirectory() as td:
            p = Path(td) / "POST_TRADE_RECONCILIATION.json"
            p.write_text("{", encoding="utf-8")
            state = build_operator_risk_state(
                private_client=FakePrivate(),
                receipt_root=td,
                now=datetime(2026, 9, 30, 12, 0, tzinfo=timezone.utc),
            )
            self.assertFalse(state["pass"])
            self.assertIn("LOCAL_RECONCILIATION_ACCOUNTING_INVALID", state["blockers"])

    def test_corrupt_active_state_fails_closed(self):
        with tempfile.TemporaryDirectory() as td:
            p = Path(td) / "ACTIVE_TRADE_STATE.json"
            p.write_text("{", encoding="utf-8")
            state = build_operator_risk_state(
                private_client=FakePrivate(),
                receipt_root=td,
                now=datetime(2026, 9, 30, 12, 0, tzinfo=timezone.utc),
            )
            self.assertFalse(state["pass"])
            self.assertTrue(any(x.startswith("LOCAL_ACTIVE_STATE_INVALID:") for x in state["blockers"]))

    def test_unresolved_order_intent_reserves_slot(self):
        with tempfile.TemporaryDirectory() as td:
            p = Path(td) / "ORDER_INTENT.json"
            p.write_text(json.dumps({
                "external_oid": "pending",
                "signal_identity": "synthetic",
            }), encoding="utf-8")
            state = build_operator_risk_state(
                private_client=FakePrivate(),
                receipt_root=td,
                now=datetime(2026, 9, 30, 12, 0, tzinfo=timezone.utc),
            )
            self.assertFalse(state["pass"])
            self.assertIn("GLOBAL_POSITION_SLOT_OCCUPIED", state["blockers"])
            self.assertTrue(any(x.startswith("UNRESOLVED_ORDER_INTENT_RESERVES_GLOBAL_SLOT:") for x in state["blockers"]))

    def test_nonfinite_pnl_fails_closed(self):
        with tempfile.TemporaryDirectory() as td:
            p = Path(td) / "POST_TRADE_RECONCILIATION.json"
            p.write_text(json.dumps({
                "closed_at_utc": "2026-09-30T10:00:00Z",
                "realized_net_pnl_usdt": "NaN",
            }), encoding="utf-8")
            state = build_operator_risk_state(
                private_client=FakePrivate(),
                receipt_root=td,
                now=datetime(2026, 9, 30, 12, 0, tzinfo=timezone.utc),
            )
            self.assertFalse(state["pass"])
            self.assertIn("LOCAL_RECONCILIATION_ACCOUNTING_INVALID", state["blockers"])

    def test_overlapping_roots_count_receipt_once(self):
        import os
        from unittest.mock import patch
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            child = root / "trade"
            child.mkdir()
            (child / "POST_TRADE_RECONCILIATION.json").write_text(json.dumps({
                "closed_at_utc": "2026-09-30T10:00:00Z",
                "realized_net_pnl_usdt": -3.0,
            }), encoding="utf-8")
            with patch.dict(os.environ, {"CRYPTO_LAB_EXTERNAL_RECEIPT_ROOTS": str(child)}):
                loss = realized_loss_state(
                    root,
                    now=datetime(2026, 9, 30, 12, 0, tzinfo=timezone.utc),
                )
            self.assertEqual(loss["daily_realized_loss_usdt"], 3.0)


    def test_hash_bound_correction_overlay_changes_loss_without_mutating_receipt(self):
        import os
        from unittest.mock import patch
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            receipt = root / "POST_TRADE_RECONCILIATION.json"
            original = {
                "signal_identity": "OPTIONS-SPOTPERP-001:V2.1:2026-09-28",
                "closed_at_utc": "2026-09-30T00:00:06Z",
                "realized_net_pnl_usdt": -0.01696,
            }
            receipt.write_text(json.dumps(original, sort_keys=True), encoding="utf-8")
            digest = hashlib.sha256(receipt.read_bytes()).hexdigest()
            overlay = root / "overlay.json"
            overlay.write_text(json.dumps({
                "entries": [{
                    "signal_identity": original["signal_identity"],
                    "original_receipt_sha256": digest,
                    "stored_net_pnl_usdt": -0.01696,
                    "corrected_realized_net_pnl_usdt": -0.03032779,
                }]
            }), encoding="utf-8")
            before = receipt.read_bytes()
            with patch.dict(os.environ, {"CRYPTO_LAB_PNL_CORRECTION_OVERLAY": str(overlay)}):
                loss = realized_loss_state(
                    root,
                    now=datetime(2026, 9, 30, 12, 0, tzinfo=timezone.utc),
                )
            self.assertAlmostEqual(loss["daily_realized_loss_usdt"], 0.03032779)
            self.assertEqual(receipt.read_bytes(), before)

    def test_correction_overlay_hash_mismatch_fails_closed(self):
        import os
        from unittest.mock import patch
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            receipt = root / "POST_TRADE_RECONCILIATION.json"
            receipt.write_text(json.dumps({
                "signal_identity": "OPTIONS-SPOTPERP-001:V2.1:2026-09-28",
                "closed_at_utc": "2026-09-30T00:00:06Z",
                "realized_net_pnl_usdt": -0.01696,
            }), encoding="utf-8")
            overlay = root / "overlay.json"
            overlay.write_text(json.dumps({
                "entries": [{
                    "signal_identity": "OPTIONS-SPOTPERP-001:V2.1:2026-09-28",
                    "original_receipt_sha256": "0" * 64,
                    "stored_net_pnl_usdt": -0.01696,
                    "corrected_realized_net_pnl_usdt": -0.03032779,
                }]
            }), encoding="utf-8")
            with patch.dict(os.environ, {"CRYPTO_LAB_PNL_CORRECTION_OVERLAY": str(overlay)}):
                state = build_operator_risk_state(
                    private_client=FakePrivate(),
                    receipt_root=root,
                    now=datetime(2026, 9, 30, 12, 0, tzinfo=timezone.utc),
                )
            self.assertFalse(state["pass"])
            self.assertIn("LOCAL_RECONCILIATION_ACCOUNTING_INVALID", state["blockers"])


    def test_open_tpsl_order_blocks_global_slot_clean_state(self):
        with tempfile.TemporaryDirectory() as td:
            state = build_operator_risk_state(
                private_client=FakePrivate(tpsl=[{
                    "id": 123,
                    "positionId": 77,
                    "state": 1,
                    "symbol": "BTC_USDT",
                }]),
                receipt_root=td,
                now=datetime(2026, 9, 30, 12, 0, tzinfo=timezone.utc),
            )
            self.assertFalse(state["pass"])
            self.assertIn("GLOBAL_OPEN_TPSL_ORDER_PRESENT", state["blockers"])
            self.assertEqual(state["exchange_open_tpsl_order_count"], 1)


if __name__ == "__main__":
    unittest.main()
