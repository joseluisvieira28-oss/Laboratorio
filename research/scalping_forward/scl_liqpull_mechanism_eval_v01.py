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
VERSION = "0.1"
ORDER_SIZE_BTC = 0.001
LOOKBACK_MS = 1000
FILL_WINDOW_MS = 2000
MARKOUT_MS = (1000, 5000, 15000)
PRIMARY_MARKOUT_MS = 5000
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
    seen_trade_keys: set[tuple] = set()
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
                ch = payload.get("channel")
                recv_ns = int(row.get("recv_monotonic_ns", 0))
                if ch == "l2Book":
                    books.append(parse_book(payload, recv_ns))
                elif ch == "trades":
                    for tr in parse_trades(payload, recv_ns):
                        key = (tr.t, tr.side, tr.px, tr.sz, json.dumps(payload, sort_keys=True))
                        if key not in seen_trade_keys:
                            seen_trade_keys.add(key)
                            trades.append(tr)
    if not books:
        raise FailClosed("no valid l2Book rows")
    books.sort(key=lambda x: (x.t, x.recv_ns))
    trades.sort(key=lambda x: (x.t, x.recv_ns))
    return books, trades, protocol_commits


def first_book_at_or_after(
    books: list[Book], book_times: list[int], target_ms: int
) -> tuple[int, Book] | None:
    i = bisect.bisect_left(book_times, target_ms)
    if i >= len(books):
        return None
    return i, books[i]


def aggressive_notional_window(
    trades: list[Trade], trade_times: list[int], lo_exclusive: int, hi_inclusive: int
) -> tuple[float, float]:
    lo = bisect.bisect_right(trade_times, lo_exclusive)
    hi = bisect.bisect_right(trade_times, hi_inclusive)
    buy = 0.0
    sell = 0.0
    for t in trades[lo:hi]:
        if t.side == "BUY":
            buy += t.ntl
        else:
            sell += t.ntl
    return buy, sell


def build_observations(books: list[Book], trades: list[Trade]) -> list[dict]:
    by_second: dict[int, int] = {}
    for i, b in enumerate(books):
        sec = b.t // 1000
        by_second.setdefault(sec, i)

    obs: list[dict] = []
    seconds = sorted(by_second)
    book_times = [b.t for b in books]
    trade_times = [t.t for t in trades]

    for sec in seconds:
        i = by_second[sec]
        b = books[i]
        target_prev = b.t - LOOKBACK_MS
        prev_pair = first_book_at_or_after(books, book_times, target_prev)
        if prev_pair is None:
            continue
        _, prev = prev_pair
        if prev.t >= b.t:
            continue
        if prev.t < b.t - 1500:
            continue

        buy_ntl, sell_ntl = aggressive_notional_window(
            trades, trade_times, b.t - LOOKBACK_MS, b.t
        )
        pull_buy = max(
            0.0, prev.bid_depth5_ntl - b.bid_depth5_ntl - sell_ntl
        ) / max(prev.bid_depth5_ntl, EPS)
        pull_sell = max(
            0.0, prev.ask_depth5_ntl - b.ask_depth5_ntl - buy_ntl
        ) / max(prev.ask_depth5_ntl, EPS)

        for passive_side, join_px, touch_sz, pull, opp_aggr in (
            ("BUY", b.bid_px, b.bid_sz, pull_buy, "SELL"),
            ("SELL", b.ask_px, b.ask_sz, pull_sell, "BUY"),
        ):
            deadline = b.t + FILL_WINDOW_MS
            cum = 0.0
            fill_t: int | None = None
            invalid_t: int | None = None

            b_end = bisect.bisect_right(book_times, deadline)
            for nb in books[i + 1 : b_end]:
                if passive_side == "BUY" and nb.bid_px != join_px:
                    invalid_t = nb.t
                    break
                if passive_side == "SELL" and nb.ask_px != join_px:
                    invalid_t = nb.t
                    break
            end_t = min(deadline, invalid_t) if invalid_t is not None else deadline

            t_lo = bisect.bisect_right(trade_times, b.t)
            t_hi = bisect.bisect_right(trade_times, end_t)
            for tr in trades[t_lo:t_hi]:
                if (
                    tr.side == opp_aggr
                    and abs(tr.px - join_px)
                    <= max(abs(join_px), 1.0) * 1e-12
                ):
                    cum += tr.sz
                    if cum + 1e-15 >= touch_sz + ORDER_SIZE_BTC:
                        fill_t = tr.t
                        break
            if fill_t is None:
                continue

            row = {
                "entry_time_ms": b.t,
                "fill_time_ms": fill_t,
                "utc_day": dt.datetime.fromtimestamp(
                    fill_t / 1000, tz=dt.timezone.utc
                ).date().isoformat(),
                "side": passive_side,
                "join_px": join_px,
                "entry_touch_size_btc": touch_sz,
                "pull_score": pull,
            }
            direction = 1.0 if passive_side == "BUY" else -1.0
            complete = True
            for h in MARKOUT_MS:
                pair = first_book_at_or_after(books, book_times, fill_t + h)
                if pair is None:
                    complete = False
                    break
                _, future_book = pair
                if future_book.t > fill_t + h + 1100:
                    complete = False
                    break
                row[f"markout_{h}ms_bps"] = (
                    direction * (future_book.mid / join_px - 1.0) * 10_000.0
                )
                row[f"markout_book_time_{h}ms"] = future_book.t
            if complete:
                obs.append(row)
    return obs


