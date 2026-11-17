#!/usr/bin/env python3
"""DIGUI-008 full-launch historical graduation & post-graduation audit.
NO orders. No secret keys. NOT live execution PnL. Frozen 17 Nov 2026.
"""
from pathlib import Path
from huggingface_hub import hf_hub_download
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.metrics import average_precision_score, roc_auc_score, brier_score_loss
import numpy as np
import pandas as pd
import pyarrow.parquet as pq
import json, hashlib, time

DATASET="Slinky21/Pumpfun_Memecoin_Corpus"
REV="13bec2bf3089d56d50c35e602616d1b993bb37f5"
SHA={"tokens.parquet":"c005d86d424013e5c78701161b025f3d8c3d472afb61466e0ad6fd5afe9e8ea6",
     "postgard_outcomes.parquet":"00a9980cb97630e9ea89574742f0e134d448e5566c5d7bda461f59bb02de022b"}
OUT=Path("digui008-evidence")
OUT.mkdir(exist_ok=True)
BASE=["initial_buy_sol","initial_price_sol","is_mayhem_mode","is_cashback_enabled","days_since_start","hour_sin","hour_cos"]
HOLD=["initial_holder_count","initial_top10_pct_corrected","initial_gini","dev_buy_pct_corrected"]
UNVERIFIED=["creator_past_tokens","creator_past_rugs"]
BANNED={"graduated_at","seconds_to_graduation","peak_market_cap_sol","peak_market_cap_at",
        "trade_count","is_training_ready","is_zombie","entry_price_usd","entry_price_20s_usd",
        "entry_price_30s_usd","entry_price_1m_usd","tracking_expires_at","data_quality_score",
        "top10_pct_suspect","first_trade_price_sol","launch_snipe_delta_sol"}

def get(name):
    p=Path(hf_hub_download(DATASET,name,repo_type="dataset",revision=REV))
    h=hashlib.sha256()
    with p.open("rb") as fh:
        for chunk in iter(lambda:fh.read(4*1024*1024),b""):h.update(chunk)
    digest=h.hexdigest()
    if digest!=SHA[name]:raise ValueError(f"Source drift {name}: {digest}")
    return p

def measure(y,prob):
    y=np.asarray(y,dtype=int)
    prob=np.asarray(prob,dtype=float)
    n=len(y); pos=int(y.sum()); top=max(1,int(np.ceil(n*.01)))
    order=np.argsort(-prob,kind="stable")[:top]
    out={"n":n,"positive":pos,"prevalence":float(y.mean()),
         "average_precision":float(average_precision_score(y,prob)),
         "top1_precision":float(y[order].mean()),"top1_hits":int(y[order].sum()),
         "top1_count":int(len(order)),
         "brier":float(brier_score_loss(y,prob))}
    out["auc"]=float(roc_auc_score(y,prob)) if y.min()!=y.max() else None
    return out

def features(df,cols):
    assert not set(cols)&BANNED, f"FORBIDDEN feature in model: {set(cols)&BANNED}"
    x=df[cols].apply(pd.to_numeric,errors="coerce").to_numpy(dtype=np.float32)
    x[~np.isfinite(x)]=np.nan
    return x

def trainpredict(train,val,test,cols):
    m=HistGradientBoostingClassifier(max_iter=90,max_leaf_nodes=15,
        min_samples_leaf=350,learning_rate=.07,l2_regularization=3.,
        early_stopping=False,random_state=17)
    t=time.time()
    m.fit(features(train,cols),train.target.to_numpy())
    return m.predict_proba(features(val,cols))[:,1],m.predict_proba(features(test,cols))[:,1],round(time.time()-t,1)

def ftime(s):
    x=pd.to_datetime(s,utc=True,errors="coerce")
    return x

