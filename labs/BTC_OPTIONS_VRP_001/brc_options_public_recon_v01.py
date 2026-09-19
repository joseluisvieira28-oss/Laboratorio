#!/usr/bin/env python3
from __future__ import annotations
import hashlib, json, re, urllib.request
from pathlib import Path

URLS={
 "request":"https://blockchain-research-center.com/blockchain-explorer/request-data/",
 "register":"https://blockchain-research-center.com/blockchain-explorer/register/",
 "paper":"https://www.mdpi.com/2227-9091/11/5/85",
 "code":"https://raw.githubusercontent.com/QuantLet/BitcoinOptions/master/src/brc.py",
}

def get(url):
    req=urllib.request.Request(url,headers={"User-Agent":"CryptoLab-PublicRecon/0.1"})
    with urllib.request.urlopen(req,timeout=45) as r:
        raw=r.read()
    return raw.decode("utf-8","replace"), hashlib.sha256(raw).hexdigest(), len(raw)

def has(text,*needles):
    low=text.lower()
    return all(n.lower() in low for n in needles)

def main():
    docs={}
    errors={}
    for k,u in URLS.items():
        try:
            text,sha,n=get(u)
            docs[k]={"text":text,"sha256":sha,"bytes":n}
        except Exception as e:
            errors[k]=f"{type(e).__name__}:{str(e)[:300]}"

    req=docs.get("request",{}).get("text","")
    reg=docs.get("register",{}).get("text","")
    pap=docs.get("paper",{}).get("text","")
    code=docs.get("code",{}).get("text","")

    evidence={
      "current_catalog_mentions_deribit_futures": has(req,"Deribit","BTC Futures"),
      "current_catalog_mentions_generic_deribit_lob": has(req,"Deribit LOB"),
      "registration_says_free_account": has(reg,"free account"),
      "registration_requires_accreditation": has(reg,"accredited"),
      "paper_snapshot_count_present": "8,444,664" in pap or "8444664" in pap,
      "paper_period_present": ("2021-04-01" in pap and "2022-04-01" in pap),
      "paper_says_options_and_futures": has(pap,"options and futures"),
      "paper_says_database_available_brc": has(pap,"database is available","Blockchain Research Center"),
      "code_has_deribit_orderbooks_collection": "deribit_orderbooks" in code,
      "code_has_best_bid_price": "best_bid_price" in code,
      "code_has_best_ask_price": "best_ask_price" in code,
      "code_has_underlying_price": "underlying_price" in code,
      "code_has_index_price": "index_price" in code,
      "code_has_bid_size_field_reference": bool(re.search(r"best_bid_(amount|size)|bid_amount|bid_size",code)),
      "code_has_ask_size_field_reference": bool(re.search(r"best_ask_(amount|size)|ask_amount|ask_size",code)),
    }

    historical_identity=all([
      evidence["paper_snapshot_count_present"],
      evidence["paper_period_present"],
      evidence["paper_says_options_and_futures"],
      evidence["paper_says_database_available_brc"],
      evidence["code_has_deribit_orderbooks_collection"],
      evidence["code_has_best_bid_price"],
      evidence["code_has_best_ask_price"],
    ])
    current_access_route=(evidence["registration_says_free_account"] and evidence["registration_requires_accreditation"])
    exact_current_options_catalog_confirmed=(
      "btc options" in req.lower() or "bitcoin options" in req.lower()
    )

    if historical_identity and current_access_route and exact_current_options_catalog_confirmed:
        classification="BRC_OPTIONS_CURRENT_ACCESS_CONFIRMED"
    elif historical_identity and current_access_route:
        classification="BRC_OPTIONS_PUBLISHED_ROUTE_IDENTITY_UNRESOLVED"
    else:
        classification="BRC_OPTIONS_PUBLIC_ROUTE_NOT_ESTABLISHED"

    receipt={
      "source_probe_id":"OVRP-BRC-OPTIONS-ACCESS-001",
      "classification":classification,
      "evidence":evidence,
      "source_hashes":{k:{"sha256":v["sha256"],"bytes":v["bytes"]} for k,v in docs.items()},
      "fetch_errors":errors,
      "historical_options_dataset_identity_established":historical_identity,
      "current_member_access_route_established":current_access_route,
      "exact_options_dataset_in_current_public_catalog":exact_current_options_catalog_confirmed,
      "user_identity_submitted":False,
      "account_created":False,
      "credentials_used":False,
      "cash_spend_usd":0,
      "outcomes_opened":False
    }
    Path("brc_options_public_recon_receipt_v01.json").write_text(json.dumps(receipt,indent=2,sort_keys=True)+"\n")
    print(json.dumps(receipt,sort_keys=True))
    return 0

if __name__=="__main__":
    raise SystemExit(main())
