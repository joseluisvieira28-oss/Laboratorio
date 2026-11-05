"""Offline cash-flow research ledger. No exchange, network, credentials or orders.

Money is Decimal in ONE reporting currency. Product-specific adapters must supply
audited cash flows; this module does not price inverse contracts or infer fills.
Hash chains detect changes only against a separately retained head hash.
"""
import argparse
import datetime as dt
from decimal import Decimal as D
import hashlib
import json
from pathlib import Path
import random
import statistics

COSTS = {"fees", "funding", "delivery", "liquidation", "borrow", "transfer", "conversion", "other"}
ZERO = "0" * 64


def require(ok, reason):
    if not ok:
        raise ValueError(reason)


def number(x):
    require(isinstance(x, (str, int)) and not isinstance(x, bool), "DECIMAL_STRING_REQUIRED")
    v = D(x)
    require(v.is_finite(), "NONFINITE")
    return v


def instant(x):
    v = dt.datetime.fromisoformat(x.replace("Z", "+00:00"))
    require(v.tzinfo is not None, "TIMEZONE_REQUIRED")
    return v.astimezone(dt.timezone.utc)


def canonical(x):
    return json.dumps(x, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()


def digest(x):
    return hashlib.sha256(canonical(x)).hexdigest()


def sha(x):
    require(isinstance(x, str) and len(x) == 64 and all(c in "0123456789abcdef" for c in x), "BAD_SHA256")


def replay(rows, expected_head=None):
    """Validate every event; never silently drop malformed or incomplete trades."""
    head = ZERO
    trades = {}
    event_ids = set()
    currency = None
    last_at = None
    for row in rows:
        require(set(row) == {"previous", "event", "hash"}, "ROW_SCHEMA")
        require(row["previous"] == head, "CHAIN_BROKEN")
        require(row["hash"] == digest({"previous": head, "event": row["event"]}), "EVENT_HASH")
        e = row["event"]
        require(e["id"] not in event_ids, "DUPLICATE_EVENT")
        event_ids.add(e["id"])
        at = instant(e["at"])
        require(last_at is None or at >= last_at, "LEDGER_TIME_REVERSED")
        last_at = at
        require(e.get("simulation") is True, "RESEARCH_ONLY")
        sha(e["evidence_sha256"])
        tid, kind = e["trade_id"], e["kind"]
        if kind == "precommit":
            require(tid not in trades, "DUPLICATE_SIGNAL")
            require(e["phase"] in {"development", "confirmation", "oos"}, "BAD_PHASE")
            require(e["decision"] in {"enter", "abstain"}, "BAD_DECISION")
            require(e["strategy"] and e["cohort"] and e["rules_sha256"], "MISSING_PRECOMMIT")
            sha(e["rules_sha256"])
            require(instant(e["information_cutoff"]) <= at < instant(e["entry_deadline"]), "PRECOMMIT_CHRONOLOGY")
            require(number(e["risk"]) > 0, "RISK_REQUIRED")
            require(isinstance(e["currency"], str) and bool(e["currency"]), "CURRENCY_REQUIRED")
            currency = currency or e["currency"]
            require(currency == e["currency"], "MIXED_CURRENCY")
            trades[tid] = dict(signal=e, commitment=row["hash"], events=[], closed=False)
        else:
            require(tid in trades, "NO_PRECOMMIT")
            t = trades[tid]
            require(e["commitment"] == t["commitment"], "PRECOMMIT_BINDING")
            require(at > instant(t["signal"]["at"]) and not t["closed"], "EVENT_CHRONOLOGY_OR_CLOSED")
            require(t["signal"]["decision"] == "enter", "ABSTENTION_HAS_EXECUTION")
            require(e["currency"] == currency, "MIXED_CURRENCY")
            if kind in {"entry", "exit"}:
                require(e["instrument"] and e["leg"] and e["side"] in {"buy", "sell", "settlement"}, "FILL_IDENTITY")
                require(number(e["quantity"]) > 0 and number(e["price"]) >= 0, "BAD_FILL")
                number(e["cash"])
                # Cash excludes separately recorded fees. Spread/slippage already in cash.
                for key in ("spread_embedded", "slippage_embedded"):
                    number(e[key])
                entries = [x for x in t["events"] if x["kind"] == "entry"]
                require(kind != "entry" or at <= instant(t["signal"]["entry_deadline"]), "LATE_ENTRY")
                require(kind != "entry" or not any(x["kind"] == "exit" for x in t["events"]), "ENTRY_AFTER_EXIT")
                require(kind != "exit" or any(x["leg"] == e["leg"] and x["instrument"] == e["instrument"] for x in entries), "EXIT_WITHOUT_LEG")
            elif kind == "cost":
                require(any(x["kind"] == "entry" for x in t["events"]), "COST_WITHOUT_ENTRY")
                require(e["category"] in COSTS, "COST_CATEGORY")
                number(e["cash"])  # signed: costs negative, rebates/funding credits positive
            elif kind == "close":
                require(set(e["coverage"]) == COSTS, "COST_COVERAGE_MISSING")
                require(all(v in {"recorded", "not_applicable"} for v in e["coverage"].values()), "UNKNOWN_COST")
                require(e["reconciliation_evidence"], "CLOSE_RECONCILIATION_REQUIRED")
                entries = {x["leg"] for x in t["events"] if x["kind"] == "entry"}
                exits = {x["leg"] for x in t["events"] if x["kind"] == "exit"}
                require(entries and entries == exits, "UNRESOLVED_LEGS")
                require(set(e["reconciled_legs"]) == entries, "LEG_RECONCILIATION")
                for cat, status in e["coverage"].items():
                    seen = any(x["kind"] == "cost" and x["category"] == cat for x in t["events"])
                    require(seen == (status == "recorded"), "COST_COVERAGE_CONFLICT")
                t["closed"] = True
            else:
                raise ValueError("UNKNOWN_EVENT_KIND")
            t["events"].append(e)
        head = row["hash"]
    if expected_head is not None:
        require(head == expected_head, "ANCHOR_MISMATCH")
    return trades, head, currency


def append(path, event):
    """Single-writer append with exclusive sidecar lock; validates before mutation."""
    path = Path(path)
    lock = Path(str(path) + ".lock")
    with lock.open("x"):
        pass
    try:
        rows = read(path) if path.exists() else []
        _, head, _ = replay(rows)
        row = {"previous": head, "event": event}
        row["hash"] = digest(row)
        replay(rows + [row])
        with path.open("ab") as stream:
            stream.write(canonical(row) + b"\n")
            stream.flush()
            import os
            os.fsync(stream.fileno())
        return row["hash"]
    finally:
        # A crash can leave the lock; recovery must inspect ledger before removing it.
        lock.unlink()


def read(path):
    raw = Path(path).read_bytes()
    require(not raw or raw.endswith(b"\n"), "TRUNCATED_LEDGER")
    return [json.loads(line) for line in raw.splitlines()]


def interval(values, block=7, replicates=10000, seed=20261105):
    """Exploratory circular moving-block interval over consecutive COHORTS.

    Callers must retain zero eligible abstentions, provide full chronological
    cohorts and pre-register the sampling design. No automatic trading gate.
    """
    require(block >= 1 and replicates >= 100, "BOOTSTRAP_CONFIG")
    if len(values) < max(30, 4 * block):
        return {"status": "INSUFFICIENT_COHORTS", "lower95_one_sided": None, "upper95_one_sided": None}
    rng = random.Random(seed)
    means = []
    n = len(values)
    for _ in range(replicates):
        sample = []
        while len(sample) < n:
            start = rng.randrange(n)
            sample.extend(values[(start + j) % n] for j in range(block))
        means.append(statistics.mean(sample[:n]))
    means.sort()
    return dict(status="EXPLORATORY_NOT_PROMOTION", lower95_one_sided=means[int(.05*replicates)],
                upper95_one_sided=means[min(replicates-1, int(.95*replicates))],
                block=block, replicates=replicates, seed=seed)


def report(rows, expected_head=None):
    trades, head, currency = replay(rows, expected_head)
    outcomes = []
    incomplete = []
    for tid, t in trades.items():
        s = t["signal"]
        if s["decision"] == "abstain":
            outcomes.append(dict(trade_id=tid, strategy=s["strategy"], phase=s["phase"], cohort=s["cohort"],
                                 at=s["at"], exit_at=s["at"], net="0", r="0", abstention=True))
        elif not t["closed"]:
            incomplete.append(tid)
        else:
            cash = sum((number(x["cash"]) for x in t["events"] if "cash" in x), D(0))
            gross = sum((number(x["cash"]) for x in t["events"] if x["kind"] in {"entry", "exit"}), D(0))
            costs = {c: str(sum((number(x["cash"]) for x in t["events"] if x["kind"] == "cost" and x["category"] == c), D(0))) for c in sorted(COSTS)}
            outcomes.append(dict(trade_id=tid, strategy=s["strategy"], phase=s["phase"], cohort=s["cohort"],
                                 at=s["at"], exit_at=t["events"][-1]["at"], net=str(cash), gross_at_fills=str(gross),
                                 costs=costs, r=str(cash/number(s["risk"])), abstention=False,
                                 spread_embedded=str(sum((number(x["spread_embedded"]) for x in t["events"] if x["kind"] in {"entry", "exit"}), D(0))),
                                 slippage_embedded=str(sum((number(x["slippage_embedded"]) for x in t["events"] if x["kind"] in {"entry", "exit"}), D(0)))))
    # Never pool development, confirmation, OOS, different rules or strategies.
    groups = {}
    for o in outcomes:
        s = trades[o["trade_id"]]["signal"]
        key = (s["strategy"], s["rules_sha256"], s["phase"])
        groups.setdefault(key, []).append(o)
    summaries = []
    for key, items in sorted(groups.items()):
        ordered = sorted(items, key=lambda x: (instant(x["exit_at"]), x["trade_id"]))
        equity = peak = dd = D(0)
        for o in ordered:
            equity += number(o["net"])
            peak = max(peak, equity)
            dd = max(dd, peak-equity)
        cohorts = {}
        for o in sorted(items, key=lambda x: instant(x["at"])):
            cohorts.setdefault(o["cohort"], []).append(float(number(o["r"])))
        vals = [sum(v) for v in cohorts.values()]
        executed = [number(x["net"]) for x in items if not x["abstention"]]
        gains = sum((max(x, D(0)) for x in executed), D(0))
        losses = sum((max(-x, D(0)) for x in executed), D(0))
        blocked = any((t["signal"]["strategy"], t["signal"]["rules_sha256"], t["signal"]["phase"]) == key for tid, t in trades.items() if tid in incomplete)
        summaries.append(dict(strategy=key[0], rules_sha256=key[1], phase=key[2], observations=len(items),
                              trades=sum(not x["abstention"] for x in items), cohorts=len(vals),
                              net=str(equity), realized_cash_drawdown=str(dd),
                              mean_net_per_trade=str(sum(executed)/D(len(executed))) if executed else None,
                              win_rate=str(D(sum(x > 0 for x in executed))/D(len(executed))) if executed else None,
                              profit_factor=str(gains/losses) if losses else None,
                              worst_observed_r=str(min(number(x["r"]) for x in items)),
                              mean_r_per_cohort=statistics.mean(vals),
                              uncertainty={"status": "INCOMPLETE_LEDGER"} if blocked else interval(vals)))
    return dict(version=1, simulation=True, currency=currency, head=head, anchor_checked=expected_head is not None,
                status="INCOMPLETE" if incomplete else "RESEARCH_ONLY", incomplete=incomplete,
                outcomes=outcomes, summaries=summaries, live_go=False,
                limitations=["Local times and hash chains do not prove external precommit; publish and retain head before entry.",
                             "Cash and reconciliation are adapter assertions requiring raw evidence review.",
                             "Drawdown is realized cash only; open risk and intratrade tail risk are not estimated.",
                             "Cohort completeness/dependence and cost assumptions need a frozen study-specific audit."])


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("ledger")
    p.add_argument("--append-event", help="JSON event file; never an exchange order")
    p.add_argument("--expected-head")
    a = p.parse_args()
    if a.append_event:
        print(append(a.ledger, json.loads(Path(a.append_event).read_text())))
    else:
        print(json.dumps(report(read(a.ledger), a.expected_head), indent=2, allow_nan=False))
