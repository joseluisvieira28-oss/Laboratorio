"""Verify exact prior-run public-source artifact before append-only GitHub recovery."""
import hashlib,json,sys
from pathlib import Path
import rw_hl_public_source_gate_v01 as pub

EXPECTED_RUN="37939142048"
EXPECTED_DAY="2026-10-09"
class RecoveryBlocked(ValueError):pass

def verify_dir(root):
    root=Path(root)
    if EXPECTED_RUN not in root.name or not root.name.startswith(EXPECTED_DAY+"T"):
        raise RecoveryBlocked("ARTIFACT_SOURCE_RUN_OR_DATE_UNBOUND")
    files=sorted(root.glob("SNAPSHOT_*.json"))
    if len(files)!=3:raise RecoveryBlocked("REQUIRED_EXACTLY_THREE_SOURCE_SNAPSHOTS")
    rp=root/"CAPTURE_RECEIPT.json"
    if not rp.exists():raise RecoveryBlocked("RECEIPT_MISSING")
    rec=json.loads(rp.read_text())
    if rec.get("lab_id")!="RW-HL-EXITFLOW-001" or rec.get("state")!="THREE_PUBLIC_SNAPSHOTS_DURABLY_READY":
        raise RecoveryBlocked("SOURCE_SCIENCE_ID_MISMATCH")
    if rec.get("economic_outcomes_opened") is not False or rec.get("trading_authority")!="NONE":
        raise RecoveryBlocked("OUTCOME_OR_EXECUTION_MISMATCH")
    entries=rec["observations"]
    if len(entries)!=3 or rec["snapshots_received"]!=3:
        raise RecoveryBlocked("RECEIPT_COUNT_MISMATCH")
    prev="0"*64;previous_time=""
    for i,(entry,path) in enumerate(zip(entries,files),start=1):
        raw=path.read_bytes()
        if entry["ordinal"]!=i or entry["file"]!=path.name or path.name!=f"SNAPSHOT_{i:02d}.json":
            raise RecoveryBlocked("ORDINAL_MISMATCH")
        if hashlib.sha256(raw).hexdigest()!=entry["sha256"]:
            raise RecoveryBlocked("SOURCE_BYTE_SHA256_MISMATCH")
        prev=hashlib.sha256(bytes.fromhex(prev)+raw).hexdigest()
        if prev!=entry["chain_sha256"]:raise RecoveryBlocked("IMMUTABLE_CHAIN_MISMATCH")
        obj=json.loads(raw)
        if (obj.get("lab_id")!="RW-HL-EXITFLOW-001" or obj.get("historical_outcome") is not False
            or obj.get("trading_authority")!="NONE" or obj.get("ordinal")!=i
            or obj.get("read_utc")!=entry["received_utc"]):
            raise RecoveryBlocked("RECEIPT_OBSERVATION_BINDING_MISMATCH")
        now=entry["received_utc"]
        if previous_time and now<=previous_time:raise RecoveryBlocked("NONMONOTONE_RECEIVE_TIME")
        previous_time=now
        values=obj.get("context",{})
        markets=values.get("market_context",[])
        if len(markets)!=entry["valid_markets"] or len(markets)<5:
            raise RecoveryBlocked("SOURCE_MARKET_COUNT_MISMATCH")
        if any(not isinstance(m,dict) or not {"coin","openInterest","markPx","funding"}<=set(m) for m in markets):
            raise RecoveryBlocked("SOURCE_PUBLIC_FIELDS_MISSING")
    return {"state":"VERIFIED_SOURCE_ONLY_RECOVERY","snapshots":3,"last_chain":prev,
       "input_run":EXPECTED_RUN,"input_utc_date":EXPECTED_DAY,
       "economic_outcomes_opened":False,"trading_authority":"NONE"}

if __name__=="__main__":
    try:print(json.dumps(verify_dir(sys.argv[1]),sort_keys=True))
    except (RecoveryBlocked,OSError,ValueError,IndexError,TypeError,KeyError) as e:
        print(json.dumps({"state":"SOURCE_RECOVERY_BLOCKED","reason":str(e)}))
        raise SystemExit(2)
