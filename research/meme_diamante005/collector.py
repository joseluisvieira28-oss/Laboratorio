#!/usr/bin/env python3
"""MEME-005 read-only market screen. A watchlist is NEVER a trading signal."""
import datetime as dt
import hashlib
import json
import math
import os
import pathlib
import time
import urllib.error
import urllib.parse
import urllib.request

UA="CryptoLab-MEME005-Research/1.0 (read-only)"
CG="https://api.coingecko.com/api/v3/"
DEX="https://api.dexscreener.com/token-pairs/v1/solana/"
GECKO="https://api.geckoterminal.com/api/v2/networks/solana/pools/"
MIN_AGE_DAYS=7
MIN_LIQ_USD=150000.
MIN_VOLUME_USD=50000.
MIN_TXS_24H=200
ORDER_USD=100.
MAX_ORDER_SHARE_LIQ=.001
COHORT_N=15

def utc():
    return dt.datetime.now(dt.timezone.utc).isoformat(timespec="milliseconds")

def number(x):
    try:
        v=float(x)
        return v if math.isfinite(v) else None
    except (TypeError,ValueError,OverflowError):return None

def http_json(url, timeout=16):
    start=utc(); t0=time.monotonic();raw=None;payload=None;err=None;status=None
    req=urllib.request.Request(url,headers={"User-Agent":UA,"Accept":"application/json"},method="GET")
    try:
        with urllib.request.urlopen(req,timeout=timeout) as r:
            status=r.status
            raw=r.read(3_000_000)
        payload=json.loads(raw)
    except urllib.error.HTTPError as e:
        status=e.code;err="HTTP_"+str(e.code)
    except (urllib.error.URLError,TimeoutError,OSError,ValueError,UnicodeDecodeError) as e:
        err=type(e).__name__+":"+str(e)[:180]
    return payload,dict(url=url,started_at=start,received_at=utc(),
        http_status=status,elapsed_ms=round((time.monotonic()-t0)*1000),
        bytes=len(raw) if raw is not None else None,
        body_sha256=hashlib.sha256(raw).hexdigest() if raw is not None else None,error=err)

def sol_mint(coin):
    if not isinstance(coin,dict):return None
    mint=(coin.get("platforms") or {}).get("solana")
    if not mint:
        item=(coin.get("detail_platforms") or {}).get("solana") or {}
        mint=item.get("contract_address")
    return mint if isinstance(mint,str) and len(mint)>=32 else None

def choose_pair(pairs,mint):
    if not isinstance(pairs,list):return None
    good=[p for p in pairs if p.get("chainId")=="solana"
          and (p.get("baseToken") or {}).get("address")==mint
          and isinstance(p.get("pairAddress"),str)]
    good.sort(key=lambda p:number((p.get("liquidity") or {}).get("usd")) or 0.,reverse=True)
    return good[0] if good else None

def evaluate(row,now_ms):
    reasons=[];unknown=[]
    pair=row.get("pair")
    if not pair:return dict(status="UNKNOWN",reasons=["NO_VERIFIED_POOL"],unknown=["executable_bid_ask"])
    created=pair.get("pair_created_ms")
    age=(now_ms-created)/86400000. if isinstance(created,(int,float)) else None
    liq=number(pair.get("liquidity_usd"))
    vol=number(pair.get("volume_h24_usd"))
    buy=number(pair.get("txns_h24_buys"))
    sell=number(pair.get("txns_h24_sells"))
    tx=buy+sell if buy is not None and sell is not None else None
    if age is None:unknown.append("pool_age")
    elif age<MIN_AGE_DAYS:reasons.append("POOL_AGE_LT_7D")
    if liq is None:unknown.append("reported_liquidity")
    elif liq<MIN_LIQ_USD:reasons.append("LIQ_LT_150K_USD")
    elif ORDER_USD/liq>MAX_ORDER_SHARE_LIQ:reasons.append("SIZE_GT_0_1PCT_LIQ")
    if vol is None:unknown.append("24h_volume")
    elif vol<MIN_VOLUME_USD:reasons.append("VOL_LT_50K_USD")
    if tx is None:unknown.append("24h_transactions")
    elif tx<MIN_TXS_24H:reasons.append("TX_LT_200")
    # Provider metadata is NOT a marketable swap/exit quote.
    row["age_days"]=round(age,3) if age is not None else None
    row["size_over_reported_liquidity_pct"]=round(100*ORDER_USD/liq,4) if liq else None
    if row.get("gecko_cross_check")!="OK":unknown.append("independent_pool_price_check")
    verdict="REJECT" if reasons else ("UNKNOWN" if unknown else "SCREEN_PASS_ONLY")
    return dict(status=verdict,reasons=reasons,unknown=unknown,can_execute=False,
                economic_edge=False,actual_fills=0)

def pool_extract(p):
    if not p:return None
    tx=(p.get("txns") or {}).get("h24") or {}
    return dict(pair_address=p.get("pairAddress"),dex_id=p.get("dexId"),
        url=p.get("url"),pair_created_ms=p.get("pairCreatedAt"),
        base_mint=(p.get("baseToken") or {}).get("address"),
        quote_mint=(p.get("quoteToken") or {}).get("address"),
        price_usd=number(p.get("priceUsd")),
        liquidity_usd=number((p.get("liquidity") or {}).get("usd")),
        volume_h24_usd=number((p.get("volume") or {}).get("h24")),
        txns_h24_buys=number(tx.get("buys")),
        txns_h24_sells=number(tx.get("sells")),
        price_change_h24_pct=number((p.get("priceChange") or {}).get("h24")),
        fdv_usd=number(p.get("fdv")))

