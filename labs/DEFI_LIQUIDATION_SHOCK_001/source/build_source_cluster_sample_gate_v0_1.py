#!/usr/bin/env python3
import argparse, hashlib, json
from collections import defaultdict
from datetime import datetime, timezone, timedelta
from pathlib import Path

try:
    import ijson
except ImportError:
    raise SystemExit("ijson_required")

DISCOVERY_END=datetime.fromisoformat("2024-01-01T00:00:00+00:00")
OOS_END=datetime.fromisoformat("2025-01-01T00:00:00+00:00")
WINDOWS=[15,60,300]
PRIMARY=60
OUT=Path("labs/DEFI_LIQUIDATION_SHOCK_001/SOURCE_CLUSTER_SAMPLE_GATE_RECEIPT_V0.1.json")
CLUSTER_OUT=Path("labs/DEFI_LIQUIDATION_SHOCK_001/SOURCE_PRIMARY_CLUSTER_CENSUS_V0.1.ndjson")

def dtv(s):
    return datetime.fromisoformat(str(s).replace("Z","+00:00"))

def addr_key(v):
    return json.dumps(v,separators=(",",":"),sort_keys=True)

def find_one(root,names):
    if isinstance(names,str): names=[names]
    hits=[]
    for name in names:
        hits.extend(Path(root).rglob(name))
    if not hits:return None,None
    p=sorted(set(hits))[0]
    return json.loads(p.read_text()),str(p)

def iter_array(path,prefix):
    with open(path,"rb") as fh:
        for item in ijson.items(fh,prefix+".item"):
            yield item

def top_scalar(path,key):
    with open(path,"rb") as fh:
        for prefix,event,value in ijson.parse(fh):
            if prefix==key and event in ("string","number","boolean","null"):
                return value
            if prefix in ("enriched_rows","event_units") and event=="start_array":
                break
    return None

def files_sorted(root,prefix):
    return sorted([p for p in Path(root).rglob("*.json") if p.name.startswith(prefix)])

class ClusterCounter:
    def __init__(self,quiet,emit_path=None):
        self.quiet=quiet
        self.open={}
        self.aggregate=defaultdict(int)
        self.subgroup=defaultdict(int)
        self.asset=defaultdict(int)
        self.protected_cross=0
        self.total_clusters=0
        self.total_events=0
        self.max_event_count=0
        self.event_count_hist=defaultdict(int)
        self.emit_path=Path(emit_path) if emit_path else None
        self.emit_fh=None
        self.emitted_cluster_count=0
        if self.emit_path:
            self.emit_path.parent.mkdir(parents=True,exist_ok=True)
            self.emit_fh=self.emit_path.open("w",encoding="utf-8")

    def _split(self,last_ts):
        t0=last_ts+timedelta(seconds=self.quiet)
        if t0<DISCOVERY_END:return "discovery",t0
        if t0<OOS_END:return "oos",t0
        return "protected_excluded",t0

    def _finish(self,key,state):
        split,t0=self._split(state["last"])
        self.total_clusters+=1
        n=state["event_count"]
        self.max_event_count=max(self.max_event_count,n)
        if n==1:b="1"
        elif n<=3:b="2-3"
        elif n<=10:b="4-10"
        elif n<=100:b="11-100"
        else:b="101+"
        self.event_count_hist[b]+=1
        if split=="protected_excluded":
            self.protected_cross+=1
            return
        protocol,cls,market=key
        self.aggregate[split]+=1
        self.subgroup[(split,protocol,cls)]+=1
        self.asset[(split,protocol,cls,market)]+=1
        if self.emit_fh is not None:
            raw="|".join([
                "DEFI-LIQUIDATION-SHOCK-001","cluster-v0.1",str(self.quiet),
                protocol,cls,market,state["first"].isoformat(),state["last"].isoformat(),
                state["first_signature"],state["last_signature"],str(n)
            ])
            cluster_id=hashlib.sha256(raw.encode()).hexdigest()
            row={
              "cluster_id":cluster_id,
              "quiet_seconds":self.quiet,
              "split":split,
              "protocol":protocol,
              "instruction_class":cls,
              "primary_market_identity":market,
              "first_event_timestamp":state["first"].isoformat().replace("+00:00","Z"),
              "last_event_timestamp":state["last"].isoformat().replace("+00:00","Z"),
              "t0":t0.isoformat().replace("+00:00","Z"),
              "event_count":n,
              "distinct_transaction_signature_count":len(state["signatures"]),
              "first_signature":state["first_signature"],
              "last_signature":state["last_signature"],
              "source_only":True
            }
            self.emit_fh.write(json.dumps(row,separators=(",",":"),sort_keys=True)+"\n")
            self.emitted_cluster_count+=1

    def add(self,protocol,cls,market,ts,signature):
        key=(protocol,cls,market)
        self.total_events+=1
        s=self.open.get(key)
        if s is None:
            self.open[key]={"first":ts,"last":ts,"event_count":1,
                            "first_signature":signature,"last_signature":signature,
                            "signatures":{signature}}
            return
        if ts<s["last"]:
            raise RuntimeError(f"non_monotonic_event_time:{key}:{ts.isoformat()}<{s['last'].isoformat()}")
        if (ts-s["last"]).total_seconds()<=self.quiet:
            s["last"]=ts
            s["event_count"]+=1
            s["last_signature"]=signature
            s["signatures"].add(signature)
        else:
            self._finish(key,s)
            self.open[key]={"first":ts,"last":ts,"event_count":1,
                            "first_signature":signature,"last_signature":signature,
                            "signatures":{signature}}

    def finish_all(self):
        for k,s in list(self.open.items()):self._finish(k,s)
        self.open.clear()
        if self.emit_fh is not None:
            self.emit_fh.flush()
            self.emit_fh.close()
            self.emit_fh=None

