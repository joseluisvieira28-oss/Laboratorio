#!/usr/bin/env python3
import hashlib, io, json, math, os, re, sys, time, zipfile
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd
import requests

SEED = 20261005
SYMBOLS = ["BTCUSDT", "ETHUSDT"]
START_YEAR, END_YEAR = 2021, 2025
FUNDING_THRESHOLD = 0.0005
PRE60_THRESHOLD = 0.005
PRIMARY_HOURS = 4
PRIMARY_COST_BPS = 8.0
MIN_PRIMARY_N = 40
MIN_ASSET_N = 10
BASE = "https://data.binance.vision/data/futures/um/monthly"
OUT = Path("research/funding_shock_reset/results_v01")
OUT.mkdir(parents=True, exist_ok=True)

session = requests.Session()
session.headers.update({"User-Agent": "CryptoLab-FundingShockReset-V0.1/ResearchOnly"})

def months():
    for y in range(START_YEAR, END_YEAR + 1):
        for m in range(1, 13):
            yield y, m

def get(url, retries=4):
    last = None
    for i in range(retries):
        try:
            r = session.get(url, timeout=60)
            if r.status_code == 200:
                return r.content
            last = RuntimeError(f"HTTP {r.status_code}: {url}")
        except Exception as e:
            last = e
        time.sleep(1.5 * (i + 1))
    raise RuntimeError(f"download failed after retries: {url}: {last}")

def verify_download(url):
    payload = get(url)
    check = get(url + ".CHECKSUM").decode("utf-8", errors="replace").strip()
    expected = check.split()[0].strip().lower()
    actual = hashlib.sha256(payload).hexdigest().lower()
    if not re.fullmatch(r"[0-9a-f]{64}", expected):
        raise RuntimeError(f"invalid checksum sidecar for {url}: {check[:160]}")
    if expected != actual:
        raise RuntimeError(f"checksum mismatch for {url}: expected={expected} actual={actual}")
    return payload, actual

def unzip_csv_bytes(payload):
    with zipfile.ZipFile(io.BytesIO(payload)) as z:
        names = [n for n in z.namelist() if n.lower().endswith(".csv")]
        if len(names) != 1:
            raise RuntimeError(f"expected exactly 1 csv, got {names}")
        return z.read(names[0])

def normalize_epoch_ms(s):
    x = pd.to_numeric(s, errors="coerce")
    med = float(x.dropna().median()) if x.notna().any() else float("nan")
    if not math.isfinite(med):
        return x
    if med > 1e17:
        x = np.floor(x / 1_000_000)
    elif med > 1e14:
        x = np.floor(x / 1_000)
    return x.astype("Int64")

def parse_klines(csv_bytes, symbol, archive_sha):
    raw = pd.read_csv(io.BytesIO(csv_bytes), header=None, dtype=str)
    if raw.empty:
        raise RuntimeError(f"empty kline archive {symbol}")
    first = str(raw.iloc[0, 0]).strip().lower()
    if first in ("open_time", "opentime"):
        raw = raw.iloc[1:].reset_index(drop=True)
    if raw.shape[1] < 12:
        raise RuntimeError(f"unexpected kline columns={raw.shape[1]} {symbol}")
    cols = ["open_time","open","high","low","close","volume","close_time","quote_volume","trades","taker_buy_base","taker_buy_quote","ignore"]
    raw = raw.iloc[:, :12]
    raw.columns = cols
    raw["open_time"] = normalize_epoch_ms(raw["open_time"])
    for c in ("open","high","low","close","volume"):
        raw[c] = pd.to_numeric(raw[c], errors="coerce")
    raw = raw.dropna(subset=["open_time","open","close"]).copy()
    raw["open_time"] = raw["open_time"].astype("int64")
    raw["symbol"] = symbol
    raw["archive_sha256"] = archive_sha
    return raw[["open_time","open","close","symbol"]]

def _header_tokens(raw):
    return [str(x).strip().lower() for x in raw.iloc[0].tolist()]

