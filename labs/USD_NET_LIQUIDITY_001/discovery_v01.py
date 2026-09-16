#!/usr/bin/env python3
from __future__ import annotations

import csv
import hashlib
import io
import json
import math
import os
import pathlib
import random
import statistics
import urllib.request
import zipfile
from datetime import date, datetime, timedelta, timezone

LAB_ID = "USD-NET-LIQUIDITY-001"
MVE_ID = "UNL-FED-TGA-RRP-W1-001"
MACRO_START = "2017-12-27"
MACRO_END = "2024-12-18"
EXPECTED_RAW = {
    "WALCL": "f9fbf97ef2d7528b0740457046fcf9d68f9ada73ef65975ca4388c4f7340d060",
    "WDTGAL": "c8cf69cc94a50f65fbd31ef4cc640fa07d77f197d257d9d823f551b7c82c9ee4",
    "RRPONTSYD": "c7baab35063f36e75b2361cc1c78c16091bfd595af93bc76672a4f54724f5e72",
}
EXPECTED_ALIGNED_SHA = "7706003c6cd99f0b4a44140a0db8e03967722b44e3e4be58a745d5af23751219"
EXPECTED_DELTAS_SHA = "b13bdabe229da799f49ef0563fe7085b9cf70ea85d1ecbed5318bc8ef2ce8728"
EXPECTED_ALIGNED_N = 359
EXPECTED_DELTAS_N = 358
ENTRY_START = date(2018, 1, 5)
ENTRY_END = date(2024, 12, 20)
LATEST_EXIT = date(2024, 12, 27)
COST_PRIMARY = 10.0
COST_STRESS = 20.0
BOOT_REPS = 5000
BOOT_SEED = 230911
BOOT_BLOCK = 4
MIN_TRADES = 300
OUT = pathlib.Path(os.environ.get("UNL_DISCOVERY_OUT", "artifacts/usd_net_liquidity_discovery_v01"))


