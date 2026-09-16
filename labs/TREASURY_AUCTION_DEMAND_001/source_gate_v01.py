#!/usr/bin/env python3
"""TREASURY-AUCTION-DEMAND-001 / TAD-COUPON-SOURCE-001.

READ-ONLY / SOURCE-ONLY / BTC OUTCOMES FORBIDDEN.
Fetches only official U.S. Treasury auction rows whose auction_date is in 2021-2024.
"""
from __future__ import annotations

import csv
import hashlib
import json
import math
import os
import sys
from collections import Counter
from datetime import date
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any

import requests

LAB_ID = "TREASURY-AUCTION-DEMAND-001"
GATE_ID = "TAD-COUPON-SOURCE-001"
API = "https://api.fiscaldata.treasury.gov/services/api/fiscal_service/v1/accounting/od/auctions_query"
START = "2021-01-01"
END = "2024-12-31"
TERMS = ("2-Year", "3-Year", "5-Year", "7-Year", "10-Year", "20-Year", "30-Year")
REQ = (
    "auction_date", "cusip", "security_type", "original_security_term",
    "inflation_index_security", "floating_rate", "bid_to_cover_ratio",
    "comp_accepted", "primary_dealer_accepted", "direct_bidder_accepted",
    "indirect_bidder_accepted", "total_accepted", "total_tendered",
)
OUT = Path(os.environ.get("TAD_OUT_DIR", "artifacts/treasury_auction_demand_source_v01"))
PAGE_SIZE = 100


def sha256_bytes(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def canonical_json(obj: Any) -> bytes:
    return (json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False) + "\n").encode("utf-8")


def dec(v: Any) -> Decimal:
    if v is None:
        raise InvalidOperation("null")
    s = str(v).strip().replace(",", "").replace("$", "")
    if not s:
        raise InvalidOperation("empty")
    d = Decimal(s)
    if not d.is_finite():
        raise InvalidOperation("non-finite")
    return d


def flag_no(v: Any) -> bool:
    return str(v).strip().lower() in {"no", "n", "false", "0"}


def fetch_pages() -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    OUT.mkdir(parents=True, exist_ok=True)
    session = requests.Session()
    session.headers.update({"User-Agent": "TAD-COUPON-SOURCE-001/0.1 research-only"})
    all_rows: list[dict[str, Any]] = []
    receipts: list[dict[str, Any]] = []
    seen_page_fingerprints: set[str] = set()

    for page in range(1, 101):
        params = {
            "filter": f"auction_date:gte:{START},auction_date:lte:{END}",
            "sort": "auction_date,cusip",
            "page[size]": str(PAGE_SIZE),
            "page[number]": str(page),
        }
        r = session.get(API, params=params, timeout=60)
        r.raise_for_status()
        raw = r.content
        fp = sha256_bytes(raw)
        if fp in seen_page_fingerprints:
            raise RuntimeError(f"PAGINATION_REPEAT page={page} sha256={fp}")
        seen_page_fingerprints.add(fp)
        p = OUT / f"raw_page_{page:03d}.json"
        p.write_bytes(raw)
        obj = r.json()
        rows = obj.get("data")
        if not isinstance(rows, list):
            raise RuntimeError(f"SCHEMA_NO_DATA_LIST page={page}")
        receipts.append({"page": page, "url": r.url, "http": r.status_code, "bytes": len(raw), "sha256": fp, "rows": len(rows)})
        if not rows:
            break
        all_rows.extend(rows)
        if len(rows) < PAGE_SIZE:
            break
    else:
        raise RuntimeError("PAGINATION_LIMIT_EXCEEDED")

    return all_rows, receipts


