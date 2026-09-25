#!/usr/bin/env python3
from __future__ import annotations

import argparse
import bisect
import csv
import datetime as dt
import json
import math
import random
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Any

LAB_ID = "SCL-LIQPULL-TOXICITY-FWD-001"
VERSION = "0.2"
ORDER_SIZE_BTC = 0.001
LOOKBACK_MS = 1000
FILL_WINDOW_MS = 2000
MARKOUT_MS = (1000, 5000, 15000)
TOP_LEVELS = 5
MIN_DAYS = 14
MIN_FILLS_GLOBAL = 5000
MIN_FILLS_SIDE = 1500
BOOTSTRAP_REPS = 10_000
BOOTSTRAP_SEED = 20260925
EPS = 1e-12


class FailClosed(RuntimeError):
    pass


@dataclass(frozen=True)
class Book:
    t: int
    recv_ns: int
    bid_px: float
    bid_sz: float
    ask_px: float
    ask_sz: float
    bid_depth5_ntl: float
    ask_depth5_ntl: float

    @property
    def mid(self) -> float:
        return (self.bid_px + self.ask_px) / 2.0


@dataclass(frozen=True)
class Trade:
    t: int
    recv_ns: int
    side: str
    px: float
    sz: float

    @property
    def ntl(self) -> float:
        return self.px * self.sz


def _f(x: Any) -> float:
    v = float(x)
    if not math.isfinite(v) or v <= 0:
        raise FailClosed(f"non-positive/non-finite numeric field: {x!r}")
    return v


def normalize_trade_side(side: Any) -> str:
    s = str(side).strip().upper()
    if s in {"B", "BUY"}:
        return "BUY"
    if s in {"A", "S", "SELL"}:
        return "SELL"
    raise FailClosed(f"unknown trade side: {side!r}")


def parse_book(payload: dict, recv_ns: int) -> Book:
    data = payload.get("data")
    if not isinstance(data, dict) or data.get("coin") != "BTC":
        raise FailClosed("invalid BTC l2Book payload")
    levels = data.get("levels")
    if not isinstance(levels, list) or len(levels) != 2:
        raise FailClosed("invalid l2 levels")
    bids, asks = levels
    if not bids or not asks:
        raise FailClosed("empty top of book")

    def lv(x):
        return _f(x["px"]), _f(x["sz"])

    bp, bs = lv(bids[0])
    ap, ass = lv(asks[0])
    if not bp < ap:
        raise FailClosed("crossed/locked book")
    bd = sum(px * sz for px, sz in (lv(x) for x in bids[:TOP_LEVELS]))
    ad = sum(px * sz for px, sz in (lv(x) for x in asks[:TOP_LEVELS]))
    return Book(int(data["time"]), int(recv_ns), bp, bs, ap, ass, bd, ad)


def parse_trades(payload: dict, recv_ns: int) -> list[Trade]:
    data = payload.get("data")
    if not isinstance(data, list):
        raise FailClosed("invalid trades payload")
    out = []
    for x in data:
        if x.get("coin") != "BTC":
            continue
        out.append(
            Trade(
                int(x["time"]),
                int(recv_ns),
                normalize_trade_side(x["side"]),
                _f(x["px"]),
                _f(x["sz"]),
            )
        )
    return out


