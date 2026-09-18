from __future__ import annotations
import argparse, csv, hashlib, io, json, math, re, zipfile
from pathlib import Path
import numpy as np
import pandas as pd
from research.ll0017_top_global_positioning_v01 import FROZEN, threshold_cross_direction

SYMBOLS=("BTCUSDT","ETHUSDT","SOLUSDT","BNBUSDT","XRPUSDT","DOGEUSDT")
DISCOVERY_START=pd.Timestamp("2023-02-01T00:00:00Z")
DISCOVERY_END=pd.Timestamp("2024-01-01T00:00:00Z")
SOURCE_START=pd.Timestamp("2023-01-01T00:00:00Z")
SOURCE_END=pd.Timestamp("2024-01-01T00:00:00Z")
CONFIRMATION_START=pd.Timestamp("2024-01-01T00:00:00Z")
EXPECTED_OUTER_SHA256={
"LL-0016-B-RUN02_RAW_part01.zip":"592b88bd34613675e12932aefc874f3f6b37af02f4c1608a2cc94a52853e5d2b",
"LL-0016-B-RUN02_RAW_part02.zip":"a0170e4f3fc742e95680195b5cd36ec8928e5650cc2de7e6d8f055be6e661065",
"LL-0016-B-RUN02_RAW_part03.zip":"f315e93b893e124467696bd54e0d2cfe147a34df55d79d77b46ef6ad61e1f629",
"LL-0016-B-RUN02_RAW_part04.zip":"3677b41e1c1ffc5108208215e8ff65811614afad08dad840b04ce2b17214a834",
"LL-0016-B-RUN02_RAW_part05.zip":"41381d98adeeb36db0428d380635dfd30d9e45374383acd163d35fa7eea30f52"}
EXPECTED_METRICS_2023_HASHSET="8ecfde4485a20a9197b6ad60404db09697179e2bd0a96f8b2d9062dfebc49aad"
EXPECTED_PRICE_2023_HASHSET="61af8288142dbd0496596b9096113ec804835b488fa2a2640324722b0ff10a87"
BOOTSTRAP_SEED=20260918; BOOTSTRAP_REPS=9999

def sha256_file(path):
 h=hashlib.sha256()
 with open(path,"rb") as f:
  for c in iter(lambda:f.read(8*1024*1024),b""): h.update(c)
 return h.hexdigest()

def nested_checksum(outer,name,blob):
 actual=hashlib.sha256(blob).hexdigest(); names=set(outer.namelist()); chk=name+".CHECKSUM"
 if chk not in names:
  alt=name.replace(".zip",".zip.CHECKSUM"); chk=alt if alt in names else ""
 if not chk:return actual,False
 return actual,outer.read(chk).decode("utf-8","replace").strip().split()[0].lower()==actual

def verify_outer_parts(raw_dir):
 parts={}
 for fn,expected in EXPECTED_OUTER_SHA256.items():
  p=raw_dir/fn
  if not p.exists() or sha256_file(p)!=expected: raise RuntimeError("SOURCE_GATE_BLOCKED outer "+fn)
  parts[fn]=p
 return parts

def load_metrics(part1):
 rows={s:[] for s in SYMBOLS}; hashes=[]
 with zipfile.ZipFile(part1) as outer:
  for name in sorted(n for n in outer.namelist() if n.startswith("RAW/OI_RAW/") and n.endswith(".zip")):
   m=re.search(r"/([A-Z]+USDT)-metrics-(2023-\d{2}-\d{2})\.zip$",name)
   if not m or m.group(1) not in rows:continue
   sym,day=m.group(1),m.group(2); blob=outer.read(name); actual,ok=nested_checksum(outer,name,blob)
   if not ok:raise RuntimeError("SOURCE_GATE_BLOCKED nested "+name)
   hashes.append((name,actual)); named=pd.Timestamp(day,tz="UTC")
   with zipfile.ZipFile(io.BytesIO(blob)) as inner:
    cn=next(n for n in inner.namelist() if n.lower().endswith(".csv"))
    rd=csv.DictReader(io.TextIOWrapper(inner.open(cn),encoding="utf-8-sig",newline="")); seen=set()
    for r in rd:
     t=pd.Timestamp(r["create_time"])
     if t.tzinfo is None:t=t.tz_localize("UTC")
     else:t=t.tz_convert("UTC")
     if not(named<=t<named+pd.Timedelta(days=1)):continue
     if t in seen:raise RuntimeError("SOURCE_GATE_BLOCKED duplicate metric")
     seen.add(t)
     try:vals=[float(r[k]) for k in ("sum_toptrader_long_short_ratio","count_long_short_ratio","count_toptrader_long_short_ratio","sum_taker_long_short_vol_ratio")]
     except:vals=[float("nan")]*4
     rows[sym].append((t,*vals))
 canon="\n".join(f"{n}\t{h}" for n,h in sorted(hashes)).encode(); hs=hashlib.sha256(canon).hexdigest()
 if hs!=EXPECTED_METRICS_2023_HASHSET:raise RuntimeError("SOURCE_GATE_BLOCKED metrics hashset")
 full=pd.date_range(SOURCE_START,SOURCE_END-pd.Timedelta(minutes=5),freq="5min")
 return {s:pd.DataFrame(a,columns=["time","top_pos","global_acct","top_acct","taker"]).set_index("time").sort_index().reindex(full) for s,a in rows.items()},hs