def sha256(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def get(url: str, timeout: int = 60) -> bytes:
    if "2025" in url or "2026" in url:
        raise RuntimeError(f"PROTECTED_PERIOD_URL_BLOCKED:{url}")
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 USD-NET-LIQUIDITY-001 research-only"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        b = r.read()
    if not b:
        raise RuntimeError(f"EMPTY_DOWNLOAD:{url}")
    return b


def fetch_macro(sid: str) -> bytes:
    return get(f"https://fred.stlouisfed.org/graph/fredgraph.csv?id={sid}&cosd={MACRO_START}&coed={MACRO_END}")


def parse_macro(sid: str, body: bytes) -> dict[str, float]:
    rows = list(csv.DictReader(io.StringIO(body.decode("utf-8-sig"))))
    if not rows:
        raise RuntimeError(f"NO_MACRO_ROWS:{sid}")
    value_col = sid if sid in rows[0] else [c for c in rows[0] if c not in {"observation_date", "DATE"}][0]
    out = {}
    for r in rows:
        ds = (r.get("observation_date") or r.get("DATE") or "").strip()
        if not ds:
            continue
        if ds < MACRO_START or ds > MACRO_END:
            raise RuntimeError(f"PROTECTED_MACRO_DATE:{sid}:{ds}")
        raw = (r.get(value_col) or "").strip()
        if raw in {"", "."}:
            continue
        v = float(raw)
        if not math.isfinite(v) or ds in out:
            raise RuntimeError(f"BAD_MACRO_ROW:{sid}:{ds}")
        out[ds] = v
    return out


def bind_macro():
    parsed = {}
    raw_hashes = {}
    for sid in ("WALCL", "WDTGAL", "RRPONTSYD"):
        b = fetch_macro(sid)
        h = sha256(b)
        if h != EXPECTED_RAW[sid]:
            raise RuntimeError(f"MACRO_RAW_HASH_MISMATCH:{sid}:{h}")
        raw_hashes[sid] = h
        parsed[sid] = parse_macro(sid, b)
    aligned = []
    for ds in sorted(set(parsed["WALCL"]) & set(parsed["WDTGAL"]) & set(parsed["RRPONTSYD"])):
        if date.fromisoformat(ds).weekday() != 2:
            continue
        nl = parsed["WALCL"][ds] - parsed["WDTGAL"][ds] - 1000.0 * parsed["RRPONTSYD"][ds]
        aligned.append({
            "date": ds,
            "walcl_musd": parsed["WALCL"][ds],
            "wdtgal_musd": parsed["WDTGAL"][ds],
            "rrp_busd": parsed["RRPONTSYD"][ds],
            "net_liquidity_musd": nl,
        })
    deltas = []
    for prev, cur in zip(aligned, aligned[1:]):
        deltas.append({
            "date": cur["date"],
            "previous_eligible_date": prev["date"],
            "delta_net_liquidity_musd": cur["net_liquidity_musd"] - prev["net_liquidity_musd"],
        })
    ab = ("\n".join(json.dumps(r, sort_keys=True) for r in aligned) + "\n").encode()
    db = ("\n".join(json.dumps(r, sort_keys=True) for r in deltas) + "\n").encode()
    if len(aligned) != EXPECTED_ALIGNED_N or sha256(ab) != EXPECTED_ALIGNED_SHA:
        raise RuntimeError("ALIGNED_SOURCE_BINDING_FAILURE")
    if len(deltas) != EXPECTED_DELTAS_N or sha256(db) != EXPECTED_DELTAS_SHA:
        raise RuntimeError("DELTA_SOURCE_BINDING_FAILURE")
    return deltas, raw_hashes


def months():
    for y in range(2018, 2025):
        for m in range(1, 13):
            yield y, m


def load_btc_daily():
    prices = {}
    market_manifest = []
    for y, m in months():
        ym = f"{y:04d}-{m:02d}"
        name = f"BTCUSDT-1d-{ym}.zip"
        base = f"https://data.binance.vision/data/spot/monthly/klines/BTCUSDT/1d/{name}"
        zbytes = get(base, timeout=90)
        cbytes = get(base + ".CHECKSUM", timeout=60)
        expected = cbytes.decode("utf-8", errors="strict").strip().split()[0].lower()
        actual = sha256(zbytes)
        if len(expected) != 64 or actual != expected:
            raise RuntimeError(f"BINANCE_CHECKSUM_FAILURE:{ym}:{actual}:{expected}")
        with zipfile.ZipFile(io.BytesIO(zbytes)) as zf:
            names = [n for n in zf.namelist() if not n.endswith("/")]
            if len(names) != 1:
                raise RuntimeError(f"BINANCE_ZIP_SHAPE:{ym}:{names}")
            rows = list(csv.reader(io.StringIO(zf.read(names[0]).decode("utf-8-sig"))))
        nrows = 0
        for r in rows:
            if not r or not r[0].isdigit():
                continue
            ts = int(r[0])
            # Historical 2018-2024 Binance Data Vision timestamps are milliseconds.
            if ts > 10**14:
                raise RuntimeError(f"UNEXPECTED_TIMESTAMP_UNIT:{ym}:{ts}")
            d = datetime.fromtimestamp(ts / 1000.0, tz=timezone.utc).date()
            if d.year != y or d.month != m:
                raise RuntimeError(f"MONTH_ARCHIVE_DATE_ESCAPE:{ym}:{d}")
            if d.year >= 2025:
                raise RuntimeError(f"PROTECTED_BTC_DATE:{d}")
            op = float(r[1])
            if not math.isfinite(op) or op <= 0 or d in prices:
                raise RuntimeError(f"BAD_BTC_OPEN:{d}")
            prices[d] = op
            nrows += 1
        market_manifest.append({"month": ym, "zip_sha256": actual, "checksum_sha256": sha256(cbytes), "rows": nrows})
    if not prices:
        raise RuntimeError("NO_BTC_PRICES")
    if max(prices) > date(2024, 12, 31):
        raise RuntimeError("PROTECTED_BTC_PERIOD_OPENED")
    return prices, market_manifest


def percentile(xs, p):
    ys = sorted(xs)
    if not ys:
        return None
    x = (len(ys) - 1) * p
    lo = int(math.floor(x)); hi = int(math.ceil(x))
    if lo == hi:
        return ys[lo]
    return ys[lo] * (hi - x) + ys[hi] * (x - lo)


def bootstrap_mean_ci(values):
    n = len(values)
    if n == 0:
        return None, None
    rng = random.Random(BOOT_SEED)
    means = []
    for _ in range(BOOT_REPS):
        sample = []
        while len(sample) < n:
            s = rng.randrange(n)
            for k in range(BOOT_BLOCK):
                sample.append(values[(s + k) % n])
                if len(sample) == n:
                    break
        means.append(sum(sample) / n)
    return percentile(means, 0.025), percentile(means, 0.975)


def profit_factor(values):
    pos = sum(v for v in values if v > 0)
    neg = -sum(v for v in values if v < 0)
    if neg == 0:
        return float("inf") if pos > 0 else 0.0
    return pos / neg


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    authority = pathlib.Path(__file__).with_name("DISCOVERY_AUTHORITY_V0.1.json")
    a = json.loads(authority.read_text(encoding="utf-8"))
    if a.get("discovery_authorized") is not True or a.get("oos_2025_authorized") is not False or a.get("access_2026_authorized") is not False:
        raise RuntimeError("AUTHORITY_FIREWALL_FAILURE")

    deltas, raw_hashes = bind_macro()
    prices, market_manifest = load_btc_daily()

    trades = []
    for r in deltas:
        wed = date.fromisoformat(r["date"])
        entry = wed + timedelta(days=2)
        exitd = entry + timedelta(days=7)
        if entry < ENTRY_START or entry > ENTRY_END:
            continue
        if exitd > LATEST_EXIT or entry.year >= 2025 or exitd.year >= 2025:
            raise RuntimeError(f"PROTECTED_TRADE_DATE:{entry}:{exitd}")
        delta = float(r["delta_net_liquidity_musd"])
        if delta == 0:
            continue
        if entry not in prices or exitd not in prices:
            raise RuntimeError(f"MISSING_BTC_OPEN:{entry}:{exitd}")
        direction = 1 if delta > 0 else -1
        entry_open = prices[entry]
        exit_open = prices[exitd]
        gross = direction * ((exit_open / entry_open) - 1.0) * 10000.0
        trades.append({
            "signal_wednesday": r["date"],
            "previous_eligible_wednesday": r["previous_eligible_date"],
            "delta_net_liquidity_musd": delta,
            "direction": "LONG" if direction == 1 else "SHORT",
            "entry_date": entry.isoformat(),
            "exit_date": exitd.isoformat(),
            "entry_open": entry_open,
            "exit_open": exit_open,
            "gross_bps": gross,
            "net10_bps": gross - COST_PRIMARY,
            "net20_bps": gross - COST_STRESS,
        })

    n = len(trades)
    net10 = [t["net10_bps"] for t in trades]
    net20 = [t["net20_bps"] for t in trades]
    gross = [t["gross_bps"] for t in trades]
    ci_lo, ci_hi = bootstrap_mean_ci(net10)
    pf10 = profit_factor(net10)
    years = {}
    for y in range(2018, 2025):
        vals = [t["net10_bps"] for t in trades if int(t["entry_date"][:4]) == y]
        years[str(y)] = {"n": len(vals), "mean_net10_bps": (sum(vals) / len(vals) if vals else None)}
    nonneg_all = sum(1 for v in years.values() if v["n"] and v["mean_net10_bps"] >= 0)
    nonneg_last4 = sum(1 for y in ("2021", "2022", "2023", "2024") if years[y]["n"] and years[y]["mean_net10_bps"] >= 0)

    mean_gross = sum(gross) / n if n else None
    mean10 = sum(net10) / n if n else None
    mean20 = sum(net20) / n if n else None
    gates = {
        "n_ge_300": n >= MIN_TRADES,
        "mean_net10_gt_0": bool(n and mean10 > 0),
        "pf_net10_gt_1": bool(n and pf10 > 1.0),
        "bootstrap_95_lower_gt_0": bool(ci_lo is not None and ci_lo > 0),
        "nonnegative_years_2018_2024_ge_5": nonneg_all >= 5,
        "nonnegative_years_2021_2024_ge_3": nonneg_last4 >= 3,
        "source_binding_pass": True,
        "access_2025": False,
        "access_2026": False,
        "live_trading": False,
        "exchange_mutation": False,
    }
    required = [gates[k] for k in (
        "n_ge_300", "mean_net10_gt_0", "pf_net10_gt_1", "bootstrap_95_lower_gt_0",
        "nonnegative_years_2018_2024_ge_5", "nonnegative_years_2021_2024_ge_3", "source_binding_pass"
    )]
    if n < MIN_TRADES:
        classification = "INSUFFICIENT_SAMPLE"
        economic_companion = None
    elif all(required):
        classification = "SURVIVES_DISCOVERY"
        economic_companion = "POSITIVE_EXPECTANCY"
    else:
        classification = "DISCOVERY_FAIL_NO_PROMOTION"
        economic_companion = "NEGATIVE_EXPECTANCY" if mean10 is not None and mean10 <= 0 else "POSITIVE_EXPECTANCY_UNCONFIRMED"

    tb = ("\n".join(json.dumps(t, sort_keys=True) for t in trades) + "\n").encode()
    (OUT / "trades_v01.jsonl").write_bytes(tb)
    market_bytes = (json.dumps(market_manifest, indent=2, sort_keys=True) + "\n").encode()
    (OUT / "btc_market_source_manifest_v01.json").write_bytes(market_bytes)
    result = {
        "lab_id": LAB_ID,
        "mve_id": MVE_ID,
        "classification": classification,
        "economic_companion": economic_companion,
        "n": n,
        "longs": sum(t["direction"] == "LONG" for t in trades),
        "shorts": sum(t["direction"] == "SHORT" for t in trades),
        "mean_gross_bps": mean_gross,
        "median_gross_bps": statistics.median(gross) if gross else None,
        "mean_net10_bps": mean10,
        "mean_net20_bps": mean20,
        "profit_factor_net10": pf10,
        "win_rate_net10": (sum(v > 0 for v in net10) / n if n else None),
        "bootstrap_mean_net10_95_ci": [ci_lo, ci_hi],
        "bootstrap_repetitions": BOOT_REPS,
        "bootstrap_seed": BOOT_SEED,
        "bootstrap_block_weeks": BOOT_BLOCK,
        "calendar_years": years,
        "nonnegative_years_2018_2024": nonneg_all,
        "nonnegative_years_2021_2024": nonneg_last4,
        "gates": gates,
        "macro_raw_sha256": raw_hashes,
        "aligned_sha256": EXPECTED_ALIGNED_SHA,
        "weekly_deltas_sha256": EXPECTED_DELTAS_SHA,
        "btc_market_manifest_sha256": sha256(market_bytes),
        "trades_sha256": sha256(tb),
        "latest_market_date_opened": max(prices).isoformat(),
        "access_2025": False,
        "access_2026": False,
        "orders_submitted": False,
        "live_trading": False,
        "exchange_mutation": False,
        "full_oos_or_live_promotion_authorized": False,
    }
    rb = (json.dumps(result, indent=2, sort_keys=True) + "\n").encode()
    (OUT / "discovery_result_v01.json").write_bytes(rb)
    manifest = {
        "result_sha256": sha256(rb),
        "trades_sha256": sha256(tb),
        "btc_market_manifest_sha256": sha256(market_bytes),
        "authority_git_path": str(authority),
    }
    (OUT / "discovery_manifest_v01.json").write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
