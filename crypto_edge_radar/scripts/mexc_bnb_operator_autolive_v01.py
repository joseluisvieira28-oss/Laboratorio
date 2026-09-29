from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import time
from typing import Any

from radar.bnb_launchpool_watcher import (
    BinanceOfficialLaunchpoolSource,
    _cluster_announcements,
    _cluster_key,
)
from radar.global_fishing_dispatcher_v02 import arbitrate_due_signals
from radar.mexc_auth_readonly import MEXCCredentials
from radar.operator_futures_engine_v02 import OperatorFuturesEngineV02
from radar.strategies.bnb_launchpool_demand import (
    exact_exit_open_ms,
    first_eligible_entry_open_ms,
)

CANDIDATE_ID = "BNB-LAUNCHPOOL-DEMAND-001"
SYMBOL = "BNB_USDT"
POLL_FLOOR_SECONDS = 30.0
ARM_LEAD_SECONDS = 60.0
MAX_LATE_SECONDS = 2.0


def _iso_ms(ms: int) -> str:
    return (
        datetime.fromtimestamp(ms / 1000.0, tz=timezone.utc)
        .isoformat()
        .replace("+00:00", "Z")
    )


def _atomic_write(path: str | Path, payload: dict[str, Any]) -> None:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    tmp = target.with_suffix(target.suffix + ".tmp")
    tmp.write_text(
        json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    tmp.replace(target)


def _load_state(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {
            "version": "BNB_OPERATOR_AUTOLIVE_V0.1",
            "candidate_id": CANDIDATE_ID,
            "events": {},
            "science_credit": False,
        }
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise RuntimeError("state file must contain JSON object")
    payload.setdefault("events", {})
    return payload


def _validate_policy(path: str | Path) -> dict[str, Any]:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    if payload.get("policy_id") != "CRYPTO-LAB-OPERATOR-GLOBAL-RISK-V0.2":
        raise RuntimeError("unexpected operator risk policy")
    global_risk = payload.get("global_risk") or {}
    expected = {
        "max_simultaneous_positions": 1,
        "margin_mode": "ISOLATED",
        "leverage": 5,
        "max_initial_margin_usdt_per_position": 10,
        "max_notional_usdt_per_position": 50,
        "daily_realized_loss_kill_usdt": 5,
    }
    for key, value in expected.items():
        if global_risk.get(key) != value:
            raise RuntimeError(f"operator risk policy mismatch: {key}")
    bnb = (payload.get("current_candidate_states") or {}).get(CANDIDATE_ID) or {}
    if bnb.get("state") != "PREARMED_FOR_AUTOMATED_OPERATOR_LIVE":
        raise RuntimeError("BNB candidate is not prearmed in policy")
    return payload


def build_signal(cluster: list[Any]) -> dict[str, Any]:
    anchor = cluster[0]
    key = _cluster_key(cluster)
    entry_ms = first_eligible_entry_open_ms(anchor.published_ms)
    exit_ms = exact_exit_open_ms(entry_ms)
    return {
        "candidate_id": CANDIDATE_ID,
        "strategy_id": CANDIDATE_ID,
        "immutable_signal_key": key,
        "source": "BINANCE_SUPPORT_CMS_PUBLIC",
        "signal_article_code": anchor.article_code,
        "cluster_article_codes": [event.article_code for event in cluster],
        "signal_timestamp_utc": anchor.published_utc,
        "symbol": SYMBOL,
        "direction": "LONG",
        "entry_target_utc": _iso_ms(entry_ms),
        "exit_target_utc": _iso_ms(exit_ms),
        "max_late_seconds": MAX_LATE_SECONDS,
        "max_initial_margin_usdt": 10.0,
        "max_notional_usdt": 50.0,
        "leverage": 5,
        "margin_mode": "ISOLATED",
        "max_projected_roundtrip_friction_bps": 30.0,
        "scientific_credit": False,
        "operator_proxy": True,
    }


class BNBOperatorAutoLiveV01:
    def __init__(
        self,
        *,
        engine: OperatorFuturesEngineV02,
        state_path: str,
        source: BinanceOfficialLaunchpoolSource | None = None,
        poll_seconds: float = POLL_FLOOR_SECONDS,
    ) -> None:
        self.engine = engine
        self.state_path = Path(state_path)
        self.source = source or BinanceOfficialLaunchpoolSource(timeout=15)
        self.poll_seconds = max(POLL_FLOOR_SECONDS, float(poll_seconds))
        self.state = _load_state(self.state_path)

    def _save(self, **updates: Any) -> dict[str, Any]:
        self.state.update(updates)
        self.state["checked_at_utc"] = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
        _atomic_write(self.state_path, self.state)
        return self.state

    def discover(self, *, now_ms: int) -> list[dict[str, Any]]:
        events = self.source.discover_eligible(now_ms=now_ms)
        clusters = _cluster_announcements(events)
        signals: list[dict[str, Any]] = []
        for cluster in clusters:
            signal = build_signal(cluster)
            key = signal["immutable_signal_key"]
            target_ms = int(
                datetime.fromisoformat(signal["entry_target_utc"].replace("Z", "+00:00")).timestamp()
                * 1000
            )
            row = self.state["events"].get(key)
            if row is None:
                row = {
                    "first_observed_at_utc": _iso_ms(now_ms),
                    "entry_target_utc": signal["entry_target_utc"],
                    "exit_target_utc": signal["exit_target_utc"],
                    "signal_article_code": signal["signal_article_code"],
                    "status": (
                        "PENDING_FUTURE_ENTRY"
                        if now_ms < target_ms
                        else "MISSED_FIRST_OBSERVATION_NO_CHASE"
                    ),
                    "late_chase_allowed": False,
                }
                self.state["events"][key] = row
            if row.get("status") in {
                "PENDING_FUTURE_ENTRY",
                "PREARMED",
            }:
                signals.append(signal)
        self._save(
            source_status="OK",
            visible_event_count=len(events),
            visible_cluster_count=len(clusters),
        )
        return sorted(signals, key=lambda s: (s["entry_target_utc"], s["immutable_signal_key"]))

    def run_cycle(self, *, now_ms: int | None = None) -> dict[str, Any]:
        if now_ms is None:
            now_ms = int(datetime.now(timezone.utc).timestamp() * 1000)

        active = self.engine.manage_active()
        if active.get("status") not in {
            "IDLE_NO_OPERATOR_POSITION",
            "CLOSED_RECONCILED",
        }:
            return self._save(
                status="MANAGING_ACTIVE_OPERATOR_POSITION",
                engine=active,
            )

        try:
            signals = self.discover(now_ms=now_ms)
        except Exception as exc:
            return self._save(
                status="FAIL_CLOSED_SOURCE",
                source_status="FAIL_CLOSED",
                error=f"{type(exc).__name__}:{exc}",
            )

        if not signals:
            return self._save(
                status="WATCHING_FOR_BNB_LAUNCHPOOL_EVENT",
                pending_signal_count=0,
            )

        signal = signals[0]
        target = datetime.fromisoformat(
            signal["entry_target_utc"].replace("Z", "+00:00")
        ).astimezone(timezone.utc)
        now = datetime.fromtimestamp(now_ms / 1000.0, tz=timezone.utc)
        seconds = (target - now).total_seconds()
        key = signal["immutable_signal_key"]

        if seconds > ARM_LEAD_SECONDS:
            self.state["events"][key]["status"] = "PENDING_FUTURE_ENTRY"
            return self._save(
                status="WAITING_BNB_ENTRY_WINDOW",
                pending_signal_count=len(signals),
                next_signal_identity=key,
                entry_target_utc=signal["entry_target_utc"],
                seconds_to_entry=seconds,
            )

        if seconds > 0:
            self.state["events"][key]["status"] = "PREARMED"
            return self._save(
                status="PREARMED_FOR_BNB_ENTRY",
                pending_signal_count=len(signals),
                next_signal_identity=key,
                entry_target_utc=signal["entry_target_utc"],
                seconds_to_entry=seconds,
            )

        # Deterministic single-slot arbitration. Exchange truth is checked again
        # inside the engine immediately before any mutation.
        try:
            slot_occupied = bool(self.engine.readonly.open_positions())
        except Exception as exc:
            self.state["events"][key]["status"] = "BLOCKED_ACCOUNT_STATE_UNKNOWN_NO_CHASE"
            return self._save(
                status="FAIL_CLOSED_ACCOUNT_STATE",
                error=f"{type(exc).__name__}:{exc}",
            )

        decision = arbitrate_due_signals(
            signals,
            now=now,
            global_slot_occupied=slot_occupied,
        )
        if decision["winner"] is None:
            for loser in decision.get("losers", []):
                loser_key = loser["signal_identity"]
                if loser_key in self.state["events"]:
                    self.state["events"][loser_key]["status"] = loser["reason"]
            return self._save(
                status=decision["status"],
                arbitration=decision,
            )

        winner = decision["winner"]
        result = self.engine.enter_signal(winner)
        winner_key = winner["immutable_signal_key"]
        result_status = str(result.get("status") or "")
        if result_status == "FILLED_EXIT_PENDING":
            self.state["events"][winner_key]["status"] = "CONSUMED_ACTIVE_REAL_MONEY"
        elif result_status == "WAITING_ENTRY_TARGET":
            self.state["events"][winner_key]["status"] = "PREARMED"
        else:
            # No later retry after the immutable +2s window.
            self.state["events"][winner_key]["status"] = "BLOCKED_AT_ENTRY_NO_CHASE"
            self.state["events"][winner_key]["entry_result"] = result_status

        for loser in decision.get("losers", []):
            loser_key = loser["signal_identity"]
            if loser_key in self.state["events"]:
                self.state["events"][loser_key]["status"] = loser["reason"]

        return self._save(
            status=result_status,
            arbitration=decision,
            engine=result,
        )

    def run_forever(self) -> None:
        while True:
            started = time.monotonic()
            state = self.run_cycle()
            status = str(state.get("status") or "")
            if status == "PREARMED_FOR_BNB_ENTRY":
                seconds = float(state.get("seconds_to_entry", 0) or 0)
                sleep_for = max(0.02, min(0.25, seconds))
            else:
                sleep_for = self.poll_seconds
            elapsed = time.monotonic() - started
            time.sleep(max(0.02, sleep_for - elapsed))


def main() -> int:
    ap = argparse.ArgumentParser(
        description="24/7 BNB operator AutoLive supervisor. No discretionary per-trade confirmation."
    )
    ap.add_argument("--policy", required=True)
    ap.add_argument("--receipt-root", default="live_receipts/operator_futures_v02")
    ap.add_argument("--state-path", default="live_state/bnb_operator_autolive_v01.json")
    ap.add_argument("--status-path", default="live_state/operator_futures_engine_v02.json")
    ap.add_argument("--armed-path", default="OPERATOR_FUTURES_V02_ARMED.json")
    ap.add_argument("--kill-switch", default="OPERATOR_FUTURES_V02_KILL_SWITCH")
    ap.add_argument("--poll-seconds", type=float, default=POLL_FLOOR_SECONDS)
    args = ap.parse_args()

    _validate_policy(args.policy)
    credentials = MEXCCredentials.from_env()
    engine = OperatorFuturesEngineV02(
        credentials=credentials,
        receipt_root=args.receipt_root,
        armed_path=args.armed_path,
        kill_switch_path=args.kill_switch,
        status_path=args.status_path,
    )
    supervisor = BNBOperatorAutoLiveV01(
        engine=engine,
        state_path=args.state_path,
        poll_seconds=args.poll_seconds,
    )
    supervisor.run_forever()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
