from __future__ import annotations

from datetime import datetime, timedelta, timezone
from decimal import Decimal, ROUND_DOWN, ROUND_CEILING
import hashlib
import json
import math
import os
from pathlib import Path
import time
from typing import Any

from .market import MEXCFuturesPublicFeed
from .mexc_auth_readonly import MEXCCredentials, MEXCFuturesAuthenticatedReadOnlyClient
from .mexc_operator_futures_transport_v04 import (
    MEXCMultiSlotFuturesTransportV04,
    MultiSlotFuturesPolicy,
    direction_meta,
)
from .multi_slot_reservation_v04 import MultiSlotReservationV04
from .operator_risk_v02 import realized_loss_state

OFFICIAL_API_TAKER_FLOOR = 0.0008
MAX_CLOCK_OFFSET_MS = 500.0

OPTIONS = "OPTIONS-SPOTPERP-001-V2.1"
BNB = "BNB-LAUNCHPOOL-DEMAND-001"
DH03 = "HTF-DH03-12H-STANDALONE-FORWARD-V1"


class MultiSlotEngineError(RuntimeError):
    pass


def _load(path: str | Path) -> dict[str, Any]:
    obj = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(obj, dict):
        raise MultiSlotEngineError(f"JSON object required: {path}")
    return obj


