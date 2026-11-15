"""Independent frozen Deribit V2 settlement audit (no market calls, no probe import).

Checks original archived entry and official settlement source raw SHA, timestamps,
European terminal payoff, venue fees, stress and same-quote P1/C0 accounting.
This verifies one simulated outcome, NEVER proves positive expected value.
"""
import argparse
import datetime as dt
from decimal import Decimal as D
import hashlib
import json
from pathlib import Path
import zipfile
import audit_forward as independent

Q = D(".01")
ELIGIBLE = {"SIMULATED_ENTRY_SELECTED", "ABSTAIN_FORECAST"}

def require(ok, code):
    if not ok:
        raise ValueError(code)

def approx(observed, expected, label):
    require(abs(independent.dec(observed) - expected) <= D(".000001"), "SETTLEMENT_MISMATCH_"+label)

def load(z, name):
    return json.loads(z.read(name))

def payoff(legs, terminal, expiry):
    gross = D(0)
    delivery = D(0)
    for leg in legs:
        k = independent.dec(leg["meta"]["strike"])
        intrinsic = max(D(0), terminal-k) if leg["meta"]["option_type"]=="call" else max(D(0),k-terminal)
        gross += Q * intrinsic
        if expiry.weekday() == 4:
            delivery += Q * min(D(".00015")*terminal, intrinsic/D(8))
    return gross, delivery

def entry_legs(z, entry):
    raw = lambda key: load(z, "raw/"+key+".json")["result"]
    metas = {v["instrument_name"]:v for v in raw("instruments")}
    legs = []
    for side in ("atm_call","atm_put"):
        b=raw(side); m=metas[entry["chosen"][side]]
        require(b["instrument_name"]==m["instrument_name"], "CONTRACT_MISMATCH")
        legs.append(dict(meta=m,ask=min(independent.dec(v) for v,q in b["asks"]),
                         index=independent.dec(b["index_price"])))
    return legs

def entry_cost(legs, ticks, factor):
    result=D(0)
    for leg in legs:
        price=leg["ask"]
        for _ in range(ticks):
            price=independent.next_price(price,leg["meta"])
        result+=Q*price+factor*independent.fee(price,leg["index"])
    return result

def audit(entry_zip, entry_archive_sha, settlement_zip, settlement_archive_sha, day):
    # Integrity and causal source/decision validation before reading ANY terminal outcome.
    forward=independent.audit_entry(entry_zip,entry_archive_sha,day)
    require(forward["status"]=="FORWARD_DECISION_AUDITED_NOT_PROFIT", "UNSETTLEABLE_ENTRY")
    entry_bytes=Path(entry_zip).read_bytes()
    settle_bytes=Path(settlement_zip).read_bytes()
    require(hashlib.sha256(entry_bytes).hexdigest()==entry_archive_sha,"ENTRY_ARCHIVE_HASH_MISMATCH")
    require(hashlib.sha256(settle_bytes).hexdigest()==settlement_archive_sha,"SETTLEMENT_ARCHIVE_HASH_MISMATCH")
    with zipfile.ZipFile(entry_zip) as ez, zipfile.ZipFile(settlement_zip) as sz:
        entry_bytes=ez.read("raw/receipt.json")
        entry=load(ez,"raw/receipt.json")
        receipt=load(sz,"raw/receipt.json")
        require(receipt.get("entry_sha256")==hashlib.sha256(entry_bytes).hexdigest(), "ENTRY_RECEIPT_HASH_MISMATCH")
        require(receipt.get("freeze")==independent.FREEZE and receipt.get("simulation") is True, "FREEZE_OR_MODE_MISMATCH")
        require(receipt.get("status") in {"UNSETTLED","OFFICIAL_DELIVERY_SIMULATED_PNL"},"SETTLEMENT_STATUS")
        manifest=load(sz,"raw/manifest.json")
        require(manifest==receipt.get("manifest"),"SETTLEMENT_MANIFEST_MISMATCH")
        require(len(manifest)==1 and manifest[0].get("name")=="settlement","SETTLEMENT_SOURCE_COUNT")
        source=manifest[0]
        require(source.get("url","").startswith("https://www.deribit.com/api/v2/public/get_delivery_prices?"),
                "NOT_OFFICIAL_DELIVERY_ENDPOINT")
        require("index_name=btc_usdc" in source["url"], "WRONG_DELIVERY_INDEX")
        expiry=independent.instant(entry["expiry"])
        requested_at=independent.instant(source["started"])
        require(requested_at>expiry,"FUTURE_INFORMATION_LEAK")
        if "sha256" not in source:
            require("error" in source and receipt["status"]=="UNSETTLED","MISSING_SOURCE_HASH")
            require("terminal" not in receipt and "primary_net" not in receipt,"UNSETTLED_HAS_PNL")
            return dict(status="UNSETTLED",reason="SOURCE_FAILURE",edge_proven=False)
        body=sz.read("raw/settlement.json")
        require(hashlib.sha256(body).hexdigest()==source["sha256"],"SETTLEMENT_RAW_HASH_MISMATCH")
        response=json.loads(body)
        require(response.get("testnet") is False and "error" not in response,"NOT_REAL_PUBLIC_SOURCE")
        vals=[independent.dec(v["delivery_price"]) for v in response["result"]["data"]
              if v["date"]==expiry.date().isoformat()]
        if len(vals)!=1:
            require(receipt["status"]=="UNSETTLED","MISSING_DELIVERY_CANNOT_PRODUCE_PNL")
            require("terminal" not in receipt and "primary_net" not in receipt,"UNSETTLED_HAS_PNL")
            return dict(status="UNSETTLED",reason="NO_UNIQUE_OFFICIAL_PRICE",edge_proven=False)
        require(receipt["status"]=="OFFICIAL_DELIVERY_SIMULATED_PNL","OFFICIAL_PRICE_NOT_SETTLED")
        terminal=vals[0]
        require(terminal>0,"BAD_DELIVERY_PRICE")
        legs=entry_legs(ez,entry)
        gross,delivery=payoff(legs,terminal,expiry)
        risk=entry_cost(legs,1,D(1))
        stressed=entry_cost(legs,2,D("1.5"))
        control=gross-delivery-risk
        chosen=bool(forward["P1_selected"])
        primary=control if chosen else D(0)
        stress=gross-delivery-stressed if chosen else D(0)
        for key,value in (("terminal",terminal),("risk",risk),("gross",gross),
                          ("delivery",delivery),("control_net",control),
                          ("primary_net",primary),("stress_net",stress)):
            approx(receipt[key],value,key)
        return dict(status="OFFICIAL_SETTLEMENT_INDEPENDENTLY_AUDITED_NOT_EDGE",
                    date=day,expiry=expiry.isoformat(),terminal=str(terminal),
                    P1_selected=chosen,C0_selected=True,P1_net_usdc=str(primary),
                    C0_net_usdc=str(control),P1_minus_C0_usdc=str(primary-control),
                    P1_stress_usdc=str(stress),risk_usdc=str(risk),
                    gross_usdc=str(gross),delivery_fee_usdc=str(delivery),
                    entry_archive_sha256=entry_archive_sha,
                    settlement_archive_sha256=settlement_archive_sha,
                    simulation=True,edge_proven=False)

if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--entry-archive",required=True)
    p.add_argument("--entry-sha256",required=True)
    p.add_argument("--settlement-archive",required=True)
    p.add_argument("--settlement-sha256",required=True)
    p.add_argument("--date",required=True)
    a=p.parse_args()
    print(json.dumps(audit(a.entry_archive,a.entry_sha256,a.settlement_archive,a.settlement_sha256,a.date),sort_keys=True))
