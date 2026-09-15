from __future__ import annotations

"""Inspect only the public JavaScript bundle for MEXC market-data-download/[currency].
No market-data file/response is downloaded or parsed.
"""
import argparse, json, re
from pathlib import Path
import requests

URL = "https://static.mocortech.com/www/_next/static/chunks/pages/market-data-download/%5Bcurrency%5D-c624d37f89007981.js"
TERMS = ("/api/", "download", "history", "kline", "interval", "currency", "period", "date", "file", "csv", "spot", "market")


def main():
    ap=argparse.ArgumentParser(); ap.add_argument("--receipt", required=True); a=ap.parse_args()
    r=requests.get(URL,headers={"User-Agent":"Mozilla/5.0 TFG source-contract audit"},timeout=30); r.raise_for_status(); text=r.text
    strings=[]
    for m in re.finditer(r'(["\'])(.*?)(?<!\\)\1', text):
        s=m.group(2)
        if any(t.lower() in s.lower() for t in TERMS) and len(s) <= 2000:
            strings.append(s)
    contexts=[]
    needles=("/api/", "download", "history", "kline", "Min15", "fileName", "downloadUrl", "interval")
    for needle in needles:
        start=0
        while True:
            i=text.find(needle,start)
            if i<0: break
            snippet=re.sub(r"\s+"," ",text[max(0,i-1400):min(len(text),i+2200)])
            contexts.append({"needle":needle,"context":snippet[:3800]})
            start=i+len(needle)
            if len(contexts)>160: break
    # dedup
    strings=list(dict.fromkeys(strings))
    seen=set(); unique=[]
    for c in contexts:
        k=(c['needle'],c['context'])
        if k not in seen: seen.add(k); unique.append(c)
    payload={
      "status":"PASS_PUBLIC_JS_CONTRACT_INSPECTION",
      "bundle_url":URL,"http_status":r.status_code,"bundle_byte_count":len(r.content),
      "interesting_string_literals":strings[:1000],"contexts":unique[:160],
      "market_file_downloaded":False,"market_rows_parsed":False,"outcome_evaluation_performed":False,
      "validation_2025_access_performed":False,"holdout_2026_access_performed":False,
      "exchange_mutation_performed":False,"orders_submitted":False
    }
    p=Path(a.receipt); p.parent.mkdir(parents=True,exist_ok=True); p.write_text(json.dumps(payload,indent=2,sort_keys=True)+"\n")
    print("STATUS",payload['status'],"BYTES",payload['bundle_byte_count'])
    print("=== STRINGS ===")
    for s in strings[:300]: print(s)
    print("=== CONTEXTS ===")
    for c in unique[:80]: print("NEEDLE",c['needle']); print(c['context']); print("---")
    return 0
if __name__=='__main__': raise SystemExit(main())
