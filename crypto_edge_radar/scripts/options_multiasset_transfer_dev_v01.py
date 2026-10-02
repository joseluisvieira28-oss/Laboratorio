#!/usr/bin/env python3
"""Frozen 2024 Development evaluator for OPTIONS multi-asset transfer V0.1."""

from __future__ import annotations
import argparse,csv,datetime as dt,hashlib,io,json,math,statistics,time,urllib.error,urllib.request,zipfile
from pathlib import Path
from typing import Any

UTC=dt.timezone.utc
BASE_COST_BPS=10.0
STRESS_COST_BPS=20.0
RV_WINDOW=20
MIN_RV_HISTORY=60
SYMBOLS={"ETH":"ETHUSDT","SOL":"SOLUSDT","XRP":"XRPUSDT"}
EXPECTED_MONTHS={
 "ETH":[f"2024-{m:02d}" for m in range(1,13)],
 "SOL":[f"2024-{m:02d}" for m in range(3,13)],
 "XRP":[f"2024-{m:02d}" for m in range(3,13)],
}

def request_bytes(url:str)->bytes:
    req=urllib.request.Request(url,headers={"User-Agent":"CryptoLab-Options-MultiAsset-Dev/0.1"})
    last=None
    for n in range(1,6):
        try:
            with urllib.request.urlopen(req,timeout=90) as r:
                body=r.read()
            if not body: raise RuntimeError("empty body")
            return body
        except (urllib.error.URLError,urllib.error.HTTPError,TimeoutError,OSError,RuntimeError) as e:
            last=e
            if n<5: time.sleep(min(8.0,1.5*n))
    raise RuntimeError(f"price source fetch failed: {last}")

def month_iter(start:dt.date,end:dt.date):
    cur=dt.date(start.year,start.month,1)
    while cur<=end:
        yield cur.strftime("%Y-%m")
        cur=dt.date(cur.year+1,1,1) if cur.month==12 else dt.date(cur.year,cur.month+1,1)

def load_binance(asset:str):
    symbol=SYMBOLS[asset]; daily={}; manifest=[]
    for ym in month_iter(dt.date(2023,1,1),dt.date(2024,12,1)):
        url=f"https://data.binance.vision/data/spot/monthly/klines/{symbol}/1d/{symbol}-1d-{ym}.zip"
        body=request_bytes(url)
        manifest.append({"month":ym,"url":url,"sha256":hashlib.sha256(body).hexdigest(),"bytes":len(body)})
        with zipfile.ZipFile(io.BytesIO(body)) as zf:
            members=[n for n in zf.namelist() if not n.endswith("/")]
            if len(members)!=1: raise RuntimeError(f"unexpected ZIP members {ym}")
            with zf.open(members[0]) as raw:
                for row in csv.reader(io.TextIOWrapper(raw,encoding="utf-8",newline="")):
                    if not row: continue
                    try: raw_ts=int(row[0])
                    except Exception: continue
                    # Binance Vision spot timestamps are milliseconds historically; tolerate microseconds fail-safely.
                    sec=raw_ts/1_000_000.0 if raw_ts>100_000_000_000_000 else raw_ts/1000.0
                    day=dt.datetime.fromtimestamp(sec,tz=UTC).date()
                    op=float(row[1]); cl=float(row[4])
                    if not all(math.isfinite(v) and v>0 for v in (op,cl)):
                        raise RuntimeError(f"invalid OHLC {day}")
                    if day in daily: raise RuntimeError(f"duplicate price day {day}")
                    daily[day]={"open":op,"close":cl}
    days=sorted(daily)
    for i in range(1,len(days)):
        if (days[i]-days[i-1]).days!=1:
            raise RuntimeError(f"daily price continuity failure {days[i-1]}->{days[i]}")
    return daily,manifest

def rv20_series(prices):
    days=sorted(prices); rets=[]
    for i in range(1,len(days)):
        rets.append((days[i],math.log(prices[days[i]]["close"]/prices[days[i-1]]["close"])))
    out={}
    for i in range(RV_WINDOW-1,len(rets)):
        vals=[rets[j][1] for j in range(i-RV_WINDOW+1,i+1)]
        rv=statistics.stdev(vals)
        if not math.isfinite(rv) or rv<=0: raise RuntimeError(f"invalid RV20 {rets[i][0]}")
        out[rets[i][0]]=float(rv)
    return out

def weights(rv):
    out={}; hist=[]
    for d in sorted(rv):
        x=rv[d]; hist.append(x)
        if len(hist)<MIN_RV_HISTORY: continue
        med=float(statistics.median(hist)); w=min(1.0,med/x)
        if not math.isfinite(w) or not (0<w<=1): raise RuntimeError(f"invalid weight {d}")
        out[d]=w
    return out

def max_drawdown(net_bps):
    wealth=peak=1.0; mdd=0.0
    for x in net_bps:
        wealth*=math.exp(x/10000.0); peak=max(peak,wealth); mdd=min(mdd,wealth/peak-1.0)
    return mdd

