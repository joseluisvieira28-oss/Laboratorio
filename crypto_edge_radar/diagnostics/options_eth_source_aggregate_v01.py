from __future__ import annotations
import argparse,gzip,json
from pathlib import Path

MONTHS=[f"2024-{m:02d}" for m in range(1,13)]
def main():
    ap=argparse.ArgumentParser(); ap.add_argument("--root",required=True); ap.add_argument("--out",required=True); a=ap.parse_args()
    root=Path(a.root); receipts=[]; all_ids=set(); global_dups=0
    missing=[]
    for m in MONTHS:
        matches=list(root.rglob(f"eth_{m}_receipt.json"))
        ids=list(root.rglob(f"eth_{m}_trade_ids.txt.gz"))
        if len(matches)!=1 or len(ids)!=1: missing.append(m); continue
        r=json.loads(matches[0].read_text()); receipts.append(r)
        with gzip.open(ids[0],"rt",encoding="utf-8") as f:
            for line in f:
                tid=line.strip()
                if not tid: continue
                if tid in all_ids: global_dups+=1
                else: all_ids.add(tid)
    sums=lambda k: sum(int(r.get(k,0) or 0) for r in receipts)
    transport=[r["month"] for r in receipts if r.get("transport_error")]
    source=[r["month"] for r in receipts if r.get("source_error")]
    empty=[r["month"] for r in receipts if int(r.get("rows",0))<=0]
    fail_data=bool(missing or empty or sums("timestamp_violations") or sums("missing_structural") or sums("instrument_parse_failures") or sums("duplicates_within_shard") or global_dups)
    if transport: verdict="SOURCE_GATE_BLOCKED_TRANSPORT"; rc=12
    elif source or fail_data: verdict="SOURCE_GATE_FAIL_DATA"; rc=2
    else: verdict="SOURCE_GATE_PASS"; rc=0
    out={"gate_id":"OPTIONS_ETH_001_SOURCE_GATE_V0.1_SHARDED","verdict":verdict,"requested_start_utc":"2024-01-01T00:00:00Z","requested_end_exclusive_utc":"2025-01-01T00:00:00Z",
         "months_received":[r["month"] for r in receipts],"missing_months":missing,"empty_months":empty,"transport_blocked_months":transport,"source_error_months":source,
         "rows":sums("rows"),"unique_trade_ids":len(all_ids),"duplicate_trade_ids_global":global_dups,"duplicates_within_shards":sums("duplicates_within_shard"),
         "timestamp_violations":sums("timestamp_violations"),"missing_structural_fields":sums("missing_structural"),"instrument_parse_failures":sums("instrument_parse_failures"),
         "invalid_iv_rows":sums("invalid_iv"),"invalid_index_price_rows":sums("invalid_index_price"),
         "skew_computed":False,"signal_computed":False,"forward_return_computed":False,"pnl_computed":False,"outcome_source_contacted":False,"year_2025_accessed":False}
    Path(a.out).write_text(json.dumps(out,indent=2,sort_keys=True)+"\n"); print(json.dumps(out,indent=2)); return rc
if __name__=="__main__": raise SystemExit(main())
