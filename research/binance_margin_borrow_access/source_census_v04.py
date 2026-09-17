#!/usr/bin/env python3
"""BINANCE-MARGIN-BORROW-ACCESS-001 source census V0.4.

Source-only / outcome-blind. Implements frozen V0.4 architecture:
A) protected-safe immutable Telegram index manifest;
B) exactly 8 deterministic official Binance Support detail-hydration shards;
C) canonical aggregation with fail-closed source verdict.

No market prices, returns, basis, borrow rates/inventory, authenticated API,
account data, PnL or live execution are requested.
"""
from __future__ import annotations

import argparse
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
DETAIL_ENDPOINT = "https://www.binance.com/bapi/composite/v1/public/cms/article/detail/query"
REFERER = "https://www.binance.com/en/support/announcement"
UPPER_CURSOR = 6899
START_DT = datetime(2023, 1, 1, tzinfo=timezone.utc)
END_DT = datetime(2024, 12, 31, 23, 59, 59, tzinfo=timezone.utc)
END_DAY_FLOOR_DT = datetime(2024, 12, 31, tzinfo=timezone.utc)
START_MS = int(START_DT.timestamp() * 1000)
END_MS = int(END_DT.timestamp() * 1000)
END_DAY_FLOOR_MS = int(END_DAY_FLOOR_DT.timestamp() * 1000)
MAX_PAGES = 500
SHARD_COUNT = 8

POSITIVE_CONTROLS = {
    "a74f935eaa2247889d58e33ec23313bb": 2023,
    "6674719e209641bda688729852d35fb5": 2024,
}

UA = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/140 Safari/537.36"
CODE_RE = re.compile(r"([0-9a-fA-F]{32})")
PUBLISHED_RE = re.compile(
    r"Published\s+on\s+(\d{4}-\d{2}-\d{2})\s+(\d{2}:\d{2})(?::(\d{2}))?(?:\s*\(UTC\)|\s*UTC)?",
    re.I,
)
RELEASE_KEYS = {
    "releasedate", "releasetime", "publishtime", "publishdate", "publishedat", "publishedtime"
}

SESSION = requests.Session()
SESSION.headers.update({"User-Agent": UA, "Accept-Language": "en-US,en;q=0.9"})

SAFETY = {
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
    "protected_2025_2026_message_seen": False,
}


def stable_json_sha(obj: Any) -> str:
    raw = json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()
    return hashlib.sha256(raw).hexdigest()


def request_bytes(url: str, params: dict[str, str] | None = None, attempts: int = 6) -> tuple[bytes, int]:
    last: Exception | None = None
    for attempt in range(attempts):
        try:
            r = SESSION.get(url, params=params, headers={"Referer": REFERER}, timeout=45)
            if r.status_code == 429 or 500 <= r.status_code < 600:
                raise RuntimeError(f"retryable HTTP {r.status_code}")
            r.raise_for_status()
            return r.content, r.status_code
        except Exception as exc:
            last = exc
            if attempt + 1 < attempts:
                time.sleep(min(20.0, 1.5 * (2 ** attempt)))
    raise RuntimeError(str(last))


def iter_dicts(obj: Any) -> Iterable[dict[str, Any]]:
    if isinstance(obj, dict):
        yield obj
        for v in obj.values():
            yield from iter_dicts(v)
    elif isinstance(obj, list):
        for v in obj:
            yield from iter_dicts(v)


def collect_strings(obj: Any) -> list[str]:
    out: list[str] = []
    if isinstance(obj, dict):
        for k, v in obj.items():
            if isinstance(v, str) and k.lower() not in {"url", "link", "shareurl", "image", "icon"}:
                out.append(v)
            elif isinstance(v, (dict, list)):
                out.extend(collect_strings(v))
    elif isinstance(obj, list):
        for v in obj:
            out.extend(collect_strings(v))
    return out


