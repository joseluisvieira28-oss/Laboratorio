#!/usr/bin/env python3
"""DIAGNOSTIC ONLY: source transport adaptation, frozen macro signal/economics unchanged.

Strict/original run is in the separate workflow. BLS original HTML is 403 in Actions.
This runner uses a Jina TEXT MIRROR, not a BLS byte-authenticated original archive;
any economic replay here is NON-CANONICAL and cannot promote an edge.
2022-2024 ONLY, Binance original CHECKSUM checked by frozen scorer.
"""
import hashlib
import sys
from datetime import date
from urllib.request import Request, urlopen
import news_shock_v03b_nfp_master_discovery as frozen

_original_fetch = frozen.fetch

def mirror_transport(url, allowed_prefixes, attempts=4):
    if url.startswith("https://www.bls.gov/news.release/archives/empsit_"):
        mirrored = "https://r.jina.ai/" + url
        last = None
        for n in range(3):
            try:
                req = Request(mirrored, headers={"User-Agent":"Mozilla/5.0 (archival research; read-only)"})
                with urlopen(req, timeout=55) as r:
                    raw = r.read()
                txt=raw.decode("utf-8",errors="replace")
                if "URL Source: " + url not in txt:
                    raise RuntimeError("mirror did not attest exact BLS URL")
                if "Employment Situation News Release" not in txt:
                    raise RuntimeError("mirror source title absent")
                day=url.rsplit("_",1)[-1].split(".")[0]
                if len(day)!=8 or not day.isdigit():
                    raise RuntimeError("bad BLS archive day")
                d=date(int(day[-4:]),int(day[0:2]),int(day[2:4]))
                if d.year not in (2022,2023,2024):
                    raise PermissionError("protected year requested")
                actual=frozen.parse_bls_actual(d.isoformat(),raw)
                print("BLS_MIRRORED_PROVENANCE_NOT_ORIGINAL_BYTES",d.isoformat(),
                    "sha256",hashlib.sha256(raw).hexdigest(),"first_release_parse",actual,flush=True)
                return raw
            except Exception as exc:
                last=exc
                print("BLS_MIRROR_TRANSPORT_RETRY",n+1,repr(exc),flush=True)
        raise RuntimeError("MIRROR_SOURCE_BLOCKED "+repr(last))
    return _original_fetch(url,allowed_prefixes,attempts)

frozen.fetch=mirror_transport
if __name__=="__main__":
    frozen.main()
