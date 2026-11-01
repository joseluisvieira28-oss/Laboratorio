#!/usr/bin/env python3
"""BTC 10m INTERPRETABLE HISTORICAL MARKET BEHAVIOURAL CONDITION DISCOVERY.
Primary source: official Binance SPOT 1-minute monthly ZIP + matching SHA256 CHECKSUM.
Pre-outcome freeze: BTC10M_BEHAVIOURAL_DISCOVERY_PREOUTCOME_FREEZE_2026_11_01.md.
No Event Futures execution, account calls, capital, protected 2025/2026 outcomes or tuning after 2023 selection.
"""
from __future__ import annotations
import concurrent.futures
import csv
import datetime as dt
import hashlib
import io
import json
import math
import pathlib
import urllib.request
import zipfile
from collections import defaultdict
from datetime import timezone

import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.tree import DecisionTreeClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import brier_score_loss, log_loss

ROOT=pathlib.Path("artifacts/btc10m_behavioural_discovery_v01")
ARCH=pathlib.Path("downloaded/original_source")
MONTHS=[f"{year}-{month:02d}" for year in (2023,2024) for month in range(1,13)]
BASE="https://data.binance.vision/data/spot/monthly/klines/BTCUSDT/1m"
FEATURES=("z1","z3","z5","z10","z30","z60","vol_ratio","taker_share","clv","range1_norm","sigma10_over_sigma60")
CANDIDATES=("LOGIT_P60","TREE_P60","SHOCK_CONT","SHOCK_REVERT","PULLBACK_TREND",
            "SQUEEZE_BREAK","TAKER_SURGE","EXTREME_CLV_REVERT")
TRAIN_END="2023-09-30 23:49:00+00:00"
SELECT_START="2023-10-01 00:00:00+00:00"
SELECT_END="2023-12-31 23:49:00+00:00"
OOS_START="2024-01-01 00:00:00+00:00"
OOS_END="2024-12-31 23:49:00+00:00"
MAX_ZIP=15_000_000
START_UTC=dt.datetime.now(timezone.utc)
SEED=20261101
BOOT_N=2000
def utc():return dt.datetime.now(timezone.utc).isoformat().replace("+00:00","Z")
def digest(x):return hashlib.sha256(x).hexdigest()
class Failed(Exception):pass
def source_url(m):return f"{BASE}/BTCUSDT-1m-{m}.zip"
def fetch_one(m):
    """ONLY original pinned archived ZIP+official CHECKSUM; ZERO HTTP network calls."""
    url=source_url(m)
    path=ARCH/(m+".zip")
    chk=ARCH/(m+".zip.CHECKSUM")
    if not path.is_file() or not chk.is_file():raise Failed("ORIGINAL_PINNED_SOURCE_FILE_MISSING_"+m)
    body=path.read_bytes();check=chk.read_bytes()
    if not body or len(body)>MAX_ZIP:raise Failed("ORIGINAL_PINNED_SOURCE_BYTES_INVALID_"+m)
    parts=check.decode("ascii").strip().split()
    if not parts or len(parts[0])!=64 or not all(t in "0123456789abcdefABCDEF" for t in parts[0]):
        raise Failed("ORIGINAL_CHECKSUM_SYNTAX_"+m)
    if digest(body)!=parts[0].lower():raise Failed("ORIGINAL_PINNED_SHA256_MISMATCH_"+m)
    if not zipfile.is_zipfile(io.BytesIO(body)):raise Failed("ORIGINAL_ZIP_INVALID_"+m)
    return {"month":m,"url":url,"checksum_url":url+".CHECKSUM",
            "pinned_original_github_artifact":13078359511,
            "zip_sha256":digest(body),"official_sha256":parts[0].lower(),
            "zip_bytes":len(body),"read_time_utc":utc(),"fresh_http_calls":0}
def normalize_time(value):
    t=int(value)
    if 10**12<=t<10**14:return t
    if 10**15<=t<10**17 and t%1000==0:return t//1000
    raise Failed("INVALID_TIME_UNITS")
def month_bounds(m):
    start=dt.datetime.strptime(m+"-01","%Y-%m-%d").replace(tzinfo=timezone.utc)
    end=dt.datetime(start.year+(start.month==12),1 if start.month==12 else start.month+1,1,tzinfo=timezone.utc)
    return int(start.timestamp()*1000),int(end.timestamp()*1000)
