#!/usr/bin/env python3
import json
from pathlib import Path

BASE=Path("labs/DEFI_LIQUIDATION_SHOCK_001")
checks=[]
errors=[]

def read(path):
    p=Path(path)
    if not p.exists():
        errors.append({"reason":"missing_file","path":str(p)})
        return ""
    return p.read_text()

def require(name, text, needle):
    ok=needle in text
    checks.append({"check":name,"pass":ok,"needle":needle})
    if not ok:
        errors.append({"reason":"required_wiring_missing","check":name,"needle":needle})

collector=read(BASE/"source/collect_global_field_gate_artifacts_v0_1.py")
adjudicator=read(BASE/"source/adjudicate_global_field_coverage_final_v0_1.py")
builder=read(BASE/"source/build_source_cluster_sample_gate_v0_1.py")
sample_wf=read(".github/workflows/dls-source-cluster-sample-gate-v01.yml")
finalizer=read(BASE/"source/finalize_pre_discovery_authority_v0_1.py")

require("collector_field_v03","".join(collector.split()),'"kamino_save11_field":["dls-kamino-save11-field-enrichment-population-v03","dls-kamino-save11-field-enrichment-population-v02","dls-kamino-save11-field-enrichment-population-v01"]')
require("collector_unit_v04","".join(collector.split()),'"kamino_save11_units":["dls-kamino-save11-unit-metadata-population-v04","dls-kamino-save11-unit-metadata-population-v03","dls-kamino-save11-unit-metadata-population-v02","dls-kamino-save11-unit-metadata-population-v01"]')
require("adjudicator_field_v03",adjudicator,'"KAMINO_SAVE11_FIELD_ENRICHMENT_POPULATION_RECEIPT_V0.3.json"')
require("adjudicator_unit_v04",adjudicator,'"KAMINO_SAVE11_UNIT_METADATA_POPULATION_RECEIPT_V0.4.json"')
require("adjudicator_v04_addenda",adjudicator,'GLOBAL_FIELD_COVERAGE_FINAL_GATE_VERSION_PRECEDENCE_ADDENDUM_V0.4.md + GLOBAL_FIELD_FINALIZER_ARTIFACT_SELECTION_ADDENDUM_V0.4.md')
require("sample_workflow_save11_v04",sample_wf,'pattern: dls-save11-unit-v04-*')
require("sample_workflow_v04_path",sample_wf,'path: ks_units/save11_v04')
require("builder_save11_v04_dir",builder,'ks_save11_v04=ks_root/"save11_v04"')
require("builder_save11_v04_selection",builder,'"reason":"save11_v04_receipt_selection"')
require("builder_save11_v04_authority",builder,'"SOURCE_SAMPLE_GATE_SAVE11_UNIT_PRECEDENCE_ADDENDUM_V0.3.md"')
for doc in [
 "GLOBAL_FIELD_COVERAGE_FINAL_GATE_VERSION_PRECEDENCE_ADDENDUM_V0.4.md",
 "GLOBAL_FIELD_FINALIZER_ARTIFACT_SELECTION_ADDENDUM_V0.4.md",
 "SOURCE_SAMPLE_GATE_SAVE11_UNIT_PRECEDENCE_ADDENDUM_V0.3.md",
]:
    require("final_authority_doc_"+doc,finalizer,f'"{doc}"')
    if not (BASE/doc).exists():
        errors.append({"reason":"missing_frozen_addendum","document":doc})

classification="DLS_PRE_DISCOVERY_WIRING_AUDIT_PASS" if not errors else "DLS_PRE_DISCOVERY_WIRING_AUDIT_BLOCKED"
receipt={
 "schema_version":"0.9",
 "lab_id":"DEFI-LIQUIDATION-SHOCK-001",
 "classification":classification,
 "check_count":len(checks),
 "pass_count":sum(1 for c in checks if c["pass"]),
 "error_count":len(errors),
 "checks":checks,
 "errors":errors,
 "firewall":{
   "prices_opened":False,"returns_opened":False,"pnl_opened":False,
   "direction_opened":False,"usd_notional_opened":False,"economic_outcomes_opened":False,
   "protected_2025_2026_opened":False,"post_outcome_tuning":False,
   "live_trading":False,"orders":False,"wallets":False,"exchange_mutation":False,"merge_main":False
 }
}
out=BASE/"DLS_PRE_DISCOVERY_WIRING_AUDIT_RECEIPT_V0.9.json"
out.write_text(json.dumps(receipt,indent=2,sort_keys=True)+"\n")
print(json.dumps(receipt,indent=2,sort_keys=True))
if classification!="DLS_PRE_DISCOVERY_WIRING_AUDIT_PASS":
    raise SystemExit(2)
