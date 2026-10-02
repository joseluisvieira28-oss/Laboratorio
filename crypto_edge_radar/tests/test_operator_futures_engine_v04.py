from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
import json
from pathlib import Path
import tempfile
import unittest

from radar.mexc_auth_readonly import MEXCCredentials
from radar.mexc_operator_futures_transport_v04 import direction_meta
from radar.operator_futures_engine_v04 import (
    BNB,
    DH03,
    OPTIONS,
    OperatorFuturesEngineV04,
)


@dataclass
class Snap:
    bid_price: float
    ask_price: float


class FakeExchange:
    def __init__(self):
        self.positions = {}
        self.orders = {}
        self.tpsl = {}
        self.historical = {}
        self.leverage_rows = {}
        self.next_position_id = 100
        self.next_order_id = 1000
        self.next_tpsl_id = 5000
        self.entry_submit_count = 0
        self.exit_submit_count = 0
        self.raise_after_accept_entry = False
        self.raise_after_accept_exit = False
        self._raised_entry = False
        self._raised_exit = False

    def new_order(self, *, symbol, direction, phase, volume, external_oid, leverage, position_id=None):
        oid = self.next_order_id
        self.next_order_id += 1
        price = {
            "BTC_USDT": 80000.0,
            "BNB_USDT": 700.0,
            "XRP_USDT": 1.0,
            "DOGE_USDT": 0.09,
            "SOL_USDT": 100.0,
            "ETH_USDT": 2500.0,
        }[symbol]
        order = {
            "orderId": str(oid),
            "externalOid": external_oid,
            "symbol": symbol,
            "state": 3,
            "dealVol": volume,
            "dealAvgPrice": price,
            "totalFee": 0.0,
            "takerFee": 0.001,
        }
        self.orders[(symbol, external_oid)] = order
        if phase == "ENTRY":
            self.entry_submit_count += 1
            pid = self.next_position_id
            self.next_position_id += 1
            self.positions[pid] = {
                "positionId": pid,
                "symbol": symbol,
                "positionType": direction_meta(direction)["position_type"],
                "holdVol": volume,
                "leverage": leverage,
                "openType": 1,
                "autoAddIm": False,
                "openAvgPrice": price,
            }
            if self.raise_after_accept_entry and not self._raised_entry:
                self._raised_entry = True
                raise RuntimeError("synthetic transport lost ACK after accepted entry")
        else:
            self.exit_submit_count += 1
            pid = int(position_id)
            pos = self.positions.pop(pid)
            self.historical[pid] = {
                "positionId": pid,
                "symbol": symbol,
                "positionType": pos["positionType"],
                "state": 3,
                "realised": 0.05,
                "closeAvgPrice": price,
                "closeProfitLoss": 0.06,
                "holdFee": 0.0,
                "totalFee": 0.01,
            }
            for tid in list(self.tpsl):
                if int(self.tpsl[tid]["positionId"]) == pid:
                    self.tpsl.pop(tid)
            if self.raise_after_accept_exit and not self._raised_exit:
                self._raised_exit = True
                raise RuntimeError("synthetic transport lost ACK after accepted exit")
        return {"orderId": str(oid)}


class FakeReadOnly:
    def __init__(self, exchange: FakeExchange):
        self.x = exchange

    def assets(self):
        return [{"currency": "USDT", "equity": 100.0, "availableBalance": 100.0}]

    def open_positions(self, symbol=None):
        rows = list(self.x.positions.values())
        if symbol:
            rows = [r for r in rows if r["symbol"] == symbol]
        return [dict(r) for r in rows]

    def open_orders(self, symbol=None):
        return []

    def open_tpsl_orders(self, symbol=None):
        rows = list(self.x.tpsl.values())
        if symbol:
            rows = [r for r in rows if r["symbol"] == symbol]
        return [dict(r) for r in rows]

    def fee_details(self, symbol):
        return {"realTakerFee": 0.0002}

    def leverage(self, symbol):
        return [
            {
                "symbol": sym,
                "positionType": ptype,
                "leverage": lev,
                "openType": 1,
            }
            for (sym, ptype), lev in self.x.leverage_rows.items()
            if sym == symbol
        ]

    def order_by_external(self, *, symbol, external_oid):
        key = (symbol, external_oid)
        if key not in self.x.orders:
            raise RuntimeError("order not found")
        return dict(self.x.orders[key])

    def historical_positions(self, *, symbol=None, position_type=None, start_time=None, end_time=None):
        rows = list(self.x.historical.values())
        if symbol:
            rows = [r for r in rows if r["symbol"] == symbol]
        if position_type is not None:
            rows = [r for r in rows if int(r["positionType"]) == int(position_type)]
        return [dict(r) for r in rows]


