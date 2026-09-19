#!/usr/bin/env python3
"""Canonical aggregate adjudicator for OEG signed-flow corpus source V0.5."""
from __future__ import annotations
import hashlib,json,sys
from collections import Counter
from pathlib import Path

HERE=Path(__file__).resolve().parent
AUTH_PATH=HERE/"SIGNED_FLOW_CORPUS_AUTHORITY_V0.5.json"
AUTH=json.loads(AUTH_PATH.read_text(encoding="utf-8"))
OUT=Path("artifacts/options_expiry_gamma_signed_flow_corpus_v05")

def main()->int:
    files=sorted(Path("downloaded_signed_flow_shards").rglob("shard_*.json"))
    result={"lab_id":AUTH["lab_id"],"source_gate_id":AUTH["source_gate_id"],"classification":None,
            "failure":None,"total_dates":0,"passing_dates":0,"passing_dates_by_year":{},
            "technical_error_dates":0,"aggregate_gate_checks":{},
            "api_key_used":False,"subscription_purchase":False,"option_values_retained":False,
            "gamma_exposure_computed":False,"dealer_inventory_computed":False,"dealer_gamma_sign_computed":False,
            "btc_price_outcomes_opened":False,"returns_opened":False,"pnl_opened":False,
            "access_2025":False,"access_2026":False,"live_trading":False,"exchange_mutation":False,
            "wallet_access":False,"merge_to_main":False}
    try:
        if len(files)!=int(AUTH["shard_count"]):
            raise RuntimeError(f"expected {AUTH['shard_count']} shard receipts, got {len(files)}")
        rows=[json.loads(p.read_text(encoding="utf-8")) for p in files]
        ids=sorted(int(x["shard_id"]) for x in rows)
        if ids!=list(range(int(AUTH["shard_count"]))): raise RuntimeError(f"shard ids mismatch {ids}")
        expected=list(AUTH["deterministic_dates"])
        probes=[]
        technical=0
        for r in rows:
            if r.get("source_gate_id")!=AUTH["source_gate_id"]: raise RuntimeError("source gate id mismatch")
            if r.get("authority_sha256")!=hashlib.sha256(AUTH_PATH.read_bytes()).hexdigest(): raise RuntimeError("authority hash mismatch")
            if any(bool(r.get(k)) for k in ["api_key_used","subscription_purchase","option_values_retained","gamma_exposure_computed",
                   "dealer_inventory_computed","dealer_gamma_sign_computed","btc_price_outcomes_opened","returns_opened",
                   "pnl_opened","access_2025","access_2026","live_trading","exchange_mutation","wallet_access","merge_to_main"]):
                raise RuntimeError("firewall violation")
            technical += int(r.get("technical_error_dates",0))
            probes.extend(r.get("probes") or [])
        got=[str(x.get("date")) for x in probes]
        if len(got)!=48 or len(set(got))!=48 or sorted(got)!=sorted(expected):
            raise RuntimeError("48-date deterministic corpus coverage mismatch")
        pass_dates=[x for x in probes if bool(x.get("pass"))]
        by_year=Counter(str(x["date"])[:4] for x in pass_dates)
        g=AUTH["aggregate_gates"]
        checks={
          "passing_dates_ge_min":len(pass_dates)>=int(g["minimum_total_passing_dates"]),
          "distinct_years_ge_min":len([y for y in ("2021","2022","2023","2024") if by_year[y]>0])>=int(g["minimum_distinct_calendar_years"]),
          "passing_dates_per_year_ge_min":all(by_year[y]>=int(g["minimum_passing_dates_per_calendar_year"]) for y in ("2021","2022","2023","2024")),
          "technical_errors_le_max":technical<=int(g["technical_error_dates_maximum"])
        }
        if not checks["technical_errors_le_max"]:
            cls=AUTH["classifications"]["technical_failure"]
        elif all(checks.values()):
            cls=AUTH["classifications"]["pass"]
        else:
            cls=AUTH["classifications"]["insufficient"]
        result.update({"classification":cls,"total_dates":len(probes),"passing_dates":len(pass_dates),
                       "passing_dates_by_year":dict(sorted(by_year.items())),"technical_error_dates":technical,
                       "aggregate_gate_checks":checks,
                       "date_results":[{"date":x.get("date"),"pass":bool(x.get("pass")),
                                        "technical_error":x.get("technical_error"),"metrics":x.get("metrics"),
                                        "gate_checks":x.get("gate_checks")} for x in sorted(probes,key=lambda z:z["date"])]})
    except Exception as exc:
        result["classification"]=AUTH["classifications"]["technical_failure"]
        result["failure"]=f"{type(exc).__name__}: {str(exc)[:1200]}"
    OUT.mkdir(parents=True,exist_ok=True)
    p=OUT/"SIGNED_FLOW_CORPUS_SOURCE_RESULT_V0.5.json"
    p.write_text(json.dumps(result,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    manifest={"authority_sha256":hashlib.sha256(AUTH_PATH.read_bytes()).hexdigest(),
              "result_sha256":hashlib.sha256(p.read_bytes()).hexdigest()}
    (OUT/"manifest.json").write_text(json.dumps(manifest,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    print(json.dumps({"classification":result["classification"],"total_dates":result["total_dates"],
                      "passing_dates":result["passing_dates"],"passing_dates_by_year":result["passing_dates_by_year"],
                      "technical_error_dates":result["technical_error_dates"],"returns_opened":False,"pnl_opened":False},sort_keys=True))
    return 0

if __name__=="__main__": raise SystemExit(main())
