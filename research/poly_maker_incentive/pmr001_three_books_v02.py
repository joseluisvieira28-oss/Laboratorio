"""PMR001 V0.2: exactly 3x read-only public CLOB book batches, no order transport."""
from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
import json
import os
from pathlib import Path
import time
from urllib.request import Request, urlopen

from .pmr001_source_gate import fetch_one, valid_reward_rate, positive_decimal, SourceBlocked

CLOB_BOOKS = "https://clob.polymarket.com/books"
SNAPSHOT_OFFSETS_SECONDS = (0, 10, 20)
MAX_BODY_BYTES = 2_000_000
MAX_SECONDS = 120
N = 3


def d(value, name="numeric"):
    try:
        x = Decimal(str(value))
    except (ValueError, InvalidOperation, TypeError) as exc:
        raise SourceBlocked("INVALID_" + name.upper()) from exc
    if not x.is_finite():
        raise SourceBlocked("NONFINITE_" + name.upper())
    return x


def parse_token_ids(raw):
    if isinstance(raw, str):
        try:
            raw = json.loads(raw)
        except (json.JSONDecodeError, ValueError):
            return None
    if not isinstance(raw, list) or len(raw) != 2:
        return None
    if not all(isinstance(v, str) and v.isdigit() for v in raw):
        return None
    if raw[0] == raw[1]:
        return None
    return raw


def selection(pages: list, today) -> list[dict]:
    if len(pages) != 2 or any(not isinstance(x, list) for x in pages):
        raise SourceBlocked("MARKET_PAGES_MISSING")
    records = pages[0] + pages[1]
    ids = set()
    filtered = []
    for m in records:
        if not isinstance(m, dict):
            raise SourceBlocked("MARKET_NOT_OBJECT")
        market_id = str(m.get("id", ""))
        if not market_id.isdigit() or market_id in ids:
            raise SourceBlocked("MARKET_ID_INVALID_OR_DUPLICATE")
        ids.add(market_id)
        if not (m.get("active") is True and m.get("closed") is False
                and m.get("acceptingOrders") is True
                and m.get("enableOrderBook") is True):
            continue
        if valid_reward_rate(m, today) <= 0:
            continue
        quantity = positive_decimal(m.get("rewardsMinSize"))
        maxspread = positive_decimal(m.get("rewardsMaxSpread"))
        liquidity = positive_decimal(m.get("liquidityNum", m.get("liquidity", 0)))
        if not (0 < quantity <= 100 and maxspread > 0 and liquidity > 0):
            continue
        tokens = parse_token_ids(m.get("clobTokenIds"))
        if tokens is None:
            # Token IDs absent => not a source-qualified candidate, never substitute.
            continue
        condition = m.get("conditionId")
        if not isinstance(condition, str) or not condition.startswith("0x") or len(condition) != 66:
            continue
        filtered.append({
            "market_id": market_id,
            "condition_id": condition.lower(),
            "tokens": tokens,
            "min_reward_eligible_shares": float(quantity),
            "max_reward_spread_cents": float(maxspread),
            "daily_total_pool_shared_usdc": float(valid_reward_rate(m, today)),
            "slug": str(m.get("slug", ""))[:150]
        })
    return sorted(filtered, key=lambda m: int(m["market_id"]))[:N]


