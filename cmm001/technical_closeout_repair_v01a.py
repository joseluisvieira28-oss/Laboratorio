#!/usr/bin/env python3
import csv, hashlib, json, math, os, random, statistics
from collections import defaultdict

ROOT = os.path.dirname(__file__)
RES = os.path.join(ROOT, "discovery_results")
LEDGER = os.path.join(RES, "CMM001_EVENT_LEDGER_V01.csv")
SOURCE = os.path.join(RES, "CMM001_DISCOVERY_SOURCE_REPORT_V01.json")
OUT_JSON = os.path.join(RES, "CMM001_DISCOVERY_RESULT_V01A_TECHNICAL_CLOSEOUT.json")
OUT_MD = os.path.join(RES, "CMM001_DISCOVERY_CLOSEOUT_V01A.md")
OUT_RECEIPT = os.path.join(RES, "CMM001_TECHNICAL_REPAIR_RECEIPT_V01A.json")

BLOCKS = ["A_DISCOVERY", "B_REPLICATION_2023", "C_REPLICATION_2024"]
BOOT_SEED = 20260925
BOOT_N = 10000

ANCHORS = {
    "A_DISCOVERY": {"n":15, "mean":-15.974320184676847, "pf":0.9381782766756509},
    "B_REPLICATION_2023": {"n":16, "mean":-12.489306569098197, "pf":0.8850931891227862},
    "C_REPLICATION_2024": {"n":4, "mean":-177.31335986960195, "pf":0.09769585257550582},
}
BOOT_ANCHOR = {
    "p":0.663,
    "p05":-166.61399403900987,
    "p50":-36.041367109127606,
    "p95":111.00334437994752,
}

def sha256_path(path):
    h=hashlib.sha256()
    with open(path,"rb") as f:
        for chunk in iter(lambda:f.read(1<<20), b""):
            h.update(chunk)
    return h.hexdigest()

def percentile_linear(values, q):
    xs=sorted(float(x) for x in values)
    if not xs: return None
    if len(xs)==1: return xs[0]
    pos=(len(xs)-1)*q
    lo=int(math.floor(pos)); hi=int(math.ceil(pos))
    if lo==hi: return xs[lo]
    w=pos-lo
    return xs[lo]*(1-w)+xs[hi]*w

def pf_raw(vals):
    pos=sum(x for x in vals if x>0)
    neg=-sum(x for x in vals if x<0)
    if neg==0:
        return math.inf if pos>0 else 0.0
    return pos/neg

def pf_json(x):
    if math.isinf(x): return {"value":None,"repr":"INF"}
    return {"value":x,"repr":None}

def metrics(evs):
    vals=[float(e["net10_bps"]) for e in evs]
    stress=[float(e["stress20_bps"]) for e in evs]
    pos=[x for x in vals if x>0]
    pf=pf_raw(vals)
    return {
        "n":len(vals),
        "mean_net10_bps":statistics.fmean(vals) if vals else None,
        "median_net10_bps":statistics.median(vals) if vals else None,
        "pf_net10":pf_json(pf),
        "positive_fraction":sum(1 for x in vals if x>0)/len(vals) if vals else None,
        "mean_stress20_bps":statistics.fmean(stress) if stress else None,
        "largest_positive_net_share":max(pos)/sum(pos) if pos and sum(pos)>0 else None,
        "_pf_raw":pf,
    }

def public_metric(m):
    return {k:v for k,v in m.items() if not k.startswith("_")}

def close(a,b,tol=1e-10):
    return abs(a-b) <= tol*max(1.0,abs(a),abs(b))

with open(SOURCE,"r",encoding="utf-8") as f:
    source=json.load(f)
if source.get("source_pass") is not True or source.get("outcomes_opened") is not True:
    raise SystemExit("FAIL_CLOSED: parent source report is not SOURCE PASS + outcomes opened")
if source.get("protected_periods",{}).get("2025")!="LOCKED_NOT_FETCHED":
    raise SystemExit("FAIL_CLOSED: parent 2025 protection receipt missing")
