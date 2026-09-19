#!/usr/bin/env python3
"""Exact zero-price optionsDX variation direct-file precheck.

No cart, checkout, account, order or paid download is touched.
"""
from __future__ import annotations

import json
import re
import urllib.parse
import urllib.request
from urllib.parse import urlsplit, urlunsplit

PRODUCT_URL = "https://www.optionsdx.com/product/btc-option-chains/"
AJAX_URL = "https://www.optionsdx.com/?wc-ajax=get_variation"
FIELDS = {
    "product_id": "1527",
    "attribute_period": "2021-06",
    "attribute_quote-frequency": "End of Day",
}


def public_variation() -> dict:
    data=urllib.parse.urlencode(FIELDS).encode("utf-8")
    req=urllib.request.Request(
        AJAX_URL,
        data=data,
        method="POST",
        headers={
            "User-Agent":"CryptoLab-ZeroCashSourcePrecheck/0.1",
            "Content-Type":"application/x-www-form-urlencoded; charset=UTF-8",
            "X-Requested-With":"XMLHttpRequest",
            "Referer":PRODUCT_URL,
        },
    )
    with urllib.request.urlopen(req,timeout=45) as r:
        return json.loads(r.read().decode("utf-8","replace"))


def safe_url(u: str) -> str:
    try:
        s=urlsplit(u)
        return urlunsplit((s.scheme,s.netloc,s.path,"",""))
    except Exception:
        return ""


def walk(obj, path="$"):
    if isinstance(obj,dict):
        for k,v in obj.items():
            yield from walk(v,f"{path}.{k}")
    elif isinstance(obj,list):
        for i,v in enumerate(obj):
            yield from walk(v,f"{path}[{i}]")
    elif isinstance(obj,str):
        yield path,obj


def main() -> int:
    receipt={
        "source_mve_id":"OVRP-OPTIONSDX-FREE-EOD-2021-06-001-SOURCE",
        "cash_spend_usd":0,
        "cart_used":False,
        "checkout_used":False,
        "account_created":False,
        "order_created":False,
        "user_identity_submitted":False,
    }
    try:
        obj=public_variation()
    except Exception as exc:
        receipt["classification"]="ZERO_PRICE_VARIATION_METADATA_ACQUISITION_FAILURE"
        receipt["error"]=f"{type(exc).__name__}:{str(exc)[:300]}"
        _write(receipt)
        return 2

    receipt["variation_id"]=obj.get("variation_id")
    receipt["display_price"]=obj.get("display_price")
    receipt["display_regular_price"]=obj.get("display_regular_price")
    receipt["variation_is_active"]=obj.get("variation_is_active")
    receipt["is_in_stock"]=obj.get("is_in_stock")
    receipt["is_purchasable"]=obj.get("is_purchasable")
    receipt["public_top_level_keys"]=sorted(str(k) for k in obj)

    candidates=[]
    file_ext=re.compile(r"\.(?:csv|zip|gz|parquet|7z|rar)(?:$|[?#])",re.I)
    for path,value in walk(obj):
        if value.startswith(("http://","https://")) and (
            file_ext.search(value) or "download" in path.lower()
        ):
            candidates.append({"json_path":path,"safe_url":safe_url(value)})

    receipt["public_direct_file_candidate_count"]=len(candidates)
    receipt["public_direct_file_candidates"]=candidates

    if candidates:
        receipt["classification"]="ANONYMOUS_DIRECT_FILE_CANDIDATE_FOUND"
        code=0
    else:
        receipt["classification"]="NO_ANONYMOUS_DIRECT_FILE_IN_VARIATION_METADATA"
        code=0

    _write(receipt)
    return code


def _write(x):
    with open("optionsdx_free_eod_precheck_receipt_v01.json","w",encoding="utf-8") as f:
        json.dump(x,f,indent=2,sort_keys=True)
        f.write("\n")
    print(json.dumps(x,sort_keys=True))


if __name__=="__main__":
    raise SystemExit(main())
