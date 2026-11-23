#!/usr/bin/env python3
"""BINANCE-005: immutable code + one dated PR marker + public runner gate."""
from __future__ import annotations
import datetime as dt
import hashlib
import json
import os
from pathlib import Path

REPO=Path(__file__).resolve().parents[2]
PINNED = {
    "research/binance_diamante004/PROTOCOL.md":"b1b8d2aa2b9dd4853e04671de0d96336ae895d1b",
    "research/binance_diamante004/capture_forward.py":"ef8a987e026656cd3a60d402761c21078dee3ca7",
    "research/binance_diamante004/study.py":"58cf6af9c0ba26da2ac9efa700c103b93c7580b5",
    "research/binance_diamante004/verify_offline.py":"33ca9731cbbb2d4f22db8d5309d4616bfe3ca616",
    "research/binance_diamante003/book_core.py":"9b2a92455d36dc251ec99a2754c07a7f91a9af91",
}
FIRST=dt.date(2026,11,23)
LAST=dt.date(2026,12,23)
def git_blob_sha(raw:bytes)->str:
    return hashlib.sha1(b"blob "+str(len(raw)).encode()+b"\\0"+raw).hexdigest()

def check(today=None, base=None, private=None):
    today=today or dt.datetime.now(dt.timezone.utc).date()
    base=Path(base) if base else REPO
    if private is None:
        private=os.getenv("GITHUB_REPOSITORY_PRIVATE","").lower()=="true"
    if private:raise RuntimeError("PRIVATE_REPO_NO_FREE_RUNNER_ASSUMPTION")
    if os.getenv("GITHUB_REPOSITORY") and os.getenv("GITHUB_REPOSITORY")!="joseluisvieira28-oss/Laboratorio":
        raise RuntimeError("WRONG_REPOSITORY")
    if not (FIRST<=today<=LAST):
        raise RuntimeError("OUTSIDE_FROZEN_31_DAY_DATE_WINDOW")
    for rel,expected in PINNED.items():
        actual=git_blob_sha((base/rel).read_bytes())
        if actual!=expected:
            raise RuntimeError("FROZEN_004_SOURCE_DRIFT_"+rel+"_"+actual)
    marker_dir=base/"research/binance_diamante005/requests"
    markers=sorted(p for p in marker_dir.glob("*.txt") if p.is_file())
    if not markers or len(markers)!=len(set(p.stem for p in markers)):
        raise RuntimeError("MISSING_OR_DUPLICATE_MARKER")
    for p in markers:
        try: day=dt.date.fromisoformat(p.stem)
        except ValueError as e:raise RuntimeError("BAD_MARKER_DATE") from e
        if day<FIRST or day>LAST or p.read_text(encoding="utf-8").strip()!=("AUTHORIZE_READONLY_ONE_CAPTURE_UTC_DAY="+p.stem):
            raise RuntimeError("WRONG_OR_TAMPERED_MARKER_"+p.name)
    if markers[-1].stem!=today.isoformat():
        raise RuntimeError("LATEST_MARKER_NOT_CURRENT_UTC_DAY")
    return {"status":"FROZEN_SOURCE_AND_DATED_MARKER_PASS_ONLY","utc_date":today.isoformat(),
            "frozen_original_blobs":PINNED,"marker_count":len(markers),
            "public_repo_runner_only":True,"no_trades":True}

def main():
    result=check()
    print(json.dumps(result,indent=2,sort_keys=True))
    ev=Path("binance004-evidence")
    ev.mkdir(exist_ok=True)
    p=ev/"binance005_daily_guard.json"
    p.write_text(json.dumps(result,indent=2,sort_keys=True)+"\n")
if __name__=="__main__":main()