def slope(xs: list[float], ys: list[float]) -> float:
    if len(xs) != len(ys) or len(xs) < 2:
        return float("nan")
    mx = sum(xs) / len(xs)
    my = sum(ys) / len(ys)
    den = sum((x - mx) ** 2 for x in xs)
    if den <= 0:
        return float("nan")
    return sum((x - mx) * (y - my) for x, y in zip(xs, ys)) / den


def percentile(v: list[float], p: float) -> float:
    z = sorted(x for x in v if math.isfinite(x))
    if not z:
        return float("nan")
    k = (len(z) - 1) * p
    lo = int(math.floor(k))
    hi = int(math.ceil(k))
    if lo == hi:
        return z[lo]
    return z[lo] * (hi - k) + z[hi] * (k - lo)


def clustered_bootstrap_ci(
    rows: list[dict], reps: int = BOOTSTRAP_REPS, seed: int = BOOTSTRAP_SEED
) -> tuple[float, float]:
    by_day: dict[str, list[dict]] = defaultdict(list)
    for r in rows:
        by_day[r["utc_day"]].append(r)
    days = sorted(by_day)
    rng = random.Random(seed)
    vals = []
    for _ in range(reps):
        sample = []
        for _day_slot in days:
            d = rng.choice(days)
            sample.extend(by_day[d])
        s = slope(
            [r["pull_score"] for r in sample],
            [r["markout_5000ms_bps"] for r in sample],
        )
        if math.isfinite(s):
            vals.append(s)
    return percentile(vals, 0.025), percentile(vals, 0.975)


def quartile_delta(rows: list[dict]) -> float:
    ordered = sorted(rows, key=lambda r: r["pull_score"])
    n = len(ordered)
    if n < 4:
        return float("nan")
    q = max(1, n // 4)
    bottom = ordered[:q]
    top = ordered[-q:]
    return (
        sum(r["markout_5000ms_bps"] for r in top) / len(top)
        - sum(r["markout_5000ms_bps"] for r in bottom) / len(bottom)
    )


def adjudicate(rows: list[dict]) -> dict:
    days = sorted({r["utc_day"] for r in rows})
    buys = [r for r in rows if r["side"] == "BUY"]
    sells = [r for r in rows if r["side"] == "SELL"]
    result = {
        "lab_id": LAB_ID,
        "version": VERSION,
        "sample": {
            "fills": len(rows),
            "days": len(days),
            "buy_fills": len(buys),
            "sell_fills": len(sells),
        },
        "bootstrap_reps": BOOTSTRAP_REPS,
        "bootstrap_seed": BOOTSTRAP_SEED,
        "economics_computed": False,
        "fees_computed": False,
        "pnl_computed": False,
        "tier_claim": False,
    }
    if (
        len(days) < MIN_DAYS
        or len(rows) < MIN_FILLS_GLOBAL
        or len(buys) < MIN_FILLS_SIDE
        or len(sells) < MIN_FILLS_SIDE
    ):
        result["classification"] = "INSUFFICIENT_FORWARD_SAMPLE"
        return result

    global_slope = slope(
        [r["pull_score"] for r in rows],
        [r["markout_5000ms_bps"] for r in rows],
    )
    buy_slope = slope(
        [r["pull_score"] for r in buys],
        [r["markout_5000ms_bps"] for r in buys],
    )
    sell_slope = slope(
        [r["pull_score"] for r in sells],
        [r["markout_5000ms_bps"] for r in sells],
    )
    ci_lo, ci_hi = clustered_bootstrap_ci(rows)
    qd = quartile_delta(rows)
    gates = {
        "global_slope_negative": global_slope < 0,
        "bootstrap_ci_upper_negative": math.isfinite(ci_hi) and ci_hi < 0,
        "buy_slope_negative": buy_slope < 0,
        "sell_slope_negative": sell_slope < 0,
        "top_minus_bottom_quartile_markout_negative": math.isfinite(qd) and qd < 0,
    }
    result.update(
        {
            "global_slope_bps_per_pull_unit": global_slope,
            "buy_slope_bps_per_pull_unit": buy_slope,
            "sell_slope_bps_per_pull_unit": sell_slope,
            "bootstrap_ci95": [ci_lo, ci_hi],
            "top_minus_bottom_quartile_markout_5s_bps": qd,
            "gates": gates,
            "classification": (
                "MECHANISM_FORWARD_PASS"
                if all(gates.values())
                else "DISCOVERY_FAIL_NO_PROMOTION"
            ),
        }
    )
    return result


def write_outputs(rows: list[dict], result: dict, out_dir: Path) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    csvp = out_dir / "SCL_LIQPULL_TOXICITY_FWD_001_PROVED_FILLS_V0_1.csv"
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
    with csvp.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        w.writerows(rows)
    (
        out_dir / "SCL_LIQPULL_TOXICITY_FWD_001_RESULT_V0_1.json"
    ).write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def main() -> int:
    p = argparse.ArgumentParser(
        description="Frozen forward fill-toxicity mechanism evaluator; no trading economics."
    )
    p.add_argument("--raw-dir", type=Path, required=True)
    p.add_argument("--out-dir", type=Path, required=True)
    args = p.parse_args()
    paths = sorted(args.raw_dir.glob(f"{LAB_ID}_*.jsonl"))
    if not paths:
        raise SystemExit("Fail closed: no canonical raw shards found")
    books, trades, commits = load_rows(paths)
    if len(commits) != 1:
        raise SystemExit(f"Fail closed: mixed protocol commits: {sorted(commits)}")
    rows = build_observations(books, trades)
    result = adjudicate(rows)
    result["protocol_commit"] = next(iter(commits))
    result["raw_shards"] = len(paths)
    write_outputs(rows, result, args.out_dir)
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
