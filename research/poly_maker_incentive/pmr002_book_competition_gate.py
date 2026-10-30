#!/usr/bin/env python3
"""PMR-002: strictly bounded read-only public reward-market and order book competition gate.

NOT a predicted income, market-making bot, fee/reward claim, or trading signal.
"""
from __future__ import annotations
import datetime as dt
import hashlib
import json
import math
import pathlib
import time
import urllib.error
import urllib.parse
import urllib.request
from decimal import Decimal, InvalidOperation

ROOT=pathlib.Path("artifacts/pmr002_public_book_competition_v01")
GAMMA="https://gamma-api.polymarket.com/markets"
BOOK="https://clob.polymarket.com/book"
OFFSETS=(0,100)
NMARKETS=3
ROUND_OFFSETS_SECONDS=(0,20,40)
TOKEN_LIMIT=2
BODY_MAX_GAMMA=3_000_000
BODY_MAX_BOOK=1_500_000
HEADERS={"Accept":"application/json","User-Agent":"CryptoLab-PMR002-PublicSource-Research/1.0"}
class Blocked(Exception):pass
def ts():return dt.datetime.now(dt.timezone.utc).isoformat().replace("+00:00","Z")
def sha(x:bytes):return hashlib.sha256(x).hexdigest()
def positive(value,allow_zero=False):
    try:n=Decimal(str(value))
    except (ValueError,InvalidOperation,TypeError):raise Blocked("MALFORMED_DECIMAL")
    if not n.is_finite() or n<0 or (not allow_zero and n==0):
        raise Blocked("NEGATIVE_OR_NONFINITE_DECIMAL")
    return n
def tokenize(raw):
    if isinstance(raw,str):
        try:raw=json.loads(raw)
        except Exception as e:raise Blocked("TOKEN_JSON_FORMAT_"+type(e).__name__) from e
    if not isinstance(raw,list) or len(raw)!=2:raise Blocked("NOT_BINARY_MARKET_TOKENS")
    if not all(isinstance(x,str) and x.isdecimal() and len(x)<100 for x in raw):raise Blocked("INVALID_TOKEN_ID")
    if raw[0]==raw[1]:raise Blocked("DUPLICATE_TOKEN_ID")
    return raw
def active_pool(row,today):
    rr=row.get("clobRewards")
    if not isinstance(rr,list):return Decimal("0")
    total=Decimal("0")
    for e in rr:
        if not isinstance(e,dict):raise Blocked("BAD_REWARD_ROW")
        try:start=dt.date.fromisoformat(str(e["startDate"])[:10])
        except (ValueError,KeyError,TypeError):raise Blocked("BAD_REWARD_START_DATE")
        try:end=dt.date.fromisoformat(str(e["endDate"])[:10]) if e.get("endDate") else None
        except (ValueError,TypeError):raise Blocked("BAD_REWARD_END_DATE")
        if start<=today and (end is None or end>=today):
            total+=positive(e.get("rewardsDailyRate"),allow_zero=True)
    return total
def select(rows,today):
    if len(rows)!=200:raise Blocked("CENSUS_NOT_200_ROWS")
    unique=set()
    eligible=[]
    for item in rows:
        if not isinstance(item,dict):raise Blocked("GAMMA_INVALID_MARKET_ROW")
        ident=str(item.get("id") or "")
        if not ident.isdecimal() or ident in unique:raise Blocked("DUPLICATE_OR_NONNUMERIC_MARKET_ID")
        unique.add(ident)
        if not item.get("active") or item.get("closed") or not item.get("acceptingOrders") or not item.get("enableOrderBook"):
            continue
        pool=active_pool(item,today)
        if pool<=0:continue
        try:
            minsize=positive(item.get("rewardsMinSize"))
            spread=positive(item.get("rewardsMaxSpread"))
            liquidity=positive(item.get("liquidityNum",item.get("liquidity")))
        except Blocked:
            continue
        if minsize>100:continue
        try:tokens=tokenize(item.get("clobTokenIds"))
        except Blocked:continue
        eligible.append({"id":ident,"condition_id":str(item.get("conditionId") or ""),
          "slug":str(item.get("slug") or "")[:150],
          "tokens":tokens,
          "pool_per_day_shared_usdc":str(pool),
          "min_reward_shares":str(minsize),
          "max_reward_spread_as_reported":str(spread),
          "liquidity_as_reported":str(liquidity)})
    eligible.sort(key=lambda x:int(x["id"]))
    return {"matching_first_200":len(eligible),"selected":eligible[:NMARKETS]}
