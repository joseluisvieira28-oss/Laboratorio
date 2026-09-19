#!/usr/bin/env python3
"""Public optionsDX product-catalog metadata probe. No checkout or purchase."""
from __future__ import annotations

import html
import json
import re
import urllib.request

PRODUCT_URL = "https://www.optionsdx.com/product/btc-option-chains/"
STORE_API = "https://www.optionsdx.com/wp-json/wc/store/v1/products?slug=btc-option-chains"


def get(url: str) -> tuple[int, str, str]:
    req = urllib.request.Request(url, headers={"User-Agent":"CryptoLab-ProcurementMetadata/0.1"})
    with urllib.request.urlopen(req, timeout=45) as r:
        raw=r.read()
        return getattr(r,"status",200), r.headers.get("Content-Type",""), raw.decode("utf-8","replace")


def parse_html_variations(text: str) -> list[dict]:
    m=re.search(r'data-product_variations="([^"]+)"', text, flags=re.I|re.S)
    if not m:
        return []
    payload=html.unescape(m.group(1))
    obj=json.loads(payload)
    out=[]
    for v in obj:
        attrs=v.get("attributes") or {}
        out.append({
            "variation_id":v.get("variation_id"),
            "attributes":attrs,
            "display_price":v.get("display_price"),
            "display_regular_price":v.get("display_regular_price"),
            "is_in_stock":v.get("is_in_stock"),
            "is_purchasable":v.get("is_purchasable"),
        })
    return out


def parse_store_api(text: str) -> list[dict]:
    data=json.loads(text)
    if not isinstance(data,list) or not data:
        return []
    p=data[0]
    out=[]
    # Woo Store API may expose variations as IDs only; retain only public metadata.
    for v in p.get("variations") or []:
        if isinstance(v,dict):
            out.append(v)
        else:
            out.append({"variation_id":v})
    return out


def main() -> int:
    result={
        "probe_id":"OVRP-OPTIONSDX-ZERO-PRICE-CATALOG-001",
        "product_url":PRODUCT_URL,
        "cash_spend_usd":0,
        "cart_or_checkout_used":False,
    }
    variations=[]
    errors=[]
    try:
        status,ctype,text=get(PRODUCT_URL)
        result["product_http_status"]=status
        result["product_content_type"]=ctype
        variations=parse_html_variations(text)
        result["html_variation_count"]=len(variations)
    except Exception as exc:
        errors.append(f"html:{type(exc).__name__}:{str(exc)[:300]}")

    if not variations:
        try:
            status,ctype,text=get(STORE_API)
            result["store_api_http_status"]=status
            result["store_api_content_type"]=ctype
            variations=parse_store_api(text)
            result["store_api_variation_count"]=len(variations)
        except Exception as exc:
            errors.append(f"store_api:{type(exc).__name__}:{str(exc)[:300]}")

    cleaned=[]
    zero=[]
    prices=set()
    for v in variations:
        # Keep only non-sensitive public procurement metadata.
        row={
            "variation_id":v.get("variation_id") or v.get("id"),
            "attributes":v.get("attributes") or {},
            "display_price":v.get("display_price"),
            "display_regular_price":v.get("display_regular_price"),
            "is_in_stock":v.get("is_in_stock"),
            "is_purchasable":v.get("is_purchasable"),
        }
        cleaned.append(row)
        price=row["display_price"]
        if isinstance(price,(int,float)):
            prices.add(float(price))
            if float(price)==0.0:
                zero.append(row)

    result["variation_count"]=len(cleaned)
    result["distinct_display_prices"]=sorted(prices)
    result["zero_price_variation_count"]=len(zero)
    result["zero_price_variations"]=zero
    result["errors"]=errors

    if zero:
        result["classification"]="OPTIONSDX_ZERO_PRICE_VARIATION_FOUND"
        code=0
    elif cleaned:
        result["classification"]="OPTIONSDX_NO_ZERO_PRICE_VARIATION_VISIBLE"
        code=0
    elif errors:
        result["classification"]="OPTIONSDX_CATALOG_ACQUISITION_FAILURE"
        code=2
    else:
        result["classification"]="OPTIONSDX_CATALOG_METADATA_INSUFFICIENT"
        code=2

    with open("optionsdx_zero_price_catalog_receipt_v01.json","w",encoding="utf-8") as f:
        json.dump(result,f,indent=2,sort_keys=True)
        f.write("\n")
    print(json.dumps(result,sort_keys=True))
    return code


if __name__=="__main__":
    raise SystemExit(main())