def fetch_books(tokens: list[str]) -> list[dict]:
    payload = json.dumps([{"token_id": t} for t in tokens]).encode("utf8")
    request = Request(CLOB_BOOKS, data=payload,
                      headers={"Content-Type": "application/json",
                               "Accept": "application/json",
                               "User-Agent": "CryptoLab-PMR001-V02-Research-Only"},
                      method="POST")
    try:
        with urlopen(request, timeout=12) as resp:
            if resp.status != 200:
                raise SourceBlocked("BOOK_HTTP_NON200")
            raw = resp.read(MAX_BODY_BYTES + 1)
        if len(raw) > MAX_BODY_BYTES:
            raise SourceBlocked("BOOK_RESPONSE_TOO_LARGE")
        x = json.loads(raw)
    except SourceBlocked:
        raise
    except Exception as exc:
        raise SourceBlocked("BOOK_TRANSPORT_" + type(exc).__name__) from exc
    if not isinstance(x, list) or len(x) != len(tokens):
        raise SourceBlocked("BOOK_BATCH_WRONG_CARDINALITY")
    found = {}
    for row in x:
        if not isinstance(row, dict):
            raise SourceBlocked("BOOK_NOT_OBJECT")
        tok = str(row.get("asset_id"))
        if tok in found or tok not in tokens:
            raise SourceBlocked("BOOK_TOKEN_IDENTITY_WRONG")
        found[tok] = row
    if set(found) != set(tokens):
        raise SourceBlocked("BOOK_TOKEN_SET_WRONG")
    return [found[t] for t in tokens]


def book_data(book: dict, token: str, condition_id: str) -> dict:
    if str(book.get("asset_id")) != token or str(book.get("market", "")).lower() != condition_id:
        raise SourceBlocked("BOOK_MARKET_OR_TOKEN_ID_MISMATCH")
    if not book.get("hash") or book.get("timestamp") is None:
        raise SourceBlocked("BOOK_STATE_IDENTITY_MISSING")
    tick=d(book.get("tick_size"),"tick")
    if tick <= 0:
        raise SourceBlocked("TICK_NOT_POSITIVE")
    per_side={}
    for name in ("bids", "asks"):
        levels=book.get(name)
        if not isinstance(levels,list):
            raise SourceBlocked("BOOK_LEVEL_SCHEMA_INVALID")
        valid=[]
        for level in levels:
            if not isinstance(level,dict):
                raise SourceBlocked("BOOK_LEVEL_NOT_OBJECT")
            price=d(level.get("price"),"price")
            size=d(level.get("size"),"size")
            if not (0 < price < 1 and size > 0):
                raise SourceBlocked("BOOK_LEVEL_PRICE_OR_SIZE_OUT_OF_RANGE")
            valid.append((price,size))
        valid.sort(key=lambda t: t[0],reverse=(name=="bids"))
        per_side[name]=valid
    bids=per_side["bids"]
    asks=per_side["asks"]
    if not bids or not asks or bids[0][0] >= asks[0][0]:
        raise SourceBlocked("MISSING_OR_CROSSED_TOP_BOOK")
    bid,ask=bids[0][0],asks[0][0]
    return {
        "token_id":token,
        "book_hash":str(book["hash"]),
        "book_timestamp":str(book["timestamp"]),
        "best_bid":float(bid),
        "best_ask":float(ask),
        "midpoint":float((bid+ask)/2),
        "spread_cents":float((ask-bid)*100),
        "tick_size":float(tick),
        "top3_bid_shares":float(sum((s for _,s in bids[:3]),Decimal(0))),
        "top3_ask_shares":float(sum((s for _,s in asks[:3]),Decimal(0))),
    }


def analyze_pair(market: dict, yes: dict, no: dict) -> dict:
    y=book_data(yes,market["tokens"][0],market["condition_id"])
    n=book_data(no,market["tokens"][1],market["condition_id"])
    q=d(market["min_reward_eligible_shares"],"min_shares")
    # Both YES and NO at best bid (if BOTH filled); indicative collateral cost.
    # Never claim these quotes actually could earn maker rewards or even survive.
    total=q * (d(y["best_bid"]) + d(n["best_bid"]))
    return {
        "market_id":market["market_id"],
        "status":"BOOK_PAIR_OBSERVED_NO_LIVE_ORDER",
        "yes":y,"no":n,
        "counterfactual_buy_yes_and_no_at_best_bid_usdc":float(total),
        "quote_quantity_each_side_shares":float(q),
        "cash_proxy_under_100_usdc":bool(total <= 100),
        "individual_reward_share":None,
        "individual_usdc_payout":None,
        "user_net_pnl":None,
    }


