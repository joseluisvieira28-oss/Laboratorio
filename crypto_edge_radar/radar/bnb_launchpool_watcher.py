from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import hashlib
import html
import json
import re
import time
from typing import Any, Iterable
from urllib.error import HTTPError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from .evidence import EvidenceStore, PostgresEvidenceStore
from .strategies.bnb_launchpool_demand import (
    BASE_COST_BPS,
    STRESS_COST_BPS,
    FORWARD_BOUNDARY_MS,
    BinanceSpotBNBBTCKlineFeed,
    BNBLaunchpoolSourceError,
    bind_prospective_event,
    exact_exit_open_ms,
    first_eligible_entry_open_ms,
)

Store = EvidenceStore | PostgresEvidenceStore
BINANCE_CMS_BASE = "https://www.binance.com"
CATALOG_PATH = "/bapi/composite/v1/public/cms/article/catalog/list/query"
DETAIL_PATH = "/bapi/composite/v1/public/cms/article/detail/query"
CATALOG_ID = 48
PAGE_SIZE = 50
CLUSTER_MS = 60 * 60 * 1000
FROZEN_DETAIL_PROBE_CODE = "73d44e64598c446cb4ec2f83b776c2f0"
MISSED_PROSPECTIVE_EVENT = "BNB_FORWARD_MISSED_PROSPECTIVE_OBSERVATION"


@dataclass(frozen=True)
class LaunchpoolAnnouncement:
    article_code: str
    title: str
    published_ms: int
    published_utc: str
    detail_sha256: str


def _utc_iso(ms: int) -> str:
    return datetime.fromtimestamp(ms / 1000.0, tz=timezone.utc).isoformat().replace("+00:00", "Z")


def _walk(obj: Any):
    if isinstance(obj, dict):
        for key, value in obj.items():
            yield str(key), value
            yield from _walk(value)
    elif isinstance(obj, list):
        for value in obj:
            yield from _walk(value)


def _flatten_text(obj: Any) -> str:
    chunks = [str(v) for _, v in _walk(obj) if isinstance(v, str)]
    raw = "\n".join(chunks)
    raw = html.unescape(re.sub(r"<[^>]+>", " ", raw))
    return re.sub(r"\s+", " ", raw).strip()


def _parse_timestamp_ms(value: Any) -> int | None:
    if value is None or isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        x = float(value)
        if x > 1e14:
            x /= 1_000.0
        elif x < 1e11:
            x *= 1_000.0
        try:
            return int(x)
        except Exception:
            return None
    text = str(value).strip()
    if not text:
        return None
    if re.fullmatch(r"\d{10,18}", text):
        return _parse_timestamp_ms(int(text))
    try:
        dt = datetime.fromisoformat(text.replace("Z", "+00:00"))
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return int(dt.astimezone(timezone.utc).timestamp() * 1000)
    except Exception:
        return None


def _find_original_publication_ms(obj: Any) -> int | None:
    priority = (
        "releasedate",
        "release_time",
        "releasetime",
        "publishdate",
        "publish_date",
        "publishtime",
        "publish_time",
        "publishedat",
        "published_at",
        "publicationdate",
    )
    found: list[tuple[int, int]] = []
    for key, value in _walk(obj):
        normalized = key.lower().split("[")[0]
        if normalized in priority:
            ts = _parse_timestamp_ms(value)
            if ts is not None:
                found.append((priority.index(normalized), ts))
    if not found:
        return None
    found.sort(key=lambda item: (item[0], item[1]))
    return found[0][1]


def _article_code_from_dict(row: dict[str, Any]) -> str | None:
    for key in ("articleCode", "article_code", "code"):
        value = row.get(key)
        if isinstance(value, str) and re.fullmatch(r"[0-9a-fA-F]{32}", value.strip()):
            return value.strip().lower()
    return None


def _candidate_rows(obj: Any) -> list[tuple[str, str]]:
    found: dict[str, str] = {}

    def visit(node: Any) -> None:
        if isinstance(node, dict):
            code = _article_code_from_dict(node)
            title = node.get("title")
            if code and isinstance(title, str) and "launchpool" in title.lower():
                found[code] = title.strip()
            for value in node.values():
                visit(value)
        elif isinstance(node, list):
            for value in node:
                visit(value)

    visit(obj)
    return sorted(found.items())