def parse_book(obj,token):
    if not isinstance(obj,dict):raise Blocked("BOOK_NOT_OBJECT")
    if str(obj.get("asset_id"))!=token:raise Blocked("BOOK_TOKEN_ID_MISMATCH")
    def levels(side):
        if not isinstance(obj.get(side),list) or not obj[side]:raise Blocked("BOOK_"+side.upper()+"_EMPTY")
        parsed=[]
        for row in obj[side]:
            if not isinstance(row,dict):raise Blocked("BOOK_LEVEL_SCHEMA")
            price=positive(row.get("price"));size=positive(row.get("size"))
            if price>=1:raise Blocked("BOOK_PRICE_OUTSIDE_0_1")
            parsed.append((price,size))
        return parsed
    bids=levels("bids");asks=levels("asks")
    bid=max(price for price,size in bids);ask=min(price for price,size in asks)
    if not bid<ask:raise Blocked("CROSSED_OR_LOCKED_BOOK")
    bid_sz=sum(size for price,size in bids if price==bid)
    ask_sz=sum(size for price,size in asks if price==ask)
    if bid_sz<=0 or ask_sz<=0:raise Blocked("EMPTY_BEST_LEVEL")
    # Hypothetical new 100-share resting bid at the SAME price; never actual queue/score.
    size_fraction=Decimal(100)/(Decimal(100)+bid_sz)
    return {"best_bid":str(bid),"best_ask":str(ask),
            "visible_spread_cents":str((ask-bid)*100),
            "visible_best_bid_size_shares":str(bid_sz),
            "visible_best_ask_size_shares":str(ask_sz),
            "one_hundred_share_bid_order_value_usdc_indicative":str(Decimal(100)*bid),
            "visible_best_bid_100_share_fraction_NOT_REWARD_SHARE":str(size_fraction),
            "book_market":str(obj.get("market") or ""),
            "book_timestamp_as_reported":obj.get("timestamp"),
            "book_public_hash":obj.get("hash"),
            "book_tick_size_as_reported":obj.get("tick_size"),
            "book_min_order_size_as_reported":obj.get("min_order_size")}
def self_tests():
    today=dt.date(2026,10,30)
    def market(ident,qty=50,rate=1,tokens=None):
        return {"id":str(ident),"active":True,"closed":False,"acceptingOrders":True,
         "enableOrderBook":True,"liquidityNum":1000,"rewardsMinSize":qty,"rewardsMaxSpread":3,
         "clobRewards":[{"startDate":"2026-10-01","endDate":"2026-12-01","rewardsDailyRate":rate}],
         "clobTokenIds":tokens or json.dumps([str(ident)+"01",str(ident)+"02"])}
    rows=[market(i,qty=200) for i in range(1000,1197)]+[market(999)]+[market(500)]+[market(750)]
    selected=select(rows,today)
    assert [z["id"] for z in selected["selected"]]==["500","750","999"]
    assert tokenize('["1","2"]')==["1","2"]
    good={"asset_id":"1","bids":[{"price":".48","size":"50"},{"price":".48","size":"30"}],
          "asks":[{"price":".52","size":"80"}],"timestamp":"0","market":"m"}
    book=parse_book(good,"1")
    assert book["visible_spread_cents"]=="4.00"
    assert book["visible_best_bid_size_shares"]=="80"
    assert close_fraction(book["visible_best_bid_100_share_fraction_NOT_REWARD_SHARE"],Decimal(100)/Decimal(180))
    try:parse_book({**good,"asset_id":"2"},"1");raise AssertionError("TOKEN MISMATCH ACCEPTED")
    except Blocked:pass
    try:parse_book({**good,"bids":[]},"1");raise AssertionError("EMPTY BOOK ACCEPTED")
    except Blocked:pass
def close_fraction(a,b):return abs(Decimal(a)-b)<Decimal("0.0000000001")
def get(url,max_bytes,save_path):
    req=urllib.request.Request(url,headers=HEADERS,method="GET")
    started=ts()
    try:
        with urllib.request.urlopen(req,timeout=8) as resp:
            status=resp.status
            raw=resp.read(max_bytes+1)
    except Exception as exc:
        raise Blocked("GET_FAILED_"+type(exc).__name__) from exc
    received=ts()
    if status!=200 or len(raw)>max_bytes:raise Blocked("HTTP_OR_SIZE_GATE")
    save_path.write_bytes(raw)
    try:obj=json.loads(raw)
    except Exception as exc:raise Blocked("NOT_JSON_"+type(exc).__name__) from exc
    return obj,{"source_url":url,"started_at_utc":started,"received_at_utc":received,
                "http":status,"bytes":len(raw),"raw_sha256":sha(raw)}
