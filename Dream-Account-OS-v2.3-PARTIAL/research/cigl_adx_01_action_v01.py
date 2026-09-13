#!/usr/bin/env python3
from __future__ import annotations

"""CIGL-ADX-01 — frozen Wilder ADX/DMI action runner.

Rules come only from CLASSIC_INDICATORS_GAP_LAB_V01_PROTOCOL.json.
Discovery 2022-2023 is opened first. 2024 is acquired only after the frozen
1H pooled Discovery gate passes. 2025+ is structurally unreachable.
The pre-declared 4H evaluation is diagnostic only and can never rescue 1H.
"""

import hashlib
import io
import json
import math
import re
import urllib.request
import zipfile
from pathlib import Path

import numpy as np
import pandas as pd
import zstandard as zstd

import classic_indicators_gap_v01 as common

EXPERIMENT = "CIGL-ADX-01"
ADX_LENGTH = 14
ADX_THRESHOLD = 25.0
BASE = "https://data.binance.vision/data/futures/um/monthly/klines"
SYMBOLS = common.SYMBOLS
DISCOVERY_YMS = [f"{y}-{m:02d}" for y in (2022, 2023) for m in range(1, 13)]
VALIDATION_YMS = [f"2024-{m:02d}" for m in range(1, 13)]
FIELDS = [
    "open_time","open","high","low","close","volume","close_time",
    "quote_asset_volume","number_of_trades","taker_buy_base_volume",
    "taker_buy_quote_volume","ignore_provider_field","symbol","interval",
    "source_archive","source_csv","provider_sha256","source_local_sha256",
]

# Frozen from the historical H180 Run03 audit material before ADX outcomes.
EXPECTED_PHASE_RAW_FP = {
    "DISCOVERY_2022_2023": {
        "BTCUSDT": "bdd944c4dd1da8d889a3f13961bdda687ccc9afd91be29a9d9cfcafb98a4cbfa",
        "ETHUSDT": "d22c1997541fbfba8ddb3436c45e80ef98b3d35006f67e1ca692942543adbafe",
        "SOLUSDT": "def9502c70da1dee58b1ca061ff5da2d2755ec0a6a9be9a18b04c155579b9aa4",
        "BNBUSDT": "4f76a7a0592e12ff3be547723ce97e628a84061610f91c7433e3d42fa0efa5e5",
        "XRPUSDT": "e88ac51a27f78b750401116bbbff36ff339f1a73587885354b2bf4966700a1b7",
        "DOGEUSDT": "950d47f2f1f7118e0a1ccead7a402d5ac919708cfa1910b3b3eebee722e691ce",
    },
    "VALIDATION_2024": {
        "BTCUSDT": "58b16d48f55af32d9596b3b27a298a8b749c76ea7e8395c9efab4e5eabc416e2",
        "ETHUSDT": "78cacf1ebd56cc314e8ff3abdfd817ceaa79c2724bd880c0596fe418c9d70590",
        "SOLUSDT": "795283535ec8f63f5960802b3a78537e94258f1461f0cf59deefb87cc26ee3f1",
        "BNBUSDT": "a8c90d0d4dc6c63691fbb27b97e9d7276ca7a1d1cb41fbfae02910582eef0cc1",
        "XRPUSDT": "e0f6ee46f5d846b2ee8843ddff0ba9149a925369942d6bbd1e982febaba811f7",
        "DOGEUSDT": "3a0da3b5c86a56ff1f6ff17a3b197cd1abb210d1aef2e162aa3bbf402a192b23",
    },
}


