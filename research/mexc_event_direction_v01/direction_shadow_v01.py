#!/usr/bin/env python3
"""Offline, read-only MEXC Event Futures shadow decision/expiry admission layer.

NO network, account, orders or signal generation. V0.13 retains statistical authority.
Local hashes/timestamps alone do not prove prospective custody.
"""
import argparse
import json
import math
from collections import defaultdict
from pathlib import Path

HORIZONS = {10, 30, 60}
SYMBOLS = {"BTC_USDT", "ETH_USDT"}
HASH_FIELDS = ("rule_hash", "model_hash", "signal_source_sha256",
               "payout_source_sha256", "decision_index_raw_sha256")

def require(ok, reason):
    if not ok:
        raise ValueError(reason)

def positive_number(value):
    try:
        n = float(value)
        require(math.isfinite(n) and n > 0, "expected finite positive number")
        return n
    except (ValueError, TypeError) as e:
        raise ValueError("expected finite positive number") from e

def timestamp(value):
    require(type(value) is int and value > 0, "invalid millisecond timestamp")
    return value

def sha(value):
    require(type(value) is str and len(value) == 64
            and all(c in "0123456789abcdef" for c in value), "invalid sha256")
    return value

def read_jsonl(path):
    rows = []
    for number, line in enumerate(Path(path).read_text(encoding="utf-8").splitlines(), 1):
        if line.strip():
            try:
                rows.append(json.loads(line))
            except json.JSONDecodeError as e:
                raise ValueError(f"line {number}: invalid JSON") from e
    return rows

def verified_decision(s, allowed_rule_hashes):
    required = (
        "signal_id", "signal_source_sha256", "rule_hash", "model_hash", "model_id",
        "symbol", "direction", "horizon_minutes", "signal_ts_ms",
        "signal_received_ms", "feature_cutoff_ms", "payout_received_ms",
        "index_received_ms", "decision_ts_ms", "decision_index",
        "payout_up", "payout_down", "payout_source_sha256",
        "decision_index_raw_sha256", "product_state", "forecast_prob_up"
    )
    require(all(k in s for k in required), "missing decision field")
    require(s["rule_hash"] in allowed_rule_hashes, "unregistered scientific rule hash")
    for name in HASH_FIELDS:
        sha(s[name])
    require(type(s["signal_id"]) is str and bool(s["signal_id"]), "bad signal_id")
    require(s["symbol"] in SYMBOLS and type(s["horizon_minutes"]) is int
            and s["horizon_minutes"] in HORIZONS, "unsupported cell")
    require(s["product_state"] == "ONLINE", "product is not ONLINE")
    require(s["direction"] in {"UP", "DOWN"}, "bad direction")
    p = float(s["forecast_prob_up"])
    require(math.isfinite(p) and 0 <= p <= 1, "bad forecast probability")
    for key in ("signal_ts_ms", "signal_received_ms", "feature_cutoff_ms",
                "payout_received_ms", "index_received_ms", "decision_ts_ms"):
        timestamp(s[key])
    require(
        s["feature_cutoff_ms"] <= s["signal_ts_ms"] <=
        s["signal_received_ms"] <= s["payout_received_ms"] <=
        s["decision_ts_ms"], "future feature/signal or noncausal order")
    require(s["index_received_ms"] >= s["payout_received_ms"]
            and s["index_received_ms"] - s["payout_received_ms"] <= 5000,
            "stale payout/index join")
    require(s["decision_ts_ms"] - s["signal_ts_ms"] <= 10000, "stale signal")
    up, down = positive_number(s["payout_up"]), positive_number(s["payout_down"])
    positive_number(s["decision_index"])
    ev_up = p * up - (1 - p)
    ev_down = (1 - p) * down - p
    best = "UP" if ev_up >= ev_down else "DOWN"
    require(s["direction"] == best and max(ev_up, ev_down) > 0,
            "no positive forecast EV / non-optimal side; abstain")
    q = up if s["direction"] == "UP" else down
    return {
        "family_id": "EVENT-FUTURES-DIRECTION-V01",
        "family_version": "0.1", "signal_id": s["signal_id"],
        "symbol": s["symbol"], "direction": s["direction"],
        "direction_policy": s["model_id"],
        "horizon_minutes": s["horizon_minutes"],
        "decision_ts_ms": s["decision_ts_ms"],
        "decision_index": float(s["decision_index"]),
        "payout": q, "break_even_probability": 1 / (1 + q),
        "expiry_target_ts_ms": s["decision_ts_ms"] + 60000 * s["horizon_minutes"],
        "payout_source_sha256": s["payout_source_sha256"],
        "decision_index_raw_sha256": s["decision_index_raw_sha256"],
        "rule_hash": s["rule_hash"], "model_hash": s["model_hash"],
        "forecast_prob_up": p, "source_integrity_ok": True,
    }

