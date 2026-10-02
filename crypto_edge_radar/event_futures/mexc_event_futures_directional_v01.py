from __future__ import annotations

import csv
import gzip
import hashlib
import json
import math
import os
import time
import urllib.parse
import urllib.request
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

API_BASE = "https://api.mexc.com"
ASSETS = {
    "BTCUSDT": "BTC_USDT",
    "ETHUSDT": "ETH_USDT",
    "NVDAUSDT": "NVIDIA_USDT",
    "MUUSDT": "MUSTOCK_USDT",
    "SPCXUSDT": "SPCXSTOCK_USDT",
}
LOOKBACKS = (5, 15, 60, 240, 1440)
HORIZONS = (10, 30, 60, 1440)
FAMILIES = ("MOMENTUM", "REVERSAL")

FETCH_START = 1782345600   # 2026-06-25T00:00:00Z
DEV_START = 1782864000     # 2026-07-01T00:00:00Z
DEV_END = 1785542400       # 2026-08-01T00:00:00Z
OOS_START = DEV_END
OOS_END = 1788220800       # 2026-09-01T00:00:00Z
HOLD_START = OOS_END
HOLD_END = 1790812800      # 2026-10-01T00:00:00Z

BAR_SECONDS = 300
CHUNK_BARS = 1900
REQUEST_SLEEP_SECONDS = 0.13
USER_AGENT = "crypto-edge-radar/mexc-event-futures-directional-v01"


class SourceError(RuntimeError):
    pass


@dataclass
class Metric:
    asset: str
    symbol: str
    partition: str
    horizon_min: int
    lookback_min: int
    family: str
    eligible: int
    ties: int
    wins: int
    losses: int
    target_up: int
    target_down: int
    accuracy: float | None
    ci_low: float | None
    ci_high: float | None
    p_value: float
    mean_margin_bps: float | None
    bh_q: float | None = None
    dev_survivor: bool = False
    oos_survivor: bool = False
    holdout_survivor: bool = False
    above_80pct_payout_be_point: bool = False

    def key(self) -> tuple[str, int, int, str]:
        return (self.asset, self.horizon_min, self.lookback_min, self.family)

    def as_dict(self) -> dict[str, Any]:
        return self.__dict__.copy()


def iso(ts: int) -> str:
    return datetime.fromtimestamp(ts, tz=timezone.utc).isoformat().replace("+00:00", "Z")


def http_json(url: str, retries: int = 6) -> tuple[dict[str, Any], str]:
    last: Exception | None = None
    for attempt in range(retries):
        try:
            req = urllib.request.Request(
                url,
                headers={"User-Agent": USER_AGENT, "Accept": "application/json"},
            )
            with urllib.request.urlopen(req, timeout=30) as r:
                raw = r.read()
                if int(r.status) != 200:
                    raise SourceError(f"HTTP_{r.status}")
            payload = json.loads(raw.decode("utf-8"))
            digest = hashlib.sha256(raw).hexdigest()
            return payload, digest
        except Exception as exc:
            last = exc
            time.sleep(min(8.0, 0.75 * (2 ** attempt)))
    raise SourceError(f"REQUEST_FAILED:{type(last).__name__}:{last}")


def parse_kline(payload: dict[str, Any], req_start: int, req_end: int) -> list[tuple[int, float]]:
    if payload.get("success") is not True:
        raise SourceError(
            f"API_SUCCESS_FALSE:{payload.get('code')}:{payload.get('message')}"
        )
    data = payload.get("data")
    if not isinstance(data, dict):
        raise SourceError("DATA_NOT_OBJECT")
    times = data.get("time")
    closes = data.get("close")
    if not isinstance(times, list) or not isinstance(closes, list):
        raise SourceError("TIME_CLOSE_NOT_ARRAY")
    if len(times) != len(closes):
        raise SourceError("TIME_CLOSE_LENGTH_MISMATCH")
    out: list[tuple[int, float]] = []
    for ts0, close0 in zip(times, closes):
        ts = int(ts0)
        close = float(close0)
        if not math.isfinite(close) or close <= 0:
            raise SourceError("INVALID_CLOSE")
        if ts < req_start - 120 or ts > req_end + 120:
            raise SourceError(f"TIMESTAMP_OUTSIDE_REQUEST:{ts}")
        out.append((ts, close))
    return out


