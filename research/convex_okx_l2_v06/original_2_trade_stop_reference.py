"""Emit exact already-frozen original V5 BASE exit reference fields, no new market data."""
import csv,json,hashlib,sys
from decimal import Decimal
from pathlib import Path
spec={
"SOLUSDT":("1h",1685376300000,1685981100000,"104.79202011433037",84),
"BNBUSDT":("4h",1698854700000,1700588700000,"8.822493532731512",28)}
def one(symbol,root):
    tf,entry,exit_,q,n=spec[symbol]
    p=list(Path(root).rglob(tf+"_BASE_TRADES.csv"))
    if len(p)!=1:raise ValueError("ONE_CANONICAL_CSV_REQUIRED")
    path=p[0]
    with path.open(encoding="utf8",newline="") as f:rows=list(csv.DictReader(f))
    if len(rows)!=n:raise ValueError("COUNT_MISMATCH")
    rr=[x for x in rows if int(x["open_t"])==entry]
    if len(rr)!=1:raise ValueError("MATCH_NOT_UNIQUE")
    row=rr[0]
    if int(row["close_t"])!=exit_ or row.get("exit_reason")!="STOP_INTRABAR" or abs(Decimal(row["qty"])-Decimal(q))>Decimal("0.00000001"):
        raise ValueError("FROZEN_IDENTITIES_MISMATCH")
    raw=Decimal(row["exit_price"])/(Decimal(1)-Decimal("0.0002"))
    print("ORIGINAL_EXACT_STOP_REFERENCE",json.dumps({
      "symbol":symbol,"entry_ms":entry,"exit_bar_end_ms":exit_,
      "modeled_entry":row["entry_price"],"modeled_exit_after_2bps_slip":row["exit_price"],
      "model_raw_stop_at_binance_5m_intrabar":str(raw),"original_base_qty":row["qty"],
      "original_exit_reason":row["exit_reason"],
      "original_csv_sha256":hashlib.sha256(path.read_bytes()).hexdigest(),
      "not_actual_broker_trigger":True,
      "original_fee_rate_per_side":"0.0008",
    },sort_keys=True))
if __name__=="__main__":
 one("SOLUSDT",sys.argv[1]);one("BNBUSDT",sys.argv[2])
