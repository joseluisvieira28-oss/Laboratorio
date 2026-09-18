from __future__ import annotations

import hashlib
import html
import json
import re
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

BOUNDARY = datetime.fromisoformat("2026-09-16T20:51:23+00:00")
LIST_URL = (
    "https://www.binance.com/bapi/composite/v1/public/cms/article/list/query"
    "?type=1&catalogId=48&pageNo=1&pageSize=50"
)
DETAIL_URL = "https://www.binance.com/bapi/composite/v1/public/cms/article/detail/query?articleCode={}"
UA = {
    "User-Agent": "Mozilla/5.0 BNB-LAUNCHPOOL-DEMAND-001-FORWARD-PREFLIGHT/1.0",
    "Accept": "application/json,text/plain,*/*",
    "Accept-Language": "en-US,en;q=0.9",
    "clienttype": "web",
}

HERE = Path(__file__).resolve().parent
OUT = HERE / "BNB_LAUNCHPOOL_DEMAND_001_V3_FORWARD_SOURCE_PREFLIGHT_RECEIPT_V0.1.json"


def canonical_hash(obj: Any) -> str:
    return hashlib.sha256(
        json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    ).hexdigest()


def parse_ts(v: Any) -> datetime | None:
    if v is None or isinstance(v, bool):
        return None
    if isinstance(v, (int, float)):
        x = float(v)
        if x > 1e14:
            x /= 1_000_000.0
        elif x > 1e11:
            x /= 1_000.0
        try:
            return datetime.fromtimestamp(x, tz=timezone.utc)
        except Exception:
            return None
    s = str(v).strip()
    if not s:
        return None
    if re.fullmatch(r"\d{10,18}", s):
        return parse_ts(int(s))
    try:
        dt = datetime.fromisoformat(s.replace("Z", "+00:00"))
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(timezone.utc)
    except Exception:
        return None


def iso(dt: datetime | None) -> str | None:
    if dt is None:
        return None
    return dt.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def fetch_json(url: str) -> tuple[bytes, dict]:
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=35) as r:
        body = r.read()
        if getattr(r, "status", 200) != 200:
            raise RuntimeError(f"HTTP_STATUS_{getattr(r, 'status', None)}")
    return body, json.loads(body.decode("utf-8"))


def walk(obj: Any):
    if isinstance(obj, dict):
        for k, v in obj.items():
            yield str(k), v
            yield from walk(v)
    elif isinstance(obj, list):
        for v in obj:
            yield from walk(v)


def flatten_text(obj: Any) -> str:
    chunks = [v for _, v in walk(obj) if isinstance(v, str)]
    raw = html.unescape(re.sub(r"<[^>]+>", " ", "\n".join(chunks)))
    return re.sub(r"\s+", " ", raw).strip()


def first_value(d: dict, keys: tuple[str, ...]):
    for k in keys:
        if k in d and d[k] not in (None, ""):
            return d[k]
    return None


def article_ts(a: dict) -> datetime | None:
    direct = first_value(
        a,
        (
            "releaseDate", "releaseTime", "publishDate", "publishTime",
            "publishedAt", "publicationDate", "date",
        ),
    )
    if direct is not None:
        return parse_ts(direct)
    for k, v in walk(a):
        lk = k.lower()
        if lk in {
            "releasedate", "releasetime", "publishdate", "publishtime",
            "publishedat", "publicationdate"
        }:
            t = parse_ts(v)
            if t is not None:
                return t
    return None


def article_code(a: dict) -> str | None:
    for key in ("code", "articleCode", "article_code"):
        v = a.get(key)
        if isinstance(v, str) and re.fullmatch(r"[0-9a-fA-F]{32}", v):
            return v.lower()
    for _, v in walk(a):
        if isinstance(v, str):
            m = re.search(r"/detail/([0-9a-fA-F]{32})", v)
            if m:
                return m.group(1).lower()
    return None


def article_title(a: dict) -> str:
    v = first_value(a, ("title", "articleTitle", "name"))
    return str(v or "").strip()


def extract_articles(obj: dict) -> list[dict]:
    data = obj.get("data") if isinstance(obj, dict) else None
    if not isinstance(data, dict):
        return []
    if isinstance(data.get("articles"), list):
        return [x for x in data["articles"] if isinstance(x, dict)]
    out: list[dict] = []
    catalogs = data.get("catalogs")
    if isinstance(catalogs, list):
        for cat in catalogs:
            if isinstance(cat, dict) and isinstance(cat.get("articles"), list):
                out.extend(x for x in cat["articles"] if isinstance(x, dict))
    return out


