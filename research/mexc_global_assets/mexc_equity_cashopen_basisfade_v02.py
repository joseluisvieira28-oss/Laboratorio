#!/usr/bin/env python3
from __future__ import annotations
import csv,io,json,math,statistics,time,zipfile,hashlib
from datetime import date,datetime,timedelta,timezone
from pathlib import Path
import requests
HERE=Path(__file__).resolve().parent
RP=HERE/"MEXC_EQUITY_CASHOPEN_BASISFADE_RULE_V0.2.json"; BP=HERE/"MEXC_EQUITY_CASHOPEN_BASISFADE_BINDING_V0.2.json"
R=json.loads(RP.read_text()); B=json.loads(BP.read_text())
OUT=Path("artifacts/mexc_global_assets/equity_cashopen_basisfade_v02"); UA="CryptoLab-MEXC-CashOpen-BasisFade/0.2"
def shaf(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def mean(x): return sum(x)/len(x) if x else None
def med(x): return statistics.median(x) if x else None
def sgn(x): return 1 if x>0 else (-1 if x<0 else 0)
def ts(d,h,m): return int(datetime(d.year,d.month,d.day,h,m,tzinfo=timezone.utc).timestamp())
def sess():
 a=date.fromisoformat(R["sample_start_date"]); b=date.fromisoformat(R["sample_end_date_inclusive"]); ex={date.fromisoformat(x) for x in R["excluded_dates"]}; o=[]; d=a
 while d<=b:
  if d.weekday()<5 and d not in ex:o.append(d)
  d+=timedelta(days=1)
 return o
def req(u,p=None,t=60,retries=4):
 last=None
 for i in range(retries):
  try:
   z=requests.get(u,params=p,headers={"User-Agent":UA},timeout=t)
   if z.status_code!=200: raise RuntimeError(f"HTTP_{z.status_code}:{z.url}")
   return z
  except Exception as e:last=e;time.sleep(.5*(i+1))
 raise last
def mexc(d,sym):
 z=req(f"https://api.mexc.com/api/v1/contract/kline/{sym}",{"interval":"Min1","start":str(ts(d,13,27)),"end":str(ts(d,14,0))}).json()
 if z.get("success") is not True: raise RuntimeError(f"MEXC:{sym}:{d}:{z}")
 return {int(t)+60:float(p) for t,p in zip((z.get("data") or {}).get("time") or [],(z.get("data") or {}).get("close") or [])}
def bitget(d,sym):
 z=req("https://api.bitget.com/api/v2/mix/market/history-candles",{"symbol":sym,"productType":"USDT-FUTURES","granularity":"1m","startTime":str(ts(d,13,27)*1000),"endTime":str(ts(d,13,30)*1000),"limit":"20"}).json()
 if z.get("code")!="00000": raise RuntimeError(f"BITGET:{sym}:{d}:{z}")
 return {int(r[0])//1000+60:float(r[4]) for r in z.get("data") or []}
def binance(d,sym):
 day=d.isoformat(); r=req(f"https://data.binance.vision/data/futures/um/daily/klines/{sym}/1m/{sym}-1m-{day}.zip",t=90)
 z=zipfile.ZipFile(io.BytesIO(r.content)); names=z.namelist()
 if len(names)!=1: raise RuntimeError("BINANCE_ID")
 o={}
 for row in csv.reader(io.TextIOWrapper(z.open(names[0]),encoding="utf-8")):
  try:t=int(row[0])//1000;p=float(row[4])
  except:continue
  if ts(d,13,27)<=t<=ts(d,13,30):o[t+60]=p
 return o
def binom(w,n): return sum(math.comb(n,k) for k in range(w,n+1))/(2**n) if n else None
def halves(v):
 k=len(v)//2
 return [mean(v[:k]),mean(v[k:])] if len(v)>=2 else [None,None]
def evaluate(ticker,cfg,days):
 vals=[]; bases=[]; events=[]
 for d in days:
  m=mexc(d,cfg["target"]); b=binance(d,cfg["external"]); g=bitget(d,cfg["external"])
  t=ts(d,13,29); x=ts(d,13,59)
  if t not in m or x not in m or t not in b or t not in g: continue
  ext=(b[t]+g[t])/2; basis=10000*(m[t]/ext-1); side=-sgn(basis)
  if side==0: continue
  gross=side*10000*(m[x]/m[t]-1)
  vals.append(gross); bases.append(basis); events.append({"date":d.isoformat(),"basis_bps":basis,"gross_signed_bps":gross})
  time.sleep(.02)
 n=len(vals); wins=sum(v>0 for v in vals); hs=halves(vals); sg=R["scientific_gate"]; eg=R["execution_scale_gate"]
 eligible=bool(n>=sg["min_n"] and mean(vals)>0 and med(vals)>0 and wins/n>0.5 and all(x>0 for x in hs))
 scale=bool(mean(vals)>eg["mean_gross_signed_bps_gt"] and med(vals)>eg["median_gross_signed_bps_gt"]) if vals else False
 return {"ticker":ticker,"n":n,"wins":wins,"win_rate":wins/n if n else None,"mean_gross_bps":mean(vals),"median_gross_bps":med(vals),"chronological_half_means_bps":hs,"mean_abs_basis_bps":mean([abs(x) for x in bases]),"p_value_one_sided_binomial_vs_50":binom(wins,n),"scientific_eligible_pre_holm":eligible,"execution_scale_raw_pass":scale,"events":events,"cost_scenarios_mean_net_bps":{str(c):(mean(vals)-c if vals else None) for c in R["cost_scenarios_roundtrip_bps"]}}
def holm(res):
 items=sorted(res.items(),key=lambda kv:kv[1]["p_value_one_sided_binomial_vs_50"] if kv[1]["p_value_one_sided_binomial_vs_50"] is not None else 1)
 active=True;m=len(items)
 for rank,(t,r) in enumerate(items,1):
  cut=R["scientific_gate"]["family_wise_alpha"]/(m-rank+1); p=r["p_value_one_sided_binomial_vs_50"]; reject=bool(active and p is not None and p<=cut)
  r.update({"holm_rank":rank,"holm_cutoff":cut,"holm_reject":reject}); active=active and reject
 for r in res.values():
  r["scientific_pass"]=bool(r["scientific_eligible_pre_holm"] and r["holm_reject"])
  r["execution_scale_pass"]=bool(r["scientific_pass"] and r["execution_scale_raw_pass"])
  r["classification"]=R["promotion_if_science_and_scale"] if r["execution_scale_pass"] else (R["science_only_classification"] if r["scientific_pass"] else (R["underpowered_classification"] if r["n"]<R["scientific_gate"]["min_n"] else R["fail_classification"]))
def main():
 if R["outcomes_opened_at_freeze"]!=0 or B["historical_outcomes_opened_at_binding"]!=0: raise SystemExit("FAIL_CLOSED")
 if R["horizon_min"]!=30 or R["basis_threshold_bps"] is not None: raise SystemExit("FAIL_CLOSED_RULE_CHANGED")
 days=sess()
 if len(days)!=17:raise SystemExit(f"SESSION_COUNT:{len(days)}")
 res={}
 for t,cfg in R["assets"].items():res[t]=evaluate(t,cfg,days)
 holm(res); science=sum(x["scientific_pass"] for x in res.values());scale=sum(x["execution_scale_pass"] for x in res.values())
 report={"study_id":R["study_id"],"generated_at_utc":datetime.now(timezone.utc).isoformat(),"rule_sha256":shaf(RP),"binding_sha256":shaf(BP),"results":res,"scientific_survivor_count":science,"execution_scale_survivor_count":scale,"verdict":"CASHOPEN_EXECUTION_SCALE_CANDIDATE_FOUND" if scale else ("CASHOPEN_SCIENTIFIC_SURVIVOR_ONLY" if science else "NO_CASHOPEN_BASISFADE_SURVIVOR_AT_FROZEN_V02_GATE"),"live_trading_authorized":False}
 OUT.mkdir(parents=True,exist_ok=True);(OUT/"MEXC_EQUITY_CASHOPEN_BASISFADE_CLOSEOUT_V02.json").write_text(json.dumps(report,indent=2,sort_keys=True))
 slim={k:{x:v[x] for x in ["n","wins","win_rate","mean_gross_bps","median_gross_bps","chronological_half_means_bps","p_value_one_sided_binomial_vs_50","holm_cutoff","holm_reject","scientific_pass","execution_scale_pass","classification"]} for k,v in res.items()}
 print(json.dumps({"verdict":report["verdict"],"scientific_survivor_count":science,"execution_scale_survivor_count":scale,"results":slim},indent=2,sort_keys=True))
if __name__=="__main__":main()