def run():
    ROOT.mkdir(parents=True,exist_ok=True)
    self_tests()
    summary={"lab":"PMR002_REWARD_CLOB_COMPETITION_SOURCE_V01","started_at_utc":ts(),
       "source_status":"SOURCE_BLOCKED","economic_edge":"UNPROVEN",
       "orders_created":0,"account_calls":0,"wallet_calls":0,
       "gross_reward_paid_to_operator":None,"net_pnl":None,
       "book_requests_cap":18,"book_receipts":[],"gamma_receipts":[],
       "no_live_or_trade":True,"not_compliant_account_eligibility_proven":True}
    try:
        pages=[]
        for offset in OFFSETS:
            url=GAMMA+"?"+urllib.parse.urlencode({"active":"true","closed":"false",
               "limit":100,"order":"volume24hr","ascending":"false","offset":offset})
            obj,meta=get(url,BODY_MAX_GAMMA,ROOT/("gamma_"+str(offset)+".json"))
            if not isinstance(obj,list) or len(obj)!=100:raise Blocked("GAMMA_PAGE_NOT_100")
            pages.extend(obj)
            summary["gamma_receipts"].append(meta)
        chosen=select(pages,dt.datetime.now(dt.timezone.utc).date())
        summary["eligible_from_200"]=chosen["matching_first_200"]
        summary["selected"]=chosen["selected"]
        if len(chosen["selected"])!=3:
            summary["source_status"]="SOURCE_INCOMPLETE"
            summary["reason"]="FEWER_THAN_3_BINARY_MARKETS_WITH_ACTIVE_100_SHARE_REWARDS"
            return summary
        schedule_start=time.monotonic()
        for rn,offset in enumerate(ROUND_OFFSETS_SECONDS,1):
            time.sleep(max(0,schedule_start+offset-time.monotonic()))
            this={"round":rn,"target_offset_seconds":offset,"actual_started_at_utc":ts(),"tokens":[]}
            summary.setdefault("rounds",[]).append(this)
            for market in chosen["selected"]:
                for side,token in enumerate(market["tokens"]):
                    url=BOOK+"?token_id="+urllib.parse.quote(token,safe="")
                    receipt={"round":rn,"market_id":market["id"],"token_side_index":side,"token":token}
                    try:
                        obj,meta=get(url,BODY_MAX_BOOK,ROOT/("book_"+str(rn)+"_"+market["id"]+"_"+str(side)+".json"))
                        receipt.update(meta)
                        receipt["book"]=parse_book(obj,token)
                        receipt["status"]="BOOK_COMPLETE"
                    except Blocked as exc:
                        receipt["status"]="BOOK_BLOCKED"
                        receipt["reason"]=str(exc)
                    this["tokens"].append(receipt)
                    summary["book_receipts"].append(receipt)
        complete=(len(summary["book_receipts"])==18 and
                  all(b["status"]=="BOOK_COMPLETE" for b in summary["book_receipts"]))
        summary["source_status"]="SOURCE_COMPLETE_VISIBLE_COMPETITION_ONLY" if complete else "SOURCE_INCOMPLETE"
    except Blocked as exc:
        summary["source_status"]="SOURCE_BLOCKED"
        summary["reason"]=str(exc)
    finally:
        summary["finished_at_utc"]=ts()
        summary["economic_verdict"]="NO_NET_ECONOMIC_EDGE_CERTIFIED"
        summary["interpretation"]="Public 3x order book snapshots cannot reconstruct individual time-weighted reward scores, filled trades, adverse selection, verified user payouts or Swiss account eligibility."
        (ROOT/"receipt.json").write_text(json.dumps(summary,indent=2,sort_keys=True)+"\n",encoding="utf-8")
        public={key:summary.get(key) for key in ("lab","source_status","eligible_from_200","selected","reason",
                  "finished_at_utc","economic_verdict")}
        public["rounds"]=[{"number":r["round"],"complete_books":sum(t["status"]=="BOOK_COMPLETE" for t in r["tokens"]),
                           "blocked_books":[{"market_id":t["market_id"],"reason":t.get("reason")} for t in r["tokens"] if t["status"]!="BOOK_COMPLETE"]}
                          for r in summary.get("rounds",[])]
        print(json.dumps(public,indent=2,sort_keys=True),flush=True)
    return summary
if __name__=="__main__":
    report=run()
    if report["source_status"]!="SOURCE_COMPLETE_VISIBLE_COMPETITION_ONLY":
        raise SystemExit(2)
