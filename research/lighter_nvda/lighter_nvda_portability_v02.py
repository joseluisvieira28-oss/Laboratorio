#!/usr/bin/env python3
from __future__ import annotations
import csv,io,json,math,statistics,time,zipfile,hashlib
from datetime import date,datetime,timedelta,timezone
from pathlib import Path
import requests
HERE=Path(__file__).resolve().parent
R=json.loads((HERE/"LIGHTER_NVDA_PORTABILITY_RULE_V0.2.json").read_text())
B=json.loads((HERE/"LIGHTER_NVDA_PORTABILITY_SOURCE_BINDING_V0.2.json").read_text())
OUT=Path("artifacts/lighter_nvda/v02_portability")
UA="CryptoLab-Lighter-NVDA-Portability/0.2"
def H(b):return hashlib.sha256(b).hexdigest()
def mean(x):return sum(x)/len(x) if x else None
def med(x):return statistics.median(x) if x else None
def sgn(x):return 1 if x>0 else(-1 if x<0 else 0)
def sec(d,h,m):return int(datetime(d.year,d.month,d.day,h,m,tzinfo=timezone.utc).timestamp())
def req(url,params=None,timeout=60,retries=4):
 last=None
 for i in range(retries):
  try:
   r=requests.get(url,params=params,headers={"User-Agent":UA},timeout=timeout)
   if r.status_code!=200:raise RuntimeError(f"HTTP_{r.status_code}:{r.url}")
   return r
  except Exception as e:last=e;time.sleep(.5*(i+1))
 raise last
def sessions():
 a=date.fromisoformat(R["sample_start"]);b=date.fromisoformat(R["sample_end_inclusive"]);ex={date.fromisoformat(x) for x in R["excluded_dates"]};o=[];d=a
 while d<=b:
  if d.weekday()<5 and d not in ex:o.append(d)
  d+=timedelta(days=1)
 return o