ap=argparse.ArgumentParser()
ap.add_argument("--global-evidence",required=True)
ap.add_argument("--marginfi-field",required=True)
ap.add_argument("--save0c-units",required=True)
ap.add_argument("--ks-units",required=True)
ap.add_argument("--drift-field",required=True)
args=ap.parse_args()

errors=[]

global_receipt,_=find_one(args.global_evidence,"GLOBAL_FIELD_COVERAGE_FINAL_RECEIPT_V0.1.json")
if not global_receipt:
    errors.append({"reason":"missing_global_field_receipt"})
elif global_receipt.get("classification")!="GLOBAL_FIELD_COVERAGE_FINAL_PASS":
    errors.append({"reason":"global_field_not_pass","classification":global_receipt.get("classification")})

# Frozen final unit receipts selected by global evidence collector.
marginfi_reg,mr_path=find_one(args.global_evidence,[
    "MARGINFI_BANK_UNIT_REGISTRY_RECEIPT_V0.2.json",
    "MARGINFI_BANK_UNIT_REGISTRY_RECEIPT_V0.1.json"])
save0c_final,su_path=find_one(args.global_evidence,[
    "SAVE0C_UNIT_METADATA_POPULATION_RECEIPT_V0.3.json",
    "SAVE0C_UNIT_METADATA_POPULATION_RECEIPT_V0.2.json",
    "SAVE0C_UNIT_METADATA_POPULATION_RECEIPT_V0.1.json"])

if not marginfi_reg or marginfi_reg.get("classification")!="MARGINFI_BANK_UNIT_REGISTRY_POPULATION_PASS":
    errors.append({"reason":"marginfi_final_unit_registry_not_pass",
                   "classification":(marginfi_reg or {}).get("classification")})
if not save0c_final or save0c_final.get("classification")!="SAVE0C_UNIT_METADATA_POPULATION_PASS":
    errors.append({"reason":"save0c_final_unit_registry_not_pass",
                   "classification":(save0c_final or {}).get("classification")})

bank_map={}
for x in (marginfi_reg or {}).get("bank_registry") or []:
    if x.get("bank") and x.get("mint"):bank_map[x["bank"]]=x["mint"]