def fetch_series(
    symbol: str,
    start_s: int,
    end_s: int,
    phase: str,
) -> tuple[dict[int, float], list[dict[str, Any]]]:
    points: dict[int, float] = {}
    manifest: list[dict[str, Any]] = []
    cur = start_s
    chunk_seconds = CHUNK_BARS * BAR_SECONDS
    request_no = 0
    while cur < end_s:
        stop = min(end_s - BAR_SECONDS, cur + chunk_seconds - BAR_SECONDS)
        q = urllib.parse.urlencode(
            {"interval": "Min5", "start": str(cur), "end": str(stop)}
        )
        url = f"{API_BASE}/api/v1/contract/kline/index_price/{symbol}?{q}"
        payload, digest = http_json(url)
        rows = parse_kline(payload, cur, stop)
        for ts, close in rows:
            if start_s <= ts < end_s:
                if ts in points and points[ts] != close:
                    raise SourceError(f"CONFLICTING_DUPLICATE:{symbol}:{ts}")
                points[ts] = close
        manifest.append(
            {
                "phase": phase,
                "symbol": symbol,
                "request_no": request_no,
                "requested_start": cur,
                "requested_end": stop,
                "rows_returned": len(rows),
                "sha256": digest,
            }
        )
        request_no += 1
        cur = stop + BAR_SECONDS
        time.sleep(REQUEST_SLEEP_SECONDS)

    ordered = sorted(points)
    if not ordered:
        raise SourceError(f"EMPTY_SERIES:{symbol}:{phase}")
    if any(t % 60 != 0 for t in ordered):
        raise SourceError(f"NON_MINUTE_TIMESTAMP:{symbol}:{phase}")
    return points, manifest


def write_corpus_gz(path: str, series: dict[str, dict[int, float]]) -> str:
    h = hashlib.sha256()
    with gzip.open(path, "wt", newline="", encoding="utf-8") as f:
        f.write("asset,timestamp_utc,close\n")
        for asset in sorted(series):
            for ts in sorted(series[asset]):
                line = f"{asset},{iso(ts)},{series[asset][ts]:.12g}\n"
                f.write(line)
                h.update(line.encode("utf-8"))
    return h.hexdigest()


def wilson(wins: int, n: int) -> tuple[float | None, float | None]:
    if n <= 0:
        return None, None
    z = 1.959963984540054
    p = wins / n
    den = 1.0 + z * z / n
    center = (p + z * z / (2 * n)) / den
    half = z * math.sqrt((p * (1 - p) + z * z / (4 * n)) / n) / den
    return max(0.0, center - half), min(1.0, center + half)


def _logaddexp(a: float, b: float) -> float:
    if a == -math.inf:
        return b
    if b == -math.inf:
        return a
    m = max(a, b)
    return m + math.log(math.exp(a - m) + math.exp(b - m))


def exact_two_sided_binom_p(wins: int, n: int) -> float:
    if n <= 0:
        return 1.0
    k = max(wins, n - wins)
    if k <= n / 2:
        return 1.0
    logsum = -math.inf
    log2 = math.log(2.0)
    for j in range(k, n + 1):
        lp = (
            math.lgamma(n + 1)
            - math.lgamma(j + 1)
            - math.lgamma(n - j + 1)
            - n * log2
        )
        logsum = _logaddexp(logsum, lp)
    one_tail = 0.0 if logsum < -745 else math.exp(logsum)
    return min(1.0, 2.0 * one_tail)


def is_entry_grid(ts: int, horizon: int) -> bool:
    dt = datetime.fromtimestamp(ts, tz=timezone.utc)
    if horizon == 10:
        return dt.minute % 10 == 0
    if horizon == 30:
        return dt.minute % 30 == 0
    if horizon == 60:
        return dt.minute == 0
    if horizon == 1440:
        return dt.hour == 0 and dt.minute == 0
    raise ValueError(horizon)