def normalize_text(raw: str) -> str:
    raw = re.sub(r"<script[^>]*>.*?</script>", " ", raw, flags=re.I | re.S)
    raw = re.sub(r"<style[^>]*>.*?</style>", " ", raw, flags=re.I | re.S)
    raw = re.sub(r"<[^>]+>", " ", raw)
    raw = html.unescape(raw)
    return re.sub(r"\s+", " ", raw).strip()


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
            dt = datetime.fromisoformat(str(time_tag.get("datetime")).replace("Z", "+00:00")).astimezone(timezone.utc)
        except Exception:
            continue
        text_node = msg.select_one("div.tgme_widget_message_text")
        text = text_node.get_text("\n", strip=True) if text_node else ""
        title = next((x.strip() for x in text.splitlines() if x.strip()), "")
        codes: set[str] = set()
        for a in msg.select("a[href]"):
            href = str(a.get("href", ""))
            if "binance.com/" not in href or "/support/announcement/" not in href:
                continue
            m = CODE_RE.search(href)
            if m:
                codes.add(m.group(1).lower())
        records.append({
            "message_id": message_id,
            "timestamp_ms": int(dt.timestamp() * 1000),
            "timestamp_utc": dt.isoformat(),
            "title": title,
            "article_codes": sorted(codes),
        })
    return records


def cmd_manifest(out_dir: Path) -> int:
    out_dir.mkdir(parents=True, exist_ok=True)
    cursor = UPPER_CURSOR
    reached_before_start = False
    relevant_by_code: dict[str, dict[str, Any]] = {}
    pages: list[dict[str, Any]] = []
    total_messages = 0
    total_links = 0
    classification = "SOURCE_ACQUISITION_TECHNICAL_FAILURE"
    failure: str | None = None
    protected = False
    try:
        for page_no in range(1, MAX_PAGES + 1):
            raw, status = request_bytes(TELEGRAM_BASE, {"before": str(cursor)})
            page = parse_telegram_page(raw)
            if not page:
                raise RuntimeError(f"Telegram page {page_no} returned no parseable messages")
            ids = sorted({x["message_id"] for x in page})
            next_cursor = min(ids)
            if next_cursor >= cursor:
                raise RuntimeError(f"non-descending cursor {cursor}->{next_cursor}")
            pmin = min(x["timestamp_ms"] for x in page)
            pmax = max(x["timestamp_ms"] for x in page)
            if page_no == 1 and not (END_DAY_FLOOR_MS <= pmax <= END_MS):
                if pmax > END_MS:
                    protected = True
                    raise RuntimeError("protected-period firewall: V0.4 first page exceeds 2024-12-31")
                classification = "SOURCE_ENUMERATION_INCOMPLETE"
                raise RuntimeError("upper cursor does not cover 2024-12-31 UTC")
            if pmax > END_MS:
                protected = True
                raise RuntimeError("protected-period firewall: page exceeds 2024-12-31")
            in_window = [x for x in page if START_MS <= x["timestamp_ms"] <= END_MS]
            total_messages += len(in_window)
            for rec in in_window:
                total_links += len(rec["article_codes"])
                low = rec["title"].lower()
                source_candidate = any(t in low for t in ("margin", "borrowable", "cross margin"))
                for code in rec["article_codes"]:
                    if not (source_candidate or code in POSITIVE_CONTROLS):
                        continue
                    candidate = {
                        "code": code,
                        "telegram_message_id": rec["message_id"],
                        "telegram_timestamp_ms": rec["timestamp_ms"],
                        "telegram_title": rec["title"],
                        "source_candidate": source_candidate,
                    }
                    old = relevant_by_code.get(code)
                    if old is None or candidate["telegram_message_id"] < old["telegram_message_id"]:
                        relevant_by_code[code] = candidate
            pages.append({
                "page": page_no,
                "requested_before": cursor,
                "http_status": status,
                "response_sha256": hashlib.sha256(raw).hexdigest(),
                "messages": len(page),
                "min_message_id": min(ids),
                "max_message_id": max(ids),
                "min_timestamp_ms": pmin,
                "max_timestamp_ms": pmax,
                "retained_window_messages": len(in_window),
            })
            if pmin < START_MS:
                reached_before_start = True
                break
            cursor = next_cursor
        if not reached_before_start:
            classification = "SOURCE_ENUMERATION_INCOMPLETE"
            raise RuntimeError("lower 2023 boundary was not crossed")
        missing_controls = sorted(set(POSITIVE_CONTROLS) - set(relevant_by_code))
        if missing_controls:
            classification = "PROVENANCE_FAILURE"
            raise RuntimeError("positive controls missing from immutable index: " + ",".join(missing_controls))
        items = sorted(relevant_by_code.values(), key=lambda x: x["code"])
        manifest_core = {
            "lab_id": LAB_ID,
            "phase": "V0_4_IMMUTABLE_INDEX_MANIFEST",
            "upper_cursor": UPPER_CURSOR,
            "frozen_start_utc": "2023-01-01T00:00:00Z",
            "frozen_end_utc": "2024-12-31T23:59:59Z",
            "shard_count": SHARD_COUNT,
            "items": items,
        }
        digest = stable_json_sha(manifest_core)
        manifest = {
            **manifest_core,
            "manifest_sha256": digest,
            "classification": "MANIFEST_PASS",
            "enumeration_boundary_reached_before_start": True,
            "protected_period_seen": False,
            "page_count": len(pages),
            "total_messages_in_frozen_window": total_messages,
            "total_support_links_in_frozen_window": total_links,
            "relevant_or_control_codes": len(items),
            "pages": pages,
            "safety": SAFETY,
        }
        (out_dir / "manifest.json").write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n")
        print(json.dumps({"classification":"MANIFEST_PASS","codes":len(items),"pages":len(pages),"manifest_sha256":digest}))
        return 0
    except Exception as exc:
        failure = f"{type(exc).__name__}: {str(exc)[:1000]}"
        if protected:
            classification = "PROVENANCE_FAILURE"
        elif classification not in {"SOURCE_ENUMERATION_INCOMPLETE", "PROVENANCE_FAILURE"}:
            classification = "SOURCE_ACQUISITION_TECHNICAL_FAILURE"
        receipt = {
            "lab_id": LAB_ID,
            "phase": "V0_4_IMMUTABLE_INDEX_MANIFEST",
            "classification": classification,
            "failure": failure,
            "protected_period_seen": protected,
            "enumeration_boundary_reached_before_start": reached_before_start,
            "page_count": len(pages),
            "total_messages_in_frozen_window": total_messages,
            "total_support_links_in_frozen_window": total_links,
            "pages": pages,
            "safety": {**SAFETY, "protected_2025_2026_message_seen": protected},
        }
        (out_dir / "manifest_failure.json").write_text(json.dumps(receipt, indent=2, sort_keys=True)+"\n")
        print(json.dumps({"classification":classification,"failure":failure}))
        return 2


