from __future__ import annotations

import asyncio
import copy
import json
import pathlib
import statistics
import time
import urllib.request
from datetime import datetime, timezone
from decimal import Decimal, getcontext, ROUND_FLOOR

import websockets

getcontext().prec = 50

ROOT = pathlib.Path(__file__).resolve().parent
OUT = ROOT / "evidence"
OUT.mkdir(parents=True, exist_ok=True)

RPC = "https://ethereum-rpc.publicnode.com"
QUOTER = "0x61ffe014ba17989e743c5f6cb21bf9697530b21e"
QUOTE_SEL = "c6a5026a"  # quoteExactInputSingle((address,address,uint256,uint24,uint160))
FEES = [100, 500, 3000, 10000]
NOTIONALS = [100, 500, 1000, 5000]

TOKENS = {
    "WETH": {"address":"0xc02aaa39b223fe8d0a0e5c4f27ead9083c756cc2","decimals":18,"cex":"ETHUSDT"},
    "USDC": {"address":"0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48","decimals":6,"cex":"USDCUSDT"},
    "USDT": {"address":"0xdac17f958d2ee523a2206206994597c13d831ec7","decimals":6,"cex":None},
    "WBTC": {"address":"0x2260fac5e5542a773aa44fbcfedf7c193bc2c599","decimals":8,"cex":"BTCUSDT"},
    "LINK": {"address":"0x514910771af9ca656af840dff83e8264ecf986ca","decimals":18,"cex":"LINKUSDT"},
    "PEPE": {"address":"0x6982508145454ce325ddbe47a25d4ec3d2311933","decimals":18,"cex":"PEPEUSDT"},
    "SHIB": {"address":"0x95ad61b0a150d79219dcf64e1e6cc01f0b64c4ce","decimals":18,"cex":"SHIBUSDT"},
}

PAIRS = [
    ("WETH","USDC"),
    ("WETH","USDT"),
    ("WBTC","WETH"),
    ("LINK","WETH"),
    ("PEPE","WETH"),
    ("SHIB","WETH"),
]

POOL_FEES = {
    "WETH-USDC":[100,500,3000,10000],
    "WETH-USDT":[100,500,3000,10000],
    "WBTC-WETH":[100,500,3000,10000],
    "LINK-WETH":[100,500,3000,10000],
    "PEPE-WETH":[100,500,3000,10000],
    "SHIB-WETH":[500,3000,10000],
}

SYMBOLS = ["ETHUSDT","BTCUSDT","LINKUSDT","PEPEUSDT","SHIBUSDT","USDCUSDT"]
STREAMS = "/".join(f"{s.lower()}@depth20@100ms" for s in SYMBOLS)
WS_URL = "wss://data-stream.binance.vision/stream?streams=" + STREAMS

def utc_now():
    return datetime.now(timezone.utc).isoformat()

def rpc(method, params):
    payload = json.dumps({"jsonrpc":"2.0","id":1,"method":method,"params":params}).encode()
    req = urllib.request.Request(
        RPC, data=payload,
        headers={"Content-Type":"application/json","User-Agent":"CryptoLab-AMM-LVR-001-economic/0.2"}
    )
    with urllib.request.urlopen(req, timeout=30) as r:
        body = json.loads(r.read().decode())
    if body.get("error"):
        raise RuntimeError(str(body["error"]))
    return body.get("result")

def word_address(a):
    return a[2:].lower().rjust(64,"0")

def word_uint(v):
    return hex(int(v))[2:].rjust(64,"0")

def eth_call(to, data, block_tag):
    return rpc("eth_call", [{"to":to,"data":"0x"+data}, block_tag])

def quote_exact_in(token_in, token_out, amount_in_raw, fee, block_tag):
    data = (
        QUOTE_SEL
        + word_address(TOKENS[token_in]["address"])
        + word_address(TOKENS[token_out]["address"])
        + word_uint(amount_in_raw)
        + word_uint(fee)
        + word_uint(0)
    )
    out = eth_call(QUOTER, data, block_tag)
    if not out or out == "0x":
        return None
    h = out[2:]
    if len(h) < 64 * 4:
        return None
    return {
        "amount_out_raw": int(h[0:64],16),
        "sqrt_price_x96_after": int(h[64:128],16),
        "initialized_ticks_crossed": int(h[128:192],16),
        "quoter_gas_estimate": int(h[192:256],16),
    }