def evaluate_cell(
    asset: str,
    symbol: str,
    prices: dict[int, float],
    partition: str,
    part_start: int,
    part_end: int,
    horizon: int,
    lookback: int,
    family: str,
) -> Metric:
    wins = losses = ties = target_up = target_down = 0
    margins: list[float] = []

    for ts in range(part_start, part_end, BAR_SECONDS):
        if not is_entry_grid(ts, horizon):
            continue
        target_ts = ts + horizon * 60
        look_ts = ts - lookback * 60
        if target_ts >= part_end:
            continue
        p0 = prices.get(ts)
        p_prev = prices.get(look_ts)
        p1 = prices.get(target_ts)
        if p0 is None or p_prev is None or p1 is None:
            continue
        trailing = p0 / p_prev - 1.0
        if trailing == 0:
            continue
        pred = 1 if trailing > 0 else -1
        if family == "REVERSAL":
            pred *= -1

        if p1 > p0:
            actual = 1
            target_up += 1
        elif p1 < p0:
            actual = -1
            target_down += 1
        else:
            ties += 1
            continue

        margin_bps = (p1 / p0 - 1.0) * 10000.0
        margins.append(pred * margin_bps)
        if pred == actual:
            wins += 1
        else:
            losses += 1

    n = wins + losses
    acc = wins / n if n else None
    lo, hi = wilson(wins, n)
    return Metric(
        asset=asset,
        symbol=symbol,
        partition=partition,
        horizon_min=horizon,
        lookback_min=lookback,
        family=family,
        eligible=n,
        ties=ties,
        wins=wins,
        losses=losses,
        target_up=target_up,
        target_down=target_down,
        accuracy=acc,
        ci_low=lo,
        ci_high=hi,
        p_value=exact_two_sided_binom_p(wins, n),
        mean_margin_bps=(sum(margins) / len(margins)) if margins else None,
        above_80pct_payout_be_point=bool(acc is not None and acc > (1.0 / 1.8)),
    )


def evaluate_partition(
    series: dict[str, dict[int, float]],
    partition: str,
    start_s: int,
    end_s: int,
    restrict_keys: set[tuple[str, int, int, str]] | None = None,
) -> list[Metric]:
    out: list[Metric] = []
    for asset, symbol in ASSETS.items():
        prices = series[asset]
        for horizon in HORIZONS:
            for lookback in LOOKBACKS:
                for family in FAMILIES:
                    key = (asset, horizon, lookback, family)
                    if restrict_keys is not None and key not in restrict_keys:
                        continue
                    out.append(
                        evaluate_cell(
                            asset, symbol, prices, partition, start_s, end_s,
                            horizon, lookback, family
                        )
                    )
    return out


def apply_bh(metrics: list[Metric]) -> None:
    m = len(metrics)
    ranked = sorted(enumerate(metrics), key=lambda x: x[1].p_value)
    adjusted = [1.0] * m
    running = 1.0
    for rank_rev in range(m - 1, -1, -1):
        original_idx, metric = ranked[rank_rev]
        rank = rank_rev + 1
        raw_adj = metric.p_value * m / rank
        running = min(running, raw_adj)
        adjusted[original_idx] = min(1.0, running)
    for i, metric in enumerate(metrics):
        metric.bh_q = adjusted[i]


def minimum_n(horizon: int) -> int:
    return 20 if horizon == 1440 else 100


def mark_development(metrics: list[Metric]) -> set[tuple[str, int, int, str]]:
    apply_bh(metrics)
    survivors: set[tuple[str, int, int, str]] = set()
    for m in metrics:
        m.dev_survivor = bool(
            m.eligible >= minimum_n(m.horizon_min)
            and m.accuracy is not None
            and m.accuracy > 0.50
            and m.bh_q is not None
            and m.bh_q <= 0.05
        )
        if m.dev_survivor:
            survivors.add(m.key())
    return survivors


def mark_oos(
    metrics: list[Metric],
    dev_survivors: set[tuple[str, int, int, str]],
) -> set[tuple[str, int, int, str]]:
    survivors: set[tuple[str, int, int, str]] = set()
    for m in metrics:
        m.oos_survivor = bool(
            m.key() in dev_survivors
            and m.eligible >= minimum_n(m.horizon_min)
            and m.accuracy is not None
            and m.accuracy > 0.50
            and m.p_value <= 0.05
        )
        if m.oos_survivor:
            survivors.add(m.key())
    return survivors


def mark_holdout(
    metrics: list[Metric],
    oos_survivors: set[tuple[str, int, int, str]],
) -> set[tuple[str, int, int, str]]:
    survivors: set[tuple[str, int, int, str]] = set()
    for m in metrics:
        m.holdout_survivor = bool(
            m.key() in oos_survivors
            and m.eligible >= minimum_n(m.horizon_min)
            and m.accuracy is not None
            and m.accuracy > 0.50
            and m.p_value <= 0.05
        )
        if m.holdout_survivor:
            survivors.add(m.key())
    return survivors


