#!/usr/bin/env python3
"""Public optionsDX product-catalog metadata probe. No checkout or purchase."""
from __future__ import annotations

import html
import json
import re
import urllib.parse
import urllib.request

PRODUCT_URL = "https://www.optionsdx.com/product/btc-option-chains/"
STORE_PRODUCTS_API = "https://www.optionsdx.com/wp-json/wc/store/v1/products?slug=btc-option-chains"
STORE_BASE = "https://www.optionsdx.com/wp-json/wc/store/v1"


def get(url: str) -> tuple[int, str, str]:
    req = urllib.request.Request(
        url,
        headers={"User-Agent": "CryptoLab-ProcurementMetadata/0.1"},
        method="GET",
    )
    with urllib.request.urlopen(req, timeout=45) as r:
        raw = r.read()
        return (
            getattr(r, "status", 200),
            r.headers.get("Content-Type", ""),
            raw.decode("utf-8", "replace"),
        )


def parse_html_variations(text: str) -> list[dict]:
    m = re.search(r'data-product_variations="([^"]+)"', text, flags=re.I | re.S)
    if not m:
        return []
    payload = html.unescape(m.group(1))
    obj = json.loads(payload)
    if not isinstance(obj, list):
        return []
    out = []
    for v in obj:
        attrs = v.get("attributes") or {}
        out.append(
            {
                "variation_id": v.get("variation_id"),
                "attributes": attrs,
                "display_price": v.get("display_price"),
                "display_regular_price": v.get("display_regular_price"),
                "is_in_stock": v.get("is_in_stock"),
                "is_purchasable": v.get("is_purchasable"),
                "price_source": "html_variation_payload",
            }
        )
    return out


def attr_map(attrs) -> dict:
    if isinstance(attrs, dict):
        return attrs
    out = {}
    if isinstance(attrs, list):
        for a in attrs:
            if not isinstance(a, dict):
                continue
            name = a.get("name") or a.get("attribute") or a.get("slug")
            value = a.get("value") or a.get("term") or a.get("option")
            if name is not None:
                out[str(name)] = value
    return out


def wc_price(v: dict) -> tuple[float | None, float | None]:
    prices = v.get("prices")
    if not isinstance(prices, dict):
        direct = v.get("display_price")
        regular = v.get("display_regular_price")
        return (
            float(direct) if isinstance(direct, (int, float)) else None,
            float(regular) if isinstance(regular, (int, float)) else None,
        )

    minor = prices.get("currency_minor_unit", 2)
    try:
        divisor = 10 ** int(minor)
    except Exception:
        divisor = 100

    def dec(x):
        if x is None or x == "":
            return None
        try:
            return int(str(x)) / divisor
        except Exception:
            try:
                return float(x)
            except Exception:
                return None

    return dec(prices.get("price")), dec(prices.get("regular_price"))


def parse_product_record(text: str) -> tuple[int | None, list]:
    data = json.loads(text)
    if not isinstance(data, list) or not data:
        return None, []
    p = data[0]
    return p.get("id"), p.get("variations") or []


def fetch_variation_details(product_id: int) -> tuple[list[dict], list[str]]:
    rows: list[dict] = []
    errors: list[str] = []
    for page in range(1, 6):
        q = urllib.parse.urlencode({"per_page": 100, "page": page})
        url = f"{STORE_BASE}/products/{product_id}/variations?{q}"
        try:
            status, ctype, text = get(url)
            obj = json.loads(text)
            if not isinstance(obj, list):
                errors.append(f"variation_page_{page}:non_list_json")
                break
            if not obj:
                break
            for v in obj:
                if not isinstance(v, dict):
                    continue
                price, regular = wc_price(v)
                rows.append(
                    {
                        "variation_id": v.get("id") or v.get("variation_id"),
                        "attributes": attr_map(v.get("attributes") or {}),
                        "display_price": price,
                        "display_regular_price": regular,
                        "is_in_stock": v.get("is_in_stock"),
                        "is_purchasable": v.get("is_purchasable"),
                        "price_source": "wc_store_variation_detail",
                    }
                )
            if len(obj) < 100:
                break
        except Exception as exc:
            errors.append(
                f"variation_page_{page}:{type(exc).__name__}:{str(exc)[:300]}"
            )
            break
    return rows, errors