def audited_tokens():
    cols=["mint","detected_at","graduated_at","top10_pct_suspect",
          "initial_buy_sol","initial_price_sol","is_mayhem_mode",
          "is_cashback_enabled","initial_holder_count","initial_top10_pct_corrected",
          "initial_gini","dev_buy_pct_corrected","creator_past_tokens",
          "creator_past_rugs","entry_price_20s_usd"]
    src=pq.read_table(get("tokens.parquet"),columns=cols).to_pandas()
    original=len(src)
    src["detected_at"]=ftime(src.detected_at)
    src["graduated_at"]=ftime(src.graduated_at)
    timeline=src.dropna(subset=["detected_at"]).copy()
    suspect=timeline.top10_pct_suspect.fillna(False).astype(bool)
    invalid=pd.to_numeric(timeline.initial_top10_pct_corrected,errors="coerce")
    invalid=(invalid<0)|(invalid>100)
    filtered=timeline.loc[~suspect & ~invalid].copy()
    filtered=filtered.sort_values("detected_at").drop_duplicates("mint",keep="first")
    # right-censor: final 48h of corpus intentionally excluded
    filtered=filtered.loc[filtered.detected_at<pd.Timestamp("2026-07-12T00:00:00Z")].copy()
    filtered["target"]=(filtered.graduated_at.notna() &
       (filtered.graduated_at>=filtered.detected_at) &
       (filtered.graduated_at<=filtered.detected_at+pd.Timedelta(hours=48))).astype(int)
    # "graduated after 48h" counted as not 48h success by design
    filtered["days_since_start"]=(filtered.detected_at-pd.Timestamp("2026-06-05T00:00:00Z")).dt.total_seconds()/86400
    h=filtered.detected_at.dt.hour+filtered.detected_at.dt.minute/60
    filtered["hour_sin"]=np.sin(2*np.pi*h/24)
    filtered["hour_cos"]=np.cos(2*np.pi*h/24)
    ranges={
      "train":(pd.Timestamp("2026-06-05T00:00Z"),pd.Timestamp("2026-06-24T00:00Z")),
      "validation":(pd.Timestamp("2026-06-26T00:00Z"),pd.Timestamp("2026-07-02T00:00Z")),
      "test":(pd.Timestamp("2026-07-05T00:00Z"),pd.Timestamp("2026-07-12T00:00Z"))}
    folds={k:filtered.loc[(filtered.detected_at>=start)&(filtered.detected_at<end)].copy()
            for k,(start,end) in ranges.items()}
    if min(map(len,folds.values()))<2000:raise ValueError("Not enough rows")
    if any(f.target.sum()<20 for f in folds.values()):raise ValueError("Not enough positive cases")
    quality={"raw_token_rows":original,"non_null_dates":len(timeline),
        "suspect_pct":float(suspect.mean()),"invalid_concentration_count":int(invalid.sum()),
        "filtered_before_split":len(filtered),"all_cohort_graduation_within_48h_rate":float(filtered.target.mean()),
        "splits":{k:{"n":len(f),"positives":int(f.target.sum()),"base_rate":float(f.target.mean()),
                      "date_min":str(f.detected_at.min()),"date_max":str(f.detected_at.max())}
                  for k,f in folds.items()}}
    quality["leak_negative_control"]={}
    for k,f in folds.items():
        leak=f.entry_price_20s_usd.notna()
        quality["leak_negative_control"][k]={
            "entry_price_20s_present_frac_winners":float(leak[f.target==1].mean()),
            "entry_price_20s_present_frac_losers":float(leak[f.target==0].mean())}
    return folds,quality,filtered

def block_bootstrap(fold,p1,p0,n_iter=350):
    d=fold.detected_at.dt.strftime("%Y-%m-%d").to_numpy()
    y=fold.target.to_numpy()
    days=np.unique(d)
    by=[np.where(d==z)[0] for z in days]
    rng=np.random.default_rng(2026)
    diffs=[]
    for _ in range(n_iter):
        idx=np.concatenate([by[j] for j in rng.integers(len(days),size=len(days))])
        if y[idx].sum()<10:continue
        diffs.append(average_precision_score(y[idx],p1[idx])-average_precision_score(y[idx],p0[idx]))
    return {"days":len(days),"delta_ap_95pct_empirical_quantile":
        [float(z) for z in np.quantile(diffs,[.025,.975])],
        "NOTE":"Only seven test days; interval is descriptive, not independent scientific confirmation"}

