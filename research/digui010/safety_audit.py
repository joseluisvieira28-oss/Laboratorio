#!/usr/bin/env python3
"""DIGUI-010-C: adversarial check for *relative percentage* liquidity trap.
POST-HOC on same four days. Quoted liquidity != executable depth. No trades.
"""
from pathlib import Path
import json
import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingClassifier
import analysis as a

def make(tr,va,te,target,features):
    m=HistGradientBoostingClassifier(max_iter=60,max_leaf_nodes=7,max_depth=3,
        min_samples_leaf=35,learning_rate=.06,l2_regularization=5.,random_state=17,
        early_stopping=False)
    m.fit(tr[features].to_numpy(float),tr[target].to_numpy(int))
    sv=m.predict_proba(va[features].to_numpy(float))[:,1]
    st=m.predict_proba(te[features].to_numpy(float))[:,1]
    return st<=float(np.quantile(sv,.70))
def finite_median(s):
    v=pd.to_numeric(s,errors="coerce")
    return float(v.median()) if len(v) and v.notna().any() else None
def eval(df,mask):
    sub=df.loc[mask]
    return {"n":int(len(sub)),
       "pct_of_total":float(100*len(sub)/len(df)),
       "start_liq_usd_median":finite_median(sub.liq_s),
       "hour_liq_usd_median":finite_median(sub.liq_h),
       "start_liq_below_1000_pct":float(100*(sub.liq_s<1000).mean()) if len(sub) else None,
       "hour_liq_below_1000_pct":float(100*(sub.liq_h<1000).mean()) if len(sub) else None,
       "hour_liq_below_5000_pct":float(100*(sub.liq_h<5000).mean()) if len(sub) else None,
       "hour_liq_below_10000_pct":float(100*(sub.liq_h<10000).mean()) if len(sub) else None,
       "price_fall_50pct":float(100*sub.collapse_price.mean()) if len(sub) else None,
       "liquidity_fall_80pct":float(100*sub.collapse_liquidity.mean()) if len(sub) else None,
       "upside_20pct_count":int(sub.upside20.sum()),
       "upside_20pct_rate":float(100*sub.upside20.mean()) if len(sub) else None,
       "median_price_return_pct":float(100*(sub.price_ratio.median()-1)) if len(sub) else None}
def main():
    df,q=a.sample()
    (tr,va,te),split=a.split(df)
    yl=make(tr,va,te,"collapse_liquidity",a.BASE)
    yp=make(tr,va,te,"collapse_price",a.BASE)
    masks={"all":np.ones(len(te),dtype=bool),"liquidity_shield":yl,
          "price_shield":yp,"both_shields":(yl&yp),
          "liquid_1000plus":te.liq_s.to_numpy()>=1000,
          "liquid_5000plus":te.liq_s.to_numpy()>=5000,
          "liquid_10000plus":te.liq_s.to_numpy()>=10000}
    out={"study":"DIGUI-010-C","caution":"Exploratory post-hoc analysis; same reused four-day holdout, never independent confirmation",
         "source_revision":a.REV,"sample_n":len(te),"results":{},"quartiles":[],
         "thresholds":"70% accept calibrated validation only; fixed absolute $1k,$5k,$10k","orders_sent":0,
         "economic_gate":"NO-GO: liquidity TVL is not executable quote depth"}
    for key,mask in masks.items():
        out["results"][key]=eval(te,mask)
        print("POOL_RISK",key,json.dumps(out["results"][key]),flush=True)
    qs=np.quantile(va.liq_s,[0,.25,.5,.75,1])
    qs[0]=0;qs[-1]=float("inf")
    for i in range(4):
        mask=(te.liq_s>=qs[i])&(te.liq_s<qs[i+1])
        v=eval(te,mask)
        v["validation_quartile"]=i+1
        v["validation_bounds_usd"]=[float(qs[i]),float(qs[i+1]) if np.isfinite(qs[i+1]) else "inf"]
        out["quartiles"].append(v)
    print("START_LIQ_QUARTILES",json.dumps(out["quartiles"]),flush=True)
    path=Path("digui010-evidence/absolute_liquidity_adversarial.json")
    path.write_text(json.dumps(out,indent=2,ensure_ascii=False))
    print("ABSOLUTE_EXIT_VERDICT",json.dumps({"results":out["results"],"status":"ECONOMIC NO-GO"}),flush=True)
if __name__=="__main__":main()