def run():
    started=time.monotonic()
    now=datetime.now(timezone.utc)
    result={
        "version":"PMR001_V02_PUBLIC_BOOKS",
        "observation_start_utc":now.isoformat(),
        "status":"SOURCE_BLOCKED",
        "profitability_verdict":"UNPROVEN",
        "trading_authority":"NONE","orders_created":False,
        "selected":[], "snapshots":[],
        "individual_reward_usdc":None, "user_net_pnl_usdc":None,
        "all_source_complete":False
    }
    try:
        pages=[fetch_one(i) for i in (0,100)]
        picked=selection(pages,now.date())
        result["gamma_rows_scanned"]=sum(len(p) for p in pages)
        result["selected"]=picked
        if len(picked)<3:
            result["status"]="INSUFFICIENT_MICROCAP_MARKET_SAMPLE"
            return result
        tokens=[tok for m in picked for tok in m["tokens"]]
        for index,second in enumerate(SNAPSHOT_OFFSETS_SECONDS):
            if time.monotonic()-started>MAX_SECONDS:
                raise SourceBlocked("CAPTURE_MAX_SECONDS_EXCEEDED")
            wait=max(0,started+second-time.monotonic())
            if wait:
                time.sleep(wait)
            try:
                books=fetch_books(tokens)
                pairs=[]
                for j,m in enumerate(picked):
                    try:
                        pairs.append(analyze_pair(m,books[2*j],books[2*j+1]))
                    except SourceBlocked as exc:
                        pairs.append({"market_id":m["market_id"],"status":"INVALID_BOOK_PAIR", "reason":str(exc)})
                result["snapshots"].append({
                    "snapshot_index":index,
                    "captured_utc":datetime.now(timezone.utc).isoformat(),
                    "source_status":"BATCH_RECEIVED",
                    "market_pairs":pairs,
                })
            except SourceBlocked as exc:
                result["snapshots"].append({
                    "snapshot_index":index,
                    "captured_utc":datetime.now(timezone.utc).isoformat(),
                    "source_status":"BATCH_FAILED","reason":str(exc),
                })
                break
        result["all_source_complete"]=len(result["snapshots"])==3 and all(
            s["source_status"]=="BATCH_RECEIVED" for s in result["snapshots"])
        complete_ids=[]
        for m in picked:
            ident=m["market_id"]
            rows=[next((p for p in s.get("market_pairs",[])
                        if p["market_id"]==ident),None) for s in result["snapshots"]]
            if len(rows)==3 and all(p and p.get("status")=="BOOK_PAIR_OBSERVED_NO_LIVE_ORDER"
                                     for p in rows):
                complete_ids.append(ident)
        result["complete_3x_book_market_ids"]=complete_ids
        result["market_pairs_with_any_observation"]=sum(
            p.get("status")=="BOOK_PAIR_OBSERVED_NO_LIVE_ORDER"
            for s in result["snapshots"] for p in s.get("market_pairs",[]))
        result["status"]=("BOOK_COMPETITION_VISIBLE_NET_UNPROVEN" if complete_ids else
                          "CLOB_BOOK_ACCESS_OR_IDENTITY_BLOCKED")
        result["why_profit_unproven"]=(
            "Public books do not identify maker accounts; no individual reward share, "
            "time-weighted score, quote survival or adverse fill/settlement losses.")
    except SourceBlocked as exc:
        result["status"]="SOURCE_BLOCKED"
        result["reason"]=str(exc)
    return result


if __name__=="__main__":
    r=run()
    dest=Path(os.environ.get("PMR001_V02_OUTPUT","PMR001_V02_ORDERBOOK_RECEIPT.json"))
    dest.write_text(json.dumps(r,indent=2,sort_keys=True)+"\n",encoding="utf8")
    print(json.dumps(r,indent=2,sort_keys=True))
