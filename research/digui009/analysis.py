#!/usr/bin/env python3
"""DIGUI-009: adversarial point-in-time trade replay for holder-count hypothesis.
Historical 33.58M-trade corpus. NO transactions, secrets, live orders or market writes.
All trade execution outcomes are print-based sensitivity PROXIES, not actual fills.
"""
import os, time, sys, json, hashlib
from pathlib import Path
import pyarrow as pa
import pyarrow.parquet as pq
import pyarrow.compute as pc
import numpy as np
import pandas as pd
import duckdb
from huggingface_hub import HfApi, HfFileSystem
from sklearn.metrics import average_precision_score
from sklearn.ensemble import HistGradientBoostingClassifier

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"digui008"))
import analysis as prev

REV=prev.REV
DS=prev.DATASET
ROOT=Path("digui009-evidence")
CACHE=Path("digui009-work")
ROOT.mkdir(exist_ok=True); CACHE.mkdir(exist_ok=True)
SYS_PROGRAM="BwWK17cbHxwWBKZkUYvzxLcNQ1YVyaFezduWbtm2de6s"
COLS=["mint","event_time","seconds_since_launch","is_buy","sol_amount","token_amount","user_wallet","price_sol"]
BASE=prev.BASE
COUNT_BASE=["trades_30","buys_30","sells_30","sum_buy_sol_30","sum_sell_sol_30","first_trade_seconds"]
WALLET=["wallets_30","buyers_30"]
ERR=[]

def j(x):
    return json.dumps(x,ensure_ascii=False,default=str)
def safe_float(v):
    try:return float(v)
    except:return None
def replay():
    t0=time.time()
    info=HfApi().repo_info(DS,repo_type="dataset",revision=REV,files_metadata=True)
    shards=sorted([x for x in info.siblings if x.rfilename.startswith("trades/") and x.rfilename.endswith(".parquet")],key=lambda x:x.rfilename)
    if len(shards)!=18:raise RuntimeError("Required all 18 shards; found "+str(len(shards)))
    fs=HfFileSystem()
    status=[]
    for i,item in enumerate(shards):
        out=CACHE/f"early-{i:02}.parquet"
        url=f"datasets/{DS}@{REV}/{item.rfilename}"
        started=time.time()
        with fs.open(url,"rb") as fd:
            pf=pq.ParquetFile(fd)
            writer=None
            observed=0; retained=0; negative=0
            try:
                for batch in pf.iter_batches(batch_size=200000,columns=COLS,use_threads=False):
                    table=pa.Table.from_batches([batch])
                    observed+=len(table)
                    sec=table.column("seconds_since_launch")
                    negative+=int(pc.sum(pc.fill_null(pc.less(sec,0),False)).as_py() or 0)
                    mask=pc.fill_null(pc.and_(pc.greater_equal(sec,0),pc.less_equal(sec,900)),False)
                    sub=table.filter(mask)
                    if len(sub)==0:continue
                    retained+=len(sub)
                    if writer is None:writer=pq.ParquetWriter(out,sub.schema,compression="zstd")
                    writer.write_table(sub)
            finally:
                if writer:writer.close()
        status.append({"shard":item.rfilename,"size":item.size,
                       "lfs_sha256":getattr(getattr(item,"lfs",None),"sha256",None),
                       "rows":observed,"kept_le900s":retained,"negative_secs":negative,
                       "elapsed_s":round(time.time()-started,1)})
        print("REPLAY_SHARD",i+1,"/",len(shards),j(status[-1]),flush=True)
    files=list(CACHE.glob("early-*.parquet"))
    if len(files)!=18:raise RuntimeError("Incomplete first 900-second materialization; fail closed")
    print("REPLAY_COMPLETE",j({"shards":len(files),"raw_rows":sum(s["rows"] for s in status),
          "early_rows":sum(s["kept_le900s"] for s in status),"elapsed_s":round(time.time()-t0,1)}),flush=True)
    (ROOT/"source_receipts.json").write_text(j({"revision":REV,"shards":status}),encoding="utf-8")
    return status

