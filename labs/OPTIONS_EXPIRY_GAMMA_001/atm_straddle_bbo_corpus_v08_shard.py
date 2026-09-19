#!/usr/bin/env python3
"""Full 48-date BBO corpus shard V0.8.
Reuses the exact V0.7 per-date probe implementation; source-only.
"""
import json,os,sys
from pathlib import Path
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE))
import atm_straddle_bbo_source_v07_shard as v7
AUTH=json.loads((HERE/"ATM_STRADDLE_BBO_CORPUS_AUTHORITY_V0.8.json").read_text())
v7.AUTH=AUTH
OUT=Path("artifacts/oeg_atm_straddle_bbo_corpus_v08_shards");OUT.mkdir(parents=True,exist_ok=True)

def main():
    sid=int(os.environ["OEG_SHARD_ID"]);n=int(AUTH["shard_count"])
    idxs=[i for i in range(len(AUTH["deterministic_dates"])) if i%n==sid]
    if len(idxs)!=6:raise SystemExit(f"FAIL_CLOSED expected 6 indices got {len(idxs)}")
    rows=[]
    for k,idx in enumerate(idxs,1):
        os.environ["OEG_PROBE_INDEX"]=str(idx)
        rc=v7.main()
        p=Path("artifacts/oeg_atm_straddle_bbo_source_v07_shards")/f"probe_{idx}.json"
        rec=json.loads(p.read_text())
        rows.append(rec)
        print(f"OEG_BBO_V08_PROGRESS shard={sid} {k}/6 {rec['date']} pass={rec.get('pass')}",flush=True)
    result={"lab_id":AUTH["lab_id"],"source_gate_id":AUTH["source_gate_id"],"shard_id":sid,"shard_count":n,"rows":rows,
      "bid_ask_values_retained":False,"pnl_opened":False,"returns_opened":False,"access_2025":False,"access_2026":False,
      "live_trading":False,"exchange_mutation":False,"wallet_access":False,"merge_to_main":False}
    (OUT/f"shard_{sid}.json").write_text(json.dumps(result,indent=2,sort_keys=True)+"\n")
    print(json.dumps({"shard_id":sid,"dates":len(rows),"passing":sum(bool(x.get('pass')) for x in rows),"technical_errors":sum(bool(x.get('technical_error')) for x in rows)},sort_keys=True))
    return 0
if __name__=="__main__":sys.exit(main())