def qty_to_raw(token, qty):
    x = Decimal(qty) * (Decimal(10) ** TOKENS[token]["decimals"])
    return int(x.to_integral_value(rounding=ROUND_FLOOR))

def raw_to_qty(token, raw):
    return Decimal(raw) / (Decimal(10) ** TOKENS[token]["decimals"])

def buy_base_qty(book, qty):
    left = Decimal(qty)
    cost = Decimal(0)
    filled = Decimal(0)
    for p,q in book["asks"]:
        take = min(left,q)
        cost += take*p
        filled += take
        left -= take
        if left <= 0:
            break
    if left > 0:
        return None
    return {"base_qty":filled,"quote_value":cost,"vwap":cost/filled if filled else None}

def sell_base_qty(book, qty):
    left = Decimal(qty)
    proceeds = Decimal(0)
    filled = Decimal(0)
    for p,q in book["bids"]:
        take = min(left,q)
        proceeds += take*p
        filled += take
        left -= take
        if left <= 0:
            break
    if left > 0:
        return None
    return {"base_qty":filled,"quote_value":proceeds,"vwap":proceeds/filled if filled else None}

def buy_base_for_quote(book, quote_budget):
    left = Decimal(quote_budget)
    base = Decimal(0)
    spent = Decimal(0)
    for p,q in book["asks"]:
        level_quote = p*q
        if left >= level_quote:
            base += q
            spent += level_quote
            left -= level_quote
        else:
            take = left/p
            base += take
            spent += left
            left = Decimal(0)
            break
    if left > Decimal("0.00000001"):
        return None
    return {"base_qty":base,"quote_value":spent,"vwap":spent/base if base else None}

def fee_history(block_num):
    hist = rpc("eth_feeHistory", [hex(20), hex(block_num), [50,90]])
    base = int(hist["baseFeePerGas"][-1],16)
    p50s = [int(x[0],16) for x in hist["reward"] if len(x)>=2]
    p90s = [int(x[1],16) for x in hist["reward"] if len(x)>=2]
    return {
        "base_fee_wei": base,
        "priority_p50_wei": int(statistics.median(p50s)),
        "priority_p90_wei": int(statistics.median(p90s)),
    }

