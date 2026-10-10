#!/usr/bin/env python3
"""Outcome-blind VRP bank integrity regression fixtures only (no public requests)."""
import datetime as dt
import json
import tempfile
from pathlib import Path
from unittest.mock import patch
from labs.BTC_OPTIONS_VRP_001 import usdc_forward_entry_bank_v01 as bank

tests=0
def good(b=True,a=True,age=True,small=False):
    return {"bid_price":2.0 if b else None,"ask_price":2.1 if a else None,
            "bid_amount":.1 if not small else .001,"ask_amount":.1,
            "fresh_30s":age}
def case(name,test):
    global tests
    assert test,name
    tests+=1
def record(day,receipt_dir,src_valid=True,seal=False):
    receipt_dir.mkdir(parents=True,exist_ok=True)
    (receipt_dir/f"{day}.json").write_text('{"source_only":true}')
    return {"schema_version":"BTC_VRP_USDC_FORWARD_ENTRY_SOURCE_V0.1",
      "capture_date_utc":day,"source_valid":src_valid,
      "settlement_fetched":False,"future_path_fetched":False,
      "returns_computed":seal,"pnl_computed":False,"expectancy_computed":False,
      "authenticated":False,"orders":False,"wallets":False}
def raises(f):
    try:f()
    except (RuntimeError, ValueError, KeyError, TypeError, SystemExit):return True
    return False
def now():
    return dt.datetime(2026,10,15,8,5,0,tzinfo=dt.timezone.utc)
def test_main_pair(tmp,invalid=False):
    calls=[]
    def fake_api(method,params):
        calls.append(method)
        if method=="public/get_index_price":
            return {"index_price":80000.0},1,2
        if method=="public/get_instruments":
            a=[]
            # Exact tie at 25 vs 35 days: choose earlier expiry; strike nearest 80k.
            for d in (25,35):
                exp=int(now().timestamp()*1000)+d*86400000
                for typ in ("call","put"):
                    a.append({"instrument_name":f"BTC_USDC-PAIR-{d}-{typ}",
                       "expiration_timestamp":exp,"strike":80000.0,"option_type":typ,
                       "is_active":True,"min_trade_amount":.01})
            return a,1,2
        raise ValueError("NO_FROZEN_API_METHOD_ALLOWLIST")
    def fake_book(name):
        if name=="BTC_USDC-PAIR-25-put" and invalid:
            return {**good(), "ask_price":None, "instrument_name":name}
        return {**good(),"instrument_name":name}
    bank.OUT=tmp/"data.jsonl";bank.RECEIPT_DIR=tmp/"receipts"
    with patch.object(bank,"now",now),patch.object(bank,"api",fake_api),patch.object(bank,"capture_book",fake_book):
        if invalid:
            case("invalid_option_is_fail_closed",raises(bank.main))
        else:bank.main()
        case("duplicate_date_prevents_second_capture",raises(bank.main))
    rows=[json.loads(z) for z in bank.OUT.read_text().splitlines()]
    case("one_append_only_row",len(rows)==1)
    r=rows[0]
    case("frozen_expiry_tiebreak",r["selection"]["call_instrument"]=="BTC_USDC-PAIR-25-call")
    case("minimum_amount_not_tuned",r["selection"]["amount_each_leg"]==.01)
    case("source_valid_label_matches_book",r["source_valid"]==(not invalid))
    case("sealed_prospective_outcomes",all(r[x] is False for x in
       ("settlement_fetched","future_path_fetched","returns_computed","pnl_computed","expectancy_computed","authenticated","orders","wallets")))
    case("index_and_instruments_only_public",calls==["public/get_index_price","public/get_instruments"])
def main():
    case("valid_unlocked_two_sided",bank.valid_book_source(good(),.01))
    case("missing_bid_fail",not bank.valid_book_source(good(b=False),.01))
    case("missing_ask_fail",not bank.valid_book_source(good(a=False),.01))
    case("crossed_book_fail",not bank.valid_book_source({**good(),"bid_price":2.2},.01))
    case("locked_book_fail",not bank.valid_book_source({**good(),"ask_price":2.0},.01))
    case("insufficient_bid_qty_fail",not bank.valid_book_source(good(small=True),.01))
    case("insufficient_ask_qty_fail",not bank.valid_book_source({**good(),"ask_amount":.001},.01))
    case("stale_book_fail",not bank.valid_book_source(good(age=False),.01))
    case("nan_price_fail",not bank.valid_book_source({**good(),"bid_price":float("nan")},.01))
    case("infinite_price_fail",not bank.valid_book_source({**good(),"ask_price":float("inf")},.01))
    case("lot_exact_pass",bank.valid_option_minimum({"min_trade_amount":.01}))
    case("lot_gt_min_fail",not bank.valid_option_minimum({"min_trade_amount":.1}))
    case("lot_nan_fail",not bank.valid_option_minimum({"min_trade_amount":float("nan")}))
    case("top_empty_returns_missing",bank.top({"bids":[]},"bids")== (None,None))
    case("top_nan_returns_missing",bank.top({"bids":[[float("nan"),.2]]},"bids")==(None,None))
    def fake_book(ts):
        with patch.object(bank,"api",return_value=({"bids":[[2,.5]],"asks":[[2.1,.5]],"timestamp":ts},1000,2000)):
            return bank.capture_book("SYNTHETIC_TEST_ONLY")
    case("future_quote_not_fresh",fake_book(2001)["fresh_30s"] is False)
    case("current_older_quote_fresh",fake_book(1900)["fresh_30s"] is True)
    case("missing_timestamp_not_fresh",fake_book(None)["fresh_30s"] is False)
    case("perp_size_positive_source_witness",bank.valid_book_source(good(small=True),0.0))
    with tempfile.TemporaryDirectory() as d:
        root=Path(d);bank.OUT=root/"bank.jsonl";bank.RECEIPT_DIR=root/"receipts"
        day="2026-10-15";a=record(day,bank.RECEIPT_DIR)
        bank.OUT.write_text(json.dumps(a)+"\n")
        case("existing_valid_date",bank.existing_dates()=={day})
        bank.OUT.write_text(json.dumps(a)+"\n"+json.dumps(a)+"\n")
        case("duplicate_existing_date_blocks",raises(bank.existing_dates))
        bank.OUT.write_text("not json\n")
        case("corrupt_json_blocks",raises(bank.existing_dates))
        bank.OUT.write_text(json.dumps(record(day,bank.RECEIPT_DIR,seal=True))+"\n")
        case("unsealed_outcome_flag_blocks",raises(bank.existing_dates))
        bank.OUT.write_text(json.dumps(a)+"\n")
        (bank.RECEIPT_DIR/f"{day}.json").unlink()
        case("missing_original_receipt_blocks",raises(bank.existing_dates))
        bank.OUT.write_text("\n")
        case("empty_ledger_row_blocks",raises(bank.existing_dates))
    with tempfile.TemporaryDirectory() as d:test_main_pair(Path(d))
    with tempfile.TemporaryDirectory() as d:test_main_pair(Path(d),invalid=True)
    print(f"VRP_USDC_BANK_INTEGRITY_SYNTHETIC_PASS count={tests} "
       "no_market_requests=true pnl_opened=false trading=false")
if __name__=="__main__":main()