def main() -> int:
    print(f"{LAB_ID} / {GATE_ID} SOURCE ONLY — BTC OUTCOMES LOCKED")
    print(f"frozen_source_window={START}..{END}")

    rows, receipts = fetch_pages()
    if not rows:
        raise RuntimeError("SOURCE_RETURNED_ZERO_ROWS")

    outside_provider_filter = []
    for r in rows:
        ad = str(r.get("auction_date", ""))
        if not (START <= ad <= END):
            outside_provider_filter.append((ad, r.get("cusip")))

    retained: list[dict[str, Any]] = []
    invalid_rows: list[dict[str, Any]] = []
    allocation_failures: list[dict[str, Any]] = []
    duplicate_ids: list[tuple[str, str]] = []
    ids: set[tuple[str, str]] = set()

    for r in rows:
        term = str(r.get("original_security_term", "")).strip()
        if term not in TERMS:
            continue
        if not flag_no(r.get("inflation_index_security")):
            continue
        if not flag_no(r.get("floating_rate")):
            continue

        missing = [k for k in REQ if r.get(k) is None or str(r.get(k)).strip() == ""]
        if missing:
            invalid_rows.append({"auction_date": r.get("auction_date"), "cusip": r.get("cusip"), "reason": "missing_required", "fields": missing})
            continue

        ad = str(r["auction_date"])
        try:
            date.fromisoformat(ad)
            btc = dec(r["bid_to_cover_ratio"])
            comp = dec(r["comp_accepted"])
            dealer = dec(r["primary_dealer_accepted"])
            direct = dec(r["direct_bidder_accepted"])
            indirect = dec(r["indirect_bidder_accepted"])
            total_a = dec(r["total_accepted"])
            total_t = dec(r["total_tendered"])
        except Exception as e:
            invalid_rows.append({"auction_date": ad, "cusip": r.get("cusip"), "reason": f"numeric_or_date:{type(e).__name__}"})
            continue

        nums = (comp, dealer, direct, indirect, total_a, total_t)
        if btc <= 0 or any(x < 0 for x in nums):
            invalid_rows.append({"auction_date": ad, "cusip": r.get("cusip"), "reason": "nonpositive_btc_or_negative_amount"})
            continue
        if not (START <= ad <= END):
            invalid_rows.append({"auction_date": ad, "cusip": r.get("cusip"), "reason": "outside_frozen_window"})
            continue

        alloc_diff = abs((dealer + direct + indirect) - comp)
        if alloc_diff > Decimal(1):
            allocation_failures.append({"auction_date": ad, "cusip": r.get("cusip"), "diff": str(alloc_diff)})

        ident = (ad, str(r["cusip"]))
        if ident in ids:
            duplicate_ids.append(ident)
        ids.add(ident)

        retained.append({
            "auction_date": ad,
            "cusip": str(r["cusip"]),
            "security_type": str(r["security_type"]),
            "original_security_term": term,
            "inflation_index_security": str(r["inflation_index_security"]),
            "floating_rate": str(r["floating_rate"]),
            "bid_to_cover_ratio": str(btc),
            "comp_accepted": str(comp),
            "primary_dealer_accepted": str(dealer),
            "direct_bidder_accepted": str(direct),
            "indirect_bidder_accepted": str(indirect),
            "total_accepted": str(total_a),
            "total_tendered": str(total_t),
        })

    retained.sort(key=lambda x: (x["original_security_term"], x["auction_date"], x["cusip"]))
    per_term = Counter(r["original_security_term"] for r in retained)

    prev: dict[str, Decimal] = {}
    comparable = 0
    delta_pos = delta_neg = delta_zero = 0
    canonical_with_delta: list[dict[str, Any]] = []
    for r in retained:
        term = r["original_security_term"]
        cur = Decimal(r["bid_to_cover_ratio"])
        d = None
        if term in prev:
            d = cur - prev[term]
            comparable += 1
            if d > 0: delta_pos += 1
            elif d < 0: delta_neg += 1
            else: delta_zero += 1
        prev[term] = cur
        rr = dict(r)
        rr["delta_bid_to_cover"] = None if d is None else str(d)
        canonical_with_delta.append(rr)

    canonical_path = OUT / "canonical_coupon_auctions_v01.jsonl"
    with canonical_path.open("wb") as f:
        for r in canonical_with_delta:
            f.write(canonical_json(r))

    access_2025 = any(str(r.get("auction_date", "")).startswith("2025") for r in rows)
    access_2026 = any(str(r.get("auction_date", "")).startswith("2026") for r in rows)

    gates = {
        "retained_rows_ge_300": len(retained) >= 300,
        "each_frozen_tenor_ge_40": all(per_term.get(t, 0) >= 40 for t in TERMS),
        "comparable_same_tenor_rows_ge_280": comparable >= 280,
        "zero_duplicate_identities": len(duplicate_ids) == 0,
        "zero_invalid_required_rows": len(invalid_rows) == 0,
        "zero_allocation_reconciliation_failures": len(allocation_failures) == 0,
        "zero_provider_rows_outside_filter": len(outside_provider_filter) == 0,
        "protected_period_closed": (not access_2025 and not access_2026),
        "raw_and_canonical_sha_receipts_present": bool(receipts) and canonical_path.exists(),
    }

    if all(gates.values()):
        classification = "SOURCE_DATA_PASS"
    elif not gates["retained_rows_ge_300"] or not gates["each_frozen_tenor_ge_40"] or not gates["comparable_same_tenor_rows_ge_280"]:
        classification = "SOURCE_DATA_INSUFFICIENT"
    else:
        classification = "SOURCE_DATA_FAILURE"

    result = {
        "lab_id": LAB_ID,
        "source_gate_id": GATE_ID,
        "classification": classification,
        "source": API,
        "source_window": {"start": START, "end": END},
        "provider_rows": len(rows),
        "retained_rows": len(retained),
        "per_term_counts": {t: per_term.get(t, 0) for t in TERMS},
        "comparable_same_tenor_rows": comparable,
        "delta_sign_counts": {"positive": delta_pos, "negative": delta_neg, "zero": delta_zero},
        "invalid_required_rows": len(invalid_rows),
        "allocation_reconciliation_failures": len(allocation_failures),
        "duplicate_identities": len(duplicate_ids),
        "provider_rows_outside_filter": len(outside_provider_filter),
        "access_2025": access_2025,
        "access_2026": access_2026,
        "btc_market_values_opened": False,
        "btc_returns_opened": False,
        "pnl_opened": False,
        "live_trading": False,
        "exchange_mutation": False,
        "gates": gates,
        "canonical_sha256": sha256_bytes(canonical_path.read_bytes()),
        "raw_page_receipts": receipts,
        "invalid_row_examples": invalid_rows[:20],
        "allocation_failure_examples": allocation_failures[:20],
        "duplicate_examples": duplicate_ids[:20],
    }
    (OUT / "source_gate_result_v01.json").write_bytes(canonical_json(result))
    (OUT / "manifest_v01.json").write_bytes(canonical_json({
        "authority": "PRE_SOURCE_AUTHORITY_V0.1.md",
        "result_sha256": sha256_bytes((OUT / "source_gate_result_v01.json").read_bytes()),
        "canonical_sha256": result["canonical_sha256"],
        "raw_page_sha256": [x["sha256"] for x in receipts],
    }))

    print(json.dumps(result, indent=2, sort_keys=True))
    print("BTC MARKET VALUES / RETURNS / PNL OPENED = FALSE")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as e:
        print(f"FAIL-CLOSED TECHNICAL: {type(e).__name__}: {e}", file=sys.stderr)
        raise
