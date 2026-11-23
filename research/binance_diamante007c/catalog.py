#!/usr/bin/env python3
"""Metadata only. Diagnose actual HF API tree schema/path; never fetch L2 bytes."""
import datetime as dt
import hashlib
import json
import urllib.request
from collections import Counter
from pathlib import Path

HOST="https://huggingface.co"
REPOS=("MaximumLeverage/crypto-lob-stream","Goooddy/crypto-lob-stream")
OUT=Path("binance007c-evidence")
MAX_SOURCE=3_000_000

def fetch(url):
    if not url.startswith("https://huggingface.co/api/datasets/"):
        raise ValueError("UNWHITELISTED_PUBLIC_API")
    with urllib.request.urlopen(urllib.request.Request(url,headers={
          "Accept":"application/json",
          "User-Agent":"CryptoLab007C-MetadataOnly-ReadOnly/1.0"
    }),timeout=25) as response:
        if response.status!=200:raise ValueError("UNAVAILABLE_PUBLIC_DATASET_METADATA")
        content=response.read(MAX_SOURCE+1)
    if len(content)>MAX_SOURCE:raise ValueError("CATALOG_TOO_BIG")
    return json.loads(content),hashlib.sha256(content).hexdigest(),len(content)

def query(repo):
    out={"provider":repo,"metadata_only":True,"replay_qualified":False}
    try:
        info,hash_info,info_len=fetch(f"{HOST}/api/datasets/{repo}")
        out.update({"revision_sha":info.get("sha"),"license":(info.get("cardData") or {}).get("license"),
            "private":info.get("private"),"gated":info.get("gated"),
            "info_bytes":info_len,"info_sha256":hash_info})
        tree,hash_tree,tree_len=fetch(f"{HOST}/api/datasets/{repo}/tree/main?recursive=true&expand=true")
        out.update({"tree_bytes":tree_len,"tree_sha256":hash_tree,"tree_python_type":type(tree).__name__})
        if isinstance(tree,list):
            out["total_returned_items"]=len(tree)
            out["first_raw_item_sample"]=tree[0] if tree else None
            out["type_counts"]=dict(Counter(str(x.get("type")) for x in tree if isinstance(x,dict)))
            out["first_18_paths"]=[x.get("path") for x in tree[:18] if isinstance(x,dict)]
            hits=[x for x in tree if isinstance(x,dict) and
                  any(x.get("path","").endswith("/"+mon+".parquet") for mon in ("2026-08","2026-09"))
                  and "BTCUSDT" in x.get("path","")]
            out["btc_2026_08_09_matches"]=[{"path":x.get("path"),"size":x.get("size"),"type":x.get("type")} for x in hits[:30]]
            out["contains_historical_market_files"]=bool(hits)
            out["server_catalog_not_full_coverage_proof"]=True
        else:
            out["top_level_object_keys"]=list(tree)[:20] if isinstance(tree,dict) else []
        out["status"]="PUBLIC_METADATA_INSPECTED_ONLY"
    except Exception as exc:
        out["status"]="CATALOG_SOURCE_BLOCKED"
        out["error_type"]=type(exc).__name__
        out["error"]=str(exc)[:260]
    return out

def main():
    OUT.mkdir(parents=True,exist_ok=True)
    results=[query(repo) for repo in REPOS]
    report={"study":"BINANCE007C_PROVIDER_CATALOG_FORENSICS",
       "metadata_only":True,"actual_parquet_downloads":0,
       "source_qualified":False,"no_trades":True,"no_capital":True,
       "checked_utc":dt.datetime.now(dt.timezone.utc).isoformat(),
       "candidates":results}
    dest=OUT/"catalog_report.json"
    dest.write_text(json.dumps(report,ensure_ascii=False,indent=2,sort_keys=True)+"\n")
    (OUT/"catalog_report.sha256").write_text(hashlib.sha256(dest.read_bytes()).hexdigest()+"  "+dest.name+"\n")
    print(json.dumps(report,ensure_ascii=False,indent=2,sort_keys=True))
    return 0 if all(x["status"]=="PUBLIC_METADATA_INSPECTED_ONLY" for x in results) else 2
if __name__=="__main__":raise SystemExit(main())
