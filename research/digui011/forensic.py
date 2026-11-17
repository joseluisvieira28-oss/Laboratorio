#!/usr/bin/env python3
"""DIGUI-011-B: POST-HOC adversarial examination of previously observed top 4h breakouts.
Must not be mistaken for independent confirmation; test dates are reused.
"""
from pathlib import Path
import numpy as np
import pandas as pd
import json,hashlib
R=Path("digui011-evidence")
MODELS=("ETH_4h_breakout_2bps","SOL_4h_breakout_2bps")
OUT=R/"adversarial.json"

def analyse(d,coin):
    x=d[(d.coin==coin)&(d.frame_h==4)&(d.strategy=="breakout")&
        (d.slippage_bps==2)&(d.phase=="test")].copy()
    if len(x)<40:raise ValueError("Missing final test trades")
    x["month"]=pd.to_datetime(x.entry_ms,unit="ms",utc=True).dt.strftime("%Y-%m")
    y=x.net_return.to_numpy(float)*10000
    months=sorted(x.month.unique())
    if len(months)!=16:raise ValueError("Unexpected month count")
    group=[x.loc[x.month==m,"net_return"].to_numpy(float)*10000 for m in months]
    rng=np.random.default_rng(20261117)
    stats=[]
    for _ in range(5000):
        ix=rng.integers(0,len(months),size=len(months))
        part=np.concatenate([group[int(z)] for z in ix])
        stats.append(float(part.mean()))
    stats=np.array(stats)
    robust=y.sum()-sum(sorted(y,reverse=True)[:5])
    return {"n":len(x),"mean_net_bps":float(np.mean(y)),
      "median_net_bps":float(np.median(y)),
      "sum_net_bps_per_1_fixed_notional":float(y.sum()),
      "sum_top5_positive_bps":float(sum(sorted(y,reverse=True)[:5])),
      "sum_without_top5_bps":float(robust),
      "mean_without_top5_bps":float(robust/(len(y)-5)),
      "positive_months":int(sum(np.sum(g)>0 for g in group)),
      "total_months":len(months),
      "bootstrap_month_block_95pct_ci_mean_bps":list(map(float,np.quantile(stats,[.025,.975]))),
      "bootstrap_fraction_mean_above_zero":float(np.mean(stats>0)),
      "test_reused_post_hoc":True,
      "last_months":{m:float(sum(g)) for m,g in zip(months,group)},
      "stop_rate_pct":float(100*np.mean(x.reason=="stop")),
      "funding_total_bps":float(10000*x.funding_return.sum()),
      "fee_total_bps":float(10000*x.fee_return.sum())}

def main():
    x=json.loads((R/"backtest.json").read_text())
    m=json.loads((R/"source_manifest.json").read_text())
    if hashlib.sha256((R/"ohlcv_1h.csv").read_bytes()).hexdigest()!=m["csv_sha256"]:
        raise ValueError("SOURCE SHA changed")
    df=pd.read_csv(R/"trades.csv")
    rows=x["test_report"]
    winners=[k for k,v in rows.items() if v["test"].get("mean_net_bps",0)>0]
    replicated=[k for k,v in rows.items() if v["test"].get("mean_net_bps",0)>0 and
                v["validation"].get("mean_net_bps",0)>0 and v["slippage_stress_test"].get("mean_net_bps",0)>0 and
                v["test"].get("n",0)>=100]
    if set(winners)!={*MODELS}:raise ValueError("Unexpected positive model set; audit freeze needs update")
    d={"study":"DIGUI-011-B","POST_HOC":True,
       "warning":"After observing 24 final-test variants; does not make hypothesis independent",
       "positive_final_models":winners,"replicated_validation_test_with_100_trades":replicated,
       "all_24_tested":len(rows),"interpretation":"NO-GO, unstable post-hoc outliers",
       "winners":{coin:analyse(df,coin) for coin in ("ETH","SOL")},
       "no_trades":True,"no_live_go":True}
    raw=json.dumps(d,indent=2,ensure_ascii=False).encode()
    OUT.write_bytes(raw)
    (R/"adversarial.sha256").write_text(hashlib.sha256(raw).hexdigest()+"  adversarial.json\n")
    print("ADVERSARIAL_DIGUI011",json.dumps(d,ensure_ascii=False)[:16000],flush=True)
if __name__=="__main__":main()
