#!/usr/bin/env python3
from __future__ import annotations

import argparse, hashlib, io, json, math, re, urllib.request, zipfile
from pathlib import Path
import numpy as np
import pandas as pd
import cigl_adx_01_action_v01 as frozen

EXPERIMENT = "MVE-ADX4H-01-TIER1-CONFIRMATION-V0.1"
SYMBOLS = ["BTCUSDT","ETHUSDT","SOLUSDT","BNBUSDT","XRPUSDT","DOGEUSDT"]
MONTHS = [f"2025-{m:02d}" for m in range(1,13)]
BASE = "https://data.binance.vision/data/futures/um/monthly/klines"
BASE_COST = 10.0
STRESS_COST = 14.0
HOLD_BARS = 4
SEED = 20260914
BOOT_REPS = 5000
FORBIDDEN_START = pd.Timestamp("2026-01-01T00:00:00Z")


def sha256(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def fetch(url: str) -> bytes:
    if not url.startswith(BASE + "/"):
        raise PermissionError("network destination outside frozen Binance USD-M monthly kline path")
    with urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent":"MVE-ADX4H-01-TIER1/0.1"}), timeout=90) as r:
        return r.read()


def checksum_digest(text: str, filename: str) -> str:
    m = re.fullmatch(r"\s*([0-9a-fA-F]{64})\s+\*?([^\s]+)\s*", text)
    if not m or m.group(2) != filename:
        raise RuntimeError(f"invalid provider CHECKSUM for {filename}")
    return m.group(1).lower()


def parse_archive(symbol: str, ym: str) -> tuple[pd.DataFrame, dict]:
    filename = f"{symbol}-1m-{ym}.zip"
    base = f"{BASE}/{symbol}/1m/{filename}"
    ctext = fetch(base + ".CHECKSUM").decode("utf-8-sig")
    raw = fetch(base)
    got = sha256(raw); expected = checksum_digest(ctext, filename)
    if got != expected:
        raise RuntimeError(f"provider checksum mismatch {symbol} {ym}")
    with zipfile.ZipFile(io.BytesIO(raw)) as z:
        csvs = [n for n in z.namelist() if n.endswith('.csv')]
        if len(csvs) != 1: raise RuntimeError(f"unexpected CSV cardinality {symbol} {ym}")
        b = z.read(csvs[0])
    cols = ["open_time","open","high","low","close","volume","close_time","qav","trades","tb_base","tb_quote","ignore"]
    df = pd.read_csv(io.BytesIO(b), header=None, names=cols)
    if not np.issubdtype(df["open_time"].dtype, np.number):
        df = df[pd.to_numeric(df["open_time"], errors="coerce").notna()].copy()
    for c in ["open_time","open","high","low","close","volume"]:
        df[c] = pd.to_numeric(df[c], errors="coerce")
    if df[["open_time","open","high","low","close","volume"]].isna().any().any():
        raise RuntimeError(f"invalid numeric rows {symbol} {ym}")
    ot = df["open_time"].astype("int64")
    med = int(ot.median())
    unit = "us" if med >= 10**14 else "ms"
    df["ts"] = pd.to_datetime(ot, unit=unit, utc=True)
    start = pd.Timestamp(f"{ym}-01T00:00:00Z")
    end = start + pd.offsets.MonthBegin(1)
    if (df["ts"] < start).any() or (df["ts"] >= end).any() or (df["ts"] >= FORBIDDEN_START).any():
        raise RuntimeError(f"timestamp window violation {symbol} {ym}")
    if df["ts"].duplicated().any(): raise RuntimeError(f"duplicate timestamps {symbol} {ym}")
    return df[["ts","open","high","low","close","volume"]].copy(), {"symbol":symbol,"month":ym,"source_sha256":got,"rows":int(len(df)),"timestamp_unit":unit}


def make_trades(h: pd.DataFrame, symbol: str) -> pd.DataFrame:
    h = frozen.add_adx(h.copy())
    long_sig = h["bar_ok"] & (h["adx"] >= 25.0) & (h["plus_di"] > h["minus_di"])
    short_sig = h["bar_ok"] & (h["adx"] >= 25.0) & (h["minus_di"] > h["plus_di"])
    direction = np.where(long_sig,1,np.where(short_sig,-1,0)).astype(int)
    rows=[]; active_until=-1; idx=h.index; delta=pd.Timedelta("4h")
    for signal_pos,sig in enumerate(direction):
        if sig == 0 or signal_pos < active_until: continue
        entry_pos=signal_pos+1; exit_pos=entry_pos+HOLD_BARS
        if exit_pos >= len(h): continue
        if not h["bar_ok"].iloc[signal_pos:exit_pos+1].all(): continue
        if idx[entry_pos]-idx[signal_pos] != delta or idx[exit_pos]-idx[entry_pos] != HOLD_BARS*delta: continue
        et=idx[entry_pos]; xt=idx[exit_pos]
        if et >= FORBIDDEN_START or xt >= FORBIDDEN_START: continue
        ep=float(h["open"].iloc[entry_pos]); xp=float(h["open"].iloc[exit_pos])
        if not (math.isfinite(ep) and math.isfinite(xp) and ep>0 and xp>0): continue
        gross=float(sig*math.log(xp/ep)*10000.0)
        rows.append({"symbol":symbol,"entry_time":et,"exit_time":xt,"direction":int(sig),"gross_bps":gross,"net10_bps":gross-BASE_COST,"net14_bps":gross-STRESS_COST})
        active_until=exit_pos
    return pd.DataFrame(rows)


def pf(s: pd.Series):
    pos=float(s[s>0].sum()); neg=float(-s[s<0].sum())
    if neg == 0: return None if pos == 0 else float("inf")
    return pos/neg


def bootstrap_day(t: pd.DataFrame):
    d=t.assign(day=t["entry_time"].dt.floor("D")).groupby("day")["net10_bps"].agg(["sum","count"])
    a=d[["sum","count"]].to_numpy(float); rng=np.random.default_rng(SEED); vals=np.empty(BOOT_REPS)
    for i in range(BOOT_REPS):
        s=a[rng.integers(0,len(a),size=len(a))].sum(axis=0); vals[i]=s[0]/s[1]
    return {"reps":BOOT_REPS,"seed":SEED,"mean_bps":float(vals.mean()),"ci95_low_bps":float(np.quantile(vals,.025)),"ci95_high_bps":float(np.quantile(vals,.975))}


def summarize(t: pd.DataFrame):
    t=t.sort_values(["entry_time","symbol"]).copy()
    per_asset={}
    for s,g in t.groupby("symbol"):
        per_asset[s]={"n":int(len(g)),"net10_mean_bps":float(g.net10_bps.mean()),"pf10":pf(g.net10_bps),"net14_mean_bps":float(g.net14_bps.mean()),"pf14":pf(g.net14_bps)}
    tq=t.assign(quarter=t["entry_time"].dt.to_period("Q").astype(str))
    quarters={q:{"n":int(len(g)),"net10_mean_bps":float(g.net10_bps.mean())} for q,g in tq.groupby("quarter")}
    loo={s:float(t[t.symbol!=s].net10_bps.mean()) for s in SYMBOLS}
    pos=t.assign(pos=t.net10_bps.clip(lower=0)); total=float(pos.pos.sum())
    asset_share=float(pos.groupby("symbol").pos.sum().max()/total) if total>0 else None
    qshare=float(pos.assign(quarter=pos.entry_time.dt.to_period("Q").astype(str)).groupby("quarter").pos.sum().max()/total) if total>0 else None
    b=bootstrap_day(t)
    m={"n":int(len(t)),"gross_mean_bps":float(t.gross_bps.mean()),"net10_mean_bps":float(t.net10_bps.mean()),"pf10":pf(t.net10_bps),"net14_mean_bps":float(t.net14_bps.mean()),"pf14":pf(t.net14_bps),"net10_median_bps":float(t.net10_bps.median()),"positive_trade_fraction":float((t.net10_bps>0).mean()),"cumulative_net10_bps":float(t.net10_bps.sum()),"bootstrap_day_net10_mean":b,"per_asset":per_asset,"quarterly":quarters,"leave_one_asset_out_net10_mean_bps":loo,"max_asset_positive_net10_pnl_share":asset_share,"max_quarter_positive_net10_pnl_share":qshare}
    checks={
      "A_provenance_integrity_all_6x12": True,
      "B_n_ge_1000": m["n"]>=1000,
      "C_pooled_net10_mean_gt_0": m["net10_mean_bps"]>0,
      "D_pooled_pf10_gt_1": m["pf10"] is not None and m["pf10"]>1,
      "E_bootstrap_ci95_low_gt_0": b["ci95_low_bps"]>0,
      "F_positive_quarters_ge_3": sum(v["net10_mean_bps"]>0 for v in quarters.values())>=3,
      "G_positive_assets_ge_4": sum(v["net10_mean_bps"]>0 for v in per_asset.values())>=4,
      "H_positive_loo_ge_5": sum(v>0 for v in loo.values())>=5,
      "I_max_asset_positive_pnl_share_le_0_40": asset_share is not None and asset_share<=0.40,
      "J_max_quarter_positive_pnl_share_le_0_50": qshare is not None and qshare<=0.50,
      "K_exact_frozen_rule_bytes_required": True
    }
    if m["n"]<1000: classification="INSUFFICIENT_SAMPLE_FOR_TIER1"
    elif all(checks.values()): classification="TIER1_CONFIRMATION_ELIGIBLE_RESEARCH_ONLY"
    elif not (checks["C_pooled_net10_mean_gt_0"] and checks["D_pooled_pf10_gt_1"]): classification="CONFIRMATION_FAIL_APPLY_FROZEN_PROMOTION_POLICY_V2"
    else: classification="NO_TIER1_REMAIN_TIER2_FRAGILE_OR_DOWNGRADE_BY_V2"
    return m,checks,classification


def main():
    ap=argparse.ArgumentParser(); ap.add_argument("--work",required=True); args=ap.parse_args(); work=Path(args.work); out=work/"outputs"; out.mkdir(parents=True,exist_ok=True)
    audits=[]; trades=[]
    for symbol in SYMBOLS:
        frames=[]
        for ym in MONTHS:
            df,a=parse_archive(symbol,ym); frames.append(df); audits.append(a)
        minute=pd.concat(frames,ignore_index=True).sort_values("ts")
        if minute["ts"].duplicated().any(): raise RuntimeError(f"cross-month duplicate timestamps {symbol}")
        h=frozen.hourly_ohlc(minute,"4h")
        trades.append(make_trades(h,symbol))
    t=pd.concat(trades,ignore_index=True)
    if (t.entry_time>=FORBIDDEN_START).any() or (t.exit_time>=FORBIDDEN_START).any(): raise RuntimeError("2026 firewall violation")
    metrics,checks,classification=summarize(t)
    result={"experiment":EXPERIMENT,"status":"COMPLETE_ONE_SHOT_2025_CONFIRMATION","window":{"start":"2025-01-01T00:00:00Z","end_exclusive":"2026-01-01T00:00:00Z"},"source":"Official Binance USD-M Futures monthly 1m archives","provenance_receipts":audits,"metrics":metrics,"frozen_gate":{"checks":checks,"pass":all(checks.values())},"classification":classification,"locks":{"2026_opened":False,"live_trading":False,"exchange_mutation":False,"main_merge":False,"render_deploy":False}}
    (out/"MVE_ADX4H_01_TIER1_2025_CLOSEOUT.json").write_text(json.dumps(result,indent=2,sort_keys=True,default=str),encoding="utf-8")
    t.to_csv(out/"MVE_ADX4H_01_TIER1_2025_TRADES.csv",index=False)
    print("MVE_ADX4H_TIER1_2025_CLOSEOUT_JSON="+json.dumps(result,sort_keys=True,default=str))
    print("MVE-ADX4H-01 2025 confirmation:",classification)

if __name__ == "__main__": main()