def load_prices(parts):
 price={s:[] for s in SYMBOLS}; hashes=[]
 for p in parts.values():
  with zipfile.ZipFile(p) as outer:
   for name in sorted(n for n in outer.namelist() if n.startswith("RAW/PRICE_RAW/") and n.endswith(".zip")):
    m=re.search(r"/([A-Z]+USDT)-1m-2023-(\d{2})\.zip$",name)
    if not m or m.group(1) not in price:continue
    sym=m.group(1); blob=outer.read(name); actual,ok=nested_checksum(outer,name,blob)
    if not ok:raise RuntimeError("SOURCE_GATE_BLOCKED price checksum")
    hashes.append((name,actual))
    with zipfile.ZipFile(io.BytesIO(blob)) as inner:
     cn=next(n for n in inner.namelist() if n.lower().endswith(".csv")); lines=inner.read(cn).decode("utf-8-sig","replace").splitlines()
     data=lines[1:] if lines and not lines[0].split(",")[0].strip().isdigit() else lines
     for line in data:
      c=line.split(",")
      if len(c)<6:continue
      t=pd.to_datetime(int(c[0]),unit="ms",utc=True)
      if SOURCE_START<=t<SOURCE_END:price[sym].append((t,float(c[1])))
 canon="\n".join(f"{n}\t{h}" for n,h in sorted(hashes)).encode(); hs=hashlib.sha256(canon).hexdigest()
 if hs!=EXPECTED_PRICE_2023_HASHSET:raise RuntimeError("SOURCE_GATE_BLOCKED price hashset")
 full=pd.date_range(SOURCE_START,SOURCE_END-pd.Timedelta(minutes=1),freq="1min"); out={}
 for s,a in price.items():
  ser=pd.Series(dict(a),dtype=float).sort_index().reindex(full)
  if ser.notna().mean()<.9999:raise RuntimeError("SOURCE_GATE_BLOCKED price coverage "+s)
  out[s]=ser
 return out,hs

def build_events(metrics,prices):
 events=[]; minp=math.ceil(30*24*12*FROZEN.min_lookback_coverage)
 for sym in SYMBOLS:
  df=metrics[sym].copy(); valid=(df.top_pos>0)&(df.global_acct>0)
  df["divergence"]=np.where(valid,np.log(df.top_pos)-np.log(df.global_acct),np.nan)
  roll=df.divergence.rolling("30D",closed="left",min_periods=minp); df["z"]=(df.divergence-roll.mean())/roll.std(ddof=1); df["zprev"]=df.z.shift(1)
  last_exit=pd.Timestamp.min.tz_localize("UTC")
  for t,row in df.loc[(df.index>=DISCOVERY_START)&(df.index<DISCOVERY_END)].iterrows():
   if pd.isna(row.z) or pd.isna(row.zprev):continue
   d=threshold_cross_direction(float(row.z),float(row.zprev))
   if d==0:continue
   entry=t+pd.Timedelta(minutes=FROZEN.entry_delay_minutes); exit_=entry+pd.Timedelta(minutes=FROZEN.primary_hold_minutes)
   if exit_>=CONFIRMATION_START or entry<last_exit:continue
   p0=prices[sym].get(entry,np.nan); p1=prices[sym].get(exit_,np.nan)
   if pd.isna(p0) or pd.isna(p1) or p0<=0 or p1<=0:continue
   gross=d*math.log(float(p1)/float(p0))*10000
   events.append({"symbol":sym,"signal_time":t,"entry_time":entry,"exit_time":exit_,"direction":d,"z":float(row.z),"gross_bps":gross,"net14_bps":gross-14.0,"net20_bps":gross-20.0}); last_exit=exit_
 return pd.DataFrame(events)

