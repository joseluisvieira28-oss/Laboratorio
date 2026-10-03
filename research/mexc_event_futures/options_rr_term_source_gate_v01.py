#!/usr/bin/env python3
"""OPTIONS-RR-TERM-FWD-001 public source gate. Zero outcomes."""
import argparse, concurrent.futures, json, math, time
from priority_source_gates_v013 import Evidence, get, positive, valid_ticker

BUCKETS={
    "SHORT":(7*86400000,21*86400000),
    "MEDIUM":(35*86400000,70*86400000),
}
CURRENCIES=("BTC","ETH")

def approx_delta(meta, summary, recv):
    f=summary.get("underlying_price"); iv=summary.get("mark_iv")
    if not positive(f) or not positive(iv):
        return None
    expiry=meta["expiration_timestamp"]
    tau=(expiry-recv)/(365.25*86400000)
    if tau<=0: return None
    vol=iv/100
    if vol<=0:return None
    if meta["option_type"]=="call" and meta["strike"]<=f:return None
    if meta["option_type"]=="put" and meta["strike"]>=f:return None
    d1=(math.log(f/meta["strike"])+.5*vol*vol*tau)/(vol*math.sqrt(tau))
    nd1=.5*(1+math.erf(d1/math.sqrt(2)))
    return nd1 if meta["option_type"]=="call" else nd1-1

def choose_expiry(instruments,recv,lo,hi):
    ex=sorted({m["expiration_timestamp"] for m in instruments
               if m.get("is_active") is True and m.get("kind")=="option"
               and lo <= m["expiration_timestamp"]-recv <= hi})
    if not ex:
        raise ValueError("NO_ELIGIBLE_EXPIRY")
    return ex[0]

def fetch_pair(currency,bucket,expiry,instruments,summaries,recv,evidence,round_id,meta_sha,sum_sha):
    eligible=[m for m in instruments if m.get("is_active") is True
              and m.get("kind")=="option" and m.get("base_currency")==currency
              and m.get("expiration_timestamp")==expiry]
    choices=[]
    for side in ("call","put"):
        scored=[]
        for m in eligible:
            if m.get("option_type")!=side: continue
            s=summaries.get(m["instrument_name"],{})
            d=approx_delta(m,s,recv)
            if d is None: continue
            scored.append((abs(abs(d)-.25),m["instrument_name"],m))
        for _,_,m in sorted(scored)[:2]:
            choices.append(m)
    if len(choices)<2:
        raise ValueError(f"{bucket}_INSUFFICIENT_CANDIDATES")

    candidates=[]
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
        futs={pool.submit(get,"ticker",{"instrument_name":m["instrument_name"]},evidence,
                          f"rrterm-{round_id}-{currency}-{bucket}-{m['instrument_name']}-ticker.json"):m
              for m in choices}
        for fut,m in futs.items():
            t,received,ref=fut.result()
            candidates.append({
                "instrument":m["instrument_name"],
                "option_type":m["option_type"],
                "valid":valid_ticker(t,m,received),
                "ticker":t,
                "received_at_ms":received,
                "raw_sha256":ref["sha256"],
                "metadata_sha256":meta_sha,
                "selection_summary_sha256":sum_sha,
            })

    pair=[]
    for side in ("call","put"):
        valid=[r for r in candidates if r["valid"] and r["option_type"]==side]
        if not valid:
            raise ValueError(f"{bucket}_{side.upper()}_NO_VALID_TICKER")
        pair.append(min(valid,key=lambda r:(abs(abs(r["ticker"]["greeks"]["delta"])-.25),r["instrument"])))
    spread=abs(pair[0]["ticker"]["timestamp"]-pair[1]["ticker"]["timestamp"])
    if spread>5000:
        raise ValueError(f"{bucket}_PAIR_TIMESTAMP_SPREAD")
    by={r["option_type"]:r for r in pair}
    skew=float(by["put"]["ticker"]["mark_iv"])-float(by["call"]["ticker"]["mark_iv"])
    return {
        "bucket":bucket,
        "expiry_ms":expiry,
        "dte_days_at_metadata":(expiry-recv)/86400000,
        "selected_pair":pair,
        "timestamp_spread_ms":spread,
        "rr_skew_pp":skew,
    }