if source.get("protected_periods",{}).get("2026")!="LOCKED_NOT_FETCHED":
    raise SystemExit("FAIL_CLOSED: parent 2026 protection receipt missing")

with open(LEDGER,"r",encoding="utf-8-sig",newline="") as f:
    events=list(csv.DictReader(f))

if not events:
    raise SystemExit("FAIL_CLOSED: immutable event ledger empty")

# Strict structural checks; no event creation/deletion is allowed.
required={"date","block","entry_utc","exit_utc","direction","G","q95","entry_price","exit_price","gross_bps","net10_bps","stress20_bps","F_z","C_z"}
missing=required-set(events[0].keys())
if missing:
    raise SystemExit(f"FAIL_CLOSED: ledger columns missing {sorted(missing)}")
if any(e["block"] not in BLOCKS for e in events):
    raise SystemExit("FAIL_CLOSED: unexpected block in immutable ledger")

by=defaultdict(list)
for e in events: by[e["block"]].append(e)
bm={b:metrics(by[b]) for b in BLOCKS}
pooled=metrics(events)
loo={b:metrics([e for e in events if e["block"]!=b]) for b in BLOCKS}

# Reproduce original pre-crash anchors exactly enough to prove this is a serialization repair.
anchor_checks={}
for b,a in ANCHORS.items():
    m=bm[b]
    ok=(m["n"]==a["n"] and close(m["mean_net10_bps"],a["mean"]) and close(m["_pf_raw"],a["pf"]))
    anchor_checks[b]=ok
    if not ok:
        raise SystemExit(f"FAIL_CLOSED: scientific anchor mismatch {b}: {m} vs {a}")

vals=[float(e["net10_bps"]) for e in events]
rng=random.Random(BOOT_SEED)
boot=[]
n=len(vals)
for _ in range(BOOT_N):
    boot.append(statistics.fmean(vals[rng.randrange(n)] for _ in range(n)))
boot.sort()
bp=sum(1 for x in boot if x<=0)/len(boot)
b05=percentile_linear(boot,.05)
b50=percentile_linear(boot,.50)
b95=percentile_linear(boot,.95)
boot_ok=(close(bp,BOOT_ANCHOR["p"]) and close(b05,BOOT_ANCHOR["p05"]) and close(b50,BOOT_ANCHOR["p50"]) and close(b95,BOOT_ANCHOR["p95"]))
if not boot_ok:
    raise SystemExit(f"FAIL_CLOSED: bootstrap anchor mismatch {(bp,b05,b50,b95)} vs {BOOT_ANCHOR}")

adequate=(pooled["n"]>=30 and all(bm[b]["n"]>=8 for b in BLOCKS))

def pos_pf(m):
    return m["n"]>0 and m["mean_net10_bps"] is not None and m["mean_net10_bps"]>0 and m["_pf_raw"]>1

tier2=(
    adequate
    and all(pos_pf(bm[b]) for b in BLOCKS)
    and pos_pf(pooled)
    and all(pos_pf(loo[b]) for b in BLOCKS)
    and pooled["largest_positive_net_share"] is not None
    and pooled["largest_positive_net_share"]<=0.40
)

independent_material_contradiction=any(
    bm[b]["n"]>=8
    and bm[b]["mean_net10_bps"] is not None
    and bm[b]["mean_net10_bps"]<=-10.0
    and bm[b]["_pf_raw"]<=0.90
    for b in ("B_REPLICATION_2023","C_REPLICATION_2024")
)
pooled_strong_negative=(
    adequate and pooled["mean_net10_bps"] is not None and pooled["mean_net10_bps"]<0
    and pooled["_pf_raw"]<1 and b95 is not None and b95<0
)

if not adequate:
    verdict="INSUFFICIENT_SAMPLE"
    maturity="M3_DISCOVERY_ATTEMPT"
elif tier2:
    verdict="TIER2_PROMOTED_CANDIDATE__QUASE_DIAMANTE"
    maturity="M4_REPLICATION"
elif independent_material_contradiction or pooled_strong_negative:
    verdict="TIER4_REJECTED"
    maturity="M4_REPLICATION"