def _cluster_announcements(events: Iterable[LaunchpoolAnnouncement]) -> list[list[LaunchpoolAnnouncement]]:
    ordered = sorted(events, key=lambda event: (event.published_ms, event.article_code))
    clusters: list[list[LaunchpoolAnnouncement]] = []
    for event in ordered:
        if not clusters or event.published_ms - clusters[-1][-1].published_ms > CLUSTER_MS:
            clusters.append([event])
        else:
            clusters[-1].append(event)
    return clusters


def _cluster_key(cluster: list[LaunchpoolAnnouncement]) -> str:
    anchor = cluster[0]
    return f"BNB-LAUNCHPOOL-DEMAND-001:{anchor.article_code}:{anchor.published_ms}"


class BinanceOfficialLaunchpoolSource:
    """Official Binance Support/CMS GET-only discovery surface."""

    provider = "BINANCE_SUPPORT_CMS_PUBLIC"

    def __init__(self, timeout: int = 15) -> None:
        self.timeout = timeout

    def _get(self, path: str, query: dict[str, Any]) -> tuple[Any, bytes]:
        url = f"{BINANCE_CMS_BASE}{path}?{urlencode(query)}"
        request = Request(
            url,
            method="GET",
            headers={
                "User-Agent": "Mozilla/5.0 crypto-edge-radar/0.9 bnb-launchpool-shadow",
                "Accept": "application/json,text/plain,*/*",
                "Accept-Language": "en-US,en;q=0.9",
            },
        )
        body: bytes | None = None
        last_error: Exception | None = None
        for attempt in range(3):
            try:
                with urlopen(request, timeout=self.timeout) as response:
                    body = response.read()
                    if response.status != 200 or not body:
                        raise BNBLaunchpoolSourceError(
                            f"Binance CMS HTTP/empty response:{response.status}"
                        )
                    break
            except HTTPError as exc:
                last_error = exc
                if exc.code != 429 and exc.code < 500:
                    break
                if attempt < 2:
                    retry_after = exc.headers.get("Retry-After") if exc.headers else None
                    try:
                        delay = min(5.0, max(0.5, float(retry_after))) if retry_after else float(attempt + 1)
                    except (TypeError, ValueError):
                        delay = float(attempt + 1)
                    time.sleep(delay)
            except Exception as exc:
                last_error = exc
                if attempt < 2:
                    time.sleep(float(attempt + 1))
                    continue
                break
        if not body:
            exc = last_error or BNBLaunchpoolSourceError("Binance CMS returned empty response")
            if isinstance(exc, BNBLaunchpoolSourceError):
                raise exc
            raise BNBLaunchpoolSourceError(
                f"Binance CMS source unavailable:{type(exc).__name__}:{exc}"
            ) from exc
        try:
            return json.loads(body.decode("utf-8")), body
        except Exception as exc:
            raise BNBLaunchpoolSourceError("Binance CMS returned non-JSON bytes") from exc

    def catalog(self) -> tuple[Any, bytes]:
        return self._get(
            CATALOG_PATH,
            {"catalogId": CATALOG_ID, "pageNo": 1, "pageSize": PAGE_SIZE},
        )

    def detail(self, article_code: str) -> tuple[Any, bytes]:
        if not re.fullmatch(r"[0-9a-f]{32}", article_code):
            raise BNBLaunchpoolSourceError("invalid Binance article code")
        return self._get(DETAIL_PATH, {"articleCode": article_code})

    def validate_detail(
        self,
        *,
        article_code: str,
        fallback_title: str,
        now_ms: int,
        require_post_boundary: bool = True,
    ) -> LaunchpoolAnnouncement | None:
        obj, raw = self.detail(article_code)
        text = _flatten_text(obj)
        lower = text.lower()
        if article_code not in lower:
            raise BNBLaunchpoolSourceError(f"article identity missing from official detail:{article_code}")
        if "launchpool" not in lower:
            return None
        if re.search(r"\bbnb\b", lower) is None:
            return None
        if not any(term in lower for term in ("stake", "staking", "lock", "locking", "farm", "farming")):
            return None
        published_ms = _find_original_publication_ms(obj)
        if published_ms is None:
            raise BNBLaunchpoolSourceError(f"canonical publication timestamp missing:{article_code}")
        if published_ms > now_ms + 5 * 60_000:
            raise BNBLaunchpoolSourceError(f"future-dated Binance publication timestamp:{article_code}")
        if require_post_boundary and published_ms <= FORWARD_BOUNDARY_MS:
            return None
        title = fallback_title
        for key, value in _walk(obj):
            if key.lower() == "title" and isinstance(value, str) and "launchpool" in value.lower():
                title = value.strip()
                break
        return LaunchpoolAnnouncement(
            article_code=article_code,
            title=title,
            published_ms=published_ms,
            published_utc=_utc_iso(published_ms),
            detail_sha256=hashlib.sha256(raw).hexdigest(),
        )

    def discover_eligible(self, *, now_ms: int) -> list[LaunchpoolAnnouncement]:
        catalog_obj, _raw = self.catalog()
        candidates = _candidate_rows(catalog_obj)
        events: dict[tuple[str, int], LaunchpoolAnnouncement] = {}
        for code, title in candidates:
            event = self.validate_detail(
                article_code=code,
                fallback_title=title,
                now_ms=now_ms,
                require_post_boundary=True,
            )
            if event is not None:
                events[(event.article_code, event.published_ms)] = event
        return sorted(events.values(), key=lambda event: (event.published_ms, event.article_code))

    def source_probe(self, *, now_ms: int) -> dict[str, Any]:
        catalog_obj, catalog_raw = self.catalog()
        candidates = _candidate_rows(catalog_obj)
        probe_obj, probe_raw = self.detail(FROZEN_DETAIL_PROBE_CODE)
        probe_text = _flatten_text(probe_obj).lower()
        probe_pub = _find_original_publication_ms(probe_obj)
        if FROZEN_DETAIL_PROBE_CODE not in probe_text:
            raise BNBLaunchpoolSourceError("fixed detail probe identity mismatch")
        if "launchpool" not in probe_text or re.search(r"\bbnb\b", probe_text) is None:
            raise BNBLaunchpoolSourceError("fixed detail probe no longer exposes frozen Launchpool/BNB evidence")
        if probe_pub is None:
            raise BNBLaunchpoolSourceError("fixed detail probe publication timestamp missing")
        return {
            "status": "PASS_SOURCE_ONLY",
            "provider": self.provider,
            "catalog_path": CATALOG_PATH,
            "detail_path": DETAIL_PATH,
            "catalog_id": CATALOG_ID,
            "catalog_sha256": hashlib.sha256(catalog_raw).hexdigest(),
            "launchpool_candidates_on_current_page": len(candidates),
            "fixed_detail_probe_code": FROZEN_DETAIL_PROBE_CODE,
            "fixed_detail_probe_sha256": hashlib.sha256(probe_raw).hexdigest(),
            "fixed_detail_probe_published_utc": _utc_iso(probe_pub),
            "authenticated_exchange_api_used": False,
            "order_created": False,
            "exchange_mutation_performed": False,
        }