def one_currency(currency,evidence,round_id):
    instruments,recv,meta_ref=get("get_instruments",
        {"currency":currency,"kind":"option","expired":"false"},evidence,
        f"rrterm-{round_id}-{currency}-instruments.json")
    instruments=[m for m in instruments if m.get("base_currency")==currency]
    summary,_,sum_ref=get("get_book_summary_by_currency",
        {"currency":currency,"kind":"option"},evidence,
        f"rrterm-{round_id}-{currency}-summary.json")
    summaries={r["instrument_name"]:r for r in summary}
    expiries={}
    pairs={}
    for bucket,(lo,hi) in BUCKETS.items():
        expiry=choose_expiry(instruments,recv,lo,hi)
        expiries[bucket]=expiry
        pairs[bucket]=fetch_pair(currency,bucket,expiry,instruments,summaries,recv,evidence,
                                 round_id,meta_ref["sha256"],sum_ref["sha256"])
    if expiries["SHORT"]==expiries["MEDIUM"]:
        raise ValueError("BUCKET_EXPIRY_COLLISION")
    stamps=[x["ticker"]["timestamp"] for b in pairs.values() for x in b["selected_pair"]]
    cross=max(stamps)-min(stamps)
    if cross>10000:
        raise ValueError("CROSS_EXPIRY_TIMESTAMP_SPREAD")
    rr_term=pairs["SHORT"]["rr_skew_pp"]-pairs["MEDIUM"]["rr_skew_pp"]
    return {
        "currency":currency,
        "metadata_received_at_ms":recv,
        "short":pairs["SHORT"],
        "medium":pairs["MEDIUM"],
        "cross_expiry_timestamp_spread_ms":cross,
        "rr_term_pp":rr_term,
    }

def main(output):
    ev=Evidence(output)
    rounds=[];errors=[]
    for rid in range(1,4):
        accepted={}
        for currency in CURRENCIES:
            try:
                accepted[currency]=one_currency(currency,ev,rid)
            except Exception as exc:
                errors.append({"round":rid,"currency":currency,"type":type(exc).__name__,"error":str(exc)})
                accepted[currency]={"currency":currency,"passed":False}
        round_pass=all(c in accepted and accepted[c].get("rr_term_pp") is not None for c in CURRENCIES)
        rounds.append({"round":rid,"passed":round_pass,"accepted":accepted})
        if rid<3: time.sleep(5)

    btc_pass=sum(1 for r in rounds if r["accepted"].get("BTC",{}).get("rr_term_pp") is not None)
    eth_pass=sum(1 for r in rounds if r["accepted"].get("ETH",{}).get("rr_term_pp") is not None)
    if btc_pass==3 and eth_pass==3 and not errors:
        verdict="SOURCE_GATE_PASS"
    elif btc_pass or eth_pass:
        verdict="PARTIAL_SOURCE"
    else:
        verdict="SOURCE_BLOCKED"
    receipt={
        "family_id":"OPTIONS-RR-TERM-FWD-001",
        "family_version":"0.1-source-gate",
        "verdict":verdict,
        "rounds":rounds,
        "errors":errors,
        "btc_pass_rounds":btc_pass,
        "eth_pass_rounds":eth_pass,
        "price_outcomes_opened":0,
        "event_futures_outcomes_opened":0,
        "mexc_accessed":False,
        "directional_statistics_run":False,
    }
    ev.finish(receipt)
    if verdict=="SOURCE_BLOCKED":
        raise SystemExit(2)

if __name__=="__main__":
    ap=argparse.ArgumentParser()
    ap.add_argument("--output",required=True)
    a=ap.parse_args()
    main(a.output)
