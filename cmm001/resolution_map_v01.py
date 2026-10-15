#!/usr/bin/env python3
import csv, json, math, os, hashlib
from datetime import date, timedelta
from statistics import mean, median

BASE = os.path.dirname(__file__)
IN_DAILY = os.path.join(BASE, "discovery_results", "CMM001_DAILY_STATE_LEDGER_V01.csv")
IN_EVENTS = os.path.join(BASE, "discovery_results", "CMM001_EVENT_LEDGER_V01.csv")
OUT = os.path.join(BASE, "resolution_map_results")
os.makedirs(OUT, exist_ok=True)

EXPECTED_EVENT_SHA = "8c79b4287d5a0bc7ab263b856b56bded638d75e2ea14c25434156a4eb20909d8"

def sha256(path):
    h=hashlib.sha256()
    with open(path,"rb") as f:
        for chunk in iter(lambda:f.read(1<<20), b""):
            h.update(chunk)
    return h.hexdigest()

def f(x):
    if x is None or x == "":
        return None
    try:
        v=float(x)
        return v if math.isfinite(v) else None
    except Exception:
        return None

if sha256(IN_EVENTS) != EXPECTED_EVENT_SHA:
    raise SystemExit("FAIL_CLOSED_EVENT_LEDGER_SHA_MISMATCH")

daily={}
with open(IN_DAILY, newline="", encoding="utf-8") as fh:
    for r in csv.DictReader(fh):
        daily[r["date"]] = {
            "S_z": f(r.get("S_z")),
            "O_z": f(r.get("O_z")),
            "R_z": f(r.get("R_z")),
            "L_z": f(r.get("L_z")),
            "N": f(r.get("N")),
            "G": f(r.get("G")),
        }

events=[]
with open(IN_EVENTS, newline="", encoding="utf-8") as fh:
    for r in csv.DictReader(fh):
        # No PnL/return field is read into the analysis object.
        g=f(r.get("G"))
        if g is None or g == 0:
            continue
        events.append({
            "date": r["date"],
            "block": r["block"],
            "G0": g,
        })

def sign(x):
    return 1 if x > 0 else (-1 if x < 0 else 0)

rows=[]
horizons=(1,3,7)
for ev in events:
    d0=date.fromisoformat(ev["date"])
    s0=daily.get(ev["date"])
    if not s0 or s0["G"] is None or s0["S_z"] is None or s0["N"] is None:
        raise SystemExit("FAIL_CLOSED_PARENT_EVENT_STATE_MISSING:"+ev["date"])
    g0=s0["G"]
    sg=sign(g0)
    for h in horizons:
        dh=(d0+timedelta(days=h)).isoformat()
        sh=daily.get(dh)
        rec={
            "event_date":ev["date"],"block":ev["block"],"horizon_days":h,
            "future_date":dh,"G0":g0,"orientation":"G_POS" if g0>0 else "G_NEG",
            "available":False,
        }
        if not sh or sh["G"] is None or sh["S_z"] is None or sh["N"] is None:
            rows.append(rec); continue
        gh=sh["G"]
        agr=abs(gh)/abs(g0) if g0 != 0 else None
        shrank=abs(gh)<abs(g0)
        crossed=(sign(gh) != 0 and sign(gh) != sg)
        sc=sg*(s0["S_z"]-sh["S_z"])
        nc=sg*(sh["N"]-s0["N"])
        leader=None
        if shrank:
            if abs(sc-nc) <= 1e-12: leader="TIE"
            elif sc>nc: leader="SPOT_LED"
            else: leader="NONSPOT_LED"
        rec.update({
            "available":True,"Gh":gh,"AGR":agr,
            "resolution_fraction":1-agr,
            "gap_shrank":shrank,"gap_crossed":crossed,
            "spot_close":sc,"nonspot_close":nc,"leader_if_shrank":leader,
        })
        for k in ("O_z","R_z","L_z"):
            x0=s0.get(k); xh=sh.get(k)
            rec[k+"_move_toward_spot"] = (sg*(xh-x0) if x0 is not None and xh is not None else None)
        rows.append(rec)

def avg(xs):
    xs=[x for x in xs if x is not None and math.isfinite(x)]
    return mean(xs) if xs else None

def med(xs):
    xs=[x for x in xs if x is not None and math.isfinite(x)]
    return median(xs) if xs else None

def frac(vals):
    vals=list(vals)
    return (sum(1 for x in vals if x)/len(vals)) if vals else None

