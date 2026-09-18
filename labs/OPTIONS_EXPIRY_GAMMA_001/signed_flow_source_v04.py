#!/usr/bin/env python3
import csv,gzip,hashlib,io,json,math,sys
from datetime import datetime,timezone
from pathlib import Path
import requests

ROOT=Path("labs/OPTIONS_EXPIRY_GAMMA_001")
AUTH=json.loads((ROOT/"SIGNED_FLOW_SOURCE_AUTHORITY_V0.4.json").read_text())
OUT=Path("artifacts/options_expiry_gamma_signed_flow_source_v04");OUT.mkdir(parents=True,exist_ok=True)
S=requests.Session();S.headers.update({"User-Agent":"SRC-Crypto-Lab-OEG-SignedFlow/0.4","Accept":"application/gzip"})

def num(v):
    if v is None:return None
    try:
        x=float(str(v).strip())
        return x if math.isfinite(x) else None
    except Exception:return None

def integer(v):
    x=num(v);return None if x is None else int(x)

def us(day,t):
    return int(datetime.fromisoformat(day+"T"+t+"+00:00").timestamp()*1_000_000)

def stream_csv(url):
    r=S.get(url,stream=True,timeout=120)
    raw_hash=hashlib.sha256()
    if r.status_code!=200:
        return r,None,raw_hash
    class H(io.RawIOBase):
        def __init__(self,raw):self.raw=raw
        def readable(self):return True
        def readinto(self,b):
            n=self.raw.readinto(b)
            if n:raw_hash.update(memoryview(b)[:n])
            return n
    txt=io.TextIOWrapper(gzip.GzipFile(fileobj=io.BufferedReader(H(r.raw))),encoding="utf-8",newline="")
    return r,csv.DictReader(txt),raw_hash

def probe(day):
    y,m,d=day.split("-")
    turl=f"https://datasets.tardis.dev/v1/deribit/trades/{y}/{m}/{d}/OPTIONS.csv.gz"
    curl=f"https://datasets.tardis.dev/v1/deribit/options_chain/{y}/{m}/{d}/OPTIONS.csv.gz"
    start=us(day,AUTH["window"]["start_time_utc"])
    target=us(day,AUTH["window"]["target_time_utc"])
    stop=us(day,AUTH["window"]["stop_after_utc"])

    tr,trd,th=stream_csv(turl)
    if tr.status_code!=200 or trd is None:
        return {"date":day,"pass":False,"technical_error":f"trades HTTP {tr.status_code}"}
    trades=0;syms=set();side_ok=price_ok=amt_ok=0
    for row in trd:
        ts=integer(row.get("timestamp"))
        if ts is None:continue
        if ts>stop:break
        if ts<start or ts>target:continue
        sym=(row.get("symbol") or "").strip().upper()
        if not sym.startswith("BTC-"):continue
        trades+=1;syms.add(sym)
        if (row.get("side") or "").strip().lower() in ("buy","sell"):side_ok+=1
        if num(row.get("price")) is not None:price_ok+=1
        if num(row.get("amount")) is not None:amt_ok+=1
    tr.close()

    cr,ch,hh=stream_csv(curl)
    if cr.status_code!=200 or ch is None:
        return {"date":day,"pass":False,"technical_error":f"chain HTTP {cr.status_code}"}
    earliest={};latest={};target_latest={}
    for row in ch:
        ts=integer(row.get("timestamp"))
        if ts is None:continue
        if ts>stop:break
        if ts<start:continue
        sym=(row.get("symbol") or "").strip().upper()
        if not sym.startswith("BTC-"):continue
        oi=num(row.get("open_interest"));ga=num(row.get("gamma"))
        if ts<=target:
            if sym not in earliest or ts<earliest[sym][0]:earliest[sym]=(ts,oi,ga)
            if sym not in latest or ts>latest[sym][0]:latest[sym]=(ts,oi,ga)
            if sym not in target_latest or ts>target_latest[sym][0]:target_latest[sym]=(ts,oi,ga)
    cr.close()

    n=max(1,trades)
    target_n=len(target_latest)
    matched=syms & set(target_latest)
    changed=0
    for s in matched:
        a=earliest.get(s);b=latest.get(s)
        if a and b and a[1] is not None and b[1] is not None and b[1]!=a[1]:
            changed+=1
    g=AUTH["per_date_gates"]
    metrics={
      "btc_option_trades":trades,
      "distinct_trade_symbols":len(syms),
      "trade_side_coverage":side_ok/n,
      "trade_price_coverage":price_ok/n,
      "trade_amount_coverage":amt_ok/n,
      "target_chain_instruments":target_n,
      "target_chain_open_interest_coverage":sum(1 for _,oi,_ in target_latest.values() if oi is not None)/max(1,target_n),
      "target_chain_gamma_coverage":sum(1 for _,_,ga in target_latest.values() if ga is not None)/max(1,target_n),
      "trade_symbol_chain_match_coverage":len(matched)/max(1,len(syms)),
      "matched_symbols_with_nonzero_oi_change":changed
    }
    checks={
      "trades":trades>=g["minimum_btc_option_trades"],
      "symbols":len(syms)>=g["minimum_distinct_trade_symbols"],
      "side":metrics["trade_side_coverage"]>=g["trade_side_coverage_minimum"],
      "price":metrics["trade_price_coverage"]>=g["trade_price_coverage_minimum"],
      "amount":metrics["trade_amount_coverage"]>=g["trade_amount_coverage_minimum"],
      "match":metrics["trade_symbol_chain_match_coverage"]>=g["trade_symbol_chain_match_coverage_minimum"],
      "oi":metrics["target_chain_open_interest_coverage"]>=g["target_chain_open_interest_coverage_minimum"],
      "gamma":metrics["target_chain_gamma_coverage"]>=g["target_chain_gamma_coverage_minimum"],
      "oi_changes":changed>=g["minimum_matched_symbols_with_nonzero_oi_change"]
    }
    return {"date":day,"trades_http":tr.status_code,"chain_http":cr.status_code,
      "trades_sha256":th.hexdigest(),"chain_sha256":hh.hexdigest(),"metrics":metrics,"gate_checks":checks,"pass":all(checks.values())}