def main() -> int:
    receipt = {
        "document_id": "BNB_LAUNCHPOOL_DEMAND_001_V3_FORWARD_SOURCE_PREFLIGHT_RECEIPT_V0.1",
        "boundary_utc": iso(BOUNDARY),
        "source_list_url": LIST_URL,
        "classification": None,
        "post_boundary_articles_seen": 0,
        "launchpool_title_candidates": 0,
        "eligible_events": [],
        "noneligible_post_boundary_articles": [],
        "ambiguous_candidates": [],
        "price_firewall": {
            "market_data_access": False,
            "BNBBTC_price_access": False,
            "returns": False,
            "pnl": False,
            "orders": False,
            "wallets": False,
            "authenticated_exchange": False,
        },
    }
    try:
        list_body, obj = fetch_json(LIST_URL)
        receipt["list_response_sha256"] = hashlib.sha256(list_body).hexdigest()
        articles = extract_articles(obj)
        if not articles:
            raise RuntimeError("NO_ARTICLES_PARSED_FROM_OFFICIAL_CMS_LIST")

        for a in articles:
            t = article_ts(a)
            if t is None:
                # Do not open detail when the list itself cannot prove the article is post-boundary.
                receipt["ambiguous_candidates"].append({
                    "title": article_title(a),
                    "reason": "LIST_PUBLICATION_TIMESTAMP_UNAVAILABLE",
                })
                continue
            if t <= BOUNDARY:
                continue

            title = article_title(a)
            code = article_code(a)
            receipt["post_boundary_articles_seen"] += 1

            # The frozen event source is a Launchpool announcement, not any article
            # that incidentally mentions Launchpool in its body.
            if "launchpool" not in title.lower():
                receipt["noneligible_post_boundary_articles"].append({
                    "title": title,
                    "list_published_utc": iso(t),
                    "reason": "TITLE_NOT_LAUNCHPOOL_ANNOUNCEMENT",
                })
                continue

            receipt["launchpool_title_candidates"] += 1
            if code is None:
                receipt["ambiguous_candidates"].append({
                    "title": title,
                    "list_published_utc": iso(t),
                    "reason": "CANONICAL_ARTICLE_CODE_UNAVAILABLE",
                })
                continue

            body, detail = fetch_json(DETAIL_URL.format(code))
            text = flatten_text(detail)
            tl = text.lower()
            detail_t = article_ts(detail)
            if detail_t is None:
                receipt["ambiguous_candidates"].append({
                    "title": title,
                    "article_code": code,
                    "reason": "DETAIL_PUBLICATION_TIMESTAMP_UNAVAILABLE",
                    "detail_sha256": hashlib.sha256(body).hexdigest(),
                })
                continue
            if detail_t <= BOUNDARY:
                receipt["ambiguous_candidates"].append({
                    "title": title,
                    "article_code": code,
                    "reason": "LIST_DETAIL_TIMESTAMP_BOUNDARY_CONFLICT",
                    "list_published_utc": iso(t),
                    "detail_published_utc": iso(detail_t),
                    "detail_sha256": hashlib.sha256(body).hexdigest(),
                })
                continue

            launchpool = "launchpool" in tl
            bnb = re.search(r"\bbnb\b", tl) is not None
            utility = any(k in tl for k in ("stake", "staking", "lock", "locking", "farm", "farming"))
            event = {
                "title": title,
                "article_code": code,
                "published_timestamp_utc": iso(detail_t),
                "official_support_url": f"https://www.binance.com/en/support/announcement/detail/{code}",
                "detail_sha256": hashlib.sha256(body).hexdigest(),
                "launchpool_text_present": launchpool,
                "bnb_text_present": bnb,
                "staking_or_locking_or_farming_text_present": utility,
            }
            if launchpool and bnb and utility:
                receipt["eligible_events"].append(event)
            else:
                event["reason"] = "FROZEN_ELIGIBILITY_TEXT_GATE_FAIL"
                receipt["noneligible_post_boundary_articles"].append(event)

        if receipt["ambiguous_candidates"]:
            receipt["classification"] = "SOURCE_PREFLIGHT_AMBIGUOUS"
        elif receipt["eligible_events"]:
            receipt["classification"] = "SOURCE_PREFLIGHT_PASS_ELIGIBLE_EVENT_FOUND"
        else:
            receipt["classification"] = "SOURCE_PREFLIGHT_PASS_NO_ELIGIBLE_EVENT"
    except Exception as e:
        receipt["classification"] = "SOURCE_PREFLIGHT_BLOCKED"
        receipt["error"] = f"{type(e).__name__}:{e}"

    clone = dict(receipt)
    receipt["fingerprint"] = canonical_hash(clone)
    OUT.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({
        "classification": receipt["classification"],
        "post_boundary_articles_seen": receipt["post_boundary_articles_seen"],
        "launchpool_title_candidates": receipt["launchpool_title_candidates"],
        "eligible_event_count": len(receipt["eligible_events"]),
        "ambiguous_count": len(receipt["ambiguous_candidates"]),
        "fingerprint": receipt["fingerprint"],
    }, indent=2))
    return 0 if receipt["classification"].startswith("SOURCE_PREFLIGHT_PASS") else 2


if __name__ == "__main__":
    raise SystemExit(main())
