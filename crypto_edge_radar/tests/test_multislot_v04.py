from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
import json
import tempfile
import unittest

from radar.multi_slot_reservation_v04 import MultiSlotReservationV04, MultiSlotReservationError
from radar.global_fishing_dispatcher_v04 import arbitrate_due_signals_multislot
from radar.multislot_shadow_capacity_v04 import evaluate_shadow_capacity
from radar.multislot_shadow_lifecycle_v04 import MultiSlotShadowLifecycleV04


POLICY = {
    "capacity": {"max_simultaneous_positions": 3},
    "global_risk": {
        "max_total_notional_usdt": 30,
        "max_total_initial_margin_usdt": 14,
        "daily_realized_loss_kill_usdt": 5,
        "rolling_7d_realized_loss_kill_usdt": 5,
    },
    "lanes": {
        "OPTIONS": {
            "symbol_policy": ["BTC_USDT"],
            "leverage": 1,
            "max_notional_usdt": 10,
            "max_initial_margin_usdt": 10,
            "max_positions": 1,
        },
        "BNB": {
            "symbol_policy": ["BNB_USDT"],
            "leverage": 5,
            "max_notional_usdt": 10,
            "max_initial_margin_usdt": 2,
            "max_positions": 1,
        },
        "DH03": {
            "symbol_policy": ["SOL_USDT", "XRP_USDT", "DOGE_USDT"],
            "leverage": 5,
            "max_notional_usdt": 10,
            "max_initial_margin_usdt": 2,
            "max_positions": 3,
        },
    },
}


class ReservationV04Tests(unittest.TestCase):
    def _claim(self, ledger, n, symbol):
        return ledger.claim(
            candidate_id="DH03",
            signal_identity=f"sig-{n}",
            external_oid=f"oid-{n}",
            symbol=symbol,
            leverage=5,
            max_notional_usdt=10,
            max_initial_margin_usdt=2,
        )

    def test_three_claims_then_full(self):
        with tempfile.TemporaryDirectory() as td:
            ledger = MultiSlotReservationV04(Path(td) / "ledger.json", capacity=3)
            self.assertEqual(self._claim(ledger, 1, "SOL_USDT")["claim_status"], "CLAIMED")
            self.assertEqual(self._claim(ledger, 2, "XRP_USDT")["claim_status"], "CLAIMED")
            self.assertEqual(self._claim(ledger, 3, "DOGE_USDT")["claim_status"], "CLAIMED")
            self.assertEqual(self._claim(ledger, 4, "BTC_USDT")["claim_status"], "CAPACITY_FULL")
            self.assertEqual(len(ledger.current()["reservations"]), 3)

    def test_same_symbol_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            ledger = MultiSlotReservationV04(Path(td) / "ledger.json", capacity=3)
            self._claim(ledger, 1, "SOL_USDT")
            self.assertEqual(self._claim(ledger, 2, "SOL_USDT")["claim_status"], "SYMBOL_OCCUPIED")

    def test_release_reopens_capacity(self):
        with tempfile.TemporaryDirectory() as td:
            ledger = MultiSlotReservationV04(Path(td) / "ledger.json", capacity=3)
            self._claim(ledger, 1, "SOL_USDT")
            out = ledger.release(
                signal_identity="sig-1",
                reason="POST_TRADE_RECONCILIATION_CONFIRMED",
            )
            self.assertEqual(out["release_status"], "RELEASED")
            self.assertEqual(len(ledger.current()["reservations"]), 0)

    def test_lock_left_by_crash_fails_closed(self):
        with tempfile.TemporaryDirectory() as td:
            ledger = MultiSlotReservationV04(Path(td) / "ledger.json", capacity=3)
            ledger.lock_path.write_text("synthetic crash", encoding="utf-8")
            with self.assertRaises(MultiSlotReservationError):
                self._claim(ledger, 1, "SOL_USDT")