def parse_month(m,meta):
    raw=(ARCH/(m+".zip")).read_bytes()
    if digest(raw)!=meta["official_sha256"]:raise Failed("ZIP_BYTES_CHANGED")
    with zipfile.ZipFile(io.BytesIO(raw)) as z:
        names=[x for x in z.namelist() if x.endswith(".csv") and "/" not in x]
        if len(names)!=1:raise Failed("ZIP_EXPECT_ONE_CSV_"+m)
        df=pd.read_csv(z.open(names[0]),header=None,usecols=[0,1,2,3,4,7,8,10],
          names=["time_ms","open","high","low","close","quote","ntrades","taker_quote"],
          dtype={"time_ms":"int64","open":"float64","high":"float64","low":"float64",
              "close":"float64","quote":"float64","ntrades":"float64","taker_quote":"float64"},
          low_memory=False)
    first,last=month_bounds(m)
    ts=df["time_ms"].to_numpy(dtype=np.int64)
    if len(ts) and ts[0]>=10**15:
        if np.any(ts%1000):raise Failed("MICRO_TIMESTAMP_NOT_MILLISECOND_ALIGNED_"+m)
        ts=ts//1000
    if not len(ts) or ts[0]<first or ts[-1]>=last or np.any(ts%60000):
        raise Failed("MONTH_TIMESTAMP_BOUNDS_OR_CADENCE_"+m)
    if np.any(np.diff(ts)<=0):raise Failed("OUT_OF_ORDER_OR_DUPLICATE_MINUTE_"+m)
    expected=(last-first)//60000
    missing=expected-len(ts)
    if ts[0]!=first or ts[-1]!=last-60000:raise Failed("SOURCE_MONTH_FIRST_OR_LAST_NOT_EXACT_"+m)
    diffs=np.diff(ts)
    if m=="2023-03":
        if missing!=80 or np.count_nonzero(diffs>60000)!=1 or int(diffs.max())!=81*60000:
            raise Failed("MARCH_2023_PRE_FROZEN_EXACT_80MIN_SINGLE_GAP_NOT_MATCHED")
        first_missing_idx=np.where(diffs>60000)[0][0]
        if int(ts[first_missing_idx])+60000!=1679661600000:
            raise Failed("MARCH_2023_ORIGINAL_TIMESTAMP_GAP_LOCATION_CHANGED")
    elif missing!=0 or np.any(diffs!=60000):
        raise Failed("OTHER_23_SOURCE_MONTHS_NOT_EXACT_100PCT_COVERAGE_"+m)
    vals=df[["open","high","low","close","quote","ntrades","taker_quote"]].to_numpy()
    if not np.all(np.isfinite(vals)):raise Failed("NONFINITE_KLINE_"+m)
    if np.any(df["open"]<=0) or np.any(df["low"]<=0) or np.any(df["close"]<=0):
        raise Failed("NONPOSITIVE_PRICES_"+m)
    if np.any(df["high"]<df["low"]) or np.any(df["high"]+1e-8<df["close"]):
        raise Failed("INVALID_OHLC_"+m)
    if np.any(df["quote"]<0) or np.any(df["taker_quote"]<0) or np.any(df["taker_quote"]>df["quote"]*(1+1e-8)+1e-5):
        raise Failed("INVALID_VOLUME_"+m)
    df["time_ms"]=ts
    df=df.set_index("time_ms")
    return df,{"month":m,"expected_minutes":int(expected),"actual_minutes":int(len(ts)),
        "missing_minutes":int(missing),"completeness":float(len(ts)/expected),
        "first_t_ms":int(ts[0]),"last_t_ms":int(ts[-1])}