save_ext={}
for x in (save0c_final or {}).get("registry_extension") or []:
    r=x.get("reserve");m=x.get("underlying_mint")
    if r and m:save_ext[r]=m

counters={w:ClusterCounter(w,CLUSTER_OUT if w==PRIMARY else None) for w in WINDOWS}
first_event={}

def add_event(protocol,cls,market,ts_s,sig):
    if not market:
        errors.append({"reason":"missing_primary_market_identity","protocol":protocol,"class":cls,"signature":sig})
        return
    ts=dtv(ts_s)
    g=(protocol,cls)
    if g not in first_event or ts<first_event[g]:first_event[g]=ts
    for c in counters.values():c.add(protocol,cls,market,ts,sig)

# Marginfi: use field-enrichment rows + terminal Bank registry.
mf_files=files_sorted(args.marginfi_field,"marginfi-")
if len(mf_files)!=23:
    errors.append({"reason":"marginfi_partition_file_count","observed":len(mf_files),"expected":23})
for p in mf_files:
    for e in iter_array(p,"enriched_rows"):
        sem=e.get("semantic_accounts") or {}
        bank=sem.get("asset_bank")
        mint=bank_map.get(bank)
        if not mint:
            errors.append({"reason":"marginfi_asset_bank_unresolved","bank":bank,"signature":e.get("signature"),"file":str(p)})
            continue
        add_event("marginfi",e.get("instruction_class") or "lending_account_liquidate",
                  "mint:"+mint,e.get("timestamp"),e.get("signature"))

# Save0c: unit events already contain collateral-underlying when direct; terminal extension fills only frozen unresolved reserves.
s0_files=files_sorted(args.save0c_units,"save0c-")
if len(s0_files)!=37:
    errors.append({"reason":"save0c_partition_file_count","observed":len(s0_files),"expected":37})
for p in s0_files:
    for e in iter_array(p,"event_units"):
        cu=e.get("collateral_underlying") or {}
        mint=cu.get("mint")
        if not mint:
            mint=save_ext.get(e.get("withdraw_reserve"))
        if not mint:
            errors.append({"reason":"save0c_collateral_underlying_unresolved",
                           "reserve":e.get("withdraw_reserve"),"signature":e.get("signature"),"file":str(p)})
            continue
        add_event("save0c","LiquidateObligation","mint:"+mint,e.get("timestamp"),e.get("signature"))

# Kamino + Save11: select frozen receipt precedence from explicit authority directories.
# Kamino original V0.1: kamino-YYYYMM.json
# Kamino V0.3 recovery: unit-kamino-YYYYMM.json
# Save11 V0.4 authority: save11-YYYYMM.json from save11_v04 only.
ks_root=Path(args.ks_units)
ks_original=ks_root/"original"
ks_recovery=ks_root/"recovery"
ks_save11_v04=ks_root/"save11_v04"
expected_orig_k=[f"kamino-{y}{m:02d}.json" for y,m in [(2023,11),(2023,12),(2024,1),(2024,2)]]
expected_rec_k=[f"unit-kamino-2024{m:02d}.json" for m in range(3,13)]
expected_save=[f"save11-2024{m:02d}.json" for m in range(7,13)]
ks_files=[]

for name in expected_orig_k:
    hits=sorted(ks_original.rglob(name))
    if len(hits)!=1:
        errors.append({"reason":"kamino_original_receipt_selection","basename":name,
                       "observed":len(hits),"files":[str(x) for x in hits]})
    else:
        ks_files.append(hits[0])

for name in expected_rec_k:
    hits=sorted(ks_recovery.rglob(name))
    if len(hits)!=1:
        errors.append({"reason":"kamino_recovery_receipt_selection","basename":name,
                       "observed":len(hits),"files":[str(x) for x in hits]})
    else:
        ks_files.append(hits[0])

for name in expected_save:
    hits=sorted(ks_save11_v04.rglob(name))
    if len(hits)!=1:
        errors.append({"reason":"save11_v04_receipt_selection","basename":name,
                       "observed":len(hits),"files":[str(x) for x in hits]})
    else:
        ks_files.append(hits[0])