def parse_timestamp_value(value: Any) -> int | None:
    if isinstance(value, (int, float)):
        ts = int(value)
        if ts < 10_000_000_000:
            ts *= 1000
        return ts
    if isinstance(value, str):
        s = value.strip()
        if re.fullmatch(r"\d{10,16}", s):
            ts = int(s)
            if ts < 10_000_000_000:
                ts *= 1000
            return ts
        try:
            dt = datetime.fromisoformat(s.replace("Z", "+00:00"))
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            return int(dt.astimezone(timezone.utc).timestamp() * 1000)
        except Exception:
            return None
    return None


def release_from_payload(obj: dict[str, Any], text: str) -> tuple[int | None, str | None, str | None]:
    candidates: list[tuple[int, str]] = []
    for node in iter_dicts(obj):
        for key, value in node.items():
            if key.lower() in RELEASE_KEYS:
                ts = parse_timestamp_value(value)
                if ts is not None:
                    candidates.append((ts, key))
    in_window = [(ts, key) for ts, key in candidates if START_MS <= ts <= END_MS]
    if in_window:
        ts, key = min(in_window)
        return ts, f"payload:{key}", None
    m = PUBLISHED_RE.search(text)
    if m:
        sec = m.group(3) or "00"
        literal = m.group(0)
        dt = datetime.strptime(f"{m.group(1)} {m.group(2)}:{sec}", "%Y-%m-%d %H:%M:%S").replace(tzinfo=timezone.utc)
        return int(dt.timestamp()*1000), "article_text:Published on", literal
    if candidates:
        ts, key = min(candidates)
        return ts, f"payload:{key}", None
    return None, None, None


