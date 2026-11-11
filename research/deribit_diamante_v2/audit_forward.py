"""Independent, read-only audit of preserved forward entry ZIPs.

No imports from probe.py. Never calls market endpoints or manufactures PnL.
A valid entry/abstention is still NOT evidence of net expected profit.
"""
import argparse
import datetime as dt
from decimal import Decimal as D, ROUND_FLOOR
import hashlib
import json
import math
from pathlib import Path
import statistics
import zipfile

UTC = dt.timezone.utc
Q = D("0.01")
FREEZE = "e34ad0732abf1574735006b33307ddf5653fbaa9"
NAMES = {"instruments", "summaries", "deliveries", "index", "atm_call", "atm_put"}
ELIGIBLE = {"SIMULATED_ENTRY_SELECTED", "ABSTAIN_FORECAST"}

def check(ok, reason):
    if not ok:
        raise ValueError(reason)

def dec(value):
    result = D(str(value))
    check(result.is_finite(), "NONFINITE_PRICE")
    return result

def instant(text):
    value = dt.datetime.fromisoformat(text.replace("Z", "+00:00"))
    check(value.tzinfo is not None, "NAIVE_TIMESTAMP")
    return value.astimezone(UTC)

def record(z, filename):
    return json.loads(z.read(filename))

def fee(price, index):
    return Q * min(index * D("0.0003"), price / D(8))

def next_price(price, meta):
    tick = dec(meta["tick_size"])
    for rule in sorted(meta.get("tick_size_steps", []), key=lambda row: dec(row["above_price"])):
        if price >= dec(rule["above_price"]):
            tick = dec(rule["tick_size"])
    check(tick > 0, "BAD_TICK")
    return ((price / tick).to_integral_value(rounding=ROUND_FLOOR) + 1) * tick

