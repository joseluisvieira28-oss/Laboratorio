#!/usr/bin/env python3
from __future__ import annotations

import csv
import hashlib
import json
import math
import os
import statistics
import time
import urllib.parse
import urllib.request
import zipfile
from datetime import datetime, timedelta, timezone
from pathlib import Path

import tv_footprint_calibration_001 as cal

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "tradingview" / "terminal" / "run_output"
RAW = OUT / "binance_raw"
OUT.mkdir(parents=True, exist_ok=True)
RAW.mkdir(parents=True, exist_ok=True)

SAMPLE_PARTS = [
    ROOT / "tradingview" / "terminal" / "TVFP_TERMINAL_SAMPLE_2016_PART_A.csv",
    ROOT / "tradingview" / "terminal" / "TVFP_TERMINAL_SAMPLE_2016_PART_B.csv",
]

VISION_BASE = "https://data.binance.vision/data/spot/daily/aggTrades/BTCUSDT"
API_BASES = [
    "https://data-api.binance.vision/api/v3/aggTrades",
    "https://api.binance.com/api/v3/aggTrades",
]


def sha256_bytes(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def get_bytes(url: str, attempts: int = 5) -> bytes:
    last = None
    for i in range(attempts):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "CryptoLab-TVFP/0.1"})
            with urllib.request.urlopen(req, timeout=60) as r:
                return r.read()
        except Exception as exc:
            last = exc
            time.sleep(min(2 ** i, 10))
    raise RuntimeError(f"download failed after retries: {url}: {last}")


def to_ms(v: int | float | str) -> int:
    x = int(v)
    ax = abs(x)
    if ax < 10**11:
        return x * 1000
    if ax < 10**14:
        return x
    if ax < 10**17:
        return x // 1000
    return x // 1_000_000


def load_tv() -> list[dict]:
    rows = []
    seen = set()
    for path in SAMPLE_PARTS:
        with path.open(newline="", encoding="utf-8") as fh:
            for r in csv.DictReader(fh):
                bo = int(r["bar_open_ms"])
                if bo in seen:
                    raise RuntimeError(f"duplicate TV bar_open_ms {bo}")
                seen.add(bo)
                rows.append({
                    "bar_open_ms": bo,
                    "bar_close_ms": int(r["bar_close_ms"]),
                    "tv_total_volume": float(r["tv_total_volume"]),
                    "tv_delta": float(r["tv_delta"]),
                    "evidence_key": r["evidence_key"],
                    "payload_sha256": r["payload_sha256"],
                })
    rows.sort(key=lambda r: r["bar_open_ms"])
    if len(rows) != cal.MIN_MATCHED_BARS:
        raise RuntimeError(f"TV terminal sample must be exactly 2016, got {len(rows)}")
    for a, b in zip(rows, rows[1:]):
        if b["bar_open_ms"] - a["bar_open_ms"] != cal.BAR_MS:
            raise RuntimeError("TV terminal sample gap")
    return rows


def download_historical_day(day: str) -> tuple[Path, dict]:
    name = f"BTCUSDT-aggTrades-{day}.zip"
    url = f"{VISION_BASE}/{name}"
    checksum_url = url + ".CHECKSUM"
    zbytes = get_bytes(url)
    cbytes = get_bytes(checksum_url)
    actual = sha256_bytes(zbytes)
    expected = cbytes.decode("utf-8", "replace").strip().split()[0].lower()
    if actual != expected:
        raise RuntimeError(f"Binance Vision checksum mismatch {day}: {actual} != {expected}")
    zpath = RAW / name
    zpath.write_bytes(zbytes)
    with zipfile.ZipFile(zpath) as zf:
        members = [m for m in zf.namelist() if not m.endswith("/")]
        if len(members) != 1:
            raise RuntimeError(f"unexpected ZIP members for {day}: {members}")
        out = RAW / f"{day}.csv"
        out.write_bytes(zf.read(members[0]))
    return out, {
        "date": day,
        "source_type": "BINANCE_VISION_DAILY_AGGTRADES",
        "url": url,
        "checksum_url": checksum_url,
        "zip_sha256": actual,
        "checksum_verified": True,
    }


def api_json(params: dict) -> tuple[list[dict], str]:
    last = None
    for base in API_BASES:
        url = base + "?" + urllib.parse.urlencode(params)
        try:
            raw = get_bytes(url, attempts=3)
            obj = json.loads(raw)
            if not isinstance(obj, list):
                raise RuntimeError(f"unexpected API object: {obj}")
            return obj, base
        except Exception as exc:
            last = exc
    raise RuntimeError(f"all official Binance public API bases failed: {last}")