def main():
    start=utc();receipts=[];rows=[]
    url=(CG+"coins/markets?"+urllib.parse.urlencode({
        "vs_currency":"usd","category":"solana-meme-coins",
        "order":"market_cap_desc","per_page":str(COHORT_N),"page":"1",
        "sparkline":"false"}))
    market,rec=http_json(url);receipts.append(dict(source="coingecko_category",**rec))
    if not isinstance(market,list) or len(market)==0:
        return dict(protocol="MEME005-v1",started_at=start,completed_at=utc(),
            source_status="COINGECKO_CATEGORY_BLOCKED",
            selection=[],
            receipts=receipts,
            final="NO-GO: no valid as-of category universe, no execution quotes")
    market=market[:COHORT_N]
    for rank,coin in enumerate(market,1):
        coinid=coin.get("id")
        row=dict(rank=rank,coingecko_id=coinid,coin_name=coin.get("name"),
                 symbol=coin.get("symbol"),market_cap_usd=number(coin.get("market_cap")),
                 cg_volume_24h_usd=number(coin.get("total_volume")),
                 mint=None,pair=None,gecko_cross_check="NOT_CHECKED")
        rows.append(row)
        if not coinid:row["screen"]=dict(status="UNKNOWN",reasons=["COIN_ID_MISSING"]);continue
        # 15 individual official coin details; NEVER infer addresses from tickers.
        detailurl=(CG+"coins/"+urllib.parse.quote(coinid,safe="")+"?"+
            urllib.parse.urlencode(dict(localization="false",tickers="false",
                market_data="false",community_data="false",developer_data="false")))
        time.sleep(.7)
        detail,rec=http_json(detailurl)
        receipts.append(dict(source="coingecko_contract",rank=rank,**rec))
        mint=sol_mint(detail)
        row["mint"]=mint
        if not mint:
            row["screen"]=dict(status="UNKNOWN",reasons=["NO_OFFICIAL_SOLANA_MINT"])
            continue
        time.sleep(.45)
        dex,rec=http_json(DEX+urllib.parse.quote(mint,safe=""))
        receipts.append(dict(source="dexscreener_pairs",rank=rank,**rec))
        pair=choose_pair(dex,mint)
        row["pairs_returned"]=len(dex) if isinstance(dex,list) else None
        row["pair"]=pool_extract(pair)
        if pair:
            time.sleep(.35)
            gecko,rec=http_json(GECKO+urllib.parse.quote(pair.get("pairAddress"),safe=""))
            receipts.append(dict(source="geckoterminal_pool",rank=rank,**rec))
            att=(((gecko or {}).get("data") or {}).get("attributes") or {}) if isinstance(gecko,dict) else {}
            dexpx=number(pair.get("priceUsd"))
            gpx=number(att.get("base_token_price_usd"))
            row["gecko_liquidity_usd"]=number(att.get("reserve_in_usd"))
            row["gecko_price_usd"]=gpx
            row["price_disagreement_pct"]=round(100*abs(dexpx-gpx)/dexpx,3) if dexpx and gpx else None
            row["gecko_cross_check"]=(
                "OK" if dexpx and gpx and abs(dexpx-gpx)/dexpx<=.03
                else ("PRICE_DISAGREEMENT" if dexpx and gpx else "UNVERIFIED"))
        row["screen"]=evaluate(row,int(dt.datetime.now(dt.timezone.utc).timestamp()*1000))
    stats={}
    for row in rows:
        s=row.get("screen") or {}
        key=s.get("status","UNKNOWN");stats[key]=stats.get(key,0)+1
    return dict(protocol="MEME005-v1",started_at=start,completed_at=utc(),
                source_status="AS_OF_CATEGORY_NOT_FULL_LAUNCH_UNIVERSE",
                cohort_size=len(rows),thresholds=dict(age_days=MIN_AGE_DAYS,
                    liquidity_usd=MIN_LIQ_USD,volume_h24_usd=MIN_VOLUME_USD,
                    transactions_24h=MIN_TXS_24H,trade_usd=ORDER_USD,
                    max_order_over_reported_liquidity=MAX_ORDER_SHARE_LIQ),
                selection=rows,receipt_count=len(receipts),receipts=receipts,screen_counts=stats,
                economic_profit_samples=0,quote_samples=0,completed_roundtrips=0,
                final="RESEARCH SCREEN ONLY: NEVER AN EXECUTABLE TRADE QUOTE OR PROFITABLE EDGE",
                no_wallet=True,no_orders=True,no_paid_endpoint=True)

if __name__=="__main__":
    result=main()
    output=pathlib.Path(os.environ.get("MEME005_OUTPUT_DIR","meme005-evidence"))
    output.mkdir(parents=True,exist_ok=True)
    raw=json.dumps(result,ensure_ascii=False,sort_keys=True,indent=2).encode("utf-8")
    (output/"snapshot.json").write_bytes(raw)
    (output/"snapshot.sha256").write_text(
        hashlib.sha256(raw).hexdigest()+"  snapshot.json\n",encoding="utf8")
    print("MEME005_RECEIPT="+json.dumps({
        "source_status":result["source_status"],"cohort":result.get("cohort_size",0),
        "screen_counts":result.get("screen_counts"),"receipt_count":result.get("receipt_count"),
        "snapshot_sha256":hashlib.sha256(raw).hexdigest(),"quote_samples":0,
        "economic_decision":"NO-GO","orders":0}))