def audit_entry(archive, sha256, day):
    body = Path(archive).read_bytes()
    check(hashlib.sha256(body).hexdigest() == sha256, "ENTRY_ARCHIVE_HASH_MISMATCH")
    day = dt.date.fromisoformat(day)
    with zipfile.ZipFile(archive) as z:
        files = set(z.namelist())
        receipt_name = "raw/receipt.json" if "raw/receipt.json" in files else "receipt.json"
        check(receipt_name in files, "ENTRY_RECEIPT_MISSING")
        receipt = record(z, receipt_name)
        check(receipt.get("freeze") == FREEZE, "FREEZE_MISMATCH")
        check(receipt.get("mode") == "entry" and receipt.get("simulation") is True,
              "NOT_SIMULATED_FORWARD_ENTRY")
        manifest = receipt.get("manifest", [])
        check(isinstance(manifest, list), "INVALID_MANIFEST")
        raw = {}
        for item in manifest:
            name = item["name"]
            check(name not in raw and name in NAMES, "DUPLICATE_OR_UNEXPECTED_SOURCE")
            if "sha256" in item:
                filename = "raw/" + name + ".json"
                check(filename in files, "MISSING_RAW")
                bytes_ = z.read(filename)
                check(hashlib.sha256(bytes_).hexdigest() == item["sha256"], "RAW_HASH_MISMATCH")
                raw[name] = json.loads(bytes_)
            else:
                check("error" in item, "UNEXPLAINED_MISSING_RAW")
                raw[name] = None
        state = receipt["status"]
        if state not in ELIGIBLE:
            check(state in {"SOURCE_BLOCKED", "MISSED_SESSION", "ABSTAIN_LIQUIDITY_COST"},
                  "UNKNOWN_ENTRY_STATUS")
            return dict(status="NON_ECONOMIC_ENTRY",reason=state,raw_responses_verified=sum(v is not None for v in raw.values()),
                        simulated=True,edge_proven=False)
        check(set(raw) == NAMES and all(raw.values()), "INCOMPLETE_ACCEPTED_SOURCE")
        check(set(row["name"] for row in manifest) == NAMES, "INCOMPLETE_MANIFEST")
        check(record(z, "raw/manifest.json") == manifest, "MANIFEST_DISAGREEMENT")
        start = dt.datetime.combine(day, dt.time(8, 5), UTC)
        stop = dt.datetime.combine(day, dt.time(8, 10), UTC)
        for item in manifest:
            check(start <= instant(item["started"]) <= instant(item["received"]) < stop,
                  "OUT_OF_WINDOW_SOURCE")
        check(start <= instant(receipt["observed"]) < stop, "OUT_OF_WINDOW_OBSERVATION")
        check(start <= instant(receipt["decision_at"]) < stop, "OUT_OF_WINDOW_DECISION")
        check(receipt["diagnostic_only"] is False and receipt["orders"] == 0, "NOT_SIMULATION_ONLY")
        for name, envelope in raw.items():
            check(envelope.get("testnet") is False and "result" in envelope and "error" not in envelope,
                  "INVALID_PUBLIC_SOURCE")
        data = {k:v["result"] for k,v in raw.items()}
        index = dec(data["index"]["index_price"])
        check(index > 0 and index == dec(receipt["index"]), "INDEX_MISMATCH")
        expiration = dt.datetime.combine(day + dt.timedelta(days=1), dt.time(8), UTC)
        check(instant(receipt["expiry"]) == expiration, "EXPIRY_MISMATCH")
        metas = {}
        for m in data["instruments"]:
            if m.get("instrument_name", "").startswith("BTC_USDC-") and m.get("expiration_timestamp") == int(expiration.timestamp()*1000):
                metas[m["instrument_name"]] = m
        pairs = {}
        for m in metas.values():
            pairs.setdefault(dec(m["strike"]), {})[m["option_type"]] = m
        strikes = [k for k, legs in pairs.items() if set(legs) == {"call", "put"}]
        check(bool(strikes), "NO_ATM_PAIR")
        strike = min(strikes, key=lambda v:(abs(v-index),v))
        chosen = {"atm_call":pairs[strike]["call"]["instrument_name"],
                  "atm_put":pairs[strike]["put"]["instrument_name"]}
        check(receipt["chosen"] == chosen, "STRIKE_HINDSIGHT_OR_MISMATCH")
        legs = []
        timestamps = []
        for side in ("atm_call", "atm_put"):
            m = metas[chosen[side]]
            b = data[side]
            check(m["kind"] == "option" and m["base_currency"] == "BTC" and m["price_index"] == "btc_usdc"
                  and m["quote_currency"] == m["settlement_currency"] == "USDC"
                  and dec(m["contract_size"]) == 1 and dec(m["min_trade_amount"]) == Q
                  and dec(m["taker_commission"]) == D("0.0003") and m["is_active"] is True,
                  "CONTRACT_METADATA_MISMATCH")
            check(b["instrument_name"] == chosen[side] and b["state"] == "open", "BOOK_IDENTITY")
            bid = max((dec(v),dec(q)) for v,q in b["bids"])
            ask = min((dec(v),dec(q)) for v,q in b["asks"])
            check(0 < bid[0] < ask[0] and min(bid[1],ask[1]) >= D("0.05"),
                  "BAD_PRICE_OR_DEPTH")
            item = next(row for row in manifest if row["name"] == side)
            age = instant(item["received"]).timestamp() - b["timestamp"]/1000
            check(-3 <= age <= 10, "BOOK_AGE")
            timestamps.append(b["timestamp"])
            legs.append(dict(meta=m, book=b, bid=bid[0], ask=ask[0],
                             index=dec(b["index_price"]), side=m["option_type"]))
        check(max(timestamps)-min(timestamps)<=1000, "BOOK_SKEW")
        check(max(abs(t/1000-instant(next(row for row in manifest if row["name"]=="index")["received"]).timestamp())
                  for t in timestamps) <= 10, "INDEX_DISTANCE")
        premium = sum(Q*v["ask"] for v in legs)
        entryfee = sum(fee(v["ask"],v["index"]) for v in legs)
        exitfee = sum(fee(v["bid"],v["index"]) for v in legs)
        spread = Q*sum(v["ask"]-v["bid"] for v in legs)
        friction_pct = (spread+entryfee+exitfee)/premium*100
        entry_allin = premium+entryfee
        one_tick = sum(Q*next_price(v["ask"],v["meta"])+fee(next_price(v["ask"],v["meta"]),v["index"]) for v in legs)
        econ = receipt["structures"]["straddle"]
        recorded_legs = econ.get("legs", [])
        check(len(recorded_legs) == 2, "MISSING_PINNED_ENTRY_LEGS")
        for name, expected, pinned in zip(("atm_call", "atm_put"), legs, recorded_legs):
            check(pinned.get("symbol") == chosen[name] and pinned.get("side") == expected["side"],
                  "PINNED_CONTRACT_MISMATCH")
            for key, value in (("strike", strike), ("ask", expected["ask"]),
                               ("bid", expected["bid"]), ("index", expected["index"])):
                check(key in pinned and abs(dec(pinned[key])-value)<D(".000001"),
                      "PINNED_LEG_MISMATCH_"+key)
            book=data[name]
            check(dec(pinned.get("bid_depth",0))==max((dec(q) for v,q in book["bids"] if dec(v)==expected["bid"]),default=D(0)) and
                  dec(pinned.get("ask_depth",0))==max((dec(q) for v,q in book["asks"] if dec(v)==expected["ask"]),default=D(0)),
                  "PINNED_DEPTH_MISMATCH")
            check(instant(pinned.get("expiry"))==expiration, "PINNED_EXPIRY_MISMATCH")
        for field,value in [("entry_premium",premium),("entry_fee",entryfee),
                            ("entry_allin",entry_allin),("roundtrip_pct",friction_pct),
                            ("one_tick_allin",one_tick)]:
            check(abs(dec(econ[field])-value) < D("0.000001"), "ECONOMICS_MISMATCH_"+field)
        check(abs(strike/index-1)<=D(".01") and friction_pct<=8, "LIQUIDITY_GATE_VIOLATION")
        cutoff = day
        daily = {dt.date.fromisoformat(x["date"]):float(x["delivery_price"])
                 for x in data["deliveries"]["data"] if dt.date.fromisoformat(x["date"])<=cutoff}
        dates = [cutoff-dt.timedelta(days=i) for i in reversed(range(61))]
        check(all(x in daily and math.isfinite(daily[x]) and daily[x]>0 for x in dates),
              "MISSING_CAUSAL_DELIVERIES")
        returns = [math.log(daily[b]/daily[a]) for a,b in zip(dates,dates[1:])]
        center = statistics.mean(returns)
        horizon = (expiration-instant(receipt["observed"])).total_seconds()
        multiples = [math.exp((r-center)*math.sqrt(horizon/86400)) for r in returns]
        avg = statistics.mean(multiples)
        spots = [float(index)*m/avg for m in multiples]
        def intrinsic(s):
            total = D(0)
            for leg in legs:
                move = max(D(0),dec(s)-strike) if leg["side"]=="call" else max(D(0),strike-dec(s))
                total += Q*move
                if expiration.weekday() == 4:
                    total -= Q*min(D("0.00015")*dec(s),move/8)
            return total
        value = sum(intrinsic(s) for s in spots)/D(60)
        forecast = receipt["forecast"]
        check(abs(value-dec(forecast["forecast_net_proceeds"]))<D("0.0001"), "FORECAST_MISMATCH")
        selected = value>=D("1.20")*one_tick
        check(bool(forecast["selected"]) == selected, "P1_SELECTION_MISMATCH")
        check((state == "SIMULATED_ENTRY_SELECTED")==selected and receipt["control_selected"] is True,
              "P1_C0_STATUS_MISMATCH")
        check(forecast["input_dates"] == [d.isoformat() for d in dates],
              "FORECAST_DATE_LEAKAGE")
        return dict(status="FORWARD_DECISION_AUDITED_NOT_PROFIT",date=day.isoformat(),P1_selected=selected,
                    C0_selected=True,expiry=expiration.isoformat(),premium_usdc=str(premium),
                    one_tick_risk_usdc=str(one_tick),immediate_friction_pct=str(friction_pct),
                    forecast_net_proceeds_usdc=str(value),raw_responses_verified=6,
                    simulated=True,edge_proven=False)

if __name__ == "__main__":
    parser=argparse.ArgumentParser()
    parser.add_argument("--archive",required=True)
    parser.add_argument("--sha256",required=True)
    parser.add_argument("--date",required=True)
    args=parser.parse_args()
    print(json.dumps(audit_entry(args.archive,args.sha256,args.date),sort_keys=True))
