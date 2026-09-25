from __future__ import annotations

import argparse
from datetime import date, datetime, time as dtime, timedelta, timezone
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time
from typing import Any

from radar.mexc_spot_auth_v3 import (
    ALLOWED_SYMBOL,
    MEXCSpotAuthenticatedReadOnlyClient,
    MEXCSpotCredentials,
    MEXCSpotMutationTransport,
)
from radar.options_v21_live import (
    DAY_MS,
    HISTORICAL_STATE_START,
    BinanceBTCUSDTDailyFeed,
    DailyBar,
    DeribitBTCOptionTradeFeed,
    OptionTrade,
    _utc_day_bounds,
    build_daily_skew,
    rv20_and_weight,
)
from scripts.mexc_risk_state import build_state
from scripts.mexc_spot_authenticated_preflight import build_preflight


POLICY_ID = "TIER2-MICROLIVE-POLICY-V1.0-FROZEN-2026-09-24"
STRATEGY_ID = "OPTIONS-SPOTPERP-001-V2.1"
ARMING_ID = "TIER2_AUTOLIVE_ARMING_V0.3"
LIVE_TOKEN = "CRYPTO_LAB_TIER2_MICROLIVE_V0_3"
PREFETCH_LEAD_SECONDS = 180
PREFLIGHT_LEAD_SECONDS = 40
TAIL_PREFETCH_SECONDS = 5
MAX_ENTRY_LATE_SECONDS = 2.0


