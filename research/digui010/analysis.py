#!/usr/bin/env python3
"""DIGUI-010: frozen, read-only, cost-free 1m->1h liquidity/price LOSS AVOIDANCE test.
Pumpswap pool quoted snapshots, not executable trade fills. 2026-11-17 v0.1.
"""
from pathlib import Path
from huggingface_hub import hf_hub_download
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.metrics import average_precision_score, roc_auc_score, brier_score_loss
import duckdb, numpy as np, pandas as pd, json, hashlib
REPO="Slinky21/Pumpfun_Memecoin_Corpus"
REV="13bec2bf3089d56d50c35e602616d1b993bb37f5"
EXPECTED={"postgard_snapshots.parquet":"34a63b8333a41b3cc84d05461febe725cf37842fa0e21d6ea00472dcdcfa1e72",
          "migrations.parquet":"ef5d5141fd94acbcd121bed50e39e525cf7777d25338fc9852a67fd8a085105d"}
OUT=Path("digui010-evidence");OUT.mkdir(exist_ok=True)
BASE=["log_liq","log_price","log_volume","tx5m"]
EXTRA=["price_momentum_early","liq_momentum_early","buy_sell_pressure"]
N_TRAIN=.50
N_VALID=.25
EMBARGO_H=1

def get(name):
    p=Path(hf_hub_download(REPO,name,repo_type="dataset",revision=REV))
    sha=hashlib.sha256(p.read_bytes()).hexdigest()
    assert sha==EXPECTED[name],f"source hash mismatch {name}"
    return p

def sample():
    path=get("postgard_snapshots.parquet")
    mig=get("migrations.parquet")
    con=duckdb.connect()
    con.read_parquet(str(path)).create_view("ss")
    con.read_parquet(str(mig)).create_view("mm")
    # Only pumpswap with independently measured USD liquidity and price.
    # Raw "price_change_*" and outcome/rug labels are categorically EXCLUDED as features.
    sql="""WITH valid AS (
       SELECT mint,pair_address,snapshot_time,seconds_since_graduation sec,
          liquidity_usd liq, price_usd px,
          volume_5m vol5,buys_5m buys,sells_5m sells
       FROM ss
       WHERE dex_id='pumpswap'
         AND NOT COALESCE(incomplete_data,TRUE)
         AND seconds_since_graduation BETWEEN 0 AND 3900
         AND liquidity_usd>0 AND price_usd>0
    ),
    x AS (
       SELECT mint,
        arg_min(pair_address,abs(sec-90)) FILTER(WHERE sec BETWEEN 60 AND 150) pair_s,
        arg_min(pair_address,abs(sec-3600)) FILTER(WHERE sec BETWEEN 3300 AND 3900) pair_h,
        arg_min(snapshot_time,abs(sec-90)) FILTER(WHERE sec BETWEEN 60 AND 150) stamp_s,
        arg_min(snapshot_time,abs(sec-3600)) FILTER(WHERE sec BETWEEN 3300 AND 3900) stamp_h,
        arg_min(sec,abs(sec-90)) FILTER(WHERE sec BETWEEN 60 AND 150) sec_s,
        arg_min(sec,abs(sec-3600)) FILTER(WHERE sec BETWEEN 3300 AND 3900) sec_h,
        arg_min(liq,abs(sec-90)) FILTER(WHERE sec BETWEEN 60 AND 150) liq_s,
        arg_min(px,abs(sec-90)) FILTER(WHERE sec BETWEEN 60 AND 150) px_s,
        arg_min(vol5,abs(sec-90)) FILTER(WHERE sec BETWEEN 60 AND 150) vol_s,
        arg_min(buys,abs(sec-90)) FILTER(WHERE sec BETWEEN 60 AND 150) buys_s,
        arg_min(sells,abs(sec-90)) FILTER(WHERE sec BETWEEN 60 AND 150) sells_s,
        arg_min(liq,sec) FILTER(WHERE sec BETWEEN 0 AND 60) liq_early,
        arg_min(px,sec) FILTER(WHERE sec BETWEEN 0 AND 60) px_early,
        arg_min(liq,abs(sec-3600)) FILTER(WHERE sec BETWEEN 3300 AND 3900) liq_h,
        arg_min(px,abs(sec-3600)) FILTER(WHERE sec BETWEEN 3300 AND 3900) px_h
       FROM valid
       GROUP BY mint
    ) SELECT x.*,m.migrated_at
    FROM x LEFT JOIN mm m USING(mint)"""
    df=con.sql(sql).df()
    con.close()
    total=len(df)
    before=df.notna().sum()
    df=df.dropna(subset=["stamp_s","stamp_h","migrated_at","liq_s","liq_h","px_s","px_h","pair_s","pair_h"])
    paired=len(df)
    same=df.pair_s.eq(df.pair_h)
    df=df.loc[same].copy()
    df["stamp_s"]=pd.to_datetime(df.stamp_s,utc=True)
    df["stamp_h"]=pd.to_datetime(df.stamp_h,utc=True)
    df["migrated_at"]=pd.to_datetime(df.migrated_at,utc=True)
    df["asof_delta_s"]=(df.stamp_s-df.migrated_at).dt.total_seconds()-df.sec_s
    df["outcome_delta_s"]=(df.stamp_h-df.migrated_at).dt.total_seconds()-df.sec_h
    median_abs_asof=float(df.asof_delta_s.abs().median())
    median_abs_outcome=float(df.outcome_delta_s.abs().median())
    # Timestamps have to agree with the independent migration event, not just each other.
    time_ok=(df.asof_delta_s.abs()<=60)&(df.outcome_delta_s.abs()<=60)
    before_time=len(df)
    df=df.loc[time_ok].copy()
    # Exclude outcome windows with accidental crossover of survey timestamps.
    df=df.loc[df.stamp_h>df.stamp_s].copy()
    df["liquidity_ratio"]=df.liq_h/df.liq_s
    df["price_ratio"]=df.px_h/df.px_s
    df["collapse_liquidity"]=(df.liquidity_ratio<=0.2).astype(int)
    df["collapse_price"]=(df.price_ratio<=0.5).astype(int)
    df["risk"]=(df.collapse_liquidity.astype(bool)|df.collapse_price.astype(bool)).astype(int)
    df["upside20"]=(df.price_ratio>=1.2).astype(int)
    df["log_liq"]=np.log1p(df.liq_s)
    df["log_price"]=np.log(df.px_s)
    df["log_volume"]=np.log1p(df.vol_s.clip(lower=0))
    df["tx5m"]=df.buys_s.fillna(0).clip(lower=0)+df.sells_s.fillna(0).clip(lower=0)
    df["price_momentum_early"]=np.log((df.px_s/df.px_early).where(df.px_early>0)).clip(-10,10)
    df["liq_momentum_early"]=np.log((df.liq_s/df.liq_early).where(df.liq_early>0)).clip(-10,10)
    df["buy_sell_pressure"]=(df.buys_s-df.sells_s)/(df.tx5m.replace(0,np.nan))
    for col in BASE+EXTRA:
        df[col]=pd.to_numeric(df[col],errors="coerce")
        df[col]=df[col].replace([np.inf,-np.inf],np.nan)
    quality={"total_distinct_pumpswap_mints_with_any_observation":total,
       "with_both_1m_1h_liq_and_price":paired,
       "same_pool_count":before_time,
       "time_valid_count":len(df),
       "median_abs_migration_residual_signal_sec":median_abs_asof,
       "median_abs_migration_residual_1h_sec":median_abs_outcome,
       "time_rejected":before_time-len(df),
       "liq_collapse_rate":float(df.collapse_liquidity.mean()) if len(df) else None,
       "price_collapse_rate":float(df.collapse_price.mean()) if len(df) else None,
       "combined_risk_rate":float(df.risk.mean()) if len(df) else None,
       "missing_initial_momentum":float(df.price_momentum_early.isna().mean()) if len(df) else None}
    return df,quality