def admit(decisions, authority):
    require(authority.get("status") == "ACTIVE_PROSPECTIVE"
            and authority.get("operator_authority") is True,
            "activation/source gate not authorized")
    require(type(authority.get("activated_at_ms")) is int,
            "missing activation timestamp")
    rules = authority.get("allowed_rule_hashes")
    require(type(rules) is list and bool(rules), "no registered model rules")
    for rule in rules:
        sha(rule)
    output, ids = [], set()
    active_until = defaultdict(int)
    for raw in decisions:
        s = verified_decision(raw, set(rules))
        require(s["decision_ts_ms"] > authority["activated_at_ms"],
                "pre-activation decision")
        require(raw["model_hash"] ==
                authority.get("model_hash_by_id", {}).get(raw["model_id"]),
                "model hash is not preregistered")
        key = (s["symbol"], s["horizon_minutes"], s["direction_policy"])
        require(s["signal_id"] not in ids, "duplicated signal")
        ids.add(s["signal_id"])
        require(s["decision_ts_ms"] >= active_until[key],
                "overlapping unresolved signal in cell")
        active_until[key] = s["expiry_target_ts_ms"] + 5000
        output.append(s)
    return output

def settle(admitted, ticks):
    groups = defaultdict(list)
    for tick in ticks:
        require(tick.get("symbol") in SYMBOLS, "unsupported tick symbol")
        timestamp(tick.get("server_ts_ms"))
        timestamp(tick.get("received_ms"))
        sha(tick.get("raw_sha256"))
        price = positive_number(tick.get("index"))
        require(abs(tick["received_ms"] - tick["server_ts_ms"]) <= 5000,
                "tick receipt clock skew or lateness exceeds 5 seconds")
        groups[tick["symbol"]].append((tick["server_ts_ms"],
                                       tick["received_ms"], price,
                                       tick["raw_sha256"]))
    for symbol in groups:
        groups[symbol].sort()
    result, blocked = [], []
    for s in admitted:
        target = s["expiry_target_ts_ms"]
        tick = next((t for t in groups[s["symbol"]] if t[0] >= target), None)
        if tick is None or tick[0] - target > 5000:
            blocked.append({"signal_id": s["signal_id"],
                            "reason": "BLOCKED_MISSING_EXPIRY_INDEX"})
            continue
        actual_up = tick[2] > s["decision_index"]
        tie = tick[2] == s["decision_index"]
        win = (s["direction"] == "UP") == actual_up
        outcome = "TIE" if tie else "WIN" if win else "LOSS"
        result.append({
            **{k: v for k, v in s.items()
               if k not in ("model_hash", "forecast_prob_up")},
            "expiry_ts_ms": tick[0], "expiry_index": tick[2],
            "expiry_index_raw_sha256": tick[3],
            "outcome": outcome,
            "unit_return": 0 if tie else s["payout"] if win else -1,
            "status": "RESOLVED", "model_hash": s["model_hash"],
            "forecast_prob_up": s["forecast_prob_up"],
        })
    return result, blocked

def main():
    ap = argparse.ArgumentParser(description="Offline READ-ONLY shadow verifier")
    for name in ("authority", "decisions", "ticks", "output"):
        ap.add_argument("--" + name, required=True)
    args = ap.parse_args()
    authority = json.loads(Path(args.authority).read_text(encoding="utf-8"))
    admitted = admit(read_jsonl(args.decisions), authority)
    resolved, blocked = settle(admitted, read_jsonl(args.ticks))
    report = {"status": "READ_ONLY_SHADOW_ONLY", "admitted": len(admitted),
              "resolved": len(resolved), "blocked": blocked,
              "outcomes": resolved, "edge_claim": False,
              "warning": "Local hashes/timestamps do NOT prove independent pre-outcome custody or MEXC executed openPrice"}
    Path(args.output).write_text(json.dumps(report, indent=2, sort_keys=True) + "\n",
                                 encoding="utf-8")
    print(json.dumps({k: v for k, v in report.items() if k != "outcomes"}, indent=2))

if __name__ == "__main__":
    main()