def parse_funding(csv_bytes, symbol, archive_sha):
    raw = pd.read_csv(io.BytesIO(csv_bytes), header=None, dtype=str)
    if raw.empty:
        raise RuntimeError(f"empty funding archive {symbol}")
    tokens = _header_tokens(raw)
    has_header = any(("fund" in t) or ("calc_time" in t) for t in tokens)
    if has_header:
        df = raw.iloc[1:].copy()
        df.columns = tokens
        t_candidates = [c for c in df.columns if c in ("fundingtime","funding_time","calc_time","time","timestamp") or ("time" in c and "interval" not in c)]
        r_candidates = [c for c in df.columns if c in ("fundingrate","funding_rate","last_funding_rate") or ("fund" in c and "rate" in c)]
        if not t_candidates or not r_candidates:
            raise RuntimeError(f"cannot identify funding columns {tokens}")
        tcol, rcol = t_candidates[0], r_candidates[-1]
        t = normalize_epoch_ms(df[tcol])
        rate = pd.to_numeric(df[rcol], errors="coerce")
    else:
        # Fail-closed inference for legacy archives: epoch-like column + small signed-rate column.
        candidates_t = []
        candidates_r = []
        for c in raw.columns:
            num = pd.to_numeric(raw[c], errors="coerce")
            good = num.dropna()
            if len(good) < max(3, int(0.8 * len(raw))):
                continue
            med = float(good.abs().median())
            p99 = float(good.abs().quantile(0.99))
            if med > 1e11:
                candidates_t.append(c)
            elif p99 <= 0.1:
                candidates_r.append(c)
        if len(candidates_t) != 1 or not candidates_r:
            raise RuntimeError(f"ambiguous legacy funding schema symbol={symbol} t={candidates_t} r={candidates_r} shape={raw.shape}")
        tcol = candidates_t[0]
        rcol = candidates_r[-1]
        t = normalize_epoch_ms(raw[tcol])
        rate = pd.to_numeric(raw[rcol], errors="coerce")
    out = pd.DataFrame({"funding_time": t, "funding_rate": rate})
    out = out.dropna().copy()
    out["funding_time"] = out["funding_time"].astype("int64")
    out["funding_rate"] = out["funding_rate"].astype(float)
    out["symbol"] = symbol
    out["archive_sha256"] = archive_sha
    # hard plausibility checks
    if (out["funding_rate"].abs() > 0.05).any():
        raise RuntimeError(f"implausible funding rate >5% detected for {symbol}")
    return out

def load_symbol(symbol):
    kframes, fframes, manifest = [], [], []
    for y, m in months():
        ym = f"{y:04d}-{m:02d}"
        kurl = f"{BASE}/klines/{symbol}/5m/{symbol}-5m-{ym}.zip"
        furl = f"{BASE}/fundingRate/{symbol}/{symbol}-fundingRate-{ym}.zip"
        kp, ksha = verify_download(kurl)
        fp, fsha = verify_download(furl)
        kdf = parse_klines(unzip_csv_bytes(kp), symbol, ksha)
        fdf = parse_funding(unzip_csv_bytes(fp), symbol, fsha)
        kframes.append(kdf)
        fframes.append(fdf)
        manifest.append({"symbol":symbol,"month":ym,"kline_url":kurl,"kline_sha256":ksha,"funding_url":furl,"funding_sha256":fsha,"kline_rows":len(kdf),"funding_rows":len(fdf)})
        print(f"loaded {symbol} {ym}: klines={len(kdf)} funding={len(fdf)}", flush=True)
    k = pd.concat(kframes, ignore_index=True).drop_duplicates("open_time").sort_values("open_time")
    f = pd.concat(fframes, ignore_index=True).drop_duplicates("funding_time").sort_values("funding_time")
    return k, f, manifest

def exact_price_maps(k):
    return dict(zip(k["open_time"].astype("int64"), k["open"].astype(float))), dict(zip(k["open_time"].astype("int64"), k["close"].astype(float)))