def sensitivity() -> list[dict[str, float]]:
    return [
        {"payout": payout, "break_even_win_rate": 1.0 / (1.0 + payout)}
        for payout in (0.70, 0.75, 0.80, 0.85, 0.90)
    ]


def top_rows(metrics: list[Metric], n: int = 15) -> list[Metric]:
    return sorted(
        metrics,
        key=lambda m: (
            -(m.accuracy if m.accuracy is not None else -1.0),
            m.p_value,
            -m.eligible,
        ),
    )[:n]


def pct(x: float | None) -> str:
    return "NA" if x is None else f"{100*x:.3f}%"


def write_markdown(
    path: str,
    dev: list[Metric],
    oos: list[Metric],
    hold: list[Metric],
    dev_keys: set[tuple[str, int, int, str]],
    oos_keys: set[tuple[str, int, int, str]],
    hold_keys: set[tuple[str, int, int, str]],
    source_manifest_sha: str,
) -> None:
    lines: list[str] = []
    lines.append("# MEXC EVENT FUTURES — DIRECTIONAL V0.1 RESULT")
    lines.append("")
    lines.append("Status: RESEARCH ONLY — FIVE_MINUTE_GRID_DIRECTIONAL_PROXY")
    lines.append("")
    lines.append(f"- Development survivors: **{len(dev_keys)}**")
    lines.append(f"- OOS survivors: **{len(oos_keys)}**")
    lines.append(f"- Holdout survivors: **{len(hold_keys)}**")
    lines.append(f"- Source manifest SHA256: {source_manifest_sha}")
    lines.append("- Historical Event Futures payout-at-entry: **NOT PROVEN**")
    lines.append("- Historical product PnL claim: **NOT AUTHORIZED**")
    lines.append("")
    lines.append("## Payout sensitivity")
    lines.append("")
    lines.append("| Payout | Break-even win rate |")
    lines.append("|---:|---:|")
    for row in sensitivity():
        lines.append(
            f"| {100*row['payout']:.0f}% | {100*row['break_even_win_rate']:.3f}% |"
        )
    lines.append("")

    def table(title: str, rows: list[Metric], survivor_keys: set[tuple[str,int,int,str]]) -> None:
        lines.append(f"## {title}")
        lines.append("")
        if not rows:
            lines.append("No rows.")
            lines.append("")
            return
        lines.append("| Asset | H | L | Family | N | Acc | 95% CI | p | BH q | Survivor | >80% BE |")
        lines.append("|---|---:|---:|---|---:|---:|---|---:|---:|---|---|")
        for m in rows:
            lines.append(
                f"| {m.asset} | {m.horizon_min}m | {m.lookback_min}m | {m.family} | "
                f"{m.eligible} | {pct(m.accuracy)} | {pct(m.ci_low)}–{pct(m.ci_high)} | "
                f"{m.p_value:.3g} | "
                f"{'NA' if m.bh_q is None else f'{m.bh_q:.3g}'} | "
                f"{'YES' if m.key() in survivor_keys else 'NO'} | "
                f"{'YES' if m.above_80pct_payout_be_point else 'NO'} |"
            )
        lines.append("")

    table("Development — top accuracy cells", top_rows(dev, 20), dev_keys)
    oos_rows = [m for m in oos if m.key() in dev_keys]
    table("OOS — development survivors only", oos_rows, oos_keys)
    table("Final holdout — OOS survivors only", hold, hold_keys)

    lines.append("## Interpretation firewall")
    lines.append("")
    lines.append(
        "A DIRECTIONAL_HOLDOUT_SURVIVOR is evidence only for the frozen five-minute-grid "
        "directional proxy. It is not proof of Event Futures profitability because "
        "historical payout-at-entry remains unproven and Event Futures cannot be "
        "automated through the official MEXC API."
    )
    lines.append("")
    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")