def fetch_live_segment(start_ms: int, end_ms: int) -> tuple[list[dict], dict]:
    """Fetch exact public aggTrades over [start_ms, end_ms)."""
    all_rows = {}
    requests = 0
    base_used = set()
    hour = start_ms
    while hour < end_ms:
        seg_end = min(hour + 3600_000, end_ms)
        batch, base = api_json({
            "symbol": "BTCUSDT",
            "startTime": hour,
            "endTime": seg_end - 1,
            "limit": 1000,
        })
        requests += 1
        base_used.add(base)
        for x in batch:
            t = to_ms(x["T"])
            if hour <= t < seg_end:
                all_rows[int(x["a"])] = x

        while len(batch) == 1000:
            last_id = int(batch[-1]["a"])
            nxt, base = api_json({
                "symbol": "BTCUSDT",
                "fromId": last_id + 1,
                "limit": 1000,
            })
            requests += 1
            base_used.add(base)
            if not nxt:
                break
            batch = nxt
            crossed = False
            for x in batch:
                t = to_ms(x["T"])
                if t >= seg_end:
                    crossed = True
                    continue
                if t >= hour:
                    all_rows[int(x["a"])] = x
            if crossed:
                break
        hour = seg_end

    rows = [all_rows[k] for k in sorted(all_rows)]
    if not rows:
        raise RuntimeError("current-day Binance aggTrades source returned no rows")

    path = RAW / "2026-10-01-live-aggTrades.csv"
    with path.open("w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        for x in rows:
            w.writerow([x["a"], x["p"], x["q"], x["f"], x["l"], x["T"], x["m"], x.get("M", True)])

    raw_jsonl = "".join(json.dumps(x, sort_keys=True, separators=(",", ":")) + "\n" for x in rows)
    raw_path = RAW / "2026-10-01-live-aggTrades.jsonl"
    raw_path.write_text(raw_jsonl, encoding="utf-8")

    return [dict(x) for x in rows], {
        "date": "2026-10-01",
        "source_type": "BINANCE_PUBLIC_SPOT_API_AGGTRADES",
        "api_bases_used": sorted(base_used),
        "request_count": requests,
        "aggregate_trade_rows": len(rows),
        "first_agg_trade_id": int(rows[0]["a"]),
        "last_agg_trade_id": int(rows[-1]["a"]),
        "first_timestamp_ms": to_ms(rows[0]["T"]),
        "last_timestamp_ms": to_ms(rows[-1]["T"]),
        "raw_jsonl_sha256": sha256_bytes(raw_jsonl.encode()),
        "authenticated": False,
    }


def sample_hash(tv: list[dict]) -> str:
    h = hashlib.sha256()
    for r in tv:
        h.update((
            f'{r["evidence_key"]}|{r["payload_sha256"]}|{r["bar_open_ms"]}|'
            f'{r["bar_close_ms"]}|{r["tv_total_volume"]:.17g}|{r["tv_delta"]:.17g}\n'
        ).encode())
    return h.hexdigest()


def main() -> None:
    tv = load_tv()
    eval_start = tv[0]["bar_open_ms"]
    eval_end = tv[-1]["bar_close_ms"]

    first_date = datetime.fromtimestamp(eval_start / 1000, tz=timezone.utc).date()
    last_date = datetime.fromtimestamp((eval_end - 1) / 1000, tz=timezone.utc).date()

    csv_paths = []
    provenance = []
    day = first_date
    while day < last_date:
        p, prov = download_historical_day(day.isoformat())
        csv_paths.append(p)
        provenance.append(prov)
        day += timedelta(days=1)

    live_start = int(datetime(last_date.year, last_date.month, last_date.day, tzinfo=timezone.utc).timestamp() * 1000)
    live_rows, live_prov = fetch_live_segment(live_start, eval_end)
    provenance.append(live_prov)
    live_csv = RAW / "2026-10-01-live-aggTrades.csv"
    csv_paths.append(live_csv)

    agg = cal.aggregate_binance(csv_paths)
    report = cal.calibrate(tv, agg)

    if report.get("terminal_interval_start_ms") != eval_start or report.get("terminal_interval_end_ms") != eval_end:
        raise RuntimeError("terminal interval drift")
    if report.get("terminal_tv_bars") != 2016:
        raise RuntimeError("terminal TV count drift")

    report["tv_terminal_sample_sha256"] = sample_hash(tv)
    report["binance_source_receipts"] = provenance
    report["verdict_is_terminal"] = bool(report["minimum_evidence_satisfied"])
    report["trading_authority"] = "NONE"
    report["edge_authority"] = "NONE"

    (OUT / "TVFP_TERMINAL_CALIBRATION_REPORT.json").write_text(
        json.dumps(report, indent=2, sort_keys=True, allow_nan=False) + "\n",
        encoding="utf-8",
    )
    (OUT / "BINANCE_SOURCE_PROVENANCE.json").write_text(
        json.dumps(provenance, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    tv_map = {int(r["bar_open_ms"]): r for r in tv}
    agg_map = {int(r["bar_open_ms"]): r for r in agg if eval_start <= int(r["bar_open_ms"]) < eval_end}
    with (OUT / "TVFP_TERMINAL_BAR_COMPARISON.csv").open("w", newline="", encoding="utf-8") as fh:
        fields = ["bar_open_ms","bar_close_ms","tv_total_volume","agg_base_volume","relative_volume_error","tv_delta","agg_delta","sign_match"]
        w = csv.DictWriter(fh, fieldnames=fields)
        w.writeheader()
        for k in sorted(tv_map):
            t = tv_map[k]
            a = agg_map.get(k)
            if a is None:
                w.writerow({"bar_open_ms":k,"bar_close_ms":k+cal.BAR_MS,"tv_total_volume":t["tv_total_volume"],"tv_delta":t["tv_delta"]})
                continue
            rel = abs(t["tv_total_volume"]-a["agg_base_volume"])/a["agg_base_volume"] if a["agg_base_volume"] else math.nan
            st=(t["tv_delta"]>0)-(t["tv_delta"]<0)
            sa=(a["agg_delta"]>0)-(a["agg_delta"]<0)
            w.writerow({
                "bar_open_ms":k,"bar_close_ms":k+cal.BAR_MS,
                "tv_total_volume":t["tv_total_volume"],"agg_base_volume":a["agg_base_volume"],
                "relative_volume_error":rel,"tv_delta":t["tv_delta"],"agg_delta":a["agg_delta"],
                "sign_match":int(st==sa) if st and sa else "",
            })

    print(json.dumps(report, indent=2, sort_keys=True, allow_nan=False))


if __name__ == "__main__":
    main()
