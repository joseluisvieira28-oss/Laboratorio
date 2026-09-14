#!/usr/bin/env python3
"""One-shot frozen Discovery for OPTIONS-EXPIRY-REVERSAL-001.

Must only be executed after an exact immutable SOURCE_DATASET_PASS artifact is
bound by the workflow. Downloads protected Binance BTCUSDT Spot 1m monthly
archives for 2021-05 through 2024-12 only, verifies official CHECKSUM files,
and executes the frozen regression/bootstrap/economics exactly once.
"""
from __future__ import annotations

import csv
import datetime as dt
import hashlib
import io
import json
import math
import os
import random
import statistics
import sys
import urllib.request
import zipfile
from pathlib import Path

import numpy as np

UTC = dt.timezone.utc
LAB_ID = "OPTIONS-EXPIRY-REVERSAL-001"
MVE_ID = "OER-BTC-EXPIRY-INTENSITY-30M-001"
START_DATE = dt.date(2021, 5, 2)
END_DATE = dt.date(2024, 12, 31)
BLOCK_LEN = 7
BOOTSTRAPS = 20_000
SEED = 20260914
COST10_BPS = 10.0
COST14_BPS = 14.0
BASE = "https://data.binance.vision/data/spot/monthly/klines/BTCUSDT/1m"
TARGET_MINUTES = {(7, 30): "p0730", (8, 0): "p0800", (8, 1): "p0801", (8, 31): "p0831"}


