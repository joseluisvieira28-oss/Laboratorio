#!/usr/bin/env python3
"""Synthetic no-market-data QA for L2-RESILIENCY-001 schema auditor."""
from __future__ import annotations
import hashlib
import json
import tempfile
from pathlib import Path

import lz4.frame

import l2r_full_corpus_schema_audit_v01 as a


def rec(ts: int):
    bids=[{"px":str(60000-i),"sz":str(1+i/10),"n":i+1} for i in range(5)]
    asks=[{"px":str(60001+i),"sz":str(1+i/10),"n":i+1} for i in range(5)]
    return {"time":ts,"ver_num":1,"raw":{"channel":"l2Book","data":{"coin":"BTC","time":ts,"levels":[bids,asks]}}}


def md5(p: Path):
    h=hashlib.md5()
    h.update(p.read_bytes())
    return h.hexdigest()


def sha(p: Path):
    h=hashlib.sha256()
    h.update(p.read_bytes())
    return h.hexdigest()


def main():
    start,_=a.hour_bounds_ms("market_data/20240901/0/l2Book/BTC.lz4")
    with tempfile.TemporaryDirectory() as td:
        root=Path(td)
        p=root/"x.lz4"
        with lz4.frame.open(p,"wb") as f:
            for t in [start+1000,start+1600,start+1600,start+2200]:
                f.write((json.dumps(rec(t))+"\n").encode())
        m=md5(p)
        row={"key":"market_data/20240901/0/l2Book/BTC.lz4","content_length":p.stat().st_size,
             "sha256":sha(p),"md5":m,"etag":m}
        r=a.audit_object(p,row)
        assert r.record_count==4
        assert r.duplicate_timestamp_transitions==1

        bad=rec(start+3000)
        bad["raw"]["data"]["levels"][0][1]["px"]="999999"
        try:
            a.audit_record(bad,start,start+3600000)
        except a.AuditFailure:
            pass
        else:
            raise AssertionError("bad bid ordering did not fail")

        crossed=rec(start+4000)
        crossed["raw"]["data"]["levels"][0][0]["px"]="70000"
        try:
            a.audit_record(crossed,start,start+3600000)
        except a.AuditFailure:
            pass
        else:
            raise AssertionError("crossed book did not fail")

    print("L2_SCHEMA_AUDITOR_SYNTHETIC_PASS | NO MARKET OUTCOMES | NO SWEEPS | NO RETURNS | NO PNL")
    return 0


if __name__=="__main__":
    raise SystemExit(main())
