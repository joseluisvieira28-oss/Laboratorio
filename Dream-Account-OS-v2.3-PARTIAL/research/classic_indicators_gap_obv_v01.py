#!/usr/bin/env python3
"""CIGL-OBV-01 — canonical OBV/SMA20 crossover experiment."""
from __future__ import annotations
import argparse, hashlib, json, math
from pathlib import Path
import numpy as np
import pandas as pd
from classic_indicators_gap_v01 import BASE_COST_BPS, STRESS_COST_BPS, HOLD_BARS, SYMBOLS, DISCOVERY_MONTHS, VALIDATION_MONTHS, FORBIDDEN_START, summarize, discovery_gate, validation_gate
from classic_indicators_gap_vwap_data_vision_v01 import load_symbol_phase, json_safe
L=20

def aggregate_exact(minute,timeframe):
    rule,expected=("1h",60) if timeframe=="1H" else ("4h",240)
    d=minute.copy().set_index("ts").sort_index()
    h=d.resample(rule,label="left",closed="left").agg(open=("open","first"),high=("high","max"),low=("low","min"),close=("close","last"),volume=("volume","sum"),minute_count=("close","count"))
    h["bar_ok"]=(h["minute_count"]==expected)&h[["open","high","low","close","volume"]].notna().all(axis=1)&(h["volume"]>0)
    return h

def add_obv(bars):
    out=bars.copy(); out["obv"]=np.nan; out["obv_sma20"]=np.nan
    valid=out["bar_ok"].fillna(False).to_numpy(bool); size=len(out); i=0
    while i<size:
        if not valid[i]: i+=1; continue
        j=i
        while j<size and valid[j]: j+=1
        if j-i>=L+2:
            cl=out["close"].iloc[i:j].to_numpy(float); vol=out["volume"].iloc[i:j].to_numpy(float); obv=np.zeros(j-i,dtype=float)
            for k in range(1,j-i):
                if cl[k]>cl[k-1]: obv[k]=obv[k-1]+vol[k]
                elif cl[k]<cl[k-1]: obv[k]=obv[k-1]-vol[k]
                else: obv[k]=obv[k-1]
            s=pd.Series(obv).rolling(L,min_periods=L).mean().to_numpy()
            idx=out.index[i:j]; out.loc[idx,"obv"]=obv; out.loc[idx,"obv_sma20"]=s
        i=j
    return out

def make_trades(bars,symbol,timeframe):
    h=bars.copy(); prev_ok=h["bar_ok"].shift(1).eq(True); cur_ok=h["bar_ok"].fillna(False)
    eligible=prev_ok&cur_ok&h[["obv","obv_sma20"]].notna().all(axis=1)&h[["obv","obv_sma20"]].shift(1).notna().all(axis=1)
    long_sig=eligible&(h["obv"].shift(1)<=h["obv_sma20"].shift(1))&(h["obv"]>h["obv_sma20"])
    short_sig=eligible&(h["obv"].shift(1)>=h["obv_sma20"].shift(1))&(h["obv"]<h["obv_sma20"])
    direction=pd.Series(0,index=h.index,dtype="int8"); direction[long_sig]=1; direction[short_sig]=-1
    rows=[]; next_free=-1; idx=h.index
    for pos,sig in enumerate(direction.to_numpy()):
        if sig==0: continue
        entry=pos+1; exit_=entry+HOLD_BARS
        if entry<=next_free or exit_>=len(h): continue
        if not bool(h["bar_ok"].iloc[entry:exit_].fillna(False).all()): continue
        et,xt=idx[entry],idx[exit_]
        if xt>=FORBIDDEN_START: continue
        ep,xp=float(h["open"].iloc[entry]),float(h["open"].iloc[exit_])
        if not(ep>0 and xp>0 and math.isfinite(ep) and math.isfinite(xp)): continue
        gross=float(sig*math.log(xp/ep)*10000.0)
        rows.append({"symbol":symbol,"timeframe":timeframe,"signal_time":idx[pos],"entry_time":et,"exit_time":xt,"direction":int(sig),"signal_obv":float(h["obv"].iloc[pos]),"signal_obv_sma20":float(h["obv_sma20"].iloc[pos]),"entry_price":ep,"exit_price":xp,"gross_bps":gross,"net10_bps":gross-BASE_COST_BPS,"net14_bps":gross-STRESS_COST_BPS})
        next_free=exit_-1
    return pd.DataFrame(rows)

def evaluate(months,phase,prov):
    parts={"1H":[],"4H":[]}; cov={}
    for s in SYMBOLS:
        minute=load_symbol_phase(s,months,phase,prov); cov[s]={"minute_rows":len(minute)}
        for tf in ("1H","4H"):
            bars=add_obv(aggregate_exact(minute,tf)); t=make_trades(bars,s,tf)
            cov[s][tf]={"valid_bars":int(bars.bar_ok.sum()),"obv_sma_bars":int(bars.obv_sma20.notna().sum()),"trades":len(t)}
            print(f"[{phase}] {s} {tf}: valid={cov[s][tf]['valid_bars']} sma={cov[s][tf]['obv_sma_bars']} trades={len(t)}",flush=True)
            if len(t): parts[tf].append(t)
    def comb(xs):
        if not xs:return pd.DataFrame()
        t=pd.concat(xs,ignore_index=True)
        for c in ["signal_time","entry_time","exit_time"]:t[c]=pd.to_datetime(t[c],utc=True)
        return t.sort_values(["entry_time","symbol"]).reset_index(drop=True)
    return comb(parts["1H"]),comb(parts["4H"]),cov