class FakePublic:
    def __init__(self):
        self.price = {
            "BTC_USDT": 80000.0,
            "BNB_USDT": 700.0,
            "XRP_USDT": 1.0,
            "DOGE_USDT": 0.09,
            "SOL_USDT": 100.0,
            "ETH_USDT": 2500.0,
        }
        self.size = {
            "BTC_USDT": 0.0001,
            "BNB_USDT": 0.01,
            "XRP_USDT": 1.0,
            "DOGE_USDT": 100.0,
            "SOL_USDT": 0.1,
            "ETH_USDT": 0.01,
        }

    def contract_row(self, symbol):
        return {
            "symbol": symbol,
            "contractSize": self.size[symbol],
            "minVol": 1,
            "volUnit": 1,
            "priceUnit": 0.0001 if symbol in {"XRP_USDT", "DOGE_USDT"} else 0.1,
            "apiAllowed": True,
            "state": 0,
            "futureType": 1,
        }

    def all_market_snapshots(self):
        out = {}
        for symbol, px in self.price.items():
            canonical = symbol.replace("_", "")
            out[canonical] = Snap(bid_price=px * 0.99995, ask_price=px * 1.00005)
        return out


class FakeTransport:
    def __init__(self, exchange: FakeExchange, policy):
        self.x = exchange
        self.policy = policy

    def configure_isolated_leverage(self, *, symbol, direction):
        self.x.leverage_rows[(symbol, direction_meta(direction)["position_type"])] = self.policy.required_leverage
        return {"ok": True}

    def set_auto_add_margin(self, *, position_id, enabled):
        self.x.positions[int(position_id)]["autoAddIm"] = bool(enabled)
        return {"ok": True}

    def cancel_by_external(self, *, symbol, external_oid):
        return {"ok": True}

    def submit_market_order(self, *, symbol, direction, phase, volume_contracts, external_oid, position_id=None):
        return self.x.new_order(
            symbol=symbol,
            direction=direction,
            phase=phase,
            volume=volume_contracts,
            external_oid=external_oid,
            leverage=self.policy.required_leverage,
            position_id=position_id,
        )

    def place_position_tpsl(
        self,
        *,
        symbol,
        direction,
        position_id,
        volume_contracts,
        stop_loss_price,
        take_profit_price,
    ):
        tid = self.x.next_tpsl_id
        self.x.next_tpsl_id += 1
        self.x.tpsl[tid] = {
            "id": tid,
            "symbol": symbol,
            "positionId": int(position_id),
            "state": 1,
            "vol": int(volume_contracts),
            "stopLossPrice": float(stop_loss_price),
            "takeProfitPrice": float(take_profit_price),
        }
        return {"id": tid}