def summarize(sub):
    v=[r for r in sub if r.get("available")]
    shrinking=[r for r in v if r.get("gap_shrank")]
    spot_led=[r for r in shrinking if r.get("leader_if_shrank")=="SPOT_LED"]
    nonspot_led=[r for r in shrinking if r.get("leader_if_shrank")=="NONSPOT_LED"]
    tie=[r for r in shrinking if r.get("leader_if_shrank")=="TIE"]
    out={
        "n_valid":len(v),
        "gap_shrink_rate":frac(r["gap_shrank"] for r in v),
        "gap_cross_rate":frac(r["gap_crossed"] for r in v),
        "AGR_mean":avg(r.get("AGR") for r in v),
        "AGR_median":med(r.get("AGR") for r in v),
        "resolution_fraction_mean":avg(r.get("resolution_fraction") for r in v),
        "resolution_fraction_median":med(r.get("resolution_fraction") for r in v),
        "spot_close_mean":avg(r.get("spot_close") for r in v),
        "spot_close_median":med(r.get("spot_close") for r in v),
        "nonspot_close_mean":avg(r.get("nonspot_close") for r in v),
        "nonspot_close_median":med(r.get("nonspot_close") for r in v),
        "shrinking_gap_count":len(shrinking),
        "spot_led_count_among_shrinking":len(spot_led),
        "nonspot_led_count_among_shrinking":len(nonspot_led),
        "tie_count_among_shrinking":len(tie),
        "spot_led_share_among_shrinking":len(spot_led)/len(shrinking) if shrinking else None,
        "nonspot_led_share_among_shrinking":len(nonspot_led)/len(shrinking) if shrinking else None,
        "spot_led_resolution_rate_unconditional":len(spot_led)/len(v) if v else None,
        "nonspot_led_resolution_rate_unconditional":len(nonspot_led)/len(v) if v else None,
    }
    for k in ("O_z","R_z","L_z"):
        vals=[r.get(k+"_move_toward_spot") for r in v if r.get(k+"_move_toward_spot") is not None]
        out[k+"_move_toward_spot_positive_rate"]=(sum(x>0 for x in vals)/len(vals) if vals else None)
        out[k+"_move_toward_spot_mean"]=avg(vals)
    return out

result={
    "lab_id":"CMM-RM-001",
    "status":"EXPLORATORY_HYPOTHESIS_GENERATION_ONLY",
    "parent_verdict":"INSUFFICIENT_SAMPLE",
    "event_ledger_sha256":sha256(IN_EVENTS),
    "new_market_data_access":False,
    "pnl_or_return_used":False,
    "protected_2025_2026_accessed":False,
    "horizons":{},
}
for h in horizons:
    sub=[r for r in rows if r["horizon_days"]==h]
    result["horizons"][str(h)] = {
        "all": summarize(sub),
        "G_POS": summarize([r for r in sub if r["orientation"]=="G_POS"]),
        "G_NEG": summarize([r for r in sub if r["orientation"]=="G_NEG"]),
    }

with open(os.path.join(OUT,"CMM_RM_001_RESULT_V01.json"),"w",encoding="utf-8") as fobj:
    json.dump(result,fobj,indent=2,sort_keys=True,allow_nan=False)

cols=[
    "event_date","block","horizon_days","future_date","orientation","available",
    "G0","Gh","AGR","resolution_fraction","gap_shrank","gap_crossed",
    "spot_close","nonspot_close","leader_if_shrank",
    "O_z_move_toward_spot","R_z_move_toward_spot","L_z_move_toward_spot"
]
with open(os.path.join(OUT,"CMM_RM_001_EVENT_RESOLUTION_LEDGER_V01.csv"),"w",newline="",encoding="utf-8") as fobj:
    w=csv.DictWriter(fobj,fieldnames=cols)
    w.writeheader()
    for r in rows:
        w.writerow({k:r.get(k) for k in cols})

md=["# CMM-RM-001 — CROSS-MARKET RESOLUTION MAP V0.1","",
    "**Status: EXPLORATORY / HYPOTHESIS-GENERATION ONLY**","",
    "No new market data were accessed. No PnL/return variable was used. 2025/2026 remained closed.",""]
for h in horizons:
    x=result["horizons"][str(h)]["all"]
    md += [f"## Horizon {h}d",
           f"- Valid events: {x['n_valid']}",
           f"- Gap shrank: {100*x['gap_shrink_rate']:.2f}%" if x["gap_shrink_rate"] is not None else "- Gap shrank: n/a",
           f"- Median |G_h|/|G_0|: {x['AGR_median']:.4f}" if x["AGR_median"] is not None else "- Median |G_h|/|G_0|: n/a",
           f"- Spot-led among shrinking gaps: {100*x['spot_led_share_among_shrinking']:.2f}%" if x["spot_led_share_among_shrinking"] is not None else "- Spot-led among shrinking gaps: n/a",
           f"- Non-spot-led among shrinking gaps: {100*x['nonspot_led_share_among_shrinking']:.2f}%" if x["nonspot_led_share_among_shrinking"] is not None else "- Non-spot-led among shrinking gaps: n/a",
           f"- Unconditional spot-led resolution: {100*x['spot_led_resolution_rate_unconditional']:.2f}%" if x["spot_led_resolution_rate_unconditional"] is not None else "- Unconditional spot-led resolution: n/a",
           f"- Unconditional non-spot-led resolution: {100*x['nonspot_led_resolution_rate_unconditional']:.2f}%" if x["nonspot_led_resolution_rate_unconditional"] is not None else "- Unconditional non-spot-led resolution: n/a",
           ""]
md += ["## Governance",
       "- This map does not change the parent INSUFFICIENT_SAMPLE verdict.",
       "- No subgroup from this result is promotable.",
       "- Any predictive child must be a new frozen identity tested on genuinely independent future evidence.",
       "- No live trading, micro-live, orders, exchange mutation, alerts/webhooks, Render or main merge.",
       ""]
with open(os.path.join(OUT,"CMM_RM_001_CLOSEOUT_V01.md"),"w",encoding="utf-8") as fobj:
    fobj.write("\n".join(md))

print(json.dumps(result,indent=2,sort_keys=True))
