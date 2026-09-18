#!/usr/bin/env python3
"""CED1D AVAX20 V3 execution-feasibility audit V0.1.

Consumes the immutable 2025 one-shot event ledger and official Binance USD-M
AVAXUSDT monthly aggTrades. No 2026, no orders, no live API, no parameter tuning.
"""
from __future__ import annotations
import argparse,csv,hashlib,io,json,math,re,statistics,urllib.request,zipfile
from collections import defaultdict
from datetime import datetime,date,timedelta,timezone
from pathlib import Path

SYMBOL="AVAXUSDT"
TARGET="CED1D-0031"
YEAR=2025
BASE="https://data.binance.vision/data/futures/um/monthly/aggTrades"
UA="CED1D-AVAX20-V3-EXECUTION/0.1"
NOTIONAL=100.0
WINDOW_MS=5000
BASE_FEE_RT_BPS=8.0
STRESS_FEE_RT_BPS=10.0
FIRST_WEEK=date(2025,1,6)
END_WEEK_EXCL=date(2025,12,29)

class GateError(RuntimeError): pass

def sha256_bytes(b): return hashlib.sha256(b).hexdigest()
def canonical(o): return json.dumps(o,sort_keys=True,separators=(",",":"),ensure_ascii=True).encode()
def mean(xs): return math.fsum(xs)/len(xs) if xs else None

def percentile(xs,p):
    a=sorted(xs)
    if not a:return None
    q=(len(a)-1)*p; lo=math.floor(q); hi=math.ceil(q)
    return a[lo]+(a[hi]-a[lo])*(q-lo)

def week_start(d): return d-timedelta(days=d.weekday())
def complete_week(d): return FIRST_WEEK<=week_start(d)<END_WEEK_EXCL

def fetch(url):
    req=urllib.request.Request(url,headers={"User-Agent":UA})
    try:
        with urllib.request.urlopen(req,timeout=180) as r:
            if r.status!=200: raise GateError(f"HTTP_{r.status}:{url}")
            return r.read()
    except Exception as e:
        if isinstance(e,GateError): raise
        raise GateError(f"FETCH_FAIL:{type(e).__name__}:{e}:{url}") from e

def verified_zip(url):
    raw=fetch(url)
    check=fetch(url+".CHECKSUM").decode("utf-8",errors="replace")
    m=re.search(r"([0-9a-fA-F]{64})",check)
    if not m: raise GateError(f"CHECKSUM_PARSE:{url}")
    expected=m.group(1).lower(); actual=sha256_bytes(raw)
    if actual!=expected: raise GateError(f"CHECKSUM_MISMATCH:{url}:{actual}:{expected}")
    with zipfile.ZipFile(io.BytesIO(raw)) as z:
        bad=z.testzip()
        if bad is not None: raise GateError(f"ZIP_CRC_FAIL:{url}:{bad}")
        members=[n for n in z.namelist() if not n.endswith("/")]
        if len(members)!=1: raise GateError(f"ZIP_MEMBER_COUNT:{url}:{len(members)}")
    return raw,actual

def norm_ms(v):
    n=int(float(v))
    while n>10**14: n//=1000
    return n

def as_bool(s):
    v=str(s).strip().lower()
    if v in ("true","1"): return True
    if v in ("false","0"): return False
    raise GateError(f"BOOL_PARSE:{s}")

def load_events(ledger:Path):
    rows=[]
    with ledger.open("r",encoding="utf-8-sig",newline="") as f:
        for r in csv.DictReader(f):
            if r.get("combination_id")!=TARGET or r.get("status")!="TRADE": continue
            sd=date.fromisoformat(r["signal_day"])
            if not complete_week(sd): continue
            direction=int(float(r["direction"]))
            if direction not in (-1,1): raise GateError(f"DIRECTION:{r}")
            entry_day=r["entry_day"]; exit_day=r["exit_day"]
            ets=int(datetime.fromisoformat(entry_day).replace(tzinfo=timezone.utc).timestamp()*1000)+60000
            xts=int(datetime.fromisoformat(exit_day).replace(tzinfo=timezone.utc).timestamp()*1000)+60000
            if datetime.fromtimestamp(ets/1000,tz=timezone.utc).year!=2025 or datetime.fromtimestamp(xts/1000,tz=timezone.utc).year!=2025:
                raise GateError("EVENT_OUTSIDE_2025")
            rows.append({
                "event_id":f"{TARGET}:{r['signal_day']}",
                "signal_day":r["signal_day"],"entry_day":entry_day,"exit_day":exit_day,
                "direction":direction,"entry_ts_ms":ets,"exit_ts_ms":xts,
                "reference_gross_bps":float(r["gross_bps"]),
                "funding_lower_bps":float(r["funding_lower_bps"]),
            })
    rows.sort(key=lambda x:x["signal_day"])
    if len(rows)!=357: raise GateError(f"IMMUTABLE_EVENT_COUNT_NOT_357:{len(rows)}")
    if len({r["event_id"] for r in rows})!=357: raise GateError("DUP_EVENT_ID")
    return rows