else:
    verdict="TIER3_WATCHLIST"
    maturity="M4_REPLICATION"

def diag(key):
    groups={"EXTREME_POS":[],"EXTREME_NEG":[],"NON_EXTREME":[],"MISSING":[]}
    for e in events:
        s=(e.get(key) or "").strip()
        if not s:
            groups["MISSING"].append(e); continue
        try: z=float(s)
        except: groups["MISSING"].append(e); continue
        if z>=1.5: groups["EXTREME_POS"].append(e)
        elif z<=-1.5: groups["EXTREME_NEG"].append(e)
        else: groups["NON_EXTREME"].append(e)
    return {k:public_metric(metrics(v)) for k,v in groups.items()}

result={
    "lab_id":"CMM-001-V01",
    "repair_id":"CMM-001-V01A-TECHNICAL-CLOSEOUT",
    "parent_run":36107876501,
    "parent_evidence_commit":"7ce2438cdcc9e45ff237daf68ec823e643cbfb42",
    "repair_scope":"NO_NETWORK__IMMUTABLE_LEDGER_ONLY",
    "source_pass":True,
    "outcomes_opened_in_parent":True,
    "protected_periods":{"2025":"LOCKED_NOT_FETCHED","2026":"LOCKED_NOT_FETCHED"},
    "event_ledger_sha256":sha256_path(LEDGER),
    "source_report_sha256":sha256_path(SOURCE),
    "reproduction_anchors":{"blocks":anchor_checks,"bootstrap":boot_ok,"all_pass":all(anchor_checks.values()) and boot_ok},
    "blocks":{b:public_metric(bm[b]) for b in BLOCKS},
    "pooled":public_metric(pooled),
    "leave_one_block_out":{b:public_metric(loo[b]) for b in BLOCKS},
    "bootstrap":{
        "reps":BOOT_N,"seed":BOOT_SEED,
        "one_sided_p_mean_le_zero":bp,
        "p05_mean_net10_bps":b05,
        "p50_mean_net10_bps":b50,
        "p95_mean_net10_bps":b95,
    },
    "sample_adequacy":{
        "pooled_n_ge_30":pooled["n"]>=30,
        "each_block_n_ge_8":{b:bm[b]["n"]>=8 for b in BLOCKS},
        "pass":adequate,
    },
    "tier2_gates":{
        "all_blocks_positive_pf_gt_1":all(pos_pf(bm[b]) for b in BLOCKS),
        "pooled_positive_pf_gt_1":pos_pf(pooled),
        "all_loo_positive_pf_gt_1":all(pos_pf(loo[b]) for b in BLOCKS),
        "pooled_largest_positive_share_le_40pct":pooled["largest_positive_net_share"] is not None and pooled["largest_positive_net_share"]<=0.40,
    },
    "tier4_diagnostics_not_reachable_if_sample_inadequate":{
        "independent_material_contradiction":independent_material_contradiction,
        "pooled_strong_negative":pooled_strong_negative,
    },
    "diagnostics_only":{
        "funding_z_strata":diag("F_z"),
        "cftc_z_strata":diag("C_z"),
    },
    "verdict":verdict,
    "maturity":maturity,
    "governance":{
        "post_outcome_rule_changes":False,
        "network_market_data_access_in_repair":False,
        "tier1_possible":False,
        "live_trading_authorized":False,
        "micro_live_authorized":False,
        "main_merge_authorized":False,
        "rescue_authorized":False,
    },
}

with open(OUT_JSON,"w",encoding="utf-8") as f:
    json.dump(result,f,indent=2,sort_keys=True,allow_nan=False)

def fv(x, nd=4):
    if x is None: return "NA"
    return f"{x:.{nd}f}"

