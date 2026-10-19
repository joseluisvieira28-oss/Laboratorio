"""Original exact two Binance V5 trade EXIT-DATE locators, no PnL or market data."""
from __future__ import annotations
import argparse,csv,hashlib,json
from datetime import datetime,timezone
from pathlib import Path
from decimal import Decimal

MATCHES={
    "SOLUSDT":{"tf":"1h","open_t":1685376300000,"qty":"104.79202011433037","count":84},
    "BNBUSDT":{"tf":"4h","open_t":1698854700000,"qty":"8.822493532731512","count":28},
}
def utc(t):
    return datetime.fromtimestamp(t/1000,timezone.utc).isoformat()
def read(root,symbol):
    c=MATCHES[symbol]
    files=list(root.rglob(f"{c['tf']}_BASE_TRADES.csv"))
    if len(files)!=1:raise ValueError("EXACT_CANONICAL_ORIGINAL_LEDGER_NOT_FOUND:"+str(len(files)))
    file=files[0]
    with file.open(encoding="utf-8",newline="") as f:rows=list(csv.DictReader(f))
    if len(rows)!=c["count"]:raise ValueError("CANONICAL_COUNT_NOT_EXPECTED")
    matched=[row for row in rows if int(row["open_t"])==c["open_t"]]
    if len(matched)!=1:raise ValueError("ORIGINAL_ENTRY_NOT_UNIQUE")
    row=matched[0]
    if abs(Decimal(row["qty"])-Decimal(c["qty"]))>Decimal("0.00000001"):
        raise ValueError("MODELED_QTY_NOT_IDENTICAL")
    close=int(row["close_t"])
    if close<=c["open_t"] or close>=1767225600000:
        raise ValueError("NOT_ORIGINAL_CLOSED_2023_25_TRADE")
    return {
        "symbol":symbol,"tf":c["tf"],"open_t":c["open_t"],
        "entry_utc":utc(c["open_t"]),"original_close_t":close,"original_close_utc":utc(close),
        "original_close_utc_date":utc(close)[:10],
        "exit_reason":row.get("exit_reason","FIELD_UNAVAILABLE"),
        "trade_record_sha256":hashlib.sha256(json.dumps(row,sort_keys=True).encode()).hexdigest(),
        "source_original_ledger_sha256":hashlib.sha256(file.read_bytes()).hexdigest(),
        "original_qty_equal_prior_evidence":True,
        "broker_exit_trigger_ts_verified":False,
        "all_in_venue_cost_verified":False,
        "source_only_no_OOS":True
    }
def main():
    p=argparse.ArgumentParser()
    p.add_argument("--sol-root",type=Path,required=True)
    p.add_argument("--bnb-root",type=Path,required=True)
    p.add_argument("--out",type=Path,required=True)
    a=p.parse_args()
    result=[read(a.sol_root,"SOLUSDT"),read(a.bnb_root,"BNBUSDT")]
    a.out.mkdir(parents=True,exist_ok=True)
    (a.out/"V05E_ORIGINAL_TWO_EXIT_DAYS_ONLY.json").write_text(json.dumps(result,sort_keys=True,indent=2)+"\n")
    for x in result:print("V05E_EXIT_DATE",json.dumps({k:v for k,v in x.items() if k in
       ("symbol","entry_utc","original_close_utc","original_close_utc_date",
        "exit_reason","broker_exit_trigger_ts_verified")},sort_keys=True))
    print("VERDICT","SOURCE_ONLY_ORIGINAL_V5_EXIT_DATE_LOCATED_NOT_EXCHANGE_FILL")
if __name__=="__main__":main()
