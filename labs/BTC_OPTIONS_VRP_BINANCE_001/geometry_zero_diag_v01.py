#!/usr/bin/env python3
from __future__ import annotations
import csv, io, json, re, urllib.request, zipfile
from collections import Counter

BASE="https://data.binance.vision/data/option/daily/EOHSummary/BTCUSDT/"
DATES=["2023-05-18","2023-07-01","2023-10-23"]
HOUR=8

def norm(x):
    return re.sub(r"[^a-z0-9]+","_",x.strip().strip("[]").lower()).strip("_")

def parse_hour(v):
    s=str(v).strip()
    try:
        f=float(s)
        if 0 <= f < 24: return int(f)
    except Exception:
        pass
    m=re.search(r"(\d{1,2})",s)
    return int(m.group(1)) if m and 0 <= int(m.group(1)) < 24 else None

def parse_expiry(sym):
    m=re.search(r"(?:^|-)(\d{6})(?:-|$)",sym)
    return bool(m)

def nonempty(v):
    return v is not None and str(v).strip() not in {"","nan","NaN","null","None"}

def run_date(ds):
    url=f"{BASE}BTCUSDT-EOHSummary-{ds}.zip"
    req=urllib.request.Request(url,headers={"User-Agent":"CryptoLab-SourceGeometry-Diagnostic/0.1"})
    with urllib.request.urlopen(req,timeout=45) as r: raw=r.read()
    with zipfile.ZipFile(io.BytesIO(raw)) as z:
        name=[n for n in z.namelist() if not n.endswith("/")][0]
        with z.open(name) as fh:
            reader=csv.DictReader(io.TextIOWrapper(fh,encoding="utf-8-sig",newline=""))
            by={norm(h):h for h in (reader.fieldnames or [])}
            counts=Counter()
            types=Counter()
            for row in reader:
                if parse_hour(row.get(by["hour"], "")) != HOUR: continue
                counts["rows_08utc"] += 1
                sym=str(row.get(by["symbol"], "")).strip()
                if not sym:
                    counts["reject_symbol_missing"] += 1; continue
                if not parse_expiry(sym):
                    counts["reject_expiry_parse"] += 1; continue
                typ=str(row.get(by["type"], "")).strip()
                types[typ] += 1
                if typ.upper() not in {"CALL","PUT","C","P"}:
                    counts["reject_unknown_type"] += 1; continue
                try: float(row.get(by["strike"], ""))
                except Exception:
                    counts["reject_strike_parse"] += 1; continue
                try: float(row.get(by["delta"], ""))
                except Exception:
                    counts["reject_delta_parse"] += 1; continue
                if not all(nonempty(row.get(by[k])) for k in ("best_bid_price","best_bid_qty","best_ask_price","best_ask_qty")):
                    counts["reject_incomplete_bbo"] += 1; continue
                counts["structurally_complete"] += 1
    return {"date":ds,"counts":dict(counts),"type_labels":dict(types),"prices_emitted":False}

out={"diagnostic_id":"BOVRP-BINANCE-GEOMETRY-ZERO-DIAG-001","dates":[run_date(d) for d in DATES],"outcomes_opened":False,"prices_emitted":False,"returns_computed":False,"vrp_computed":False,"pnl_computed":False}
open("binance_geometry_zero_diag_v01.json","w").write(json.dumps(out,indent=2,sort_keys=True)+"\n")
print(json.dumps(out,sort_keys=True))
