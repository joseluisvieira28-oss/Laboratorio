#!/usr/bin/env python3
from __future__ import annotations
import csv,io,json,math,statistics,time,zipfile,hashlib
from datetime import date,datetime,timedelta,timezone
from pathlib import Path
import requests
HERE=Path(__file__).resolve().parent
RULE_PATH=HERE/"MEXC_APPLE_REGSESSION_TRANSFER_RULE_V0.2.json"
BIND_PATH=HERE/"MEXC_APPLE_REGSESSION_TRANSFER_BINDING_V0.2.json"
RULE=json.loads(RULE_PATH.read_text()); BIND=json.loads(BIND_PATH.read_text())
OUT=Path("artifacts/mexc_global_assets/apple_transfer_v02"); UA="CryptoLab-MEXC-APPLE-Transfer/0.2"
def shaf(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def shab(b): return hashlib.sha256(b).hexdigest()
def mean(x): return sum(x)/len(x) if x else None
def med(x): return statistics.median(x) if x else None
def sgn(x): return 1 if x>0 else (-1 if x<0 else 0)
def ts(d,h,m): return int(datetime(d.year,d.month,d.day,h,m,tzinfo=timezone.utc).timestamp())
def sessions():
 a=date.fromisoformat(RULE["sample_start_date"]); b=date.fromisoformat(RULE["sample_end_date_inclusive"]); ex={date.fromisoformat(x) for x in RULE["excluded_dates"]}; out=[]; d=a
 while d<=b:
  if d.weekday()<5 and d not in ex: out.append(d)
  d+=timedelta(days=1)
 return out
def req(u,p=None,t=60,retries=4):
 last=None
 for i in range(retries):
  try:
   r=requests.get(u,params=p,headers={"User-Agent":UA},timeout=t)
   if r.status_code!=200: raise RuntimeError(f"HTTP_{r.status_code}:{r.url}")
   return r
  except Exception as e:
   last=e; time.sleep(.7*(i+1))
 raise last
def mexc(d):
 r=req("https://api.mexc.com/api/v1/contract/kline/AAPLSTOCK_USDT",{"interval":"Min1","start":str(ts(d,14,29)),"end":str(ts(d,18,59))}); j=r.json()
 if j.get("success") is not True: raise RuntimeError(f"MEXC:{d}:{j}")
 out={}; z=j.get("data") or {}
 for t,p in zip(z.get("time") or [],z.get("close") or []):
  try: out[int(t)+60]=float(p)
  except: pass
 return out,shab(r.content)
def bitget(d):
 out={}; hs=[]
 for a,b in [(ts(d,14,29),ts(d,16,44)),(ts(d,16,45),ts(d,18,59))]:
  r=req("https://api.bitget.com/api/v2/mix/market/history-candles",{"symbol":"AAPLUSDT","productType":"USDT-FUTURES","granularity":"1m","startTime":str(a*1000),"endTime":str(b*1000),"limit":"200"})
  hs.append(shab(r.content)); j=r.json()
  if j.get("code")!="00000": raise RuntimeError(f"BITGET:{d}:{j}")
  for row in j.get("data") or []:
   try: out[int(row[0])//1000+60]=float(row[4])
   except: pass
 return out,hs
def binance(d):
 day=d.isoformat(); r=req(f"https://data.binance.vision/data/futures/um/daily/klines/AAPLUSDT/1m/AAPLUSDT-1m-{day}.zip",t=90)
 z=zipfile.ZipFile(io.BytesIO(r.content)); names=z.namelist()
 if len(names)!=1: raise RuntimeError(f"BINANCE_ID:{day}:{names}")
 out={}; lo=ts(d,14,29); hi=ts(d,18,59)
 for row in csv.reader(io.TextIOWrapper(z.open(names[0]),encoding="utf-8")):
  try: t=int(row[0])//1000; p=float(row[4])
  except: continue
  if lo<=t<=hi: out[t+60]=p
 return out,shab(r.content)
def binom(w,n): return sum(math.comb(n,k) for k in range(w,n+1))/(2**n) if n else None
def thirds(vals):
 n=len(vals); cuts=[0,n//3,(2*n)//3,n]
 return [mean(vals[cuts[i]:cuts[i+1]]) for i in range(3)] if n else [None,None,None]
def main():
 if RULE["outcomes_opened_at_freeze"]!=0 or BIND["historical_outcomes_opened_at_binding"]!=0: raise SystemExit("FAIL_CLOSED_NOT_PRE_OUTCOME")
 c=RULE["frozen_cell"]
 if [c["shock_threshold_bps"],c["lag_gap_threshold_bps"],c["horizon_min"]] != [5,3,1]: raise SystemExit("FAIL_CLOSED_CELL_CHANGED")
 sess=sessions()
 if len(sess)!=17: raise SystemExit(f"EXPECTED_17_SESSIONS_GOT_{len(sess)}")
 vals=[]; events=[]; hashes={}; common_total=0
 for d in sess:
  m,mh=mexc(d); b,bh=binance(d); g,gh=bitget(d); ds=d.isoformat(); hashes[ds]={"mexc":mh,"binance":bh,"bitget":gh}
  common=set(m)&set(b)&set(g); common_total+=len(common); nxt=ts(d,14,31)
  for t in sorted(common):
   if t<ts(d,14,31) or t>ts(d,18,44) or t<nxt: continue
   p=t-60; x=t+60
   if p not in m or p not in b or p not in g or x not in m: continue
   ext=(10000*(b[t]/b[p]-1)+10000*(g[t]/g[p]-1))/2
   mr=10000*(m[t]/m[p]-1); gap=ext-mr
   if abs(ext)<5 or sgn(gap)!=sgn(ext) or abs(gap)<3: continue
   gross=sgn(ext)*10000*(m[x]/m[t]-1)
   vals.append(gross); events.append({"date":ds,"t_utc":datetime.fromtimestamp(t,tz=timezone.utc).isoformat(),"external_return_bps":ext,"lag_gap_bps":gap,"gross_signed_bps":gross}); nxt=t+60
  time.sleep(.03)
 n=len(vals); wins=sum(x>0 for x in vals); days=len(set(e["date"] for e in events)); p=binom(wins,n); tr=thirds(vals); g=RULE["validation_gate"]
 enough=n>=g["min_n"] and days>=g["min_distinct_signal_sessions"]
 passed=bool(enough and mean(vals)>0 and med(vals)>0 and wins/n>0.5 and all(x is not None and x>0 for x in tr) and p<g["exact_one_sided_binomial_p_lt"])
 verdict=(RULE["promotion_if_pass"] if passed else (RULE["underpowered_outcome"] if not enough else RULE["fail_outcome"]))
 report={"study_id":RULE["study_id"],"generated_at_utc":datetime.now(timezone.utc).isoformat(),"rule_sha256":shaf(RULE_PATH),"binding_sha256":shaf(BIND_PATH),"sessions":len(sess),"exact_common_minutes":common_total,"n":n,"distinct_signal_sessions":days,"wins":wins,"win_rate":wins/n if n else None,"mean_gross_bps":mean(vals),"median_gross_bps":med(vals),"chronological_third_means_bps":tr,"p_value_one_sided_binomial_vs_50":p,"validation_pass":passed,"verdict":verdict,"cost_scenarios_mean_net_bps":{str(c):(mean(vals)-c if vals else None) for c in RULE["cost_scenarios_roundtrip_bps"]},"events":events,"source_hashes":hashes,"retrospective_oos_opened":False,"live_trading_authorized":False}
 OUT.mkdir(parents=True,exist_ok=True); (OUT/"MEXC_APPLE_REGSESSION_TRANSFER_CLOSEOUT_V02.json").write_text(json.dumps(report,indent=2,sort_keys=True))
 print(json.dumps({k:report[k] for k in ["verdict","sessions","exact_common_minutes","n","distinct_signal_sessions","wins","win_rate","mean_gross_bps","median_gross_bps","chronological_third_means_bps","p_value_one_sided_binomial_vs_50","validation_pass"]},indent=2))
if __name__=="__main__": main()
