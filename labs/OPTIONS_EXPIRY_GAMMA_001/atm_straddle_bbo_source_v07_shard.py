#!/usr/bin/env python3
import csv,gzip,hashlib,io,json,math,os,sys
from datetime import date,datetime,timezone,timedelta
from pathlib import Path
import requests
ROOT=Path("labs/OPTIONS_EXPIRY_GAMMA_001")
AUTH=json.loads((ROOT/"ATM_STRADDLE_BBO_SOURCE_AUTHORITY_V0.7.json").read_text())
SPEC=json.loads((ROOT/"ATM_STRADDLE_BBO_SOURCE_TECHNICAL_SPEC_V0.7.json").read_text())
OUT=Path("artifacts/oeg_atm_straddle_bbo_source_v07_shards");OUT.mkdir(parents=True,exist_ok=True)
S=requests.Session();S.headers.update({"User-Agent":"SRC-Crypto-Lab-OEG-BBO/0.7","Accept":"application/gzip"})
def num(v):
    try:
        x=float(str(v).strip());return x if math.isfinite(x) else None
    except Exception:return None
def integer(v):
    x=num(v);return None if x is None else int(x)
def us(day,t):
    return int(datetime.fromisoformat(day+"T"+t+"+00:00").timestamp()*1_000_000)
def stream(url):
    r=S.get(url,stream=True,timeout=180);h=hashlib.sha256()
    if r.status_code!=200:return r,None,h
    class H(io.RawIOBase):
        def __init__(self,raw):self.raw=raw
        def readable(self):return True
        def readinto(self,b):
            n=self.raw.readinto(b)
            if n:h.update(memoryview(b)[:n])
            return n
    txt=io.TextIOWrapper(gzip.GzipFile(fileobj=io.BufferedReader(H(r.raw))),encoding="utf-8",newline="")
    return r,csv.DictReader(txt),h
def parse_exp(v):
    iv=integer(v)
    if iv is not None:return datetime.fromtimestamp(iv/1_000_000,tz=timezone.utc).date()
    try:return datetime.fromisoformat(str(v).replace("Z","+00:00")).date()
    except Exception:return None
def main():
    idx=int(os.environ["OEG_PROBE_INDEX"]);day=AUTH["deterministic_probe_dates"][idx]
    y,m,d=day.split("-");target=us(day,"12:00:00");eod=us(day,"23:59:59.999999")
    curl=f"https://datasets.tardis.dev/v1/deribit/options_chain/{y}/{m}/{d}/OPTIONS.csv.gz"
    qurl=f"https://datasets.tardis.dev/v1/deribit/quotes/{y}/{m}/{d}/OPTIONS.csv.gz"
    result={"date":day,"pass":False,"technical_error":None,"bid_ask_values_retained":False,"pnl_opened":False,"returns_opened":False}
    try:
        cr,ch,chash=stream(curl)
        if cr.status_code!=200 or ch is None:raise RuntimeError(f"chain HTTP {cr.status_code}")
        latest={}
        for row in ch:
            ts=integer(row.get("timestamp"))
            if ts is None:continue
            if ts>target:break
            sym=(row.get("symbol") or "").strip().upper()
            if not sym.startswith("BTC-"):continue
            typ=(row.get("type") or "").strip().lower();strike=num(row.get("strike_price"));und=num(row.get("underlying_price"));exp=parse_exp(row.get("expiration"))
            if typ not in ("call","put") or strike is None or und is None or exp is None:continue
            dte=(exp-date.fromisoformat(day)).days
            if dte<AUTH["selection"]["expiry_dte_min"] or dte>AUTH["selection"]["expiry_dte_max"]:continue
            if sym not in latest or ts>latest[sym][0]:latest[sym]=(ts,typ,strike,und,exp)
        cr.close()
        pairs={}
        for sym,(ts,typ,strike,und,exp) in latest.items():
            key=(exp.isoformat(),strike);pairs.setdefault(key,{"und":[]})[typ]=sym;pairs[key]["und"].append(und)
        cands=[]
        for (exp_s,strike),v in pairs.items():
            if "call" in v and "put" in v:
                und=sum(v["und"])/len(v["und"]);dte=(date.fromisoformat(exp_s)-date.fromisoformat(day)).days
                cands.append((dte,abs(strike-und),strike,exp_s,v["call"],v["put"]))
        if not cands:raise RuntimeError("no eligible ATM call-put pair")
        cands.sort(key=lambda x:(x[0],x[1],x[2],x[3]));sel=cands[0]
        dte,dist,strike,exp_s,call,put=sel
        entry0=target;entry1=target+5*60*1_000_000;exit0=us(day,"23:55:00");exit1=eod
        qr,qd,qhash=stream(qurl)
        if qr.status_code!=200 or qd is None:raise RuntimeError(f"quotes HTTP {qr.status_code}")
        found={(call,"entry"):None,(put,"entry"):None,(call,"exit"):None,(put,"exit"):None}
        for row in qd:
            ts=integer(row.get("timestamp"))
            if ts is None:continue
            if ts>exit1:break
            sym=(row.get("symbol") or "").strip().upper()
            if sym not in (call,put):continue
            bid=num(row.get("bid_price"));ask=num(row.get("ask_price"));ba=num(row.get("bid_amount"));aa=num(row.get("ask_amount"))
            good=bid is not None and ask is not None and ba is not None and aa is not None and bid>0 and ask>0 and ba>0 and aa>0 and ask>=bid
            if not good:continue
            if entry0<=ts<=entry1 and found[(sym,"entry")] is None:found[(sym,"entry")]=ts
            if exit0<=ts<=exit1 and found[(sym,"exit")] is None:found[(sym,"exit")]=ts
        qr.close()
        checks={"pair_selected":True,"entry_call":found[(call,"entry")] is not None,"entry_put":found[(put,"entry")] is not None,"exit_call":found[(call,"exit")] is not None,"exit_put":found[(put,"exit")] is not None}
        result.update({"pass":all(checks.values()),"selected_expiry":exp_s,"selected_strike":strike,"selected_dte":dte,"call_symbol":call,"put_symbol":put,"gate_checks":checks,
          "entry_call_delay_seconds":None if found[(call,"entry")] is None else (found[(call,"entry")]-entry0)/1e6,
          "entry_put_delay_seconds":None if found[(put,"entry")] is None else (found[(put,"entry")]-entry0)/1e6,
          "exit_call_delay_seconds":None if found[(call,"exit")] is None else (found[(call,"exit")]-exit0)/1e6,
          "exit_put_delay_seconds":None if found[(put,"exit")] is None else (found[(put,"exit")]-exit0)/1e6,
          "chain_http":cr.status_code,"quotes_http":qr.status_code,"chain_sha256":chash.hexdigest(),"quotes_sha256":qhash.hexdigest()})
    except Exception as e:result["technical_error"]=f"{type(e).__name__}: {str(e)[:700]}"
    p=OUT/f"probe_{idx}.json";p.write_text(json.dumps(result,indent=2,sort_keys=True)+"\n")
    print(json.dumps(result,sort_keys=True))
    return 0
if __name__=="__main__":sys.exit(main())