def main() -> int:
    result = {
        "probe_id": "OVRP-OPTIONSDX-ZERO-PRICE-CATALOG-001",
        "product_url": PRODUCT_URL,
        "cash_spend_usd": 0,
        "cart_or_checkout_used": False,
        "account_created": False,
    }
    variations: list[dict] = []
    errors: list[str] = []
    product_id = None
    product_level_variation_count = 0

    try:
        status, ctype, text = get(PRODUCT_URL)
        result["product_http_status"] = status
        result["product_content_type"] = ctype
        try:
            variations = parse_html_variations(text)
            result["html_variation_count"] = len(variations)
        except Exception as exc:
            errors.append(f"html_parse:{type(exc).__name__}:{str(exc)[:300]}")
    except Exception as exc:
        errors.append(f"html_transport:{type(exc).__name__}:{str(exc)[:300]}")

    # If HTML did not expose fully priced variation metadata, use only the
    # public read-only Woo Store API. No cart or checkout endpoint is touched.
    if not variations or not any(
        isinstance(v.get("display_price"), (int, float)) for v in variations
    ):
        try:
            status, ctype, text = get(STORE_PRODUCTS_API)
            result["store_api_http_status"] = status
            result["store_api_content_type"] = ctype
            product_id, ids = parse_product_record(text)
            result["store_product_id"] = product_id
            product_level_variation_count = len(ids)
            result["store_product_variation_reference_count"] = len(ids)
            if product_id is not None:
                detail_rows, detail_errors = fetch_variation_details(int(product_id))
                errors.extend(detail_errors)
                if detail_rows:
                    variations = detail_rows
        except Exception as exc:
            errors.append(f"store_api:{type(exc).__name__}:{str(exc)[:300]}")

    cleaned = []
    zero = []
    prices = set()
    priced_rows = 0
    for v in variations:
        row = {
            "variation_id": v.get("variation_id") or v.get("id"),
            "attributes": v.get("attributes") or {},
            "display_price": v.get("display_price"),
            "display_regular_price": v.get("display_regular_price"),
            "is_in_stock": v.get("is_in_stock"),
            "is_purchasable": v.get("is_purchasable"),
            "price_source": v.get("price_source"),
        }
        cleaned.append(row)
        price = row["display_price"]
        if isinstance(price, (int, float)):
            priced_rows += 1
            prices.add(float(price))
            if float(price) == 0.0:
                zero.append(row)

    result["product_level_variation_reference_count"] = product_level_variation_count
    result["variation_detail_count"] = len(cleaned)
    result["priced_variation_count"] = priced_rows
    result["distinct_display_prices"] = sorted(prices)
    result["zero_price_variation_count"] = len(zero)
    result["zero_price_variations"] = zero
    result["errors"] = errors

    if zero:
        result["classification"] = "OPTIONSDX_ZERO_PRICE_VARIATION_FOUND"
        code = 0
    elif priced_rows > 0:
        result["classification"] = "OPTIONSDX_NO_ZERO_PRICE_VARIATION_VISIBLE"
        code = 0
    elif errors and product_id is None:
        result["classification"] = "OPTIONSDX_CATALOG_ACQUISITION_FAILURE"
        code = 2
    else:
        result["classification"] = "OPTIONSDX_CATALOG_METADATA_INSUFFICIENT"
        code = 2

    with open(
        "optionsdx_zero_price_catalog_receipt_v01.json", "w", encoding="utf-8"
    ) as f:
        json.dump(result, f, indent=2, sort_keys=True)
        f.write("\n")
    print(json.dumps(result, sort_keys=True))
    return code


if __name__ == "__main__":
    raise SystemExit(main())