def extract_title(obj: dict[str, Any]) -> str:
    titles: list[str] = []
    for node in iter_dicts(obj):
        value = node.get("title")
        if isinstance(value, str) and value.strip():
            titles.append(normalize_text(value))
    return titles[0] if titles else ""


def detail_request(code: str, max_attempts: int = 9) -> tuple[dict[str, Any], int, str, int]:
    last: str | None = None
    for attempt in range(max_attempts):
        try:
            r = SESSION.get(DETAIL_ENDPOINT, params={"articleCode": code}, headers={"Referer": REFERER}, timeout=45)
            status = r.status_code
            if status == 429 or 500 <= status < 600:
                last = f"HTTP {status}"
                if attempt + 1 < max_attempts:
                    retry_after = r.headers.get("Retry-After")
                    try:
                        delay = float(retry_after) if retry_after else min(60.0, 4.0 * (2 ** attempt))
                    except Exception:
                        delay = min(60.0, 4.0 * (2 ** attempt))
                    time.sleep(delay)
                    continue
                raise RuntimeError(last)
            r.raise_for_status()
            raw = r.content
            obj = r.json()
            if not isinstance(obj, dict):
                raise RuntimeError("non-object official detail JSON")
            return obj, status, hashlib.sha256(raw).hexdigest(), attempt
        except Exception as exc:
            last = f"{type(exc).__name__}: {str(exc)[:300]}"
            if attempt + 1 < max_attempts:
                time.sleep(min(30.0, 2.0 * (2 ** attempt)))
    raise RuntimeError(last or "official detail request failed")


def hydrate_one(meta: dict[str, Any]) -> dict[str, Any]:
    code = meta["code"]
    obj, status, raw_sha, retries = detail_request(code)
    data = obj.get("data", obj)
    text = normalize_text(" ".join(collect_strings(data)))
    if not text:
        raise RuntimeError(f"empty canonical article text for {code}")
    payload_codes: set[str] = set()
    for node in iter_dicts(obj):
        for ck in ("code", "articleCode", "articlecode"):
            if node.get(ck):
                payload_codes.add(str(node[ck]).lower())
    release_ms, release_source, release_literal = release_from_payload(obj, text)
    low = text.lower()
    title = extract_title(obj)
    return {
        **meta,
        "http_status": status,
        "response_sha256": raw_sha,
        "request_retries": retries,
        "payload_code_match": code in payload_codes,
        "official_title": title,
        "official_title_nonempty": bool(title),
        "canonical_text_length": len(text),
        "canonical_text_sha256": hashlib.sha256(text.encode()).hexdigest(),
        "official_release_ms": release_ms,
        "official_release_source": release_source,
        "official_release_literal": release_literal,
        "contains_borrowable_asset_phrase": "borrowable asset" in low,
        "contains_cross_margin_phrase": "cross margin" in low,
        "structural_phrase_pass": ("borrowable asset" in low and "cross margin" in low),
    }


