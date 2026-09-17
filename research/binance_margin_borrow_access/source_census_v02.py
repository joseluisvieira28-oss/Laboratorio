#!/usr/bin/env python3
"""BINANCE-MARGIN-BORROW-ACCESS-001 source census V0.2.

Source-only / outcome-blind.
- official Binance English Telegram channel = deterministic index/transport only;
- official Binance Support CMS detail = canonical article content;
- frozen scientific window = 2023-01-01 through 2024-12-31;
- hard fail if the historical Telegram cursor returns any 2025/2026 message;
- no price, returns, basis, borrow-rate, account, PnL or live data.
"""
from __future__ import annotations

import hashlib
import html
import json
import re
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

import requests
from bs4 import BeautifulSoup

LAB_ID = "BINANCE-MARGIN-BORROW-ACCESS-001"
TELEGRAM_BASE = "https://t.me/s/binance_announcements"
UPPER_CURSOR = 6900
START_DT = datetime(2023, 1, 1, tzinfo=timezone.utc)
END_DT = datetime(2024, 12, 31, 23, 59, 59, tzinfo=timezone.utc)
START_MS = int(START_DT.timestamp() * 1000)
END_MS = int(END_DT.timestamp() * 1000)
MAX_PAGES = 500
DETAIL_ENDPOINT = "https://www.binance.com/bapi/composite/v1/public/cms/article/detail/query"
REFERER = "https://www.binance.com/en/support/announcement"

POSITIVE_CONTROLS = {
    "a74f935eaa2247889d58e33ec23313bb": 2023,
    "6674719e209641bda688729852d35fb5": 2024,
}

SESSION = requests.Session()
SESSION.headers.update({
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/140 Safari/537.36",
    "Accept-Language": "en-US,en;q=0.9",
})

CODE_RE = re.compile(r"([0-9a-fA-F]{32})")


def request_bytes(url: str, params: dict[str, str] | None = None, attempts: int = 5) -> tuple[bytes, int]:
    last: Exception | None = None
    for attempt in range(attempts):
        try:
            r = SESSION.get(url, params=params, headers={"Referer": REFERER}, timeout=45)
            r.raise_for_status()
            return r.content, r.status_code
        except Exception as exc:
            last = exc
            if attempt + 1 < attempts:
                time.sleep(1.25 * (attempt + 1))
    raise RuntimeError(str(last))


def request_json(url: str, params: dict[str, str], attempts: int = 5) -> tuple[dict[str, Any], int, str]:
    raw, status = request_bytes(url, params=params, attempts=attempts)
    try:
        obj = json.loads(raw)
    except Exception as exc:
        raise RuntimeError(f"non-JSON canonical detail response: {exc}") from exc
    if not isinstance(obj, dict):
        raise RuntimeError("non-object canonical detail response")
    return obj, status, hashlib.sha256(raw).hexdigest()


def iter_dicts(obj: Any) -> Iterable[dict[str, Any]]:
    if isinstance(obj, dict):
        yield obj
        for value in obj.values():
            yield from iter_dicts(value)
    elif isinstance(obj, list):
        for value in obj:
            yield from iter_dicts(value)


def collect_strings(obj: Any) -> list[str]:
    out: list[str] = []
    if isinstance(obj, dict):
        for key, value in obj.items():
            if isinstance(value, str) and key.lower() not in {"url", "link", "shareurl", "image", "icon"}:
                out.append(value)
            elif isinstance(value, (dict, list)):
                out.extend(collect_strings(value))
    elif isinstance(obj, list):
        for value in obj:
            out.extend(collect_strings(value))
    return out


def normalize_text(raw: str) -> str:
    raw = re.sub(r"<script[^>]*>.*?</script>", " ", raw, flags=re.I | re.S)
    raw = re.sub(r"<style[^>]*>.*?</style>", " ", raw, flags=re.I | re.S)
    raw = re.sub(r"<[^>]+>", " ", raw)
    raw = html.unescape(raw)
    return re.sub(r"\s+", " ", raw).strip()


def extract_release_ms(obj: dict[str, Any]) -> int | None:
    candidates: list[int] = []
    for node in iter_dicts(obj):
        for key in ("releaseDate", "releaseTime", "publishTime"):
            value = node.get(key)
            if value is None:
                continue
            try:
                ts = int(value)
            except (TypeError, ValueError):
                continue
            if ts < 10_000_000_000:
                ts *= 1000
            candidates.append(ts)
    in_window = [x for x in candidates if START_MS <= x <= END_MS]
    if in_window:
        return min(in_window)
    return min(candidates) if candidates else None