class DepthFeed:
    def __init__(self):
        self.latest = {}
        self.cond = asyncio.Condition()
        self.error = None

    async def run(self):
        try:
            async with websockets.connect(
                WS_URL, ping_interval=20, ping_timeout=20, close_timeout=5, max_size=2_000_000
            ) as ws:
                async for raw in ws:
                    now_ns = time.monotonic_ns()
                    now_utc = utc_now()
                    msg = json.loads(raw)
                    stream = msg.get("stream","")
                    data = msg.get("data",{})
                    sym = stream.split("@",1)[0].upper()
                    if sym not in SYMBOLS:
                        continue
                    bids = [(Decimal(p),Decimal(q)) for p,q in data.get("bids",[])]
                    asks = [(Decimal(p),Decimal(q)) for p,q in data.get("asks",[])]
                    if not bids or not asks:
                        continue
                    rec = {
                        "symbol":sym,
                        "bids":bids,
                        "asks":asks,
                        "lastUpdateId":data.get("lastUpdateId"),
                        "received_at_utc":now_utc,
                        "mono_ns":now_ns,
                    }
                    async with self.cond:
                        self.latest[sym] = rec
                        self.cond.notify_all()
        except Exception as e:
            self.error = type(e).__name__ + ":" + str(e)[:500]
            async with self.cond:
                self.cond.notify_all()

    async def wait_ready(self, symbols, timeout=25):
        deadline = time.monotonic() + timeout
        async with self.cond:
            while True:
                if self.error:
                    raise RuntimeError("websocket feed failed: " + self.error)
                now_ns = time.monotonic_ns()
                if all(s in self.latest and now_ns-self.latest[s]["mono_ns"] < 3_000_000_000 for s in symbols):
                    return {s:copy.deepcopy(self.latest[s]) for s in symbols}
                remain = deadline-time.monotonic()
                if remain <= 0:
                    raise TimeoutError("initial WebSocket depth not ready")
                try:
                    await asyncio.wait_for(self.cond.wait(), timeout=remain)
                except asyncio.TimeoutError:
                    raise TimeoutError("initial WebSocket depth not ready")

    async def snapshot_fresh(self, symbols, max_age_sec=2):
        return await self.wait_ready(symbols, timeout=max_age_sec+5)

    async def wait_after(self, symbols, mono_ns, timeout=8):
        deadline = time.monotonic() + timeout
        async with self.cond:
            while True:
                if self.error:
                    raise RuntimeError("websocket feed failed: " + self.error)
                if all(s in self.latest and self.latest[s]["mono_ns"] > mono_ns for s in symbols):
                    return {s:copy.deepcopy(self.latest[s]) for s in symbols}
                remain = deadline-time.monotonic()
                if remain <= 0:
                    raise TimeoutError("no post-quote WebSocket depth update")
                try:
                    await asyncio.wait_for(self.cond.wait(), timeout=remain)
                except asyncio.TimeoutError:
                    raise TimeoutError("no post-quote WebSocket depth update")

def json_book_meta(book):
    return {
        "lastUpdateId":book["lastUpdateId"],
        "received_at_utc":book["received_at_utc"],
        "mono_ns":book["mono_ns"],
        "top_bid":str(book["bids"][0][0]),
        "top_bid_qty":str(book["bids"][0][1]),
        "top_ask":str(book["asks"][0][0]),
        "top_ask_qty":str(book["asks"][0][1]),
        "levels_bids":len(book["bids"]),
        "levels_asks":len(book["asks"]),
    }

