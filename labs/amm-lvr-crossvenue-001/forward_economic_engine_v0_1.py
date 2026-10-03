from __future__ import annotations

import json
import math
import pathlib
import statistics
import time
import urllib.request
from datetime import datetime, timezone
from decimal import Decimal, getcontext

getcontext().prec = 50

ROOT = pathlib.Path(__file__).resolve().parent
OUT = ROOT / "evidence"
OUT.mkdir(parents=True, exist_ok=True)

RPC = "https://ethereum-rpc.publicnode.com"
FACTORY = "0x1f98431c8ad98523631ae4a59f267346ea31f984"
QUOTER = "0x61ffe014ba17989e743c5f6cb21bf9697530b21e"
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

def utc_now():
    return datetime.now(timezone.utc).isoformat()

def rpc(method, params):
    payload = json.dumps({"jsonrpc":"2.0","id":1,"method":method,"params":params}).encode()
    req = urllib.request.Request(
        RPC, data=payload,
        headers={"Content-Type":"application/json","User-Agent":"CryptoLab-AMM-LVR-001-economic/0.1"}
    )
    with urllib.request.urlopen(req, timeout=30) as r:
        body = json.loads(r.read().decode())
    if body.get("error"):
        raise RuntimeError(str(body["error"]))
    return body.get("result")

def get_json(url):
    req = urllib.request.Request(url, headers={"User-Agent":"CryptoLab-AMM-LVR-001-economic/0.1"})
    t0 = time.monotonic_ns()
    with urllib.request.urlopen(req, timeout=30) as r:
        body = json.loads(r.read().decode())
    t1 = time.monotonic_ns()
    return body, {"received_at_utc":utc_now(),"mono_ns":t1,"latency_ms":(t1-t0)/1e6}

def selector(sig):
    return rpc("web3_sha3", ["0x"+sig.encode().hex()])[2:10]

GETPOOL_SEL = selector("getPool(address,address,uint24)")
QUOTE_SEL = selector("quoteExactInputSingle((address,address,uint256,uint24,uint160))")

def word_address(a):
    return a[2:].lower().rjust(64,"0")

def word_uint(v):
    return hex(int(v))[2:].rjust(64,"0")

def eth_call(to, data, block_tag):
    return rpc("eth_call", [{"to":to,"data":"0x"+data}, block_tag])

def get_pool(a,b,fee,block_tag):
    out = eth_call(FACTORY, GETPOOL_SEL+word_address(a)+word_address(b)+word_uint(fee), block_tag)
    if not out or out=="0x":
        return None
    addr = "0x"+out[-40:]
    if int(addr,16)==0:
        return None
    return addr.lower()

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
    if not out or out=="0x":
        return None
    h = out[2:]
    if len(h) < 64*4:
        return None
    return {
        "amount_out_raw": int(h[0:64],16),
        "sqrt_price_x96_after": int(h[64:128],16),
        "initialized_ticks_crossed": int(h[128:192],16),
        "quoter_gas_estimate": int(h[192:256],16),
    }

def book_ticker(symbol):
    body, meta = get_json(f"https://data-api.binance.vision/api/v3/ticker/bookTicker?symbol={symbol}")
    return {"bid":Decimal(body["bidPrice"]),"bid_qty":Decimal(body["bidQty"]),
            "ask":Decimal(body["askPrice"]),"ask_qty":Decimal(body["askQty"]), **meta}

def depth(symbol):
    body, meta = get_json(f"https://data-api.binance.vision/api/v3/depth?symbol={symbol}&limit=100")
    return {
        "bids":[(Decimal(p),Decimal(q)) for p,q in body["bids"]],
        "asks":[(Decimal(p),Decimal(q)) for p,q in body["asks"]],
        **meta
    }

def sweep_buy(book, base_qty):
    left = Decimal(base_qty)
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
    return {"qty":filled,"usdt":cost,"vwap":cost/filled if filled else None}

def sweep_sell(book, base_qty):
    left = Decimal(base_qty)
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
    return {"qty":filled,"usdt":proceeds,"vwap":proceeds/filled if filled else None}