def cmd_hydrate(manifest_path: Path, shard: int, out_dir: Path) -> int:
    out_dir.mkdir(parents=True, exist_ok=True)
    manifest = json.loads(manifest_path.read_text())
    items = manifest.get("items", [])
    digest = manifest.get("manifest_sha256")
    assigned = [x for i, x in enumerate(items) if i % SHARD_COUNT == shard]
    resolved: list[dict[str, Any]] = []
    classification = "SHARD_PASS"
    failure: str | None = None
    try:
        if manifest.get("classification") != "MANIFEST_PASS" or manifest.get("shard_count") != SHARD_COUNT:
            raise RuntimeError("invalid V0.4 manifest input")
        core = {k: manifest[k] for k in ("lab_id","phase","upper_cursor","frozen_start_utc","frozen_end_utc","shard_count","items")}
        if stable_json_sha(core) != digest:
            raise RuntimeError("manifest digest mismatch")
        for meta in assigned:
            rec = hydrate_one(meta)
            resolved.append(rec)
            time.sleep(3.0)
    except Exception as exc:
        classification = "SOURCE_ACQUISITION_TECHNICAL_FAILURE"
        failure = f"{type(exc).__name__}: {str(exc)[:1000]}"
    receipt = {
        "lab_id": LAB_ID,
        "phase": "V0_4_DETAIL_HYDRATION_SHARD",
        "classification": classification,
        "shard": shard,
        "shard_count": SHARD_COUNT,
        "manifest_sha256": digest,
        "assigned_codes": len(assigned),
        "resolved_codes": len(resolved),
        "records": resolved,
        "failure": failure,
        "safety": SAFETY,
    }
    path = out_dir / f"shard_{shard}.json"
    path.write_text(json.dumps(receipt, indent=2, sort_keys=True)+"\n")
    print(json.dumps({"classification":classification,"shard":shard,"assigned":len(assigned),"resolved":len(resolved),"failure":failure}))
    return 0 if classification == "SHARD_PASS" else 2