def build_events(symbol, k, f):
    open_map, close_map = exact_price_maps(k)
    rows = []
    five = 5 * 60 * 1000
    hour = 60 * 60 * 1000
    for rec in f.itertuples(index=False):
        t0 = int(rec.funding_time)
        dt = datetime.fromtimestamp(t0/1000, tz=timezone.utc)
        if dt.year < START_YEAR or dt.year > END_YEAR:
            continue
        # final completed close before T0 = close of bar opened T0-5m
        p_last = close_map.get(t0 - five)
        p_prev = close_map.get(t0 - five - hour)
        entry_t = t0 + five
        entry = open_map.get(entry_t)
        if None in (p_last, p_prev, entry):
            continue
        pre60 = p_last / p_prev - 1.0
        fr = float(rec.funding_rate)
        direction = 0
        if fr >= FUNDING_THRESHOLD and pre60 >= PRE60_THRESHOLD:
            direction = -1
        elif fr <= -FUNDING_THRESHOLD and pre60 <= -PRE60_THRESHOLD:
            direction = +1
        if direction == 0:
            continue
        row = {"symbol":symbol,"t0":t0,"funding_rate":fr,"pre60_return":pre60,"direction":direction,"entry_time":entry_t,"entry":entry}
        ok = True
        for h in (1,4,8):
            # Holding h hours: exit at close of bar opened entry + h - 5m.
            exit_open_t = entry_t + h*hour - five
            px = close_map.get(exit_open_t)
            if px is None:
                ok = False
                break
            row[f"ret_{h}h"] = direction * (px / entry - 1.0)
        if ok:
            rows.append(row)
    return pd.DataFrame(rows)

def event_portfolio(events):
    g = events.groupby("t0", sort=True)
    rows = []
    for t0, d in g:
        rows.append({
            "t0": int(t0),
            "n_assets": int(len(d)),
            "symbols": ",".join(sorted(d["symbol"].tolist())),
            "ret_1h": float(d["ret_1h"].mean()),
            "ret_4h": float(d["ret_4h"].mean()),
            "ret_8h": float(d["ret_8h"].mean()),
            "mean_abs_funding": float(d["funding_rate"].abs().mean()),
        })
    p = pd.DataFrame(rows).sort_values("t0").reset_index(drop=True)
    p["dt"] = pd.to_datetime(p["t0"], unit="ms", utc=True)
    p["day"] = p["dt"].dt.strftime("%Y-%m-%d")
    return p

def bootstrap_day_blocks(p, cost_bps):
    rng = np.random.default_rng(SEED)
    p = p.copy()
    p["net"] = p["ret_4h"] - cost_bps / 10000.0
    blocks = [g["net"].to_numpy(float) for _, g in p.groupby("day", sort=True)]
    if len(blocks) < 2:
        return float("nan"), float("nan")
    means = np.empty(10000, dtype=float)
    nb = len(blocks)
    for i in range(len(means)):
        idx = rng.integers(0, nb, size=nb)
        sample = np.concatenate([blocks[j] for j in idx])
        means[i] = sample.mean()
    return float(np.quantile(means, 0.025)), float(np.quantile(means, 0.975))

def summary_stats(x):
    x = np.asarray(x, dtype=float)
    return {
        "n": int(len(x)),
        "mean_bps": float(x.mean()*10000) if len(x) else None,
        "median_bps": float(np.median(x)*10000) if len(x) else None,
        "win_rate": float((x>0).mean()) if len(x) else None,
        "total_compound_pct": float((np.prod(1+x)-1)*100) if len(x) else None,
    }