def raw_to_qty(token, raw):
    return Decimal(raw) / (Decimal(10) ** TOKENS[token]["decimals"])

def qty_to_raw(token, qty):
    scaled = Decimal(qty) * (Decimal(10) ** TOKENS[token]["decimals"])
    return int(scaled.to_integral_value(rounding="ROUND_FLOOR"))

def fee_history(block_num):
    hist = rpc("eth_feeHistory", [hex(20), hex(block_num), [50,90]])
    base = int(hist["baseFeePerGas"][-1],16)
    p50s = [int(x[0],16) for x in hist["reward"] if len(x)>=2]
    p90s = [int(x[1],16) for x in hist["reward"] if len(x)>=2]
    return {
        "base_fee_wei":base,
        "priority_p50_wei":int(statistics.median(p50s)),
        "priority_p90_wei":int(statistics.median(p90s)),
    }

started = utc_now()
block_num = int(rpc("eth_blockNumber",[]),16)
block_tag = hex(block_num)
fees_now = fee_history(block_num)

# Freeze pool addresses at the sweep block.
pool_map = {}
for a,b in PAIRS:
    for fee in FEES:
        try:
            pool_map[(a,b,fee)] = get_pool(TOKENS[a]["address"],TOKENS[b]["address"],fee,block_tag)
        except Exception:
            pool_map[(a,b,fee)] = None

# Pre-quote sizing references.
sizing = {}
for token,meta in TOKENS.items():
    if token=="USDT":
        continue
    try:
        sizing[token] = book_ticker(meta["cex"])
    except Exception as e:
        sizing[token] = {"error":type(e).__name__+":"+str(e)[:300]}

rows = []
errors = []

for left,right in PAIRS:
    for token_in,token_out in [(left,right),(right,left)]:
        for notional in NOTIONALS:
            rec = {
                "pair":f"{left}-{right}",
                "direction":f"{token_in}->{token_out}",
                "token_in":token_in,
                "token_out":token_out,
                "notional_usd":notional,
                "block_number":block_num,
                "block_tag":block_tag,
                "status":"INIT",
            }
            try:
                if token_in=="USDT":
                    input_qty = Decimal(notional)
                else:
                    ref = sizing.get(token_in,{})
                    if "ask" not in ref:
                        raise RuntimeError("missing sizing reference")
                    input_qty = Decimal(notional) / ref["ask"]

                amount_in_raw = qty_to_raw(token_in,input_qty)
                input_qty = raw_to_qty(token_in,amount_in_raw)
                rec["input_qty"] = str(input_qty)
                rec["amount_in_raw"] = str(amount_in_raw)

                best = None
                quote_attempts = []
                quote_started = utc_now()
                quote_mono = time.monotonic_ns()
                for fee in FEES:
                    pool = pool_map.get((left,right,fee))
                    if not pool:
                        quote_attempts.append({"fee":fee,"pool":None,"ok":False})
                        continue
                    try:
                        q = quote_exact_in(token_in,token_out,amount_in_raw,fee,block_tag)
                        ok = q is not None and q["amount_out_raw"]>0
                        quote_attempts.append({"fee":fee,"pool":pool,"ok":ok})
                        if ok and (best is None or q["amount_out_raw"]>best["amount_out_raw"]):
                            best = {**q,"fee":fee,"pool":pool}
                    except Exception as e:
                        quote_attempts.append({"fee":fee,"pool":pool,"ok":False,"error":type(e).__name__})
                quote_ended = utc_now()
                if not best:
                    raise RuntimeError("no executable Uniswap quote")

                output_qty = raw_to_qty(token_out,best["amount_out_raw"])
                rec.update({
                    "dex_quote_started_utc":quote_started,
                    "dex_quote_ended_utc":quote_ended,
                    "dex_quote_mono_ns":quote_mono,
                    "best_fee_tier":best["fee"],
                    "best_pool":best["pool"],
                    "output_qty":str(output_qty),
                    "quoter_gas_estimate":best["quoter_gas_estimate"],
                    "quote_attempts":quote_attempts,
                })

                books = {}
                needed = set()
                if token_in!="USDT":
                    needed.add(TOKENS[token_in]["cex"])
                if token_out!="USDT":
                    needed.add(TOKENS[token_out]["cex"])
                needed.add("ETHUSDT")
                for sym in sorted(needed):
                    books[sym] = depth(sym)

                if token_in=="USDT":
                    input_cost = Decimal(input_qty)
                    input_leg = None
                else:
                    input_leg = sweep_buy(books[TOKENS[token_in]["cex"]], input_qty)
                    if input_leg is None:
                        raise RuntimeError("insufficient CEX ask depth for input replenish")
                    input_cost = input_leg["usdt"]

                if token_out=="USDT":
                    output_proceeds = Decimal(output_qty)
                    output_leg = None
                else:
                    output_leg = sweep_sell(books[TOKENS[token_out]["cex"]], output_qty)
                    if output_leg is None:
                        raise RuntimeError("insufficient CEX bid depth for output liquidation")
                    output_proceeds = output_leg["usdt"]

                eth_ask = books["ETHUSDT"]["asks"][0][0]
                gas_base_usdt = (
                    Decimal(300000)
                    * Decimal(fees_now["base_fee_wei"] + fees_now["priority_p50_wei"])
                    / Decimal(10**18)
                    * eth_ask
                )
                gas_stress_usdt = (
                    Decimal(500000)
                    * Decimal(fees_now["base_fee_wei"] + fees_now["priority_p90_wei"])
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

                denom = input_cost if input_cost>0 else Decimal(notional)
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
                    "cex_depth_receipts":{s:{"received_at_utc":b["received_at_utc"],"mono_ns":b["mono_ns"],"latency_ms":b["latency_ms"]} for s,b in books.items()},
                })
            except Exception as e:
                rec["status"]="UNAVAILABLE"
                rec["error"]=type(e).__name__+":"+str(e)[:500]
                errors.append({"pair":rec["pair"],"direction":rec["direction"],"notional_usd":notional,"error":rec["error"]})
            rows.append(rec)