def metrics(rows,cost_bps):
    entered=[r for r in rows if r["position"]!=0 and r["weight"]>0]
    gross=[r["aligned_unscaled_gross_bps"]*r["weight"] for r in entered]
    net=[g-cost_bps*r["weight"] for g,r in zip(gross,entered)]
    ws=[r["weight"] for r in entered]
    pos=sum(x for x in net if x>0); neg=-sum(x for x in net if x<0)
    pf=pos/neg if neg>0 else (float("inf") if pos>0 else 0.0)
    qs={}
    for q in range(1,5):
        rr=[r for r in entered if ((r["signal_date"].month-1)//3+1)==q]
        gv=[r["aligned_unscaled_gross_bps"]*r["weight"] for r in rr]
        nv=[g-cost_bps*r["weight"] for g,r in zip(gv,rr)]
        qs[f"Q{q}"]={"n":len(rr),"gross_pnl_bps":sum(gv),"net_pnl_bps":sum(nv),"net_mean_bps":sum(nv)/len(nv) if nv else None}
    positive={q:max(0.0,v["gross_pnl_bps"]) for q,v in qs.items()}
    total_positive=sum(positive.values())
    concentration=max(positive.values())/total_positive if total_positive>0 else 1.0
    return {
      "entered_scaled_trades":len(entered),
      "average_executed_notional":sum(ws)/len(ws) if ws else 0.0,
      "total_executed_notional_units":sum(ws),
      "long_count":sum(1 for r in entered if r["position"]>0),
      "short_count":sum(1 for r in entered if r["position"]<0),
      "gross_mean_bps_per_opportunity":sum(gross)/len(gross) if gross else None,
      "net_mean_bps_per_opportunity":sum(net)/len(net) if net else None,
      "profit_factor":pf,
      "cumulative_net_return":math.exp(sum(x/10000.0 for x in net))-1.0 if net else 0.0,
      "max_drawdown":max_drawdown(net),
      "win_rate":sum(1 for x in net if x>0)/len(net) if net else None,
      "quarters":qs,
      "single_quarter_max_share_of_total_positive_gross_pnl":concentration,
    }

def sanitize(x:Any)->Any:
    if isinstance(x,float) and not math.isfinite(x): return None
    if isinstance(x,dict): return {k:sanitize(v) for k,v in x.items()}
    if isinstance(x,list): return [sanitize(v) for v in x]
    return x

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--asset",required=True,choices=["ETH","SOL","XRP"])
    ap.add_argument("--signals-root",required=True)
    ap.add_argument("--repo-root",required=True)
    ap.add_argument("--out-dir",required=True)
    x=ap.parse_args(); asset=x.asset
    repo=Path(x.repo_root)
    freeze=json.loads((repo/"crypto_edge_radar/multiasset/OPTIONS_MULTI_ASSET_TRANSFER_PRE_OUTCOME_FREEZE_V0.1.json").read_text())
    if freeze.get("status")!="FROZEN_PRE_OUTCOME": raise RuntimeError("science freeze inactive")
    if freeze.get("assets")!=["ETH","SOL","XRP"]: raise RuntimeError("freeze asset identity drift")
    sg=json.loads((repo/"crypto_edge_radar/receipts/OPTIONS_MULTI_ASSET_SOURCE_GATE_CLOSEOUT_V0.1.json").read_text())
    if sg.get("hooks",{}).get(asset,{}).get("source_gate")!="PASS":
        raise RuntimeError("canonical source gate not PASS")

    root=Path(x.signals_root)
    source_receipts=[]; signal_rows=[]; observed_months=[]
    for month in EXPECTED_MONTHS[asset]:
        fs=list(root.rglob(f"{asset.lower()}_{month}_signal.json"))
        rs=list(root.rglob(f"{asset.lower()}_{month}_source_receipt.json"))
        if len(fs)!=1 or len(rs)!=1: raise RuntimeError(f"missing/duplicate source artifact {asset} {month}")
        rec=json.loads(rs[0].read_text())
        if rec.get("status")!="PASS" or rec.get("year_2026_accessed") is not False or rec.get("outcome_source_contacted") is not False:
            raise RuntimeError(f"source shard gate failed {asset} {month}")
        source_receipts.append(rec); observed_months.append(month)
        obj=json.loads(fs[0].read_text())
        for row in obj["signals"]:
            if row.get("valid"):
                signal_rows.append(row)

    if observed_months!=EXPECTED_MONTHS[asset]: raise RuntimeError("source month order mismatch")
    prices,price_manifest=load_binance(asset)
    rv=rv20_series(prices); w=weights(rv)
    rows=[]; unresolved=[]
    for s in sorted(signal_rows,key=lambda z:z["date"]):
        day=dt.date.fromisoformat(s["date"])
        if day.year!=2024: raise RuntimeError("non-2024 Development signal")
        e1=day+dt.timedelta(days=1); e2=day+dt.timedelta(days=2)
        if e1.year!=2024 or e2.year!=2024:
            unresolved.append({"signal_date":day.isoformat(),"reason":"WOULD_REQUIRE_2025_OUTCOME"})
            continue
        if e1 not in prices or e2 not in prices: raise RuntimeError(f"missing outcome price {day}")
        skew=float(s["skew"]); pos=1 if skew>0 else (-1 if skew<0 else 0)
        weight=float(w.get(day,0.0))
        fwd=math.log(prices[e2]["open"]/prices[e1]["open"])
        rows.append({"signal_date":day,"skew":skew,"position":pos,"forward_log_return":fwd,
                     "aligned_unscaled_gross_bps":pos*fwd*10000.0,"rv20":rv.get(day),"weight":weight})

    base=metrics(rows,BASE_COST_BPS); stress=metrics(rows,STRESS_COST_BPS)
    qualifying=[v for v in base["quarters"].values() if v["n"]>=10]
    nonneg=sum(1 for v in qualifying if v["net_mean_bps"] is not None and v["net_mean_bps"]>=0)
    gates={
      "A_provenance_source_leakage_pass":True,
      "B_entered_scaled_trades_ge_100":base["entered_scaled_trades"]>=100,
      "C_average_executed_notional_ge_0_40":base["average_executed_notional"]>=0.40,
      "D_base10_net_mean_positive":(base["net_mean_bps_per_opportunity"] if base["net_mean_bps_per_opportunity"] is not None else -1e99)>0,
      "E_base10_profit_factor_gt_1":base["profit_factor"]>1.0,
      "F_base10_cumulative_net_return_positive":base["cumulative_net_return"]>0,
      "G_three_qualifying_quarters_and_two_nonnegative":len(qualifying)>=3 and nonneg>=2,
      "H_single_quarter_positive_gross_share_lte_0_60":base["single_quarter_max_share_of_total_positive_gross_pnl"]<=0.60,
      "I_exact_identity_unchanged":True,
    }
    survives=all(gates.values())
    classification="DEV_SURVIVES__OOS_2025_UNLOCKED" if survives else "DEV_REJECTED_EXACT_TRANSFER__2025_REMAINS_LOCKED"
    result={
      "candidate_id":f"OPTIONS-{asset}-001-V0.1","asset":asset,"classification":classification,
      "development_year":2024,"source_months":observed_months,
      "source_valid_signal_days":len(signal_rows),"evaluable_signal_rows":len(rows),
      "unresolved_signals":unresolved,
      "source_audit_totals":{
        "target_rows":sum(int(r.get("target_rows",0)) for r in source_receipts),
        "eligible_rows":sum(int(r.get("eligible_rows",0)) for r in source_receipts),
        "invalid_iv":sum(int(r.get("invalid_iv",0)) for r in source_receipts),
        "invalid_index":sum(int(r.get("invalid_index",0)) for r in source_receipts),
        "parse_failures":sum(int(r.get("parse_failures",0)) for r in source_receipts),
        "duplicates":sum(int(r.get("duplicate_trade_ids",0)) for r in source_receipts),
      },
      "price_source":{"provider":"Binance Vision Spot monthly klines","symbol":SYMBOLS[asset],"archives":price_manifest},
      "base_10bps":base,"stress_20bps":stress,
      "qualifying_quarters_n":len(qualifying),"nonnegative_qualifying_quarters":nonneg,
      "gates":gates,
      "high_risk_fragility":base["max_drawdown"] < -0.50,
      "holdout_2025_accessed":False,"year_2026_accessed":False,
      "live_trading_authorized":False,"exchange_mutation_authorized":False,"main_merge_authorized":False,
      "no_post_outcome_rescue":True,
    }
    out=Path(x.out_dir); out.mkdir(parents=True,exist_ok=True)
    (out/f"OPTIONS_{asset}_001_V01_DEV_CLOSEOUT.json").write_text(json.dumps(sanitize(result),indent=2,sort_keys=True)+"\n")
    with (out/f"OPTIONS_{asset}_001_V01_DEV_LEDGER.csv").open("w",newline="",encoding="utf-8") as f:
        cw=csv.writer(f); cw.writerow(["signal_date","skew","position","forward_log_return","aligned_unscaled_gross_bps","rv20","weight"])
        for r in rows: cw.writerow([r["signal_date"].isoformat(),r["skew"],r["position"],r["forward_log_return"],r["aligned_unscaled_gross_bps"],r["rv20"],r["weight"]])
    print(json.dumps(sanitize({"asset":asset,"classification":classification,"base_10bps":base,"stress_20bps":stress,"gates":gates,"holdout_2025_accessed":False}),indent=2,sort_keys=True))
    return 0 if survives else 3

if __name__=="__main__": raise SystemExit(main())