if len(ks_files)!=20:
    errors.append({"reason":"kamino_save11_selected_partition_file_count","observed":len(ks_files),"expected":20})

for p in ks_files:
    proto="save11" if p.name.startswith("save11-") else "kamino"
    cls=("liquidate_obligation_and_redeem_reserve_collateral" if proto=="kamino"
         else "LiquidateObligationAndRedeemReserveCollateral")
    for e in iter_array(p,"event_units"):
        mint=(e.get("collateral_underlying") or {}).get("mint")
        if not mint:
            errors.append({"reason":"ks_collateral_underlying_unresolved","protocol":proto,
                           "signature":e.get("signature"),"file":str(p)});continue
        add_event(proto,cls,"mint:"+mint,e.get("timestamp"),e.get("signature"))

# Drift: field enrichment contains protocol-native market identity. Keep ordered tuples exactly frozen.
dr_files=files_sorted(args.drift_field,"drift-")
if len(dr_files)!=86:
    errors.append({"reason":"drift_partition_file_count","observed":len(dr_files),"expected":86})
for p in dr_files:
    for e in iter_array(p,"enriched_rows"):
        cls=e.get("class") or e.get("instruction_class")
        mi=e.get("market_identity") or {}
        if cls=="liquidate_perp":
            market=f"perp:{mi.get('perp_market_index')}" if "perp_market_index" in mi else None
        elif cls=="liquidate_spot":
            market=(f"spotpair:{mi.get('asset_spot_market_index')}:{mi.get('liability_spot_market_index')}"
                    if "asset_spot_market_index" in mi and "liability_spot_market_index" in mi else None)
        elif cls in ("liquidate_borrow_for_perp_pnl","liquidate_perp_pnl_for_deposit"):
            market=(f"perpspot:{mi.get('perp_market_index')}:{mi.get('spot_market_index')}"
                    if "perp_market_index" in mi and "spot_market_index" in mi else None)
        else:
            errors.append({"reason":"unknown_drift_class","class":cls,"signature":e.get("signature")});continue
        add_event("drift",cls,market,e.get("timestamp"),e.get("signature"))

for c in counters.values():c.finish_all()

primary=counters[PRIMARY]
disc=int(primary.aggregate.get("discovery",0));oos=int(primary.aggregate.get("oos",0))
sample_errors=[]
if disc<1000:sample_errors.append({"reason":"primary_discovery_clusters_below_gate","observed":disc,"required":1000})
if oos<500:sample_errors.append({"reason":"primary_oos_clusters_below_gate","observed":oos,"required":500})

subgroups=[]
for protocol,cls in sorted(first_event):
    fd=first_event[(protocol,cls)]
    d=int(primary.subgroup.get(("discovery",protocol,cls),0))
    o=int(primary.subgroup.get(("oos",protocol,cls),0))
    late=fd>=DISCOVERY_END
    if late:
        status=("EXTERNAL_CONFIRMATORY_INFERENTIAL" if o>=200
                else "DESCRIPTIVE_ONLY_INSUFFICIENT_INDEPENDENT_N")
    else:
        status=("INFERENTIAL_DISCOVERY_AND_OOS" if d>=200 and o>=100
                else "DESCRIPTIVE_ONLY_INSUFFICIENT_INDEPENDENT_N")
    subgroups.append({"protocol":protocol,"class":cls,"first_event":fd.isoformat().replace("+00:00","Z"),
                      "late_launch_external_confirmatory":late,
                      "discovery_clusters":d,"oos_clusters":o,"status":status})

assets=[]
asset_keys=set()
for split,protocol,cls,market in primary.asset:
    asset_keys.add((protocol,cls,market))
for protocol,cls,market in sorted(asset_keys):
    d=int(primary.asset.get(("discovery",protocol,cls,market),0))
    o=int(primary.asset.get(("oos",protocol,cls,market),0))
    status=("INFERENTIAL" if d>=200 and o>=100 else "DESCRIPTIVE_ONLY_INSUFFICIENT_INDEPENDENT_N")
    assets.append({"protocol":protocol,"class":cls,"primary_market_identity":market,
                   "discovery_clusters":d,"oos_clusters":o,"status":status})

