from __future__ import annotations

"""Official MEXC parent-corpus reacquisition for TFG-PBR01-1D-001.

Downloads only the prospectively allowed 2023-02..2024-12 monthly Min15 Spot CSVs
for the six frozen symbols. This stage saves raw bytes and hashes only; it does NOT
parse market rows, derive 1D candles, form PBR signals, calculate returns/PnL, or
access 2025/2026 market-file bytes. Corpus parsing/auditing is delegated afterwards
to the unchanged historical Phase-B adapter/auditor.
"""

import argparse
import hashlib
import json
import re
from pathlib import Path
from urllib.parse import parse_qs, unquote, urlparse

from playwright.sync_api import sync_playwright

LAB_ID = "TFG-PBR01-1D-001"
LIST_MARKER = "/file-svc/history/download?filePath="
SYMBOLS = {
    "BTCUSDT": "BTC",
    "ETHUSDT": "ETH",
    "SOLUSDT": "SOL",
    "BNBUSDT": "BNB",
    "XRPUSDT": "XRP",
    "DOGEUSDT": "DOGE",
}
START_YEAR, START_MONTH = 2023, 2
END_YEAR, END_MONTH = 2024, 12


def month_seq() -> list[str]:
    out=[]; y=START_YEAR; m=START_MONTH
    while (y,m) <= (END_YEAR,END_MONTH):
        out.append(f"{y:04d}-{m:02d}")
        if m==12: y+=1; m=1
        else: m+=1
    return out


def expected_name(base: str, ym: str) -> str:
    return f"{base}_USDT-Min15-{ym}-01.csv"


def sha256_bytes(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def symbol_id_from_observed(url: str) -> str:
    q=parse_qs(urlparse(url).query)
    vals=q.get("filePath") or q.get("filepath")
    if not vals: raise RuntimeError("FRONTEND_FILEPATH_QUERY_MISSING")
    path=unquote(vals[0])
    parts=[p for p in path.strip("/").split("/") if p]
    if len(parts)<5 or parts[0]!="SPOT2" or parts[1]!="kline":
        raise RuntimeError(f"UNEXPECTED_FRONTEND_FILE_PATH:{path}")
    sid=parts[2]
    if not re.fullmatch(r"[A-Za-z0-9_:\-.]+",sid): raise RuntimeError("UNSAFE_SYMBOL_ID")
    return sid


def main() -> int:
    ap=argparse.ArgumentParser()
    ap.add_argument("--raw-dir", required=True)
    ap.add_argument("--receipt", required=True)
    args=ap.parse_args()
    raw_dir=Path(args.raw_dir); raw_dir.mkdir(parents=True,exist_ok=True)
    months=month_seq()
    rows=[]; ids={}; errors=[]
    status="REACQUISITION_STARTED"; rc=0

    try:
        with sync_playwright() as p:
            browser=p.chromium.launch(headless=True)
            context=browser.new_context(locale="en-US",timezone_id="UTC",accept_downloads=False,user_agent="Mozilla/5.0 TFG-PBR01-1D source recovery audit")
            page=context.new_page()
            for symbol,base in SYMBOLS.items():
                page_url=f"https://www.mexc.com/market-data-download/{base}?type=kline&interval=monthly&pair=USDT"
                observed={}
                def on_req(req):
                    if LIST_MARKER in req.url and "url" not in observed:
                        observed["url"]=req.url
                page.on("request",on_req)
                page.goto(page_url,wait_until="domcontentloaded",timeout=60000)
                for _ in range(30):
                    if "url" in observed: break
                    page.wait_for_timeout(500)
                page.remove_listener("request",on_req)
                if "url" not in observed: raise RuntimeError(f"FILE_LIST_REQUEST_NOT_OBSERVED:{symbol}")
                sid=symbol_id_from_observed(observed["url"]); ids[symbol]=sid
                parsed=urlparse(observed["url"]); origin=f"{parsed.scheme}://{parsed.netloc}"
                list_url=origin+LIST_MARKER+f"SPOT2/kline/{sid}/monthly/Min15/"
                resp=context.request.get(list_url,headers={"referer":page_url},timeout=60000)
                if not resp.ok: raise RuntimeError(f"LIST_HTTP:{symbol}:{resp.status}")
                payload=resp.json()
                meta=payload.get("data") if isinstance(payload,dict) else payload
                if not isinstance(meta,list): raise RuntimeError(f"LIST_SHAPE:{symbol}")
                by_name={r.get("fileName"):r for r in meta if isinstance(r,dict) and isinstance(r.get("fileName"),str)}
                wanted=[expected_name(base,ym) for ym in months]
                missing=[n for n in wanted if n not in by_name]
                if missing: raise RuntimeError(f"MISSING_ALLOWED_SOURCE_FILE:{symbol}:{missing[0]}")
                for ym,name in zip(months,wanted):
                    item=by_name[name]
                    masked=item.get("maskedUrl")
                    if not isinstance(masked,str) or not masked.startswith(("https://","http://")):
                        raise RuntimeError(f"UNSAFE_MASKED_URL:{symbol}:{ym}")
                    fr=context.request.get(masked,headers={"referer":page_url},timeout=120000)
                    if not fr.ok: raise RuntimeError(f"DOWNLOAD_HTTP:{symbol}:{ym}:{fr.status}")
                    raw=fr.body()
                    dest=raw_dir/name
                    dest.write_bytes(raw)
                    h=sha256_bytes(raw)
                    rows.append({"symbol":symbol,"month":ym,"file_name":name,"byte_count":len(raw),"sha256":h,"http_status":fr.status})
                    print(f"{symbol} {ym}: bytes={len(raw):,} sha256={h}",flush=True)
            browser.close()
        if len(rows) != 138: raise RuntimeError(f"DOWNLOADED_FILE_COUNT:{len(rows)}")
        status="PASS_OFFICIAL_MEXC_138_FILE_REACQUISITION_BYTES_ONLY"
    except Exception as exc:
        status="BLOCKED_PRE_OUTCOME_MASS_REACQUISITION"
        errors.append(f"{type(exc).__name__}:{exc}")
        rc=2

    receipt={
        "lab_id":LAB_ID,"status":status,"start_month":"2023-02","end_month":"2024-12",
        "symbol_ids":ids,"expected_file_count":138,"downloaded_file_count":len(rows),"files":rows,"errors":errors,
        "market_rows_parsed":False,"one_day_candles_derived":False,"pbr01_outcome_evaluation_performed":False,
        "validation_2025_market_bytes_accessed":False,"holdout_2026_market_bytes_accessed":False,
        "cross_exchange_backfill_performed":False,"api_candle_substitution_performed":False,
        "synthetic_fill_performed":False,"interpolation_performed":False,
        "exchange_mutation_performed":False,"orders_submitted":False,
    }
    out=Path(args.receipt); out.parent.mkdir(parents=True,exist_ok=True); out.write_text(json.dumps(receipt,sort_keys=True,indent=2)+"\n")
    print(json.dumps({"status":status,"downloaded_file_count":len(rows),"symbol_ids":ids,"pbr01_outcome_evaluation_performed":False},indent=2))
    return rc

if __name__=="__main__": raise SystemExit(main())