def split(df):
    df=df.sort_values("migrated_at").reset_index(drop=True)
    q1=df.migrated_at.iloc[int(len(df)*N_TRAIN)]
    q2=df.migrated_at.iloc[int(len(df)*(N_TRAIN+N_VALID))]
    gap=pd.Timedelta(hours=EMBARGO_H)
    tr=df[df.migrated_at<q1-gap].copy()
    va=df[(df.migrated_at>=q1)&(df.migrated_at<q2-gap)].copy()
    te=df[df.migrated_at>=q2].copy()
    return (tr,va,te),{"train_cut":str(q1),"test_cut":str(q2),"embargo_hours":1,
        "folds":{k:{"n":len(v),"days":int(v.migrated_at.dt.date.nunique()),
            "start":str(v.migrated_at.min()),"end":str(v.migrated_at.max()),
            "risk":float(v.risk.mean()) if len(v) else None,
            "liq_collapse":float(v.collapse_liquidity.mean()) if len(v) else None}
            for k,v in [("train",tr),("validation",va),("test",te)]}}

def predict(tr,va,te,cols):
    # Single predeclared model, no hyperparameter tuning on test.
    m=HistGradientBoostingClassifier(max_iter=60,max_leaf_nodes=7,
        max_depth=3,min_samples_leaf=35,learning_rate=.06,l2_regularization=5,
        random_state=17,early_stopping=False)
    m.fit(tr[cols].to_numpy(float),tr.risk)
    return m.predict_proba(va[cols].to_numpy(float))[:,1],m.predict_proba(te[cols].to_numpy(float))[:,1]

def metric(y,p):
    y=np.asarray(y);p=np.asarray(p)
    return {"n":len(y),"positives":int(y.sum()),"prev":float(y.mean()),
       "average_precision":float(average_precision_score(y,p)),
       "auc":float(roc_auc_score(y,p)) if y.nunique()>1 else None,
       "brier":float(brier_score_loss(y,p))}