class DispatcherV04Tests(unittest.TestCase):
    def _sig(self, candidate, key, symbol):
        return {
            "candidate_id": candidate,
            "immutable_signal_key": key,
            "symbol": symbol,
            "entry_target_utc": "2026-10-02T10:00:00Z",
            "max_late_seconds": 5,
        }

    def test_three_due_signals_can_win(self):
        now = datetime(2026, 10, 2, 10, 0, 2, tzinfo=timezone.utc)
        out = arbitrate_due_signals_multislot(
            [
                self._sig("OPTIONS", "o", "BTC_USDT"),
                self._sig("BNB", "b", "BNB_USDT"),
                self._sig("DH03", "d", "SOL_USDT"),
            ],
            now=now,
            active_reservations=[],
            capacity=3,
            lane_caps={"OPTIONS": 1, "BNB": 1, "DH03": 3},
        )
        self.assertEqual(out["winner_count"], 3)

    def test_fourth_due_signal_is_capacity_no_chase(self):
        now = datetime(2026, 10, 2, 10, 0, 2, tzinfo=timezone.utc)
        out = arbitrate_due_signals_multislot(
            [
                self._sig("OPTIONS", "o", "BTC_USDT"),
                self._sig("BNB", "b", "BNB_USDT"),
                self._sig("DH03", "d1", "SOL_USDT"),
                self._sig("DH03", "d2", "XRP_USDT"),
            ],
            now=now,
            active_reservations=[],
            capacity=3,
            lane_caps={"OPTIONS": 1, "BNB": 1, "DH03": 3},
        )
        self.assertEqual(out["winner_count"], 3)
        self.assertIn("MISSED_CAPACITY_NO_CHASE", {x["reason"] for x in out["losers"]})

    def test_active_symbol_conflict_is_no_chase(self):
        now = datetime(2026, 10, 2, 10, 0, 2, tzinfo=timezone.utc)
        out = arbitrate_due_signals_multislot(
            [self._sig("DH03", "d", "BTC_USDT")],
            now=now,
            active_reservations=[{"candidate_id": "OPTIONS", "symbol": "BTC_USDT"}],
            capacity=3,
            lane_caps={"OPTIONS": 1, "BNB": 1, "DH03": 3},
        )
        self.assertEqual(out["winner_count"], 0)
        self.assertEqual(out["losers"][0]["reason"], "MISSED_SYMBOL_CONFLICT_NO_CHASE")


class ShadowCapacityV04Tests(unittest.TestCase):
    def _candidate(self, lane, symbol, lev, notional, margin):
        return {
            "candidate_id": lane,
            "symbol": symbol,
            "leverage": lev,
            "max_notional_usdt": notional,
            "max_initial_margin_usdt": margin,
        }

    def test_three_small_positions_fit(self):
        existing = [
            {
                "candidate_id": "OPTIONS",
                "signal_identity": "o",
                "symbol": "BTC_USDT",
                "estimated_notional_usdt": 10,
                "estimated_initial_margin_usdt": 10,
            },
            {
                "candidate_id": "BNB",
                "signal_identity": "b",
                "symbol": "BNB_USDT",
                "estimated_notional_usdt": 10,
                "estimated_initial_margin_usdt": 2,
            },
        ]
        out = evaluate_shadow_capacity(
            candidate=self._candidate("DH03", "SOL_USDT", 5, 10, 2),
            existing=existing,
            policy=POLICY,
        )
        self.assertTrue(out["pass"], out)
        self.assertEqual(out["projected_positions"], 3)
        self.assertEqual(out["projected_notional_usdt"], 30)

    def test_fourth_position_is_blocked(self):
        existing = [
            {"candidate_id": "OPTIONS", "signal_identity": "o", "symbol": "BTC_USDT", "estimated_notional_usdt": 10, "estimated_initial_margin_usdt": 10},
            {"candidate_id": "BNB", "signal_identity": "b", "symbol": "BNB_USDT", "estimated_notional_usdt": 10, "estimated_initial_margin_usdt": 2},
            {"candidate_id": "DH03", "signal_identity": "d", "symbol": "SOL_USDT", "estimated_notional_usdt": 10, "estimated_initial_margin_usdt": 2},
        ]
        out = evaluate_shadow_capacity(
            candidate=self._candidate("DH03", "XRP_USDT", 5, 10, 2),
            existing=existing,
            policy=POLICY,
        )
        self.assertFalse(out["pass"])
        self.assertIn("THREE_SLOT_CAPACITY_FULL", out["blockers"])

    def test_options_profile_is_one_x(self):
        out = evaluate_shadow_capacity(
            candidate=self._candidate("OPTIONS", "BTC_USDT", 5, 10, 2),
            existing=[],
            policy=POLICY,
        )
        self.assertFalse(out["pass"])
        self.assertIn("LANE_LEVERAGE_MISMATCH", out["blockers"])

    def test_realized_loss_kill_blocks_new_capacity(self):
        out = evaluate_shadow_capacity(
            candidate=self._candidate("DH03", "SOL_USDT", 5, 10, 2),
            existing=[],
            policy=POLICY,
            daily_realized_loss_usdt=5,
        )
        self.assertFalse(out["pass"])
        self.assertIn("DAILY_KILL_ACTIVE", out["blockers"])


