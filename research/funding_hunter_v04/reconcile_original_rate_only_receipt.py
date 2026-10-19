"""Ex post read-only descriptive audit of the already frozen V04 receipt.

NO MARKET API OR REANALYSIS. No threshold or parameter edits. This script
reuses the 28-day receipt sealed in original GitHub run 39242521078.
"""
import argparse,json
from collections import Counter
from decimal import Decimal
from pathlib import Path
def report(data):
    if data.get("status")!="RATE_ONLY_SCREEN_NOT_VENUE_EXECUTION":
        raise ValueError("RECEIPT_NOT_COMPLETED")
    days=data["all_predeclared_days"]
    if len(days)!=28:raise ValueError("NOT_ALL_28_DAYS")
    if not all(d["status"]=="FLAT_PREDECLARED_THRESHOLD" for d in days):
        raise ValueError("SOURCE_RESULTS_CHANGED_OR_EXPECTED_FLAT_CENSUS_MISSING")
    if not all(d["strategy_position"]=="NONE" for d in days):
        raise ValueError("INCONSISTENT_FLAT_POSITIONS")
    rates=[Decimal(d["pre_entry_normalized_funding_diff_bps_hour"]) for d in days]
    if not all(abs(v)<Decimal(".5") for v in rates):
        raise ValueError("PREDECLARED_THRESHOLD_VIOLATED")
    custody=data.get("archive_source_receipts",{})
    if set(custody)!={"LINEAR","INVERSE"}:raise ValueError("MISSING_SOURCE_CUSTODY")
    for v in custody.values():
        if int(v.get("rows",0))<50 or len(v.get("archive_local_SHA256",""))!=64:
            raise ValueError("UNVERIFIED_OFFICIAL_MONTH_SOURCE")
    return {"status":"V04_ORIGINAL_RECEIPT_CONFIRMED_28_OF_28_FLAT",
      "source":"READ_ONLY_PREVIOUS_ACTIONS_ARTIFACT_39242521078",
      "evaluated_all_original_UTC_days":len(days),
      "eligible_original_signals":0,"original_strategy_fills":0,
      "min_preentry_normalized_linear_minus_inverse_bps_per_hour":str(min(rates)),
      "max_preentry_normalized_linear_minus_inverse_bps_per_hour":str(max(rates)),
      "max_absolute_preentry_rate_differential_bps_per_hour":str(max(map(abs,rates))),
      "max_absolute_assuming_unchanged_rate_for_24h_bps_not_realized":str(max(map(abs,rates))*24),
      "threshold_frozen_bps_per_hour":"0.5",
      "original_archive_month_source_rows":{k:v["rows"] for k,v in custody.items()},
      "original_archive_UTC_first_and_last":{k:[v["first_utc"],v["last_utc"]] for k,v in custody.items()},
      "source_observed_interval_minutes":{k:v["observed_intervals_minutes"] for k,v in custody.items()},
      "max_differential_insufficient_for_original_trigger":True,
      "funding_PnL_calculated":False,
      "net_executable_profit_proven":False,
      "protected_2026_opened":False,
      "trading_authority":"NONE"}
def main():
    p=argparse.ArgumentParser()
    p.add_argument("--receipt",type=Path,required=True)
    a=p.parse_args()
    x=report(json.loads(a.receipt.read_text()))
    print("V04_INDEPENDENT_28_DAY_CENSUS",json.dumps(x,sort_keys=True))
    d=Path("research/funding_hunter_v04/receipts")
    d.mkdir(parents=True,exist_ok=True)
    (d/"V04_ORIGINAL_SOURCE_RECEIPT_RECONCILIATION.json").write_text(json.dumps(x,indent=2,sort_keys=True)+"\n")
if __name__=="__main__":main()
