#!/usr/bin/env python3
"""Reaudit exact ORIGINAL real Oct30 GitHub public market-source artifact; NO model outcomes."""
import hashlib,json,pathlib,sys,zipfile
from btc_event10m_raw_replay_v06 import validate_eight
from btc_event10m_source_gates_v04 import asof
EXPECTED="a49052bce9e0ce8d7ba216bfcc00a5b9ca9ff5d474a06c591398b5553d1b567d"
FILENAMES={"okx_book_0.json","okx_book_1.json","okx_book_2.json",
"mexc_book_0.json","mexc_book_1.json","mexc_book_2.json",
"mexc_event_contract_detail.json","mexc_index.json"}
def run(path):
    content=pathlib.Path(path).read_bytes()
    if hashlib.sha256(content).hexdigest()!=EXPECTED:
        raise ValueError("ORIGINAL_SOURCE_ZIP_SHA256_MISMATCH")
    with zipfile.ZipFile(path) as z:
        needed={"source_receipt.json"}|{"raw/"+name for name in FILENAMES}
        if set(z.namelist())!=needed:raise ValueError("ORIGINAL_ZIP_MEMBER_MISMATCH")
        src=json.loads(z.read("source_receipt.json"))
        if src.get("status")!="FOUR_LEG_ASOF_SOURCE_PASS" or src.get("source_gate_all_pass") is not True:
            raise ValueError("ORIGINAL_SOURCE_NOT_PASS")
        packets=[row[key] for row in src["samples"] for key in ("okx_spot","mexc_futures")]
        packets.extend((src["product"],src["index"]))
        for x in packets:
            if hashlib.sha256(z.read("raw/"+x["raw_file"])).hexdigest()!=x["sha256"]:
                raise ValueError("ORIGINAL_SOURCE_RAW_SHA_MISMATCH")
        validate_eight(z,{"source_receipt":src})
        checks=asof(src["samples"],src["product"],src["index"],src["asof_ms"])
        if not all(checks.values()):raise ValueError("OLD_SOURCE_FAILS_NEW_2SEC_EXCHANGE_CLOCK")
    result={"study":"BTC_EVENT10M_REAL_SOURCE_ARCHIVE_INDEPENDENT_V06",
       "status":"ORIGINAL_SOURCE_RAW_SEMANTICS_AND_EXCHANGE_CLOCK_PASS",
       "original_run_id":41096454537,"original_artifact_id":12996537229,
       "original_zip_sha256":EXPECTED,"source_gates":checks,
       "verified_raw_http_sources":8,"market_outcomes_opened":0,
       "economic_edge_proven":False,"event_futures_real_settlement_parity":False,
       "trading_orders_or_account_reads":0}
    out=pathlib.Path("artifacts/btc_event10m_real_reaudit_v06")
    out.mkdir(parents=True,exist_ok=True)
    (out/"real_source_reaudit.json").write_text(json.dumps(result,indent=2,sort_keys=True)+"\n")
    print(json.dumps(result,indent=2,sort_keys=True))
if __name__=="__main__":
    if len(sys.argv)!=2:raise SystemExit("NEED_ORIGINAL_ARTIFACT_ZIP")
    run(sys.argv[1])
