#!/usr/bin/env python3
import argparse,json,math,statistics
from collections import Counter,defaultdict
from pathlib import Path

OLD_ABS_THRESHOLD=1.252336612578286e-05
MONTHS=("2024-10","2024-11","2024-12")

ap=argparse.ArgumentParser()
ap.add_argument("--source-root",required=True)
ap.add_argument("--feature-root",required=True)
ap.add_argument("--outdir",default="labs/DEFI_LIQUIDATION_SHOCK_001")
args=ap.parse_args()
OUT=Path(args.outdir);OUT.mkdir(parents=True,exist_ok=True)
RECEIPT=OUT/"MARGINFI_ORCA_DEC_REGIME_SOURCE_AUDIT_RECEIPT_V0.1.json"
MONTHLY=OUT/"MARGINFI_ORCA_DEC_REGIME_SOURCE_AUDIT_MONTHLY_V0.1.json"

def find_one(root,name):
    hits=sorted(Path(root).rglob(name))
    return hits[0] if len(hits)==1 else None

def q(vals,p):
    xs=sorted(vals)
    if not xs:return None
    i=(len(xs)-1)*p;lo=int(math.floor(i));hi=int(math.ceil(i))
    if lo==hi:return xs[lo]
    return xs[lo]+(xs[hi]-xs[lo])*(i-lo)

def stats(vals):
    xs=list(vals)
    if not xs:return {"n":0}
    return {
      "n":len(xs),"sum":sum(xs),"mean":sum(xs)/len(xs),"median":statistics.median(xs),
      "p25":q(xs,.25),"p75":q(xs,.75),"p90":q(xs,.90),"p95":q(xs,.95),"max":max(xs)
    }

def ratio(a,b):
    if a is None or b is None or b==0:return None
    return a/b

def blocked(stage,detail):
    rec={"schema_version":"0.1","classification":"MARGINFI_ORCA_DEC_REGIME_SOURCE_AUDIT_BLOCKED",
         "stage":stage,"detail":str(detail),
         "firewall":{"market_2025_opened":False,"market_2026_opened":False,"live_trading":False,
                     "orders":False,"wallets":False,"exchange_mutation":False,"merge_main":False}}
    RECEIPT.write_text(json.dumps(rec,indent=2,sort_keys=True)+"\n")
    print(json.dumps(rec,indent=2,sort_keys=True));raise SystemExit(2)

srec=find_one(args.source_root,"MARGINFI_ORCA_OCTDEC_SIGNED_FLOW_SOURCE_RECEIPT_V0.1.json")
srows=find_one(args.source_root,"MARGINFI_ORCA_OCTDEC_SIGNED_FLOW_SOURCE_ROWS_V0.1.ndjson")
frec=find_one(args.feature_root,"MARGINFI_ORCA_TOPQ_REBOUND_OOS_V01_PREOUTCOME_SELECTION_RECEIPT.json")
frows=find_one(args.feature_root,"MARGINFI_ORCA_TOPQ_REBOUND_OOS_V01_PREOUTCOME_SELECTION_ROWS.ndjson")
if None in (srec,srows,frec,frows):blocked("authority","missing or duplicate authority file")

sr=json.loads(srec.read_text());fr=json.loads(frec.read_text())
if sr.get("classification")!="MARGINFI_ORCA_OCTDEC_SIGNED_FLOW_SOURCE_PASS":
    blocked("source_authority",sr.get("classification"))
fw=fr.get("firewall") or {}
if fw.get("ohlc_read") is not False or fw.get("returns_read") is not False or fw.get("pnl_read") is not False:
    blocked("feature_firewall",fw)

source=[json.loads(x) for x in srows.read_text().splitlines() if x.strip()]
events=[r for r in source if r.get("classification")=="DIRECTION_PROVEN"
        and r.get("route_semantic")=="COLLATERAL_TO_LIABILITY_ORCA_PROVEN"
        and r.get("asset_label")=="SIGNED_SELL_PRESSURE_PROVEN"]
if len(events)!=2263:blocked("source_count",len(events))
features=[json.loads(x) for x in frows.read_text().splitlines() if x.strip()]
if len(features)!=77:blocked("feature_count",len(features))

event_by=defaultdict(list)
for r in events:
    m=str(r.get("timestamp",""))[:7]
    if m not in MONTHS:blocked("source_month",m)
    amt=r.get("exact_route_input_amount")
    if not isinstance(amt,int) or amt<=0:blocked("source_amount",r.get("signature"))
    rr=dict(r);rr["_sold_sol"]=amt/1_000_000_000.0
    event_by[m].append(rr)

feat_by=defaultdict(list)
for r in features:
    m=str(r.get("decision_time",""))[:7]
    if m not in MONTHS:blocked("feature_month",m)
    for k in ("cascade_sold_sol","pre5m_base_volume_sol","flow_turnover_intensity"):
        v=r.get(k)
        if not isinstance(v,(int,float)) or not math.isfinite(v) or v<=0:
            blocked("feature_value",f"{m}:{r.get('cascade_id')}:{k}:{v}")
    feat_by[m].append(r)