def load_rows(paths: Iterable[Path]) -> tuple[list[Book], list[Trade], set[str]]:
    books: list[Book] = []
    trades: list[Trade] = []
    protocol_commits: set[str] = set()
    seen = set()
    for path in sorted(paths):
        with path.open("r", encoding="utf-8") as f:
            for lineno, line in enumerate(f, 1):
                if not line.strip():
                    continue
                row = json.loads(line)
                if row.get("lab_id") != LAB_ID:
                    raise FailClosed(f"wrong lab id in {path}:{lineno}")
                pc = str(row.get("protocol_commit") or "")
                if len(pc) < 7:
                    raise FailClosed(f"missing protocol commit in {path}:{lineno}")
                protocol_commits.add(pc)
                payload = row.get("provider_payload")
                if not isinstance(payload, dict):
                    continue
                recv_ns = int(row.get("recv_monotonic_ns", 0))
                ch = payload.get("channel")
                if ch == "l2Book":
                    books.append(parse_book(payload, recv_ns))
                elif ch == "trades":
                    for tr in parse_trades(payload, recv_ns):
                        key = (tr.t, tr.side, tr.px, tr.sz)
                        if key not in seen:
                            seen.add(key)
                            trades.append(tr)
    if not books:
        raise FailClosed("no valid l2Book rows")
    books.sort(key=lambda x: (x.t, x.recv_ns))
    trades.sort(key=lambda x: (x.t, x.recv_ns))
    return books, trades, protocol_commits


def first_book_at_or_after(books: list[Book], times: list[int], target: int):
    i = bisect.bisect_left(times, target)
    return None if i >= len(books) else (i, books[i])


def aggressive_window(
    trades: list[Trade], times: list[int], lo: int, hi: int
) -> tuple[float, float]:
    a = bisect.bisect_right(times, lo)
    b = bisect.bisect_right(times, hi)
    buy = 0.0
    sell = 0.0
    for t in trades[a:b]:
        if t.side == "BUY":
            buy += t.ntl
        else:
            sell += t.ntl
    return buy, sell