def aggregate():
    t0=time.time()
    c=duckdb.connect(str(CACHE/"features.duckdb"))
    c.execute("SET memory_limit='5GB'")
    c.execute("SET threads=2")
    c.execute("SET preserve_insertion_order=false")
    glob=str(CACHE/"early-*.parquet")
    # Source known issues: no public system-program identity as a wallet.
    # SOL amount used only if 0.01 <= sol/(tokens*price) <= 100.
    c.execute(f"""CREATE OR REPLACE TABLE features AS
    WITH e AS (
      SELECT mint, event_time, seconds_since_launch AS sec,
        is_buy, price_sol, user_wallet,
        (user_wallet IS NOT NULL AND user_wallet!='{SYS_PROGRAM}' AND length(user_wallet)>30) AS person_like,
        (price_sol>0 AND token_amount>0 AND sol_amount>0
        AND sol_amount/(token_amount*price_sol) BETWEEN 0.01 AND 100) AS valid_quote,
        sol_amount
      FROM read_parquet('{glob}')
      WHERE seconds_since_launch >= 0 AND seconds_since_launch <= 900
    )
    SELECT mint,
      min(sec) AS first_trade_seconds,
      min(event_time) AS first_trade_time,
      count(*) FILTER (WHERE sec<=30) AS trades_30,
      count(*) FILTER (WHERE sec<=60) AS trades_60,
      count(*) FILTER (WHERE sec<=30 AND is_buy) AS buys_30,
      count(*) FILTER (WHERE sec<=30 AND NOT is_buy) AS sells_30,
      count(DISTINCT user_wallet) FILTER (WHERE sec<=30 AND person_like) AS wallets_30,
      count(DISTINCT user_wallet) FILTER (WHERE sec<=30 AND person_like AND is_buy) AS buyers_30,
      count(DISTINCT user_wallet) FILTER (WHERE sec<=60 AND person_like AND is_buy) AS buyers_60,
      sum(sol_amount) FILTER (WHERE sec<=30 AND is_buy AND valid_quote) AS sum_buy_sol_30,
      sum(sol_amount) FILTER (WHERE sec<=30 AND NOT is_buy AND valid_quote) AS sum_sell_sol_30,
      count(*) FILTER (WHERE sec<=30 AND valid_quote) AS price_usable_30,
      count(*) FILTER (WHERE sec<=30 AND (NOT valid_quote OR valid_quote IS NULL)) AS price_bad_30,
      arg_min(price_sol,sec) FILTER (WHERE sec>=30 AND sec<=120 AND is_buy AND valid_quote AND person_like) AS observed_buy_price_30_120,
      min(sec) FILTER (WHERE sec>=30 AND sec<=120 AND is_buy AND valid_quote AND person_like) AS observed_buy_time,
      arg_min(price_sol,sec) FILTER (WHERE sec>=300 AND sec<=900 AND NOT is_buy AND valid_quote AND person_like) AS observed_sell_price_300_900,
      min(sec) FILTER (WHERE sec>=300 AND sec<=900 AND NOT is_buy AND valid_quote AND person_like) AS observed_sell_time,
      count(*) FILTER (WHERE sec>=30 AND sec<=120 AND is_buy AND valid_quote AND person_like) AS buy_trade_window,
      count(*) FILTER (WHERE sec>=300 AND sec<=900 AND NOT is_buy AND valid_quote AND person_like) AS sell_trade_window
    FROM e
    GROUP BY mint
    """)
    n=c.execute("SELECT count(*) FROM features").fetchone()[0]
    c.execute(f"COPY features TO '{str(CACHE/'features.parquet')}' (FORMAT PARQUET, COMPRESSION ZSTD)")
    print("AGGREGATED",j({"unique_mints_900s":n,"elapsed_s":round(time.time()-t0,1)}),flush=True)
    c.close()
    return n

def f_metrics(y,p):
    return prev.measure(y,p)

