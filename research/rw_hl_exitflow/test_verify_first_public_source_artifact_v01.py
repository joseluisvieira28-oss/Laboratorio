"""Synthetic regression tests for append-only prior GitHub source artifact recovery."""
import hashlib,json,tempfile,unittest
from pathlib import Path
from verify_first_public_source_artifact_v01 import verify_dir,RecoveryBlocked
from rw_hl_public_source_gate_v01 import canon

BASENAME="2026-10-09T13-45-40_212358Z_37939142048"

def fixture(root):
    folder=Path(root)/BASENAME;folder.mkdir()
    records=[];old="0"*64
    for i in range(1,4):
        ts=f"2026-10-09T13:{45+i:02d}:40Z"
        ctx={"market_context":[{"coin":c,"openInterest":"2","markPx":"50",
               "funding":"-0.001"} for c in ("BTC","ETH","SOL","DOGE","XRP")]}
        obj={"lab_id":"RW-HL-EXITFLOW-001","read_utc":ts,"ordinal":i,
             "historical_outcome":False,"trading_authority":"NONE","context":ctx}
        raw=canon(obj)+b"\n"
        name=f"SNAPSHOT_{i:02d}.json"
        (folder/name).write_bytes(raw)
        old=hashlib.sha256(bytes.fromhex(old)+raw).hexdigest()
        records.append({"ordinal":i,"file":name,"received_utc":ts,
          "sha256":hashlib.sha256(raw).hexdigest(),"chain_sha256":old,"valid_markets":5})
    receipt={"lab_id":"RW-HL-EXITFLOW-001",
        "state":"THREE_PUBLIC_SNAPSHOTS_DURABLY_READY",
        "economic_outcomes_opened":False,"trading_authority":"NONE",
        "observations":records,"snapshots_received":3}
    (folder/"CAPTURE_RECEIPT.json").write_bytes(canon(receipt)+b"\n")
    return folder

class VerifyRecovery(unittest.TestCase):
    def test_valid_chain(self):
        with tempfile.TemporaryDirectory() as tmp:
            self.assertEqual(verify_dir(fixture(tmp))["snapshots"],3)
    def test_tamper_blocks(self):
        with tempfile.TemporaryDirectory() as tmp:
            p=fixture(tmp)/"SNAPSHOT_02.json"
            p.write_bytes(p.read_bytes()+b"x")
            with self.assertRaises(RecoveryBlocked):verify_dir(p.parent)
    def test_missing_snapshot_blocks(self):
        with tempfile.TemporaryDirectory() as tmp:
            folder=fixture(tmp);(folder/"SNAPSHOT_02.json").unlink()
            with self.assertRaises(RecoveryBlocked):verify_dir(folder)
    def test_source_run_identity(self):
        with tempfile.TemporaryDirectory() as tmp:
            folder=fixture(tmp);new=folder.parent/"WRONG_RUN"
            folder.rename(new)
            with self.assertRaises(RecoveryBlocked):verify_dir(new)
    def test_authority_mismatch(self):
        with tempfile.TemporaryDirectory() as tmp:
            folder=fixture(tmp);p=folder/"CAPTURE_RECEIPT.json"
            r=json.loads(p.read_text());r["economic_outcomes_opened"]=True
            p.write_text(json.dumps(r))
            with self.assertRaises(RecoveryBlocked):verify_dir(folder)
    def test_chain_mismatch(self):
        with tempfile.TemporaryDirectory() as tmp:
            folder=fixture(tmp);p=folder/"CAPTURE_RECEIPT.json"
            r=json.loads(p.read_text());r["observations"][1]["chain_sha256"]="0"*64
            p.write_text(json.dumps(r))
            with self.assertRaises(RecoveryBlocked):verify_dir(folder)

if __name__=="__main__":unittest.main()
