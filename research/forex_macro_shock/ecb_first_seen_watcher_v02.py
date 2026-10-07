#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import re
import time
from datetime import datetime, timezone
from pathlib import Path

import requests

INDEX="https://www.ecb.europa.eu/press/govcdec/mopo/html/index.en.html"
UA={"User-Agent":"CryptoLab-ECB-FirstSeen/0.2"}
TARGET_DATE="2026-10-29"
TARGET_TOKEN="261029"
LINK_RE=re.compile(r'href=["\']([^"\']*ecb\.mp261029[^"\']*\.en\.html[^"\']*)["\']',re.I)


def utc(s):
    return datetime.fromisoformat(s.replace("Z","+00:00")).astimezone(timezone.utc)


def sha(b):
    return hashlib.sha256(b).hexdigest()


def get(url):
    started=datetime.now(timezone.utc)
    t0=time.perf_counter()
    r=requests.get(url,headers=UA,timeout=15)
    completed=datetime.now(timezone.utc)
    if r.status_code!=200:
        raise RuntimeError(f"HTTP_{r.status_code}:{url}")
    return r,{
        "request_started_utc":started.isoformat(),
        "request_completed_utc":completed.isoformat(),
        "latency_ms":round((time.perf_counter()-t0)*1000,3),
        "body_sha256":sha(r.content),
        "bytes":len(r.content),
        "status_code":r.status_code,
    }


def normalize_link(href):
    if href.startswith("http://") or href.startswith("https://"):
        return href
    if href.startswith("/"):
        return "https://www.ecb.europa.eu"+href
    return "https://www.ecb.europa.eu/press/govcdec/mopo/html/"+href


def find_target(html):
    m=LINK_RE.search(html)
    return normalize_link(m.group(1)) if m else None


def synthetic_selftest():
    sample='<a href="/press/pr/date/2026/html/ecb.mp261029~abcdef.en.html">Decision</a>'
    got=find_target(sample)
    assert got=="https://www.ecb.europa.eu/press/pr/date/2026/html/ecb.mp261029~abcdef.en.html"
    return True


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--start",required=True,help="UTC ISO")
    ap.add_argument("--end",required=True,help="UTC ISO")
    ap.add_argument("--interval-sec",type=float,default=2.0)
    ap.add_argument("--out",required=True)
    a=ap.parse_args()
    start,end=utc(a.start),utc(a.end)
    if start.date().isoformat()!=TARGET_DATE or end.date().isoformat()!=TARGET_DATE:
        raise SystemExit("FAIL_CLOSED_WRONG_TARGET_DATE")
    if not start<end:
        raise SystemExit("FAIL_CLOSED_BAD_WINDOW")
    synthetic_selftest()
    out=Path(a.out)
    out.parent.mkdir(parents=True,exist_ok=True)

    baseline_r,baseline_ev=get(INDEX)
    baseline={
        "index_sha256":baseline_ev["body_sha256"],
        "target_link_present":bool(find_target(baseline_r.text)),
        "captured_utc":baseline_ev["request_completed_utc"],
    }
    if baseline["target_link_present"]:
        raise SystemExit("FAIL_CLOSED_TARGET_ALREADY_PRESENT_AT_WATCHER_BASELINE")

    while datetime.now(timezone.utc)<start:
        time.sleep(min(5,max(0.1,(start-datetime.now(timezone.utc)).total_seconds())))

    polls=0
    errors=[]
    result=None
    while datetime.now(timezone.utc)<=end:
        try:
            r,ev=get(INDEX)
            polls+=1
            link=find_target(r.text)
            if link:
                rr,page_ev=get(link)
                result={
                    "first_seen_utc":ev["request_completed_utc"],
                    "index_evidence":ev,
                    "decision_url":link,
                    "decision_evidence":page_ev,
                }
                break
        except Exception as exc:
            errors.append({"at_utc":datetime.now(timezone.utc).isoformat(),"error":str(exc)})
        time.sleep(a.interval_sec)

    receipt={
        "candidate":"FOREX-MACRO-SHOCK-001/EUR-ECB-FWD-V0.2",
        "target_date":TARGET_DATE,
        "scheduled_clock_is_t0":False,
        "baseline":baseline,
        "watch_start_utc":start.isoformat(),
        "watch_end_utc":end.isoformat(),
        "poll_interval_sec":a.interval_sec,
        "polls":polls,
        "errors":errors,
        "publication":result,
        "verdict":"ECB_PUBLICATION_FIRST_SEEN_CAPTURED" if result else "ECB_PUBLICATION_NOT_OBSERVED_IN_WINDOW",
        "economic_market_outcomes_opened":False,
        "prices_collected":False,
    }
    out.write_text(json.dumps(receipt,indent=2,sort_keys=True))
    print(json.dumps({
        "verdict":receipt["verdict"],
        "polls":polls,
        "errors":len(errors),
        "first_seen_utc":result["first_seen_utc"] if result else None,
        "prices_collected":False,
    },sort_keys=True))


if __name__=="__main__":
    main()