def sha256_bytes(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def fetch(url: str) -> bytes:
    if not url.startswith(BASE + "/"):
        raise PermissionError("network destination outside frozen Binance USD-M monthly kline path")
    req = urllib.request.Request(url, headers={"User-Agent": "CIGL-ADX-01/0.1"})
    with urllib.request.urlopen(req, timeout=90) as r:
        return r.read()


def provider_hash(text: str, filename: str) -> str:
    m = re.fullmatch(r"\s*([0-9a-fA-F]{64})\s+\*?([^\s]+)\s*", text)
    if not m or m.group(2) != filename:
        raise RuntimeError(f"invalid provider CHECKSUM for {filename}")
    return m.group(1).lower()


def normalize_member(symbol: str, ym: str, archive: bytes, digest: str) -> tuple[str, bytes, int]:
    filename = f"{symbol}-1m-{ym}.zip"
    source_archive = f"{symbol}/1m/{filename}"
    with zipfile.ZipFile(io.BytesIO(archive)) as z:
        csvs = [n for n in z.namelist() if n.endswith(".csv")]
        if len(csvs) != 1:
            raise RuntimeError(f"unexpected CSV cardinality {source_archive}")
        source_csv = csvs[0]
        out = io.BytesIO(); rows = 0
        zc = zstd.ZstdCompressor(level=6, threads=0, write_checksum=True, write_content_size=False)
        with zc.stream_writer(out, closefd=False) as zw, z.open(source_csv) as f:
            zw.write((",".join(FIELDS) + "\n").encode())
            for raw in f:
                line = raw.decode("utf-8-sig").rstrip("\r\n")
                if not line or line.startswith("open_time,"):
                    continue
                x = line.split(",")
                if len(x) != 12:
                    raise RuntimeError(f"schema drift {source_archive}")
                ts = int(x[0])
                if ts >= 1735689600000:
                    raise PermissionError("2025+ timestamp blocked")
                zw.write((",".join(x + [symbol,"1m",source_archive,source_csv,digest,digest]) + "\n").encode())
                rows += 1
        return f"{symbol}/1m/{symbol}-1m-{ym}.normalized.csv.zst", out.getvalue(), rows


def acquire_phase(normalized_dir: Path, phase: str, months: list[str], append: bool) -> dict:
    if phase not in EXPECTED_PHASE_RAW_FP:
        raise PermissionError("unknown phase")
    if any(ym >= "2025-01" for ym in months):
        raise PermissionError("2025+ month blocked")
    if phase == "DISCOVERY_2022_2023" and any(not (ym.startswith("2022-") or ym.startswith("2023-")) for ym in months):
        raise PermissionError("Discovery year drift")
    if phase == "VALIDATION_2024" and any(not ym.startswith("2024-") for ym in months):
        raise PermissionError("Validation year drift")
    normalized_dir.mkdir(parents=True, exist_ok=True)
    rows_out = []; fps = {}
    for symbol in SYMBOLS:
        material = []
        package = normalized_dir / f"H180-0001_NORMALIZED_{symbol}.zip"
        mode = "a" if append and package.exists() else "w"
        with zipfile.ZipFile(package, mode, compression=zipfile.ZIP_STORED, allowZip64=True) as oz:
            existing = set(oz.namelist())
            for ym in months:
                filename = f"{symbol}-1m-{ym}.zip"
                url = f"{BASE}/{symbol}/1m/{filename}"
                checksum = fetch(url + ".CHECKSUM").decode("utf-8-sig")
                archive = fetch(url)
                digest = sha256_bytes(archive)
                if digest != provider_hash(checksum, filename):
                    raise RuntimeError(f"provider checksum mismatch {symbol} {ym}")
                material.append(f"{symbol}/1m/{filename}\t{digest}\n")
                member, zbytes, nrows = normalize_member(symbol, ym, archive, digest)
                if member in existing:
                    raise RuntimeError(f"duplicate normalized member {member}")
                zi = zipfile.ZipInfo(member, (1980,1,1,0,0,0)); zi.compress_type = zipfile.ZIP_STORED; zi.external_attr = 0o100444 << 16
                oz.writestr(zi, zbytes)
                rows_out.append({"symbol":symbol,"month":ym,"source_sha256":digest,"rows":nrows,"normalized_member":member})
        fp = hashlib.sha256("".join(material).encode()).hexdigest()
        expected = EXPECTED_PHASE_RAW_FP[phase][symbol]
        if fp != expected:
            raise RuntimeError(f"historical H180 raw fingerprint mismatch {phase} {symbol}: {fp} != {expected}")
        fps[symbol] = fp
        print(f"{phase} {symbol}: historical raw fingerprint MATCH", flush=True)
    return {"phase": phase, "months": [months[0], months[-1]], "symbol_raw_fingerprints": fps, "rows": rows_out}


def hourly_ohlc(minute: pd.DataFrame, freq: str) -> pd.DataFrame:
    expected = 60 if freq == "1h" else 240
    d = minute.copy().set_index("ts").sort_index()
    h = d.resample(freq, label="left", closed="left").agg(
        open=("open","first"), high=("high","max"), low=("low","min"),
        close=("close","last"), volume=("volume","sum"), minute_count=("close","count")
    )
    finite = np.isfinite(h[["open","high","low","close"]].to_numpy(float)).all(axis=1)
    h["bar_ok"] = (h["minute_count"].to_numpy() == expected) & finite
    return h


def _wilder_adx_segment(seg: pd.DataFrame, n: int = ADX_LENGTH) -> tuple[np.ndarray,np.ndarray,np.ndarray]:
    m = len(seg); adx = np.full(m, np.nan); pdi = np.full(m, np.nan); mdi = np.full(m, np.nan)
    if m < 2*n - 1:
        return adx, pdi, mdi
    hi = seg["high"].to_numpy(float); lo = seg["low"].to_numpy(float); cl = seg["close"].to_numpy(float)
    tr = np.zeros(m); pdm = np.zeros(m); mdm = np.zeros(m)
    tr[0] = hi[0] - lo[0]
    for i in range(1,m):
        tr[i] = max(hi[i]-lo[i], abs(hi[i]-cl[i-1]), abs(lo[i]-cl[i-1]))
        up = hi[i]-hi[i-1]; down = lo[i-1]-lo[i]
        pdm[i] = up if up > down and up > 0 else 0.0
        mdm[i] = down if down > up and down > 0 else 0.0
    atr = np.full(m,np.nan); sp = np.full(m,np.nan); sm = np.full(m,np.nan)
    atr[n-1] = tr[:n].mean(); sp[n-1] = pdm[:n].mean(); sm[n-1] = mdm[:n].mean()
    for i in range(n,m):
        atr[i] = (atr[i-1]*(n-1)+tr[i])/n
        sp[i] = (sp[i-1]*(n-1)+pdm[i])/n
        sm[i] = (sm[i-1]*(n-1)+mdm[i])/n
    ok = atr > 0
    pdi[ok] = 100.0 * sp[ok] / atr[ok]; mdi[ok] = 100.0 * sm[ok] / atr[ok]
    denom = pdi + mdi
    dx = np.full(m,np.nan)
    both = np.isfinite(denom) & (denom > 0)
    dx[both] = 100.0 * np.abs(pdi[both]-mdi[both]) / denom[both]
    zero = np.isfinite(denom) & (denom == 0); dx[zero] = 0.0
    first = 2*n - 2
    seed = dx[n-1:first+1]
    if np.isfinite(seed).all():
        adx[first] = seed.mean()
        for i in range(first+1,m):
            if np.isfinite(dx[i]):
                adx[i] = (adx[i-1]*(n-1)+dx[i])/n
    return adx,pdi,mdi


def add_adx(hourly: pd.DataFrame) -> pd.DataFrame:
    h = hourly.copy(); h["adx"] = np.nan; h["plus_di"] = np.nan; h["minus_di"] = np.nan
    valid = h["bar_ok"].to_numpy(bool); start = None
    for i in range(len(h)+1):
        is_valid = i < len(h) and valid[i]
        if is_valid and start is None:
            start = i
        if (not is_valid) and start is not None:
            seg = h.iloc[start:i]
            a,p,m = _wilder_adx_segment(seg)
            h.iloc[start:i, h.columns.get_loc("adx")] = a
            h.iloc[start:i, h.columns.get_loc("plus_di")] = p
            h.iloc[start:i, h.columns.get_loc("minus_di")] = m
            start = None
    return h


def make_trades(hourly: pd.DataFrame, symbol: str, timeframe: str) -> pd.DataFrame:
    h = add_adx(hourly)
    long_sig = h["bar_ok"] & (h["adx"] >= ADX_THRESHOLD) & (h["plus_di"] > h["minus_di"])
    short_sig = h["bar_ok"] & (h["adx"] >= ADX_THRESHOLD) & (h["minus_di"] > h["plus_di"])
    direction = np.where(long_sig, 1, np.where(short_sig, -1, 0)).astype(int)
    rows = []; active_until = -1; idx = h.index; bar_delta = pd.Timedelta(timeframe)
    for signal_pos, sig in enumerate(direction):
        if sig == 0 or signal_pos < active_until:
            continue
        entry_pos = signal_pos + 1; exit_pos = entry_pos + common.HOLD_BARS
        if exit_pos >= len(h):
            continue
        if not h["bar_ok"].iloc[signal_pos:exit_pos+1].all():
            continue
        if idx[entry_pos] - idx[signal_pos] != bar_delta or idx[exit_pos] - idx[entry_pos] != common.HOLD_BARS * bar_delta:
            continue
        entry_t = idx[entry_pos]; exit_t = idx[exit_pos]
        if entry_t >= common.FORBIDDEN_START or exit_t >= common.FORBIDDEN_START:
            continue
        ep = float(h["open"].iloc[entry_pos]); xp = float(h["open"].iloc[exit_pos])
        if not (math.isfinite(ep) and math.isfinite(xp) and ep > 0 and xp > 0):
            continue
        gross = float(sig * math.log(xp/ep) * 10000.0)
        rows.append({"symbol":symbol,"timeframe":timeframe,"signal_time":idx[signal_pos],"entry_time":entry_t,"exit_time":exit_t,"direction":sig,"entry_price":ep,"exit_price":xp,"signal_adx":float(h["adx"].iloc[signal_pos]),"signal_plus_di":float(h["plus_di"].iloc[signal_pos]),"signal_minus_di":float(h["minus_di"].iloc[signal_pos]),"gross_bps":gross,"net10_bps":gross-common.BASE_COST_BPS,"net14_bps":gross-common.STRESS_COST_BPS})
        active_until = exit_pos
    return pd.DataFrame(rows)


def run_phase(norm: Path, months: list[str], protected_start: pd.Timestamp, phase: str) -> tuple[pd.DataFrame,pd.DataFrame,list[dict]]:
    p1=[]; d4=[]; audits=[]
    for symbol in SYMBOLS:
        minute,audit = common.load_symbol(norm,symbol,months,protected_start); audits.append(audit.__dict__)
        t1 = make_trades(hourly_ohlc(minute,"1h"),symbol,"1h")
        t4 = make_trades(hourly_ohlc(minute,"4h"),symbol,"4h")
        p1.append(t1); d4.append(t4)
        print(f"{phase} {symbol}: 1H={len(t1):,} 4H_diagnostic={len(t4):,}",flush=True)
    one = pd.concat(p1,ignore_index=True) if p1 else pd.DataFrame(); four = pd.concat(d4,ignore_index=True) if d4 else pd.DataFrame()
    for t in (one,four):
        if len(t):
            for c in ("signal_time","entry_time","exit_time"): t[c]=pd.to_datetime(t[c],utc=True)
            t.sort_values(["entry_time","symbol"],inplace=True)
    return one,four,audits


def save(path: Path, obj: object) -> None:
    path.write_text(json.dumps(obj,indent=2,sort_keys=True,default=str)+"\n",encoding="utf-8")


def self_test() -> None:
    idx=pd.date_range("2022-01-01",periods=100,freq="1h",tz="UTC")
    x=np.arange(100,dtype=float)
    h=pd.DataFrame({"open":100+x,"high":101+x,"low":99+x,"close":100.5+x,"volume":1000.0,"minute_count":60,"bar_ok":True},index=idx)
    z=add_adx(h)
    assert abs(float(z["adx"].dropna().iloc[-1])-100.0) < 1e-9
    assert float(z["plus_di"].dropna().iloc[-1]) > float(z["minus_di"].dropna().iloc[-1])
    tr=make_trades(h,"TESTUSDT","1h")
    assert len(tr)>0 and (tr["direction"]==1).all()
    print(json.dumps({"self_test":"PASS","tail_adx":float(z["adx"].dropna().iloc[-1]),"trades":len(tr)},indent=2))


def main() -> None:
    import argparse
    ap=argparse.ArgumentParser(); ap.add_argument("--work",type=Path,required=True); args=ap.parse_args()
    work=args.work; norm=work/"normalized"; out=work/"outputs"; out.mkdir(parents=True,exist_ok=True)
    self_test()
    src=acquire_phase(norm,"DISCOVERY_2022_2023",DISCOVERY_YMS,append=False); save(out/f"{EXPERIMENT}_DISCOVERY_SOURCE_AUDIT.json",src)
    one,four,aud=run_phase(norm,common.DISCOVERY_MONTHS,common.VALIDATION_START,"DISCOVERY")
    one=common.split_trades(one,common.DISCOVERY_START,common.DISCOVERY_END); four=common.split_trades(four,common.DISCOVERY_START,common.DISCOVERY_END)
    m1=common.summarize(one); m4=common.summarize(four); gate=common.discovery_gate(m1)
    one.to_csv(out/f"{EXPERIMENT}_DISCOVERY_1H_TRADES.csv",index=False); four.to_csv(out/f"{EXPERIMENT}_DISCOVERY_4H_DIAGNOSTIC_TRADES.csv",index=False)
    save(out/f"{EXPERIMENT}_DISCOVERY_GATE.json",{"primary_1h":m1,"diagnostic_4h":m4,"gate":gate,"load_audits":aud,"four_hour_can_rescue":False})
    if not gate["pass"]:
        receipt={"lab":common.LAB,"experiment":EXPERIMENT,"status":"DISCOVERY_FAIL_NO_VALIDATION_ACCESS","frozen_rule":{"style":"Wilder","length":ADX_LENGTH,"threshold":ADX_THRESHOLD,"long":"ADX>=25 AND +DI>-DI","short":"ADX>=25 AND -DI>+DI","primary":"1H","robustness_only":"4H","entry":"next_bar_open","holding_bars":common.HOLD_BARS,"base_cost_bps":common.BASE_COST_BPS},"discovery":{"primary_1h":m1,"diagnostic_4h":m4,"gate":gate},"validation_2024_opened":False,"protected":{"2025":"UNOPENED","2026":"LOCKED_UNOPENED"},"source_authority":{"historical_h180_fingerprint":common.SOURCE_CANONICAL_FP,"discovery_raw_match":True}}
        save(out/f"{EXPERIMENT}_ACTION_RECEIPT.json",receipt); print(json.dumps({"status":receipt["status"],"gate":gate},indent=2)); return
    src24=acquire_phase(norm,"VALIDATION_2024",VALIDATION_YMS,append=True); save(out/f"{EXPERIMENT}_VALIDATION_2024_SOURCE_AUDIT.json",src24)
    v1,v4,vaud=run_phase(norm,common.VALIDATION_MONTHS,common.FORBIDDEN_START,"VALIDATION_2024")
    v1=common.split_trades(v1,common.VALIDATION_START,common.VALIDATION_END); v4=common.split_trades(v4,common.VALIDATION_START,common.VALIDATION_END)
    vm1=common.summarize(v1); vm4=common.summarize(v4); vgate=common.validation_gate(vm1)
    v1.to_csv(out/f"{EXPERIMENT}_VALIDATION_2024_1H_TRADES.csv",index=False); v4.to_csv(out/f"{EXPERIMENT}_VALIDATION_2024_4H_DIAGNOSTIC_TRADES.csv",index=False)
    status="MVE_1_REPLICATION_READY" if vgate["pass"] else "VALIDATION_FAIL_NO_EDGE_STOP"
    receipt={"lab":common.LAB,"experiment":EXPERIMENT,"status":status,"frozen_rule":{"style":"Wilder","length":ADX_LENGTH,"threshold":ADX_THRESHOLD,"long":"ADX>=25 AND +DI>-DI","short":"ADX>=25 AND -DI>+DI","primary":"1H","robustness_only":"4H","entry":"next_bar_open","holding_bars":common.HOLD_BARS,"base_cost_bps":common.BASE_COST_BPS},"discovery":{"primary_1h":m1,"diagnostic_4h":m4,"gate":gate},"validation_2024_opened":True,"validation_2024":{"primary_1h":vm1,"diagnostic_4h":vm4,"gate":vgate,"load_audits":vaud},"protected":{"2025":"UNOPENED","2026":"LOCKED_UNOPENED"},"source_authority":{"historical_h180_fingerprint":common.SOURCE_CANONICAL_FP,"discovery_raw_match":True,"validation_2024_raw_match":True}}
    save(out/f"{EXPERIMENT}_ACTION_RECEIPT.json",receipt); print(json.dumps({"status":status,"discovery_gate":gate,"validation_gate":vgate},indent=2))

if __name__=="__main__": main()