def build_ten_minute_features(d):
    """Features for minute B from ONLY closed minutes B-61..B-1. No future candle used."""
    close=d["close"]
    logp=np.log(close)
    logret=logp.diff()
    delayed=logret.shift(1)
    sigma60=np.sqrt(delayed.pow(2).rolling(60,min_periods=60).mean())
    sigma10=np.sqrt(delayed.pow(2).rolling(10,min_periods=10).mean())
    f=pd.DataFrame(index=d.index)
    for k in (1,3,5,10,30,60):
        f["z"+str(k)]=((logp.shift(1)-logp.shift(k+1))/(sigma60*np.sqrt(k))).clip(-10,10)
    q=d["quote"].shift(1)
    q3=q.rolling(3,min_periods=3).sum()
    q60=q.rolling(60,min_periods=60).sum()
    f["vol_ratio"]=(q3/(3*q60/60)).clip(0,20)
    taker=d["taker_quote"].shift(1).rolling(3,min_periods=3).sum()
    f["taker_share"]=taker/q3
    rng=(d["high"]-d["low"])
    f["clv"]=(((d["close"]-d["low"])/rng.replace(0,np.nan)).fillna(.5)).shift(1).clip(0,1)
    f["range1_norm"]=((rng/d["close"]).shift(1)/sigma60).clip(0,20)
    f["sigma10_over_sigma60"]=(sigma10/sigma60).clip(0,20)
    f["spot_open"]=d["open"]
    f["target_spot_open"]=d["open"].shift(-10)
    f["time_ms"]=d.index
    # Build on EXACT 10minute boundaries; 10min outcome windows are non-overlap.
    minutes=(d.index.to_numpy(dtype=np.int64)//60000)%10
    f=f.iloc[np.where(minutes==0)[0]].copy()
    f=f.replace([np.inf,-np.inf],np.nan)
    f=f.dropna(subset=[*FEATURES,"spot_open","target_spot_open"])
    f=f.loc[(f["taker_share"]>=0)&(f["taker_share"]<=1)&(f["spot_open"]>0)&(f["target_spot_open"]>0)]
    f["truth"]=np.where(f["target_spot_open"]>f["spot_open"],1,
              np.where(f["target_spot_open"]<f["spot_open"],-1,0))
    f["date"]=pd.to_datetime(f.index,unit="ms",utc=True).date.astype(str)
    f["month"]=pd.to_datetime(f.index,unit="ms",utc=True).strftime("%Y-%m")
    f["quarter"]=pd.to_datetime(f.index,unit="ms",utc=True).quarter
    return f
def within(frame,start,end):
    st=int(pd.Timestamp(start).timestamp()*1000)
    en=int(pd.Timestamp(end).timestamp()*1000)
    # En is last allowed entry timestamp with target >=? freezed slots require target <= same period.
    return frame.loc[(frame["time_ms"]>=st)&(frame["time_ms"]<=en)].copy()
def candidates(frame,models):
    z1=frame["z1"].to_numpy();z3=frame["z3"].to_numpy();z5=frame["z5"].to_numpy()
    z30=frame["z30"].to_numpy()
    vol=frame["vol_ratio"].to_numpy();take=frame["taker_share"].to_numpy()
    clv=frame["clv"].to_numpy();vol10=frame["sigma10_over_sigma60"].to_numpy()
    side={}
    x=frame[list(FEATURES)].to_numpy(dtype=np.float64)
    probs={}
    for name in ("LOGIT_P60","TREE_P60"):
        mdl,scalar=models[name]
        p=mdl.predict_proba(scalar.transform(x) if scalar is not None else x)[:,1]
        probs[name]=p
        side[name]=np.where(p>=.60,1,np.where(p<=.40,-1,0))
    impulse=(np.abs(z5)>=2)&(vol>=1.5)
    side["SHOCK_CONT"]=np.where(impulse,np.sign(z5),0).astype(np.int8)
    side["SHOCK_REVERT"]=np.where(impulse,-np.sign(z5),0).astype(np.int8)
    side["PULLBACK_TREND"]=np.where((z30>=1)&(z3<=-.7),1,
                                np.where((z30<=-1)&(z3>=.7),-1,0))
    side["SQUEEZE_BREAK"]=np.where((vol10<=.65)&(np.abs(z1)>=.9)&(vol>=1.5),np.sign(z1),0).astype(np.int8)
    side["TAKER_SURGE"]=np.where((take>=.62)&(vol>=1.5),1,
                              np.where((take<=.38)&(vol>=1.5),-1,0))
    side["EXTREME_CLV_REVERT"]=np.where((z5>=1.3)&(clv>=.90)&(vol>=1.3),-1,
                                         np.where((z5<=-1.3)&(clv<=.10)&(vol>=1.3),1,0))
    assert set(side)==set(CANDIDATES)
    return side,probs
def payoff(pred,truth,q):
    return np.where(truth==0,0.0,np.where(pred==truth,q,-1.0))
def daily_lower(rows,q,reference=None,alpha=.025,seed=SEED):
    if rows.empty:return None
    val=payoff(rows["side"].to_numpy(),rows["truth"].to_numpy(),q)
    if reference is not None:
        val=val-payoff(rows[reference].to_numpy(),rows["truth"].to_numpy(),q)
    days=rows["date"].to_numpy()
    u,rev=np.unique(days,return_inverse=True)
    sums=np.bincount(rev,weights=val,minlength=len(u))
    counts=np.bincount(rev,minlength=len(u))
    rng=np.random.default_rng(seed+int(q*1000)+len(rows)+(33 if reference else 0))
    draw=rng.integers(0,len(u),size=(BOOT_N,len(u)))
    boot=sums[draw].sum(axis=1)/counts[draw].sum(axis=1)
    return float(np.quantile(boot,alpha))
def stats(frame,side,name,with_time_slices=False):
    if len(frame)!=len(side):raise Failed("PREDICTION_FRAME_LENGTH_MISMATCH")
    selected=frame.loc[np.asarray(side)!=0,["time_ms","date","month","quarter","truth","spot_open","target_spot_open","z5"]].copy()
    selected["side"]=np.asarray(side)[np.asarray(side)!=0]
    selected["always_up"]=1
    selected["momentum5"]=np.where(selected["z5"]>=0,1,-1)
    n=len(selected)
    w=int((selected["side"]==selected["truth"]).sum())
    tie=int((selected["truth"]==0).sum());lo=n-w-tie
    days=selected["date"].nunique()
    data={"candidate":name,"signal_count":int(n),"non_tie_signals":int(n-tie),
         "wins":w,"losses":int(lo),"ties":tie,
         "distinct_utc_signal_days":int(days),
         "all_evaluable_10m_slots":int(len(frame)),
         "signal_coverage_fraction":float(n/len(frame)) if len(frame) else None,
         "win_rate_non_tie":w/(n-tie) if n>tie else None,
         "up_predictions":int((selected["side"]==1).sum()),
         "down_predictions":int((selected["side"]==-1).sum())}
    for q in (.70,.80,1.):
        prefix="q"+str(q).replace(".","p")
        data["synthetic_payoff_per_stake_"+prefix]=float(payoff(selected["side"].to_numpy(),selected["truth"].to_numpy(),q).mean()) if n else None
        data["daily_boot_lower_97p5_"+prefix]=daily_lower(selected,q) if n else None
        data["always_up_on_same_slots_"+prefix]=float(payoff(selected["always_up"].to_numpy(),selected["truth"].to_numpy(),q).mean()) if n else None
        data["momentum5_on_same_slots_"+prefix]=float(payoff(selected["momentum5"].to_numpy(),selected["truth"].to_numpy(),q).mean()) if n else None
    if with_time_slices:
        data["q070_lower_95_vs_always_up"]=daily_lower(selected,.70,reference="always_up",alpha=.05) if n else None
        data["q070_lower_95_vs_momentum5"]=daily_lower(selected,.70,reference="momentum5",alpha=.05) if n else None
        data["quarters"]=[]
        data["months"]=[]
        for typ,col,labels in (("quarters","quarter",(1,2,3,4)),
                                ("months","month",tuple(sorted(selected["month"].unique())))):
            for label in labels:
                group=selected.loc[selected[col]==label]
                wins_=int((group["side"]==group["truth"]).sum())
                ties_=int((group["truth"]==0).sum());wrong=len(group)-wins_-ties_
                data[typ].append({"period":str(label),"signals":int(len(group)),
                  "wins":wins_,"losses":wrong,"ties":ties_,
                  "synthetic_q070_per_stake":(wins_*.7-wrong)/len(group) if len(group) else None})
        data["positive_2024_quarters_q070"]=sum(v["synthetic_q070_per_stake"] is not None and v["synthetic_q070_per_stake"]>0 for v in data["quarters"])
    return data,selected
def probability_diagnostic(frame,probs):
    truth=frame["truth"].to_numpy()
    binary=truth!=0
    # TIE is excluded from Brier and log loss for direction classification.
    y=(truth[binary]==1).astype(int)
    p=np.clip(probs[binary],1e-8,1-1e-8)
    d={"directional_non_tie_samples":int(len(y)),
       "brier":float(brier_score_loss(y,p)) if len(y) else None,
       "log_loss":float(log_loss(y,p,labels=[0,1])) if len(y) else None,
       "baseline_constant_p05_brier":float(brier_score_loss(y,np.full_like(p,.5))) if len(y) else None,
       "baseline_constant_p05_log_loss":float(log_loss(y,np.full_like(p,.5),labels=[0,1])) if len(y) else None,
       "reliability_bins":[]}
    for i in range(10):
        lo=i/10;hi=(i+1)/10
        m=(p>=lo)&((p<hi) if i<9 else (p<=hi))
        d["reliability_bins"].append({"probability_range":[lo,hi],"count":int(m.sum()),
            "mean_predicted_up":float(p[m].mean()) if m.any() else None,
            "empirical_up_share":float(y[m].mean()) if m.any() else None})
    return d
def unit_tests():
    assert source_url("2023-01").endswith("BTCUSDT-1m-2023-01.zip")
    assert normalize_time("1672531200000")==1672531200000
    assert normalize_time("1735689600000000")==1735689600000
    assert np.array_equal(payoff(np.array([1,1,-1]),np.array([1,-1,0]),.70),np.array([.70,-1.,0.]))
    base=dt.datetime(2023,1,1,tzinfo=timezone.utc)
    ts=(int(base.timestamp()*1000)+np.arange(300)*60000)
    opens=100+np.arange(300)*.01
    test=pd.DataFrame({"open":opens,"high":opens+.05,"low":opens-.05,
        "close":opens+.01,"quote":np.full(300,100.),
        "ntrades":np.full(300,100.),"taker_quote":np.full(300,50.)},index=ts)
    # This is synthetic. Deliberately corrupt candle AT the decision and its future:
    # no computed feature at B should change.
    fx=build_ten_minute_features(test)
    original=fx.loc[ts[100],list(FEATURES)].to_numpy(dtype=float)
    altered=test.copy()
    for key in ("open","high","low","close","quote","ntrades","taker_quote"):
        altered.at[ts[100],key]=1000000.0
    fa=build_ten_minute_features(altered)
    new=fa.loc[ts[100],list(FEATURES)].to_numpy(dtype=float)
    assert np.allclose(original,new,equal_nan=True), "LEAKAGE_FEATURE_HAS_CURRENT_OR_FUTURE_MINUTE"
    # Outcome is open[t+10min] compared with spot open[t].
    assert fx.loc[ts[100],"truth"]==1
def main():
    ROOT.mkdir(parents=True,exist_ok=True);ARCH.mkdir(parents=True,exist_ok=True)
    receipt={"study":"BTC10M_BEHAVIOURAL_DISCOVERY_2023_TRAIN_Q4_SELECTION_2024_OOS_V01",
      "freeze":"research/btc10m_behavioural_v01/BTC10M_BEHAVIOURAL_DISCOVERY_PREOUTCOME_FREEZE_2026_11_01.md",
      "source_only_exception_freeze":"research/btc10m_behavioural_v01/BTC10M_BEHAVIOURAL_80MIN_MARCH_SOURCE_EXCEPTION_PREOUTCOME_V02.md",
      "source_original_run_id":41294978457,"source_original_artifact_id":13078359511,
      "start_utc":utc(),"status":"SOURCE_BLOCKED_FAIL_CLOSED",
      "exact_months":MONTHS,"official_archive_manifest":[],"source_quality":[],
      "candidate_selection_2023Q4":{},"one_selected_2024OOS":None,
      "opened_2025_prices_or_outcomes":False,"opened_2026_prices_or_outcomes":False,
      "private_api_calls":0,"actual_orders":0,"money_spent":0,"main_modified":False,
      "economic_edge_certified":False,"real_event_futures_settlement_parity_proven":False}
    try:
        unit_tests()
        # Resolve only the EXACT 24 already preregistered ZIPs + official checksums.
        manifest={}
        errors=[]
        with concurrent.futures.ThreadPoolExecutor(max_workers=6) as pool:
            futures={pool.submit(fetch_one,m):m for m in MONTHS}
            for future in concurrent.futures.as_completed(futures):
                m=futures[future]
                try:
                    obj=future.result()
                    manifest[m]=obj
                    print("ORIGINAL_ZIP_PASS",m,obj["zip_bytes"],flush=True)
                except Exception as e:
                    errors.append({"month":m,"error":type(e).__name__+":"+str(e)[:160]})
        if errors:raise Failed("OFFICIAL_SOURCE_ERRORS_"+json.dumps(errors)[:1700])
        if set(manifest)!=set(MONTHS):raise Failed("INCOMPLETE_SOURCE_MONTHS")
        receipt["official_archive_manifest"]=[manifest[m] for m in MONTHS]
        dfs=[]
        for m in MONTHS:
            df,quality=parse_month(m,manifest[m])
            dfs.append(df);receipt["source_quality"].append(quality)
            print("SOURCE_CANDLES",m,quality["actual_minutes"],flush=True)
        d=pd.concat(dfs,verify_integrity=True).sort_index()
        del dfs
        # Explicit full UTC minute grid: NaNs for precisely the 80 ORIGINAL missing 2023-03 bars.
        # This is NOT imputation; all rolling 61-minute signals overlapping NaNs abstain.
        full_index=np.arange(int(pd.Timestamp("2023-01-01",tz="UTC").timestamp()*1000),
            int(pd.Timestamp("2025-01-01",tz="UTC").timestamp()*1000),60000,dtype=np.int64)
        if len(full_index)-len(d)!=80:raise Failed("ORIGINAL_REINDEX_MISSING_NOT_EXACTLY_80")
        d=d.reindex(full_index)
        if int(d["open"].isna().sum())!=80:raise Failed("EXPLICIT_MARCH_GAP_NAN_COUNT_NOT_80")
        receipt["nan_gap_source_protocol"]={
            "missing_minutes_original_march_2023":80,
            "missing_first_timestamp_ms":1679661600000,
            "imputation_performed":False,
            "all_source_data_reused_from_original_pinned_artifact":13078359511,
            "fresh_market_http_calls":0}
        f=build_ten_minute_features(d)
        del d
        train=within(f,"2023-01-01 00:00:00+00:00",TRAIN_END)
        select=within(f,SELECT_START,SELECT_END)
        oos=within(f,OOS_START,OOS_END)
        if min(len(train),len(select),len(oos))<=1000:raise Failed("INSUFFICIENT_STRICT_TIME_SPLIT")
        receipt["split_sizes"]={"2023_train":len(train),"2023_q4_selection":len(select),"2024_untouched_oos":len(oos)}
        print("SPLIT_SOURCE_AND_FEATURE_COUNTS_ONLY",json.dumps(receipt["split_sizes"]),flush=True)
        X=train[list(FEATURES)].to_numpy(dtype=float)
        Y=(train["truth"].to_numpy()==1).astype(int)
        mask=train["truth"].to_numpy()!=0
        scaler=StandardScaler().fit(X[mask])
        logistic=LogisticRegression(C=.1,max_iter=200,random_state=SEED,solver="lbfgs").fit(scaler.transform(X[mask]),Y[mask])
        tree=DecisionTreeClassifier(max_depth=3,min_samples_leaf=350,min_samples_split=700,random_state=SEED).fit(X[mask],Y[mask])
        models={"LOGIT_P60":(logistic,scaler),"TREE_P60":(tree,None)}
        # 2023 Q4 ONLY selection; 2024 outcomes remain unopened until selected.
        side_select,probs_select=candidates(select,models)
        info=[]
        for name in CANDIDATES:
            metric,_=stats(select,side_select[name],name)
            info.append(metric)
        eligible=[x for x in info if x["non_tie_signals"]>=100 and x["distinct_utc_signal_days"]>=20]
        receipt["candidate_selection_2023Q4"]={"all_eight_predefined_candidate_metrics":info,
          "eligible_candidates":sorted(x["candidate"] for x in eligible),
          "ranking":"daily q070 bootstrap lower 97.5% -> n desc -> name ascending",
          "q070_payout_not_actual_mexc":True,
          "notes":"Only 2023 Q4 labels used for ranking, NEVER 2024."}
        if eligible:
            eligible.sort(key=lambda x:(-x["daily_boot_lower_97p5_q0p7"],-x["non_tie_signals"],x["candidate"]))
            winner=eligible[0]["candidate"]
            receipt["candidate_selection_2023Q4"]["selected_candidate"]=winner
            receipt["candidate_selection_2023Q4"]["selected_2023Q4_lower_q070"]=eligible[0]["daily_boot_lower_97p5_q0p7"]
            print("PRE_OOS_CANDIDATE_LOCKED",json.dumps({"winner":winner,"selection_metrics":eligible[0]},sort_keys=True),flush=True)
            # NOW, AFTER fixed selection logged, score ONE candidate on untouched chronological 2024.
            if winner in ("LOGIT_P60","TREE_P60"):
                p_model,scalar=models[winner]
                x_oos=oos[list(FEATURES)].to_numpy(dtype=float)
                p=p_model.predict_proba(scalar.transform(x_oos) if scalar is not None else x_oos)[:,1]
                side=np.where(p>=.60,1,np.where(p<=.40,-1,0))
                diag=probability_diagnostic(oos,p)
            else:
                # Construction computes *feature* side arrays for 8 candidates, but does NOT score
                # any 2024 outcome other than frozen winner, and does not print other candidate stats.
                all_oos_side,_=candidates(oos,models)
                side=all_oos_side[winner]
                diag=None
            metric,events=stats(oos,side,winner,with_time_slices=True)
            non=metric["non_tie_signals"]
            good=(non>=300 and metric["distinct_utc_signal_days"]>=20
                and metric["win_rate_non_tie"] is not None and metric["win_rate_non_tie"]>1/1.7
                and metric["daily_boot_lower_97p5_q0p7"]>0
                and metric["q070_lower_95_vs_always_up"]>0
                and metric["q070_lower_95_vs_momentum5"]>0
                and metric["positive_2024_quarters_q070"]>=3)
            if non<300 or metric["distinct_utc_signal_days"]<20:verdict="INSUFFICIENT_2024_OOS_SIGNAL_FREQUENCY"
            elif not good:verdict="2024_OOS_NO_CERTIFIED_DIRECTIONAL_OR_Q070_EDGE"
            else:verdict="2024_OOS_RESEARCH_CANDIDATE_SURVIVES_ONLY_NO_LIVE_GO"
            receipt["one_selected_2024OOS"]={"selected_candidate":winner,
                "metrics":metric,"probability_diagnostics":diag,"verdict":verdict,
                "all_other_candidates_2024_outcomes_tested":False}
            # Save only winning model's event rows as evidence of time and prices.
            with (ROOT/"2024_SELECTED_CANDIDATE_EVENTS.csv").open("w") as file:
                events[["time_ms","date","month","quarter","truth","side","spot_open","target_spot_open","z5"]].to_csv(file,index=False)
            receipt["status"]="2024_OOS_RESEARCH_CANDIDATE_SURVIVES_ONLY" if good else "2024_OOS_NO_EDGE_OR_INSUFFICIENT"
            print("FINAL_SELECTED_2024_OUTCOME",json.dumps({"winner":winner,"metrics":metric,"verdict":verdict},sort_keys=True),flush=True)
        else:
            receipt["status"]="2023_Q4_NO_CANDIDATE_ENOUGH_SIGNAL_FREQUENCY"
            print("SELECTION_NO_CANDIDATE_ELIGIBLE_2024_LABELS_NOT_OPENED",flush=True)
    except Exception as exc:
        receipt["status"]="SOURCE_BLOCKED_FAIL_CLOSED"
        receipt["error"]=type(exc).__name__+":"+str(exc)[:2200]
    finally:
        receipt["finish_utc"]=utc()
        (ROOT/"receipt.json").write_text(json.dumps(receipt,indent=2,sort_keys=True)+"\n",encoding="utf8")
        print("FINAL_STUDY_RECEIPT",json.dumps({
            "status":receipt["status"],"error":receipt.get("error"),
            "selected_candidate":receipt["candidate_selection_2023Q4"].get("selected_candidate"),
            "one_selected_2024OOS":receipt.get("one_selected_2024OOS"),
            "source_archives_passed":len(receipt["official_archive_manifest"])},sort_keys=True),flush=True)
    if receipt["status"]=="SOURCE_BLOCKED_FAIL_CLOSED":raise SystemExit(2)
if __name__=="__main__":main()
