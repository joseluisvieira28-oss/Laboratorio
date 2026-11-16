#!/usr/bin/env python3
"""DIAMANTE V9: source-only incremental CMS catalogue audit.

No trading access, no market prices, no historical performance computation.
One GET maximum per invocation. A 429 is never retried in the same invocation.
Historical announcements found now are never considered prospective observations.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timedelta, timezone
from email.utils import parsedate_to_datetime
import hashlib
import json
import os
from pathlib import Path
from typing import Any, Callable
from urllib.error import HTTPError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from bnb_launchpool_source_coverage_v08 import catalog_articles
from radar.bnb_launchpool_watcher import _article_code_from_dict

BASE = "https://www.binance.com"
PATH = "/bapi/composite/v1/public/cms/article/catalog/list/query"
CATALOGS = (49, 93, 128)  # exploratory V8 secondary categories, not canonical signal authority
PAGE_SIZE = 50
MAX_PAGE = 80
SCHEMA = "BNB_SOURCE_ONLY_V09_STATE_1"
BOUNDARY_UTC = "2026-09-24T17:58:57Z"
STATE_DIR = Path("artifacts/bnb_launchpool/source_v09/state")
RECEIPT_DIR = Path("artifacts/bnb_launchpool/source_v09/receipts")
MIN_CATALOG_INTERVAL_SECONDS = 900
DEFAULT_429_COOLDOWN_SECONDS = 3600
MAX_BYTES = 2_000_000

def utc(dt: datetime) -> str:
    return dt.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")

def parse_utc(s: str) -> datetime:
    return datetime.fromisoformat(s.replace("Z", "+00:00")).astimezone(timezone.utc)

def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()

def canonical(data: dict[str, Any]) -> bytes:
    return json.dumps(data, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")

def new_state() -> dict[str, Any]:
    return {
        "schema": SCHEMA, "catalogs": {
            str(cid): {
                "next_page": 1, "pages": [], "first_seen": {},
                "phase": "NOT_STARTED", "last_request_utc": None
            } for cid in CATALOGS
        }, "global_not_before_utc": None,
        "no_market_outcomes_accessed": True, "no_live_trading": True
    }

def load_state(state_dir: Path) -> tuple[dict[str, Any], str]:
    path, digest = state_dir / "checkpoint.json", state_dir / "checkpoint.sha256"
    if not path.exists() and not digest.exists():
        return new_state(), "NEW_CHECKPOINT__NO_PAST_COVERAGE_CLAIM"
    if not path.exists() or not digest.exists():
        raise ValueError("CHECKPOINT_PAIR_INCOMPLETE")
    b = path.read_bytes()
    if sha256(b) != digest.read_text(encoding="ascii").strip():
        raise ValueError("CHECKPOINT_SHA256_MISMATCH")
    state = json.loads(b)
    if state.get("schema") != SCHEMA or sorted(state.get("catalogs", {})) != sorted(map(str, CATALOGS)):
        raise ValueError("CHECKPOINT_SCHEMA_OR_UNIVERSE_MISMATCH")
    if state.get("no_market_outcomes_accessed") is not True or state.get("no_live_trading") is not True:
        raise ValueError("CHECKPOINT_GOVERNANCE_MISMATCH")
    return state, "VERIFIED_RESTORED_CHECKPOINT"

def save_state(state: dict[str, Any], state_dir: Path) -> str:
    state_dir.mkdir(parents=True, exist_ok=True)
    b = canonical(state)
    tmp = state_dir / "checkpoint.json.tmp"
    tmp.write_bytes(b)
    os.replace(tmp, state_dir / "checkpoint.json")
    (state_dir / "checkpoint.sha256").write_text(sha256(b) + "\n", encoding="ascii")
    return sha256(b)

def retry_after_seconds(value: str | None, now: datetime) -> int:
    if not value:
        return DEFAULT_429_COOLDOWN_SECONDS
    try:
        n = int(value.strip())
        return max(0, n)
    except (TypeError, ValueError):
        pass
    try:
        parsed = parsedate_to_datetime(value)
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=timezone.utc)
        n = int((parsed.astimezone(timezone.utc) - now).total_seconds())
        return max(0, n)
    except (TypeError, ValueError, OverflowError):
        return DEFAULT_429_COOLDOWN_SECONDS

def fetch_catalog(catalog_id: int, page: int) -> tuple[Any, bytes]:
    if catalog_id not in CATALOGS or not (1 <= page <= MAX_PAGE):
        raise ValueError("UNAPPROVED_CATALOG_OR_PAGE")
    qs = urlencode({"catalogId": catalog_id, "pageNo": page, "pageSize": PAGE_SIZE})
    req = Request(
        BASE + PATH + "?" + qs, method="GET",
        headers={"User-Agent": "crypto-edge-radar/0.9 bnb-v9-source-only",
                 "Accept": "application/json",
                 "Accept-Language": "en-US,en;q=0.9"}
    )
    # Exactly one request: do not reuse old client's 3x retry-on-429 behavior.
    with urlopen(req, timeout=12) as response:
        if response.status != 200:
            raise ValueError("HTTP_STATUS_NOT_200")
        body = response.read(MAX_BYTES + 1)
        if not body or len(body) > MAX_BYTES:
            raise ValueError("HTTP_BODY_EMPTY_OR_TOO_LARGE")
        return json.loads(body.decode("utf-8")), body

def known_catalog_schema(payload: Any) -> bool:
    if not isinstance(payload, dict) or payload.get("success") is False or not isinstance(payload.get("data"), dict):
        return False
    def visit(n: Any) -> bool:
        if isinstance(n, dict):
            return any(k in ("catalogs", "articles") and isinstance(v, list) for k, v in n.items()) or any(visit(v) for v in n.values())
        return isinstance(n, list) and any(visit(v) for v in n)
    return visit(payload["data"])

def invalid_launchpool_title_codes(payload: Any) -> int:
    n = 0
    def visit(node: Any):
        nonlocal n
        if isinstance(node, dict):
            if isinstance(node.get("title"), str) and "launchpool" in node["title"].lower():
                if _article_code_from_dict(node) is None:
                    n += 1
            for child in node.values():
                visit(child)
        elif isinstance(node, list):
            for child in node:
                visit(child)
    visit(payload)
    return n

def audit_one(
    state: dict[str, Any], *, catalog_id: int, now: datetime,
    transport: Callable[[int, int], tuple[Any, bytes]]
) -> tuple[dict[str, Any], dict[str, Any]]:
    if catalog_id not in CATALOGS:
        raise ValueError("UNAPPROVED_CATALOG")
    now = now.astimezone(timezone.utc)
    part = state["catalogs"][str(catalog_id)]
    receipt: dict[str, Any] = {
        "audit_id": "BNB-LAUNCHPOOL-V09-INCREMENTAL-SOURCE-ONLY",
        "checked_at_utc": utc(now),
        "catalog_id": catalog_id, "attempted_requests": 0,
        "catalog_phase_before": part["phase"], "catalog_page_requested": part["next_page"],
        "source_only": True, "prices_accessed": False,
        "pnl_accessed": False, "orders_created": False, "exchange_mutation": False,
        "not_retroactively_eligible_for_25_events": True,
        "known_limitations": [
            "Only the chosen provisional CMS category and a single page were examined in this run.",
            "A retrospective catalogue crawl cannot prove that the parent watcher first observed an article before its frozen entry.",
            "Article titles are candidates, not events meeting frozen BNB staking/locking detail and time rules.",
            "Dynamic pagination can shift across runs; completion needs separate continuity review."
        ]
    }
    if part["phase"] == "CATALOG_REACHED_END__REVIEW_REQUIRED":
        receipt["status"] = "ALREADY_SCANNED__NOT_PROSPECTIVE_PASS"
        return state, receipt
    if state.get("global_not_before_utc") and now < parse_utc(state["global_not_before_utc"]):
        receipt.update(status="GLOBAL_COOLDOWN_HONORED__SOURCE_PENDING",
                       next_eligible_utc=state["global_not_before_utc"])
        return state, receipt
    if part.get("last_request_utc"):
        permitted = parse_utc(part["last_request_utc"]) + timedelta(seconds=MIN_CATALOG_INTERVAL_SECONDS)
        if now < permitted:
            receipt.update(status="CATALOG_MIN_INTERVAL_HONORED__SOURCE_PENDING",
                           next_eligible_utc=utc(permitted))
            return state, receipt
    page = int(part["next_page"])
    if page > MAX_PAGE:
        receipt["status"] = "MAX_PAGE_BUDGET__SOURCE_BLOCKED"
        return state, receipt

    # Single GET. On HTTP429 no retry; honor the header or a conservative backoff.
    receipt["attempted_requests"] = 1
    part["last_request_utc"] = utc(now)
    try:
        payload, raw = transport(catalog_id, page)
    except HTTPError as exc:
        if exc.code == 429:
            wait = retry_after_seconds(exc.headers.get("Retry-After") if exc.headers else None, now)
            next_allowed = now + timedelta(seconds=max(wait, DEFAULT_429_COOLDOWN_SECONDS))
            state["global_not_before_utc"] = utc(next_allowed)
            part["phase"] = "RATE_LIMITED__CHECKPOINT_PRESERVED"
            receipt.update(status="HTTP_429_SOURCE_BLOCKED", retry_after_header=exc.headers.get("Retry-After") if exc.headers else None,
                           next_eligible_utc=utc(next_allowed), page_not_advanced=True)
        else:
            part["phase"] = "HTTP_ERROR__SOURCE_BLOCKED"
            receipt.update(status="HTTP_ERROR_SOURCE_BLOCKED", http_status=exc.code, page_not_advanced=True)
        return state, receipt
    except Exception as exc:
        part["phase"] = "SOURCE_ERROR__SOURCE_BLOCKED"
        receipt.update(status="SOURCE_ERROR_BLOCKED", error_type=type(exc).__name__, page_not_advanced=True)
        return state, receipt

    if not known_catalog_schema(payload):
        part["phase"] = "SCHEMA_ERROR__SOURCE_BLOCKED"
        receipt.update(status="SCHEMA_ERROR_SOURCE_BLOCKED", page_sha256=sha256(raw), page_not_advanced=True)
        return state, receipt
    if invalid_launchpool_title_codes(payload):
        part["phase"] = "BAD_ARTICLE_ID__SOURCE_BLOCKED"
        receipt.update(status="BAD_LAUNCHPOOL_ARTICLE_ID_SOURCE_BLOCKED", page_sha256=sha256(raw), page_not_advanced=True)
        return state, receipt

    rows = catalog_articles(payload)
    codes = tuple(sorted(row["code"] for row in rows))
    fp = sha256("\n".join(codes).encode("ascii"))
    if part["pages"] and any(r["code_fingerprint_sha256"] == fp for r in part["pages"]):
        part["phase"] = "PAGINATION_REPEAT__SOURCE_BLOCKED"
        receipt.update(status="PAGINATION_REPEAT_SOURCE_BLOCKED", page_sha256=sha256(raw), page_not_advanced=True)
        return state, receipt

    if not rows and page == 1:
        part["phase"] = "EMPTY_FIRST_PAGE__SOURCE_BLOCKED"
        receipt.update(status="EMPTY_FIRST_PAGE_SOURCE_BLOCKED", page_sha256=sha256(raw), page_not_advanced=True)
        return state, receipt

    listing_candidates = [r for r in rows if "launchpool" in r["title"].lower()]
    for row in listing_candidates:
        if row["code"] not in part["first_seen"]:
            part["first_seen"][row["code"]] = {
                "first_seen_at_utc": utc(now),
                "title_at_first_seen": row["title"],
                "first_seen_catalog_page": page,
                "page_sha256": sha256(raw),
                "historical_backfill_allowed": False,
                "detail_eligibility_verified": False,
            }
    part["pages"].append({
        "page": page, "checked_at_utc": utc(now), "raw_sha256": sha256(raw),
        "code_fingerprint_sha256": fp,
        "articles_on_page": len(rows),
        "launchpool_title_candidates_on_page": len(listing_candidates)
    })
    part["next_page"] = page + 1
    if not rows:
        part["phase"] = "CATALOG_REACHED_END__REVIEW_REQUIRED"
        receipt["status"] = "CATALOG_PAGINATION_REACHED_END__NOT_FORWARD_PROOF"
    else:
        part["phase"] = "INCREMENTAL_SCAN_PENDING"
        receipt["status"] = "INCREMENTAL_PAGE_OBSERVED__NOT_FORWARD_PROOF"
    receipt.update(
        page_sha256=sha256(raw), unique_articles_on_page=len(rows),
        launchpool_title_candidates_on_page=len(listing_candidates),
        cumulative_pages=len(part["pages"]),
        cumulative_launchpool_title_candidates=len(part["first_seen"]),
        next_page=part["next_page"], catalog_phase_after=part["phase"]
    )
    return state, receipt

def write_receipt(receipt: dict[str, Any], out_dir: Path) -> Path:
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / "BNB_SOURCE_V09_RESULT.json"
    path.write_text(json.dumps(receipt, sort_keys=True, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return path

def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--catalog", type=int, default=49, choices=CATALOGS)
    parser.add_argument("--state-dir", type=Path, default=STATE_DIR)
    parser.add_argument("--receipt-dir", type=Path, default=RECEIPT_DIR)
    args = parser.parse_args()
    now = datetime.now(timezone.utc)
    try:
        state, recovery = load_state(args.state_dir)
        state, receipt = audit_one(state, catalog_id=args.catalog, now=now, transport=fetch_catalog)
        receipt["checkpoint_recovery"] = recovery
        receipt["checkpoint_sha256"] = save_state(state, args.state_dir)
    except Exception as exc:
        receipt = {
            "audit_id": "BNB-LAUNCHPOOL-V09-INCREMENTAL-SOURCE-ONLY",
            "checked_at_utc": utc(now), "catalog_id": args.catalog,
            "status": "CHECKPOINT_OR_AUDITOR_ERROR__SOURCE_BLOCKED",
            "error_type": type(exc).__name__,
            "governance": "NO_TRADING_NO_BACKFILL",
            "attempted_requests": 0, "prices_accessed": False, "pnl_accessed": False
        }
    write_receipt(receipt, args.receipt_dir)
    print(json.dumps({k: receipt.get(k) for k in (
        "status", "catalog_id", "attempted_requests", "checkpoint_recovery",
        "catalog_page_requested", "unique_articles_on_page",
        "launchpool_title_candidates_on_page", "next_page", "next_eligible_utc",
        "checkpoint_sha256"
    )}, indent=2))
    # A scientific source block is an explicit red CI status, not a silent PASS.
    return 0 if receipt["status"] == "INCREMENTAL_PAGE_OBSERVED__NOT_FORWARD_PROOF" else 2

if __name__ == "__main__":
    raise SystemExit(main())
