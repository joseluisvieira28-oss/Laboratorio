"""LOCAL-ONLY V05C importer for two user-downloaded historical OKX L2 files.

NEVER calls network. Never uploads/prints raw quotes. Requires a matching official
file name and keeps SHA256, format diagnostics and count-only reports. No alpha GO.
"""
from __future__ import annotations
import argparse,hashlib,json
from pathlib import Path
from research.convex_okx_l2_v05.catalogue_gate import CASES
from research.convex_okx_l2_v05.raw_l2_two_archives import (
    CASES_AT_T0,MAX_ZIP,audit_tar
)

def validate_one(case,path):
    fam,inst,day,epoch=case
    result={"instrument":inst,"expected_day":day,
            "status":"SOURCE_NOT_PROVEN","reason":"",
            "market_data_exported":False,"actual_broker_fill_verified":False,
            "historical_contract_multiplier_verified":False}
    try:
        if path is None:raise ValueError("USER_ARCHIVE_NOT_YET_SUPPLIED")
        src=Path(path)
        if not src.is_file() or src.is_symlink():raise ValueError("ARCHIVE_NOT_REGULAR_FILE")
        name=src.name
        if not (name.startswith(inst) and day in name and name.endswith(".tar.gz")):
            raise ValueError("WRONG_INSTRUMENT_DAY_OR_ARCHIVE_FILENAME")
        if src.stat().st_size>MAX_ZIP:raise ValueError("SAME_FROZEN_190MB_SOURCE_CAP")
        h=hashlib.sha256()
        with src.open("rb") as f:
            for chunk in iter(lambda:f.read(4_194_304),b""):
                h.update(chunk)
        result.update({"local_archive_transport_sha256_no_publisher_hash":h.hexdigest(),
                       "compressed_bytes":src.stat().st_size})
        metadata={"instrument":inst,"source_day":day,"filename":name}
        result.update(audit_tar(src,metadata,CASES_AT_T0[fam]))
        result["status"]=result.pop("status")
        result["reason"]="LOCAL_FILE_CUSTODY_ONLY_NO_PUBLISHER_CHECKSUM_OR_ACCOUNT_PROOF"
    except Exception as exc:
        result["status"]="SOURCE_BLOCKED"
        result["reason"]=type(exc).__name__+":"+str(exc)[:155]
    return result

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--sol-archive",type=Path)
    p.add_argument("--bnb-archive",type=Path)
    p.add_argument("--out",type=Path,default=Path("convex_v05c_private_local_receipts"))
    a=p.parse_args()
    cases={x[0]:x for x in CASES}
    vals=[
        validate_one(cases["SOL-USDT"],a.sol_archive),
        validate_one(cases["BNB-USDT"],a.bnb_archive)
    ]
    report={"status":"PERSONAL_RESEARCH_LOCAL_ONLY_NO_RAW_EXPORT",
            "cases":vals,"archives_uploaded":False,
            "official_publisher_checksum_verified":False,
            "broker_order_or_fill_verified":False,
            "independent_OOS":False,"trading_authority":"NONE"}
    a.out.mkdir(parents=True,exist_ok=True)
    out=a.out/"V05C_LOCAL_TWO_ARCHIVE_SOURCE_REPORT.json"
    out.write_text(json.dumps(report,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    for item in vals:print("LOCAL_GATE",json.dumps(item,sort_keys=True))
    print("SOURCE_REPORT_FILE",str(out))
if __name__=="__main__":
    main()
