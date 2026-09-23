#!/usr/bin/env python3
"""
BTC-CONVEX-TREND-CAPTURE-001 — EXIT TIMING DIAGNOSTIC V0.3

POST-HOC FORENSIC ONLY / ZERO PROMOTION CREDIT.
Tests whether the observed ~12% peak trail can be explained by:
A) always-active trailing;
B) fixed profit activation thresholds.

It does NOT optimize or propose a tradable rule.
"""
from pathlib import Path
import bisect, json, math

LAB=Path(__file__).resolve().parent
v1=LAB/"entry_fingerprint_probe_v0_1.py"
src=v1.read_text(encoding="utf-8")
prefix=src.split('result={"lab"')[0]
ns={"__file__":str(v1)}
exec(prefix,ns)
rows=ns["rows"]; load_tf=ns["load_tf"]
EVID=LAB/"evidence"

TRAIL=0.12
HARD_STOP=0.04
ACT_THRESHOLDS=[0.05,0.10,0.15,0.17,0.20,0.25,0.30,0.40,0.50]

out={"lab":"BTC-CONVEX-TREND-CAPTURE-001","probe":"EXIT_TIMING_DIAGNOSTIC_V0.3",
     "role":"POST_HOC_FORENSIC_ONLY","promotion_credit":0,
     "hard_stop_pct":HARD_STOP*100,"trail_pct":TRAIL*100,
     "activation_threshold_grid_pct":[x*100 for x in ACT_THRESHOLDS],
     "timeframes":{}}

for tf in ["5m","15m","4h"]:
    bars,fail=load_tf(tf)
    ts=[x[0] for x in bars]; idx={t:i for i,t in enumerate(ts)}
    trades=sorted([r for r in rows if r["timeframe"]==tf and r["exit_ms"] is not None],key=lambda r:r["trade_no"])
    recs=[]
    hard_first_hit_exact=0; hard_losses=0
    always_early=0; always_exact=0; always_late_or_none=0
    threshold_stats={str(int(x*100)):{"exact":0,"early":0,"late_or_none":0,"eligible":0} for x in ACT_THRESHOLDS}

    for tr in trades:
        ei=idx.get(tr["entry_ms"]); xi=idx.get(tr["exit_ms"])
        if ei is None or xi is None or xi<ei: continue
        entry=tr["entry_price"]; exitp=tr["exit_price"]
        segment=bars[ei:xi+1]
        # hard stop: first bar whose low touches entry*0.96
        stop=entry*(1-HARD_STOP)
        first_hard=None
        for j,b in enumerate(segment):
            if b[3] <= stop:
                first_hard=ei+j; break
        is_normal_loss=abs(tr["return_pct"]-(-4.19))<0.03
        if is_normal_loss:
            hard_losses+=1
            if first_hard==xi: hard_first_hit_exact+=1

        # Conservative prior-bar-high trail. Entry bar high initializes after bar;
        # stop on bar j uses running high through j-1, avoiding same-bar path assumptions.
        running_high=segment[0][2]
        first_always=None
        for j in range(1,len(segment)):
            trail_level=running_high*(1-TRAIL)
            if segment[j][3] <= trail_level:
                first_always=ei+j; break
            running_high=max(running_high,segment[j][2])
        if first_always is None or first_always>xi: always_late_or_none+=1
        elif first_always<xi: always_early+=1
        else: always_exact+=1

        act_results={}
        for th in ACT_THRESHOLDS:
            activation_price=entry*(1+th)
            active=False; rh=None; first=None
            # activation uses completed-bar high; stop starts on following bar.
            for j in range(len(segment)):
                b=segment[j]
                if not active:
                    if b[2]>=activation_price:
                        active=True; rh=b[2]
                    continue
                if j==0: continue
                level=rh*(1-TRAIL)
                if b[3] <= level:
                    first=ei+j; break
                rh=max(rh,b[2])
            key=str(int(th*100)); s=threshold_stats[key]; s["eligible"]+=1
            if first is None or first>xi: s["late_or_none"]+=1; cls="late_or_none"
            elif first<xi: s["early"]+=1; cls="early"
            else: s["exact"]+=1; cls="exact"
            act_results[key]=cls

        recs.append({
          "trade_no":tr["trade_no"],"return_pct":tr["return_pct"],"entry_ms":tr["entry_ms"],"exit_ms":tr["exit_ms"],
          "normal_loss":is_normal_loss,
          "hard_first_hit_matches_exit": first_hard==xi if first_hard is not None else False,
          "always_active_trail_class": "exact" if first_always==xi else ("early" if first_always is not None and first_always<xi else "late_or_none"),
          "fixed_activation_classes":act_results
        })

    out["timeframes"][tf]={
      "source_failures":fail,"matched_closed_trades":len(recs),
      "hard_stop_validation":{"normal_losses":hard_losses,"first_touch_on_actual_exit":hard_first_hit_exact,
                              "rate":hard_first_hit_exact/hard_losses if hard_losses else None},
      "always_active_12pct_priorbar_trail":{"early":always_early,"exact":always_exact,"late_or_none":always_late_or_none},
      "fixed_profit_activation_grid":threshold_stats,
      "records":recs
    }

path=EVID/"EXIT_TIMING_DIAGNOSTIC_V0.3.json"
path.write_text(json.dumps(out,indent=2),encoding="utf-8")
for tf,v in out["timeframes"].items():
    print("\n==",tf,"==",v["matched_closed_trades"])
    print("hard",v["hard_stop_validation"])
    print("always",v["always_active_12pct_priorbar_trail"])
    print("activation grid")
    for k,s in v["fixed_profit_activation_grid"].items():
        print(k,"%",s)
print("WROTE",path)