def _atomic_write(path: str | Path, payload: dict[str, Any]) -> None:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    tmp = target.with_suffix(target.suffix + ".tmp")
    tmp.write_text(
        json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    tmp.replace(target)


def _exclusive_write(path: str | Path, payload: dict[str, Any]) -> bool:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    try:
        fd = os.open(str(target), os.O_CREAT | os.O_EXCL | os.O_WRONLY)
    except FileExistsError:
        return False
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            json.dump(payload, handle, indent=2, sort_keys=True, ensure_ascii=False)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
    except Exception:
        target.unlink(missing_ok=True)
        raise
    return True


def _utc(value: Any) -> datetime:
    dt = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    if dt.tzinfo is None:
        raise MultiSlotEngineError("timezone-aware timestamp required")
    return dt.astimezone(timezone.utc)


def _iso(value: datetime | None = None) -> str:
    return (value or datetime.now(timezone.utc)).astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def _finite(value: Any, field: str) -> float:
    x = float(value)
    if not math.isfinite(x):
        raise MultiSlotEngineError(f"{field} must be finite")
    return x


def _sha256_file(path: str | Path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def _floor_step(value: float, step: float) -> float:
    if value <= 0 or step <= 0:
        return 0.0
    return float(
        (Decimal(str(value)) / Decimal(str(step))).to_integral_value(rounding=ROUND_DOWN)
        * Decimal(str(step))
    )


def _ceil_step(value: float, step: float) -> float:
    if value <= 0 or step <= 0:
        return 0.0
    return float(
        (Decimal(str(value)) / Decimal(str(step))).to_integral_value(rounding=ROUND_CEILING)
        * Decimal(str(step))
    )


def _oid(signal_identity: str, phase: str, attempt: int = 1) -> str:
    digest = hashlib.sha256(
        f"{signal_identity}:{phase}:{attempt}:multislot-v04".encode("utf-8")
    ).hexdigest()[:18]
    return f"ms4-{phase[:3]}-{attempt}-{digest}"


def _session_name(candidate_id: str, signal_identity: str) -> str:
    digest = hashlib.sha256(signal_identity.encode("utf-8")).hexdigest()[:18]
    safe = "".join(ch.lower() if ch.isalnum() else "-" for ch in candidate_id).strip("-")
    return f"{safe[:28]}-{digest}"


def timing_state(now: datetime, target: datetime, max_late_seconds: float) -> str:
    delta = (now.astimezone(timezone.utc) - target.astimezone(timezone.utc)).total_seconds()
    if delta < 0:
        return "WAITING"
    if delta <= max_late_seconds:
        return "DUE"
    return "MISSED_NO_CHASE"


def protective_prices(
    *,
    entry_price: float,
    direction: str,
    stop_distance_fraction: float,
    take_profit_distance_fraction: float,
    price_unit: float,
) -> dict[str, float]:
    for name, value in (
        ("entry_price", entry_price),
        ("stop_distance_fraction", stop_distance_fraction),
        ("take_profit_distance_fraction", take_profit_distance_fraction),
        ("price_unit", price_unit),
    ):
        if not math.isfinite(float(value)) or float(value) <= 0:
            raise MultiSlotEngineError(f"{name} must be positive finite")
    direction = direction.upper()
    if direction == "LONG":
        stop = _ceil_step(entry_price * (1.0 - stop_distance_fraction), price_unit)
        target = _floor_step(entry_price * (1.0 + take_profit_distance_fraction), price_unit)
        if not 0 < stop < entry_price < target:
            raise MultiSlotEngineError("LONG protective geometry invalid")
    elif direction == "SHORT":
        stop = _floor_step(entry_price * (1.0 + stop_distance_fraction), price_unit)
        target = _ceil_step(entry_price * (1.0 - take_profit_distance_fraction), price_unit)
        if not 0 < target < entry_price < stop:
            raise MultiSlotEngineError("SHORT protective geometry invalid")
    else:
        raise MultiSlotEngineError("unsupported direction")
    return {"stop_loss_price": stop, "take_profit_price": target, "price_unit": price_unit}


class OperatorFuturesEngineV04:
    """Three-slot MEXC operator engine.

    The code is mutation-capable but remains inert unless a separate ACTIVE V0.4
    authority, a fresh PASS readiness receipt and an armed marker all exist.
    The repository currently ships only a DRAFT authority; therefore this class
    cannot be activated by the engineering branch alone.
    """

    def __init__(
        self,
        *,
        credentials: MEXCCredentials,
        receipt_root: str,
        policy_path: str,
        activation_authority_path: str,
        readiness_receipt_path: str,
        armed_path: str,
        kill_switch_path: str,
        ledger_path: str,
        status_path: str,
        readonly_client: Any | None = None,
        public_feed: Any | None = None,
        transport_factory: Any | None = None,
    ) -> None:
        self.credentials = credentials
        self.receipt_root = Path(receipt_root)
        self.policy_path = Path(policy_path)
        self.activation_authority_path = Path(activation_authority_path)
        self.readiness_receipt_path = Path(readiness_receipt_path)
        self.armed_path = Path(armed_path)
        self.kill_switch_path = Path(kill_switch_path)
        self.status_path = Path(status_path)
        self.policy = _load(self.policy_path)
        if self.policy.get("policy_id") != "TRIPLE_FISHING_MULTI_SLOT_SMALL_AGGRESSIVE_V0.4":
            raise MultiSlotEngineError("unexpected V0.4 policy")
        if int(self.policy.get("capacity", {}).get("max_simultaneous_positions", 0)) != 3:
            raise MultiSlotEngineError("V0.4 policy must be exactly three slots")
        self.ledger = MultiSlotReservationV04(ledger_path, capacity=3)
        self.readonly = readonly_client or MEXCFuturesAuthenticatedReadOnlyClient(credentials)
        self.public = public_feed or MEXCFuturesPublicFeed(timeout=10)
        self.transport_factory = transport_factory or (
            lambda policy: MEXCMultiSlotFuturesTransportV04(credentials, policy)
        )

    def _status(self, status: str, **extra: Any) -> dict[str, Any]:
        payload = {
            "version": "OPERATOR_FUTURES_ENGINE_V0.4",
            "checked_at_utc": _iso(),
            "status": status,
            "max_simultaneous_positions": 3,
            **extra,
        }
        _atomic_write(self.status_path, payload)
        return payload

    def _assert_live_authorized(self) -> dict[str, Any]:
        blockers: list[str] = []
        authority = None
        readiness = None
        armed = None

        if self.kill_switch_path.exists():
            blockers.append("KILL_SWITCH_PRESENT")

        if not self.activation_authority_path.exists():
            blockers.append("V04_ACTIVE_AUTHORITY_MISSING")
        else:
            try:
                authority = _load(self.activation_authority_path)
                if authority.get("authority_id") != "OPERATOR-FUTURES-GLOBAL-V0.4-ACTIVE":
                    blockers.append("V04_ACTIVE_AUTHORITY_ID_INVALID")
                if authority.get("status") != "ACTIVE":
                    blockers.append("V04_ACTIVE_AUTHORITY_NOT_ACTIVE")
                if int(authority.get("risk", {}).get("max_simultaneous_positions", 0)) != 3:
                    blockers.append("V04_ACTIVE_AUTHORITY_CAPACITY_INVALID")
            except Exception as exc:
                blockers.append(f"V04_ACTIVE_AUTHORITY_INVALID:{type(exc).__name__}")

        if not self.readiness_receipt_path.exists():
            blockers.append("V04_READINESS_RECEIPT_MISSING")
        else:
            try:
                readiness = _load(self.readiness_receipt_path)
                if readiness.get("readiness_id") != "MEXC-TRIPLE-FISHING-MULTISLOT-READY-V0.4":
                    blockers.append("V04_READINESS_ID_INVALID")
                if readiness.get("pass") is not True:
                    blockers.append("V04_READINESS_NOT_PASS")
                readiness_sha256 = _sha256_file(self.readiness_receipt_path)
            except Exception as exc:
                readiness_sha256 = None
                blockers.append(f"V04_READINESS_INVALID:{type(exc).__name__}")

        if not self.armed_path.exists():
            blockers.append("V04_NOT_ARMED")
        else:
            try:
                armed = _load(self.armed_path)
                if armed.get("authority") != "OPERATOR-FUTURES-GLOBAL-V0.4-ACTIVE":
                    blockers.append("V04_ARMED_MARKER_AUTHORITY_INVALID")
                if int(armed.get("max_simultaneous_positions", 0)) != 3:
                    blockers.append("V04_ARMED_MARKER_CAPACITY_INVALID")
                if readiness is not None:
                    expected_ready = str(armed.get("readiness_receipt_sha256") or "")
                    if not expected_ready or expected_ready != readiness_sha256:
                        blockers.append("V04_ARMED_MARKER_READINESS_HASH_MISMATCH")
                if authority is not None:
                    authority_sha256 = _sha256_file(self.activation_authority_path)
                    expected_authority = str(armed.get("active_authority_sha256") or "")
                    if not expected_authority or expected_authority != authority_sha256:
                        blockers.append("V04_ARMED_MARKER_AUTHORITY_HASH_MISMATCH")
                    bound_ready = str(authority.get("readiness_receipt_sha256") or "")
                    if not bound_ready or bound_ready != readiness_sha256:
                        blockers.append("V04_ACTIVE_AUTHORITY_READINESS_HASH_MISMATCH")
            except Exception as exc:
                blockers.append(f"V04_ARMED_MARKER_INVALID:{type(exc).__name__}")

        return {
            "pass": not blockers,
            "blockers": blockers,
            "authority": authority,
            "readiness": readiness,
            "armed": armed,
        }


    def _assert_exit_authorized(self) -> dict[str, Any]:
        """Exits stay available after entry-readiness ages out or kill is raised.

        A live position must never become trapped merely because the 15-minute
        pre-entry readiness receipt is stale. Exit authority still requires the
        explicit ACTIVE V0.4 authority and the V0.4 armed marker.
        """
        blockers: list[str] = []
        authority = None
        armed = None
        if not self.activation_authority_path.exists():
            blockers.append("V04_ACTIVE_AUTHORITY_MISSING")
        else:
            try:
                authority = _load(self.activation_authority_path)
                if authority.get("authority_id") != "OPERATOR-FUTURES-GLOBAL-V0.4-ACTIVE":
                    blockers.append("V04_ACTIVE_AUTHORITY_ID_INVALID")
                if authority.get("status") != "ACTIVE":
                    blockers.append("V04_ACTIVE_AUTHORITY_NOT_ACTIVE")
                if int(authority.get("risk", {}).get("max_simultaneous_positions", 0)) != 3:
                    blockers.append("V04_ACTIVE_AUTHORITY_CAPACITY_INVALID")
            except Exception as exc:
                blockers.append(f"V04_ACTIVE_AUTHORITY_INVALID:{type(exc).__name__}")

        if not self.armed_path.exists():
            blockers.append("V04_NOT_ARMED")
        else:
            try:
                armed = _load(self.armed_path)
                if armed.get("authority") != "OPERATOR-FUTURES-GLOBAL-V0.4-ACTIVE":
                    blockers.append("V04_ARMED_MARKER_AUTHORITY_INVALID")
            except Exception as exc:
                blockers.append(f"V04_ARMED_MARKER_INVALID:{type(exc).__name__}")

        return {
            "pass": not blockers,
            "blockers": blockers,
            "authority": authority,
            "armed": armed,
            "kill_switch_present": self.kill_switch_path.exists(),
        }

    def _lane_profile(self, signal: dict[str, Any]) -> dict[str, Any]:
        candidate = str(signal.get("candidate_id") or signal.get("strategy_id") or "")
        symbol = str(signal.get("symbol") or "").upper()
        direction = str(signal.get("direction") or "").upper()
        lane = self.policy.get("lanes", {}).get(candidate)
        if not isinstance(lane, dict):
            raise MultiSlotEngineError("LANE_NOT_IN_V04_POLICY")

        allowed = {str(x).upper() for x in lane.get("symbol_policy", [])}
        if symbol not in allowed:
            raise MultiSlotEngineError("SYMBOL_NOT_ALLOWED_FOR_LANE")
        if direction not in {"LONG", "SHORT"}:
            raise MultiSlotEngineError("DIRECTION_INVALID")
        if candidate in {BNB, DH03} and direction != "LONG":
            raise MultiSlotEngineError("LANE_DIRECTION_NOT_AUTHORIZED")

        leverage = int(lane["leverage"])
        lane_notional = float(lane["max_notional_usdt"])
        lane_margin = float(lane["max_initial_margin_usdt"])

        if candidate == OPTIONS:
            weight = _finite(signal.get("parent_weight"), "parent_weight")
            if not 0 < weight <= 1:
                raise MultiSlotEngineError("OPTIONS_PARENT_WEIGHT_INVALID")
            target_notional = lane_notional * weight
            target_margin = target_notional / leverage
        else:
            target_notional = lane_notional
            target_margin = target_notional / leverage

        if target_margin > lane_margin + 1e-9:
            raise MultiSlotEngineError("LANE_MARGIN_CAP_INCONSISTENT")

        return {
            "candidate_id": candidate,
            "symbol": symbol,
            "direction": direction,
            "leverage": leverage,
            "lane_notional_cap_usdt": lane_notional,
            "lane_margin_cap_usdt": lane_margin,
            "target_notional_usdt": target_notional,
            "target_initial_margin_usdt": target_margin,
            "max_positions": int(lane.get("max_positions", 1)),
        }

    def _transport(self, profile: dict[str, Any]):
        policy = MultiSlotFuturesPolicy(
            policy_id=f"{profile['candidate_id']}:V04",
            symbol=profile["symbol"],
            allowed_directions=(profile["direction"],),
            required_leverage=int(profile["leverage"]),
        )
        return self.transport_factory(policy)

    def _contract_and_sizing(self, profile: dict[str, Any]) -> dict[str, Any]:
        symbol = profile["symbol"]
        row = self.public.contract_row(symbol)
        snaps = self.public.all_market_snapshots()
        canonical = symbol.replace("_", "")
        snap = snaps.get(canonical)
        if snap is None:
            raise MultiSlotEngineError("MEXC_PUBLIC_SNAPSHOT_MISSING")
        price = float(snap.ask_price if profile["direction"] == "LONG" else snap.bid_price)
        bid = _finite(snap.bid_price, "bid")
        ask = _finite(snap.ask_price, "ask")
        if price <= 0 or ask < bid or bid <= 0:
            raise MultiSlotEngineError("MEXC_PUBLIC_PRICE_INVALID")

        contract_size = _finite(row.get("contractSize"), "contractSize")
        min_vol = _finite(row.get("minVol"), "minVol")
        vol_unit = _finite(row.get("volUnit"), "volUnit")
        price_unit = _finite(row.get("priceUnit"), "priceUnit")
        if min(contract_size, min_vol, vol_unit, price_unit) <= 0:
            raise MultiSlotEngineError("MEXC_CONTRACT_RULE_INVALID")
        if row.get("apiAllowed") is False or row.get("state") not in (None, 0):
            raise MultiSlotEngineError("MEXC_CONTRACT_NOT_API_TRADABLE")

        raw = profile["target_notional_usdt"] / (contract_size * price)
        volume = _floor_step(raw, vol_unit)
        if volume < min_vol:
            raise MultiSlotEngineError("VENUE_MINIMUM_EXCEEDS_LANE_CAP")
        if abs(volume - round(volume)) > 1e-9:
            raise MultiSlotEngineError("NON_INTEGER_CONTRACT_VOLUME_UNSUPPORTED")
        volume_int = int(round(volume))
        notional = volume_int * contract_size * price
        margin = notional / int(profile["leverage"])
        if notional > profile["lane_notional_cap_usdt"] + 1e-9:
            raise MultiSlotEngineError("SIZING_EXCEEDS_LANE_NOTIONAL_CAP")
        if margin > profile["lane_margin_cap_usdt"] + 1e-9:
            raise MultiSlotEngineError("SIZING_EXCEEDS_LANE_MARGIN_CAP")

        mid = (bid + ask) / 2.0
        spread_bps = (ask - bid) / mid * 10000.0
        fee = self.readonly.fee_details(symbol)
        raw_fee = fee.get("realTakerFee")
        if raw_fee is None:
            raw_fee = fee.get("takerFee")
        taker = max(_finite(raw_fee, "takerFee"), OFFICIAL_API_TAKER_FLOOR)
        projected_roundtrip_bps = 2.0 * taker * 10000.0 + spread_bps

        return {
            "volume_contracts": volume_int,
            "estimated_notional_usdt": notional,
            "estimated_initial_margin_usdt": margin,
            "reference_price": price,
            "bid": bid,
            "ask": ask,
            "price_unit": price_unit,
            "contract_size": contract_size,
            "min_vol": min_vol,
            "vol_unit": vol_unit,
            "account_taker_fee_fraction": float(raw_fee),
            "effective_taker_fee_fraction": taker,
            "spread_bps": spread_bps,
            "projected_roundtrip_friction_bps": projected_roundtrip_bps,
        }

    def _active_paths(self) -> list[Path]:
        out: list[Path] = []
        if not self.receipt_root.exists():
            return out
        for path in self.receipt_root.rglob("ACTIVE_TRADE_STATE.json"):
            try:
                row = _load(path)
            except Exception:
                continue
            if row.get("state") not in {"FILLED", "EXIT_PENDING"}:
                continue
            if (path.parent / "POST_TRADE_RECONCILIATION.json").exists():
                continue
            out.append(path)
        return sorted(out)

    def _pending_intent_paths(self) -> list[Path]:
        out: list[Path] = []
        if not self.receipt_root.exists():
            return out
        for path in self.receipt_root.rglob("ORDER_INTENT.json"):
            session = path.parent
            if (
                (session / "ACTIVE_TRADE_STATE.json").exists()
                or (session / "POST_TRADE_RECONCILIATION.json").exists()
                or (session / "ENTRY_TERMINAL_NO_FILL_CONFIRMED.json").exists()
                or (session / "ENTRY_NOT_SUBMITTED_FINAL.json").exists()
            ):
                continue
            out.append(path)
        return sorted(out)

    def _exchange_position_map(self) -> dict[int, dict[str, Any]]:
        rows = self.readonly.open_positions()
        out: dict[int, dict[str, Any]] = {}
        for row in rows:
            pid = int(row.get("positionId", 0) or 0)
            if pid <= 0 or pid in out:
                raise MultiSlotEngineError("EXCHANGE_POSITION_ID_INVALID_OR_DUPLICATE")
            out[pid] = row
        return out

    def _portfolio_reconcile(self) -> dict[str, Any]:
        blockers: list[str] = []
        active_rows: list[dict[str, Any]] = []
        local_by_pid: dict[int, dict[str, Any]] = {}
        local_symbols: set[str] = set()

        for path in self._active_paths():
            try:
                row = _load(path)
                pid = int(row["position_id"])
                symbol = str(row["symbol"]).upper()
                if pid <= 0 or pid in local_by_pid:
                    raise ValueError("position id collision")
                if symbol in local_symbols:
                    raise ValueError("duplicate active symbol")
                row["_path"] = str(path)
                local_by_pid[pid] = row
                local_symbols.add(symbol)
                active_rows.append(row)
            except Exception as exc:
                blockers.append(f"LOCAL_ACTIVE_INVALID:{path}:{type(exc).__name__}")

        try:
            exchange_by_pid = self._exchange_position_map()
        except Exception as exc:
            exchange_by_pid = {}
            blockers.append(f"EXCHANGE_POSITION_READ_FAILED:{type(exc).__name__}")

        for pid, row in local_by_pid.items():
            ex = exchange_by_pid.get(pid)
            if ex is None:
                blockers.append(f"LOCAL_ACTIVE_POSITION_MISSING_ON_EXCHANGE:{pid}")
                continue
            if str(ex.get("symbol") or "").upper() != str(row["symbol"]).upper():
                blockers.append(f"ACTIVE_SYMBOL_MISMATCH:{pid}")
            expected_type = direction_meta(str(row["direction"]))["position_type"]
            if int(ex.get("positionType", 0) or 0) != expected_type:
                blockers.append(f"ACTIVE_DIRECTION_MISMATCH:{pid}")

        for pid in exchange_by_pid:
            if pid not in local_by_pid:
                blockers.append(f"UNOWNED_EXCHANGE_POSITION:{pid}")

        try:
            orders = self.readonly.open_orders()
            if orders:
                blockers.append("UNRESOLVED_REGULAR_OPEN_ORDER_PRESENT")
        except Exception as exc:
            orders = []
            blockers.append(f"OPEN_ORDER_READ_FAILED:{type(exc).__name__}")

        known_tpsl: dict[int, int] = {}
        for row in active_rows:
            protective = int(row.get("protective_tpsl_order_id", 0) or 0)
            if protective > 0:
                known_tpsl[protective] = int(row["position_id"])
        try:
            tpsl = self.readonly.open_tpsl_orders()
            seen = set()
            for row in tpsl:
                oid = int(row.get("id", 0) or 0)
                pid = int(row.get("positionId", 0) or 0)
                if oid <= 0 or oid not in known_tpsl or known_tpsl[oid] != pid:
                    blockers.append(f"UNOWNED_OPEN_TPSL:{oid}:{pid}")
                else:
                    seen.add(oid)
            for row in active_rows:
                oid = int(row.get("protective_tpsl_order_id", 0) or 0)
                if row.get("protective_tpsl_required") is True and oid not in seen:
                    blockers.append(f"REQUIRED_TPSL_MISSING:{row.get('position_id')}")
        except Exception as exc:
            tpsl = []
            blockers.append(f"TPSL_READ_FAILED:{type(exc).__name__}")

        return {
            "pass": not blockers,
            "blockers": list(dict.fromkeys(blockers)),
            "active_rows": active_rows,
            "exchange_positions": list(exchange_by_pid.values()),
            "open_orders": orders,
            "open_tpsl": tpsl,
        }

    def _reservation_rows(self) -> list[dict[str, Any]]:
        return list(self.ledger.current().get("reservations") or [])

    def _admission_gate(self, profile: dict[str, Any]) -> dict[str, Any]:
        blockers: list[str] = []
        recon = self._portfolio_reconcile()
        blockers.extend(recon["blockers"])

        reservations = self._reservation_rows()
        active_by_signal = {
            str(row.get("signal_identity") or ""): row
            for row in recon["active_rows"]
            if str(row.get("signal_identity") or "")
        }

        occupied: dict[str, dict[str, Any]] = {}
        for row in reservations:
            sig = str(row.get("signal_identity") or "")
            if sig:
                occupied[sig] = {
                    "candidate_id": str(row.get("candidate_id") or ""),
                    "symbol": str(row.get("symbol") or "").upper(),
                    "notional": float(row.get("max_notional_usdt", 0) or 0),
                    "margin": float(row.get("max_initial_margin_usdt", 0) or 0),
                }
        for sig, row in active_by_signal.items():
            occupied[sig] = {
                "candidate_id": str(row.get("candidate_id") or ""),
                "symbol": str(row.get("symbol") or "").upper(),
                "notional": float(row.get("planned_notional_usdt", row.get("estimated_notional_usdt", 0)) or 0),
                "margin": float(row.get("planned_initial_margin_usdt", row.get("estimated_initial_margin_usdt", 0)) or 0),
            }

        rows = list(occupied.values())
        if len(rows) >= 3:
            blockers.append("THREE_SLOT_CAPACITY_FULL")
        if any(row["symbol"] == profile["symbol"] for row in rows):
            blockers.append("SYMBOL_ALREADY_ACTIVE_OR_RESERVED")

        lane_count = sum(
            1 for row in rows if row["candidate_id"] == profile["candidate_id"]
        )
        if lane_count >= int(profile["max_positions"]):
            blockers.append("LANE_POSITION_CAP_FULL")

        used_notional = sum(row["notional"] for row in rows)
        used_margin = sum(row["margin"] for row in rows)
        projected_notional = used_notional + float(profile["lane_notional_cap_usdt"])
        projected_margin = used_margin + float(profile["lane_margin_cap_usdt"])
        global_cfg = self.policy["global_risk"]
        if projected_notional > float(global_cfg["max_total_notional_usdt"]) + 1e-9:
            blockers.append("GLOBAL_NOTIONAL_CAP_EXCEEDED")
        if projected_margin > float(global_cfg["max_total_initial_margin_usdt"]) + 1e-9:
            blockers.append("GLOBAL_INITIAL_MARGIN_CAP_EXCEEDED")

        try:
            mode = self.readonly.position_mode()
            if int(mode) != 1:
                blockers.append("FUTURES_POSITION_MODE_NOT_HEDGE")
        except Exception as exc:
            blockers.append(f"POSITION_MODE_READ_FAILED:{type(exc).__name__}")

        try:
            before = time.time_ns() / 1_000_000.0
            server = float(self.public.server_time_ms())
            after = time.time_ns() / 1_000_000.0
            midpoint = (before + after) / 2.0
            if abs(server - midpoint) > MAX_CLOCK_OFFSET_MS:
                blockers.append("CLOCK_OFFSET_OUTSIDE_500MS")
        except Exception as exc:
            blockers.append(f"CLOCK_CHECK_FAILED:{type(exc).__name__}")

        losses = realized_loss_state(self.receipt_root, now=datetime.now(timezone.utc))
        if losses["invalid_reconciliations"]:
            blockers.append("LOCAL_RECONCILIATION_ACCOUNTING_INVALID")
        if losses["daily_realized_loss_usdt"] >= float(global_cfg["daily_realized_loss_kill_usdt"]):
            blockers.append("DAILY_REALIZED_LOSS_KILL_ACTIVE")
        if losses["rolling_7d_realized_loss_usdt"] >= float(global_cfg["rolling_7d_realized_loss_kill_usdt"]):
            blockers.append("ROLLING_7D_REALIZED_LOSS_KILL_ACTIVE")

        try:
            assets = self.readonly.assets()
            usdt = next(row for row in assets if str(row.get("currency", "")).upper() == "USDT")
            available = _finite(usdt.get("availableBalance"), "availableBalance")
            equity = _finite(usdt.get("equity"), "equity")
            if available < float(profile["lane_margin_cap_usdt"]):
                blockers.append("AVAILABLE_MARGIN_BELOW_LANE_CAP")
            if equity <= 0:
                blockers.append("ACCOUNT_EQUITY_INVALID")
        except Exception as exc:
            available = None
            equity = None
            blockers.append(f"ACCOUNT_BALANCE_READ_FAILED:{type(exc).__name__}")

        return {
            "pass": not blockers,
            "blockers": list(dict.fromkeys(blockers)),
            "occupied_positions_or_reservations": len(rows),
            "used_notional_usdt": used_notional,
            "used_initial_margin_usdt": used_margin,
            "projected_notional_cap_usdt": projected_notional,
            "projected_initial_margin_cap_usdt": projected_margin,
            "available_usdt": available,
            "equity_usdt": equity,
            "loss_state": losses,
            "portfolio_reconciliation": {
                "pass": recon["pass"],
                "blockers": recon["blockers"],
            },
        }

    def _wait_order(self, *, symbol: str, external_oid: str, timeout: float = 5.0) -> dict[str, Any]:
        deadline = time.monotonic() + timeout
        last = None
        while time.monotonic() < deadline:
            try:
                last = self.readonly.order_by_external(symbol=symbol, external_oid=external_oid)
                if int(last.get("state", 0) or 0) in (3, 4, 5):
                    return last
            except Exception:
                pass
            time.sleep(0.25)
        if isinstance(last, dict):
            return last
        raise MultiSlotEngineError("ORDER_LOOKUP_TIMEOUT")

    def _find_position(self, *, symbol: str, direction: str, timeout: float = 5.0) -> dict[str, Any] | None:
        deadline = time.monotonic() + timeout
        expected_type = direction_meta(direction)["position_type"]
        while time.monotonic() < deadline:
            rows = self.readonly.open_positions(symbol)
            matches = [
                row for row in rows
                if str(row.get("symbol") or "").upper() == symbol
                and int(row.get("positionType", 0) or 0) == expected_type
                and float(row.get("holdVol", 0) or 0) > 0
            ]
            if len(matches) > 1:
                raise MultiSlotEngineError("MULTIPLE_MATCHING_POSITIONS_SAME_SYMBOL_DIRECTION")
            if matches:
                return matches[0]
            time.sleep(0.25)
        return None

    def _configure_and_verify_leverage(
        self,
        *,
        transport: Any,
        profile: dict[str, Any],
        session: Path,
    ) -> None:
        ack = transport.configure_isolated_leverage(
            symbol=profile["symbol"],
            direction=profile["direction"],
        )
        _atomic_write(session / "LEVERAGE_CONFIGURATION_ACK.json", {
            "receipt_type": "LEVERAGE_CONFIGURATION_ACK",
            "leverage": profile["leverage"],
            "margin_mode": "ISOLATED",
            "exchange_ack": ack,
        })
        meta = direction_meta(profile["direction"])
        rows = [
            row for row in self.readonly.leverage(profile["symbol"])
            if int(row.get("positionType", 0) or 0) == meta["position_type"]
        ]
        ok = (
            len(rows) == 1
            and int(rows[0].get("leverage", 0) or 0) == int(profile["leverage"])
            and int(rows[0].get("openType", 0) or 0) == 1
        )
        _atomic_write(session / "LEVERAGE_POST_VERIFY.json", {
            "receipt_type": "LEVERAGE_POST_VERIFY",
            "pass": ok,
            "rows": rows,
        })
        if not ok:
            raise MultiSlotEngineError("LANE_LEVERAGE_POST_VERIFY_FAILED")

    def _install_protection(
        self,
        *,
        signal: dict[str, Any],
        profile: dict[str, Any],
        position: dict[str, Any],
        fill_price: float,
        sizing: dict[str, Any],
        transport: Any,
        session: Path,
    ) -> dict[str, Any] | None:
        protective = signal.get("protective_exit")
        if not isinstance(protective, dict) or protective.get("required") is not True:
            return None
        prices = protective_prices(
            entry_price=fill_price,
            direction=profile["direction"],
            stop_distance_fraction=_finite(protective.get("stop_distance_fraction"), "stop_distance_fraction"),
            take_profit_distance_fraction=_finite(protective.get("take_profit_distance_fraction"), "take_profit_distance_fraction"),
            price_unit=float(sizing["price_unit"]),
        )
        pid = int(position["positionId"])
        volume = int(sizing["volume_contracts"])
        ack = transport.place_position_tpsl(
            symbol=profile["symbol"],
            direction=profile["direction"],
            position_id=pid,
            volume_contracts=volume,
            stop_loss_price=prices["stop_loss_price"],
            take_profit_price=prices["take_profit_price"],
        )
        _atomic_write(session / "PROTECTIVE_TPSL_ACK.json", {
            "receipt_type": "PROTECTIVE_TPSL_ACK",
            "position_id": pid,
            "exchange_ack": ack,
            **prices,
        })
        time.sleep(0.35)
        rows = self.readonly.open_tpsl_orders(profile["symbol"])
        matches = []
        for row in rows:
            try:
                if int(row.get("positionId", 0) or 0) != pid:
                    continue
                if int(row.get("state", 1) or 1) != 1:
                    continue
                stop = float(row.get("stopLossPrice", 0) or 0)
                target = float(row.get("takeProfitPrice", 0) or 0)
                vol = float(row.get("vol", 0) or 0)
                if abs(stop - prices["stop_loss_price"]) > prices["price_unit"] / 2:
                    continue
                if abs(target - prices["take_profit_price"]) > prices["price_unit"] / 2:
                    continue
                if abs(vol - volume) > 1e-9:
                    continue
                matches.append(row)
            except Exception:
                continue
        if len(matches) != 1:
            raise MultiSlotEngineError(f"PROTECTIVE_TPSL_POST_VERIFY_FAILED:{len(matches)}")
        oid = int(matches[0].get("id", 0) or 0)
        if oid <= 0:
            raise MultiSlotEngineError("PROTECTIVE_TPSL_ID_INVALID")
        verify = {
            "receipt_type": "PROTECTIVE_TPSL_VERIFY",
            "pass": True,
            "position_id": pid,
            "protective_order_id": oid,
            "volume_contracts": volume,
            **prices,
        }
        _atomic_write(session / "PROTECTIVE_TPSL_VERIFY.json", verify)
        return verify

    def _finalize_filled_entry(
        self,
        *,
        signal: dict[str, Any],
        profile: dict[str, Any],
        sizing: dict[str, Any],
        order: dict[str, Any],
        position: dict[str, Any],
        session: Path,
        transport: Any,
    ) -> dict[str, Any]:
        pid = int(position.get("positionId", 0) or 0)
        if pid <= 0:
            raise MultiSlotEngineError("POSITION_ID_INVALID")
        if int(position.get("leverage", 0) or 0) != int(profile["leverage"]):
            raise MultiSlotEngineError("POSITION_LEVERAGE_MISMATCH")
        if int(position.get("openType", 0) or 0) != 1:
            raise MultiSlotEngineError("POSITION_NOT_ISOLATED")

        transport.set_auto_add_margin(position_id=pid, enabled=False)
        time.sleep(0.2)
        refreshed = self._find_position(
            symbol=profile["symbol"], direction=profile["direction"], timeout=2.0
        )
        if refreshed is None:
            raise MultiSlotEngineError("POSITION_DISAPPEARED_DURING_POST_VERIFY")
        if bool(refreshed.get("autoAddIm")):
            raise MultiSlotEngineError("AUTO_MARGIN_ADD_NOT_DISABLED")

        fill_price = float(order.get("dealAvgPrice") or refreshed.get("openAvgPrice") or 0)
        if not math.isfinite(fill_price) or fill_price <= 0:
            raise MultiSlotEngineError("ENTRY_FILL_PRICE_INVALID")

        protection = self._install_protection(
            signal=signal,
            profile=profile,
            position=refreshed,
            fill_price=fill_price,
            sizing=sizing,
            transport=transport,
            session=session,
        )

        active = {
            "state": "EXIT_PENDING",
            "candidate_id": profile["candidate_id"],
            "strategy_id": profile["candidate_id"],
            "signal_identity": str(signal["immutable_signal_key"]),
            "symbol": profile["symbol"],
            "direction": profile["direction"],
            "position_id": int(refreshed["positionId"]),
            "volume_contracts": int(sizing["volume_contracts"]),
            "entry_external_oid": str(order.get("externalOid") or _oid(str(signal["immutable_signal_key"]), "entry", 1)),
            "entry_target_utc": str(signal["entry_target_utc"]),
            "exit_target_utc": str(signal["exit_target_utc"]),
            "entry_price": fill_price,
            "planned_notional_usdt": sizing["estimated_notional_usdt"],
            "planned_initial_margin_usdt": sizing["estimated_initial_margin_usdt"],
            "leverage": int(profile["leverage"]),
            "margin_mode": "ISOLATED",
            "protective_tpsl_required": protection is not None,
            "protective_tpsl_order_id": int(protection["protective_order_id"]) if protection else None,
            "protective_stop_loss_price": protection.get("stop_loss_price") if protection else None,
            "protective_take_profit_price": protection.get("take_profit_price") if protection else None,
            "protective_price_unit": protection.get("price_unit") if protection else None,
            "opened_at_utc": _iso(),
            "scientific_credit": False,
        }
        _atomic_write(session / "ACTIVE_TRADE_STATE.json", active)
        return self._status(
            "FILLED_EXIT_PENDING",
            candidate_id=profile["candidate_id"],
            signal_identity=signal["immutable_signal_key"],
            symbol=profile["symbol"],
            position_id=active["position_id"],
            leverage=profile["leverage"],
            planned_notional_usdt=active["planned_notional_usdt"],
            session_dir=str(session),
        )

    def enter_signal(self, signal: dict[str, Any]) -> dict[str, Any]:
        auth = self._assert_live_authorized()
        if not auth["pass"]:
            return self._status("FAIL_CLOSED_NOT_AUTHORIZED", blockers=auth["blockers"])

        now = datetime.now(timezone.utc)
        candidate = str(signal.get("candidate_id") or signal.get("strategy_id") or "")
        signal_key = str(signal.get("immutable_signal_key") or "")
        if not candidate or not signal_key:
            return self._status("FAIL_CLOSED", blockers=["SIGNAL_IDENTITY_MISSING"])

        session = self.receipt_root / _session_name(candidate, signal_key)
        session.mkdir(parents=True, exist_ok=True)
        intent_path = session / "ORDER_INTENT.json"

        if intent_path.exists():
            return self._recover_entry_intent(intent_path)

        try:
            profile = self._lane_profile(signal)
            target = _utc(signal["entry_target_utc"])
            max_late = _finite(signal.get("max_late_seconds"), "max_late_seconds")
            timing = timing_state(now, target, max_late)
            if timing != "DUE":
                return self._status(
                    "WAITING_ENTRY_TARGET" if timing == "WAITING" else "FAIL_CLOSED",
                    candidate_id=candidate,
                    signal_identity=signal_key,
                    blockers=[] if timing == "WAITING" else ["MISSED_NO_CHASE"],
                )

            admission = self._admission_gate(profile)
            if not admission["pass"]:
                return self._status(
                    "FAIL_CLOSED",
                    candidate_id=candidate,
                    signal_identity=signal_key,
                    blockers=admission["blockers"],
                    admission=admission,
                )

            sizing = self._contract_and_sizing(profile)
            friction_cap = _finite(
                signal.get("max_projected_roundtrip_friction_bps"),
                "max_projected_roundtrip_friction_bps",
            )
            if sizing["projected_roundtrip_friction_bps"] > friction_cap + 1e-9:
                raise MultiSlotEngineError("PROJECTED_FRICTION_EXCEEDS_SIGNAL_CEILING")

            ext = _oid(signal_key, "entry", 1)
            _atomic_write(session / "CANONICAL_OPERATOR_SIGNAL.json", signal)
            gate = {
                "receipt_type": "PRE_ORDER_GATE",
                "pass": True,
                "candidate_id": candidate,
                "signal_identity": signal_key,
                "profile": profile,
                "sizing": sizing,
                "admission": admission,
                "timing_state": timing,
                "entry_target_utc": signal["entry_target_utc"],
                "exit_target_utc": signal["exit_target_utc"],
            }
            _atomic_write(session / "PRE_ORDER_GATE.json", gate)

            claim = self.ledger.claim(
                candidate_id=candidate,
                signal_identity=signal_key,
                external_oid=ext,
                symbol=profile["symbol"],
                leverage=int(profile["leverage"]),
                max_notional_usdt=float(profile["lane_notional_cap_usdt"]),
                max_initial_margin_usdt=float(profile["lane_margin_cap_usdt"]),
            )
            if claim.get("claim_status") not in {"CLAIMED", "RECOVERED_EXISTING_OWNER"}:
                return self._status(
                    "FAIL_CLOSED",
                    candidate_id=candidate,
                    signal_identity=signal_key,
                    blockers=[str(claim.get("claim_status") or "RESERVATION_FAILED")],
                    reservation=claim,
                )

            transport = self._transport(profile)
            try:
                self._configure_and_verify_leverage(
                    transport=transport, profile=profile, session=session
                )
                # Reconcile known positions after reservation; existing owned
                # positions are allowed, unowned exchange state is not.
                last = self._portfolio_reconcile()
                if not last["pass"]:
                    raise MultiSlotEngineError(
                        "LAST_MOMENT_PORTFOLIO_CONFLICT:" + ",".join(last["blockers"])
                    )
            except Exception as exc:
                _atomic_write(session / "ENTRY_NOT_SUBMITTED_FINAL.json", {
                    "receipt_type": "ENTRY_NOT_SUBMITTED_FINAL",
                    "signal_identity": signal_key,
                    "external_oid": ext,
                    "reason": f"{type(exc).__name__}:{exc}",
                    "order_submitted": False,
                })
                self.ledger.release(
                    signal_identity=signal_key,
                    reason="PRE_SUBMIT_ABORT_CONFIRMED",
                )
                return self._status(
                    "FAIL_CLOSED",
                    candidate_id=candidate,
                    signal_identity=signal_key,
                    blockers=[f"PRE_SUBMIT_ABORT:{type(exc).__name__}:{exc}"],
                )

            intent = {
                "receipt_type": "ORDER_INTENT",
                "candidate_id": candidate,
                "signal_identity": signal_key,
                "symbol": profile["symbol"],
                "direction": profile["direction"],
                "entry_target_utc": signal["entry_target_utc"],
                "exit_target_utc": signal["exit_target_utc"],
                "volume_contracts": int(sizing["volume_contracts"]),
                "estimated_notional_usdt": sizing["estimated_notional_usdt"],
                "estimated_initial_margin_usdt": sizing["estimated_initial_margin_usdt"],
                "leverage": int(profile["leverage"]),
                "margin_mode": "ISOLATED",
                "external_oid": ext,
                "protective_exit": signal.get("protective_exit"),
            }
            if not _exclusive_write(intent_path, intent):
                return self._status(
                    "ENTRY_RECONCILIATION_REQUIRED",
                    candidate_id=candidate,
                    signal_identity=signal_key,
                    reason="ORDER_INTENT_RACE_DETECTED",
                    blind_resend_allowed=False,
                )

            auth2 = self._assert_live_authorized()
            if not auth2["pass"]:
                _atomic_write(session / "ENTRY_NOT_SUBMITTED_FINAL.json", {
                    "receipt_type": "ENTRY_NOT_SUBMITTED_FINAL",
                    "signal_identity": signal_key,
                    "external_oid": ext,
                    "reason": "FINAL_SEND_AUTHORITY_GATE_FAILED",
                    "blockers": auth2["blockers"],
                    "order_submitted": False,
                })
                self.ledger.release(
                    signal_identity=signal_key,
                    reason="PRE_SUBMIT_ABORT_CONFIRMED",
                )
                return self._status(
                    "FAIL_CLOSED_NOT_AUTHORIZED",
                    candidate_id=candidate,
                    signal_identity=signal_key,
                    blockers=auth2["blockers"],
                )

            try:
                ack = transport.submit_market_order(
                    symbol=profile["symbol"],
                    direction=profile["direction"],
                    phase="ENTRY",
                    volume_contracts=int(sizing["volume_contracts"]),
                    external_oid=ext,
                )
            except Exception as exc:
                _atomic_write(session / "ENTRY_ACK_UNKNOWN.json", {
                    "receipt_type": "ENTRY_ACK_UNKNOWN",
                    "external_oid": ext,
                    "error": f"{type(exc).__name__}:{exc}",
                    "blind_resend_allowed": False,
                })
                return self._status(
                    "ENTRY_RECONCILIATION_REQUIRED",
                    candidate_id=candidate,
                    signal_identity=signal_key,
                    blind_resend_allowed=False,
                    reservation_retained=True,
                )

            _atomic_write(session / "ENTRY_EXCHANGE_ACK.json", {
                "receipt_type": "ENTRY_EXCHANGE_ACK",
                "external_oid": ext,
                "exchange_ack": ack,
            })
            order = self._wait_order(symbol=profile["symbol"], external_oid=ext)
            if int(order.get("state", 0) or 0) not in (3, 4, 5):
                cancel = transport.cancel_by_external(
                    symbol=profile["symbol"], external_oid=ext
                )
                _atomic_write(session / "ENTRY_CANCEL_ACK.json", {
                    "receipt_type": "ENTRY_CANCEL_ACK",
                    "exchange_ack": cancel,
                    "last_order": order,
                })
                order = self._wait_order(
                    symbol=profile["symbol"], external_oid=ext, timeout=3.0
                )

            if float(order.get("dealVol", 0) or 0) <= 0:
                _atomic_write(session / "ENTRY_TERMINAL_NO_FILL_CONFIRMED.json", {
                    "receipt_type": "ENTRY_TERMINAL_NO_FILL_CONFIRMED",
                    "signal_identity": signal_key,
                    "external_oid": ext,
                    "order": order,
                    "trade_opened": False,
                })
                self.ledger.release(
                    signal_identity=signal_key,
                    reason="ENTRY_TERMINAL_NO_FILL_CONFIRMED",
                )
                return self._status(
                    "FAIL_CLOSED",
                    candidate_id=candidate,
                    signal_identity=signal_key,
                    blockers=["ENTRY_ORDER_NOT_FILLED"],
                )

            position = self._find_position(
                symbol=profile["symbol"], direction=profile["direction"]
            )
            if position is None:
                return self._status(
                    "ENTRY_RECONCILIATION_REQUIRED",
                    candidate_id=candidate,
                    signal_identity=signal_key,
                    reason="FILLED_ORDER_WITHOUT_MATCHING_POSITION",
                    reservation_retained=True,
                )

            return self._finalize_filled_entry(
                signal=signal,
                profile=profile,
                sizing=sizing,
                order=order,
                position=position,
                session=session,
                transport=transport,
            )
        except Exception as exc:
            return self._status(
                "FAIL_CLOSED",
                candidate_id=candidate,
                signal_identity=signal_key,
                blockers=[f"{type(exc).__name__}:{exc}"],
                session_dir=str(session),
            )

    def _recover_entry_intent(self, intent_path: Path) -> dict[str, Any]:
        session = intent_path.parent
        intent = _load(intent_path)
        candidate = str(intent["candidate_id"])
        signal_key = str(intent["signal_identity"])
        signal = _load(session / "CANONICAL_OPERATOR_SIGNAL.json")
        gate = _load(session / "PRE_ORDER_GATE.json")
        profile = gate["profile"]
        sizing = gate["sizing"]
        ext = str(intent["external_oid"])

        claim = self.ledger.claim(
            candidate_id=candidate,
            signal_identity=signal_key,
            external_oid=ext,
            symbol=profile["symbol"],
            leverage=int(profile["leverage"]),
            max_notional_usdt=float(profile["lane_notional_cap_usdt"]),
            max_initial_margin_usdt=float(profile["lane_margin_cap_usdt"]),
        )
        if claim.get("claim_status") not in {"CLAIMED", "RECOVERED_EXISTING_OWNER"}:
            return self._status(
                "ENTRY_RECONCILIATION_REQUIRED",
                candidate_id=candidate,
                signal_identity=signal_key,
                reason="RESERVATION_OWNERSHIP_NOT_PROVEN",
                reservation=claim,
            )
        try:
            order = self.readonly.order_by_external(
                symbol=profile["symbol"], external_oid=ext
            )
        except Exception as exc:
            return self._status(
                "ENTRY_RECONCILIATION_REQUIRED",
                candidate_id=candidate,
                signal_identity=signal_key,
                reason=f"ORDER_IDENTITY_NOT_YET_PROVABLE:{type(exc).__name__}",
                blind_resend_allowed=False,
            )

        position = self._find_position(
            symbol=profile["symbol"], direction=profile["direction"], timeout=1.5
        )
        if float(order.get("dealVol", 0) or 0) <= 0:
            terminal = int(order.get("state", 0) or 0) in (3, 4, 5)
            if terminal and position is None:
                _atomic_write(session / "ENTRY_TERMINAL_NO_FILL_CONFIRMED.json", {
                    "receipt_type": "ENTRY_TERMINAL_NO_FILL_CONFIRMED",
                    "signal_identity": signal_key,
                    "external_oid": ext,
                    "order": order,
                    "trade_opened": False,
                })
                self.ledger.release(
                    signal_identity=signal_key,
                    reason="ENTRY_TERMINAL_NO_FILL_CONFIRMED",
                )
                return self._status(
                    "ENTRY_TERMINAL_NO_FILL_CONFIRMED",
                    candidate_id=candidate,
                    signal_identity=signal_key,
                )
            return self._status(
                "ENTRY_RECONCILIATION_REQUIRED",
                candidate_id=candidate,
                signal_identity=signal_key,
                reason="INTENT_EXISTS_BUT_FILL_NOT_PROVEN",
                blind_resend_allowed=False,
            )

        if position is None:
            return self._status(
                "ENTRY_RECONCILIATION_REQUIRED",
                candidate_id=candidate,
                signal_identity=signal_key,
                reason="FILLED_ORDER_WITHOUT_MATCHING_POSITION",
                blind_resend_allowed=False,
            )
        transport = self._transport(profile)
        return self._finalize_filled_entry(
            signal=signal,
            profile=profile,
            sizing=sizing,
            order=order,
            position=position,
            session=session,
            transport=transport,
        )

    def reconcile_pending_entries(self) -> list[dict[str, Any]]:
        results = []
        for path in self._pending_intent_paths():
            try:
                results.append(self._recover_entry_intent(path))
            except Exception as exc:
                results.append({
                    "status": "ENTRY_RECONCILIATION_REQUIRED",
                    "session_dir": str(path.parent),
                    "error": f"{type(exc).__name__}:{exc}",
                })
        return results

    def _historical_position(self, active: dict[str, Any]) -> dict[str, Any] | None:
        opened = _utc(active.get("opened_at_utc") or active["entry_target_utc"])
        rows = self.readonly.historical_positions(
            symbol=str(active["symbol"]),
            position_type=direction_meta(str(active["direction"]))["position_type"],
            start_time=int((opened - timedelta(hours=1)).timestamp() * 1000),
            end_time=int((datetime.now(timezone.utc) + timedelta(minutes=2)).timestamp() * 1000),
        )
        matches = [
            row for row in rows
            if int(row.get("positionId", 0) or 0) == int(active["position_id"])
        ]
        if len(matches) > 1:
            raise MultiSlotEngineError("MULTIPLE_HISTORICAL_POSITION_MATCHES")
        return matches[0] if matches else None

    def _reconcile_closed(self, active_path: Path, active: dict[str, Any], *, exit_reason: str) -> dict[str, Any]:
        session = active_path.parent
        hist = self._historical_position(active)
        if hist is None or int(hist.get("state", 0) or 0) != 3:
            return {
                "status": "CLOSE_RECONCILIATION_REQUIRED",
                "candidate_id": active.get("candidate_id"),
                "signal_identity": active.get("signal_identity"),
                "reason": "CLOSED_POSITION_HISTORY_NOT_YET_PROVEN",
            }

        realized = _finite(hist.get("realised"), "historical.realised")
        close_price = _finite(hist.get("closeAvgPrice"), "historical.closeAvgPrice")
        reconciliation = {
            "receipt_type": "POST_TRADE_RECONCILIATION",
            "candidate_id": active.get("candidate_id"),
            "strategy_id": active.get("strategy_id"),
            "signal_identity": active["signal_identity"],
            "symbol": active["symbol"],
            "closed_at_utc": _iso(),
            "realized_net_pnl_usdt": realized,
            "entry_price": active.get("entry_price"),
            "exit_price": close_price,
            "planned_notional_usdt": active.get("planned_notional_usdt"),
            "planned_initial_margin_usdt": active.get("planned_initial_margin_usdt"),
            "leverage": active.get("leverage"),
            "margin_mode": "ISOLATED",
            "scientific_credit": False,
            "exit_reason": exit_reason,
            "historical_position": hist,
            "open_position_after_reconciliation": False,
        }
        _atomic_write(session / "POST_TRADE_RECONCILIATION.json", reconciliation)
        active["state"] = "CLOSED"
        active["closed_at_utc"] = reconciliation["closed_at_utc"]
        active["exit_reason"] = exit_reason
        _atomic_write(active_path, active)
        release = self.ledger.release(
            signal_identity=str(active["signal_identity"]),
            reason="POST_TRADE_RECONCILIATION_CONFIRMED",
        )
        return {
            "status": "CLOSED_RECONCILED",
            "candidate_id": active.get("candidate_id"),
            "signal_identity": active.get("signal_identity"),
            "realized_net_pnl_usdt": realized,
            "exit_reason": exit_reason,
            "release": release,
        }

    def _verify_protection(self, active: dict[str, Any]) -> bool:
        if active.get("protective_tpsl_required") is not True:
            return True
        oid = int(active.get("protective_tpsl_order_id", 0) or 0)
        pid = int(active.get("position_id", 0) or 0)
        rows = self.readonly.open_tpsl_orders(str(active["symbol"]))
        matches = [
            row for row in rows
            if int(row.get("id", 0) or 0) == oid
            and int(row.get("positionId", 0) or 0) == pid
            and int(row.get("state", 1) or 1) == 1
        ]
        return len(matches) == 1

    def _request_exit(
        self,
        *,
        active_path: Path,
        active: dict[str, Any],
        position: dict[str, Any],
        reason: str,
    ) -> dict[str, Any]:
        auth = self._assert_exit_authorized()
        if not auth["pass"]:
            return {
                "status": "EXIT_BLOCKED_NOT_AUTHORIZED",
                "signal_identity": active.get("signal_identity"),
                "blockers": auth["blockers"],
            }

        session = active_path.parent
        signal_key = str(active["signal_identity"])
        exit_intent = session / "EXIT_ORDER_INTENT.json"
        ext = _oid(signal_key, "exit", 1)
        if exit_intent.exists():
            intent = _load(exit_intent)
            ext = str(intent["external_oid"])
            try:
                order = self.readonly.order_by_external(
                    symbol=str(active["symbol"]), external_oid=ext
                )
            except Exception as exc:
                return {
                    "status": "EXIT_RECONCILIATION_REQUIRED",
                    "signal_identity": signal_key,
                    "reason": f"EXIT_ORDER_NOT_YET_PROVABLE:{type(exc).__name__}",
                    "blind_resend_allowed": False,
                }
            if float(order.get("dealVol", 0) or 0) <= 0:
                return {
                    "status": "EXIT_RECONCILIATION_REQUIRED",
                    "signal_identity": signal_key,
                    "reason": "EXIT_INTENT_EXISTS_BUT_FILL_NOT_PROVEN",
                    "blind_resend_allowed": False,
                }
            remaining = self._find_position(
                symbol=str(active["symbol"]),
                direction=str(active["direction"]),
                timeout=1.0,
            )
            if remaining is not None:
                return {
                    "status": "EXIT_RECONCILIATION_REQUIRED",
                    "signal_identity": signal_key,
                    "reason": "EXIT_ORDER_FILLED_BUT_POSITION_STILL_OPEN",
                }
            return self._reconcile_closed(active_path, active, exit_reason=reason)

        volume = int(float(position.get("holdVol", 0) or 0))
        if volume <= 0:
            return self._reconcile_closed(active_path, active, exit_reason=reason)

        intent = {
            "receipt_type": "EXIT_ORDER_INTENT",
            "candidate_id": active.get("candidate_id"),
            "signal_identity": signal_key,
            "symbol": active["symbol"],
            "direction": active["direction"],
            "position_id": int(active["position_id"]),
            "volume_contracts": volume,
            "external_oid": ext,
            "reason": reason,
            "blind_resend_allowed": False,
        }
        if not _exclusive_write(exit_intent, intent):
            return {
                "status": "EXIT_RECONCILIATION_REQUIRED",
                "signal_identity": signal_key,
                "reason": "EXIT_INTENT_RACE",
            }

        profile = {
            "candidate_id": active["candidate_id"],
            "symbol": active["symbol"],
            "direction": active["direction"],
            "leverage": int(active["leverage"]),
        }
        transport = self._transport(profile)
        try:
            ack = transport.submit_market_order(
                symbol=str(active["symbol"]),
                direction=str(active["direction"]),
                phase="EXIT",
                volume_contracts=volume,
                external_oid=ext,
                position_id=int(active["position_id"]),
            )
        except Exception as exc:
            _atomic_write(session / "EXIT_ACK_UNKNOWN.json", {
                "receipt_type": "EXIT_ACK_UNKNOWN",
                "external_oid": ext,
                "error": f"{type(exc).__name__}:{exc}",
                "blind_resend_allowed": False,
            })
            return {
                "status": "EXIT_RECONCILIATION_REQUIRED",
                "signal_identity": signal_key,
                "reason": "EXIT_ACK_UNKNOWN",
                "blind_resend_allowed": False,
            }

        _atomic_write(session / "EXIT_EXCHANGE_ACK.json", {
            "receipt_type": "EXIT_EXCHANGE_ACK",
            "external_oid": ext,
            "exchange_ack": ack,
        })
        self._wait_order(symbol=str(active["symbol"]), external_oid=ext, timeout=5.0)
        remaining = self._find_position(
            symbol=str(active["symbol"]),
            direction=str(active["direction"]),
            timeout=2.0,
        )
        if remaining is not None:
            return {
                "status": "EXIT_RECONCILIATION_REQUIRED",
                "signal_identity": signal_key,
                "reason": "POSITION_STILL_OPEN_AFTER_EXIT_ACK",
            }
        return self._reconcile_closed(active_path, active, exit_reason=reason)

    def _manage_one_active(self, active_path: Path) -> dict[str, Any]:
        active = _load(active_path)
        symbol = str(active["symbol"]).upper()
        direction = str(active["direction"]).upper()
        pid = int(active["position_id"])
        rows = self.readonly.open_positions(symbol)
        matches = [
            row for row in rows
            if int(row.get("positionId", 0) or 0) == pid
        ]
        if len(matches) > 1:
            return {
                "status": "ACTIVE_FAIL_CLOSED",
                "signal_identity": active.get("signal_identity"),
                "reason": "MULTIPLE_EXCHANGE_POSITION_ID_MATCHES",
            }

        if not matches:
            reason = (
                "PROTECTIVE_OR_EXTERNAL_CLOSE"
                if active.get("protective_tpsl_required")
                else "POSITION_MISSING_RECONCILE"
            )
            return self._reconcile_closed(active_path, active, exit_reason=reason)

        position = matches[0]
        if self.kill_switch_path.exists():
            return self._request_exit(
                active_path=active_path,
                active=active,
                position=position,
                reason="KILL_SWITCH_EMERGENCY_EXIT",
            )
        if int(position.get("leverage", 0) or 0) != int(active["leverage"]):
            return self._request_exit(
                active_path=active_path,
                active=active,
                position=position,
                reason="ACTIVE_LEVERAGE_DRIFT_EMERGENCY_EXIT",
            )
        if int(position.get("openType", 0) or 0) != 1 or bool(position.get("autoAddIm")):
            return self._request_exit(
                active_path=active_path,
                active=active,
                position=position,
                reason="ACTIVE_MARGIN_MODE_DRIFT_EMERGENCY_EXIT",
            )
        if active.get("protective_tpsl_required") and not self._verify_protection(active):
            return self._request_exit(
                active_path=active_path,
                active=active,
                position=position,
                reason="ACTIVE_PROTECTIVE_TPSL_NOT_VERIFIED",
            )

        if datetime.now(timezone.utc) >= _utc(active["exit_target_utc"]):
            return self._request_exit(
                active_path=active_path,
                active=active,
                position=position,
                reason="SCHEDULED_EXIT_TARGET_REACHED",
            )

        return {
            "status": "ACTIVE_POSITION_OK",
            "candidate_id": active.get("candidate_id"),
            "signal_identity": active.get("signal_identity"),
            "symbol": symbol,
            "position_id": pid,
            "exit_target_utc": active.get("exit_target_utc"),
        }

    def manage_all(self) -> dict[str, Any]:
        pending = self.reconcile_pending_entries()
        active_results = []
        for path in self._active_paths():
            try:
                active_results.append(self._manage_one_active(path))
            except Exception as exc:
                active_results.append({
                    "status": "ACTIVE_MANAGEMENT_FAIL_CLOSED",
                    "session_dir": str(path.parent),
                    "error": f"{type(exc).__name__}:{exc}",
                })

        recon = self._portfolio_reconcile()
        ledger = self.ledger.current()
        statuses = [str(x.get("status") or "") for x in pending + active_results]
        severe = any(
            "FAIL_CLOSED" in s or "RECONCILIATION_REQUIRED" in s
            for s in statuses
        ) or not recon["pass"]
        return self._status(
            "MULTISLOT_MANAGEMENT_FAIL_CLOSED" if severe else "MULTISLOT_MANAGEMENT_OK",
            pending_entry_results=pending,
            active_results=active_results,
            portfolio_reconciliation={
                "pass": recon["pass"],
                "blockers": recon["blockers"],
            },
            reservation_count=len(ledger.get("reservations") or []),
            free_slots=3-len(ledger.get("reservations") or []),
        )


__all__ = [
    "OperatorFuturesEngineV04",
    "MultiSlotEngineError",
    "timing_state",
    "protective_prices",
]