class EngineHarness:
    def __init__(self):
        self.td = tempfile.TemporaryDirectory()
        self.root = Path(self.td.name)
        self.receipts = self.root / "receipts"
        self.policy = self.root / "policy.json"
        self.authority = self.root / "authority.json"
        self.readiness = self.root / "readiness.json"
        self.armed = self.root / "armed.json"
        self.kill = self.root / "KILL"
        self.ledger = self.root / "ledger.json"
        self.status = self.root / "status.json"
        self.exchange = FakeExchange()
        self.readonly = FakeReadOnly(self.exchange)
        self.public = FakePublic()

        self.policy.write_text(
            json.dumps(
                {
                    "policy_id": "TRIPLE_FISHING_MULTI_SLOT_SMALL_AGGRESSIVE_V0.4",
                    "capacity": {"max_simultaneous_positions": 3},
                    "global_risk": {
                        "max_total_notional_usdt": 30,
                        "max_total_initial_margin_usdt": 14,
                        "daily_realized_loss_kill_usdt": 5,
                        "rolling_7d_realized_loss_kill_usdt": 5,
                    },
                    "lanes": {
                        OPTIONS: {
                            "symbol_policy": ["BTC_USDT"],
                            "leverage": 1,
                            "max_notional_usdt": 10,
                            "max_initial_margin_usdt": 10,
                            "max_positions": 1,
                        },
                        BNB: {
                            "symbol_policy": ["BNB_USDT"],
                            "leverage": 5,
                            "max_notional_usdt": 10,
                            "max_initial_margin_usdt": 2,
                            "max_positions": 1,
                        },
                        DH03: {
                            "symbol_policy": [
                                "BTC_USDT",
                                "ETH_USDT",
                                "SOL_USDT",
                                "BNB_USDT",
                                "XRP_USDT",
                                "DOGE_USDT",
                            ],
                            "leverage": 5,
                            "max_notional_usdt": 10,
                            "max_initial_margin_usdt": 2,
                            "max_positions": 3,
                        },
                    },
                }
            ),
            encoding="utf-8",
        )
        self.authority.write_text(
            json.dumps(
                {
                    "authority_id": "OPERATOR-FUTURES-GLOBAL-V0.4-ACTIVE",
                    "status": "ACTIVE",
                    "risk": {"max_simultaneous_positions": 3},
                }
            ),
            encoding="utf-8",
        )
        self.write_readiness(datetime.now(timezone.utc))
        self.armed.write_text(
            json.dumps(
                {
                    "authority": "OPERATOR-FUTURES-GLOBAL-V0.4-ACTIVE",
                    "max_simultaneous_positions": 3,
                }
            ),
            encoding="utf-8",
        )

        self.engine = OperatorFuturesEngineV04(
            credentials=MEXCCredentials("k", "s"),
            receipt_root=str(self.receipts),
            policy_path=str(self.policy),
            activation_authority_path=str(self.authority),
            readiness_receipt_path=str(self.readiness),
            armed_path=str(self.armed),
            kill_switch_path=str(self.kill),
            ledger_path=str(self.ledger),
            status_path=str(self.status),
            readonly_client=self.readonly,
            public_feed=self.public,
            transport_factory=lambda policy: FakeTransport(self.exchange, policy),
        )

    def write_readiness(self, checked_at):
        self.readiness.write_text(
            json.dumps(
                {
                    "readiness_id": "MEXC-TRIPLE-FISHING-MULTISLOT-READY-V0.4",
                    "pass": True,
                    "checked_at_utc": checked_at.astimezone(timezone.utc).isoformat().replace("+00:00", "Z"),
                }
            ),
            encoding="utf-8",
        )

    def close(self):
        self.td.cleanup()

    @staticmethod
    def due():
        return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")

    def bnb(self, key="b"):
        now = datetime.now(timezone.utc)
        return {
            "candidate_id": BNB,
            "immutable_signal_key": key,
            "symbol": "BNB_USDT",
            "direction": "LONG",
            "entry_target_utc": now.isoformat().replace("+00:00", "Z"),
            "exit_target_utc": (now + timedelta(hours=24)).isoformat().replace("+00:00", "Z"),
            "max_late_seconds": 60,
            "max_projected_roundtrip_friction_bps": 30,
        }

    def options(self, key="o", weight=1.0):
        now = datetime.now(timezone.utc)
        return {
            "candidate_id": OPTIONS,
            "immutable_signal_key": key,
            "symbol": "BTC_USDT",
            "direction": "SHORT",
            "entry_target_utc": now.isoformat().replace("+00:00", "Z"),
            "exit_target_utc": (now + timedelta(hours=24)).isoformat().replace("+00:00", "Z"),
            "max_late_seconds": 60,
            "max_projected_roundtrip_friction_bps": 20,
            "parent_weight": weight,
        }

    def dh03(self, key="d", symbol="XRP_USDT"):
        now = datetime.now(timezone.utc)
        return {
            "candidate_id": DH03,
            "immutable_signal_key": key,
            "symbol": symbol,
            "direction": "LONG",
            "entry_target_utc": now.isoformat().replace("+00:00", "Z"),
            "exit_target_utc": (now + timedelta(hours=48)).isoformat().replace("+00:00", "Z"),
            "max_late_seconds": 60,
            "max_projected_roundtrip_friction_bps": 30,
            "protective_exit": {
                "required": True,
                "stop_distance_fraction": 0.05,
                "take_profit_distance_fraction": 0.10,
            },
        }