def resolve_detail(code: str) -> dict[str, Any]:
    failures: list[str] = []
    for key in ("articleCode", "articlecode"):
        try:
            obj, status, sha = request_json(DETAIL_ENDPOINT, {key: code})
            data = obj.get("data", obj)
            text = normalize_text(" ".join(collect_strings(data)))
            if not text:
                failures.append(f"{key}: empty canonical article text")
                continue

            payload_codes: set[str] = set()
            for node in iter_dicts(obj):
                for code_key in ("code", "articleCode", "articlecode"):
                    if node.get(code_key):
                        payload_codes.add(str(node[code_key]).lower())

            payload_code_match = code.lower() in payload_codes
            release_ms = extract_release_ms(obj)
            low = text.lower()
            return {
                "code": code.lower(),
                "detail_param": key,
                "http_status": status,
                "response_sha256": sha,
                "payload_code_match": payload_code_match,
                "canonical_text_length": len(text),
                "official_release_ms": release_ms,
                "contains_borrowable_asset_phrase": "borrowable asset" in low,
                "contains_cross_margin_phrase": "cross margin" in low,
                "structural_phrase_pass": ("borrowable asset" in low and "cross margin" in low),
            }
        except Exception as exc:
            failures.append(f"{key}: {type(exc).__name__}: {str(exc)[:180]}")
    raise RuntimeError("official detail resolution failed for " + code + ": " + " | ".join(failures))


def parse_telegram_page(raw: bytes) -> list[dict[str, Any]]:
    soup = BeautifulSoup(raw, "html.parser")
    records: list[dict[str, Any]] = []
    for msg in soup.select("div.tgme_widget_message[data-post]"):
        data_post = msg.get("data-post", "")
        if not data_post.startswith("binance_announcements/"):
            continue
        try:
            message_id = int(data_post.rsplit("/", 1)[1])
        except Exception:
            continue

        time_tag = msg.select_one("time[datetime]")
        if time_tag is None:
            continue
        try:
            dt = datetime.fromisoformat(time_tag.get("datetime").replace("Z", "+00:00")).astimezone(timezone.utc)
        except Exception:
            continue

        text_node = msg.select_one("div.tgme_widget_message_text")
        text = text_node.get_text("\n", strip=True) if text_node else ""
        title = next((line.strip() for line in text.splitlines() if line.strip()), "")

        links: list[str] = []
        for a in msg.select("a[href]"):
            href = str(a.get("href", ""))
            if "binance.com/" in href and "/support/announcement/" in href:
                links.append(href)

        codes: list[str] = []
        for link in links:
            match = CODE_RE.search(link)
            if match:
                codes.append(match.group(1).lower())

        records.append({
            "message_id": message_id,
            "timestamp_utc": dt.isoformat(),
            "timestamp_ms": int(dt.timestamp() * 1000),
            "title": title,
            "article_codes": sorted(set(codes)),
        })
    return records


