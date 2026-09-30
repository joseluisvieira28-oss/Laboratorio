from __future__ import annotations

from datetime import datetime, timedelta, timezone
import json
from pathlib import Path
from types import SimpleNamespace
import tempfile
import unittest

from radar.operator_futures_engine_v02 import (
    OperatorEngineError,
    OperatorFuturesEngineV02,
    compute_contract_volume,
    order_fee_usdt,
    timing_state,
    protective_prices,
)


class _ProtectionReadOnly:
    def __init__(self, *, open_tpsl=None, historical=None, finished_tpsl=None):
        self._open_tpsl = open_tpsl or []
        self._historical = historical or []
        self._finished_tpsl = finished_tpsl or []

    def open_tpsl_orders(self, symbol=None):
        return list(self._open_tpsl)

    def historical_positions(self, **kwargs):
        return list(self._historical)

    def tpsl_orders(self, **kwargs):
        return list(self._finished_tpsl)


class _Slot:
    def __init__(self):
        self.releases = []

    def release(self, *, signal_identity, reason):
        self.releases.append((signal_identity, reason))
        return {
            "release_status": "RELEASED",
            "signal_identity": signal_identity,
            "reason": reason,
        }




class _EntryGateReadOnly:
    def open_positions(self, symbol=None):
        return []

    def open_orders(self, symbol=None):
        return []

    def open_tpsl_orders(self, symbol=None):
        return []

    def assets(self):
        return [{"currency": "USDT", "equity": 100.0, "availableBalance": 100.0}]

    def position_mode(self):
        return 1

    def fee_details(self, symbol):
        return {"realTakerFee": 0.0005}


class _EntryGatePublic:
    def contract_row(self, symbol):
        return {
            "apiAllowed": True,
            "state": 0,
            "futureType": 1,
            "contractSize": 0.01,
            "minVol": 1,
            "volUnit": 1,
            "priceUnit": 0.1,
        }

    def all_market_snapshots(self):
        return {
            "BNBUSDT": SimpleNamespace(
                last_price=100.0,
                bid_price=99.99,
                ask_price=100.01,
            )
        }

    def funding_rate(self, symbol):
        return {"fundingRate": 0.0, "collectCycle": 8}


class _ManagingSlot(_Slot):
    def claim(self, **kwargs):
        return {"claim_status": "RECOVERED_EXISTING_OWNER", **kwargs}