def bootstrap(e,col):
 e=e.copy(); e["day"]=pd.to_datetime(e.entry_time,utc=True).dt.floor("D"); groups=[g[col].to_numpy(float) for _,g in e.groupby("day")]; rng=np.random.default_rng(BOOTSTRAP_SEED); vals=np.empty(BOOTSTRAP_REPS); n=len(groups)
 for i in range(BOOTSTRAP_REPS):
  sel=rng.integers(0,n,size=n); vals[i]=np.concatenate([groups[j] for j in sel]).mean()
 return {"p_one_sided":float((1+np.sum(vals<=0))/(BOOTSTRAP_REPS+1)),"lower95":float(np.quantile(vals,.05)),"upper95":float(np.quantile(vals,.95))}

def summarize(e):
 if e.empty:return {"decision":"NO_EVENTS","n":0}
 e=e.copy(); t=pd.to_datetime(e.entry_time,utc=True); e["quarter"]=t.dt.to_period("Q").astype(str); e["month"]=t.dt.to_period("M").astype(str)
 by_asset=e.groupby("symbol").net14_bps.agg(["count","mean"]).to_dict("index"); by_q=e.groupby("quarter").net14_bps.mean().to_dict(); loo={s:float(e.loc[e.symbol!=s,"net14_bps"].mean()) for s in SYMBOLS}
 k=max(1,math.ceil(len(e)*.01)); no_top=e.sort_values("net14_bps",ascending=False).iloc[k:]; a=e.gross_bps.abs(); den=float(a.sum()) or 1.0
 conc={"asset":float(e.assign(a=a).groupby("symbol").a.sum().max()/den),"month":float(e.assign(a=a).groupby("month").a.sum().max()/den),"top5":float(a.nlargest(min(5,len(e))).sum()/den),"single":float(a.max()/den)}
 b=bootstrap(e,"net14_bps")
 gates={"n_pooled_ge_300":len(e)>=300,"n_each_asset_ge_30":all(v["count"]>=30 for v in by_asset.values()),"net14_mean_positive":float(e.net14_bps.mean())>0,"net20_mean_positive":float(e.net20_bps.mean())>0,"gross_median_positive":float(e.gross_bps.median())>0,"bootstrap_p_lt_0_05":b["p_one_sided"]<.05,"bootstrap_lower95_positive":b["lower95"]>0,"all_leave_one_asset_out_positive":min(loo.values())>0,"four_of_six_assets_positive":sum(v["mean"]>0 for v in by_asset.values())>=4,"three_of_four_quarters_positive_and_q4":sum(v>0 for v in by_q.values())>=3 and by_q.get("2023Q4",-1)>0,"remove_top1pct_positive":float(no_top.net14_bps.mean())>0,"asset_concentration_le_0_35":conc["asset"]<=.35,"month_concentration_le_0_25":conc["month"]<=.25,"top5_concentration_le_0_15":conc["top5"]<=.15,"single_concentration_le_0_05":conc["single"]<=.05}
 return {"n":int(len(e)),"gross_mean_bps":float(e.gross_bps.mean()),"gross_median_bps":float(e.gross_bps.median()),"net14_mean_bps":float(e.net14_bps.mean()),"net20_mean_bps":float(e.net20_bps.mean()),"bootstrap":b,"by_asset":by_asset,"by_quarter":by_q,"leave_one_asset_out_net14":loo,"remove_top1pct_net14_mean_bps":float(no_top.net14_bps.mean()),"concentration":conc,"gates":gates,"decision":"SURVIVES_DISCOVERY" if all(gates.values()) else "NO_EDGE_DISCOVERY_FAIL"}

def main():
 ap=argparse.ArgumentParser(); ap.add_argument("--raw-dir",type=Path,required=True); ap.add_argument("--out-dir",type=Path,required=True); a=ap.parse_args()
 parts=verify_outer_parts(a.raw_dir); metrics,mh=load_metrics(parts["LL-0016-B-RUN02_RAW_part01.zip"]); prices,ph=load_prices(parts); events=build_events(metrics,prices)
 if not events.empty and pd.to_datetime(events.entry_time,utc=True).max()>=CONFIRMATION_START:raise RuntimeError("FIREWALL_BREACH")
 summary=summarize(events); a.out_dir.mkdir(parents=True,exist_ok=True); events.to_csv(a.out_dir/"events_2023.csv",index=False)
 receipt={"experiment_id":"LL-0017-TPD-001","version":"0.1","confirmation_2024H1_accessed":False,"2025_accessed":False,"2026_accessed":False,"metrics_2023_hashset_sha256":mh,"price_2023_hashset_sha256":ph,"summary":summary}
 (a.out_dir/"RESULT.json").write_text(json.dumps(receipt,indent=2,sort_keys=True)); hashes={p.name:sha256_file(p) for p in sorted(a.out_dir.iterdir()) if p.is_file()}; (a.out_dir/"OUTPUT_SHA256.json").write_text(json.dumps(hashes,indent=2,sort_keys=True)); print(json.dumps(receipt,indent=2,sort_keys=True))
if __name__=="__main__":main()
