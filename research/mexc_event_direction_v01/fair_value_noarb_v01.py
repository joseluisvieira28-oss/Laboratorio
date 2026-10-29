#!/usr/bin/env python3
"""Two isolated public Event Futures snapshots: static UP/DOWN no-arb, NOT trade signals."""
import json,math,pathlib
OUT=pathlib.Path("artifacts/mexc_event_fair_value_v01")
ASSETS=("BTC_USDT","ETH_USDT")
def noarb(q_up,q_down):
    q_up=float(q_up);q_down=float(q_down)
    if not all(math.isfinite(q) and 0<=q<=100 for q in (q_up,q_down)):
        raise ValueError("INVALID_PAY_RATE")
    a,b=1+q_up,1+q_down
    w_up=b/(a+b);w_down=a/(a+b)
    both_return=a*b/(a+b);net=both_return-1
    assert abs(w_up+w_down-1)<1e-12
    assert abs(w_up*a-w_down*b)<1e-12
    return {"q_up":q_up,"q_down":q_down,
            "up_stake_fraction":w_up,"down_stake_fraction":w_down,
            "two_sided_net_per_total_stake_no_tie":net,
            "synthetic_state_price_sum":1/a+1/b,
            "up_break_even_probability":1/a,"down_break_even_probability":1/b,
            "classification":"POTENTIAL_TWO_SIDED_MATH_ONLY" if net>1e-12 else "NO_STATIC_TWO_SIDED_ARBITRAGE"}
def tests():
    assert abs(noarb(.7,.7)["two_sided_net_per_total_stake_no_tie"]+.15)<1e-12
    assert abs(noarb(.8,.8)["two_sided_net_per_total_stake_no_tie"]+.1)<1e-12
    assert noarb(1.2,1.2)["classification"]=="POTENTIAL_TWO_SIDED_MATH_ONLY"
    assert abs(noarb(1.,1.)["two_sided_net_per_total_stake_no_tie"])<1e-12
    assert noarb(.4,.7)["classification"]=="NO_STATIC_TWO_SIDED_ARBITRAGE"
    for up,down in [(-1,.7),(float("nan"),.7)]:
        try:noarb(up,down);raise AssertionError("BAD_RATE_ACCEPTED")
        except ValueError:pass
def read(path):
    j=json.loads(path.read_text())
    if j.get("verdict")!="PROSPECTIVE_SNAPSHOT_PASS":
        raise ValueError("SOURCE_COLLECTOR_BLOCKED")
    safety=j.get("safety") or {}
    for key in ("authenticated_requests","orders","account_mutations","private_routes_called","transmitted_non_gets"):
        if safety.get(key)!=0:raise ValueError("UNSAFE_COLLECTOR_STATE_"+key)
    d=j.get("detail_capture") or {}
    if d.get("status")!=200 or not d.get("sha256") or not d.get("received_at_utc"):
        raise ValueError("MISSING_VALID_CAPTURE")
    return j
def rows(j):
    data={}
    for row in j.get("rows") or []:
        sym=row.get("symbol")
        if sym not in ASSETS or row.get("cycle_unit")!="MINUTE" or row.get("cycle_value")!=10:
            continue
        if sym in data:raise ValueError("DUPLICATE_TEN_MINUTE_SYMBOL_"+sym)
        if row.get("up_pay_rate") is None or row.get("down_pay_rate") is None:
            raise ValueError("MISSING_PAY_RATE_"+sym)
        data[sym]={"symbol":sym,"product_state":row.get("product_state"),
                   "contract_id":row.get("contract_id"),
                   **noarb(row["up_pay_rate"],row["down_pay_rate"])}
    if set(data)!=set(ASSETS):raise ValueError("MISSING_BTC_ETH_TEN_MINUTE")
    return data
def main():
    tests()
    OUT.mkdir(exist_ok=True,parents=True)
    report={"lab":"EVENT10M_FAIR_VALUE_STATIC_NOARB_V01",
      "scope":["BTC_USDT_10MIN","ETH_USDT_10MIN"],"NVIDIA_excluded":True,
      "trade_actions":0,"private_calls":0,"price_outcomes_opened":0,
      "protected_september_holdout_opened":False,
      "market_probability_model_available":False,
      "historical_payout_history_available":False,
      "event_order_entry_settle_parity_proven":False,
      "real_execution_costs_verified":False,
      "snapshots":[],"gate":"SOURCE_BLOCKED","execution_edge_certified":False}
    try:
        for n in (1,2):
            j=read(OUT/("public_snapshot_%d.json"%n))
            d=j["detail_capture"]
            report["snapshots"].append({"sample":n,"captured_at_utc":d["received_at_utc"],
                "source_url":d.get("url"),"source_sha256":d["sha256"],
                "products":rows(j)})
        rates=[p for s in report["snapshots"] for p in s["products"].values()]
        report["all_online"]=all(p["product_state"]=="ONLINE" for p in rates)
        report["potential_math_pairs"]=[{"sample":s["sample"],"symbol":p["symbol"]}
           for s in report["snapshots"] for p in s["products"].values()
           if p["classification"]=="POTENTIAL_TWO_SIDED_MATH_ONLY"]
        report["gate"]="STATIC_MATH_POTENTIAL_NOT_EXECUTION_PROVEN" if report["potential_math_pairs"] else "NO_STATIC_TWO_SIDED_ARBITRAGE_AT_OBSERVED_PAYOUTS"
    except Exception as e:
        report["failure"]=type(e).__name__+":"+str(e)[:200]
        report["gate"]="SOURCE_BLOCKED"
    finally:
        (OUT/"fair_value_receipt.json").write_text(json.dumps(report,indent=2,sort_keys=True)+"\n")
        print(json.dumps(report,indent=2,sort_keys=True),flush=True)
    if report["gate"]=="SOURCE_BLOCKED":raise SystemExit(2)
if __name__=="__main__":main()