async def main():
    feed = DepthFeed()
    task = asyncio.create_task(feed.run())
    rows = []
    errors = []
    started = utc_now()
    try:
        await feed.wait_ready(SYMBOLS, timeout=30)

        for left,right in PAIRS:
            pair_key = f"{left}-{right}"
            for token_in,token_out in [(left,right),(right,left)]:
                for notional in NOTIONALS:
                    rec = {
                        "pair":pair_key,
                        "direction":f"{token_in}->{token_out}",
                        "token_in":token_in,
                        "token_out":token_out,
                        "notional_usd":notional,
                        "status":"INIT",
                        "canonical_engine":"V0.2_WEBSOCKET_PER_STATE_BLOCK",
                    }
                    try:
                        sizing_symbols = []
                        if token_in != "USDT":
                            sizing_symbols.append(TOKENS[token_in]["cex"])
                        if not sizing_symbols:
                            pre_books = {}
                            input_qty = Decimal(notional)
                        else:
                            pre_books = await feed.snapshot_fresh(sorted(set(sizing_symbols)))
                            sizing_book = pre_books[TOKENS[token_in]["cex"]]
                            sized = buy_base_for_quote(sizing_book, Decimal(notional))
                            if sized is None:
                                raise RuntimeError("CEX_DEPTH_INSUFFICIENT_PREQUOTE_SIZING")
                            input_qty = sized["base_qty"]

                        amount_in_raw = qty_to_raw(token_in, input_qty)
                        input_qty = raw_to_qty(token_in, amount_in_raw)
                        rec["input_qty"] = str(input_qty)
                        rec["amount_in_raw"] = str(amount_in_raw)
                        rec["pre_quote_books"] = {s:json_book_meta(b) for s,b in pre_books.items()}

                        block_num = await asyncio.to_thread(lambda: int(rpc("eth_blockNumber",[]),16))
                        block_tag = hex(block_num)
                        rec["ethereum_block_number"] = block_num
                        rec["block_tag"] = block_tag

                        quote_start_ns = time.monotonic_ns()
                        rec["dex_quote_started_utc"] = utc_now()
                        attempts = []
                        best = None
                        for fee in POOL_FEES[pair_key]:
                            try:
                                q = await asyncio.to_thread(
                                    quote_exact_in, token_in, token_out, amount_in_raw, fee, block_tag
                                )
                                ok = q is not None and q["amount_out_raw"] > 0
                                attempts.append({"fee":fee,"ok":ok})
                                if ok and (best is None or q["amount_out_raw"] > best["amount_out_raw"]):
                                    best = {**q,"fee":fee}
                            except Exception as e:
                                attempts.append({"fee":fee,"ok":False,"error":type(e).__name__})
                        quote_end_ns = time.monotonic_ns()
                        rec["dex_quote_ended_utc"] = utc_now()
                        rec["dex_quote_start_mono_ns"] = quote_start_ns
                        rec["dex_quote_end_mono_ns"] = quote_end_ns
                        rec["quote_attempts"] = attempts
                        if best is None:
                            raise RuntimeError("NO_EXECUTABLE_UNISWAP_QUOTE")

                        output_qty = raw_to_qty(token_out, best["amount_out_raw"])
                        rec["best_fee_tier"] = best["fee"]
                        rec["output_qty"] = str(output_qty)
                        rec["quoter_gas_estimate"] = best["quoter_gas_estimate"]

                        needed = {"ETHUSDT"}
                        if token_in != "USDT":
                            needed.add(TOKENS[token_in]["cex"])
                        if token_out != "USDT":
                            needed.add(TOKENS[token_out]["cex"])
                        post_books = await feed.wait_after(sorted(needed), quote_end_ns, timeout=10)
                        rec["post_quote_books"] = {s:json_book_meta(b) for s,b in post_books.items()}

                        if token_in == "USDT":
                            input_cost = Decimal(input_qty)
                            input_leg = None
                        else:
                            input_leg = buy_base_qty(post_books[TOKENS[token_in]["cex"]], input_qty)
                            if input_leg is None:
                                raise RuntimeError("CEX_DEPTH_INSUFFICIENT_INPUT_REPLENISH")
                            input_cost = input_leg["quote_value"]

                        if token_out == "USDT":
                            output_proceeds = Decimal(output_qty)
                            output_leg = None
                        else:
                            output_leg = sell_base_qty(post_books[TOKENS[token_out]["cex"]], output_qty)
                            if output_leg is None:
                                raise RuntimeError("CEX_DEPTH_INSUFFICIENT_OUTPUT_LIQUIDATION")
                            output_proceeds = output_leg["quote_value"]

                        fh = await asyncio.to_thread(fee_history, block_num)
                        eth_ask = post_books["ETHUSDT"]["asks"][0][0]
                        gas_base_usdt = (
                            Decimal(300000)
                            * Decimal(fh["base_fee_wei"] + fh["priority_p50_wei"])
                            / Decimal(10**18)
                            * eth_ask
                        )
                        gas_stress_usdt = (
                            Decimal(500000)
                            * Decimal(fh["base_fee_wei"] + fh["priority_p90_wei"])
                            / Decimal(10**18)
                            * eth_ask
                        )

                        fee_notional = Decimal(0)
                        legs = 0
                        if input_leg is not None:
                            fee_notional += input_cost
                            legs += 1
                        if output_leg is not None:
                            fee_notional += output_proceeds
                            legs += 1

                        cex_fee_base = fee_notional * Decimal("0.001")
                        cex_fee_stress = fee_notional * Decimal("0.002")
                        gross = output_proceeds - input_cost
                        base_known = gross - cex_fee_base - gas_base_usdt
                        stress_known = gross - cex_fee_stress - gas_stress_usdt
                        denom = input_cost if input_cost > 0 else Decimal(notional)

                        rec.update({
                            "status":"EXECUTABLE",
                            "cex_legs":legs,
                            "input_replenish_usdt":str(input_cost),
                            "output_liquidation_usdt":str(output_proceeds),
                            "gross_pnl_usdt":str(gross),
                            "gross_bps":str(gross/denom*Decimal(10000)),
                            "cex_fee_base_usdt":str(cex_fee_base),
                            "cex_fee_stress_usdt":str(cex_fee_stress),
                            "gas_base_usdt":str(gas_base_usdt),
                            "gas_stress_usdt":str(gas_stress_usdt),
                            "base_known_pnl_usdt":str(base_known),
                            "stress_known_pnl_usdt":str(stress_known),
                            "base_known_bps":str(base_known/denom*Decimal(10000)),
                            "stress_known_bps":str(stress_known/denom*Decimal(10000)),
                            "base_known_survivor":base_known>0,
                            "stress_known_survivor":stress_known>0,
                            "accessibility_state":"ACCESSIBILITY_UNPROVEN" if base_known>0 else "KNOWN_COST_FAIL",
                            "builder_direct_payment_bound":False,
                            "failed_inclusion_risk_bound":False,
                            "full_cost_survivor":False,
                            "fee_history":fh,
                        })
                    except Exception as e:
                        rec["status"] = "UNAVAILABLE"
                        rec["error"] = type(e).__name__ + ":" + str(e)[:500]
                        errors.append({
                            "pair":rec["pair"],
                            "direction":rec["direction"],
                            "notional_usd":notional,
                            "error":rec["error"],
                        })
                    rows.append(rec)

        exec_rows = [r for r in rows if r["status"]=="EXECUTABLE"]
        base_surv = [r for r in exec_rows if r.get("base_known_survivor")]
        stress_surv = [r for r in exec_rows if r.get("stress_known_survivor")]

        by_pair = {}
        for pair in [f"{a}-{b}" for a,b in PAIRS]:
            rr = [r for r in exec_rows if r["pair"]==pair]
            by_pair[pair] = {
                "executable_states":len(rr),
                "base_known_survivor_states":sum(bool(r.get("base_known_survivor")) for r in rr),
                "stress_known_survivor_states":sum(bool(r.get("stress_known_survivor")) for r in rr),
            }

        summary = {
            "lab_id":"AMM-LVR-CROSSVENUE-001",
            "mve_id":"AMM-LVR-CROSSVENUE-001-FWD-MVE1",
            "phase":"FORWARD_CAUSAL_ENGINEERING_SWEEP_V0.2",
            "canonical_engine":"V0.2_WEBSOCKET_PER_STATE_BLOCK",
            "started_at_utc":started,
            "ended_at_utc":utc_now(),
            "expected_candidate_states":48,
            "executable_candidate_states":len(exec_rows),
            "unavailable_candidate_states":48-len(exec_rows),
            "base_known_cost_survivor_states":len(base_surv),
            "stress_known_cost_survivor_states":len(stress_surv),
            "by_pair":by_pair,
            "independent_events_counted":0,
            "discovery_gate_required_events":100,
            "discovery_gate_required_days":14,
            "economic_verdict":"INSUFFICIENT_FORWARD_SAMPLE",
            "accessibility_verdict":"UNPROVEN",
            "full_cost_survivors_claimed":0,
            "builder_direct_payment_bound":False,
            "failed_inclusion_risk_bound":False,
            "error_count":len(errors),
            "errors":errors,
            "note":"Canonical causal engineering sweep. Profitability signs are pilot diagnostics only and count as zero independent Discovery events."
        }

        (OUT/"forward_economic_sweep_v0_2.json").write_text(
            json.dumps(rows,indent=2,sort_keys=True),encoding="utf-8"
        )
        (OUT/"forward_economic_sweep_v0_2_summary.json").write_text(
            json.dumps(summary,indent=2,sort_keys=True),encoding="utf-8"
        )
        print(json.dumps(summary,indent=2,sort_keys=True))

        if len(exec_rows) < 36:
            raise SystemExit(2)
    finally:
        task.cancel()
        try:
            await task
        except BaseException:
            pass

if __name__ == "__main__":
    asyncio.run(main())