def lighter(d):
 r=req(B["lighter_public_api"]+B["lighter_history_endpoint"],{"market_id":110,"resolution":"1m","start_timestamp":sec(d,14,20),"end_timestamp":sec(d,19,10),"count_back":500})
 j=r.json();o={}
 for x in j.get("c") or []:
  try:o[int(x["t"])//1000]=float(x["c"])
  except:pass
 return o,H(r.content)
def binance(d):
 s="NVDAUSDT";day=d.isoformat();r=req(f"https://data.binance.vision/data/futures/um/daily/klines/{s}/1m/{s}-1m-{day}.zip",timeout=90)
 z=zipfile.ZipFile(io.BytesIO(r.content));names=z.namelist();o={}
 if len(names)!=1:raise RuntimeError("BINANCE_ZIP")
 for row in csv.reader(io.TextIOWrapper(z.open(names[0]),encoding="utf-8")):
  try:t=int(row[0])//1000;p=float(row[4])
  except:continue
  if sec(d,14,20)<=t<=sec(d,19,10):o[t+60]=p
 return o,H(r.content)
def bitget(d):
 s="NVDAUSDT";o={};hs=[]
 for a,b in [(sec(d,14,20),sec(d,16,45)),(sec(d,16,46),sec(d,19,10))]:
  r=req("https://api.bitget.com/api/v2/mix/market/history-candles",{"symbol":s,"productType":"USDT-FUTURES","granularity":"1m","startTime":str(a*1000),"endTime":str(b*1000),"limit":"200"})
  hs.append(H(r.content));j=r.json()
  for row in j.get("data") or []:
   try:o[int(row[0])//1000+60]=float(row[4])
   except:pass
 return o,hs
def binom(w,n):return sum(math.comb(n,k) for k in range(w,n+1))/(2**n) if n else None
def main():
 if R["outcomes_opened_at_freeze"]!=0 or B["outcomes_opened_at_binding"]!=0:raise SystemExit("FAIL_CLOSED_FREEZE")
 D={};cov={};hashes={}
 for d in sessions():
  ds=d.isoformat();l,lh=lighter(d);bn,bh=binance(d);bg,gh=bitget(d);common=len(set(l)&set(bn)&set(bg))
  cov[ds]={"lighter":len(l),"binance":len(bn),"bitget":len(bg),"common":common};hashes[ds]={"lighter":lh,"binance":bh,"bitget":gh}
  if len(l)>=250 and len(bn)>=250 and len(bg)>=240 and common>=240:D[ds]={"l":l,"b":bn,"g":bg}
  time.sleep(.03)
 vals=[];days=[];sh=[];gaps=[];times=[];Q=R["exact_rule"]
 for ds,X in D.items():
  d=date.fromisoformat(ds);start=sec(d,14,31);stop=sec(d,18,44);nexta=start
  for t in sorted(set(X["l"])&set(X["b"])&set(X["g"])):
   if t<start or t>stop or t<nexta:continue
   prev=t-60;ex=t+60
   if any(z not in X[k] for z in [prev,t] for k in ["l","b","g"]) or ex not in X["l"]:continue
   rb=10000*(X["b"][t]/X["b"][prev]-1);rg=10000*(X["g"][t]/X["g"][prev]-1);er=(rb+rg)/2
   lr=10000*(X["l"][t]/X["l"][prev]-1);gap=er-lr
   if abs(er)<5 or sgn(gap)!=sgn(er) or abs(gap)<3:continue
   gross=sgn(er)*10000*(X["l"][ex]/X["l"][t]-1)
   vals.append(gross);days.append(ds);sh.append(er);gaps.append(gap);times.append(datetime.fromtimestamp(t,tz=timezone.utc).isoformat())
   nexta=t+60
 n=len(vals);wins=sum(v>0 for v in vals);half=n//2;halves=[mean(vals[:half]),mean(vals[half:])] if n else [None,None]
 result={"complete_sessions":len(D),"expected_sessions":len(sessions()),"n":n,"wins":wins,"win_rate":wins/n if n else None,
  "distinct_signal_sessions":len(set(days)),"mean_gross_bps":mean(vals),"median_gross_bps":med(vals),"half_means_bps":halves,
  "p_one_sided_binomial":binom(wins,n),"mean_abs_external_shock_bps":mean([abs(x) for x in sh]) if sh else None,
  "mean_abs_gap_bps":mean([abs(x) for x in gaps]) if gaps else None,
  "net_after_cost_bps":{str(c):(mean(vals)-c if vals else None) for c in R["execution"]["cost_scenarios_roundtrip_bps"]},
  "break_even_roundtrip_cost_bps":mean(vals),"signal_times":times}
 G=R["scientific_gate"]
 result["scientific_pass"]=bool(len(D)==len(sessions()) and n>=G["min_n"] and result["distinct_signal_sessions"]>=G["min_distinct_signal_sessions"] and
  result["mean_gross_bps"]>0 and result["median_gross_bps"]>0 and result["win_rate"]>G["win_rate_gt"] and
  all(x is not None and x>0 for x in halves) and result["p_one_sided_binomial"]<G["exact_one_sided_binomial_p_lt"])
 result["verdict"]="LIGHTER_NVDA_PORTABILITY_SCIENTIFIC_PASS__MICROSTRUCTURE_REQUIRED" if result["scientific_pass"] else "LIGHTER_NVDA_PORTABILITY_FAIL_AT_FROZEN_V02_GATE"
 report={"family_id":R["family_id"],"result":result,"coverage":cov,"source_hashes":hashes,"post_outcome_tuning":False,
  "private_endpoints_used":False,"account_reads":False,"wallets":False,"orders":False,"live_trading_authorized":False}
 OUT.mkdir(parents=True,exist_ok=True);(OUT/"LIGHTER_NVDA_PORTABILITY_CLOSEOUT_V02.json").write_text(json.dumps(report,indent=2,sort_keys=True))
 print(json.dumps({"verdict":result["verdict"],**{k:result[k] for k in ["complete_sessions","n","wins","win_rate","distinct_signal_sessions","mean_gross_bps","median_gross_bps","half_means_bps","p_one_sided_binomial","break_even_roundtrip_cost_bps"]}},indent=2))
if __name__=="__main__":main()
