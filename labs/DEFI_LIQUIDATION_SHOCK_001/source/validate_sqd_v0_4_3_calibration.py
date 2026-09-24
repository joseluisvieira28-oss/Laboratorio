#!/usr/bin/env python3
import argparse,json
from pathlib import Path

ap=argparse.ArgumentParser()
ap.add_argument("--dir",required=True)
ap.add_argument("--protocol",required=True)
ap.add_argument("--known-signature",default="")
ap.add_argument("--require-empty-termination",action="store_true")
args=ap.parse_args()

root=Path(args.dir)
m=json.loads((root/"MANIFEST.json").read_text())
assert m.get("protocol")==args.protocol
assert m.get("classification")=="PARTITION_COMPLETE"
assert m.get("anomaly_count")==0
receipts=[p for p in root.glob("*.json") if p.name!="MANIFEST.json"]
assert len(receipts)==1
r=json.loads(receipts[0].read_text())
assert r.get("stream_complete") is True
assert r.get("anomaly_count")==0

if args.known_signature:
    rows=r.get("rows") or []
    assert any(x.get("signature")==args.known_signature for x in rows), "known signature missing"

if args.require_empty_termination:
    ev=r.get("termination_evidence") or []
    assert any(x.get("reason")=="EMPTY_NDJSON_DOCUMENTED_STREAM_TERMINATION" for x in ev), "documented empty termination missing"

print(json.dumps({
    "classification":"V043_CALIBRATION_SUBGATE_PASS",
    "protocol":args.protocol,
    "known_signature_recovered":bool(args.known_signature),
    "empty_stream_termination_proven":args.require_empty_termination,
    "successful_instruction_count":r.get("successful_instruction_count"),
    "failed_attempt_count":r.get("failed_attempt_count"),
    "anomaly_count":r.get("anomaly_count"),
},indent=2))
