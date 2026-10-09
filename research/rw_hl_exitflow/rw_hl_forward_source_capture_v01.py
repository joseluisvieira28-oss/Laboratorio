"""RW-HL-EXITFLOW-001: FIRST durable research-only Hyperliquid public source intake."""
import hashlib,json,os,time
from datetime import datetime,timezone
from pathlib import Path
import rw_hl_public_source_gate_v01 as pub

ROOT=Path(__file__).resolve().parent
SOURCE_PROOF=ROOT/"RW_HL_EXITFLOW_001_FIRST_PROSPECTIVE_SOURCE_CAPTURE_FREEZE_2026-10-09.md"
SAMPLE_N=3
DELAY_SECONDS=60

def stamp():
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%fZ")

def chain(prev,payload):
    return hashlib.sha256(bytes.fromhex(prev)+payload).hexdigest()

def capture_once(getter=pub.public_info):
    return pub.parse_public_market(getter({"type":"metaAndAssetCtxs"}))

def run():
    if "FIRST PROSPECTIVE SOURCE CAPTURE AUTHORITY" not in SOURCE_PROOF.read_text():
        raise pub.Blocked("PROSPECTIVE_SOURCE_FREEZE_MISSING")
    runid=os.getenv("GITHUB_RUN_ID","LOCAL")
    t0=stamp()
    safe_prefix=t0.replace(":","-").replace(".","_")
    out=ROOT/"intake"/t0[:10]/(safe_prefix+"_"+runid)
    out.mkdir(parents=True,exist_ok=False)
    records=[];previous="0"*64
    for i in range(SAMPLE_N):
        if i:time.sleep(DELAY_SECONDS)
        received=stamp()
        try:row=capture_once()
        except Exception:
            # No silent gap: preserve previously captured snapshots with hard BLOCK.
            receipt={"state":"PARTIAL_SOURCE_BLOCKED","reason":"PUBLIC_API_OR_SCHEMA_FAILURE",
                "successful_snapshots":len(records),"trading_authority":"NONE",
                "economic_outcomes_opened":False}
            (out/"CAPTURE_RECEIPT.json").write_bytes(pub.canon(receipt)+b"\n")
            raise
        payload={"lab_id":"RW-HL-EXITFLOW-001","read_utc":received,
           "ordinal":i+1,"observation_kind":"PUBLIC_MARKET_CTX_ONLY",
           "historical_outcome":False,"trading_authority":"NONE","context":row}
        raw=pub.canon(payload)+b"\n"
        p=out/("SNAPSHOT_%02d.json"%(i+1))
        with p.open("xb") as f:f.write(raw)
        digest=hashlib.sha256(raw).hexdigest()
        previous=chain(previous,raw)
        records.append({"ordinal":i+1,"file":p.name,"received_utc":received,
            "sha256":digest,"chain_sha256":previous,
            "valid_markets":row["valid_public_markets"]})
        print("CAPTURED_PUBLIC_SOURCE",i+1,row["valid_public_markets"],flush=True)
    report={"lab_id":"RW-HL-EXITFLOW-001","state":"THREE_PUBLIC_SNAPSHOTS_DURABLY_READY",
         "observations":records,"source":"public metaAndAssetCtxs Hyperliquid",
         "snapshots_expected":SAMPLE_N,"snapshots_received":len(records),
         "trading_authority":"NONE","economic_outcomes_opened":False,
         "new_listings_certified":False,"pressure_signal_computed":False,
         "profitability_claim":False,
         "append_only_under_new_path":True,
         "science":"source transport only; no forward return resolved"}
    (out/"CAPTURE_RECEIPT.json").write_bytes(pub.canon(report)+b"\n")
    print("SOURCE_CAPTURE_RECEIPT",json.dumps({"state":report["state"],"count":len(records),
         "chain":previous,"location":str(out)}),flush=True)

if __name__=="__main__":run()