def policy(test,score,threshold,accept_if,desc):
    accept=(score<=threshold) if accept_if=="low" else (score>=threshold)
    kept=test.loc[accept].copy()
    rej=test.loc[~accept].copy()
    return {"description":desc,"accepted":len(kept),"rejected":len(rej),
       "retention_rate":float(len(kept)/len(test)),
       "base_risk_rate":float(test.risk.mean()),
       "retained_risk_rate":float(kept.risk.mean()) if len(kept) else None,
       "rejected_risk_rate":float(rej.risk.mean()) if len(rej) else None,
       "retained_liq_collapse_rate":float(kept.collapse_liquidity.mean()) if len(kept) else None,
       "retained_price_collapse_rate":float(kept.collapse_price.mean()) if len(kept) else None,
       "retained_upside_rate":float(kept.upside20.mean()) if len(kept) else None,
       "upside_opportunities_rejected":int(rej.upside20.sum()),
       "all_upside_opportunities":int(test.upside20.sum()),
       "conditional_median_price_return_pct":float(100*(kept.price_ratio.median()-1)) if len(kept) else None,
       "conditional_median_liquidity_change_pct":float(100*(kept.liquidity_ratio.median()-1)) if len(kept) else None}

def main():
    df,quality=sample()
    (tr,va,te),spl=split(df)
    print("QUALITY",json.dumps(quality,default=str),flush=True)
    print("FOLDS",json.dumps(spl,default=str),flush=True)
    out={"study":"DIGUI-010","source_revision":REV,"quality":quality,"splits":spl,
       "risk_definition":"price -50% OR liquidity -80% between observed 1m and ~1h",
       "control":"No filter (all)","models":{},"policies":{},"economic_gate":"NO-GO: quotes are NOT fills","orders_sent":0}
    if min(len(tr),len(va),len(te))<150 or min([tr.risk.sum(),va.risk.sum(),te.risk.sum()])<15:
        out["conclusion"]="INCONCLUSIVE: insufficient temporally paired data or positives"
    else:
        models={"market_level":BASE,"market_plus_early_changes":BASE+EXTRA}
        for name,cols in models.items():
            pval,ptest=predict(tr,va,te,cols)
            out["models"][name]={"validation":metric(va.risk,pval),"test":metric(te.risk,ptest),"features":cols}
            cutoff=float(np.quantile(pval,.70)) # retain ~70% of least-risk validation tokens
            out["policies"][name]=policy(te,ptest,cutoff,"low",name+" risk score <= validation 70th percentile")
            print("MODEL",name,json.dumps(out["models"][name],default=str),flush=True)
        liq_cut=float(np.quantile(va.liq_s,.30))
        out["policies"]["liquidity_only"]=policy(te,te.liq_s.to_numpy(float),liq_cut,"high","signal liquidity >= validation 30th percentile")
        # Predefined low liquidity screen without model selection
        out["policies"]["no_filter"]={"n":len(te),"risk_rate":float(te.risk.mean()),
            "price_collapse_rate":float(te.collapse_price.mean()),
            "liq_collapse_rate":float(te.collapse_liquidity.mean()),
            "upside_rate":float(te.upside20.mean()),"median_price_return_pct":float(100*(te.price_ratio.median()-1))}
        for name,v in out["policies"].items():
            print("POLICY",name,json.dumps(v,default=str),flush=True)
        out["conclusion"]="HISTORICAL ASSOCIATION ONLY; no proof of economic edge or execution"
        if spl["folds"]["test"]["days"]<7:out["conclusion"]="INCONCLUSIVE temporal stability: <7 distinct days in final test"
    out["limits"]=[
      "Only graduated tokens with complete 1m and 1h PumpSwap pool quotes; strong selection and censoring",
      "Pumpfun rows have structurally missing USD liquidity and are never silently scored as safe",
      "One-hour outcome is nearest observed 3300-3900s, not a continuous drawdown curve",
      "Snapshot liquidity is not guaranteed executable exit depth; no wallets or trades",
      "Risk filter may reject winners: upside lost is explicitly counted",
      "No per-quote live source delivery latency proven; historical timestamps only",
      "One 39-day regime, with June/July platform and collection breaks",
      "Model tests performed on this existing retrospective sample, not independent prospective proof"]
    raw=json.dumps(out,indent=2,ensure_ascii=False,default=str).encode()
    p=OUT/"risk_study.json";p.write_bytes(raw)
    (OUT/"risk_study.sha256").write_text(hashlib.sha256(raw).hexdigest()+"  risk_study.json\n")
    print("VERDICT",json.dumps({"quality":quality,"splits":spl,"policies":out["policies"],
       "conclusion":out["conclusion"],"economic":out["economic_gate"]},default=str),flush=True)
if __name__=="__main__":main()
