#!/usr/bin/env python3
"""
BTC-CONVEX-TREND-CAPTURE-001 — ENTRY PULLBACK DIAGNOSTIC V0.2

POST-HOC FORENSIC ONLY.
Built after V0.1 showed bullish long-horizon state + bearish short-horizon state.
ZERO scientific/promotion credit. No parameter tuning is authorized from this output.
"""
from pathlib import Path
import bisect, json, math, statistics

LAB=Path(__file__).resolve().parent
v1=LAB/"entry_fingerprint_probe_v0_1.py"
src=v1.read_text(encoding="utf-8")
prefix=src.split('result={"lab"')[0]
ns={"__file__":str(v1)}
exec(prefix,ns)

rows=ns["rows"]; load_tf=ns["load_tf"]; build_features=ns["build_features"]; ema=ns["ema"]; rsi=ns["rsi"]
EVID=LAB/"evidence"

def features_v2(d):
    cl=d["close"]; hi=d["high"]; lo=d["low"]
    e9=ema(cl,9); e20=ema(cl,20); e50=ema(cl,50)
    rs=rsi(cl,14)
    out=[]
    for i in range(len(cl)):
        f=d["features"][i]; p=d["features"][i-1] if i else {}
        z={}
        z["macd_below_signal"]=not f["macd_gt_signal"]
        z["rsi14_le_50"]=not f["rsi14_gt_50"]
        z["momentum20_nonpos"]=not f["momentum20_pos"]
        z["ema9_le_21"]=not f["ema9_gt_21"]
        z["supertrend_not_long"]=not f["supertrend10x3_long"]
        z["pullback_core_A"]=f["ema20_gt_50"] and z["macd_below_signal"] and z["rsi14_le_50"] and z["momentum20_nonpos"]
        z["pullback_core_B"]=f["ema50_gt_200"] and z["pullback_core_A"]
        z["pullback_core_C"]=f["ema20_gt_50"] and z["ema9_le_21"] and z["macd_below_signal"] and z["rsi14_le_50"]
        z["close_below_ema9"]=cl[i]<e9[i]
        z["close_below_ema20"]=cl[i]<e20[i]
        z["close_below_ema20_above_ema50"]=cl[i]<e20[i] and cl[i]>e50[i]
        z["ema20_touch_reclaim"]=lo[i]<=e20[i] and cl[i]>=e20[i]
        z["ema50_touch_reclaim"]=lo[i]<=e50[i] and cl[i]>=e50[i]
        z["rsi14_lt_40"]=rs[i] is not None and rs[i]<40
        z["rsi14_lt_30"]=rs[i] is not None and rs[i]<30
        if i:
            z["macd_cross_down"]=(not f["macd_gt_signal"]) and p.get("macd_gt_signal",False)
            z["rsi_cross_50_down"]=(not f["rsi14_gt_50"]) and p.get("rsi14_gt_50",False)
            z["ema9_cross_21_down"]=(not f["ema9_gt_21"]) and p.get("ema9_gt_21",False)
            z["momentum20_turn_nonpos"]=(not f["momentum20_pos"]) and p.get("momentum20_pos",False)
            z["close_cross_below_ema20"]=cl[i]<e20[i] and cl[i-1]>=e20[i-1]
            z["close_cross_below_ema9"]=cl[i]<e9[i] and cl[i-1]>=e9[i-1]
        else:
            for k in ["macd_cross_down","rsi_cross_50_down","ema9_cross_21_down","momentum20_turn_nonpos","close_cross_below_ema20","close_cross_below_ema9"]: z[k]=False
        out.append(z)
    return out

CONDS=[
"macd_below_signal","rsi14_le_50","momentum20_nonpos","ema9_le_21","supertrend_not_long",
"pullback_core_A","pullback_core_B","pullback_core_C",
"close_below_ema9","close_below_ema20","close_below_ema20_above_ema50",
"ema20_touch_reclaim","ema50_touch_reclaim","rsi14_lt_40","rsi14_lt_30",
"macd_cross_down","rsi_cross_50_down","ema9_cross_21_down","momentum20_turn_nonpos",
"close_cross_below_ema20","close_cross_below_ema9"
]

out={"lab":"BTC-CONVEX-TREND-CAPTURE-001","probe":"ENTRY_PULLBACK_DIAGNOSTIC_V0.2",
     "role":"POST_HOC_FORENSIC_ONLY","promotion_credit":0,"conditions":CONDS,"timeframes":{}}

for tf in ["5m","15m","4h"]:
    bars,fail=load_tf(tf); d=build_features(bars); v2=features_v2(d); idx={t:i for i,t in enumerate(d["ts"])}
    trades=sorted([r for r in rows if r["timeframe"]==tf],key=lambda r:r["trade_no"])
    ec={k:0 for k in CONDS}; cc={k:0 for k in CONDS}; n=0; cn=0
    samebar=[]
    prev_exit=None
    for tr in trades:
        i=idx.get(tr["entry_ms"])
        is_same=prev_exit is not None and tr["entry_ms"]==prev_exit
        if i is not None and i>0:
            n+=1
            for k in CONDS: ec[k]+=int(v2[i-1][k])
            if is_same:
                vals={"open":d["open"][i],"high":d["high"][i],"low":d["low"][i],"close":d["close"][i]}
                dist={k:abs(tr["entry_price"]/p-1)*10000 for k,p in vals.items()}
                nearest=min(dist,key=dist.get)
                samebar.append({"trade_no":tr["trade_no"],"entry_dt":tr["entry_dt"],"entry_price":tr["entry_price"],
                                "ohlc":vals,"nearest_ohlc":nearest,"nearest_bps":dist[nearest],"all_bps":dist})
        prev_exit=tr["exit_ms"]

    for j in range(1,len(trades)):
        px=trades[j-1]["exit_ms"]; en=trades[j]["entry_ms"]
        if px is None or en is None or en<=px: continue
        a=bisect.bisect_right(d["ts"],px); b=bisect.bisect_left(d["ts"],en)
        for fill_i in range(a,b):
            si=fill_i-1
            if si<0: continue
            cn+=1
            for k in CONDS: cc[k]+=int(v2[si][k])

    table=[]
    for k in CONDS:
        er=ec[k]/n if n else 0; cr=cc[k]/cn if cn else 0
        lift=er/cr if cr else (999 if er else 0)
        table.append({"condition":k,"entry_recall":er,"flat_control_rate":cr,"lift":lift})
    table.sort(key=lambda x:(x["entry_recall"]*math.log10(1+x["lift"])),reverse=True)
    out["timeframes"][tf]={"matched_entries":n,"flat_controls":cn,"source_failures":fail,
                            "condition_table":table,"same_bar_reentries":samebar}

path=EVID/"ENTRY_PULLBACK_DIAGNOSTIC_V0.2.json"
path.write_text(json.dumps(out,indent=2),encoding="utf-8")
for tf,v in out["timeframes"].items():
    print("\n==",tf,"== matched",v["matched_entries"],"controls",v["flat_controls"])
    for x in v["condition_table"][:12]:
        print(x["condition"],"recall",round(x["entry_recall"],3),"control",round(x["flat_control_rate"],3),"lift",round(x["lift"],2))
    if v["same_bar_reentries"]:
        from collections import Counter
        c=Counter(x["nearest_ohlc"] for x in v["same_bar_reentries"])
        print("same-bar nearest OHLC",dict(c))
        print("within1bp",sum(x["nearest_bps"]<=1 for x in v["same_bar_reentries"]),"/",len(v["same_bar_reentries"]))
print("WROTE",path)
