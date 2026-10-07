"""Public observation scout. No execution imports or automatic arming."""
from datetime import datetime, timezone
from decimal import Decimal, ROUND_FLOOR
from pathlib import Path
import hashlib
import json
import subprocess
import time

from .market import MEXCFuturesPublicFeed
from .friction import MEXC_API_TAKER_ONE_WAY_FRACTION, FEE_SOURCE


def dec(value):
    result = Decimal(str(value))
    if not result.is_finite():
        raise ValueError("non-finite public numeric field")
    return result


def sweep(rows, contracts):
    remaining, total = contracts, Decimal(0)
    for row in rows:
        price, volume = dec(row[0]), dec(row[1])
        if price <= 0 or volume < 0:
            raise ValueError("invalid depth")
        take = min(remaining, volume)
        total += take * price
        remaining -= take
        if remaining == 0:
            return total / contracts
    raise ValueError("insufficient visible depth")


def observe(feed=None):
    feed = feed or MEXCFuturesPublicFeed(timeout=10)
    receipt = dict(symbol="NEAR_USDT", verdict="NO_TRADE", classification="SOURCE_BLOCKED",
                   execution_armed=False, orders_created=False, account_reads=False,
                   checked_at_utc=datetime.now(timezone.utc).isoformat(), raw={}, requests=[])
    # Fixed public paths; inherited feed enforces host and GET allowlist.
    paths = dict(specs="/api/v1/contract/detail", ticker="/api/v1/contract/ticker?symbol=NEAR_USDT",
                 funding="/api/v1/contract/funding_rate/NEAR_USDT", depth="/api/v1/contract/depth/NEAR_USDT?limit=20")
    try:
        for name, path in paths.items():
            started = time.time_ns() // 1000000
            payload = feed._get_json(path)
            receipt["requests"].append(dict(path=path, started_ms=started, completed_ms=time.time_ns() // 1000000))
            if payload.get("success") is not True or payload.get("code") != 0:
                raise ValueError(f"invalid {name} response")
            data = payload["data"]
            if name in ("specs", "ticker") and isinstance(data, list):
                data = next(row for row in data if row.get("symbol") == "NEAR_USDT")
            receipt["raw"][name] = data
        c, t, f, book = (receipt["raw"][k] for k in ("specs", "ticker", "funding", "depth"))
        if c["state"] != 0 or c["futureType"] != 1 or c["quoteCoin"] != "USDT":
            raise ValueError("contract inactive or not USDT perpetual")
        now = time.time_ns() // 1000000
        for name, data in (("depth", book), ("funding", f), ("ticker", t)):
            if abs(now - int(data["timestamp"])) > 30000:
                raise ValueError(f"stale {name} timestamp")
        size, step, minimum, tick = (dec(c[k]) for k in ("contractSize", "volUnit", "minVol", "priceUnit"))
        if min(size, step, minimum, tick) <= 0:
            raise ValueError("invalid contract increments")
        bid, ask = dec(book["bids"][0][0]), dec(book["asks"][0][0])
        if not 0 < bid <= ask:
            raise ValueError("crossed book")
        mid = (bid + ask) / 2
        # Prior conversation levels are a scenario, never signal authority.
        entry, stop, tp1, tp2 = map(dec, ("5.32", "5.16", "5.55", "5.72"))
        if any(price % tick for price in (entry, stop, tp1, tp2)):
            raise ValueError("scenario levels off MEXC tick")
        volume = (dec(75) / (entry * size) / step).to_integral_value(rounding=ROUND_FLOOR) * step
        if volume < minimum or volume > dec(c["maxVol"]):
            raise ValueError("scenario volume outside contract bounds")
        buy, sell = sweep(book["asks"], volume), sweep(book["bids"], volume)
        quantity, fee = volume * size, dec(MEXC_API_TAKER_ONE_WAY_FRACTION)
        funding = dec(f["fundingRate"])
        if dec(f["fairPrice"]) <= 0 or dec(f["idxPrice"]) <= 0 or int(f["collectCycle"]) <= 0:
            raise ValueError("invalid funding/mark/index")
        receipt["metrics"] = dict(min_contracts=str(minimum), contract_size_near=str(size),
            min_near=str(minimum*size), min_notional_at_ask=str(minimum*size*ask), price_tick=str(tick),
            bid=str(bid), ask=str(ask), last=str(t["lastPrice"]), mark=str(f["fairPrice"]), index=str(f["idxPrice"]),
            spread_bps=str((ask-bid)/mid*10000), buy_vwap=str(buy), sell_vwap=str(sell),
            buy_impact_bps=str((buy/ask-1)*10000), sell_impact_bps=str((1-sell/bid)*10000),
            funding_rate=str(funding), funding_cycle_hours=f["collectCycle"], next_settlement_ms=f["nextSettleTime"])
        receipt["scenario_only"] = dict(side="LONG", entry=str(entry), stop=str(stop), tp1=str(tp1), tp2=str(tp2),
            contracts=str(volume), quantity_near=str(quantity), notional_usdt=str(quantity*entry),
            leverage=3, margin_mode="ISOLATED", margin_usdt=str(quantity*entry/3),
            taker_fee_bps=str(fee*10000), fee_source=FEE_SOURCE,
            stop_loss_with_entry_exit_fees_usdt=str(quantity*(entry-stop)+quantity*(entry+stop)*fee),
            tp1_net_full_position_usdt=str(quantity*(tp1-entry)-quantity*(entry+tp1)*fee),
            tp2_net_full_position_usdt=str(quantity*(tp2-entry)-quantity*(entry+tp2)*fee),
            funding_one_settlement_at_entry_usdt=str(quantity*entry*funding),
            split_50_percent_contracts=str(volume/2),
            invalidation="Closed MEXC 15m below 5.16 before fill; no-chase above 5.45 without retest; snapshot expires after 30s",
            limitations="Not a signal. Limit fill, future exit slippage and future funding unproven. No closed-candle evidence or authorized NEAR strategy in this scout.")
        receipt.update(classification="PUBLIC_OBSERVATION_ONLY", reason="NEAR_LONG_SIGNAL_NOT_VALIDATED: prior cross-venue levels lack MEXC closed-candle/strategy evidence; scenario is not TRADEABLE_CANDIDATE")
    except Exception as exc:
        receipt["reason"] = f"PUBLIC_SOURCE_OR_SCHEMA_BLOCKED: {type(exc).__name__}: {exc}"
    return receipt


def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    out = Path(args.output)
    out.mkdir(parents=True, exist_ok=True)
    result = observe()
    result["source_commit"] = subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip()
    raw = (json.dumps(result, indent=2, ensure_ascii=True) + "\n").encode()
    (out / "receipt.json").write_bytes(raw)
    (out / "receipt.sha256").write_text(hashlib.sha256(raw).hexdigest() + "  receipt.json\n")
    verdict = {k: result[k] for k in ("symbol", "verdict", "classification", "reason", "execution_armed")}
    (out / "radar_verdict.json").write_text(json.dumps(verdict, indent=2) + "\n")
    print(json.dumps(verdict))


if __name__ == "__main__":
    main()
