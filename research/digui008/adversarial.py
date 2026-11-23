#!/usr/bin/env python3
"""DIGUI-008 post-hoc leak/ablation diagnostics, same reused June-July test.
This is NOT independent confirmation and NEVER establishes economic profitability.
"""
from pathlib import Path
import json, time
import numpy as np
import pandas as pd
import analysis as a
from sklearn.ensemble import HistGradientBoostingClassifier

def summary(x):
    s=pd.to_numeric(x,errors="coerce")
    return {"nonnull_pct":float(100*s.notna().mean()),
        "median":float(s.median()) if s.notna().any() else None,
        "q10":float(s.quantile(.1)) if s.notna().any() else None,
        "q90":float(s.quantile(.9)) if s.notna().any() else None,
        "zero_pct":float(100*(s==0).mean())}

def model(train,test,cols):
    m=HistGradientBoostingClassifier(max_iter=90,max_leaf_nodes=15,
        min_samples_leaf=350,learning_rate=.07,l2_regularization=3.,
        early_stopping=False,random_state=17)
    m.fit(a.features(train,cols),train.target)
    p=m.predict_proba(a.features(test,cols))[:,1]
    return m,p

def main():
    folds,quality,_=a.audited_tokens()
    tr,te=folds["train"],folds["test"]
    out={"study":"DIGUI-008-B","WARNING":"Post-hoc after viewing DIGUI-008 first result; the test set is REUSED, not independent evidence",
         "source":{"revision":a.REV,"sha256":a.SHA},"diagnostics":{},"models":{},
         "filters":{}}
    for name,part in [("train",tr),("test",te)]:
        out["diagnostics"][name]={}
        for c in a.HOLD+["initial_buy_sol","first_trade_price_sol"]:
            out["diagnostics"][name][c]={
                "winners":summary(part.loc[part.target==1,c]),
                "non_winners":summary(part.loc[part.target==0,c])}
        out["diagnostics"][name]["first_trade_observed_pct"]=float(
          100*pd.to_numeric(part.first_trade_price_sol,errors="coerce").notna().mean())
    configs={
      "base":a.BASE,
      "base_plus_initial_holder_count":a.BASE+["initial_holder_count"],
      "base_plus_top10_corrected":a.BASE+["initial_top10_pct_corrected"],
      "base_plus_gini":a.BASE+["initial_gini"],
      "base_plus_dev_buy_corrected":a.BASE+["dev_buy_pct_corrected"],
      "base_plus_all_holders":a.BASE+a.HOLD}
    allmodel=None
    for name,cols in configs.items():
        m,p=model(tr,te,cols)
        out["models"][name]=a.measure(te.target,p)
        print("ABLATION",name,json.dumps(out["models"][name]),flush=True)
        if name=="base_plus_all_holders":allmodel=m
    # Diagnose non-null first-trade-only cohort.
    def restrict(df):
        f=pd.to_numeric(df.first_trade_price_sol,errors="coerce")
        h=pd.to_numeric(df.initial_holder_count,errors="coerce")
        c=pd.to_numeric(df.initial_top10_pct_corrected,errors="coerce")
        return df.loc[(f>0)&h.notna()&c.notna()&c.between(0,100)].copy()
    trs,tes=restrict(tr),restrict(te)
    out["filters"]={"train_strict":len(trs),"test_strict":len(tes),
         "train_positive":int(trs.target.sum()),"test_positive":int(tes.target.sum())}
    if len(trs)>5000 and len(tes)>5000 and trs.target.sum()>30:
        for name,cols in [("strict_market",a.BASE),("strict_with_holders",a.BASE+a.HOLD)]:
            m,p=model(trs,tes,cols)
            out["models"][name]=a.measure(tes.target,p)
            print("STRICT",name,json.dumps(out["models"][name]),flush=True)
    # Test-only negative control: joint shuffle of holder fields WITHIN each day.
    # This destroys token-level predictive information while keeping daily cohort mix.
    rand=np.random.default_rng(20261117)
    test_permuted=te.copy()
    indices=test_permuted.groupby(test_permuted.detected_at.dt.strftime("%Y-%m-%d")).indices
    for _,ix in indices.items():
        vals=test_permuted.iloc[ix][a.HOLD].copy().to_numpy()
        test_permuted.iloc[ix,test_permuted.columns.get_indexer(a.HOLD)]=vals[rand.permutation(len(ix))]
    shuffled_probs=allmodel.predict_proba(a.features(test_permuted,a.BASE+a.HOLD))[:,1]
    out["negative_control_within_day_shuffle"]=a.measure(te.target,shuffled_probs)
    # In full corpus, a major data-quality regime shift can trivially mimic predictivity.
    out["test_regime_caution"]={
        "train_base_rate":float(tr.target.mean()),"test_base_rate":float(te.target.mean()),
        "comparison_fold_days":int(te.detected_at.dt.date.nunique()),
        "not_independent_replication":True}
    p=a.OUT/"adversarial_results.json"
    p.write_text(json.dumps(out,indent=2,ensure_ascii=False,default=str))
    print("ADVERSARIAL_RESULT",json.dumps({"results":out["models"],"shuffle":out["negative_control_within_day_shuffle"],
        "strict":out["filters"],"file":str(p),"economic":"NO-GO"}),flush=True)

if __name__=="__main__":main()