exec_rows = [r for r in rows if r["status"]=="EXECUTABLE"]
base_surv = [r for r in exec_rows if r.get("base_known_survivor")]
stress_surv = [r for r in exec_rows if r.get("stress_known_survivor")]

summary = {
    "lab_id":"AMM-LVR-CROSSVENUE-001",
    "mve_id":"AMM-LVR-CROSSVENUE-001-FWD-MVE1",
    "phase":"FORWARD_ENGINEERING_SWEEP_V0.1",
    "started_at_utc":started,
    "ended_at_utc":utc_now(),
    "ethereum_block_number":block_num,
    "expected_candidate_states":48,
    "executable_candidate_states":len(exec_rows),
    "unavailable_candidate_states":48-len(exec_rows),
    "base_known_cost_survivor_states":len(base_surv),
    "stress_known_cost_survivor_states":len(stress_surv),
    "independent_events_counted":0,
    "discovery_gate_required_events":100,
    "discovery_gate_required_days":14,
    "economic_verdict":"INSUFFICIENT_FORWARD_SAMPLE",
    "accessibility_verdict":"UNPROVEN",
    "full_cost_survivors_claimed":0,
    "error_count":len(errors),
    "fee_history":fees_now,
    "note":"First frozen engineering sweep only. Candidate-state profitability is not an independent-event count and cannot promote the lab."
}

(OUT/"forward_economic_sweep_v0_1.json").write_text(json.dumps(rows,indent=2,sort_keys=True),encoding="utf-8")
(OUT/"forward_economic_sweep_v0_1_summary.json").write_text(json.dumps(summary,indent=2,sort_keys=True),encoding="utf-8")
print(json.dumps(summary,indent=2,sort_keys=True))

# Engineering pass requires broad executability, but economic sign never controls CI success.
if len(exec_rows) < 36:
    raise SystemExit(2)