class ShadowLifecycleV04Tests(unittest.TestCase):
    def _reserve(self, life, lane, signal, symbol, leverage, notional, margin):
        return life.reserve_intent(
            candidate_id=lane,
            signal_identity=signal,
            external_oid=f"oid-{signal}",
            symbol=symbol,
            leverage=leverage,
            max_notional_usdt=notional,
            max_initial_margin_usdt=margin,
        )

    def test_restart_recovers_three_reserved_sessions(self):
        with tempfile.TemporaryDirectory() as td:
            life = MultiSlotShadowLifecycleV04(root=td, capacity=3)
            self._reserve(life, "OPTIONS", "o", "BTC_USDT", 1, 10, 10)
            self._reserve(life, "BNB", "b", "BNB_USDT", 5, 10, 2)
            self._reserve(life, "DH03", "d", "XRP_USDT", 5, 10, 2)
            life.mark_filled(candidate_id="OPTIONS", signal_identity="o", estimated_notional_usdt=10, estimated_initial_margin_usdt=10)
            life.mark_filled(candidate_id="BNB", signal_identity="b", estimated_notional_usdt=10, estimated_initial_margin_usdt=2)
            life.mark_filled(candidate_id="DH03", signal_identity="d", estimated_notional_usdt=10, estimated_initial_margin_usdt=2)

            restarted = MultiSlotShadowLifecycleV04(root=td, capacity=3)
            out = restarted.recover()
            self.assertEqual(out["status"], "RECOVERY_PASS")
            self.assertEqual(out["reserved_count"], 3)
            self.assertEqual(out["active_count"], 3)
            self.assertEqual(out["free_slots"], 0)

    def test_unknown_ack_survives_restart_and_keeps_slot(self):
        with tempfile.TemporaryDirectory() as td:
            life = MultiSlotShadowLifecycleV04(root=td, capacity=3)
            self._reserve(life, "BNB", "b", "BNB_USDT", 5, 10, 2)
            life.mark_unknown_ack(candidate_id="BNB", signal_identity="b")
            restarted = MultiSlotShadowLifecycleV04(root=td, capacity=3)
            out = restarted.recover()
            self.assertEqual(out["status"], "RECOVERY_PASS")
            self.assertEqual(out["unknown_ack_count"], 1)
            self.assertEqual(out["free_slots"], 2)

    def test_close_releases_exactly_one_of_three(self):
        with tempfile.TemporaryDirectory() as td:
            life = MultiSlotShadowLifecycleV04(root=td, capacity=3)
            for lane, sig, symbol, lev, margin in [
                ("OPTIONS", "o", "BTC_USDT", 1, 10),
                ("BNB", "b", "BNB_USDT", 5, 2),
                ("DH03", "d", "XRP_USDT", 5, 2),
            ]:
                self._reserve(life, lane, sig, symbol, lev, 10, margin)
                life.mark_filled(candidate_id=lane, signal_identity=sig, estimated_notional_usdt=10, estimated_initial_margin_usdt=margin)
            life.reconcile_close(candidate_id="BNB", signal_identity="b", realized_net_pnl_usdt=0)
            out = MultiSlotShadowLifecycleV04(root=td, capacity=3).recover()
            self.assertEqual(out["status"], "RECOVERY_PASS")
            self.assertEqual(out["reserved_count"], 2)
            self.assertEqual(out["active_count"], 2)
            self.assertEqual(out["free_slots"], 1)


if __name__ == "__main__":
    unittest.main()