def main():
    all_events, all_manifest = [], []
    coverage = {}
    for symbol in SYMBOLS:
        k, f, manifest = load_symbol(symbol)
        all_manifest.extend(manifest)
        coverage[symbol] = {
            "kline_rows": int(len(k)),
            "funding_rows": int(len(f)),
            "kline_start": int(k["open_time"].min()),
            "kline_end": int(k["open_time"].max()),
            "funding_start": int(f["funding_time"].min()),
            "funding_end": int(f["funding_time"].max()),
        }
        e = build_events(symbol, k, f)
        if e.empty:
            raise RuntimeError(f"no frozen signals for {symbol}")
        all_events.append(e)
    events = pd.concat(all_events, ignore_index=True).sort_values(["t0","symbol"]).reset_index(drop=True)
    portfolio = event_portfolio(events)

    # Hard no-2026 assertion.
    max_year = int(pd.to_datetime(events["t0"], unit="ms", utc=True).dt.year.max())
    if max_year > END_YEAR:
        raise RuntimeError("2026_OR_LATER_OUTCOME_LEAK")

    results = {
        "candidate_id":"FUNDING-SHOCK-RESET-001",
        "version":"V0.1",
        "frozen_seed":SEED,
        "source_integrity":"PASS",
        "coverage":coverage,
        "primary_horizon":"4h",
        "primary_cost_bps":PRIMARY_COST_BPS,
        "signal_thresholds":{"abs_funding":FUNDING_THRESHOLD,"abs_pre60":PRE60_THRESHOLD},
        "symbol_counts":{s:int((events.symbol==s).sum()) for s in SYMBOLS},
        "year_counts":{str(y):int((pd.to_datetime(events.t0, unit="ms", utc=True).dt.year==y).sum()) for y in range(START_YEAR, END_YEAR+1)},
        "primary_event_timestamps":int(len(portfolio)),
        "horizons":{},
        "asset_4h":{},
        "subsets":{},
    }
    for h in (1,4,8):
        results["horizons"][f"{h}h"] = summary_stats(portfolio[f"ret_{h}h"].to_numpy())

    for s in SYMBOLS:
        d = events[events.symbol==s]
        results["asset_4h"][s] = summary_stats(d["ret_4h"].to_numpy())

    for name, mask in {
        "positive_funding": events["funding_rate"] > 0,
        "negative_funding": events["funding_rate"] < 0,
    }.items():
        d = events[mask]
        results["subsets"][name] = summary_stats(d["ret_4h"].to_numpy())

    gross = portfolio["ret_4h"].to_numpy(float)
    costs = {}
    for bps in (4.0,8.0,12.0):
        costs[str(int(bps))] = summary_stats(gross - bps/10000.0)
    results["cost_stress"] = costs
    results["break_even_roundtrip_bps"] = float(gross.mean()*10000)

    lo, hi = bootstrap_day_blocks(portfolio, PRIMARY_COST_BPS)
    results["bootstrap_95_net8bps_mean_bps"] = [lo*10000, hi*10000]

    thirds = []
    for i, idx in enumerate(np.array_split(np.arange(len(portfolio)), 3), start=1):
        d = portfolio.iloc[idx]
        net = d["ret_4h"].to_numpy(float) - PRIMARY_COST_BPS/10000.0
        thirds.append({"third":i, **summary_stats(net), "start":str(d["dt"].iloc[0]), "end":str(d["dt"].iloc[-1])})
    results["chronological_thirds_net8bps"] = thirds

    gates = {}
    gates["source_integrity"] = True
    gates["min_n_40"] = len(portfolio) >= MIN_PRIMARY_N
    gates["mean_gross_positive"] = gross.mean() > 0
    gates["mean_net8_positive"] = (gross - PRIMARY_COST_BPS/10000.0).mean() > 0
    gates["bootstrap_lower_positive"] = lo > 0
    gates["all_thirds_positive"] = all(t["mean_bps"] is not None and t["mean_bps"] > 0 for t in thirds)
    asset_gate = True
    for s in SYMBOLS:
        d = events[events.symbol==s]["ret_4h"].to_numpy(float)
        if len(d) >= MIN_ASSET_N:
            asset_gate = asset_gate and (d.mean() > 0)
    gates["btc_eth_same_sign_if_n10"] = bool(asset_gate)
    gates["no_2026"] = max_year <= END_YEAR
    results["gates"] = gates
    results["verdict"] = "SURVIVES_V0.1" if all(gates.values()) else "NO_EDGE_V0.1"

    events.to_csv(OUT/"events.csv", index=False)
    portfolio.to_csv(OUT/"event_portfolio.csv", index=False)
    (OUT/"source_manifest.json").write_text(json.dumps(all_manifest, indent=2), encoding="utf-8")
    (OUT/"result.json").write_text(json.dumps(results, indent=2), encoding="utf-8")

    lines = [
        "# FUNDING-SHOCK-RESET-001 — RESULT V0.1",
        "",
        f"Verdict: **{results['verdict']}**",
        "",
        f"Primary distinct event timestamps: **{len(portfolio)}**",
        f"Signals: BTC={results['symbol_counts']['BTCUSDT']} ETH={results['symbol_counts']['ETHUSDT']}",
        f"4h gross mean: **{results['horizons']['4h']['mean_bps']:.2f} bps/event**",
        f"4h net @ 8 bps mean: **{results['cost_stress']['8']['mean_bps']:.2f} bps/event**",
        f"Break-even round-trip friction: **{results['break_even_roundtrip_bps']:.2f} bps**",
        f"95% day-block bootstrap CI for net@8bps mean: **[{results['bootstrap_95_net8bps_mean_bps'][0]:.2f}, {results['bootstrap_95_net8bps_mean_bps'][1]:.2f}] bps**",
        "",
        "## Horizons",
        "",
        "| Horizon | N | Mean bps | Median bps | Win rate |",
        "|---|---:|---:|---:|---:|",
    ]
    for h in (1,4,8):
        s = results["horizons"][f"{h}h"]
        lines.append(f"| {h}h | {s['n']} | {s['mean_bps']:.2f} | {s['median_bps']:.2f} | {100*s['win_rate']:.1f}% |")
    lines += ["", "## Cost stress", "", "| RT friction | Mean net bps | Win rate |", "|---:|---:|---:|"]
    for b in ("4","8","12"):
        s = results["cost_stress"][b]
        lines.append(f"| {b} bps | {s['mean_bps']:.2f} | {100*s['win_rate']:.1f}% |")
    lines += ["", "## Gates", ""]
    for k,v in gates.items():
        lines.append(f"- {k}: {'PASS' if v else 'FAIL'}")
    lines += ["", "## Chronological thirds — net @ 8 bps", ""]
    for t in thirds:
        lines.append(f"- Third {t['third']}: N={t['n']}, mean={t['mean_bps']:.2f} bps, total={t['total_compound_pct']:.2f}% ({t['start']} → {t['end']})")
    lines += ["", "## Asset replication", ""]
    for s in SYMBOLS:
        a=results["asset_4h"][s]
        lines.append(f"- {s}: N={a['n']}, mean 4h={a['mean_bps']:.2f} bps, win={100*a['win_rate']:.1f}%")
    lines += ["", "Research only. No 2026 outcomes. No live trading. No post-outcome tuning."]
    (OUT/"RESULT_V0.1.md").write_text("\n".join(lines)+"\n", encoding="utf-8")
    print(json.dumps(results, indent=2))
    print(f"VERDICT={results['verdict']}")

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        fail = {"candidate_id":"FUNDING-SHOCK-RESET-001","version":"V0.1","verdict":"SOURCE_BLOCKED_V0.1","error":repr(e)}
        (OUT/"result.json").write_text(json.dumps(fail, indent=2), encoding="utf-8")
        (OUT/"RESULT_V0.1.md").write_text(f"# FUNDING-SHOCK-RESET-001 — RESULT V0.1\n\nVerdict: **SOURCE_BLOCKED_V0.1**\n\nError: `{repr(e)}`\n", encoding="utf-8")
        print(json.dumps(fail, indent=2))
        sys.exit(2)