def risk_and_exit():
    cols=["mint","outcome_label","rug_detected","still_liquid_at_24h",
          "still_liquid_at_48h","price_at_grad_usd","price_at_1m_usd",
          "price_at_5m_usd","price_at_10m_usd","price_at_30m_usd",
          "price_change_1h_pct","price_change_24h_pct"]
    df=pq.read_table(get("postgard_outcomes.parquet"),columns=cols).to_pandas()
    out={"n_outcomes":len(df),"labels":{str(k):int(v) for k,v in df.outcome_label.fillna("MISSING").value_counts().items()}}
    for col in ("rug_detected","still_liquid_at_24h","still_liquid_at_48h"):
        v=df[col]
        out[col]={"nonnull":int(v.notna().sum()),
             "true":int((v==True).sum()),
             "false":int((v==False).sum())}
    for name in ("price_change_1h_pct","price_change_24h_pct"):
        v=pd.to_numeric(df[name],errors="coerce")
        out[name]={"valid":int(v.notna().sum()),"median_pct":float(v.median()),
                    "frac_below_minus80pct":float((v.dropna()<=-80).mean()) if v.notna().any() else None}
    p1=pd.to_numeric(df.price_at_1m_usd,errors="coerce")
    p5=pd.to_numeric(df.price_at_5m_usd,errors="coerce")
    good=(p1>0)&(p5>0)&np.isfinite(p1)&np.isfinite(p5)
    gross=p5[good].to_numpy()/p1[good].to_numpy()
    out["illustrative_1m_to_5m_fixed_exit"]={
      "usable_pairs":int(good.sum()),"eligible_total":len(df),
      "coverage":float(good.mean()),"median_gross_return_pct":float(100*(np.median(gross)-1)),
      "share_price_decrease_pct":float(100*np.mean(gross<1)),
      "NOTE":"Only grads, only observed non-null positive mid-like prices; survivorship/censoring; NOT executable fills"}
    for slip in [0,0.02,0.05,0.10]:
        f=.005  # per side illustrative commissions+priority
        net=gross*((1-f)*(1-slip))/((1+f)*(1+slip))-1
        out["illustrative_1m_to_5m_fixed_exit"][f"hypothetical_slippage_each_side_{int(slip*100)}pct"]={
            "median_net_pct":float(100*np.median(net)),
            "pct_positive":float(100*np.mean(net>0)),
            "bottom_decile_pct":float(100*np.quantile(net,.1))}
    return out

def main():
    folds,quality,all_valid=audited_tokens()
    print("SOURCE",json.dumps({"quality":quality},default=str),flush=True)
    preds={};metrics={}
    for name,cols in [("time_launch_baseline",BASE),("plus_initial_holders",BASE+HOLD),
                      ("plus_creator_unverified",BASE+HOLD+UNVERIFIED)]:
        v,t,secs=trainpredict(folds["train"],folds["validation"],folds["test"],cols)
        preds[name]={"validation":v,"test":t}
        metrics[name]={"validation":measure(folds["validation"].target,v),
                       "test":measure(folds["test"].target,t),
                       "model_seconds":secs,"features":cols,
                       "provenance":"Not proven point-in-time" if name!="time_launch_baseline" else "At or near initial trade (not necessarily executable)"}
        print("METRIC",name,json.dumps(metrics[name]),flush=True)
    test=folds["test"]
    daily={}
    for day, rows in test.groupby(test.detected_at.dt.strftime("%Y-%m-%d")):
        idx=test.index.get_indexer(rows.index)
        daily[day]={"n":len(rows),"positives":int(rows.target.sum()),"base_rate":float(rows.target.mean()),
             "AP":{n:float(average_precision_score(rows.target,v["test"][idx]))
                   for n,v in preds.items()}}
    bootstrap=block_bootstrap(test,preds["plus_initial_holders"]["test"],preds["time_launch_baseline"]["test"])
    risk=risk_and_exit()
    result={"study":"DIGUI-008","source":{"repo":DATASET,"revision":REV,"sha256":SHA},
       "quality":quality,"results":metrics,"per_test_day":daily,
       "bootstrap":bootstrap,"postgraduation":risk,"economic_gate":"NO-GO",
       "limitations":[
        "Independent launch population but only 39 days with documented regime breaks.",
        "Historical initial holder fields may not be reproducible at launch timestamp.",
        "Creator 'past' counts have no verified as-of audit and are exploratory only.",
        "Graduation is not a realizable price return; 48h labels are only observation labels.",
        "Price path conditional on migration is not marketable swap execution.",
        "Trade-level 33.58M source was NOT reprocessed, so fees, fill failures and slippage remain unverified."],
       "orders_sent":0}
    p=OUT/"history_results.json"
    p.write_text(json.dumps(result,indent=2,ensure_ascii=False,default=str))
    print("DIGUI008_RESULT",json.dumps({
        "raw_tokens":quality["raw_token_rows"],
        "splits":quality["splits"],
        "test":{k:v["test"] for k,v in metrics.items()},
        "postgrad":risk,
        "file":str(p),"status":"NO-GO ECONOMIC","orders_sent":0},default=str),flush=True)

if __name__=="__main__":main()
