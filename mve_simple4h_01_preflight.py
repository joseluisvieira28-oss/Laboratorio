#!/usr/bin/env python3
from pathlib import Path
import argparse, zipfile, pandas as pd

ASSETS=("BTCUSDT","ETHUSDT","SOLUSDT","BNBUSDT","XRPUSDT","DOGEUSDT")
CELLS=(
("ST-01_DONCHIAN_BREAKOUT","BNBUSDT"),("ST-01_DONCHIAN_BREAKOUT","DOGEUSDT"),
("ST-01_DONCHIAN_BREAKOUT","SOLUSDT"),("ST-01_DONCHIAN_BREAKOUT","XRPUSDT"),
("ST-02_EMA_PULLBACK","SOLUSDT"),("ST-02_EMA_PULLBACK","DOGEUSDT"),
("ST-03_EXTREME_MEAN_REVERSION","DOGEUSDT"))
MONTHS=tuple(f"2025-{m:02d}" for m in range(1,13))
START=pd.Timestamp("2025-01-01T00:00:00Z")
END=pd.Timestamp("2026-01-01T00:00:00Z")

def inspect_zip(p:Path):
    if "2026" in str(p): raise RuntimeError("2026 FIREWALL VIOLATION")
    with zipfile.ZipFile(p) as z:
        csvs=[n for n in z.namelist() if n.lower().endswith('.csv') and not n.endswith('/')]
        if len(csvs)!=1: raise RuntimeError(f"{p}: expected exactly one CSV")
        with z.open(csvs[0]) as f:
            d=pd.read_csv(f,header=None,usecols=[0],names=['open_time'],dtype=str)
    x=pd.to_numeric(d.open_time,errors='coerce').dropna()
    if x.empty: raise RuntimeError(f"{p}: no timestamps")
    med=float(x.median()); unit='us' if med>1e14 else ('ms' if med>1e11 else 's')
    ts=pd.to_datetime(x.astype('int64'),unit=unit,utc=True)
    if ts.min()<START or ts.max()>=END: raise RuntimeError(f"{p}: timestamp outside authorized 2025 cohort")
    return len(ts),str(ts.min()),str(ts.max())

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--source-root',required=True); ap.add_argument('--structure-only',action='store_true'); a=ap.parse_args()
    assert len(CELLS)==7 and len(set(CELLS))==7
    root=Path(a.source_root)
    expected=[root/s/f"{s}-1m-{m}.zip" for s in ASSETS for m in MONTHS]
    if a.structure_only:
        print('PREFLIGHT_CONTRACT_PASS: 7 cells; 6 assets; 12 months; 2025 only; no market bytes opened'); return
    missing=[str(p) for p in expected if not p.exists()]
    if missing: raise RuntimeError(f"SOURCE_GATE_FAIL: missing {len(missing)}/72 archives; first={missing[0]}")
    total=0
    for p in expected:
        n,lo,hi=inspect_zip(p); total+=n
    print(f"SOURCE_PREFLIGHT_PASS: 72/72 archives; {total} 1m rows inspected for timestamps only; 2026 unopened")

if __name__=='__main__': main()