def cmd_aggregate(manifest_path: Path, shards_dir: Path, out_dir: Path) -> int:
    out_dir.mkdir(parents=True, exist_ok=True)
    manifest = json.loads(manifest_path.read_text())
    digest = manifest.get("manifest_sha256")
    expected = {x["code"] for x in manifest.get("items", [])}
    records: list[dict[str, Any]] = []
    shard_receipts: list[dict[str, Any]] = []
    classification = "SOURCE_ACQUISITION_TECHNICAL_FAILURE"
    failure: str | None = None
    try:
        paths = sorted(shards_dir.rglob("shard_*.json"))
        if len(paths) != SHARD_COUNT:
            raise RuntimeError(f"expected {SHARD_COUNT} shard receipts, found {len(paths)}")
        seen_shards: set[int] = set()
        for path in paths:
            sh = json.loads(path.read_text())
            shard_receipts.append({k: sh.get(k) for k in ("shard","classification","assigned_codes","resolved_codes","manifest_sha256","failure")})
            if sh.get("manifest_sha256") != digest:
                raise RuntimeError("shard manifest digest mismatch")
            sid = int(sh.get("shard"))
            if sid in seen_shards:
                raise RuntimeError(f"duplicate shard receipt {sid}")
            seen_shards.add(sid)
            if sh.get("classification") != "SHARD_PASS":
                raise RuntimeError(f"shard {sid} did not pass: {sh.get('failure')}")
            records.extend(sh.get("records", []))
        codes = [x.get("code") for x in records]
        if len(codes) != len(set(codes)):
            raise RuntimeError("duplicate hydrated article code")
        if set(codes) != expected:
            missing = sorted(expected - set(codes))
            extra = sorted(set(codes) - expected)
            raise RuntimeError(f"exact coverage mismatch missing={missing[:10]} extra={extra[:10]}")
        if any(not x.get("payload_code_match") for x in records):
            classification = "PROVENANCE_FAILURE"
            raise RuntimeError("one or more official payload article codes did not match manifest identity")
        if any(not x.get("official_title_nonempty") or int(x.get("canonical_text_length",0)) <= 0 for x in records):
            classification = "PROVENANCE_FAILURE"
            raise RuntimeError("one or more articles lacked official title/canonical text")
        if any(x.get("official_release_ms") is None for x in records):
            classification = "PROVENANCE_FAILURE"
            missing = [x["code"] for x in records if x.get("official_release_ms") is None]
            raise RuntimeError("missing official release provenance for: " + ",".join(missing[:20]))
        if any(not (START_MS <= int(x["official_release_ms"]) <= END_MS) for x in records):
            classification = "PROVENANCE_FAILURE"
            raise RuntimeError("official release timestamp outside frozen window for manifest article")
        by_code = {x["code"]: x for x in records}
        controls = {code: by_code.get(code) for code in POSITIVE_CONTROLS}
        controls_ok = all(
            controls[c]
            and controls[c].get("structural_phrase_pass")
            and datetime.fromtimestamp(int(controls[c]["official_release_ms"])/1000, tz=timezone.utc).year == year
            for c, year in POSITIVE_CONTROLS.items()
        )
        if not controls_ok:
            classification = "PROVENANCE_FAILURE"
            raise RuntimeError("pre-frozen positive controls failed canonical identity/release/structural checks")
        qualifying = [x for x in records if x.get("structural_phrase_pass")]
        years = sorted({datetime.fromtimestamp(int(x["official_release_ms"])/1000, tz=timezone.utc).year for x in qualifying})
        if not ({2023, 2024} <= set(years)):
            classification = "INSUFFICIENT_EVENT_SAMPLE"
            raise RuntimeError("explicit Cross Margin + borrowable asset sample absent from one frozen calendar year")
        classification = "SOURCE_CENSUS_PASS"
        failure = None
    except Exception as exc:
        if classification not in {"PROVENANCE_FAILURE", "INSUFFICIENT_EVENT_SAMPLE"}:
            classification = "SOURCE_ACQUISITION_TECHNICAL_FAILURE"
        failure = f"{type(exc).__name__}: {str(exc)[:2000]}"
        controls = {}
        qualifying = []
        years = []
    receipt = {
        "lab_id": LAB_ID,
        "phase": "SOURCE_CENSUS_V0_4_CANONICAL_AGGREGATION",
        "classification": classification,
        "manifest_sha256": digest,
        "manifest_codes": len(expected),
        "hydrated_records": len(records),
        "shards": shard_receipts,
        "positive_controls": controls,
        "qualifying_cross_margin_borrowable_articles": len(qualifying),
        "years_with_structural_phrase": years,
        "failure": failure,
        "index_receipt": {
            "upper_cursor": manifest.get("upper_cursor"),
            "page_count": manifest.get("page_count"),
            "total_messages_in_frozen_window": manifest.get("total_messages_in_frozen_window"),
            "total_support_links_in_frozen_window": manifest.get("total_support_links_in_frozen_window"),
            "enumeration_boundary_reached_before_start": manifest.get("enumeration_boundary_reached_before_start"),
            "protected_period_seen": manifest.get("protected_period_seen"),
        },
        "resolved_articles": records,
        "safety": SAFETY,
    }
    path = out_dir / "BINANCE_MARGIN_BORROW_ACCESS_001_SOURCE_CENSUS_RECEIPT_V0_4.json"
    path.write_text(json.dumps(receipt, indent=2, sort_keys=True)+"\n")
    print(json.dumps({
        "lab_id":LAB_ID,"classification":classification,"manifest_codes":len(expected),
        "hydrated_records":len(records),"qualifying_articles":len(qualifying),
        "years_with_structural_phrase":years,"failure":failure,
        "prices_opened":False,"returns_opened":False,"pnl_opened":False,
    }, sort_keys=True))
    return 0 if classification == "SOURCE_CENSUS_PASS" else 2


def main() -> int:
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("manifest"); p.add_argument("--out", type=Path, required=True)
    p = sub.add_parser("hydrate"); p.add_argument("--manifest", type=Path, required=True); p.add_argument("--shard", type=int, required=True); p.add_argument("--out", type=Path, required=True)
    p = sub.add_parser("aggregate"); p.add_argument("--manifest", type=Path, required=True); p.add_argument("--shards", type=Path, required=True); p.add_argument("--out", type=Path, required=True)
    a = ap.parse_args()
    if a.cmd == "manifest": return cmd_manifest(a.out)
    if a.cmd == "hydrate":
        if not 0 <= a.shard < SHARD_COUNT: raise SystemExit("invalid shard")
        return cmd_hydrate(a.manifest, a.shard, a.out)
    return cmd_aggregate(a.manifest, a.shards, a.out)


if __name__ == "__main__":
    sys.exit(main())