class OperatorFuturesEngineV02Tests(unittest.TestCase):
    def test_zero_total_fee_falls_back_to_taker_fee(self):
        self.assertAlmostEqual(
            order_fee_usdt({"totalFee": 0, "takerFee": 0.0067, "makerFee": 0}),
            0.0067,
            places=10,
        )

    def test_positive_total_fee_has_precedence(self):
        self.assertAlmostEqual(
            order_fee_usdt({"totalFee": 0.01, "takerFee": 0.006, "makerFee": 0.004}),
            0.01,
            places=10,
        )

    def test_50_notional_maps_to_10_margin_at_5x(self):
        out = compute_contract_volume(
            target_notional_usdt=50.0,
            price=100.0,
            contract_size=0.01,
            min_vol=1,
            vol_unit=1,
        )
        self.assertEqual(out["volume_contracts"], 50)
        self.assertAlmostEqual(out["estimated_notional_usdt"], 50.0)
        self.assertAlmostEqual(out["estimated_initial_margin_usdt"], 10.0)

    def test_sizing_never_rounds_above_cap(self):
        out = compute_contract_volume(
            target_notional_usdt=50.0,
            price=123.0,
            contract_size=0.01,
            min_vol=1,
            vol_unit=1,
        )
        self.assertLessEqual(out["estimated_notional_usdt"], 50.0)

    def test_non_5x_sizing_is_rejected(self):
        with self.assertRaises(OperatorEngineError):
            compute_contract_volume(
                target_notional_usdt=10,
                price=100,
                contract_size=0.01,
                min_vol=1,
                vol_unit=1,
                leverage=1,
            )

    def test_timing_no_chase(self):
        target = datetime(2026, 9, 29, 12, 0, tzinfo=timezone.utc)
        self.assertEqual(
            timing_state(
                now=datetime(2026, 9, 29, 11, 59, 59, tzinfo=timezone.utc),
                entry_target=target,
                max_late_seconds=2,
            ),
            "WAITING",
        )
        self.assertEqual(
            timing_state(
                now=datetime(2026, 9, 29, 12, 0, 1, tzinfo=timezone.utc),
                entry_target=target,
                max_late_seconds=2,
            ),
            "DUE",
        )
        self.assertEqual(
            timing_state(
                now=datetime(2026, 9, 29, 12, 0, 3, tzinfo=timezone.utc),
                entry_target=target,
                max_late_seconds=2,
            ),
            "MISSED_NO_CHASE",
        )


    def test_protective_prices_round_conservatively_for_long(self):
        out = protective_prices(
            entry_price=100.0,
            direction="LONG",
            stop_distance_fraction=0.051,
            take_profit_distance_fraction=0.153,
            price_unit=0.1,
        )
        self.assertEqual(out["stop_loss_price"], 94.9)
        self.assertEqual(out["take_profit_price"], 115.3)

    def test_protective_prices_round_conservatively_for_short(self):
        out = protective_prices(
            entry_price=100.0,
            direction="SHORT",
            stop_distance_fraction=0.051,
            take_profit_distance_fraction=0.153,
            price_unit=0.1,
        )
        self.assertEqual(out["stop_loss_price"], 105.1)
        self.assertEqual(out["take_profit_price"], 84.7)


    def _bare_engine(self, td, readonly):
        engine = object.__new__(OperatorFuturesEngineV02)
        engine.readonly = readonly
        engine.global_slot = _Slot()
        engine.status_path = Path(td) / "status.json"
        return engine

    def test_restart_verifies_existing_exchange_hosted_protection(self):
        with tempfile.TemporaryDirectory() as td:
            readonly = _ProtectionReadOnly(open_tpsl=[{
                "id": 456,
                "positionId": 77,
                "state": 1,
                "stopLossPrice": 95.0,
                "takeProfitPrice": 115.0,
            }])
            engine = self._bare_engine(td, readonly)
            active = {
                "symbol": "BTC_USDT",
                "position_id": 77,
                "protective_tpsl_order_id": 456,
                "protective_price_unit": 0.1,
                "protective_stop_loss_price": 95.0,
                "protective_take_profit_price": 115.0,
            }
            row = engine._verify_active_protection(active=active)
            self.assertEqual(row["id"], 456)

    def test_restart_fails_closed_when_exchange_protection_missing(self):
        with tempfile.TemporaryDirectory() as td:
            engine = self._bare_engine(td, _ProtectionReadOnly(open_tpsl=[]))
            active = {
                "symbol": "BTC_USDT",
                "position_id": 77,
                "protective_tpsl_order_id": 456,
                "protective_price_unit": 0.1,
                "protective_stop_loss_price": 95.0,
                "protective_take_profit_price": 115.0,
            }
            with self.assertRaises(OperatorEngineError):
                engine._verify_active_protection(active=active)

    def test_protected_stop_close_reconciles_and_releases_global_slot(self):
        with tempfile.TemporaryDirectory() as td:
            session = Path(td) / "trade"
            session.mkdir()
            active_path = session / "ACTIVE_TRADE_STATE.json"
            active = {
                "state": "EXIT_PENDING",
                "candidate_id": "HTF-DH03-12H-STANDALONE-FORWARD-V1",
                "strategy_id": "HTF-DH03-12H-STANDALONE-FORWARD-V1",
                "signal_identity": "DH03:BTC:1",
                "symbol": "BTC_USDT",
                "direction": "LONG",
                "position_id": 77,
                "opened_at_utc": "2026-09-30T10:00:00Z",
                "entry_target_utc": "2026-09-30T10:00:00Z",
                "entry_fee_usdt": 0.08,
                "entry_price": 100.0,
                "planned_notional_usdt": 50.0,
                "planned_initial_margin_usdt": 10.0,
                "protective_tpsl_order_id": 456,
            }
            active_path.write_text(json.dumps(active), encoding="utf-8")
            hist = {
                "positionId": 77,
                "state": 3,
                "closeProfitLoss": 1.0,
                "holdFee": -0.1,
                "totalFee": 0.2,
                "realised": 0.7,
                "closeAvgPrice": 95.0,
            }
            finished = {
                "id": 456,
                "positionId": 77,
                "state": 3,
                "triggerSide": 2,
            }
            engine = self._bare_engine(
                td,
                _ProtectionReadOnly(
                    historical=[hist],
                    finished_tpsl=[finished],
                ),
            )
            out = engine._reconcile_protected_exchange_close(
                active_path=active_path,
                active=active,
                now=datetime(2026, 9, 30, 10, 5, tzinfo=timezone.utc),
            )
            self.assertEqual(out["status"], "CLOSED_RECONCILED")
            self.assertEqual(out["exit_reason"], "MEXC_STOP_LOSS_TRIGGER")
            self.assertAlmostEqual(out["realized_net_pnl_usdt"], 0.7)
            self.assertEqual(
                engine.global_slot.releases,
                [("DH03:BTC:1", "POST_TRADE_RECONCILIATION_CONFIRMED")],
            )
            recon = json.loads(
                (session / "POST_TRADE_RECONCILIATION.json").read_text(
                    encoding="utf-8"
                )
            )
            self.assertAlmostEqual(recon["entry_fee_usdt"], 0.08)
            self.assertAlmostEqual(recon["exit_fee_usdt"], 0.12)
            self.assertFalse(recon["open_position_after_reconciliation"])

    def test_protected_close_accounting_identity_mismatch_keeps_slot_reserved(self):
        with tempfile.TemporaryDirectory() as td:
            session = Path(td) / "trade"
            session.mkdir()
            active_path = session / "ACTIVE_TRADE_STATE.json"
            active = {
                "state": "EXIT_PENDING",
                "candidate_id": "HTF-DH03-12H-STANDALONE-FORWARD-V1",
                "strategy_id": "HTF-DH03-12H-STANDALONE-FORWARD-V1",
                "signal_identity": "DH03:BTC:2",
                "symbol": "BTC_USDT",
                "direction": "LONG",
                "position_id": 88,
                "opened_at_utc": "2026-09-30T10:00:00Z",
                "entry_target_utc": "2026-09-30T10:00:00Z",
                "entry_fee_usdt": 0.08,
                "entry_price": 100.0,
                "planned_notional_usdt": 50.0,
                "planned_initial_margin_usdt": 10.0,
                "protective_tpsl_order_id": 999,
            }
            active_path.write_text(json.dumps(active), encoding="utf-8")
            engine = self._bare_engine(
                td,
                _ProtectionReadOnly(
                    historical=[{
                        "positionId": 88,
                        "state": 3,
                        "closeProfitLoss": -1.0,
                        "holdFee": -0.1,
                        "totalFee": 0.2,
                        "realised": 123.0,
                        "closeAvgPrice": 95.0,
                    }],
                    finished_tpsl=[{
                        "id": 999,
                        "positionId": 88,
                        "state": 3,
                        "triggerSide": 2,
                    }],
                ),
            )
            out = engine._reconcile_protected_exchange_close(
                active_path=active_path,
                active=active,
                now=datetime(2026, 9, 30, 10, 5, tzinfo=timezone.utc),
            )
            self.assertEqual(out["status"], "PROTECTED_EXIT_RECONCILIATION_REQUIRED")
            self.assertEqual(engine.global_slot.releases, [])
            self.assertFalse(
                (session / "POST_TRADE_RECONCILIATION.json").exists()
            )



    def test_entry_gate_for_clean_bnb_signal_has_no_active_state_dependency(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            armed = root / "ARMED.json"
            armed.write_text("{}", encoding="utf-8")
            engine = object.__new__(OperatorFuturesEngineV02)
            engine.receipt_root = root / "receipts"
            engine.receipt_root.mkdir()
            engine.armed_path = armed
            engine.kill_switch_path = root / "KILL"
            engine.status_path = root / "status.json"
            engine.readonly = _EntryGateReadOnly()
            engine.public = _EntryGatePublic()
            engine._clock_gate = lambda: {
                "pass": True,
                "server_minus_local_midpoint_ms": 0.0,
                "request_rtt_ms": 1.0,
                "max_abs_offset_ms": 500.0,
            }
            now = datetime.now(timezone.utc)
            signal = {
                "candidate_id": "BNB-LAUNCHPOOL-DEMAND-001",
                "strategy_id": "BNB-LAUNCHPOOL-DEMAND-001",
                "immutable_signal_key": "BNB:test",
                "symbol": "BNB_USDT",
                "direction": "LONG",
                "entry_target_utc": (now - timedelta(seconds=0.5)).isoformat().replace("+00:00", "Z"),
                "exit_target_utc": (now + timedelta(hours=24)).isoformat().replace("+00:00", "Z"),
                "max_late_seconds": 2.0,
                "max_initial_margin_usdt": 10.0,
                "max_notional_usdt": 50.0,
                "max_projected_roundtrip_friction_bps": 30.0,
            }
            gate = engine._entry_gate(signal, now=now)
            self.assertTrue(gate["pass"], gate["blockers"])

    def test_manage_active_verifies_exchange_protection_before_waiting(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            session = root / "receipts" / "trade"
            session.mkdir(parents=True)
            active = {
                "state": "EXIT_PENDING",
                "candidate_id": "HTF-DH03-12H-STANDALONE-FORWARD-V1",
                "strategy_id": "HTF-DH03-12H-STANDALONE-FORWARD-V1",
                "signal_identity": "DH03:BTC:test",
                "symbol": "BTC_USDT",
                "direction": "LONG",
                "position_id": 77,
                "entry_external_oid": "op2-ent-test",
                "entry_target_utc": "2026-09-30T10:00:00Z",
                "exit_target_utc": "2026-10-01T10:00:00Z",
                "protective_tpsl_required": True,
                "protective_tpsl_order_id": 456,
                "protective_price_unit": 0.1,
                "protective_stop_loss_price": 95.0,
                "protective_take_profit_price": 115.0,
            }
            active_path = session / "ACTIVE_TRADE_STATE.json"
            active_path.write_text(json.dumps(active), encoding="utf-8")

            engine = object.__new__(OperatorFuturesEngineV02)
            engine.receipt_root = root / "receipts"
            engine.status_path = root / "status.json"
            engine.kill_switch_path = root / "KILL"
            engine.global_slot = _ManagingSlot()
            engine._position = lambda **kwargs: {
                "positionId": 77,
                "openType": 1,
                "leverage": 5,
                "autoAddIm": False,
                "holdVol": 1,
            }
            engine._verify_active_protection = (
                lambda **kwargs: (_ for _ in ()).throw(
                    OperatorEngineError("synthetic missing protection")
                )
            )
            seen = {}
            def fake_exit_active(*, active_path, active, reason):
                seen["reason"] = reason
                return {"status": "EXIT_REQUESTED", "reason": reason}
            engine._exit_active = fake_exit_active

            out = engine.manage_active()
            self.assertEqual(out["status"], "EXIT_REQUESTED")
            self.assertEqual(seen["reason"], "ACTIVE_PROTECTIVE_TPSL_NOT_VERIFIED")
            persisted = json.loads(active_path.read_text(encoding="utf-8"))
            self.assertTrue(persisted["execution_failure"])
            self.assertIn("protective_tpsl_runtime_error", persisted)


if __name__ == "__main__":
    unittest.main()
