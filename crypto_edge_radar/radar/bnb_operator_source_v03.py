from __future__ import annotations

from datetime import datetime, timezone
import json
from pathlib import Path
from typing import Any

from .bnb_launchpool_watcher import (
    BinanceOfficialLaunchpoolSource,
    _cluster_announcements,
    _cluster_key,
)
from .strategies.bnb_launchpool_demand import (
    exact_exit_open_ms,
    first_eligible_entry_open_ms,
)

CANDIDATE_ID = "BNB-LAUNCHPOOL-DEMAND-001"
SYMBOL = "BNB_USDT"
MAX_LATE_SECONDS = 2.0


def _iso_ms(ms: int) -> str:
    return (
        datetime.fromtimestamp(ms / 1000.0, tz=timezone.utc)
        .isoformat()
        .replace("+00:00", "Z")
    )


def _atomic_write(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(
        json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    tmp.replace(path)


def _build_signal(cluster: list[Any]) -> dict[str, Any]:
    anchor = cluster[0]
    key = _cluster_key(cluster)
    entry_ms = first_eligible_entry_open_ms(anchor.published_ms)
    exit_ms = exact_exit_open_ms(entry_ms)
    return {
        "candidate_id": CANDIDATE_ID,
        "strategy_id": CANDIDATE_ID,
        "immutable_signal_key": key,
        "source": "BINANCE_SUPPORT_CMS_PUBLIC",
        "signal_article_code": anchor.article_code,
        "cluster_article_codes": [event.article_code for event in cluster],
        "cluster_detail_sha256": {
            event.article_code: event.detail_sha256 for event in cluster
        },
        "cluster_publication_timestamps_utc": [
            event.published_utc for event in cluster
        ],
        "signal_timestamp_utc": anchor.published_utc,
        "symbol": SYMBOL,
        "direction": "LONG",
        "entry_target_utc": _iso_ms(entry_ms),
        "exit_target_utc": _iso_ms(exit_ms),
        "max_late_seconds": MAX_LATE_SECONDS,
        "max_initial_margin_usdt": 10.0,
        "max_notional_usdt": 50.0,
        "leverage": 5,
        "margin_mode": "ISOLATED",
        "max_projected_roundtrip_friction_bps": 30.0,
        "scientific_credit": False,
        "operator_proxy": True,
    }


class BNBOperatorSourceV03:
    """Public Binance announcement source with prospective first-observation guard."""

    def __init__(
        self,
        *,
        state_path: str,
        source: BinanceOfficialLaunchpoolSource | None = None,
    ) -> None:
        self.state_path = Path(state_path)
        self.source = source or BinanceOfficialLaunchpoolSource(timeout=15)
        if self.state_path.exists():
            payload = json.loads(self.state_path.read_text(encoding="utf-8"))
            if not isinstance(payload, dict):
                raise RuntimeError("BNB source state must be JSON object")
            self.state = payload
        else:
            self.state = {
                "version": "BNB_OPERATOR_SOURCE_V0.3",
                "candidate_id": CANDIDATE_ID,
                "events": {},
                "science_credit": False,
            }
        self.state.setdefault("events", {})

    def _save(self, **updates: Any) -> None:
        self.state.update(updates)
        self.state["checked_at_utc"] = datetime.now(timezone.utc).isoformat().replace(
            "+00:00", "Z"
        )
        _atomic_write(self.state_path, self.state)

    def poll(self, *, now_ms: int | None = None) -> dict[str, Any]:
        if now_ms is None:
            now_ms = int(datetime.now(timezone.utc).timestamp() * 1000)
        events = self.source.discover_eligible(now_ms=now_ms)
        clusters = _cluster_announcements(events)
        signals: list[dict[str, Any]] = []
        for cluster in clusters:
            signal = _build_signal(cluster)
            key = signal["immutable_signal_key"]
            target_ms = int(
                datetime.fromisoformat(
                    signal["entry_target_utc"].replace("Z", "+00:00")
                ).timestamp()
                * 1000
            )
            row = self.state["events"].get(key)
            if row is None:
                first_before_target = now_ms < target_ms
                row = {
                    "first_observed_at_utc": _iso_ms(now_ms),
                    "first_observed_before_entry_target": first_before_target,
                    "entry_target_utc": signal["entry_target_utc"],
                    "exit_target_utc": signal["exit_target_utc"],
                    "signal_article_code": signal["signal_article_code"],
                    "status": (
                        "PENDING_FUTURE_ENTRY"
                        if first_before_target
                        else "MISSED_FIRST_OBSERVATION_NO_CHASE"
                    ),
                    "late_chase_allowed": False,
                }
                self.state["events"][key] = row
            if (
                row.get("status") in {"PENDING_FUTURE_ENTRY", "PREARMED"}
                and row.get("first_observed_before_entry_target") is True
            ):
                candidate = dict(signal)
                candidate["first_observed_at_utc"] = row["first_observed_at_utc"]
                candidate["first_observed_before_entry_target"] = True
                signals.append(candidate)

        self._save(
            source_status="OK",
            visible_event_count=len(events),
            visible_cluster_count=len(clusters),
        )
        return {
            "source_id": "BNB_OPERATOR_SOURCE_V0.3",
            "status": "OK",
            "signals": sorted(
                signals,
                key=lambda s: (s["entry_target_utc"], s["immutable_signal_key"]),
            ),
            "visible_event_count": len(events),
            "visible_cluster_count": len(clusters),
            "orders_created": False,
            "exchange_mutation_performed": False,
        }

    def mark(self, signal_identity: str, status: str) -> None:
        row = self.state.get("events", {}).get(signal_identity)
        if isinstance(row, dict):
            row["status"] = status
            self._save()


__all__ = ["BNBOperatorSourceV03", "CANDIDATE_ID", "SYMBOL"]
