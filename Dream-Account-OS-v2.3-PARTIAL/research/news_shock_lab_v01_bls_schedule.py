from __future__ import annotations

from datetime import date, datetime, timezone
import hashlib
import json
from pathlib import Path
import re
import time
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen
from zoneinfo import ZoneInfo

from bs4 import BeautifulSoup

FREEZE_PATH = Path(__file__).with_name("NEWS_SHOCK_LAB_V01_CPI_NFP_REPLICATION_FREEZE.json")
EXPECTED_FREEZE_FINGERPRINT = "55bba04ab42e1c457427a9ba87231c6ff4df52e9f0e083e320700618c38b2f70"
NY = ZoneInfo("America/New_York")
DATE_FMT = "%A, %B %d, %Y"
TARGETS = (
    ("Consumer Price Index", "CPI"),
    ("Employment Situation", "NFP"),
)


def canonical_hash(obj: object) -> str:
    return hashlib.sha256(
        json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()
    ).hexdigest()


def load_freeze() -> dict:
    raw = json.loads(FREEZE_PATH.read_text(encoding="utf-8"))
    supplied = raw.get("fingerprint")
    unsigned = dict(raw)
    unsigned.pop("fingerprint", None)
    if supplied != EXPECTED_FREEZE_FINGERPRINT:
        raise PermissionError("V0.1 freeze fingerprint mismatch")
    if canonical_hash(unsigned) != supplied:
        raise PermissionError("V0.1 freeze canonical hash mismatch")
    if raw["governance"]["no_2026"] is not True:
        raise PermissionError("2026 guard drift")
    return raw


def fetch_text(url: str) -> str:
    last: Exception | None = None
    for attempt in range(1, 5):
        try:
            req = Request(
                url,
                headers={
                    "User-Agent": "DreamAccountOS-NewsShockLab/0.1 research-only contact",
                    "Accept": "text/html,application/xhtml+xml",
                },
            )
            with urlopen(req, timeout=45) as response:
                if response.status != 200:
                    raise RuntimeError(f"HTTP {response.status}")
                raw = response.read()
            if not raw:
                raise RuntimeError("empty BLS response")
            return raw.decode("utf-8", errors="replace")
        except (HTTPError, URLError, TimeoutError, OSError, RuntimeError) as exc:
            last = exc
            if attempt < 4:
                time.sleep(min(2 ** attempt, 8))
    raise RuntimeError(f"BLS fetch failed: {url}: {last}")


def _parse_date(text: str) -> date:
    normalized = re.sub(r"\s+", " ", text).strip()
    return datetime.strptime(normalized, DATE_FMT).date()


def extract_events_from_html(html: str, source_url: str, start: date, end: date) -> list[dict]:
    soup = BeautifulSoup(html, "html.parser")
    events: list[dict] = []
    for tr in soup.find_all("tr"):
        cells = [re.sub(r"\s+", " ", cell.get_text(" ", strip=True)).strip() for cell in tr.find_all(["th", "td"])]
        if len(cells) < 3:
            continue
        date_text, time_text = cells[0], cells[1]
        release_text = " ".join(cells[2:]).strip()
        if time_text != "08:30 AM":
            continue
        event_type = None
        source_prefix = None
        for prefix, label in TARGETS:
            if release_text.startswith(prefix):
                event_type = label
                source_prefix = prefix
                break
        if event_type is None:
            continue
        try:
            d = _parse_date(date_text)
        except ValueError:
            continue
        if not start <= d <= end:
            continue
        local_dt = datetime(d.year, d.month, d.day, 8, 30, tzinfo=NY)
        utc_dt = local_dt.astimezone(timezone.utc)
        events.append(
            {
                "event_type": event_type,
                "release_name": release_text,
                "release_prefix": source_prefix,
                "event_date": d.isoformat(),
                "release_time_et": "08:30 AM",
                "release_timezone": "America/New_York",
                "release_utc": utc_dt.isoformat().replace("+00:00", "Z"),
                "source_url": source_url,
            }
        )
    return events


def build_manifest(output_path: Path | None = None) -> dict:
    freeze = load_freeze()
    ec = freeze["event_contract"]
    start = date.fromisoformat(ec["start_date_inclusive"])
    end = date.fromisoformat(ec["end_date_inclusive"])
    events: list[dict] = []
    source_receipts: list[dict] = []
    for url in ec["source_urls"]:
        html = fetch_text(url)
        digest = hashlib.sha256(html.encode("utf-8")).hexdigest()
        extracted = extract_events_from_html(html, url, start, end)
        events.extend(extracted)
        source_receipts.append(
            {
                "source_url": url,
                "html_text_sha256": digest,
                "selected_event_count": len(extracted),
            }
        )
    unique: dict[tuple[str, str], dict] = {}
    for event in events:
        key = (event["event_type"], event["event_date"])
        if key in unique:
            raise RuntimeError(f"duplicate BLS event {key}")
        unique[key] = event
    final = sorted(unique.values(), key=lambda x: (x["event_date"], x["event_type"]))
    counts = {label: sum(e["event_type"] == label for e in final) for label in ("CPI", "NFP")}
    expected_each = int(ec["expected_events_per_type"])
    expected_total = int(ec["expected_total_events"])
    if counts != {"CPI": expected_each, "NFP": expected_each}:
        raise RuntimeError(f"BLS cardinality block: {counts}, expected {expected_each} each")
    if len(final) != expected_total:
        raise RuntimeError(f"BLS total cardinality block: {len(final)} != {expected_total}")
    if any(e["event_date"].startswith("2026-") for e in final):
        raise RuntimeError("2026 event guard violation")
    body = {
        "document_type": "NEWS_SHOCK_LAB_V01_BLS_SCHEDULE_MANIFEST",
        "version": "0.1",
        "status": "OFFICIAL_BLS_SCHEDULE_MANIFEST_COMPLETE",
        "freeze_fingerprint": EXPECTED_FREEZE_FINGERPRINT,
        "selection_rule": ec["selection_rule"],
        "window": {"start": start.isoformat(), "end": end.isoformat()},
        "event_counts": counts,
        "event_count_total": len(final),
        "source_receipts": source_receipts,
        "events": final,
        "guards": {
            "market_data_accessed": False,
            "outcomes_evaluated": False,
            "holdout_2026_accessed": False,
            "live_trading_authorized": False,
        },
    }
    body["fingerprint"] = canonical_hash(body)
    if output_path is not None:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(json.dumps(body, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return body


if __name__ == "__main__":
    import sys
    if len(sys.argv) != 2:
        raise SystemExit("usage: news_shock_lab_v01_bls_schedule <manifest.json>")
    manifest = build_manifest(Path(sys.argv[1]))
    print(json.dumps({
        "status": manifest["status"],
        "event_counts": manifest["event_counts"],
        "event_count_total": manifest["event_count_total"],
        "fingerprint": manifest["fingerprint"],
        "guards": manifest["guards"],
    }, indent=2, sort_keys=True))