def build_proved_fills(books: list[Book], trades: list[Trade]) -> list[dict]:
    by_second = {}
    for i, b in enumerate(books):
        by_second.setdefault(b.t // 1000, i)

    bt = [b.t for b in books]
    tt = [t.t for t in trades]
    out = []

    for sec in sorted(by_second):
        i = by_second[sec]
        b = books[i]
        pp = first_book_at_or_after(books, bt, b.t - LOOKBACK_MS)
        if pp is None:
            continue
        _, prev = pp
        if prev.t >= b.t or prev.t < b.t - 1500:
            continue

        buy_ntl, sell_ntl = aggressive_window(
            trades, tt, b.t - LOOKBACK_MS, b.t
        )
        pull_buy = max(
            0.0, prev.bid_depth5_ntl - b.bid_depth5_ntl - sell_ntl
        ) / max(prev.bid_depth5_ntl, EPS)
        pull_sell = max(
            0.0, prev.ask_depth5_ntl - b.ask_depth5_ntl - buy_ntl
        ) / max(prev.ask_depth5_ntl, EPS)

        for side, px, touch, pull, opp in (
            ("BUY", b.bid_px, b.bid_sz, pull_buy, "SELL"),
            ("SELL", b.ask_px, b.ask_sz, pull_sell, "BUY"),
        ):
            deadline = b.t + FILL_WINDOW_MS
            invalid = None
            bend = bisect.bisect_right(bt, deadline)
            for nb in books[i + 1 : bend]:
                if (side == "BUY" and nb.bid_px != px) or (
                    side == "SELL" and nb.ask_px != px
                ):
                    invalid = nb.t
                    break
            end = min(deadline, invalid) if invalid is not None else deadline

            lo = bisect.bisect_right(tt, b.t)
            hi = bisect.bisect_right(tt, end)
            cum = 0.0
            fill_t = None
            for tr in trades[lo:hi]:
                if tr.side == opp and abs(tr.px - px) <= max(abs(px), 1.0) * 1e-12:
                    cum += tr.sz
                    if cum + 1e-15 >= touch + ORDER_SIZE_BTC:
                        fill_t = tr.t
                        break

            if fill_t is not None:
                out.append(
                    {
                        "entry_time_ms": b.t,
                        "fill_time_ms": fill_t,
                        "utc_day": dt.datetime.fromtimestamp(
                            fill_t / 1000, tz=dt.timezone.utc
                        ).date().isoformat(),
                        "side": side,
                        "join_px": px,
                        "entry_touch_size_btc": touch,
                        "pull_score": pull,
                    }
                )
    return out


def sample_receipt(fills: list[dict]) -> dict:
    days = {x["utc_day"] for x in fills}
    buys = sum(x["side"] == "BUY" for x in fills)
    sells = len(fills) - buys
    gates = {
        "days": len(days) >= MIN_DAYS,
        "fills_global": len(fills) >= MIN_FILLS_GLOBAL,
        "buy_fills": buys >= MIN_FILLS_SIDE,
        "sell_fills": sells >= MIN_FILLS_SIDE,
    }
    return {
        "days": len(days),
        "fills": len(fills),
        "buy_fills": buys,
        "sell_fills": sells,
        "gates": gates,
        "sample_gate_pass": all(gates.values()),
    }


def attach_markouts(fills: list[dict], books: list[Book]) -> list[dict]:
    bt = [b.t for b in books]
    rows = []
    for f in fills:
        row = dict(f)
        direction = 1.0 if f["side"] == "BUY" else -1.0
        complete = True
        for h in MARKOUT_MS:
            pair = first_book_at_or_after(books, bt, f["fill_time_ms"] + h)
            if pair is None:
                complete = False
                break
            _, fb = pair
            if fb.t > f["fill_time_ms"] + h + 1100:
                complete = False
                break
            row[f"markout_{h}ms_bps"] = (
                direction * (fb.mid / f["join_px"] - 1.0) * 10_000.0
            )
            row[f"markout_book_time_{h}ms"] = fb.t
        if complete:
            rows.append(row)
    return rows


def slope(xs, ys):
    if len(xs) != len(ys) or len(xs) < 2:
        return float("nan")
    mx = sum(xs) / len(xs)
    my = sum(ys) / len(ys)
    den = sum((x - mx) ** 2 for x in xs)
    if den <= 0:
        return float("nan")
    return sum((x - mx) * (y - my) for x, y in zip(xs, ys)) / den


def percentile(v, p):
    z = sorted(x for x in v if math.isfinite(x))
    if not z:
        return float("nan")
    k = (len(z) - 1) * p
    lo = int(math.floor(k))
    hi = int(math.ceil(k))
    if lo == hi:
        return z[lo]
    return z[lo] * (hi - k) + z[hi] * (k - lo)


def clustered_bootstrap_ci(rows):
    by = defaultdict(list)
    for r in rows:
        by[r["utc_day"]].append(r)
    days = sorted(by)
    rng = random.Random(BOOTSTRAP_SEED)
    vals = []
    for _ in range(BOOTSTRAP_REPS):
        sample = []
        for _slot in days:
            sample.extend(by[rng.choice(days)])
        s = slope(
            [r["pull_score"] for r in sample],
            [r["markout_5000ms_bps"] for r in sample],
        )
        if math.isfinite(s):
            vals.append(s)
    return percentile(vals, 0.025), percentile(vals, 0.975)


def quartile_delta(rows):
    ordered = sorted(rows, key=lambda r: r["pull_score"])
    q = max(1, len(ordered) // 4)
    low = ordered[:q]
    high = ordered[-q:]
    return (
        sum(r["markout_5000ms_bps"] for r in high) / len(high)
        - sum(r["markout_5000ms_bps"] for r in low) / len(low)
    )


def adjudicate(rows: list[dict], sample: dict) -> dict:
    buys = [r for r in rows if r["side"] == "BUY"]
    sells = [r for r in rows if r["side"] == "SELL"]
    gs = slope(
        [r["pull_score"] for r in rows],
        [r["markout_5000ms_bps"] for r in rows],
    )
    bs = slope(
        [r["pull_score"] for r in buys],
        [r["markout_5000ms_bps"] for r in buys],
    )
    ss = slope(
        [r["pull_score"] for r in sells],
        [r["markout_5000ms_bps"] for r in sells],
    )
    lo, hi = clustered_bootstrap_ci(rows)
    qd = quartile_delta(rows)
    gates = {
        "global_slope_negative": gs < 0,
        "bootstrap_ci_upper_negative": math.isfinite(hi) and hi < 0,
        "buy_slope_negative": bs < 0,
        "sell_slope_negative": ss < 0,
        "top_minus_bottom_quartile_markout_negative": math.isfinite(qd) and qd < 0,
    }
    return {
        "lab_id": LAB_ID,
        "version": VERSION,
        "sample": sample,
        "outcome_accessed": True,
        "economics_computed": False,
        "fees_computed": False,
        "pnl_computed": False,
        "tier_claim": False,
        "global_slope_bps_per_pull_unit": gs,
        "buy_slope_bps_per_pull_unit": bs,
        "sell_slope_bps_per_pull_unit": ss,
        "bootstrap_reps": BOOTSTRAP_REPS,
        "bootstrap_seed": BOOTSTRAP_SEED,
        "bootstrap_ci95": [lo, hi],
        "top_minus_bottom_quartile_markout_5s_bps": qd,
        "gates": gates,
        "classification": (
            "MECHANISM_FORWARD_PASS"
            if all(gates.values())
            else "DISCOVERY_FAIL_NO_PROMOTION"
        ),
    }


def write_json(out: Path, name: str, obj: dict):
    out.mkdir(parents=True, exist_ok=True)
    (out / name).write_text(
        json.dumps(obj, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )


def write_full(rows: list[dict], out: Path):
    fields = [
        "entry_time_ms",
        "fill_time_ms",
        "utc_day",
        "side",
        "join_px",
        "entry_touch_size_btc",
        "pull_score",
        "markout_1000ms_bps",
        "markout_5000ms_bps",
        "markout_15000ms_bps",
        "markout_book_time_1000ms",
        "markout_book_time_5000ms",
        "markout_book_time_15000ms",
    ]
    with (
        out / "SCL_LIQPULL_TOXICITY_FWD_001_PROVED_FILLS_WITH_MARKOUTS_V0_2.csv"
    ).open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        w.writerows(rows)


def main() -> int:
    p = argparse.ArgumentParser(
        description="Forward fill-toxicity evaluator with sample-gated outcome firewall."
    )
    p.add_argument("--raw-dir", type=Path, required=True)
    p.add_argument("--out-dir", type=Path, required=True)
    a = p.parse_args()

    paths = sorted(a.raw_dir.glob(f"{LAB_ID}_*.jsonl"))
    if not paths:
        raise SystemExit("Fail closed: no canonical raw shards found")
    books, trades, commits = load_rows(paths)
    if len(commits) != 1:
        raise SystemExit(f"Fail closed: mixed protocol commits: {sorted(commits)}")

    fills = build_proved_fills(books, trades)
    sample = sample_receipt(fills)
    base = {
        "lab_id": LAB_ID,
        "version": VERSION,
        "protocol_commit": next(iter(commits)),
        "raw_shards": len(paths),
        "sample": sample,
        "economics_computed": False,
        "fees_computed": False,
        "pnl_computed": False,
        "tier_claim": False,
    }

    if not sample["sample_gate_pass"]:
        result = {
            **base,
            "outcome_accessed": False,
            "markouts_computed": False,
            "classification": "INSUFFICIENT_FORWARD_SAMPLE",
        }
        write_json(
            a.out_dir,
            "SCL_LIQPULL_TOXICITY_FWD_001_SAMPLE_RECEIPT_V0_2.json",
            result,
        )
        print(json.dumps(result, indent=2, sort_keys=True))
        return 0

    rows = attach_markouts(fills, books)
    result = adjudicate(rows, sample)
    result.update(
        {
            "protocol_commit": next(iter(commits)),
            "raw_shards": len(paths),
            "complete_markout_rows": len(rows),
            "markouts_computed": True,
        }
    )
    write_json(
        a.out_dir,
        "SCL_LIQPULL_TOXICITY_FWD_001_RESULT_V0_2.json",
        result,
    )
    write_full(rows, a.out_dir)
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
