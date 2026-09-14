#!/usr/bin/env python3
"""ETF-SHORTFLOW-001 / ESF-IBIT-SHORTVOL-5D-001 one-shot 2024 Discovery.

Scientific design is frozen in PRE_DISCOVERY_PROTOCOL_V0.1.md. This runner fails
closed before BTC source access unless the frozen protocol and regenerated FINRA
Source/Data Gate match the parent authority. It never requests 2025 or 2026 data.
"""
from __future__ import annotations

import csv, hashlib, io, json, math, os, subprocess, sys, urllib.request, zipfile
from collections import defaultdict
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

LAB_ID = "ETF-SHORTFLOW-001"
MVE_ID = "ESF-IBIT-SHORTVOL-5D-001"
EXPECTED_PROTOCOL_SHA256 = "5adde8f691ac762752547437d225a7ce90ac11ce1c9e34b96ea8d93f5adecb5c"
EXPECTED_PARENT_IBIT_ROWS_SHA256 = "8ad8797f43347038c4f39f3f99d8bd95c6576e412055c6f4fb329ab31a960f13"
PROTOCOL = Path("labs/ETF_SHORTFLOW_001/PRE_DISCOVERY_PROTOCOL_V0.1.md")
AUTHORITY = Path("labs/ETF_SHORTFLOW_001/DISCOVERY_AUTHORIZATION_V0.1.md")
SOURCE_DIR = Path("artifacts/etf_shortflow_source_gate_v01")
SOURCE_RECEIPT = SOURCE_DIR / "SOURCE_GATE_RECEIPT.json"
SOURCE_ROWS = SOURCE_DIR / "FINRA_IBIT_SOURCE_ROWS_2024.csv"
OUT = Path("artifacts/etf_shortflow_discovery_v01")
BINANCE_TMPL = "https://data.binance.vision/data/spot/monthly/klines/BTCUSDT/1d/BTCUSDT-1d-2024-{month:02d}.zip"
BASE_COST = 0.0010
STRESS_COST = 0.0020
HAC_LAG = 5


def sha256_bytes(b: bytes) -> str: return hashlib.sha256(b).hexdigest()
def sha256_file(p: Path) -> str: return sha256_bytes(p.read_bytes())
def git_head() -> str | None:
    try: return subprocess.check_output(["git","rev-parse","HEAD"], text=True).strip()
    except Exception: return os.environ.get("GITHUB_SHA")

def fetch(url: str) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent":"Mozilla/5.0 ETF-SHORTFLOW-001 research-only Discovery"})
    with urllib.request.urlopen(req, timeout=60) as r:
        if r.status != 200: raise RuntimeError(f"HTTP_{r.status}:{url}")
        return r.read()

def normal_cdf(z: float) -> float:
    return 0.5 * (1.0 + math.erf(z / math.sqrt(2.0)))

def inv2(a,b,c,d):
    det=a*d-b*c
    if abs(det) < 1e-18: raise RuntimeError("SINGULAR_XTX")
    return d/det, -b/det, -c/det, a/det

def ols_hac(xs: list[float], ys: list[float], lag: int=5) -> dict:
    n=len(xs)
    if n < 3: raise RuntimeError("REGRESSION_TOO_SMALL")
    sx=sum(xs); sy=sum(ys); sxx=sum(x*x for x in xs); sxy=sum(x*y for x,y in zip(xs,ys))
    den=n*sxx-sx*sx
    if abs(den) < 1e-18: raise RuntimeError("ZERO_SIGNAL_VARIANCE")
    beta=(n*sxy-sx*sy)/den
    alpha=(sy-beta*sx)/n
    u=[y-alpha-beta*x for x,y in zip(xs,ys)]
    # X'X inverse, X=[1,x]
    i00,i01,i10,i11=inv2(float(n),sx,sx,sxx)
    S00=S01=S10=S11=0.0
    for t in range(n):
        ut=u[t]; xt=xs[t]; q=ut*ut
        S00+=q; S01+=q*xt; S10+=q*xt; S11+=q*xt*xt
    for L in range(1, lag+1):
        w=1.0-L/(lag+1.0)
        for t in range(L,n):
            q=w*u[t]*u[t-L]; xt=xs[t]; xl=xs[t-L]
            S00 += 2*q
            S01 += q*(xt+xl)
            S10 += q*(xt+xl)
            S11 += 2*q*xt*xl
    # V = inv(X'X) S inv(X'X)
    a00=i00*S00+i01*S10; a01=i00*S01+i01*S11
    a10=i10*S00+i11*S10; a11=i10*S01+i11*S11
    v11=a10*i01+a11*i11
    se=math.sqrt(max(v11,0.0))
    z=beta/se if se>0 else (-math.inf if beta<0 else math.inf)
    p_left=normal_cdf(z)
    return {"n":n,"alpha":alpha,"beta":beta,"hac_se_beta":se,"z_beta":z,"one_sided_p_beta_lt_0":p_left}

