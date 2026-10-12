import copy
import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from datetime import datetime, timezone
from unittest.mock import Mock, patch

from radar.mexc_accounting import AccountingError, order_fee, fill_evidence, reconcile_position
from radar.operator_futures_engine_v02 import OperatorFuturesEngineV02
from scripts.audit_mexc_options_accounting import audit
from scripts.build_options_v21_pnl_correction_overlay_v01 import build_overlay
from radar.operator_risk_v02 import _pnl_with_overlay

ROOT = Path(__file__).parent / "fixtures/mexc_options_audit"
SESSION = next((ROOT / "operator_futures_v03").glob("*1d8a*"))


def data():
    def load(name):
        return json.loads((SESSION / name).read_text())
    active = load("ACTIVE_TRADE_STATE.json")
    entry = load("FILL_RECEIPT.json")["order"]
    exits = load("EXIT_FILL_RECEIPT.json")["orders"]
    # Synthetic settlement used to exercise the contract. This is NOT an
    # official historical-position export and is never saved as audit evidence.
    history = {"positionId": active["position_id"], "symbol": "BTC_USDT", "state": 3,
               "holdFee": "0.00667", "closeProfitLoss": "0.1586",
               "totalFee": "0.06771312", "realised": "0.09755688"}
    return active, entry, exits, history