def main():
    probes=[]
    for i,d in enumerate(AUTH["deterministic_probe_dates"],1):
        try:p=probe(d)
        except Exception as e:p={"date":d,"pass":False,"technical_error":repr(e)}
        probes.append(p);print(f"SIGNED_FLOW_SOURCE_PROGRESS {i}/{len(AUTH['deterministic_probe_dates'])} {d} pass={p.get('pass')}",flush=True)
    tech=any(p.get("technical_error") for p in probes)
    if tech:cls=AUTH["classifications"]["technical_failure"]
    elif all(p.get("pass") for p in probes):cls=AUTH["classifications"]["pass"]
    else:cls=AUTH["classifications"]["insufficient"]
    result={"lab_id":AUTH["lab_id"],"source_gate_id":AUTH["source_gate_id"],"classification":cls,"probes":probes,
      "api_key_used":False,"subscription_purchase":False,"option_values_retained":False,"gamma_exposure_computed":False,
      "dealer_inventory_computed":False,"dealer_gamma_sign_computed":False,"btc_price_outcomes_opened":False,
      "returns_opened":False,"pnl_opened":False,"access_2025":False,"access_2026":False,"live_trading":False,
      "exchange_mutation":False,"wallet_access":False,"merge_to_main":False}
    p=OUT/"source_result.json";p.write_text(json.dumps(result,indent=2,sort_keys=True)+"\n")
    (OUT/"manifest.json").write_text(json.dumps({"authority_sha256":hashlib.sha256((ROOT/"SIGNED_FLOW_SOURCE_AUTHORITY_V0.4.json").read_bytes()).hexdigest(),
      "result_sha256":hashlib.sha256(p.read_bytes()).hexdigest()},indent=2,sort_keys=True)+"\n")
    print(json.dumps({"classification":cls,"dates":[{"date":x["date"],"pass":x.get("pass"),"metrics":x.get("metrics")} for x in probes]},indent=2,sort_keys=True))
    return 0 if cls!=AUTH["classifications"]["technical_failure"] else 2

if __name__=="__main__":sys.exit(main())