def sha256_bytes(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def sha256_file(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as f:
        for c in iter(lambda: f.read(1024 * 1024), b""):
            h.update(c)
    return h.hexdigest()


def locate_unique(root: Path, name: str) -> Path:
    xs = [p for p in root.rglob(name) if p.is_file()]
    if len(xs) != 1:
        raise RuntimeError(f"expected exactly one {name}, found {len(xs)}")
    return xs[0]


def month_iter(start: dt.date, end: dt.date):
    y, m = start.year, start.month
    while (y, m) <= (end.year, end.month):
        yield y, m
        if m == 12:
            y += 1; m = 1
        else:
            m += 1


def http_get(url: str) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": "CryptoLab-OER-Discovery/0.1"})
    with urllib.request.urlopen(req, timeout=90) as r:
        if r.status != 200:
            raise RuntimeError(f"HTTP {r.status}: {url}")
        return r.read()


def parse_checksum(raw: bytes, expected_name: str) -> str:
    text = raw.decode("utf-8", errors="strict").strip()
    parts = text.split()
    if not parts or len(parts[0]) != 64:
        raise RuntimeError(f"invalid CHECKSUM body for {expected_name}: {text[:200]}")
    if len(parts) >= 2 and parts[-1].lstrip("*") != expected_name:
        raise RuntimeError(f"CHECKSUM filename mismatch: {text}")
    return parts[0].lower()


def load_source(source_root: Path):
    csv_path = locate_unique(source_root, "BTC_EXPIRY_INTENSITY_SOURCE_20210502_20241231.csv")
    receipt_path = locate_unique(source_root, "SOURCE_DATASET_RECEIPT.json")
    receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
    if receipt.get("lab_id") != LAB_ID or receipt.get("mve_id") != MVE_ID:
        raise RuntimeError("source receipt lab/MVE mismatch")
    if receipt.get("classification") != "SOURCE_DATASET_PASS":
        raise RuntimeError(f"source classification is not PASS: {receipt.get('classification')}")
    for k in ("btc_market_data_accessed", "btc_returns_computed", "pnl_computed", "open_interest_accessed", "gamma_exposure_computed", "access_2025", "access_2026"):
        if receipt.get(k) is not False:
            raise RuntimeError(f"source protection flag not false: {k}")
    if sha256_file(csv_path) != receipt.get("source_csv_sha256"):
        raise RuntimeError("source CSV hash mismatch")
    rows = []
    with csv_path.open(newline="", encoding="utf-8") as f:
        for r in csv.DictReader(f):
            d = dt.date.fromisoformat(r["date"])
            if not START_DATE <= d <= END_DATE:
                raise RuntimeError(f"source date outside protected Discovery: {d}")
            rows.append({
                "date": d,
                "high": int(r["high_expiry_pressure"]),
                "share": float(r["expiry_activity_share"]),
                "trail_median": float(r["trailing_30d_median_share"]),
            })
    if not rows or rows[0]["date"] != START_DATE or rows[-1]["date"] != END_DATE:
        raise RuntimeError("source date endpoints mismatch")
    if any((b["date"] - a["date"]).days != 1 for a, b in zip(rows, rows[1:])):
        raise RuntimeError("source dates are not consecutive calendar days")
    return rows, receipt, csv_path, receipt_path


def acquire_prices(target_dates: set[dt.date], out: Path):
    prices: dict[dt.date, dict[str, float]] = {d: {} for d in target_dates}
    archives = []
    for y, m in month_iter(START_DATE, END_DATE):
        if y >= 2025:
            raise RuntimeError("forbidden archive year")
        name = f"BTCUSDT-1m-{y:04d}-{m:02d}.zip"
        url = f"{BASE}/{name}"
        checksum_url = url + ".CHECKSUM"
        checksum_raw = http_get(checksum_url)
        expected = parse_checksum(checksum_raw, name)
        blob = http_get(url)
        actual = sha256_bytes(blob)
        if actual != expected:
            raise RuntimeError(f"official Binance checksum mismatch {name}")
        z = zipfile.ZipFile(io.BytesIO(blob))
        names = z.namelist()
        if len(names) != 1:
            raise RuntimeError(f"unexpected Binance ZIP member count {name}: {names}")
        member = names[0]
        rows_seen = 0
        required_seen = 0
        with z.open(member, "r") as raw:
            txt = io.TextIOWrapper(raw, encoding="utf-8", newline="")
            for row in csv.reader(txt):
                if not row:
                    continue
                if len(row) < 5:
                    raise RuntimeError(f"short Binance row in {name}")
                try:
                    open_ts = int(row[0])
                    open_px = float(row[1])
                except ValueError:
                    # Defensive support for a header row, though Binance archive CSVs are normally headerless.
                    if rows_seen == 0:
                        continue
                    raise
                rows_seen += 1
                if open_ts >= 10**14:
                    raise RuntimeError(f"unexpected timestamp unit before 2025 in {name}: {open_ts}")
                ts = dt.datetime.fromtimestamp(open_ts / 1000, tz=UTC)
                if ts.year != y or ts.month != m:
                    raise RuntimeError(f"timestamp outside archive month {name}: {ts.isoformat()}")
                d = ts.date()
                if d not in target_dates:
                    continue
                key = TARGET_MINUTES.get((ts.hour, ts.minute))
                if key is None or ts.second != 0 or ts.microsecond != 0:
                    continue
                if key in prices[d]:
                    raise RuntimeError(f"duplicate exact minute {d} {key}")
                if not math.isfinite(open_px) or open_px <= 0:
                    raise RuntimeError(f"invalid open price {d} {key}")
                prices[d][key] = open_px
                required_seen += 1
        archives.append({
            "name": name,
            "url": url,
            "checksum_url": checksum_url,
            "sha256": actual,
            "bytes": len(blob),
            "rows_seen": rows_seen,
            "required_points_seen": required_seen,
        })
    missing = {d.isoformat(): sorted(set(["p0730","p0800","p0801","p0831"]) - set(v)) for d, v in prices.items() if len(v) != 4}
    if missing:
        raise RuntimeError(f"missing exact protected one-minute points: {list(missing.items())[:10]}")
    return prices, archives


def design(rows):
    X=[]; y=[]
    for r in rows:
        d=r["date"]
        pre=r["r_pre"]
        high=float(r["high"])
        vec=[1.0, pre, high, pre*high]
        wd=d.weekday()
        vec.extend(1.0 if wd==i else 0.0 for i in range(1,7))
        vec.extend(1.0 if d.year==yr else 0.0 for yr in (2022,2023,2024))
        X.append(vec); y.append(r["r_post"])
    return np.asarray(X,dtype=np.float64), np.asarray(y,dtype=np.float64)


def fit_beta_int(X, y):
    beta, _, rank, _ = np.linalg.lstsq(X, y, rcond=None)
    if rank != X.shape[1]:
        raise RuntimeError(f"rank-deficient OLS: rank={rank} cols={X.shape[1]}")
    return beta, float(beta[3])


def bootstrap_p(rows, X, y):
    n=len(rows)
    starts=np.arange(0, n-BLOCK_LEN+1, dtype=np.int64)
    if len(starts) == 0:
        raise RuntimeError("insufficient rows for block bootstrap")
    rng=np.random.default_rng(SEED)
    betas=np.empty(BOOTSTRAPS,dtype=np.float64)
    blocks_needed=(n + BLOCK_LEN - 1)//BLOCK_LEN
    offsets=np.arange(BLOCK_LEN,dtype=np.int64)
    for b in range(BOOTSTRAPS):
        chosen=rng.choice(starts,size=blocks_needed,replace=True)
        idx=(chosen[:,None]+offsets[None,:]).reshape(-1)[:n]
        Xb=X[idx]; yb=y[idx]
        beta, _, rank, _=np.linalg.lstsq(Xb,yb,rcond=None)
        if rank != X.shape[1]:
            raise RuntimeError(f"rank-deficient bootstrap replicate {b}: rank={rank}")
        betas[b]=beta[3]
    p=(1.0 + float(np.count_nonzero(betas >= 0.0))) / (BOOTSTRAPS + 1.0)
    return p, betas


def profit_factor(vals):
    pos=sum(v for v in vals if v > 0)
    neg=-sum(v for v in vals if v < 0)
    if neg == 0:
        return math.inf if pos > 0 else 0.0
    return pos/neg


def equity_metrics(net_returns):
    equity=1.0; peak=1.0; max_dd=0.0
    for r in net_returns:
        equity *= (1.0+r)
        peak=max(peak,equity)
        dd=equity/peak-1.0
        max_dd=min(max_dd,dd)
    return equity-1.0, max_dd


def main():
    source_root=Path(sys.argv[1]) if len(sys.argv)>1 else Path("source_artifact")
    out=Path(sys.argv[2]) if len(sys.argv)>2 else Path("artifacts/options_expiry_reversal_discovery_v01")
    out.mkdir(parents=True,exist_ok=True)
    protocol=Path("labs/OPTIONS_EXPIRY_REVERSAL_001/FROZEN_PRE_SOURCE_PROTOCOL_V0.1.md")
    semantics=Path("labs/OPTIONS_EXPIRY_REVERSAL_001/PRE_OUTCOME_EXECUTION_SEMANTICS_V0.1.md")
    if not protocol.exists() or not semantics.exists():
        raise RuntimeError("frozen protocol/semantics missing")

    src, source_receipt, source_csv_path, source_receipt_path=load_source(source_root)
    target={r["date"] for r in src}
    prices, archives=acquire_prices(target,out)

    rows=[]
    for s in src:
        d=s["date"]; p=prices[d]
        rpre=p["p0800"]/p["p0730"]-1.0
        rpost=p["p0831"]/p["p0801"]-1.0
        rows.append({**s, **p, "r_pre":rpre, "r_post":rpost})

    X,y=design(rows)
    beta,beta_int=fit_beta_int(X,y)
    p_boot, boot_betas=bootstrap_p(rows,X,y)

    trades=[]
    for r in rows:
        if r["high"] != 1 or r["r_pre"] == 0.0:
            continue
        direction=-1.0 if r["r_pre"] > 0 else 1.0
        gross=direction*r["r_post"]
        gross_bps=gross*10000.0
        trades.append({"date":r["date"],"direction":"SHORT" if direction<0 else "LONG","r_pre":r["r_pre"],"r_post":r["r_post"],"gross_return":gross,"gross_bps":gross_bps,"net10_bps":gross_bps-COST10_BPS,"net14_bps":gross_bps-COST14_BPS})

    gross=[t["gross_bps"] for t in trades]; net10=[t["net10_bps"] for t in trades]; net14=[t["net14_bps"] for t in trades]
    net14_returns=[t["gross_return"]-COST14_BPS/10000.0 for t in trades]
    cum14, maxdd14=equity_metrics(net14_returns)
    partitions={}
    positive_gross_by_year={}
    for yr in (2021,2022,2023,2024):
        ts=[t for t in trades if t["date"].year==yr]
        vals=[t["net14_bps"] for t in ts]
        posgross=sum(max(t["gross_bps"],0.0) for t in ts)
        positive_gross_by_year[str(yr)]=posgross
        partitions[str(yr)]={"n":len(ts),"mean_gross_bps":statistics.fmean([t["gross_bps"] for t in ts]) if ts else None,"mean_net14_bps":statistics.fmean(vals) if vals else None,"net14_nonnegative":bool(vals and statistics.fmean(vals)>=0.0)}
    total_pos=sum(positive_gross_by_year.values())
    concentration=max(positive_gross_by_year.values())/total_pos if total_pos>0 else math.inf

    mean_net10=statistics.fmean(net10) if net10 else float("nan")
    mean_net14=statistics.fmean(net14) if net14 else float("nan")
    pf14=profit_factor(net14)
    nonneg_years=sum(1 for x in partitions.values() if x["net14_nonnegative"])
    gates={
        "source_pass":True,
        "beta_int_negative":beta_int<0.0,
        "bootstrap_p_le_005":p_boot<=0.05,
        "mean_net10_positive":mean_net10>0.0,
        "mean_net14_positive":mean_net14>0.0,
        "pf_net14_gt_1":pf14>1.0,
        "calendar_partitions_3_of_4_nonnegative_net14":nonneg_years>=3,
        "positive_gross_concentration_le_60pct":concentration<=0.60,
    }
    promoted=all(gates.values())
    if not gates["beta_int_negative"] or not gates["bootstrap_p_le_005"]:
        scientific="NO_STATISTICAL_EDGE"
    elif not promoted:
        scientific="NEGATIVE_EXPECTANCY_OR_ROBUSTNESS_FAIL"
    else:
        scientific="DISCOVERY_PROMOTION_CANDIDATE"

    outcome_csv=out/"DISCOVERY_DAILY_ROWS.csv"
    with outcome_csv.open("w",newline="",encoding="utf-8") as f:
        fields=["date","high","share","trail_median","p0730","p0800","p0801","p0831","r_pre","r_post"]
        w=csv.DictWriter(f,fieldnames=fields); w.writeheader()
        for r in rows: w.writerow({k:(v.isoformat() if isinstance(v,dt.date) else v) for k,v in r.items() if k in fields})
    trades_csv=out/"DISCOVERY_TRADES.csv"
    with trades_csv.open("w",newline="",encoding="utf-8") as f:
        fields=["date","direction","r_pre","r_post","gross_return","gross_bps","net10_bps","net14_bps"]
        w=csv.DictWriter(f,fieldnames=fields); w.writeheader()
        for t in trades: w.writerow({**t,"date":t["date"].isoformat()})

    receipt={
        "lab_id":LAB_ID,"mve_id":MVE_ID,"classification":scientific,"promoted":promoted,"promotion_gates":gates,
        "protected_start":START_DATE.isoformat(),"protected_end":END_DATE.isoformat(),"rows":len(rows),"trades":len(trades),
        "ols_coefficients":{"alpha":float(beta[0]),"beta_pre":float(beta[1]),"beta_high":float(beta[2]),"beta_int":beta_int},
        "bootstrap":{"block_len_calendar_rows":BLOCK_LEN,"replications":BOOTSTRAPS,"seed":SEED,"one_sided_p_beta_int_lt_0":p_boot,"beta_int_bootstrap_mean":float(np.mean(boot_betas)),"beta_int_bootstrap_median":float(np.median(boot_betas))},
        "economics":{"mean_gross_bps":statistics.fmean(gross) if gross else None,"mean_net10_bps":mean_net10,"mean_net14_bps":mean_net14,"profit_factor_net14":pf14,"win_rate_net14":sum(v>0 for v in net14)/len(net14) if net14 else None,"cumulative_net14_return":cum14,"max_drawdown_net14":maxdd14,"positive_gross_pnl_max_partition_share":concentration},
        "calendar_partitions":partitions,
        "positive_gross_by_year_bps":positive_gross_by_year,
        "binance_monthly_archives":archives,
        "source_receipt_sha256":sha256_file(source_receipt_path),"source_csv_sha256":sha256_file(source_csv_path),
        "protocol_sha256":sha256_file(protocol),"execution_semantics_sha256":sha256_file(semantics),
        "daily_rows_sha256":sha256_file(outcome_csv),"trades_csv_sha256":sha256_file(trades_csv),
        "access_2025":False,"access_2026":False,"live_trading":False,"exchange_mutation":False,"post_outcome_tuning":False,
    }
    (out/"DISCOVERY_RECEIPT.json").write_text(json.dumps(receipt,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    print(json.dumps(receipt,indent=2,sort_keys=True))
    return 0

if __name__=="__main__":
    raise SystemExit(main())