def main() -> int:
    classification = "SOURCE_ACQUISITION_TECHNICAL_FAILURE"
    failure: str | None = None
    cursor = UPPER_CURSOR
    reached_before_start = False
    page_receipts: list[dict[str, Any]] = []
    relevant_by_code: dict[str, dict[str, Any]] = {}
    total_messages_in_window = 0
    total_support_links_in_window = 0
    protected_period_seen = False

    resolved: list[dict[str, Any]] = []
    controls: dict[str, Any] = {}
    qualifying: list[dict[str, Any]] = []
    years_with_phrase: list[int] = []

    try:
        for page_no in range(1, MAX_PAGES + 1):
            raw, status = request_bytes(TELEGRAM_BASE, params={"before": str(cursor)})
            page = parse_telegram_page(raw)
            if not page:
                raise RuntimeError(f"Telegram page {page_no} returned no parseable channel messages")

            ids = sorted({x["message_id"] for x in page})
            if not ids:
                raise RuntimeError(f"Telegram page {page_no} had no message IDs")
            next_cursor = min(ids)
            if next_cursor >= cursor:
                raise RuntimeError(f"non-descending Telegram cursor: {cursor} -> {next_cursor}")

            page_min_ms = min(x["timestamp_ms"] for x in page)
            page_max_ms = max(x["timestamp_ms"] for x in page)
            if page_max_ms > END_MS:
                protected_period_seen = True
                raise RuntimeError("protected-period firewall: historical cursor returned timestamp after 2024-12-31")

            in_window = [x for x in page if START_MS <= x["timestamp_ms"] <= END_MS]
            total_messages_in_window += len(in_window)
            for rec in in_window:
                codes = rec["article_codes"]
                total_support_links_in_window += len(codes)
                low_title = rec["title"].lower()
                source_candidate = any(term in low_title for term in ("margin", "borrowable", "cross margin"))
                for code in codes:
                    if source_candidate or code in POSITIVE_CONTROLS:
                        existing = relevant_by_code.get(code)
                        candidate = {
                            "code": code,
                            "telegram_message_id": rec["message_id"],
                            "telegram_timestamp_ms": rec["timestamp_ms"],
                            "telegram_title": rec["title"],
                            "source_candidate": source_candidate,
                        }
                        if existing is None or candidate["telegram_message_id"] < existing["telegram_message_id"]:
                            relevant_by_code[code] = candidate

            page_receipts.append({
                "page": page_no,
                "requested_before": cursor,
                "http_status": status,
                "response_sha256": hashlib.sha256(raw).hexdigest(),
                "messages": len(page),
                "min_message_id": min(ids),
                "max_message_id": max(ids),
                "min_timestamp_ms": page_min_ms,
                "max_timestamp_ms": page_max_ms,
                "retained_window_messages": len(in_window),
            })

            if page_min_ms < START_MS:
                reached_before_start = True
                break
            cursor = next_cursor

        if not reached_before_start:
            classification = "SOURCE_ENUMERATION_INCOMPLETE"
        else:
            codes_to_resolve = sorted(set(relevant_by_code) | set(POSITIVE_CONTROLS))
            for code in codes_to_resolve:
                meta = relevant_by_code.get(code)
                if meta is None:
                    resolved.append({
                        "code": code,
                        "telegram_index_present": False,
                        "payload_code_match": False,
                        "structural_phrase_pass": False,
                    })
                    continue
                detail = resolve_detail(code)
                detail.update(meta)
                detail["telegram_index_present"] = True
                resolved.append(detail)

            controls = {
                code: next((x for x in resolved if x.get("code") == code), {
                    "telegram_index_present": False,
                    "payload_code_match": False,
                    "structural_phrase_pass": False,
                })
                for code in POSITIVE_CONTROLS
            }
            controls_ok = all(
                x.get("telegram_index_present")
                and x.get("payload_code_match")
                and x.get("structural_phrase_pass")
                and x.get("official_release_ms") is not None
                and START_MS <= int(x.get("official_release_ms")) <= END_MS
                for x in controls.values()
            )

            qualifying = [
                x for x in resolved
                if x.get("telegram_index_present")
                and x.get("payload_code_match")
                and x.get("structural_phrase_pass")
                and x.get("official_release_ms") is not None
                and START_MS <= int(x["official_release_ms"]) <= END_MS
            ]
            years_with_phrase = sorted({
                datetime.fromtimestamp(int(x["official_release_ms"]) / 1000, tz=timezone.utc).year
                for x in qualifying
            })

            if not controls_ok:
                classification = "PROVENANCE_FAILURE"
            elif not ({2023, 2024} <= set(years_with_phrase)):
                classification = "INSUFFICIENT_EVENT_SAMPLE"
            else:
                classification = "SOURCE_CENSUS_PASS"

    except Exception as exc:
        failure = f"{type(exc).__name__}: {str(exc)[:1000]}"
        classification = "PROVENANCE_FAILURE" if protected_period_seen else "SOURCE_ACQUISITION_TECHNICAL_FAILURE"

    receipt = {
        "lab_id": LAB_ID,
        "phase": "SOURCE_CENSUS_V0_2_ONLY_OUTCOME_BLIND",
        "classification": classification,
        "transport": "official_binance_telegram_index_plus_official_support_detail",
        "upper_cursor": UPPER_CURSOR,
        "frozen_start_utc": "2023-01-01T00:00:00Z",
        "frozen_end_utc": "2024-12-31T23:59:59Z",
        "enumeration_boundary_reached_before_start": reached_before_start,
        "protected_period_seen": protected_period_seen,
        "pages": page_receipts,
        "total_messages_in_frozen_window": total_messages_in_window,
        "total_support_links_in_frozen_window": total_support_links_in_window,
        "relevant_or_control_codes": len(set(relevant_by_code) | set(POSITIVE_CONTROLS)),
        "resolved_articles": resolved,
        "positive_controls": controls,
        "qualifying_cross_margin_borrowable_articles": len(qualifying),
        "years_with_structural_phrase": years_with_phrase,
        "failure": failure,
        "safety": {
            "price_data_opened": False,
            "returns_opened": False,
            "basis_opened": False,
            "borrow_rate_opened": False,
            "borrow_inventory_opened": False,
            "authenticated_exchange_api_used": False,
            "account_data_opened": False,
            "pnl_opened": False,
            "win_rate_opened": False,
            "pf_opened": False,
            "drawdown_opened": False,
            "live_trading": False,
            "exchange_mutation": False,
            "protected_2025_2026_message_seen": protected_period_seen,
        },
    }

    out = Path("source_census_v02_output")
    out.mkdir(parents=True, exist_ok=True)
    path = out / "BINANCE_MARGIN_BORROW_ACCESS_001_SOURCE_CENSUS_RECEIPT_V0_2.json"
    path.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    print(json.dumps({
        "lab_id": LAB_ID,
        "classification": classification,
        "pages": len(page_receipts),
        "boundary_reached": reached_before_start,
        "protected_period_seen": protected_period_seen,
        "window_messages": total_messages_in_window,
        "support_links": total_support_links_in_window,
        "resolved_articles": len(resolved),
        "qualifying_articles": len(qualifying),
        "years_with_structural_phrase": years_with_phrase,
        "prices_opened": False,
        "returns_opened": False,
        "pnl_opened": False,
    }, sort_keys=True))

    return 0 if classification == "SOURCE_CENSUS_PASS" else 2


if __name__ == "__main__":
    sys.exit(main())