if errors:
    classification="SOURCE_SAMPLE_GATE_BLOCKED_FAIL_CLOSED"
elif sample_errors:
    classification="SAMPLE_GATE_BLOCKED_FOR_PRIMARY_INFERENCE"
else:
    classification="SOURCE_SAMPLE_GATE_PASS"

def file_sha256(path):
    h=hashlib.sha256()
    with open(path,"rb") as fh:
        for block in iter(lambda:fh.read(1024*1024),b""):h.update(block)
    return h.hexdigest()

cluster_file_sha=file_sha256(CLUSTER_OUT) if CLUSTER_OUT.exists() else None
cluster_file_bytes=CLUSTER_OUT.stat().st_size if CLUSTER_OUT.exists() else 0

receipt={
 "schema_version":"0.1","lab_id":"DEFI-LIQUIDATION-SHOCK-001","classification":classification,
 "global_field_classification":(global_receipt or {}).get("classification"),
 "primary_cluster_quiet_seconds":PRIMARY,
 "primary":{"discovery_cluster_count":disc,"oos_cluster_count":oos,
            "protected_boundary_cluster_exclusion_count":primary.protected_cross,
            "total_cluster_count_including_protected_boundary":primary.total_clusters,
            "total_realized_event_count":primary.total_events,
            "max_events_in_one_cluster":primary.max_event_count,
            "cluster_event_count_histogram":dict(primary.event_count_hist),
            "emitted_cluster_count":primary.emitted_cluster_count},
 "sensitivity":{
   str(w):{"discovery_cluster_count":int(c.aggregate.get("discovery",0)),
           "oos_cluster_count":int(c.aggregate.get("oos",0)),
           "protected_boundary_cluster_exclusion_count":c.protected_cross,
           "total_cluster_count_including_protected_boundary":c.total_clusters}
   for w,c in counters.items() if w!=PRIMARY},
 "subgroups":subgroups,"asset_strata":assets,
 "source_identity_error_count":len(errors),"source_identity_errors":errors[:500],
 "sample_gate_error_count":len(sample_errors),"sample_gate_errors":sample_errors,
 "cluster_census":{"file":str(CLUSTER_OUT),"sha256":cluster_file_sha,
                   "bytes":cluster_file_bytes,"row_count":primary.emitted_cluster_count,
                   "contains_prices":False,"contains_returns":False},
 "frozen_authorities":["CASCADE_CLUSTERING_FREEZE_V0.1.md",
                       "SOURCE_SAMPLE_GATE_FREEZE_V0.1.md",
                       "SOURCE_SAMPLE_GATE_KAMINO_UNIT_PRECEDENCE_ADDENDUM_V0.2.md",
                       "SOURCE_SAMPLE_GATE_SAVE11_UNIT_PRECEDENCE_ADDENDUM_V0.3.md",
                       "PRE_DISCOVERY_TEMPORAL_HOLDOUT_FREEZE_V0.1.md"],
 "final_unit_receipts":{"marginfi":mr_path,"save0c":su_path},
 "firewall":{"prices":False,"returns":False,"pnl":False,"directional_outcomes":False,
             "economic_outcomes":False,"protected_market_outcomes_2025_2026":False,
             "post_outcome_tuning":False,"live_trading":False,"orders":False,
             "wallets":False,"exchange_mutation":False,"merge_main":False}
}
OUT.write_text(json.dumps(receipt,indent=2,sort_keys=True)+"\n")
print(json.dumps({"classification":classification,"discovery_clusters":disc,"oos_clusters":oos,
                  "event_count":primary.total_events,"source_identity_errors":len(errors),
                  "sample_gate_errors":len(sample_errors)},indent=2))
if classification=="SOURCE_SAMPLE_GATE_BLOCKED_FAIL_CLOSED":raise SystemExit(2)
if classification!="SOURCE_SAMPLE_GATE_PASS":raise SystemExit(3)