class AccountingTests(unittest.TestCase):
    def test_eight_original_execution_records_ignore_placeholder_total(self):
        orders = []
        for p in ROOT.rglob("FILL_RECEIPT.json"):
            orders.append(json.loads(p.read_text())["order"])
        for p in ROOT.rglob("EXIT_FILL_RECEIPT.json"):
            orders.extend(json.loads(p.read_text())["orders"])
        self.assertEqual(len(orders), 8)
        for order in orders:
            self.assertEqual(order["totalFee"], 0)
            self.assertEqual(fill_evidence(order, "0.0001")["fee_usdt"], str(order_fee(order)))
            self.assertGreater(order_fee(order), 0)
            self.assertEqual(order["takerFeeRate"], 0.0008)
            self.assertEqual(order["makerFeeRate"], 0.0006)

    def test_unknown_or_nonfinite_fee_fails_closed(self):
        for order in ({}, {"totalFee": 0}, {"makerFee": 0}, {"takerFee": "NaN"},
                      {"totalFee": "Infinity"}, {"takerFee": None},
                      {"totalFee": 1, "makerFee": 0, "takerFee": 2},
                      {"takerFee": 1, "feeCurrency": "BTC"}):
            with self.subTest(order=order), self.assertRaises(AccountingError):
                order_fee(order)

    def test_signed_maker_rebate_and_zero_fee_evidence(self):
        self.assertEqual(str(order_fee({"makerFee": "-0.01", "takerFee": 0, "totalFee": 0})), "-0.01")
        self.assertEqual(order_fee({"makerFee": 0, "takerFee": 0, "totalFee": 0}), 0)
        _, entry, _, _ = data()
        entry.update(makerFee=0, takerFee=0, makerFeeRate=0, takerFeeRate=0)
        self.assertEqual(fill_evidence(entry, "0.0001")["fee_usdt"], "0")

    def test_final_funding_replaces_preclose_and_matches_exchange(self):
        active, entry, exits, history = data()
        out = reconcile_position(active=active, entry_orders=[entry], exit_orders=exits, history=history)
        self.assertEqual(out["funding_hold_fee_usdt"], 0.00667)
        self.assertEqual(out["realized_net_pnl_usdt"], 0.09755688)
        self.assertNotEqual(out["funding_hold_fee_usdt"], 0.0047)

    def test_mismatched_or_missing_exchange_evidence_blocks(self):
        for field, value in (("positionId", 123), ("state", 1), ("holdFee", None),
                             ("realised", "NaN"), ("realised", 1),
                             ("closeProfitLoss", 0), ("totalFee", 0), ("symbol", "ETH_USDT")):
            active, entry, exits, history = data()
            history[field] = value
            with self.subTest(field=field), self.assertRaises(AccountingError):
                reconcile_position(active=active, entry_orders=[entry], exit_orders=exits, history=history)

    def test_duplicate_wrong_side_partial_volume_and_mixed_fees_block(self):
        for kind in ("duplicate", "side", "volume", "mixed", "rate"):
            active, entry, exits, history = data()
            if kind == "duplicate": exits.append(copy.deepcopy(exits[0]))
            if kind == "side": exits[0]["side"] = 3
            if kind == "volume": active["volume_contracts"] = 6
            if kind == "mixed": entry["makerFee"] = "0.01"
            if kind == "rate": entry["takerFeeRate"] = "0.0002"
            with self.subTest(kind=kind), self.assertRaises(AccountingError):
                reconcile_position(active=active, entry_orders=[entry], exit_orders=exits, history=history)

    def test_audit_preserves_bytes_and_does_not_invent_missing_records(self):
        before = {p: hashlib.sha256(p.read_bytes()).hexdigest() for p in ROOT.rglob("*.json")}
        out = audit(ROOT)
        self.assertEqual(out["status"], "FAIL_CLOSED")
        self.assertEqual(out["trade_count"], 6)
        self.assertEqual(out["execution_records_available"], 8)
        self.assertTrue(all(not r["accounting_verified"] for r in out["entries"]))
        self.assertEqual(before, {p: hashlib.sha256(p.read_bytes()).hexdigest() for p in before})

    def test_runtime_does_not_release_slot_or_write_reconciled_when_history_missing(self):
        active, entry, exits, _ = data()
        active["state"] = "EXIT_PENDING"
        with tempfile.TemporaryDirectory() as td:
            session = Path(td)
            active_path = session / "ACTIVE_TRADE_STATE.json"
            active_path.write_text(json.dumps(active))
            (session / "FILL_RECEIPT.json").write_text(json.dumps({"order": entry}))
            engine = object.__new__(OperatorFuturesEngineV02)
            engine.credentials = None
            engine.global_slot = Mock()
            engine._status = lambda status, **kwargs: {"status": status, **kwargs}
            position = {"positionId": active["position_id"], "holdVol": 5, "holdFee": 0.0047}
            engine._position = Mock(side_effect=[position, position, None, None])
            engine._wait_order = Mock(return_value=exits[0])
            engine._historical_position = Mock(return_value=None)
            with patch("radar.operator_futures_engine_v02.MEXCOperatorFuturesTransportV02") as transport, patch("radar.operator_futures_engine_v02.time.sleep"):
                transport.return_value.submit_market_order.return_value = {"orderId": exits[0]["orderId"]}
                out = engine._exit_active(active_path=active_path, active=active, reason="SCHEDULED_EXIT")
            self.assertEqual(out["status"], "EXIT_RECONCILIATION_REQUIRED")
            engine.global_slot.release.assert_not_called()
            self.assertFalse((session / "POST_TRADE_RECONCILIATION.json").exists())
            self.assertTrue((session / "EXIT_FILL_RECEIPT.json").exists())
            self.assertEqual(json.loads(active_path.read_text())["state"], "EXIT_PENDING")

    def test_runtime_verified_close_uses_final_funding_and_releases_slot(self):
        active, entry, exits, history = data()
        active["state"] = "EXIT_PENDING"
        with tempfile.TemporaryDirectory() as td:
            session = Path(td)
            active_path = session / "ACTIVE_TRADE_STATE.json"
            active_path.write_text(json.dumps(active))
            (session / "FILL_RECEIPT.json").write_text(json.dumps({"order": entry}))
            engine = object.__new__(OperatorFuturesEngineV02)
            engine.credentials = None
            engine.global_slot = Mock()
            engine.global_slot.release.return_value = {"release_status": "RELEASED"}
            engine._status = lambda status, **kwargs: {"status": status, **kwargs}
            position = {"positionId": active["position_id"], "holdVol": 5, "holdFee": 0.0047}
            engine._position = Mock(side_effect=[position, position, None, None])
            engine._wait_order = Mock(return_value=exits[0])
            engine._historical_position = Mock(return_value=history)
            with patch("radar.operator_futures_engine_v02.MEXCOperatorFuturesTransportV02") as transport, patch("radar.operator_futures_engine_v02.time.sleep"):
                transport.return_value.submit_market_order.return_value = {"orderId": exits[0]["orderId"]}
                out = engine._exit_active(active_path=active_path, active=active, reason="SCHEDULED_EXIT")
            self.assertEqual(out["status"], "CLOSED_RECONCILED")
            engine.global_slot.release.assert_called_once()
            recon = json.loads((session / "POST_TRADE_RECONCILIATION.json").read_text())
            self.assertEqual(recon["funding_hold_fee_usdt"], 0.00667)
            self.assertEqual(recon["realized_net_pnl_usdt"], 0.09755688)
            self.assertTrue(recon["accounting_verified"])

    def test_complete_exchange_evidence_builds_overlay_and_risk_revalidates(self):
        active, entry, exits, history = data()
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            stored = {"signal_identity": active["signal_identity"], "realized_net_pnl_usdt": 0.09558688}
            artifacts = {"ACTIVE_TRADE_STATE.json": active, "FILL_RECEIPT.json": {"order": entry},
                         "EXIT_FILL_RECEIPT.json": {"orders": exits}, "FINAL_POSITION_HISTORY.json": {"history": history},
                         "EXIT_EXCHANGE_ACK_1.json": {"orderId": exits[0]["orderId"]},
                         "POST_TRADE_RECONCILIATION.json": stored}
            for name, payload in artifacts.items():
                (root / name).write_text(json.dumps(payload))
            catalog = {"entries": [{"signal_identity": active["signal_identity"],
                       "entry_order_id": entry["orderId"], "exit_order_id": exits[0]["orderId"],
                       "stored_net_pnl_usdt": stored["realized_net_pnl_usdt"],
                       "corrected_realized_net_pnl_usdt": float(history["realised"]),
                       "entry_fee_usdt": float(order_fee(entry)), "exit_fee_usdt": float(order_fee(exits[0]))}]}
            catalog_path = root / "catalog.json"
            catalog_path.write_text(json.dumps(catalog))
            overlay = build_overlay(catalog_path=catalog_path, receipt_root=root)
            self.assertTrue(overlay["entries"][0]["accounting_verified"])
            by_signal = {active["signal_identity"]: overlay["entries"][0]}
            pnl = _pnl_with_overlay(path=root / "POST_TRADE_RECONCILIATION.json", row=stored, overlay=by_signal)
            self.assertEqual(pnl, 0.09755688)
            history["holdFee"] = "0.0047"
            (root / "FINAL_POSITION_HISTORY.json").write_text(json.dumps({"history": history}))
            with self.assertRaises(AccountingError):
                _pnl_with_overlay(path=root / "POST_TRADE_RECONCILIATION.json", row=stored, overlay=by_signal)


if __name__ == "__main__":
    unittest.main()
