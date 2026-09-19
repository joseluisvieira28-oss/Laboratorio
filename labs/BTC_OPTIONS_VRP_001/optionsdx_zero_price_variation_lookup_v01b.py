#!/usr/bin/env python3
"""Public optionsDX variation-price lookup.

Procurement metadata only. It never adds to cart, checks out, creates an
account, downloads a paid product, or opens strategy outcomes.
"""
from __future__ import annotations

import html.parser
import itertools
import json
import time
import urllib.parse
import urllib.request

PRODUCT_URL = "https://www.optionsdx.com/product/btc-option-chains/"
AJAX_URL = "https://www.optionsdx.com/?wc-ajax=get_variation"
PRODUCT_ID = "1527"
MAX_LOOKUPS = 250
PACE_SECONDS = 0.12


class SelectParser(html.parser.HTMLParser):
    def __init__(self):
        super().__init__()
        self.current_name = None
        self.selects: dict[str, list[str]] = {}

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag.lower() == "select":
            name = attrs.get("name")
            if name and str(name).startswith("attribute_"):
                self.current_name = str(name)
                self.selects.setdefault(self.current_name, [])
        elif tag.lower() == "option" and self.current_name:
            value = attrs.get("value")
            if value:
                self.selects[self.current_name].append(str(value))

    def handle_endtag(self, tag):
        if tag.lower() == "select":
            self.current_name = None


def get_text(url: str) -> str:
    req = urllib.request.Request(
        url,
        headers={"User-Agent": "CryptoLab-ProcurementMetadata/0.1"},
        method="GET",
    )
    with urllib.request.urlopen(req, timeout=45) as r:
        return r.read().decode("utf-8", "replace")


def post_form(url: str, fields: dict[str, str]) -> dict:
    data = urllib.parse.urlencode(fields).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=data,
        headers={
            "User-Agent": "CryptoLab-ProcurementMetadata/0.1",
            "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
            "X-Requested-With": "XMLHttpRequest",
            "Referer": PRODUCT_URL,
        },
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=45) as r:
        raw = r.read()
    return json.loads(raw.decode("utf-8", "replace"))


def main() -> int:
    receipt = {
        "probe_id": "OVRP-OPTIONSDX-ZERO-PRICE-CATALOG-001-V0.1B",
        "cash_spend_usd": 0,
        "cart_used": False,
        "checkout_used": False,
        "account_created": False,
        "order_created": False,
        "paid_download_used": False,
    }

    try:
        page = get_text(PRODUCT_URL)
    except Exception as exc:
        receipt.update(
            classification="OPTIONSDX_CATALOG_ACQUISITION_FAILURE",
            error=f"product_page:{type(exc).__name__}:{str(exc)[:300]}",
        )
        _write(receipt)
        return 2

    parser = SelectParser()
    parser.feed(page)
    selectors = {
        name: sorted(set(values))
        for name, values in parser.selects.items()
        if values
    }
    receipt["selector_names"] = sorted(selectors)
    receipt["selector_value_counts"] = {
        k: len(v) for k, v in sorted(selectors.items())
    }

    # Exact BTC product is expected to have two public selectors:
    # period and quote frequency. Do not invent attributes if the page changes.
    if len(selectors) < 2:
        receipt.update(
            classification="OPTIONSDX_CATALOG_METADATA_INSUFFICIENT",
            error="fewer_than_two_public_variation_selectors",
        )
        _write(receipt)
        return 2

    names = sorted(selectors)
    combinations = list(itertools.product(*(selectors[n] for n in names)))
    receipt["visible_selector_cross_product"] = len(combinations)
    if len(combinations) > MAX_LOOKUPS:
        receipt.update(
            classification="OPTIONSDX_CATALOG_METADATA_INSUFFICIENT",
            error=f"visible_cross_product_exceeds_cap:{len(combinations)}>{MAX_LOOKUPS}",
        )
        _write(receipt)
        return 2

    queried = 0
    resolved = 0
    zero_rows = []
    distinct_prices = set()
    unresolved = 0
    errors = []

    for combo in combinations:
        fields = {"product_id": PRODUCT_ID}
        attrs = dict(zip(names, combo))
        fields.update(attrs)
        queried += 1
        try:
            obj = post_form(AJAX_URL, fields)
        except Exception as exc:
            errors.append(
                f"lookup:{queried}:{type(exc).__name__}:{str(exc)[:200]}"
            )
            unresolved += 1
            time.sleep(PACE_SECONDS)
            continue

        if not isinstance(obj, dict) or not obj.get("variation_id"):
            unresolved += 1
            time.sleep(PACE_SECONDS)
            continue

        price = obj.get("display_price")
        regular = obj.get("display_regular_price")
        if isinstance(price, (int, float)):
            p = float(price)
            distinct_prices.add(p)
            resolved += 1
            if p == 0.0:
                zero_rows.append(
                    {
                        "variation_id": obj.get("variation_id"),
                        "attributes": attrs,
                        "display_price": p,
                        "display_regular_price":
                            float(regular)
                            if isinstance(regular, (int, float))
                            else None,
                        "variation_is_active": obj.get("variation_is_active"),
                        "is_in_stock": obj.get("is_in_stock"),
                        "is_purchasable": obj.get("is_purchasable"),
                    }
                )
                # The frozen question is existence of an identifiable zero-price
                # variation. Stop immediately once proven.
                break
        else:
            unresolved += 1

        time.sleep(PACE_SECONDS)

    receipt.update(
        lookup_count=queried,
        resolved_price_count=resolved,
        unresolved_lookup_count=unresolved,
        distinct_display_prices=sorted(distinct_prices),
        zero_price_variation_count=len(zero_rows),
        zero_price_variations=zero_rows,
        error_count=len(errors),
        errors=errors[:20],
    )

    if zero_rows:
        receipt["classification"] = "OPTIONSDX_ZERO_PRICE_VARIATION_FOUND"
        code = 0
    elif resolved > 0 and queried == len(combinations):
        receipt["classification"] = "OPTIONSDX_NO_ZERO_PRICE_VARIATION_VISIBLE"
        code = 0
    elif resolved > 0:
        receipt["classification"] = "OPTIONSDX_CATALOG_METADATA_PARTIAL"
        code = 2
    else:
        receipt["classification"] = "OPTIONSDX_CATALOG_METADATA_INSUFFICIENT"
        code = 2

    _write(receipt)
    return code


def _write(receipt: dict) -> None:
    with open(
        "optionsdx_zero_price_variation_receipt_v01b.json",
        "w",
        encoding="utf-8",
    ) as f:
        json.dump(receipt, f, indent=2, sort_keys=True)
        f.write("\n")
    print(json.dumps(receipt, sort_keys=True))


if __name__ == "__main__":
    raise SystemExit(main())