def _write(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(
        json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    tmp.replace(path)


def _load(path: Path) -> dict[str, Any]:
    row = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(row, dict):
        raise RuntimeError(f"JSON object required: {path}")
    return row


def _iso(dt: datetime) -> str:
    return dt.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def _ms(dt: datetime) -> int:
    return int(dt.timestamp() * 1000)


def _midnight(day: date) -> datetime:
    return datetime.combine(day, dtime.min, tzinfo=timezone.utc)


def _next_boundary(now: datetime) -> datetime:
    return _midnight(now.date() + timedelta(days=1))


def resolve_cycle_target(
    now: datetime,
    cache: "DayCache | None",
) -> tuple[date, datetime]:
    if cache is not None:
        signal_day = cache.signal_day
        return signal_day, _midnight(signal_day + timedelta(days=1))
    target = _next_boundary(now)
    return target.date() - timedelta(days=1), target


def _merge_trades(*groups: list[OptionTrade]) -> list[OptionTrade]:
    by_id: dict[str, OptionTrade] = {}
    for rows in groups:
        for row in rows:
            old = by_id.get(row.trade_id)
            if old is not None and old != row:
                raise RuntimeError("DERIBIT_TRADE_ID_COLLISION")
            by_id[row.trade_id] = row
    return sorted(by_id.values(), key=lambda x: (x.timestamp, x.trade_id))


def _daily_bar_for_day(feed: BinanceBTCUSDTDailyFeed, day: date) -> DailyBar:
    start, end = _utc_day_bounds(day)
    payload = feed._get_json(
        {
            "symbol": "BTCUSDT",
            "interval": "1d",
            "startTime": start,
            "endTime": end,
            "limit": 2,
        }
    )
    if not isinstance(payload, list) or not payload:
        raise RuntimeError("BTC_SIGNAL_DAY_DAILY_BAR_UNAVAILABLE")
    row = payload[0]
    if not isinstance(row, list) or len(row) < 7 or int(row[0]) != start:
        raise RuntimeError("BTC_SIGNAL_DAY_DAILY_BAR_BINDING_MISMATCH")
    if int(row[6]) != end:
        raise RuntimeError("BTC_SIGNAL_DAY_NOT_COMPLETE")
    op = float(row[1])
    cl = float(row[4])
    if op <= 0 or cl <= 0:
        raise RuntimeError("BTC_SIGNAL_DAY_INVALID_OHLC")
    return DailyBar(start, op, cl)


def _arm_valid(arm_path: Path, now: datetime) -> tuple[bool, str]:
    try:
        arm = _load(arm_path)
    except FileNotFoundError:
        return False, "ARMING_FILE_MISSING"
    except Exception as exc:
        return False, f"ARMING_FILE_INVALID:{type(exc).__name__}"
    if arm.get("arming_id") != ARMING_ID or arm.get("status") != "ACTIVE":
        return False, "ARMING_STATUS_INVALID"
    if arm.get("policy_id") != POLICY_ID:
        return False, "ARMING_POLICY_MISMATCH"
    if arm.get("candidate_id") != STRATEGY_ID:
        return False, "ARMING_CANDIDATE_MISMATCH"
    if arm.get("allow_real_orders") is not True:
        return False, "ARMING_REAL_ORDERS_FALSE"
    if float(arm.get("maximum_notional_usdt_equivalent", -1)) != 10.0:
        return False, "ARMING_NOTIONAL_CAP_MISMATCH"
    try:
        expires = datetime.fromisoformat(
            str(arm["expires_at_utc"]).replace("Z", "+00:00")
        ).astimezone(timezone.utc)
    except Exception:
        return False, "ARMING_EXPIRY_INVALID"
    if now >= expires:
        return False, "ARMING_EXPIRED"
    return True, "ACTIVE"


def _exe_dir() -> Path:
    return Path(sys.executable).resolve().parent


def _sibling_exe(name: str) -> Path:
    p = _exe_dir() / name
    if not p.exists():
        raise RuntimeError(f"REQUIRED_SIBLING_EXE_MISSING:{name}")
    return p


def _run_child(exe: Path, args: list[str]) -> tuple[int, str]:
    result = subprocess.run(
        [str(exe), *args],
        text=True,
        capture_output=True,
        timeout=120,
        check=False,
    )
    combined = (result.stdout or "") + ("\n" + result.stderr if result.stderr else "")
    return int(result.returncode), combined.strip()


class DayCache:
    def __init__(self, signal_day: date) -> None:
        self.signal_day = signal_day
        self.option_trades: list[OptionTrade] = []
        self.option_end_ms: int | None = None
        self.btc_history: list[DailyBar] | None = None
        self.preflight_at: datetime | None = None

    def prefetch(
        self,
        *,
        options_feed: DeribitBTCOptionTradeFeed,
        btc_feed: BinanceBTCUSDTDailyFeed,
        end_ms: int,
    ) -> None:
        start_ms, day_end_ms = _utc_day_bounds(self.signal_day)
        end_ms = min(end_ms, day_end_ms)
        start_fetch = start_ms if self.option_end_ms is None else self.option_end_ms + 1
        if start_fetch <= end_ms:
            rows = options_feed.trades(start_ms=start_fetch, end_ms=end_ms)
            self.option_trades = _merge_trades(self.option_trades, rows)
            self.option_end_ms = end_ms
        if self.btc_history is None:
            self.btc_history = btc_feed.daily(
                start_day=HISTORICAL_STATE_START,
                end_day_exclusive=self.signal_day,
            )


class AutoLiveSupervisor:
    def __init__(
        self,
        *,
        data_dir: Path,
        receipt_root: Path,
        arm_path: Path,
        interval_seconds: float = 0.25,
    ) -> None:
        self.data_dir = data_dir
        self.receipt_root = receipt_root
        self.arm_path = arm_path
        self.interval_seconds = interval_seconds
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.receipt_root.mkdir(parents=True, exist_ok=True)
        self.options_feed = DeribitBTCOptionTradeFeed(timeout=8)
        self.btc_feed = BinanceBTCUSDTDailyFeed(timeout=8)
        self.creds = MEXCSpotCredentials.from_env()
        self.readonly = MEXCSpotAuthenticatedReadOnlyClient(self.creds, timeout=8)
        self.transport = MEXCSpotMutationTransport(self.creds, timeout=8)
        self.cache: DayCache | None = None
        self.last_decision_day: date | None = None

    @property
    def status_path(self) -> Path:
        return self.data_dir / "tier2_autolive_v03_status.json"

    def _status(self, status: str, **extra: Any) -> None:
        _write(
            self.status_path,
            {
                "supervisor_id": "OPTIONS_V21_TIER2_AUTOLIVE_SUPERVISOR_V0.3",
                "status": status,
                "checked_at_utc": _iso(datetime.now(timezone.utc)),
                **extra,
            },
        )

    def _active_states(self) -> list[Path]:
        out = []
        for path in self.receipt_root.rglob("ACTIVE_TRADE_STATE.json"):
            if (path.parent / "POST_TRADE_RECONCILIATION.json").exists():
                continue
            try:
                row = _load(path)
            except Exception:
                continue
            if (
                row.get("state") == "EXIT_PENDING"
                and row.get("strategy_id") == STRATEGY_ID
            ):
                out.append(path)
        return out

    def _run_due_exits(self, now: datetime) -> None:
        for path in self._active_states():
            row = _load(path)
            try:
                due = datetime.fromisoformat(
                    str(row["exit_target_utc"]).replace("Z", "+00:00")
                ).astimezone(timezone.utc)
            except Exception:
                self._status("FAIL_CLOSED", blocker="ACTIVE_EXIT_TARGET_INVALID")
                continue
            if now < due:
                continue
            exe = _sibling_exe("OptionsV21SpotExitGuard.exe")
            rc, output = _run_child(
                exe,
                [
                    "--active-state",
                    str(path),
                    "--duplicate-lock-root",
                    str(self.data_dir / "duplicate_locks"),
                    "--execute",
                ],
            )
            _write(
                path.parent / "AUTOLIVE_EXIT_SUPERVISOR_RECEIPT.json",
                {
                    "receipt_type": "AUTOLIVE_EXIT_SUPERVISOR_RECEIPT",
                    "invoked_at_utc": _iso(now),
                    "return_code": rc,
                    "output": output[-4000:],
                },
            )

    def _refresh_preflight(self, now: datetime) -> tuple[Path, Path]:
        preflight = build_preflight(self.readonly)
        preflight_path = self.data_dir / "mexc_spot_authenticated_preflight_receipt.json"
        _write(preflight_path, preflight)
        risk = build_state(
            preflight_path=preflight_path,
            receipt_root=self.receipt_root,
            now=now,
        )
        risk_path = self.data_dir / "mexc_account_risk_state.json"
        _write(risk_path, risk)
        if preflight.get("pass") is not True:
            raise RuntimeError("SPOT_PREFLIGHT_FAIL_CLOSED")
        if risk.get("status") != "PASS":
            raise RuntimeError("ACCOUNT_RISK_STATE_FAIL_CLOSED")
        return preflight_path, risk_path

    def _final_signal(
        self,
        *,
        cache: DayCache,
        target: datetime,
    ) -> tuple[dict[str, Any], dict[str, Any]]:
        day_start_ms, day_end_ms = _utc_day_bounds(cache.signal_day)
        if cache.option_end_ms is None:
            cache.option_end_ms = day_start_ms - 1
        if cache.option_end_ms < day_end_ms:
            tail = self.options_feed.trades(
                start_ms=cache.option_end_ms + 1,
                end_ms=day_end_ms,
            )
            cache.option_trades = _merge_trades(cache.option_trades, tail)
            cache.option_end_ms = day_end_ms
        signal = build_daily_skew(cache.signal_day, cache.option_trades)
        if cache.btc_history is None:
            raise RuntimeError("BTC_HISTORY_CACHE_MISSING")
        final_bar = _daily_bar_for_day(self.btc_feed, cache.signal_day)
        bars = [*cache.btc_history, final_bar]
        risk_scaling = (
            rv20_and_weight(bars, signal_day=cache.signal_day)
            if signal.get("valid")
            else {
                "rv20": None,
                "expanding_median_rv20": None,
                "weight": 0.0,
                "valid_rv20_history_count": None,
            }
        )
        return signal, risk_scaling

    def _decision_paths(self, signal_day: date) -> tuple[Path, Path, Path, Path]:
        stem = signal_day.isoformat()
        return (
            self.data_dir / f"options_v21_live_signal_{stem}.json",
            self.data_dir / f"options_v21_active_authority_{stem}.json",
            self.data_dir / f"options_v21_order_test_{stem}.json",
            self.data_dir / f"options_v21_autolive_decision_{stem}.json",
        )

    def _handle_boundary(
        self,
        *,
        cache: DayCache,
        target: datetime,
        now: datetime,
    ) -> None:
        signal_path, authority_path, order_test_path, decision_path = self._decision_paths(
            cache.signal_day
        )
        if decision_path.exists():
            self.last_decision_day = cache.signal_day
            return

        elapsed_before_source = (now - target).total_seconds()
        if elapsed_before_source > MAX_ENTRY_LATE_SECONDS:
            _write(
                decision_path,
                {
                    "status": "NO_TRADE_MISSED_ENTRY_NO_CHASE",
                    "signal_date": cache.signal_day.isoformat(),
                    "seconds_late": elapsed_before_source,
                },
            )
            self.last_decision_day = cache.signal_day
            return

        try:
            signal, risk_scaling = self._final_signal(cache=cache, target=target)
        except Exception as exc:
            _write(
                decision_path,
                {
                    "status": "NO_TRADE_SOURCE_FAIL_CLOSED",
                    "signal_date": cache.signal_day.isoformat(),
                    "error": f"{type(exc).__name__}:{exc}",
                },
            )
            self.last_decision_day = cache.signal_day
            return

        position = int(signal.get("position") or 0)
        weight = float(risk_scaling.get("weight") or 0.0)
        immutable_key = f"OPTIONS-SPOTPERP-001:V2.1:{cache.signal_day.isoformat()}"
        signal_receipt = {
            "immutable_signal_key": immutable_key,
            "strategy_id": STRATEGY_ID,
            "signal_date": cache.signal_day.isoformat(),
            "signal_direction": "LONG" if position > 0 else ("SHORT" if position < 0 else "FLAT"),
            "position": position,
            "weight": weight,
            "canonical": bool(signal.get("valid")),
            "source_healthy": True,
            "radar_motor_healthy": True,
            "source_provider": "DERIBIT_PUBLIC_HTTP+BINANCE_SPOT_DATA_API_PUBLIC",
            "signal": signal,
            "risk_scaling": risk_scaling,
            "entry_target_utc": _iso(target),
            "exit_target_utc": _iso(target + timedelta(days=1)),
            "created_at_utc": _iso(datetime.now(timezone.utc)),
        }
        _write(signal_path, signal_receipt)

        if not signal.get("valid") or position == 0 or weight <= 0:
            _write(
                decision_path,
                {
                    "status": "NO_TRADE_FLAT_OR_INVALID",
                    "signal_date": cache.signal_day.isoformat(),
                    "position": position,
                    "weight": weight,
                },
            )
            self.last_decision_day = cache.signal_day
            return
        if position < 0:
            _write(
                decision_path,
                {
                    "status": "NO_TRADE_SHORT_LANE_NOT_YET_INSTALLED",
                    "signal_date": cache.signal_day.isoformat(),
                    "position": position,
                    "weight": weight,
                },
            )
            self.last_decision_day = cache.signal_day
            return

        current = datetime.now(timezone.utc)
        if (current - target).total_seconds() > MAX_ENTRY_LATE_SECONDS:
            _write(
                decision_path,
                {
                    "status": "NO_TRADE_SIGNAL_FINALIZED_TOO_LATE_NO_CHASE",
                    "signal_date": cache.signal_day.isoformat(),
                    "seconds_late": (current - target).total_seconds(),
                },
            )
            self.last_decision_day = cache.signal_day
            return

        preflight_path = self.data_dir / "mexc_spot_authenticated_preflight_receipt.json"
        risk_path = self.data_dir / "mexc_account_risk_state.json"
        if not preflight_path.exists() or not risk_path.exists():
            try:
                preflight_path, risk_path = self._refresh_preflight(current)
            except Exception as exc:
                _write(
                    decision_path,
                    {
                        "status": "NO_TRADE_PREFLIGHT_OR_RISK_FAIL_CLOSED",
                        "error": f"{type(exc).__name__}:{exc}",
                    },
                )
                self.last_decision_day = cache.signal_day
                return

        quote = 10.0 * weight
        client_id = "o3e" + hashlib.sha256(immutable_key.encode()).hexdigest()[:20]
        duplicate_key = "entry:" + immutable_key
        authority = {
            "authority_id": f"OPTIONS_V21_SPOT_LONG_{cache.signal_day.isoformat()}",
            "status": "ACTIVE_MICRO_LIVE_EXECUTION_AUTHORITY",
            "micro_live_policy_id": POLICY_ID,
            "strategy_id": STRATEGY_ID,
            "exchange": "MEXC",
            "market": "SPOT",
            "symbol": ALLOWED_SYMBOL,
            "direction": "LONG",
            "leverage": 1,
            "leverage_above_one": False,
            "order_type": "MARKET",
            "max_simultaneous_positions": 1,
            "signal_identity": immutable_key,
            "weight": weight,
            "base_micro_live_notional_usdt": 10.0,
            "quote_order_qty_usdt": quote,
            "maximum_notional_usdt_equivalent": 10.0,
            "maximum_total_account_exposure_usdt_equivalent": 10.0,
            "daily_realized_loss_kill_usdt": 2.0,
            "rolling_7d_realized_loss_kill_usdt": 5.0,
            "entry_target_utc": _iso(target),
            "exit_target_utc": _iso(target + timedelta(days=1)),
            "max_late_seconds": MAX_ENTRY_LATE_SECONDS,
            "max_preflight_age_seconds": 60,
            "max_risk_state_age_seconds": 60,
            "max_order_test_age_seconds": 60,
            "new_client_order_id": client_id,
            "duplicate_protection_key": duplicate_key,
            "kill_switch_path": str(self.data_dir / "KILL_SWITCH"),
            "generated_from_umbrella_operator_authority": True,
            "generated_before_order_transport": True,
        }
        _write(authority_path, authority)

        try:
            response = self.transport.test_market_buy(
                quote_order_qty=format(quote, ".8f").rstrip("0").rstrip("."),
                client_order_id=client_id,
                symbol=ALLOWED_SYMBOL,
            )
        except Exception as exc:
            _write(
                decision_path,
                {
                    "status": "NO_TRADE_ORDER_TEST_FAIL_CLOSED",
                    "error": f"{type(exc).__name__}:{exc}",
                },
            )
            self.last_decision_day = cache.signal_day
            return

        _write(
            order_test_path,
            {
                "receipt_id": "MEXC_SPOT_ORDER_TEST_V0.3",
                "checked_at_utc": _iso(datetime.now(timezone.utc)),
                "status": "PASS",
                "symbol": ALLOWED_SYMBOL,
                "side": "BUY",
                "type": "MARKET",
                "quote_order_qty_usdt": quote,
                "client_order_id": client_id,
                "matching_engine_order_created": False,
                "endpoint": "/api/v3/order/test",
                "response": response,
            },
        )

        if datetime.now(timezone.utc) - target > timedelta(seconds=MAX_ENTRY_LATE_SECONDS):
            _write(
                decision_path,
                {
                    "status": "NO_TRADE_ORDER_TEST_FINISHED_TOO_LATE_NO_CHASE",
                    "seconds_late": (datetime.now(timezone.utc) - target).total_seconds(),
                },
            )
            self.last_decision_day = cache.signal_day
            return

        exe = _sibling_exe("OptionsV21SpotLiveExecutor.exe")
        rc, output = _run_child(
            exe,
            [
                "--authority",
                str(authority_path),
                "--preflight",
                str(preflight_path),
                "--order-test",
                str(order_test_path),
                "--signal",
                str(signal_path),
                "--risk-state",
                str(risk_path),
                "--receipt-root",
                str(self.receipt_root),
                "--duplicate-lock-root",
                str(self.data_dir / "duplicate_locks"),
                "--execute",
            ],
        )
        _write(
            decision_path,
            {
                "status": "EXECUTOR_INVOKED",
                "signal_date": cache.signal_day.isoformat(),
                "return_code": rc,
                "executor_output": output[-4000:],
                "invoked_at_utc": _iso(datetime.now(timezone.utc)),
            },
        )
        self.last_decision_day = cache.signal_day

    def run_forever(self) -> None:
        self._status("STARTING")
        while True:
            now = datetime.now(timezone.utc)
            armed, reason = _arm_valid(self.arm_path, now)
            if not armed:
                self._status("DISARMED", reason=reason)
                time.sleep(5)
                continue

            try:
                self._run_due_exits(now)
            except Exception as exc:
                self._status(
                    "EXIT_SUPERVISOR_FAIL_CLOSED",
                    error=f"{type(exc).__name__}:{exc}",
                )

            if self._active_states():
                self._status("ACTIVE_POSITION_EXIT_PENDING")
                time.sleep(1)
                continue

            signal_day, target = resolve_cycle_target(now, self.cache)
            remaining = (target - now).total_seconds()

            if self.last_decision_day == signal_day:
                self._status("DAY_ALREADY_ADJUDICATED", signal_day=signal_day.isoformat())
                self.cache = None
                time.sleep(5)
                continue

            if self.cache is None:
                self.cache = DayCache(signal_day)

            try:
                if remaining <= PREFETCH_LEAD_SECONDS and remaining > TAIL_PREFETCH_SECONDS:
                    safe_end = min(
                        _ms(now - timedelta(seconds=1)),
                        _ms(target) - 1,
                    )
                    if (
                        self.cache.option_end_ms is None
                        or safe_end - self.cache.option_end_ms >= 10_000
                    ):
                        self.cache.prefetch(
                            options_feed=self.options_feed,
                            btc_feed=self.btc_feed,
                            end_ms=safe_end,
                        )
                    if (
                        remaining <= PREFLIGHT_LEAD_SECONDS
                        and (
                            self.cache.preflight_at is None
                            or (now - self.cache.preflight_at).total_seconds() >= 20
                        )
                    ):
                        self._refresh_preflight(now)
                        self.cache.preflight_at = now
                    self._status(
                        "PREARMED",
                        signal_day=signal_day.isoformat(),
                        entry_target_utc=_iso(target),
                        seconds_to_entry=remaining,
                        option_trades_cached=len(self.cache.option_trades),
                    )
            except Exception as exc:
                self._status(
                    "PREARM_FAIL_CLOSED",
                    signal_day=signal_day.isoformat(),
                    error=f"{type(exc).__name__}:{exc}",
                )

            if remaining <= 0:
                self._handle_boundary(cache=self.cache, target=target, now=now)
                self.cache = None

            time.sleep(self.interval_seconds if remaining < 10 else min(2.0, self.interval_seconds * 8))


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--data-dir", required=True)
    ap.add_argument("--receipt-root", required=True)
    ap.add_argument("--arm-file", required=True)
    ap.add_argument("--interval-seconds", type=float, default=0.25)
    args = ap.parse_args()
    if os.getenv("CRYPTO_LAB_LIVE_EXECUTION_TOKEN") != LIVE_TOKEN:
        print(json.dumps({"status": "DISARMED", "reason": "LIVE_EXECUTION_TOKEN_MISSING_OR_WRONG"}, indent=2))
        return 3
    sup = AutoLiveSupervisor(
        data_dir=Path(args.data_dir),
        receipt_root=Path(args.receipt_root),
        arm_path=Path(args.arm_file),
        interval_seconds=max(0.05, args.interval_seconds),
    )
    sup.run_forever()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