class OperatorEngineV04Tests(unittest.TestCase):
    def setUp(self):
        self.h = EngineHarness()

    def tearDown(self):
        self.h.close()

    def test_repository_draft_cannot_activate_without_active_authority(self):
        self.h.authority.unlink()
        out = self.h.engine.enter_signal(self.h.bnb())
        self.assertEqual(out["status"], "FAIL_CLOSED_NOT_AUTHORIZED")
        self.assertIn("V04_ACTIVE_AUTHORITY_MISSING", out["blockers"])
        self.assertEqual(self.h.exchange.entry_submit_count, 0)

    def test_options_is_mapped_to_one_x_and_parent_weight(self):
        p = self.h.engine._lane_profile(self.h.options(weight=0.5))
        self.assertEqual(p["leverage"], 1)
        self.assertEqual(p["target_notional_usdt"], 5)
        self.assertEqual(p["target_initial_margin_usdt"], 5)

    def test_three_distinct_small_positions_enter_and_fourth_is_blocked(self):
        one = self.h.engine.enter_signal(self.h.options())
        two = self.h.engine.enter_signal(self.h.bnb())
        three = self.h.engine.enter_signal(self.h.dh03())
        self.assertEqual(one["status"], "FILLED_EXIT_PENDING")
        self.assertEqual(two["status"], "FILLED_EXIT_PENDING")
        self.assertEqual(three["status"], "FILLED_EXIT_PENDING")
        self.assertEqual(len(self.h.engine.ledger.current()["reservations"]), 3)
        self.assertEqual(len(self.h.exchange.positions), 3)

        four = self.h.engine.enter_signal(self.h.dh03(key="d2", symbol="DOGE_USDT"))
        self.assertEqual(four["status"], "FAIL_CLOSED")
        self.assertIn("THREE_SLOT_CAPACITY_FULL", four["blockers"])
        self.assertEqual(self.h.exchange.entry_submit_count, 3)

    def test_same_symbol_conflict_blocks_dh03_btc_while_options_active(self):
        self.assertEqual(self.h.engine.enter_signal(self.h.options())["status"], "FILLED_EXIT_PENDING")
        out = self.h.engine.enter_signal(self.h.dh03(key="btc-d", symbol="BTC_USDT"))
        self.assertEqual(out["status"], "FAIL_CLOSED")
        self.assertIn("SYMBOL_ALREADY_ACTIVE_OR_RESERVED", out["blockers"])

    def test_unknown_entry_ack_is_recovered_without_resend(self):
        self.h.exchange.raise_after_accept_entry = True
        first = self.h.engine.enter_signal(self.h.bnb("unknown-entry"))
        self.assertEqual(first["status"], "ENTRY_RECONCILIATION_REQUIRED")
        self.assertEqual(self.h.exchange.entry_submit_count, 1)

        recovered = self.h.engine.reconcile_pending_entries()
        self.assertEqual(len(recovered), 1)
        self.assertEqual(recovered[0]["status"], "FILLED_EXIT_PENDING")
        self.assertEqual(self.h.exchange.entry_submit_count, 1)
        self.assertEqual(len(self.h.engine.ledger.current()["reservations"]), 1)

    def test_kill_switch_exits_all_three_even_with_stale_readiness(self):
        self.assertEqual(self.h.engine.enter_signal(self.h.options())["status"], "FILLED_EXIT_PENDING")
        self.assertEqual(self.h.engine.enter_signal(self.h.bnb())["status"], "FILLED_EXIT_PENDING")
        self.assertEqual(self.h.engine.enter_signal(self.h.dh03())["status"], "FILLED_EXIT_PENDING")

        self.h.write_readiness(datetime.now(timezone.utc) - timedelta(hours=1))
        self.h.kill.write_text("kill", encoding="utf-8")
        out = self.h.engine.manage_all()
        self.assertEqual(out["status"], "MULTISLOT_MANAGEMENT_OK")
        self.assertEqual(len(self.h.exchange.positions), 0)
        self.assertEqual(len(self.h.engine.ledger.current()["reservations"]), 0)
        self.assertEqual(self.h.exchange.exit_submit_count, 3)

    def test_unknown_exit_ack_is_reconciled_without_resend(self):
        self.assertEqual(self.h.engine.enter_signal(self.h.bnb())["status"], "FILLED_EXIT_PENDING")
        self.h.exchange.raise_after_accept_exit = True
        self.h.kill.write_text("kill", encoding="utf-8")

        first = self.h.engine.manage_all()
        self.assertEqual(self.h.exchange.exit_submit_count, 1)
        self.assertIn(
            "EXIT_RECONCILIATION_REQUIRED",
            {x.get("status") for x in first.get("active_results", [])},
        )

        second = self.h.engine.manage_all()
        self.assertEqual(self.h.exchange.exit_submit_count, 1)
        self.assertEqual(len(self.h.engine.ledger.current()["reservations"]), 0)
        self.assertEqual(len(self.h.exchange.positions), 0)

    def test_stale_readiness_blocks_new_entry_but_not_exit(self):
        self.assertEqual(self.h.engine.enter_signal(self.h.bnb())["status"], "FILLED_EXIT_PENDING")
        self.h.write_readiness(datetime.now(timezone.utc) - timedelta(hours=1))
        blocked = self.h.engine.enter_signal(self.h.dh03())
        self.assertEqual(blocked["status"], "FAIL_CLOSED_NOT_AUTHORIZED")
        self.assertIn("V04_READINESS_STALE_OVER_15_MIN", blocked["blockers"])

        self.h.kill.write_text("kill", encoding="utf-8")
        out = self.h.engine.manage_all()
        self.assertEqual(len(self.h.exchange.positions), 0)
        self.assertEqual(self.h.exchange.exit_submit_count, 1)


if __name__ == "__main__":
    unittest.main()