def assert_freeze(f):
    if f.get("experiment_id")!="CIGL-OBV-01":raise RuntimeError("OBV identity mismatch")
    o=f.get("obv",{}); e=f.get("execution",{}); g=f.get("phase_gates",{}).get("discovery_1h",{})
    if o.get("baseline")!="SMA20 of OBV" or o.get("orientation")!="flow_trend_crossover":raise RuntimeError("OBV freeze mismatch")
    if e.get("holding_bars")!=4 or e.get("base_roundtrip_cost_bps")!=10.0 or e.get("stress_roundtrip_cost_bps")!=14.0:raise RuntimeError("execution mismatch")
    if g.get("min_trades")!=300 or g.get("net10_mean_bps_gt")!=0.0 or g.get("profit_factor_gt")!=1.0:raise RuntimeError("gate mismatch")

def main():
    ap=argparse.ArgumentParser();ap.add_argument("--out",type=Path,required=True);ap.add_argument("--freeze",type=Path,required=True);a=ap.parse_args();a.out.mkdir(parents=True,exist_ok=True)
    fb=a.freeze.read_bytes();f=json.loads(fb);assert_freeze(f);prov=[]
    d1,d4,covd=evaluate(DISCOVERY_MONTHS,"DISCOVERY",prov);d1.to_csv(a.out/"CIGL_OBV_01_DISCOVERY_1H_TRADES.csv",index=False);d4.to_csv(a.out/"CIGL_OBV_01_DISCOVERY_4H_ROBUSTNESS_TRADES.csv",index=False)
    s1,s4=summarize(d1),summarize(d4);dg=discovery_gate(s1);opened=bool(dg["pass"]);vs1=vs4=vg=covv=None
    if opened:
        print("OBV DISCOVERY 1H PASS — opening frozen 2024 once",flush=True);v1,v4,covv=evaluate(VALIDATION_MONTHS,"VALIDATION_2024",prov);v1.to_csv(a.out/"CIGL_OBV_01_VALIDATION_2024_1H_TRADES.csv",index=False);v4.to_csv(a.out/"CIGL_OBV_01_VALIDATION_2024_4H_ROBUSTNESS_TRADES.csv",index=False);vs1,vs4=summarize(v1),summarize(v4);vg=validation_gate(vs1);status="MVE_1_REPLICATION_READY" if vg["pass"] else "OOS_FAIL_OBV_CLOSED"
    else:status="DISCOVERY_FAIL_OBV_CLOSED";print("OBV DISCOVERY 1H FAIL — 2024 remains unopened",flush=True)
    co=json_safe({"lab":"CLASSIC_INDICATORS_GAP_LAB_V0.1","experiment_id":"CIGL-OBV-01","status":status,"implementation_freeze_sha256":hashlib.sha256(fb).hexdigest(),"discovery_1h_summary":s1,"discovery_1h_gate":dg,"discovery_4h_robustness_summary":s4,"opened_2024":opened,"validation_1h_summary":vs1,"validation_1h_gate":vg,"validation_4h_robustness_summary":vs4,"coverage_discovery":covd,"coverage_validation":covv,"accessed_2025":False,"accessed_2026":False,"live_trading":False,"exchange_mutation":False,"post_result_parameter_change":False})
    (a.out/"CIGL_OBV_01_CLOSEOUT.json").write_text(json.dumps(co,indent=2,sort_keys=True));(a.out/"CIGL_OBV_01_DATA_PROVENANCE.json").write_text(json.dumps(json_safe(prov),indent=2,sort_keys=True));
    p,r=co["discovery_1h_summary"],co["discovery_4h_robustness_summary"];lines=["# CIGL-OBV-01 — CLOSEOUT","",f"Status: **{status}**","","## 1H Discovery",f"- Trades: {p.get('n')}",f"- Gross mean: {p.get('gross_mean_bps')} bps",f"- NET10 mean: {p.get('net10_mean_bps')} bps",f"- NET14 mean: {p.get('net14_mean_bps')} bps",f"- PF NET10: {p.get('pf_net10')}",f"- Gate pass: {dg['pass']}","","## 4H robustness",f"- Trades: {r.get('n')}",f"- NET10 mean: {r.get('net10_mean_bps')} bps",f"- PF NET10: {r.get('pf_net10')}","",f"2024 opened: **{opened}**","2025 accessed: **False**","2026 accessed: **False**"]
    if vs1:lines += ["","## 2024 OOS",f"- Trades: {vs1.get('n')}",f"- NET10 mean: {vs1.get('net10_mean_bps')} bps",f"- PF NET10: {vs1.get('pf_net10')}",f"- Gate pass: {vg['pass']}"]
    (a.out/"CIGL_OBV_01_SUMMARY.md").write_text("\n".join(lines)+"\n");print(json.dumps(co,indent=2,sort_keys=True),flush=True)
if __name__=="__main__":main()
