#!/usr/bin/env python3
"""Recover only public outbound links from the Cryptarbitrage X post.

No strategy outcomes are read. No file bytes are downloaded by this probe.
"""
from __future__ import annotations

import html
import json
import re
import urllib.parse
import urllib.request
from urllib.parse import urlsplit, urlunsplit

STATUS_URL="https://twitter.com/cryptarbitrage/status/1817888742650085616"
OEMBED="https://publish.twitter.com/oembed?" + urllib.parse.urlencode({
    "url":STATUS_URL,
    "omit_script":"true",
    "dnt":"true",
})


def safe(u: str) -> str:
    s=urlsplit(u)
    return urlunsplit((s.scheme,s.netloc,s.path,"",""))


def get_text(url: str) -> str:
    req=urllib.request.Request(
        url,
        headers={"User-Agent":"CryptoLab-PublicLinkRecovery/0.1"},
        method="GET",
    )
    with urllib.request.urlopen(req,timeout=30) as r:
        return r.read().decode("utf-8","replace")


def resolve(url: str) -> dict:
    req=urllib.request.Request(
        url,
        headers={"User-Agent":"CryptoLab-PublicLinkRecovery/0.1"},
        method="GET",
    )
    with urllib.request.urlopen(req,timeout=30) as r:
        final=r.geturl()
        ctype=r.headers.get("Content-Type","")
        clen=r.headers.get("Content-Length")
        # Deliberately do not read response body.
        return {
            "input_safe_url":safe(url),
            "final_safe_url":safe(final),
            "final_host":urlsplit(final).netloc,
            "content_type":ctype,
            "content_length_header":clen,
        }


def main() -> int:
    receipt={
        "route_id":"CRYPTARBITRAGE_FREE_2024H1_PARQUET",
        "status_url":STATUS_URL,
        "authenticated":False,
        "file_bytes_downloaded":False,
        "outcomes_opened":False,
    }
    try:
        raw=get_text(OEMBED)
        obj=json.loads(raw)
    except Exception as exc:
        receipt["classification"]="OEMBED_LINK_RECOVERY_FAILED"
        receipt["error"]=f"{type(exc).__name__}:{str(exc)[:400]}"
        _write(receipt)
        return 2

    embed=html.unescape(str(obj.get("html","")))
    hrefs=re.findall(r'href=["\'](https?://[^"\']+)["\']',embed,flags=re.I)
    hrefs=list(dict.fromkeys(hrefs))
    receipt["oembed_author_name"]=obj.get("author_name")
    receipt["oembed_author_url"]=safe(obj.get("author_url","")) if obj.get("author_url") else None
    receipt["outbound_link_count"]=len(hrefs)

    resolved=[]
    for u in hrefs:
        # Author/status/profile links are not dataset candidates.
        host=urlsplit(u).netloc.lower()
        if host in {"twitter.com","www.twitter.com","x.com","www.x.com"}:
            continue
        try:
            resolved.append(resolve(u))
        except Exception as exc:
            resolved.append({
                "input_safe_url":safe(u),
                "resolution_error":f"{type(exc).__name__}:{str(exc)[:250]}",
            })

    receipt["resolved_outbound_links"]=resolved
    candidates=[]
    for r in resolved:
        u=r.get("final_safe_url","").lower()
        host=r.get("final_host","").lower()
        if (
            any(u.endswith(ext) for ext in (".parquet",".zip",".csv",".gz",".7z"))
            or host.endswith(("drive.google.com","docs.google.com","dropbox.com","mega.nz","github.com","raw.githubusercontent.com","huggingface.co"))
        ):
            candidates.append(r)

    receipt["dataset_link_candidate_count"]=len(candidates)
    receipt["dataset_link_candidates"]=candidates
    receipt["classification"]=(
        "PUBLIC_DATASET_LINK_CANDIDATE_FOUND"
        if candidates else
        "PUBLIC_DATASET_LINK_NOT_RECOVERED_FROM_OEMBED"
    )
    _write(receipt)
    return 0


def _write(x):
    with open("cryptarbitrage_link_recovery_receipt_v01.json","w",encoding="utf-8") as f:
        json.dump(x,f,indent=2,sort_keys=True)
        f.write("\n")
    print(json.dumps(x,sort_keys=True))


if __name__=="__main__":
    raise SystemExit(main())