def build_groups(events):
    groups={}
    def add(t,side,event_id,leg):
        k=(int(t),side)
        g=groups.setdefault(k,{"target_ts_ms":int(t),"side":side,"legs":[],"required_quote":0.0,
                               "filled_quote":0.0,"base_qty":0.0,"quote_value":0.0,
                               "last_fill_ts_ms":None,"vwap":None,"filled":False})
        g["legs"].append({"event_id":event_id,"leg":leg})
        g["required_quote"]+=NOTIONAL
    for e in events:
        add(e["entry_ts_ms"],"BUY" if e["direction"]==1 else "SELL",e["event_id"],"ENTRY")
        add(e["exit_ts_ms"],"SELL" if e["direction"]==1 else "BUY",e["event_id"],"EXIT")
    return groups

def consume_trade(groups,ts,price,qty,buyer_maker):
    # All frozen targets occur exactly at 00:01; the candidate group is the
    # same UTC day's 00:01 target.
    d=datetime.fromtimestamp(ts/1000,tz=timezone.utc)
    t=int(datetime(d.year,d.month,d.day,0,1,tzinfo=timezone.utc).timestamp()*1000)
    side="SELL" if buyer_maker else "BUY"
    g=groups.get((t,side))
    if g is None or g["filled"] or ts<t or ts>t+WINDOW_MS: return
    quote=price*qty
    need=g["required_quote"]-g["filled_quote"]
    if need<=0: return
    take=min(quote,need)
    take_qty=take/price
    g["quote_value"]+=take
    g["base_qty"]+=take_qty
    g["filled_quote"]+=take
    g["last_fill_ts_ms"]=ts
    if g["filled_quote"]+1e-9>=g["required_quote"]:
        g["filled"]=True
        g["vwap"]=g["quote_value"]/g["base_qty"]

def audit_month(raw,month,groups):
    with zipfile.ZipFile(io.BytesIO(raw)) as z:
        member=[n for n in z.namelist() if not n.endswith("/")][0]
        rdr=csv.reader(io.TextIOWrapper(z.open(member),encoding="utf-8-sig",newline=""))
        first=True; rows=0; prev_ts=None; prev_id=None; ids=set(); first_ts=last_ts=None
        y=YEAR; start=int(datetime(y,month,1,tzinfo=timezone.utc).timestamp()*1000)
        end=int(datetime(y+1,1,1,tzinfo=timezone.utc).timestamp()*1000) if month==12 else int(datetime(y,month+1,1,tzinfo=timezone.utc).timestamp()*1000)
        for r in rdr:
            if not r: continue
            if first:
                first=False
                try: int(float(r[0]))
                except Exception: continue
            if len(r)<7: raise GateError(f"AGGTRADE_SHORT_ROW:{month}:{r}")
            aid=int(float(r[0])); price=float(r[1]); qty=float(r[2]); ts=norm_ms(r[5]); bm=as_bool(r[6])
            if not(math.isfinite(price) and price>0 and math.isfinite(qty) and qty>0): raise GateError(f"AGGTRADE_NUMERIC:{month}:{r}")
            if not(start<=ts<end): raise GateError(f"AGGTRADE_MONTH_BOUNDS:{month}:{ts}")
            if prev_ts is not None and ts<prev_ts: raise GateError(f"AGGTRADE_TIME_REVERSED:{month}:{prev_ts}:{ts}")
            if prev_id is not None and aid<=prev_id: raise GateError(f"AGGTRADE_ID_NONASC:{month}:{prev_id}:{aid}")
            if aid in ids: raise GateError(f"AGGTRADE_DUP_ID:{month}:{aid}")
            ids.add(aid); prev_ts=ts; prev_id=aid; rows+=1
            first_ts=ts if first_ts is None else first_ts; last_ts=ts
            consume_trade(groups,ts,price,qty,bm)
    return {"month":f"2025-{month:02d}","rows":rows,"first_ts":first_ts,"last_ts":last_ts}