def profit_factor(rs: list[float]) -> float:
    pos=sum(r for r in rs if r>0); neg=-sum(r for r in rs if r<0)
    return math.inf if neg==0 and pos>0 else (pos/neg if neg>0 else 0.0)

def summarize(events: list[dict]) -> dict:
    xs=[e["signal"] for e in events]; ys=[e["r5"] for e in events]
    reg=ols_hac(xs,ys,HAC_LAG)
    gross=[e["strategy_gross"] for e in events]
    net10=[e["strategy_net10"] for e in events]
    net20=[e["strategy_net20"] for e in events]
    reg.update({
        "mean_strategy_gross": sum(gross)/len(gross),
        "mean_net10": sum(net10)/len(net10),
        "mean_net20": sum(net20)/len(net20),
        "pf_net10": profit_factor(net10),
        "pf_net20": profit_factor(net20),
        "win_rate_net10": sum(r>0 for r in net10)/len(net10),
    })
    return reg

def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    # Hard guards before BTC source access.
    if not PROTOCOL.exists() or sha256_file(PROTOCOL) != EXPECTED_PROTOCOL_SHA256:
        raise RuntimeError("FROZEN_PROTOCOL_SHA256_MISMATCH_PREOUTCOME")
    if not AUTHORITY.exists() or "AUTHORIZED FOR EXACTLY ONE 2024 DISCOVERY EXECUTION" not in AUTHORITY.read_text(encoding="utf-8"):
        raise RuntimeError("DISCOVERY_AUTHORITY_MISSING_PREOUTCOME")
    if not SOURCE_RECEIPT.exists() or not SOURCE_ROWS.exists():
        raise RuntimeError("REGENERATED_SOURCE_GATE_OUTPUT_MISSING_PREOUTCOME")
    src=json.loads(SOURCE_RECEIPT.read_text(encoding="utf-8"))
    if src.get("classification") != "SOURCE_DATA_PASS": raise RuntimeError("SOURCE_GATE_NOT_PASS_PREOUTCOME")
    if src.get("access_2025") or src.get("access_2026") or src.get("btc_market_data_accessed"):
        raise RuntimeError("SOURCE_GATE_FIREWALL_BREACH_PREOUTCOME")
    if src.get("valid_source_files") != 245 or src.get("ibit_rows") != 245:
        raise RuntimeError("SOURCE_GATE_COVERAGE_CHANGED_PREOUTCOME")
    if src.get("ibit_rows_sha256") != sha256_file(SOURCE_ROWS):
        raise RuntimeError("SOURCE_ROWS_RECEIPT_HASH_MISMATCH_PREOUTCOME")
    # Re-generated bytes must match the canonical parent parsed-row dataset exactly.
    if sha256_file(SOURCE_ROWS) != EXPECTED_PARENT_IBIT_ROWS_SHA256:
        raise RuntimeError("SOURCE_ROWS_PARENT_HASH_MISMATCH_PREOUTCOME")

    # Source signal computation only after all source guards pass.
    rows=[]
    with SOURCE_ROWS.open("r",encoding="utf-8",newline="") as f:
        for r in csv.DictReader(f):
            d=datetime.strptime(r["Date"],"%Y%m%d").date()
            if d.year != 2024: raise RuntimeError("PROTECTED_PERIOD_FINRA_ROW")
            short=float(r["ShortVolume"]); total=float(r["TotalVolume"])
            rows.append({"trade_date":d,"short_share":short/total})
    rows.sort(key=lambda z:z["trade_date"])
    signal_rows=[]
    for i in range(20,len(rows)):
        baseline=sum(rows[j]["short_share"] for j in range(i-20,i))/20.0
        signal=rows[i]["short_share"]-baseline
        entry=rows[i]["trade_date"]+timedelta(days=1)
        exitd=entry+timedelta(days=5)
        if exitd.year > 2024: continue  # protected-period exclusion before BTC outcome lookup
        signal_rows.append({"trade_date":rows[i]["trade_date"],"short_share":rows[i]["short_share"],"baseline20":baseline,"signal":signal,"entry_date":entry,"exit_date":exitd})

    # Only now may 2024 BTC source be opened. Exactly 12 monthly archives, never 2025/2026.
    opens={}; btc_manifest=[]
    for month in range(1,13):
        url=BINANCE_TMPL.format(month=month)
        raw=fetch(url)
        ent={"month":f"2024-{month:02d}","url":url,"bytes":len(raw),"sha256":sha256_bytes(raw)}
        with zipfile.ZipFile(io.BytesIO(raw)) as zf:
            names=zf.namelist()
            if len(names)!=1: raise RuntimeError(f"BINANCE_ZIP_MEMBER_COUNT_{month}")
            payload=zf.read(names[0]).decode("utf-8")
            for rec in csv.reader(io.StringIO(payload)):
                if not rec: continue
                ts=int(rec[0]); dt=datetime.fromtimestamp(ts/1000,tz=timezone.utc)
                if dt.year != 2024: raise RuntimeError("PROTECTED_PERIOD_BINANCE_ROW")
                if dt.hour!=0 or dt.minute!=0: raise RuntimeError("BINANCE_DAILY_OPEN_NOT_0000")
                opens[dt.date()]=float(rec[1])
        btc_manifest.append(ent)
    if len(opens) not in (365,366):
        raise RuntimeError(f"BINANCE_2024_DAILY_COVERAGE:{len(opens)}")

    events=[]
    for s in signal_rows:
        if s["entry_date"] not in opens or s["exit_date"] not in opens:
            raise RuntimeError(f"MISSING_BTC_OPEN:{s['trade_date']}")
        entry=opens[s["entry_date"]]; exitp=opens[s["exit_date"]]; r5=exitp/entry-1.0
        sig=s["signal"]
        side=-1 if sig>0 else (1 if sig<0 else 0)
        gross=side*r5
        net10=gross-(BASE_COST if side else 0.0)
        net20=gross-(STRESS_COST if side else 0.0)
        e=dict(s); e.update({"entry_price":entry,"exit_price":exitp,"r5":r5,"side":side,"strategy_gross":gross,"strategy_net10":net10,"strategy_net20":net20})
        events.append(e)

    primary=summarize(events)
    # Quarter gate (signal trade date).
    q_net=defaultdict(float)
    m_gross=defaultdict(float)
    for e in events:
        q=(e["trade_date"].month-1)//3+1
        q_net[f"2024-Q{q}"] += e["strategy_net10"]
        m_gross[e["trade_date"].strftime("%Y-%m")] += e["strategy_gross"]
    nonneg_quarters=sum(v>=0 for v in q_net.values())
    positive_months={m:v for m,v in m_gross.items() if v>0}
    total_positive_month_gross=sum(positive_months.values())
    max_month_share=(max(positive_months.values())/total_positive_month_gross) if total_positive_month_gross>0 else math.inf

    gates={
        "n_ge_180": primary["n"]>=180,
        "beta_lt_0": primary["beta"]<0,
        "p_le_0_05": primary["one_sided_p_beta_lt_0"]<=0.05,
        "mean_net10_gt_0": primary["mean_net10"]>0,
        "pf_net10_gt_1": primary["pf_net10"]>1.0,
        "quarters_nonnegative_ge_3_of_4": len(q_net)==4 and nonneg_quarters>=3,
        "max_positive_month_gross_share_le_0_35": max_month_share<=0.35,
    }
    passed=all(gates.values())
    classification="DISCOVERY_MVE0_PASS" if passed else "DISCOVERY_FAIL_NO_PROMOTION"

    # Leave-one-signal-month-out diagnostics, frozen diagnostic only.
    months=sorted({e["trade_date"].strftime("%Y-%m") for e in events})
    lomo=[]
    for m in months:
        sub=[e for e in events if e["trade_date"].strftime("%Y-%m")!=m]
        sm=summarize(sub); sm["omitted_month"]=m; lomo.append(sm)

    # Persist evidence.
    with (OUT/"BTC_SOURCE_MANIFEST_2024.json").open("w",encoding="utf-8") as f: json.dump(btc_manifest,f,indent=2,sort_keys=True)
    with (OUT/"EVENT_LEVEL_2024.csv").open("w",encoding="utf-8",newline="") as f:
        fields=["trade_date","short_share","baseline20","signal","entry_date","exit_date","entry_price","exit_price","r5","side","strategy_gross","strategy_net10","strategy_net20"]
        w=csv.DictWriter(f,fieldnames=fields); w.writeheader()
        for e in events:
            rr={k:(v.isoformat() if isinstance(v,date) else v) for k,v in e.items() if k in fields}; w.writerow(rr)
    with (OUT/"LOMO_DIAGNOSTICS.json").open("w",encoding="utf-8") as f: json.dump(lomo,f,indent=2,sort_keys=True,allow_nan=True)

    receipt={
        "lab_id":LAB_ID,"mve_id":MVE_ID,"classification":classification,"git_head":git_head(),
        "frozen_protocol_sha256":sha256_file(PROTOCOL),"source_gate_classification":src["classification"],
        "source_rows_sha256":sha256_file(SOURCE_ROWS),"btc_source_months":12,"btc_daily_rows":len(opens),
        "access_2025":False,"access_2026":False,"live_trading":False,"exchange_mutation":False,
        "evaluable_events":len(events),"primary":primary,"quarter_net10":dict(sorted(q_net.items())),
        "nonnegative_quarters":nonneg_quarters,"monthly_gross":dict(sorted(m_gross.items())),
        "max_positive_month_gross_share":max_month_share,"promotion_gates":gates,
        "all_promotion_gates_pass":passed,
    }
    (OUT/"DISCOVERY_RECEIPT.json").write_text(json.dumps(receipt,indent=2,sort_keys=True,allow_nan=True)+"\n",encoding="utf-8")
    hashes={p.name:sha256_file(p) for p in sorted(OUT.iterdir()) if p.is_file()}
    (OUT/"OUTPUT_SHA256.json").write_text(json.dumps(hashes,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    print(json.dumps(receipt,indent=2,sort_keys=True,allow_nan=True))
    return 0

if __name__=="__main__": sys.exit(main())
