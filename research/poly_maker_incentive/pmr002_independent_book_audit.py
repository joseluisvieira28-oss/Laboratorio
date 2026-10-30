#!/usr/bin/env python3
"""PMR-002 forensic: read ONLY pinned archived original source books; no market/API."""
import datetime as dt
import hashlib
import json
import pathlib
import statistics
from decimal import Decimal
from pmr002_book_competition_gate import parse_book,select

SRC=pathlib.Path("downloaded")
OUT=pathlib.Path("artifacts/pmr002_original_book_audit")
RUN=41049992419
ARTIFACT_ID=12974346817
def require(cond,message):
    if not cond:raise ValueError(message)
def unpack(file):
    require(file.is_file(),"MISSING_ORIGINAL_FILE_"+file.name)
    raw=file.read_bytes()
    return json.loads(raw),hashlib.sha256(raw).hexdigest()
def median(values):
    return str(statistics.median(values))
def summarize(rows):
    def vals(k):return [Decimal(r["book"][k]) for r in rows]
    return {
        "book_count":len(rows),
        "bid_size_min_shares":str(min(vals("visible_best_bid_size_shares"))),
        "bid_size_median_shares":median(vals("visible_best_bid_size_shares")),
        "bid_size_max_shares":str(max(vals("visible_best_bid_size_shares"))),
        "bid_spread_min_cents":str(min(vals("visible_spread_cents"))),
        "bid_spread_median_cents":median(vals("visible_spread_cents")),
        "bid_spread_max_cents":str(max(vals("visible_spread_cents"))),
        "one_hundred_share_top_bid_value_min_usdc":str(min(vals("one_hundred_share_bid_order_value_usdc_indicative"))),
        "one_hundred_share_top_bid_value_median_usdc":median(vals("one_hundred_share_bid_order_value_usdc_indicative")),
        "one_hundred_share_top_bid_value_max_usdc":str(max(vals("one_hundred_share_bid_order_value_usdc_indicative"))),
        "visible_best_bid_size_fraction_min_NOT_REWARD_SHARE":str(min(vals("visible_best_bid_100_share_fraction_NOT_REWARD_SHARE"))),
        "visible_best_bid_size_fraction_median_NOT_REWARD_SHARE":median(vals("visible_best_bid_100_share_fraction_NOT_REWARD_SHARE")),
        "visible_best_bid_size_fraction_max_NOT_REWARD_SHARE":str(max(vals("visible_best_bid_100_share_fraction_NOT_REWARD_SHARE")))
    }
def audit():
    receipt,_=unpack(SRC/"receipt.json")
    require(receipt["lab"]=="PMR002_REWARD_CLOB_COMPETITION_SOURCE_V01","BAD_SOURCE_ID")
    require(receipt["source_status"]=="SOURCE_COMPLETE_VISIBLE_COMPETITION_ONLY","PARENT_NOT_SOURCE_COMPLETE")
    require(receipt["orders_created"]==0 and receipt["account_calls"]==0 and receipt["wallet_calls"]==0,"PARENT_UNSAFE")
    pages=[]
    for rr in receipt["gamma_receipts"]:
        query=rr["source_url"]
        offset=int(query.split("offset=")[-1])
        data,digest=unpack(SRC/("gamma_"+str(offset)+".json"))
        require(digest==rr["raw_sha256"],"GAMMA_HASH_MISMATCH")
        require(len(data)==100,"GAMMA_PAGE_NOT_100")
        pages.extend(data)
    nowdate=dt.date.fromisoformat(receipt["started_at_utc"][:10])
    selected=select(pages,nowdate)["selected"]
    require(selected==receipt["selected"],"DETERMINISTIC_GAMMA_SELECTION_MISMATCH")
    require(len(selected)==3 and [x["id"] for x in selected]==["562802","562803","616902"],"PINNED_IDENTITY_MISMATCH")
    books=receipt["book_receipts"]
    require(len(books)==18 and all(x["status"]=="BOOK_COMPLETE" for x in books),"INCOMPLETE_ORIGINAL_18_BOOKS")
    found=set()
    by={m["id"]:[] for m in selected}
    for r in books:
        key=(r["round"],r["market_id"],r["token_side_index"])
        require(key not in found and r["round"] in (1,2,3) and r["token_side_index"] in (0,1),"DUPLICATE_OR_INVALID_BOOK_KEY")
        found.add(key)
        market=next(x for x in selected if x["id"]==r["market_id"])
        token=market["tokens"][r["token_side_index"]]
        require(token==r["token"],"TOKEN_ID_CHANGED")
        book,digest=unpack(SRC/("book_"+str(r["round"])+"_"+r["market_id"]+"_"+str(r["token_side_index"])+".json"))
        require(digest==r["raw_sha256"],"BOOK_RAW_SHA_MISMATCH")
        parsed=parse_book(book,token)
        require(parsed==r["book"],"DERIVED_BOOK_FIELDS_CHANGED")
        by[r["market_id"]].append(r)
    require(len(found)==18 and all(len(x)==6 for x in by.values()),"NO_FULL_3x2x3_COVERAGE")
    summary={"lab":"PMR002_POST_SOURCE_ORIGINAL_EVIDENCE_REPLAY_V01",
      "parent_run":RUN,"parent_artifact_id":ARTIFACT_ID,
      "original_source_status":receipt["source_status"],
      "result":"REPRODUCIBLE_SOURCE_PASS_COMPETITION_VISIBLE",
      "economic_edge_certified":False,
      "real_account_rewards_paid_verified":False,
      "real_fills_verified":False,
      "adverse_selection_tested":False,
      "legal_swiss_account_eligibility_proven":False,
      "actual_orders":0,"new_market_calls":0,
      "per_market":[],
      "interpretation":"All statistics are public at-best book order-size and spread diagnostics from 3 nonsynchronous snapshots. Competitive rewards are pro-rata, time-weighted, qualification dependent; no actual user reward share/earnings can be inferred."}
    for m in selected:
        summary["per_market"].append({"market_id":m["id"],"slug":m["slug"],
          "configured_min_reward_shares":m["min_reward_shares"],
          "advertised_daily_pool_SHARED_usdc":m["pool_per_day_shared_usdc"],
          "public_orderbooks":summarize(by[m["id"]])})
    summary["visible_book_snapshot_count"]=18
    summary["source_original_hashes_reverified"]=20
    summary["economic_status"]="NO_PROVEN_POSITIVE_EXPECTED_NET_INCOME"
    return summary
def main():
    OUT.mkdir(parents=True,exist_ok=True)
    try:result=audit()
    except Exception as e:
        result={"lab":"PMR002_POST_SOURCE_ORIGINAL_EVIDENCE_REPLAY_V01",
                "result":"SOURCE_INTEGRITY_BLOCKED","reason":type(e).__name__+":"+str(e)[:190],
                "economic_edge_certified":False,"actual_orders":0,"new_market_calls":0}
    (OUT/"receipt.json").write_text(json.dumps(result,indent=2,sort_keys=True)+"\n")
    print(json.dumps(result,indent=2,sort_keys=True),flush=True)
    if result["result"]=="SOURCE_INTEGRITY_BLOCKED":raise SystemExit(2)
if __name__=="__main__":main()