def pf(vals):
    gains=math.fsum(v for v in vals if v>0); losses=-math.fsum(v for v in vals if v<0)
    return gains/losses if losses>0 else None

def concentration(event_rows,field):
    vals=[float(x[field]) for x in event_rows]
    total=math.fsum(abs(v) for v in vals)
    if total<=0:return {"single_month":None,"top5":None,"single_day":None,"ratio":None}
    months=defaultdict(float); days=defaultdict(float)
    for r,v in zip(event_rows,vals):
        d=date.fromisoformat(r["entry_day"])
        months[d.strftime("%Y-%m")]+=abs(v); days[d.isoformat()]+=abs(v)
    m=max(months.values())/total; d=max(days.values())/total
    t=math.fsum(sorted((abs(v) for v in vals),reverse=True)[:5])/total
    return {"single_month":m,"top5":t,"single_day":d,"ratio":max(m/.30,t/.20,d/.10)}

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--ledger",required=True)
    ap.add_argument("--output",required=True)
    a=ap.parse_args(); out=Path(a.output)
    if out.exists(): raise SystemExit("OUTPUT_EXISTS")
    out.mkdir(parents=True)
    events=load_events(Path(a.ledger)); groups=build_groups(events)

    source=[]
    for m in range(1,13):
        name=f"{SYMBOL}-aggTrades-2025-{m:02d}.zip"; url=f"{BASE}/{SYMBOL}/{name}"
        raw,h=verified_zip(url)
        meta=audit_month(raw,m,groups); meta.update(file=name,sha256=h,url=url); source.append(meta)
        print(f"[{m:02d}/12] {name} PASS rows={meta['rows']}",flush=True)

    leg_lookup={}
    for g in groups.values():
        lat=(g["last_fill_ts_ms"]-g["target_ts_ms"]) if g["filled"] else None
        for leg in g["legs"]:
            leg_lookup[(leg["event_id"],leg["leg"])]={
                "filled":bool(g["filled"]),"vwap":g["vwap"],"latency_ms":lat,
                "side":g["side"],"required_group_quote":g["required_quote"],
                "filled_group_quote":g["filled_quote"],"target_ts_ms":g["target_ts_ms"]
            }

    erows=[]; leg_rows=[]
    for e in events:
        en=leg_lookup[(e["event_id"],"ENTRY")]; ex=leg_lookup[(e["event_id"],"EXIT")]
        for typ,x in (("ENTRY",en),("EXIT",ex)):
            leg_rows.append({"event_id":e["event_id"],"leg":typ,**x})
        complete=en["filled"] and ex["filled"]
        r={**e,"entry_filled":en["filled"],"exit_filled":ex["filled"],"complete_pair":complete,
           "entry_vwap":en["vwap"],"exit_vwap":ex["vwap"],"entry_latency_ms":en["latency_ms"],"exit_latency_ms":ex["latency_ms"]}
        if complete:
            exec_gross=e["direction"]*(float(ex["vwap"])/float(en["vwap"])-1.0)*10000
            drag=e["reference_gross_bps"]-exec_gross
            r.update(execution_gross_bps=exec_gross,execution_drag_bps=drag,
                     total_nonfunding_base_proxy_bps=BASE_FEE_RT_BPS+drag,
                     base_executable_funded_bps=exec_gross-BASE_FEE_RT_BPS+e["funding_lower_bps"],
                     stress_executable_funded_bps=exec_gross-STRESS_FEE_RT_BPS+e["funding_lower_bps"])
        erows.append(r)

    filled_legs=[x for x in leg_rows if x["filled"]]
    complete=[x for x in erows if x["complete_pair"]]
    lat=[float(x["latency_ms"]) for x in filled_legs]
    costs=[float(x["total_nonfunding_base_proxy_bps"]) for x in complete]
    basevals=[float(x["base_executable_funded_bps"]) for x in complete]
    stressvals=[float(x["stress_executable_funded_bps"]) for x in complete]
    conc=concentration(complete,"base_executable_funded_bps") if complete else {"ratio":None}

    metrics={
      "events_required":357,"legs_required":714,
      "legs_filled":len(filled_legs),"leg_fill_rate":len(filled_legs)/714,
      "events_complete":len(complete),"event_complete_rate":len(complete)/357,
      "median_leg_latency_ms":statistics.median(lat) if lat else None,
      "p95_leg_latency_ms":percentile(lat,.95) if lat else None,
      "mean_total_nonfunding_base_proxy_bps":mean(costs),
      "p95_total_nonfunding_base_proxy_bps":percentile(costs,.95) if costs else None,
      "mean_base_executable_funded_bps":mean(basevals),
      "pf_base_executable_funded":pf(basevals),
      "mean_stress_executable_funded_bps":mean(stressvals),
      "pf_stress_executable_funded":pf(stressvals),
      "concentration":conc
    }
    gates={
      "leg_fill_rate_ge_099":metrics["leg_fill_rate"]>=.99,
      "event_complete_rate_ge_099":metrics["event_complete_rate"]>=.99,
      "median_latency_le_1000ms":metrics["median_leg_latency_ms"] is not None and metrics["median_leg_latency_ms"]<=1000,
      "p95_latency_le_5000ms":metrics["p95_leg_latency_ms"] is not None and metrics["p95_leg_latency_ms"]<=5000,
      "mean_nonfunding_cost_le_14":metrics["mean_total_nonfunding_base_proxy_bps"] is not None and metrics["mean_total_nonfunding_base_proxy_bps"]<=14,
      "p95_nonfunding_cost_le_20":metrics["p95_total_nonfunding_base_proxy_bps"] is not None and metrics["p95_total_nonfunding_base_proxy_bps"]<=20,
      "base_mean_gt_0":metrics["mean_base_executable_funded_bps"] is not None and metrics["mean_base_executable_funded_bps"]>0,
      "base_pf_gt_1":metrics["pf_base_executable_funded"] is not None and metrics["pf_base_executable_funded"]>1,
      "stress_mean_ge_0":metrics["mean_stress_executable_funded_bps"] is not None and metrics["mean_stress_executable_funded_bps"]>=0,
      "concentration_pass":conc.get("ratio") is not None and conc["ratio"]<=1,
    }
    verdict="EXECUTION_FEASIBILITY_PASS" if all(gates.values()) else "EXECUTION_FEASIBILITY_FAIL"

    def write_csv(name,rows):
        if not rows:return
        fields=sorted({k for r in rows for k in r})
        with (out/name).open("w",encoding="utf-8",newline="") as f:
            w=csv.DictWriter(f,fieldnames=fields,lineterminator="\n"); w.writeheader(); w.writerows(rows)
    write_csv("AVAX20_EXECUTION_LEGS.csv",leg_rows)
    write_csv("AVAX20_EXECUTION_EVENTS.csv",erows)

    receipt={"document_id":"CED_1D_AVAX20_V3_EXECUTION_FEASIBILITY_RECEIPT_V0.1",
             "status":verdict,"candidate":TARGET,"notional_per_leg_usdt":NOTIONAL,
             "window_ms":WINDOW_MS,"base_fee_roundtrip_bps":BASE_FEE_RT_BPS,
             "stress_fee_roundtrip_bps":STRESS_FEE_RT_BPS,
             "source":source,"metrics":metrics,"gates":gates,
             "governance":{"year_2026_accessed":False,"live_trading":False,"orders":False,
                           "exchange_mutation":False,"maker_assumption":False,
                           "signal_changed":False,"events_changed":False}}
    receipt["fingerprint"]=sha256_bytes(canonical(receipt))
    (out/"CED_1D_AVAX20_V3_EXECUTION_FEASIBILITY_RECEIPT_V0.1.json").write_text(json.dumps(receipt,indent=2,sort_keys=True)+"\n")
    print(json.dumps({"status":verdict,"metrics":metrics,"gates":gates,"fingerprint":receipt["fingerprint"]},indent=2,sort_keys=True))

if __name__=="__main__": main()