class BNBLaunchpoolForwardShadowWatcher:
    watcher_id = "BNB-LAUNCHPOOL-DEMAND-001-FORWARD-SHADOW-V3"

    def __init__(
        self,
        *,
        store: Store,
        source: BinanceOfficialLaunchpoolSource | None = None,
        market: BinanceSpotBNBBTCKlineFeed | None = None,
    ) -> None:
        self.store = store
        self.source = source or BinanceOfficialLaunchpoolSource()
        self.market = market or BinanceSpotBNBBTCKlineFeed()

    def run_once(self, *, now_ms: int | None = None) -> dict[str, Any]:
        if now_ms is None:
            now_ms = int(datetime.now(timezone.utc).timestamp() * 1000)
        events = self.source.discover_eligible(now_ms=now_ms)
        clusters = _cluster_announcements(events)
        inserted_events = 0
        duplicate_events = 0
        inserted_selections = 0
        duplicate_selections = 0
        inserted_suppressions = 0
        duplicate_suppressions = 0
        inserted_resolutions = 0
        duplicate_resolutions = 0
        inserted_missed_observations = 0
        duplicate_missed_observations = 0
        active_exit_ms: int | None = None
        existing_events = {
            str(payload.get("event_key")): payload
            for payload in self.store.read_payloads("BNB_FORWARD_ELIGIBLE_EVENT")
            if payload.get("event_key")
        }

        for cluster in clusters:
            anchor = cluster[0]
            key = _cluster_key(cluster)
            theoretical_entry = first_eligible_entry_open_ms(anchor.published_ms)
            theoretical_exit = exact_exit_open_ms(theoretical_entry)
            event_payload = {
                "watcher_id": self.watcher_id,
                "mode": "PUBLIC_SHADOW_ONLY",
                "event_key": key,
                "signal_article_code": anchor.article_code,
                "signal_timestamp_utc": anchor.published_utc,
                "cluster_article_codes": [event.article_code for event in cluster],
                "cluster_publication_timestamps_utc": [event.published_utc for event in cluster],
                "cluster_size": len(cluster),
                "detail_sha256": {event.article_code: event.detail_sha256 for event in cluster},
                "theoretical_entry_open_ms": theoretical_entry,
                "theoretical_exit_open_ms": theoretical_exit,
                "first_observed_at_utc": _utc_iso(now_ms),
                "observed_before_frozen_entry_open": now_ms < theoretical_entry,
                "authenticated_exchange_api_used": False,
                "order_created": False,
                "exchange_mutation_performed": False,
            }
            previously_observed = key in existing_events
            if not previously_observed and now_ms >= theoretical_entry:
                missed_payload = {
                    **event_payload,
                    "reason": "FIRST_OBSERVATION_OCCURRED_AT_OR_AFTER_FROZEN_ENTRY_OPEN",
                    "late_reconstruction_forbidden": True,
                    "used_as_forward_trade_evidence": False,
                }
                missed = self.store.append_once(MISSED_PROSPECTIVE_EVENT, key, missed_payload)
                if missed["inserted"]:
                    inserted_missed_observations += 1
                else:
                    duplicate_missed_observations += 1
                continue

            receipt = self.store.append_once("BNB_FORWARD_ELIGIBLE_EVENT", key, event_payload)
            if receipt["inserted"]:
                inserted_events += 1
                existing_events[key] = event_payload
            else:
                duplicate_events += 1

            if active_exit_ms is not None and theoretical_entry < active_exit_ms:
                suppression = self.store.append_once(
                    "BNB_FORWARD_OVERLAP_SUPPRESSED",
                    key,
                    {
                        **event_payload,
                        "reason": "ONE_ACTIVE_TRADE_FROZEN_RULE",
                        "active_exit_ms": active_exit_ms,
                    },
                )
                if suppression["inserted"]:
                    inserted_suppressions += 1
                else:
                    duplicate_suppressions += 1
                continue

            active_exit_ms = theoretical_exit
            binding = bind_prospective_event(
                self.market,
                signal_timestamp_ms=anchor.published_ms,
                now_ms=now_ms,
            )
            if binding["status"] == "WAITING_ENTRY_BAR_FULLY_AVAILABLE":
                continue

            selection = self.store.append_once(
                "BNB_FORWARD_PAPER_SELECTION",
                key,
                {
                    **event_payload,
                    "binding": binding,
                },
            )
            if selection["inserted"]:
                inserted_selections += 1
            else:
                duplicate_selections += 1

            if binding["status"] != "RESOLVED_MARKET_BINDING":
                continue
            entry = float(binding["entry_price"])
            exit_price = float(binding["exit_price"])
            gross_bps = (exit_price / entry - 1.0) * 10_000.0
            resolution_payload = {
                **event_payload,
                "binding": binding,
                "gross_return_bps": gross_bps,
                "base_net_bps": gross_bps - BASE_COST_BPS,
                "stress_net_bps": gross_bps - STRESS_COST_BPS,
            }
            resolution = self.store.append_once("BNB_FORWARD_RESOLUTION", key, resolution_payload)
            if resolution["inserted"]:
                inserted_resolutions += 1
            else:
                duplicate_resolutions += 1

        return {
            "watcher_id": self.watcher_id,
            "status": "OK",
            "mode": "PUBLIC_SHADOW_ONLY",
            "official_source_provider": self.source.provider,
            "market_provider": self.market.provider,
            "eligible_events_visible": len(events),
            "clusters_visible": len(clusters),
            "inserted_events": inserted_events,
            "duplicate_events": duplicate_events,
            "inserted_selections": inserted_selections,
            "duplicate_selections": duplicate_selections,
            "inserted_suppressions": inserted_suppressions,
            "duplicate_suppressions": duplicate_suppressions,
            "inserted_resolutions": inserted_resolutions,
            "duplicate_resolutions": duplicate_resolutions,
            "inserted_missed_observations": inserted_missed_observations,
            "duplicate_missed_observations": duplicate_missed_observations,
            "missed_prospective_observation_count": len(
                self.store.read_payloads(MISSED_PROSPECTIVE_EVENT)
            ),
            "no_chase_after_missed_entry": True,
            "evidence_backend": self.store.backend,
            "authenticated_exchange_api_used": False,
            "order_created": False,
            "exchange_mutation_performed": False,
        }

    def run_forever(self, *, interval_seconds: float = 300.0) -> None:
        if interval_seconds < 30:
            raise ValueError("BNB watcher interval must be >=30 seconds")
        while True:
            self.run_once()
            time.sleep(interval_seconds)
