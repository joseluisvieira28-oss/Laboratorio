#!/usr/bin/env python3
from pathlib import Path
import argparse, zipfile, pandas as pd
ASSETS=("BNBUSDT","DOGEUSDT","SOLUSDT","XRPUSDT")
CELLS=(("ST-01_DONCHIAN_BREAKOUT","BNBUSDT"),("ST-01_DONCHIAN_BREAKOUT","DOGEUSDT"),("ST-01_DONCHIAN_BREAKOUT","SOLUSDT"),("ST-01_DONCHIAN_BREAKOUT","XRPUSDT"),("ST-02_EMA_PULLBACK","SOLUSDT"),("ST-02_EMA_PULLBACK","DOGEUSDT"),("ST-03_EXTREME_MEAN_REVERSION","DOGEUSDT"))
MONTHS=("2024-12",)+tuple(f"2025-{m:02d}" for m in range(1,13))
LO=pd.Timestamp("2024-12-01T00:00:00Z"); HI=pd.Timestamp("2026-01-01T00:00:00Z")
def inspect_zip(p):
    if "2026" in str(p): raise RuntimeError("2026 FIREWALL VIOLATION")
    with zipfile.ZipFile(p) as z:
        csvs=[n for n in z.namelist() if n.lower().endswith('.csv') and not n.endswith('/')]
        if len(csvs)!=1: raise RuntimeError(f"{p}: expected one CSV")
        with z.open(csvs[0]) as f: d=pd.read_csv(f,header=None,usecols=[0],names=['t'],dtype=str)
    x=pd.to_numeric(d.t,errors='coerce').dropna(); med=float(x.median()); unit='us' if med>1e14 else ('ms' if med>1e11 else 's'); ts=pd.to_datetime(x.astype('int64'),unit=unit,utc=True)
    if ts.min()<LO or ts.max()>=HI: raise RuntimeError(f"{p}: timestamp outside V0.3 source window")
    return len(ts)
def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--source-root',required=True); ap.add_argument('--structure-only',action='store_true'); a=ap.parse_args(); assert len(CELLS)==7
    root=Path(a.source_root); expected=[root/s/f"{s}-1m-{m}.zip" for s in ASSETS for m in MONTHS]
    if a.structure_only: print('PREFLIGHT_CONTRACT_PASS: V0.3; 7 cells; 4 assets; 2024-12 warmup + 2025; 2026 forbidden'); return
    missing=[p for p in expected if not p.exists()]
    if missing: raise RuntimeError(f"SOURCE_GATE_FAIL: missing {len(missing)}/52; first={missing[0]}")
    total=sum(inspect_zip(p) for p in expected); print(f"SOURCE_PREFLIGHT_PASS: 52/52 archives; {total} timestamp rows; outcomes not computed; 2026 unopened")
if __name__=='__main__': main()