lines=[
"# CMM-001 — DISCOVERY TECHNICAL CLOSEOUT V0.1A",
"",
f"**FORMAL VERDICT: {verdict}**",
f"**MATURITY: {maturity}**",
"",
"Technical status: parent science reproduced from immutable event ledger; serialization bug repaired without network access or scientific changes.",
"",
"## Source integrity",
"- Parent full-corpus source gate: PASS.",
"- Options candidate-window O_raw coverage: 97.4138%.",
"- Deribit request/parse errors: 0.",
"- Deribit has_more truncation days: 0.",
"- Binance Spot exact-hour availability: 100%.",
"- 2025: LOCKED / NOT FETCHED.",
"- 2026: LOCKED / NOT FETCHED.",
"",
"## Frozen block results — BASE NET10",
]
for b in BLOCKS:
    m=bm[b]
    lines.append(f"- {b}: N={m['n']} | mean={fv(m['mean_net10_bps'])} bps | median={fv(m['median_net10_bps'])} bps | PF={fv(m['_pf_raw'])} | positive={fv((m['positive_fraction'] or 0)*100,2)}%")
lines += [
"",
"## Pooled",
f"- N={pooled['n']}",
f"- mean NET10={fv(pooled['mean_net10_bps'])} bps",
f"- median NET10={fv(pooled['median_net10_bps'])} bps",
f"- PF NET10={fv(pooled['_pf_raw'])}",
f"- positive events={fv((pooled['positive_fraction'] or 0)*100,2)}%",
f"- mean STRESS20={fv(pooled['mean_stress20_bps'])} bps",
f"- largest single positive BASE-net share={fv((pooled['largest_positive_net_share'] or 0)*100,2)}%",
"",
"## Bootstrap",
f"- 10,000 reps; seed {BOOT_SEED}",
f"- P(mean <= 0)={fv(bp,4)}",
f"- p05={fv(b05)} bps",
f"- median={fv(b50)} bps",
f"- p95={fv(b95)} bps",
"",
"## Frozen sample-adequacy gate",
f"- pooled N >=30: {'PASS' if pooled['n']>=30 else 'FAIL'}",
]
for b in BLOCKS:
    lines.append(f"- {b} N >=8: {'PASS' if bm[b]['n']>=8 else 'FAIL'}")
lines += [
"",
"Because sample adequacy fails if ANY block has N<8, the frozen authority requires INSUFFICIENT_SAMPLE before any Tier-4 adjudication. This repair does not override that precedence.",
"",
"## Scientific warning preserved",
f"- Independent 2023 block material-contradiction diagnostic: {'TRUE' if (bm['B_REPLICATION_2023']['mean_net10_bps']<=-10 and bm['B_REPLICATION_2023']['_pf_raw']<=0.90) else 'FALSE'}.",
"- This warning is not a Tier-4 verdict while the frozen corpus sample-adequacy gate is unmet.",
"- No threshold/cost/horizon/component/year/direction rescue is authorized.",
"",
"## Evidence integrity",
f"- Event ledger SHA256: {result['event_ledger_sha256']}",
f"- Source report SHA256: {result['source_report_sha256']}",
"- All original block and bootstrap reproduction anchors: PASS.",
"",
"## Safety",
"No live trading, micro-live, capital, orders, exchange mutation, alerts/webhooks, Render deployment or main merge is authorized.",
]
with open(OUT_MD,"w",encoding="utf-8") as f:
    f.write("\n".join(lines)+"\n")

receipt={
    "repair_id":"CMM-001-V01A-TECHNICAL-CLOSEOUT",
    "parent_evidence_commit":"7ce2438cdcc9e45ff237daf68ec823e643cbfb42",
    "network_market_data_access":False,
    "event_ledger_sha256":result["event_ledger_sha256"],
    "result_sha256":sha256_path(OUT_JSON),
    "closeout_sha256":sha256_path(OUT_MD),
    "anchors_all_pass":result["reproduction_anchors"]["all_pass"],
    "verdict":verdict,
}
with open(OUT_RECEIPT,"w",encoding="utf-8") as f:
    json.dump(receipt,f,indent=2,sort_keys=True)

print(json.dumps({
    "verdict":verdict,
    "pooled":public_metric(pooled),
    "blocks":{b:public_metric(bm[b]) for b in BLOCKS},
    "sample_adequacy":result["sample_adequacy"],
    "bootstrap":result["bootstrap"],
    "repair_receipt":receipt,
},indent=2,allow_nan=False))
