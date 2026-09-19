#!/usr/bin/env python3
import csv,gzip,hashlib,io,json,math,os,sys,zipfile
from datetime import date,datetime,timezone
from pathlib import Path
import requests

ROOT=Path("labs/OPTIONS_EXPIRY_GAMMA_001")
AUTH=json.loads((ROOT/"GAMMA_FLOW_VOL_DISCOVERY_AUTHORITY_V0.6.json").read_text())
OUT=Path("artifacts/oeg_gamma_flow_vol_discovery_v06_shards"); OUT.mkdir(parents=True,exist_ok=True)
S=requests.Session(); S.headers.update({"User-Agent":"SRC-Crypto-Lab-OEG-GammaFlowVol/0.6"})

def num(v):
    try:
        x=float(str(v).strip()); return x if math.isfinite(x) else None
    except Exception:return None

def integer(v):
    x=num(v); return None if x is None else int(x)

def us(day,t):
    return int(datetime.fromisoformat(day+"T"+t+"+00:00").timestamp()*1_000_000)

def stream_gz_csv(url):
    r=S.get(url,stream=True,timeout=180)
    h=hashlib.sha256()
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

def expiry_from_symbol(sym):
    try:return datetime.strptime(sym.split("-")[1],"%d%b%y").date()
    except Exception:return None

def predictor(day):
    y,m,d=day.split("-")
    turl=f"https://datasets.tardis.dev/v1/deribit/trades/{y}/{m}/{d}/OPTIONS.csv.gz"
    curl=f"https://datasets.tardis.dev/v1/deribit/options_chain/{y}/{m}/{d}/OPTIONS.csv.gz"
    start=us(day,AUTH["predictor_source"]["info_start_utc"]); end=us(day,AUTH["predictor_source"]["info_end_utc"])
    cr,ch,chash=stream_gz_csv(curl)
    if cr.status_code!=200 or ch is None:raise RuntimeError(f"chain HTTP {cr.status_code}")
    target={}
    for row in ch:
        ts=integer(row.get("timestamp"))
        if ts is None:continue
        if ts>end:break
        if ts<start:continue
        sym=(row.get("symbol") or "").strip().upper()
        if not sym.startswith("BTC-"):continue
        ex=expiry_from_symbol(sym)
        if ex is None:continue
        dte=(ex-date.fromisoformat(day)).days
        if dte<AUTH["predictor_source"]["short_dated_dte_min"] or dte>AUTH["predictor_source"]["short_dated_dte_max"]:continue
        oi=num(row.get("open_interest")); ga=num(row.get("gamma"))
        if oi is None or ga is None:continue
        if sym not in target or ts>target[sym][0]:target[sym]=(ts,oi,ga)
    cr.close()

    tr,trd,thash=stream_gz_csv(turl)
    if tr.status_code!=200 or trd is None:raise RuntimeError(f"trades HTTP {tr.status_code}")
    net=gross=0.0; n=0; syms=set()
    for row in trd:
        ts=integer(row.get("timestamp"))
        if ts is None:continue
        if ts>end:break
        if ts<start:continue
        sym=(row.get("symbol") or "").strip().upper()
        snap=target.get(sym)
        if snap is None:continue
        _,oi,ga=snap
        if oi<=0 or ga<=0:continue
        side=(row.get("side") or "").strip().lower()
        amt=num(row.get("amount"))
        if side not in ("buy","sell") or amt is None or amt<=0:continue
        w=amt*ga
        if w<=0 or not math.isfinite(w):continue
        s=1.0 if side=="buy" else -1.0
        net+=s*w; gross+=w; n+=1; syms.add(sym)
    tr.close()
    if gross<=0:raise RuntimeError("zero gamma-weighted volume")
    return {
      "gamma_flow_balance":net/gross,
      "eligible_trades":n,
      "distinct_eligible_symbols":len(syms),
      "trades_sha256":thash.hexdigest(),
      "chain_sha256":chash.hexdigest(),
      "trades_http":tr.status_code,
      "chain_http":cr.status_code
    }