def model(tr,te,cols):
    assert not set(cols)&prev.BANNED
    xtr=prev.features(tr,cols)
    xte=prev.features(te,cols)
    m=HistGradientBoostingClassifier(max_iter=90,max_leaf_nodes=15,min_samples_leaf=350,
      learning_rate=.07,l2_regularization=3.,early_stopping=False,random_state=17)
    m.fit(xtr,tr.target.to_numpy())
    p=m.predict_proba(xte)[:,1]
    return f_metrics(te.target,p),p

def metrics():
    folds,quality,filtered=prev.audited_tokens()
    feat=pq.read_table(CACHE/"features.parquet").to_pandas()
    nf=feat.mint.nunique()
    # Null zeros for genuine lack of trades, not for corrupt/missing vendor data.
    data=filtered.merge(feat,on="mint",how="left",validate="one_to_one")
    for col in COUNT_BASE+WALLET+["price_usable_30","price_bad_30"]:
        data[col]=pd.to_numeric(data[col],errors="coerce").fillna(0).astype("float32")
    data["first_trade_seconds"]=data.first_trade_seconds.replace(0,np.nan)
    day=data.detected_at.dt.strftime("%Y-%m-%d")
    test=(data.detected_at>=pd.Timestamp("2026-07-05T00:00Z"))&(data.detected_at<pd.Timestamp("2026-07-12T00:00Z"))
    train=(data.detected_at>=pd.Timestamp("2026-06-05T00:00Z"))&(data.detected_at<pd.Timestamp("2026-06-24T00:00Z"))
    val=(data.detected_at>=pd.Timestamp("2026-06-26T00:00Z"))&(data.detected_at<pd.Timestamp("2026-07-02T00:00Z"))
    tr=data[train].copy();te=data[test].copy();va=data[val].copy()
    if len(te)!=len(folds["test"]) or len(tr)!=len(folds["train"]):raise RuntimeError("Cohort mismatch")
    print("COHORTS",j({"train":len(tr),"val":len(va),"test":len(te),"positive_test":int(te.target.sum())}),flush=True)
    results={}
    preds={}
    cases=[
      ("launch_basic",BASE),
      ("trade_activity_30sec",BASE+COUNT_BASE),
      ("trade_plus_unique_wallets",BASE+COUNT_BASE+WALLET),
      ("historical_vendor_initial_holders_unaudited",BASE+prev.HOLD),
      ("trade_activity_plus_vendor_count_UNAUDITED",BASE+COUNT_BASE+["initial_holder_count"]),
    ]
    for name,cols in cases:
        m,p=model(tr,te,cols)
        results[name]=m
        preds[name]=p
        print("MODEL_ASOF",name,j(m),flush=True)
    # source feature availability and timing
    diag={}
    for name,frame in [("train",tr),("test",te)]:
        vcount=pd.to_numeric(frame.initial_holder_count,errors="coerce")
        earliest=pd.to_numeric(frame.first_trade_seconds,errors="coerce")
        n30=frame.buyers_30
        first=frame.first_trade_time
        delta=(pd.to_datetime(first,utc=True,errors="coerce")-frame.detected_at).dt.total_seconds()
        diag[name]={
            "n":len(frame),
            "first_trade_seen_by_900s_frac":float(earliest.notna().mean()),
            "first_trade_by_30s_frac":float((earliest<=30).mean()),
            "first_trade_after_30s_frac":float((earliest>30).mean()),
            "first_trade_age_when_seen_median_sec":safe_float(earliest.median()),
            "vendor_count_valid_frac":float(vcount.notna().mean()),
            "vendor_count_eq20_frac":float((vcount==20).mean()),
            "vendor_gt_observed_30sec_buyers_frac":float((vcount>n30).mean()),
            "vendor_gt_observed_30sec_buyers_if_trade_30s_frac":float(
                (vcount[frame.trades_30>0]>n30[frame.trades_30>0]).mean()) if (frame.trades_30>0).any() else None,
            "no_buyers_in_30s_frac":float((n30==0).mean()),
            "first_trade_ts_minus_detection_median_s":safe_float(delta.median()),
            "first_trade_ts_minus_detection_minus_source_age_median_s":safe_float((delta-earliest).median()),
            "vendor_count_median_winner":safe_float(vcount[frame.target.eq(1)].median()),
            "vendor_count_median_nonwinner":safe_float(vcount[frame.target.eq(0)].median()),
            "buyers_30_median_winner":safe_float(n30[frame.target.eq(1)].median()),
            "buyers_30_median_nonwinner":safe_float(n30[frame.target.eq(0)].median()),
        }
    print("POINT_IN_TIME_DIAGNOSTIC",j(diag),flush=True)
    # Look for apparent execution after a 30s signal: next observed buy then next sell. Not fills.
    top_pct=0.01
    proxy={}
    for name,p in preds.items():
        top=max(1,int(np.ceil(len(te)*top_pct)))
        selected=te.iloc[np.argsort(-p,kind="stable")[:top]].copy()
        buy=pd.to_numeric(selected.observed_buy_price_30_120,errors="coerce")
        sell=pd.to_numeric(selected.observed_sell_price_300_900,errors="coerce")
        both=(buy>0)&(sell>0)
        pxratio=(sell[both]/buy[both]).to_numpy(dtype=float)
        vals={"sampled_tokens":len(selected),"graduated_48h":int(selected.target.sum()),
              "buy_print_30_120_available":int((buy>0).sum()),
              "sell_print_300_900_available":int((sell>0).sum()),
              "both_prints_available":int(both.sum()),
              "both_prints_fraction":float(both.mean()),
              "only_prints_NOT_FILLED":True}
        for slip in [0.0,0.02,0.05,0.1]:
            cost=0.005
            gross=pxratio*(1-slip)*(1-cost)/((1+slip)*(1+cost))-1
            vals["cost_"+str(int(100*slip))+"pct_slip_per_side"]={
                "n_with_both_prints":len(gross),"median_pct":float(100*np.median(gross)) if len(gross) else None,
                "mean_pct":float(100*np.mean(gross)) if len(gross) else None,
                "p10_pct":float(100*np.quantile(gross,0.1)) if len(gross) else None,
                "share_positive_pct":float(100*np.mean(gross>0)) if len(gross) else None,
                "missing_price_assumed_total_loss_mean_pct":float(
                    100*(np.sum(gross)-(len(selected)-len(gross)))/len(selected))
                    if len(selected) else None}
        proxy[name]=vals
        print("EXECUTION_PROXY_NOT_FILLED",name,j(vals),flush=True)
    out={"source":{"revision":REV,"trade_shards":18,"source_quality_note":"3.38% inconsistent sol_amount, 7.03% NULL price; 19.92% system-program trades"},
         "cohorts":quality["splits"],
         "models":results,"diagnostics":diag,"trading_proxies":proxy,
         "limitations":[
             "The vendor initial holder count is third-party API data without point-in-time per-feature snapshots.",
             "Trade replay only measures wallets that TRANSACTED (not token owners including transfers or pre-mints).",
             "Trades are time-stamped historical prints and not marketable executable quotes/bids.",
             "Treat missing entry or exit print as severe risk; trade path may continue past 900s.",
             "No slippage model verified on-chain; 0.5% fee and slippage scenarios are illustrative.",
             "39-day corpus changes regime materially after Jul 3 outage and after June 20 Mayhem launch.",
             "Same reused Jul5-11 sample; prior discovered strategy reused, not independent confirmation."],
         "economic_gate":"NO-GO until true as-of and transaction execution",
         "orders_sent":0}
    raw=j(out).encode("utf-8")
    (ROOT/"result.json").write_bytes(raw)
    (ROOT/"result.sha256").write_text(hashlib.sha256(raw).hexdigest()+"  result.json\n")
    print("DIGUI009_FINAL",j({"models":results,"quality":diag,"proxies":proxy,"status":"NO-GO"}),flush=True)

if __name__=="__main__":
    start=time.time();replay();aggregate();metrics()
    print("ALL_DONE",round(time.time()-start,1),flush=True)
