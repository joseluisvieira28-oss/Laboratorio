#!/usr/bin/env python3
"""DIGUI-010-B: adverse exploratory test of LIQUIDITY COLLAPSE ALONE.
Post-hoc after main combined-risk results; reused test, NOT independent evidence.
"""
import json
from pathlib import Path
import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.metrics import roc_auc_score,average_precision_score
import analysis as a

def mdl(tr,va,te,cols,target):
    m=HistGradientBoostingClassifier(max_iter=60,max_leaf_nodes=7,max_depth=3,
       min_samples_leaf=35,learning_rate=.06,l2_regularization=5.,
       random_state=17,early_stopping=False)
    m.fit(tr[cols].to_numpy(float),tr[target].to_numpy(int))
    return m.predict_proba(va[cols].to_numpy(float))[:,1],m.predict_proba(te[cols].to_numpy(float))[:,1]

def sm(y,s):
    y=np.asarray(y);s=np.asarray(s)
    return {"ap":float(average_precision_score(y,s)),
        "roc_auc":float(roc_auc_score(y,s)) if len(set(y))>1 else None}
def fate(df,accept):
    kept=df.loc[accept];rejected=df.loc[~accept]
    return {"kept":len(kept),"rejected":len(rejected),
        "kept_liq_collapse_rate":float(kept.collapse_liquidity.mean()) if len(kept) else None,
        "rejected_liq_collapse_rate":float(rejected.collapse_liquidity.mean()) if len(rejected) else None,
        "kept_price_collapse_rate":float(kept.collapse_price.mean()) if len(kept) else None,
        "upside_kept":int(kept.upside20.sum()),"upside_rejected":int(rejected.upside20.sum()),
        "all_upside":int(df.upside20.sum())}
def main():
    df,q=a.sample()
    (tr,va,te),sp=a.split(df)
    out={"study":"DIGUI-010-B","WARNING":"POST-HOC after examining combined-risk test, same test set; NO independent validation",
       "quality":q,"splits":sp,"base_test":{"n":len(te),
         "liq_events":int(te.collapse_liquidity.sum()),
         "price_events":int(te.collapse_price.sum()),
         "upside":int(te.upside20.sum())},
       "models":{},"daily":[],"economics":"NO-GO: observed quotes not fills","orders_sent":0}
    for name,cols in {"market":a.BASE,"market_plus_early":a.BASE+a.EXTRA}.items():
        vp,tp=mdl(tr,va,te,cols,"collapse_liquidity")
        cutoff=float(np.quantile(vp,.70))
        out["models"][name]={"val":sm(va.collapse_liquidity,vp),
            "test":sm(te.collapse_liquidity,tp),"cutoff_from_validation":cutoff,
            "policy":fate(te,tp<=cutoff)}
        print("LIQUIDITY_ONLY",name,json.dumps(out["models"][name]),flush=True)
    for day,grp in te.groupby(te.migrated_at.dt.strftime("%Y-%m-%d")):
        out["daily"].append({"day":day,"n":len(grp),
          "liq_collapse":int(grp.collapse_liquidity.sum()),
          "price_collapse":int(grp.collapse_price.sum()),
          "median_liq_change_pct":float(100*(grp.liquidity_ratio.median()-1)),
          "median_price_change_pct":float(100*(grp.price_ratio.median()-1))})
    print("BY_DAY",json.dumps(out["daily"]),flush=True)
    d=Path("digui010-evidence");d.mkdir(exist_ok=True)
    (d/"liquidity_only_adversarial.json").write_text(json.dumps(out,indent=2))
    print("POSTHOC_COMPLETE",json.dumps({"model":out["models"],"days":len(out["daily"]),"status":"INCONCLUSIVE_ECONOMIC_NO-GO"}),flush=True)
if __name__=="__main__":main()