monthly={}
for m in MONTHS:
    ev=event_by[m];ft=feat_by[m]
    liabilities=Counter(r.get("liab_mint") for r in ev if r.get("liab_mint"))
    route_lengths=Counter(len(r.get("decoded_route") or []) for r in ev)
    itypes=Counter()
    for r in ev:
        for x in r.get("decoded_route") or []:
            if x.get("type"):itypes[x["type"]]+=1

    sold=[r["_sold_sol"] for r in ev]
    c_sold=[float(r["cascade_sold_sol"]) for r in ft]
    prevol=[float(r["pre5m_base_volume_sol"]) for r in ft]
    intensity=[float(r["flow_turnover_intensity"]) for r in ft]
    event_counts=[int(r.get("source_event_count") or 0) for r in ft]
    days=defaultdict(float)
    for r in ft:days[str(r["decision_time"])[:10]]+=float(r["cascade_sold_sol"])
    day_sums=sorted(days.values(),reverse=True)
    cs=sorted(c_sold,reverse=True)
    total_c=sum(c_sold)
    top1_liab=liabilities.most_common(1)
    top3_liab=liabilities.most_common(3)
    monthly[m]={
      "event_count":len(ev),
      "event_sold_sol":stats(sold),
      "liability_mint_count":len(liabilities),
      "liability_top10":liabilities.most_common(10),
      "liability_top1_share":top1_liab[0][1]/len(ev) if ev and top1_liab else None,
      "liability_top3_share":sum(n for _,n in top3_liab)/len(ev) if ev else None,
      "route_length_counts":dict(sorted((str(k),v) for k,v in route_lengths.items())),
      "instruction_type_counts":dict(sorted(itypes.items())),
      "cascade_count":len(ft),
      "distinct_decision_days":len(days),
      "source_events_per_cascade":stats(event_counts),
      "cascade_sold_sol":stats(c_sold),
      "pre5m_base_volume_sol":stats(prevol),
      "flow_turnover_intensity":stats(intensity),
      "old_absolute_threshold_share":sum(1 for x in intensity if x>=OLD_ABS_THRESHOLD)/len(intensity) if intensity else None,
      "top_day_sold_sol_share":day_sums[0]/total_c if day_sums and total_c else None,
      "top2_days_sold_sol_share":sum(day_sums[:2])/total_c if day_sums and total_c else None,
      "top_cascade_sold_sol_share":cs[0]/total_c if cs and total_c else None,
      "top5_cascades_sold_sol_share":sum(cs[:5])/total_c if cs and total_c else None
    }

octm,nov,decm=monthly["2024-10"],monthly["2024-11"],monthly["2024-12"]
ratios={
 "dec_over_nov_median_event_sold_sol":ratio(decm["event_sold_sol"]["median"],nov["event_sold_sol"]["median"]),
 "dec_over_oct_median_event_sold_sol":ratio(decm["event_sold_sol"]["median"],octm["event_sold_sol"]["median"]),
 "dec_over_nov_median_cascade_sold_sol":ratio(decm["cascade_sold_sol"]["median"],nov["cascade_sold_sol"]["median"]),
 "dec_over_oct_median_cascade_sold_sol":ratio(decm["cascade_sold_sol"]["median"],octm["cascade_sold_sol"]["median"]),
 "dec_over_nov_median_pre5m_turnover":ratio(decm["pre5m_base_volume_sol"]["median"],nov["pre5m_base_volume_sol"]["median"]),
 "dec_over_oct_median_pre5m_turnover":ratio(decm["pre5m_base_volume_sol"]["median"],octm["pre5m_base_volume_sol"]["median"]),
 "dec_over_nov_median_intensity":ratio(decm["flow_turnover_intensity"]["median"],nov["flow_turnover_intensity"]["median"]),
 "dec_over_oct_median_intensity":ratio(decm["flow_turnover_intensity"]["median"],octm["flow_turnover_intensity"]["median"])
}

MONTHLY.write_text(json.dumps({"monthly":monthly,"cross_month_ratios":ratios},indent=2,sort_keys=True)+"\n")
receipt={
 "schema_version":"0.1","classification":"MARGINFI_ORCA_DEC_REGIME_SOURCE_AUDIT_PASS",
 "authority":"MARGINFI_ORCA_DEC_REGIME_SOURCE_AUDIT_FREEZE_V0.1.md",
 "source":{"run_id":36814861360,"artifact_id":11140129257,
           "digest":"sha256:8d8b1b9fdf84dcc234e46012a39cc5126fa5b3068e739daf1f5d7e83ee42a4d7",
           "direction_proven_accounted":len(events)},
 "feature":{"run_id":36815199005,"artifact_id":11140992589,
            "digest":"sha256:b452730607f3db4c7f983ce748c74be1ee7f7a51301a1f3876e7d62698cac470",
            "cascade_count_accounted":len(features),"ohlc_read":False,"returns_read":False,"pnl_read":False},
 "monthly":monthly,"cross_month_ratios":ratios,
 "firewall":{"market_2025_opened":False,"market_2026_opened":False,"live_trading":False,
             "orders":False,"wallets":False,"exchange_mutation":False,"merge_main":False}
}
RECEIPT.write_text(json.dumps(receipt,indent=2,sort_keys=True)+"\n")
print(json.dumps(receipt,indent=2,sort_keys=True))