def main() -> int:
    os.makedirs("event_futures_v01_output", exist_ok=True)
    manifest: list[dict[str, Any]] = []
    preholdout: dict[str, dict[int, float]] = {}

    for asset, symbol in ASSETS.items():
        points, pages = fetch_series(symbol, FETCH_START, OOS_END, "PREHOLDOUT")
        preholdout[asset] = points
        manifest.extend(pages)

    preholdout_corpus_sha = write_corpus_gz(
        "event_futures_v01_output/preholdout_corpus_v01.csv.gz", preholdout
    )

    dev = evaluate_partition(preholdout, "DEVELOPMENT", DEV_START, DEV_END)
    dev_keys = mark_development(dev)

    oos_all = evaluate_partition(preholdout, "OOS", OOS_START, OOS_END)
    oos_keys = mark_oos(oos_all, dev_keys)

    hold: list[Metric] = []
    hold_keys: set[tuple[str, int, int, str]] = set()
    holdout_corpus_sha: str | None = None

    if oos_keys:
        hold_series: dict[str, dict[int, float]] = {}
        hold_fetch_start = HOLD_START - max(LOOKBACKS) * 60
        for asset, symbol in ASSETS.items():
            points, pages = fetch_series(symbol, hold_fetch_start, HOLD_END, "HOLDOUT")
            hold_series[asset] = points
            manifest.extend(pages)
        holdout_corpus_sha = write_corpus_gz(
            "event_futures_v01_output/holdout_corpus_v01.csv.gz", hold_series
        )
        hold = evaluate_partition(
            hold_series, "HOLDOUT", HOLD_START, HOLD_END, restrict_keys=oos_keys
        )
        hold_keys = mark_holdout(hold, oos_keys)

    manifest_json = json.dumps(manifest, indent=2, sort_keys=True)
    manifest_sha = hashlib.sha256(manifest_json.encode("utf-8")).hexdigest()
    with open(
        "event_futures_v01_output/source_page_manifest_v01.json",
        "w",
        encoding="utf-8",
    ) as f:
        f.write(manifest_json + "\n")

    result = {
        "lab_id": "MEXC_EVENT_FUTURES_DIRECTIONAL_V0.1",
        "created_utc": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "science_freeze": "MEXC_EVENT_FUTURES_DIRECTIONAL_PREOUTCOME_FREEZE_V0.1 + TRANSPORT_AMENDMENT_01",
        "proxy": "FIVE_MINUTE_GRID_DIRECTIONAL_PROXY",
        "assets": ASSETS,
        "lookbacks_min": list(LOOKBACKS),
        "settlement_horizons_min": list(HORIZONS),
        "families": list(FAMILIES),
        "partitions": {
            "development": [iso(DEV_START), iso(DEV_END)],
            "oos": [iso(OOS_START), iso(OOS_END)],
            "holdout": [iso(HOLD_START), iso(HOLD_END)],
            "october_2026_opened": False,
        },
        "source_manifest_sha256": manifest_sha,
        "preholdout_corpus_sha256": preholdout_corpus_sha,
        "holdout_corpus_sha256": holdout_corpus_sha,
        "development_survivor_count": len(dev_keys),
        "oos_survivor_count": len(oos_keys),
        "holdout_opened": bool(oos_keys),
        "holdout_survivor_count": len(hold_keys),
        "payout_history_status": "NOT_PROVEN",
        "historical_product_pnl_authorized": False,
        "event_futures_api_trading_supported": False,
        "payout_sensitivity": sensitivity(),
        "development": [m.as_dict() for m in dev],
        "oos": [m.as_dict() for m in oos_all],
        "holdout": [m.as_dict() for m in hold],
        "development_survivor_keys": [list(x) for x in sorted(dev_keys)],
        "oos_survivor_keys": [list(x) for x in sorted(oos_keys)],
        "holdout_survivor_keys": [list(x) for x in sorted(hold_keys)],
        "orders_created": False,
        "private_account_endpoint_used": False,
    }

    with open(
        "event_futures_v01_output/MEXC_EVENT_FUTURES_DIRECTIONAL_V01_RESULT.json",
        "w",
        encoding="utf-8",
    ) as f:
        json.dump(result, f, indent=2, sort_keys=True)
        f.write("\n")

    write_markdown(
        "event_futures_v01_output/MEXC_EVENT_FUTURES_DIRECTIONAL_V01_RESULT.md",
        dev, oos_all, hold, dev_keys, oos_keys, hold_keys, manifest_sha
    )

    print(
        json.dumps(
            {
                "development_survivors": len(dev_keys),
                "oos_survivors": len(oos_keys),
                "holdout_opened": bool(oos_keys),
                "holdout_survivors": len(hold_keys),
                "source_manifest_sha256": manifest_sha,
                "preholdout_corpus_sha256": preholdout_corpus_sha,
                "holdout_corpus_sha256": holdout_corpus_sha,
                "orders_created": False,
                "private_account_endpoint_used": False,
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