def btc_outcome(day):
    y,m,d=day.split("-")
    name=f"BTCUSDT-5m-{day}.zip"
    base=f"https://data.binance.vision/data/spot/daily/klines/BTCUSDT/5m/{name}"
    chk=S.get(base+".CHECKSUM",timeout=60)
    if chk.status_code!=200:raise RuntimeError(f"checksum HTTP {chk.status_code}")
    parts=chk.text.strip().split()
    if len(parts)<2:raise RuntimeError("bad checksum line")
    expected=parts[0].lower()
    z=S.get(base,timeout=120)
    if z.status_code!=200:raise RuntimeError(f"zip HTTP {z.status_code}")
    got=hashlib.sha256(z.content).hexdigest()
    if got!=expected:raise RuntimeError("binance checksum mismatch")
    target_ms=int(datetime.fromisoformat(day+"T12:00:00+00:00").timestamp()*1000)
    end_ms=int(datetime.fromisoformat(day+"T23:59:59.999+00:00").timestamp()*1000)
    bars=[]
    with zipfile.ZipFile(io.BytesIO(z.content)) as zz:
        names=zz.namelist()
        if len(names)!=1:raise RuntimeError("unexpected zip members")
        with zz.open(names[0]) as f:
            txt=io.TextIOWrapper(f,encoding="utf-8",newline="")
            for row in csv.reader(txt):
                if len(row)<5:continue
                ot=integer(row[0]); op=num(row[1]); cl=num(row[4])
                if ot is None or op is None or cl is None:continue
                if target_ms<=ot<=end_ms:bars.append((ot,op,cl))
    bars.sort()
    if len(bars)!=AUTH["outcome_source"]["required_bars"]:raise RuntimeError(f"expected 144 bars got {len(bars)}")
    prices=[bars[0][1]]+[x[2] for x in bars]
    rv=0.0
    for a,b in zip(prices,prices[1:]):
        if a<=0 or b<=0:raise RuntimeError("nonpositive BTC price")
        r=math.log(b/a); rv+=r*r
    if rv<=0:raise RuntimeError("nonpositive RV")
    return {"log_realized_variance_12h":math.log(rv),"rv_12h":rv,"bars":len(bars),"binance_zip_sha256":got,"binance_checksum_sha256":expected}

def main():
    sid=int(os.environ["OEG_SHARD_ID"]); n=int(AUTH["shard_count"])
    dates=[d for i,d in enumerate(AUTH["deterministic_dates"]) if i%n==sid]
    rows=[]
    for i,day in enumerate(dates,1):
        rec={"date":day,"year":int(day[:4]),"technical_error":None}
        try:
            p=predictor(day); o=btc_outcome(day)
            rec.update(p);rec.update(o)
            rec["eligible"]=(p["eligible_trades"]>=AUTH["predictor_source"]["minimum_eligible_trades_per_date"] and p["distinct_eligible_symbols"]>=AUTH["predictor_source"]["minimum_distinct_eligible_symbols_per_date"])
        except Exception as e:
            rec["eligible"]=False;rec["technical_error"]=f"{type(e).__name__}: {str(e)[:500]}"
        rows.append(rec)
        print(f"OEG_V06_PROGRESS shard={sid} {i}/{len(dates)} {day} eligible={rec['eligible']} err={rec['technical_error']}",flush=True)
    result={"lab_id":AUTH["lab_id"],"discovery_id":AUTH["discovery_id"],"shard_id":sid,"shard_count":n,"rows":rows,
      "dealer_inventory_inferred":False,"dealer_gamma_sign_inferred":False,"option_strategy_pnl_opened":False,
      "access_2025":False,"access_2026":False,"live_trading":False,"exchange_mutation":False,"merge_to_main":False}
    p=OUT/f"shard_{sid}.json";p.write_text(json.dumps(result,indent=2,sort_keys=True)+"\n")
    print(json.dumps({"shard_id":sid,"dates":len(rows),"eligible":sum(bool(x.get("eligible")) for x in rows),"technical_errors":sum(bool(x.get("technical_error")) for x in rows)},sort_keys=True))
    return 0
if __name__=="__main__":sys.exit(main())
