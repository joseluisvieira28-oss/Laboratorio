"""Offline pre-observation infrastructure for the Prospective Microstructure Collector V0.1.

This module is deliberately network-free and outcome-free. It prepares deterministic
storage, integrity, continuity, clock, completeness, event-window, preflight, and audit
primitives for a future explicitly-authorized prospective observation.

It MUST NOT:
- open sockets or HTTP connections;
- load exchange credentials;
- access MEXC or target outcomes;
- generate directional signals, PnL, entries, exits, stops, targets, or position sizes;
- authorize H02 or start target observation.

Scientific rule: correct infrastructure, never help a hypothesis survive.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
import hashlib
import json
import math
from pathlib import Path
from typing import Iterable, Mapping, Sequence


H02_STATUS = "NOT_AUTHORIZED"
TARGET_OBSERVATION_AUTHORIZED = False
SCIENTIFIC_SCOPE = "NON_DIRECTIONAL_MEASUREMENT_INFRASTRUCTURE_ONLY"

BINANCE_WS_HOST = "data-stream.binance.vision"
BINANCE_REST_HOST = "data-api.binance.vision"
COINBASE_WS_HOST = "advanced-trade-ws.coinbase.com"

ALLOWED_IDENTITIES = {
    "BINANCE_SPOT": {
        "symbols": {"BTCUSDT", "ETHUSDT"},
        "channels": {"depth@100ms", "bookTicker", "trade", "depth_snapshot"},
        "hosts": {BINANCE_WS_HOST, BINANCE_REST_HOST},
    },
    "COINBASE_ADVANCED_SPOT": {
        "symbols": {"BTC-USD", "ETH-USD"},
        "channels": {"l2_data", "market_trades", "heartbeats"},
        "hosts": {COINBASE_WS_HOST},
    },
}

FROZEN_EVENT_WINDOWS_NS = {
    "prebaseline": (-30 * 60 * 1_000_000_000, 0),
    "primary_state": (0, 30 * 60 * 1_000_000_000),
    "recovery_descriptive": (30 * 60 * 1_000_000_000, 60 * 60 * 1_000_000_000),
}


class CollectorPreparationViolation(ValueError):
    """Fail-closed validation error for offline collector preparation."""


def _canonical_bytes(payload: object) -> bytes:
    try:
        text = json.dumps(
            payload,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
            allow_nan=False,
        )
    except (TypeError, ValueError) as exc:
        raise CollectorPreparationViolation("payload is not canonically JSON-serializable") from exc
    return text.encode("utf-8")


def sha256_hex(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def canonical_fingerprint(payload: object) -> str:
    return sha256_hex(_canonical_bytes(payload))


def _require_hex64(value: str, name: str) -> str:
    if not isinstance(value, str) or len(value) != 64:
        raise CollectorPreparationViolation(f"{name} must be 64 hex characters")
    try:
        bytes.fromhex(value)
    except ValueError as exc:
        raise CollectorPreparationViolation(f"{name} must be hexadecimal") from exc
    return value


def _nonnegative_int(value: int, name: str) -> int:
    if isinstance(value, bool):
        raise CollectorPreparationViolation(f"{name} must be a non-negative integer")
    try:
        out = int(value)
    except (TypeError, ValueError) as exc:
        raise CollectorPreparationViolation(f"{name} must be a non-negative integer") from exc
    if out < 0:
        raise CollectorPreparationViolation(f"{name} must be a non-negative integer")
    return out


def _positive_number(value: float, name: str) -> float:
    try:
        out = float(value)
    except (TypeError, ValueError) as exc:
        raise CollectorPreparationViolation(f"{name} must be finite and > 0") from exc
    if not math.isfinite(out) or out <= 0:
        raise CollectorPreparationViolation(f"{name} must be finite and > 0")
    return out


def _safe_token(value: str, name: str) -> str:
    if not isinstance(value, str) or not value:
        raise CollectorPreparationViolation(f"{name} must be a non-empty string")
    if any(c not in "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789._-" for c in value):
        raise CollectorPreparationViolation(f"{name} contains unsafe path characters")
    return value


@dataclass(frozen=True)
class SessionManifest:
    session_id: str
    venue: str
    symbol: str
    channel: str
    endpoint_host: str
    collector_commit_sha: str
    opened_wall_ns: int
    opened_monotonic_ns: int

    def validate(self) -> None:
        _safe_token(self.session_id, "session_id")
        scope = ALLOWED_IDENTITIES.get(self.venue)
        if scope is None:
            raise CollectorPreparationViolation("venue outside frozen collector scope")
        if self.symbol not in scope["symbols"]:
            raise CollectorPreparationViolation("symbol outside frozen collector scope")
        if self.channel not in scope["channels"]:
            raise CollectorPreparationViolation("channel outside frozen collector scope")
        if self.endpoint_host not in scope["hosts"]:
            raise CollectorPreparationViolation("endpoint host outside frozen allowlist")
        if self.venue == "BINANCE_SPOT":
            if self.channel == "depth_snapshot" and self.endpoint_host != BINANCE_REST_HOST:
                raise CollectorPreparationViolation("Binance depth snapshot requires market-data-only REST host")
            if self.channel != "depth_snapshot" and self.endpoint_host != BINANCE_WS_HOST:
                raise CollectorPreparationViolation("Binance streaming channel requires market-data-only WebSocket host")
        _safe_token(self.collector_commit_sha, "collector_commit_sha")
        _nonnegative_int(self.opened_wall_ns, "opened_wall_ns")
        _nonnegative_int(self.opened_monotonic_ns, "opened_monotonic_ns")

    def fingerprint(self) -> str:
        self.validate()
        return canonical_fingerprint(asdict(self))


@dataclass(frozen=True)
class RawMessageMeta:
    ordinal: int
    collector_wall_ns: int
    collector_monotonic_ns: int
    exchange_ts_ns: int | None
    sequence_start: int | None
    sequence_end: int | None
    source_message_hash_sha256: str

    def validate(self) -> None:
        _nonnegative_int(self.ordinal, "ordinal")
        _nonnegative_int(self.collector_wall_ns, "collector_wall_ns")
        _nonnegative_int(self.collector_monotonic_ns, "collector_monotonic_ns")
        if self.exchange_ts_ns is not None:
            _nonnegative_int(self.exchange_ts_ns, "exchange_ts_ns")
        if self.sequence_start is not None:
            _nonnegative_int(self.sequence_start, "sequence_start")
        if self.sequence_end is not None:
            _nonnegative_int(self.sequence_end, "sequence_end")
        if (self.sequence_start is None) != (self.sequence_end is None):
            raise CollectorPreparationViolation("sequence interval must be both null or both present")
        if (
            self.sequence_start is not None
            and self.sequence_end is not None
            and self.sequence_start > self.sequence_end
        ):
            raise CollectorPreparationViolation("sequence_start cannot exceed sequence_end")
        _require_hex64(self.source_message_hash_sha256, "source_message_hash_sha256")


@dataclass(frozen=True)
class SegmentReceipt:
    segment_id: str
    session_manifest_fingerprint: str
    venue: str
    symbol: str
    channel: str
    parent_session_id: str
    message_count: int
    parsing_rejection_count: int
    duplicate_count: int
    reconnect_count: int
    gap_count: int
    resync_count: int
    first_collector_wall_ns: int | None
    last_collector_wall_ns: int | None
    first_exchange_ts_ns: int | None
    last_exchange_ts_ns: int | None
    ordered_segment_sha256: str
    collector_commit_sha: str
    closed: bool = True

    def validate(self) -> None:
        _safe_token(self.segment_id, "segment_id")
        _safe_token(self.parent_session_id, "parent_session_id")
        _require_hex64(self.session_manifest_fingerprint, "session_manifest_fingerprint")
        _require_hex64(self.ordered_segment_sha256, "ordered_segment_sha256")
        _safe_token(self.collector_commit_sha, "collector_commit_sha")
        for name in (
            "message_count",
            "parsing_rejection_count",
            "duplicate_count",
            "reconnect_count",
            "gap_count",
            "resync_count",
        ):
            _nonnegative_int(getattr(self, name), name)
        if self.message_count <= 0:
            raise CollectorPreparationViolation("closed segment must contain at least one raw message")
        for name in (
            "first_collector_wall_ns",
            "last_collector_wall_ns",
            "first_exchange_ts_ns",
            "last_exchange_ts_ns",
        ):
            value = getattr(self, name)
            if value is not None:
                _nonnegative_int(value, name)
        if self.first_collector_wall_ns is None or self.last_collector_wall_ns is None:
            raise CollectorPreparationViolation("closed segment requires collector wall-clock bounds")
        if self.first_collector_wall_ns > self.last_collector_wall_ns:
            raise CollectorPreparationViolation("collector wall-clock bounds are reversed")
        if (
            self.first_exchange_ts_ns is not None
            and self.last_exchange_ts_ns is not None
            and self.first_exchange_ts_ns > self.last_exchange_ts_ns
        ):
            raise CollectorPreparationViolation("exchange timestamp bounds are reversed")
        if not self.closed:
            raise CollectorPreparationViolation("segment receipt must represent a closed segment")


def ordered_segment_digest(message_hashes: Sequence[str]) -> str:
    if not message_hashes:
        raise CollectorPreparationViolation("at least one message hash is required")
    normalized = []
    for item in message_hashes:
        normalized.append(_require_hex64(item, "message hash"))
    return sha256_hex("".join(normalized).encode("ascii"))


class ImmutableSegmentWriter:
    """Filesystem-backed exact-byte segment writer with exclusive-create semantics.

    Files are never opened in truncate/overwrite mode. Closed segments reject further
    appends. Integrity verification detects any post-close byte or metadata mutation.
    """

    def __init__(self, root: Path, manifest: SessionManifest, segment_index: int) -> None:
        manifest.validate()
        self.manifest = manifest
        self.segment_index = _nonnegative_int(segment_index, "segment_index")
        seed = {
            "manifest_fingerprint": manifest.fingerprint(),
            "segment_index": self.segment_index,
        }
        self.segment_id = f"seg-{canonical_fingerprint(seed)[:24]}"
        channel_token = manifest.channel.replace("@", "_")
        self.segment_dir = (
            Path(root)
            / manifest.venue
            / manifest.symbol
            / channel_token
            / manifest.session_id
            / self.segment_id
        )
        self.segment_dir.mkdir(parents=True, exist_ok=False)
        self.messages_dir = self.segment_dir / "messages"
        self.messages_dir.mkdir(exist_ok=False)
        self._exclusive_json(self.segment_dir / "SESSION_MANIFEST.json", {
            **asdict(manifest),
            "manifest_fingerprint": manifest.fingerprint(),
        })
        self._hashes: list[str] = []
        self._metas: list[RawMessageMeta] = []
        self._closed = False
        self._parsing_rejection_count = 0
        self._duplicate_count = 0
        self._reconnect_count = 0
        self._gap_count = 0
        self._resync_count = 0

    @staticmethod
    def _exclusive_json(path: Path, payload: object) -> None:
        with path.open("x", encoding="utf-8", newline="\n") as handle:
            handle.write(json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=False))
            handle.write("\n")

    def _require_open(self) -> None:
        if self._closed:
            raise CollectorPreparationViolation("segment is already closed and immutable")

    def note_parsing_rejection(self) -> None:
        self._require_open()
        self._parsing_rejection_count += 1

    def note_duplicate(self) -> None:
        self._require_open()
        self._duplicate_count += 1

    def note_reconnect(self) -> None:
        self._require_open()
        self._reconnect_count += 1

    def note_gap(self) -> None:
        self._require_open()
        self._gap_count += 1

    def note_resync(self) -> None:
        self._require_open()
        self._resync_count += 1

    def append(
        self,
        raw_bytes: bytes,
        *,
        collector_wall_ns: int,
        collector_monotonic_ns: int,
        exchange_ts_ns: int | None = None,
        sequence_start: int | None = None,
        sequence_end: int | None = None,
    ) -> RawMessageMeta:
        self._require_open()
        if not isinstance(raw_bytes, bytes) or not raw_bytes:
            raise CollectorPreparationViolation("raw_bytes must be non-empty exact bytes")
        ordinal = len(self._hashes)
        source_hash = sha256_hex(raw_bytes)
        meta = RawMessageMeta(
            ordinal=ordinal,
            collector_wall_ns=collector_wall_ns,
            collector_monotonic_ns=collector_monotonic_ns,
            exchange_ts_ns=exchange_ts_ns,
            sequence_start=sequence_start,
            sequence_end=sequence_end,
            source_message_hash_sha256=source_hash,
        )
        meta.validate()
        stem = f"{ordinal:012d}"
        raw_path = self.messages_dir / f"{stem}.bin"
        meta_path = self.messages_dir / f"{stem}.json"
        with raw_path.open("xb") as handle:
            handle.write(raw_bytes)
        self._exclusive_json(meta_path, asdict(meta))
        self._hashes.append(source_hash)
        self._metas.append(meta)
        return meta

    def close(self) -> SegmentReceipt:
        self._require_open()
        if not self._metas:
            raise CollectorPreparationViolation("cannot close an empty segment")
        exchange_times = [m.exchange_ts_ns for m in self._metas if m.exchange_ts_ns is not None]
        receipt = SegmentReceipt(
            segment_id=self.segment_id,
            session_manifest_fingerprint=self.manifest.fingerprint(),
            venue=self.manifest.venue,
            symbol=self.manifest.symbol,
            channel=self.manifest.channel,
            parent_session_id=self.manifest.session_id,
            message_count=len(self._metas),
            parsing_rejection_count=self._parsing_rejection_count,
            duplicate_count=self._duplicate_count,
            reconnect_count=self._reconnect_count,
            gap_count=self._gap_count,
            resync_count=self._resync_count,
            first_collector_wall_ns=self._metas[0].collector_wall_ns,
            last_collector_wall_ns=self._metas[-1].collector_wall_ns,
            first_exchange_ts_ns=exchange_times[0] if exchange_times else None,
            last_exchange_ts_ns=exchange_times[-1] if exchange_times else None,
            ordered_segment_sha256=ordered_segment_digest(self._hashes),
            collector_commit_sha=self.manifest.collector_commit_sha,
        )
        receipt.validate()
        self._exclusive_json(self.segment_dir / "SEGMENT_RECEIPT.json", asdict(receipt))
        with (self.segment_dir / "CLOSED").open("x", encoding="ascii", newline="\n") as handle:
            handle.write(receipt.ordered_segment_sha256 + "\n")
        self._closed = True
        return receipt


def verify_closed_segment(segment_dir: Path) -> SegmentReceipt:
    root = Path(segment_dir)
    try:
        manifest_payload = json.loads((root / "SESSION_MANIFEST.json").read_text(encoding="utf-8"))
        receipt_payload = json.loads((root / "SEGMENT_RECEIPT.json").read_text(encoding="utf-8"))
        closed_digest = (root / "CLOSED").read_text(encoding="ascii").strip()
    except (OSError, json.JSONDecodeError) as exc:
        raise CollectorPreparationViolation("closed segment control files missing or malformed") from exc

    manifest_fields = {
        key: manifest_payload[key]
        for key in (
            "session_id",
            "venue",
            "symbol",
            "channel",
            "endpoint_host",
            "collector_commit_sha",
            "opened_wall_ns",
            "opened_monotonic_ns",
        )
    }
    manifest = SessionManifest(**manifest_fields)
    manifest.validate()
    manifest_fp = manifest.fingerprint()
    if manifest_payload.get("manifest_fingerprint") != manifest_fp:
        raise CollectorPreparationViolation("session manifest fingerprint mismatch")

    receipt = SegmentReceipt(**receipt_payload)
    receipt.validate()
    if receipt.session_manifest_fingerprint != manifest_fp:
        raise CollectorPreparationViolation("receipt manifest lineage mismatch")
    if receipt.segment_id != root.name:
        raise CollectorPreparationViolation("segment directory identity mismatch")
    if closed_digest != receipt.ordered_segment_sha256:
        raise CollectorPreparationViolation("CLOSED marker digest mismatch")

    messages_dir = root / "messages"
    raw_files = sorted(messages_dir.glob("*.bin"))
    meta_files = sorted(messages_dir.glob("*.json"))
    if len(raw_files) != receipt.message_count or len(meta_files) != receipt.message_count:
        raise CollectorPreparationViolation("segment file count does not match receipt")

    hashes: list[str] = []
    prior_ordinal = -1
    for raw_path, meta_path in zip(raw_files, meta_files):
        if raw_path.stem != meta_path.stem:
            raise CollectorPreparationViolation("raw/meta ordinal pairing mismatch")
        try:
            meta = RawMessageMeta(**json.loads(meta_path.read_text(encoding="utf-8")))
            raw = raw_path.read_bytes()
        except (OSError, json.JSONDecodeError, TypeError) as exc:
            raise CollectorPreparationViolation("raw message record is malformed") from exc
        meta.validate()
        if meta.ordinal != prior_ordinal + 1:
            raise CollectorPreparationViolation("message ordinals are not contiguous")
        if raw_path.stem != f"{meta.ordinal:012d}":
            raise CollectorPreparationViolation("message filename ordinal mismatch")
        actual_hash = sha256_hex(raw)
        if actual_hash != meta.source_message_hash_sha256:
            raise CollectorPreparationViolation("raw message hash mismatch")
        hashes.append(actual_hash)
        prior_ordinal = meta.ordinal

    digest = ordered_segment_digest(hashes)
    if digest != receipt.ordered_segment_sha256:
        raise CollectorPreparationViolation("ordered segment digest mismatch")
    return receipt


@dataclass(frozen=True)
class ClockSample:
    collector_wall_ns: int
    collector_monotonic_ns: int

    def validate(self) -> None:
        _nonnegative_int(self.collector_wall_ns, "collector_wall_ns")
        _nonnegative_int(self.collector_monotonic_ns, "collector_monotonic_ns")


def clock_diagnostics(samples: Sequence[ClockSample]) -> Mapping[str, int | bool]:
    if not samples:
        raise CollectorPreparationViolation("clock diagnostics require at least one sample")
    for sample in samples:
        sample.validate()
    wall_regressions = 0
    monotonic_nonincreasing = 0
    max_abs_drift_delta_ns = 0
    wall0 = samples[0].collector_wall_ns
    mono0 = samples[0].collector_monotonic_ns
    for prior, current in zip(samples, samples[1:]):
        if current.collector_wall_ns < prior.collector_wall_ns:
            wall_regressions += 1
        if current.collector_monotonic_ns <= prior.collector_monotonic_ns:
            monotonic_nonincreasing += 1
        drift = (
            (current.collector_wall_ns - wall0)
            - (current.collector_monotonic_ns - mono0)
        )
        max_abs_drift_delta_ns = max(max_abs_drift_delta_ns, abs(drift))
    return {
        "sample_count": len(samples),
        "wall_regressions": wall_regressions,
        "monotonic_nonincreasing": monotonic_nonincreasing,
        "max_abs_wall_vs_monotonic_drift_delta_ns": max_abs_drift_delta_ns,
        "valid_for_receive_time_ordering": (
            wall_regressions == 0 and monotonic_nonincreasing == 0
        ),
    }


def binance_sequence_status(previous_end: int, next_start: int, next_end: int) -> str:
    prior = _nonnegative_int(previous_end, "previous_end")
    start = _nonnegative_int(next_start, "next_start")
    end = _nonnegative_int(next_end, "next_end")
    if start > end:
        raise CollectorPreparationViolation("next_start cannot exceed next_end")
    if end <= prior:
        return "STALE_OR_DUPLICATE"
    if start > prior + 1:
        return "GAP_FAIL_CLOSED"
    return "CONTIGUOUS_OR_OVERLAP"


def coinbase_connection_sequence_status(previous: int, current: int) -> str:
    prior = _nonnegative_int(previous, "previous")
    now = _nonnegative_int(current, "current")
    if now == prior + 1:
        return "CONTIGUOUS"
    return "GAP_OR_REORDER_FAIL_CLOSED"


def coinbase_book_sequence_status(previous: int, current: int) -> str:
    prior = _nonnegative_int(previous, "previous")
    now = _nonnegative_int(current, "current")
    return "STRICTLY_INCREASING" if now > prior else "REGRESSION_FAIL_CLOSED"


@dataclass
class ContinuityState:
    venue: str
    synchronized: bool = False
    reconnect_count: int = 0
    gap_count: int = 0
    resync_count: int = 0
    invalid_reason: str | None = None

    def __post_init__(self) -> None:
        if self.venue not in ALLOWED_IDENTITIES:
            raise CollectorPreparationViolation("venue outside frozen collector scope")

    def on_reconnect(self, reason: str) -> None:
        if not isinstance(reason, str) or not reason:
            raise CollectorPreparationViolation("reconnect reason is required")
        self.reconnect_count += 1
        self.synchronized = False
        self.invalid_reason = f"RECONNECT:{reason}"

    def on_gap(self, reason: str) -> None:
        if not isinstance(reason, str) or not reason:
            raise CollectorPreparationViolation("gap reason is required")
        self.gap_count += 1
        self.synchronized = False
        self.invalid_reason = f"GAP:{reason}"

    def on_resync(self) -> None:
        self.resync_count += 1
        self.synchronized = True
        self.invalid_reason = None


def storage_estimate(
    *,
    observed_bytes: int,
    observed_seconds: float,
    target_hours: float,
) -> Mapping[str, float | int]:
    byte_count = _nonnegative_int(observed_bytes, "observed_bytes")
    seconds = _positive_number(observed_seconds, "observed_seconds")
    hours = _positive_number(target_hours, "target_hours")
    rate = byte_count / seconds
    baseline = int(math.ceil(rate * hours * 3600.0))
    return {
        "observed_bytes": byte_count,
        "observed_seconds": seconds,
        "bytes_per_second": rate,
        "target_hours": hours,
        "baseline_bytes": baseline,
        "planning_1_25x_bytes": int(math.ceil(baseline * 1.25)),
        "planning_1_5x_bytes": int(math.ceil(baseline * 1.5)),
        "planning_2x_bytes": baseline * 2,
    }


@dataclass(frozen=True)
class WindowRecord:
    timestamp_ns: int
    source_order: int
    source_hash_sha256: str

    def validate(self) -> None:
        _nonnegative_int(self.timestamp_ns, "timestamp_ns")
        _nonnegative_int(self.source_order, "source_order")
        _require_hex64(self.source_hash_sha256, "source_hash_sha256")


def extract_frozen_event_windows(
    records: Iterable[WindowRecord],
    *,
    event_timestamp_ns: int,
) -> Mapping[str, tuple[WindowRecord, ...]]:
    event_ts = _nonnegative_int(event_timestamp_ns, "event_timestamp_ns")
    prepared: list[WindowRecord] = []
    for record in records:
        record.validate()
        prepared.append(record)
    prepared.sort(key=lambda r: (r.timestamp_ns, r.source_order, r.source_hash_sha256))
    out: dict[str, tuple[WindowRecord, ...]] = {}
    for name, (start_offset, end_offset) in FROZEN_EVENT_WINDOWS_NS.items():
        start = event_ts + start_offset
        end = event_ts + end_offset
        selected = tuple(r for r in prepared if start <= r.timestamp_ns < end)
        out[name] = selected
    return out


def required_observation_keys() -> tuple[tuple[str, str, str], ...]:
    keys: list[tuple[str, str, str]] = []
    for symbol in ("BTCUSDT", "ETHUSDT"):
        for channel in ("depth@100ms", "bookTicker", "trade", "depth_snapshot"):
            keys.append(("BINANCE_SPOT", symbol, channel))
    for symbol in ("BTC-USD", "ETH-USD"):
        for channel in ("l2_data", "market_trades", "heartbeats"):
            keys.append(("COINBASE_ADVANCED_SPOT", symbol, channel))
    return tuple(keys)


def completeness_receipt(
    observed_keys: Iterable[tuple[str, str, str]],
) -> Mapping[str, object]:
    required = set(required_observation_keys())
    observed = set(observed_keys)
    unknown = sorted(observed - required)
    if unknown:
        raise CollectorPreparationViolation(f"observed keys outside frozen scope: {unknown}")
    missing = sorted(required - observed)
    return {
        "document_type": "MICROSTRUCTURE_COLLECTION_COMPLETENESS_RECEIPT",
        "scope": SCIENTIFIC_SCOPE,
        "required_key_count": len(required),
        "observed_key_count": len(observed),
        "missing_keys": [list(item) for item in missing],
        "complete": not missing,
        "h02_status": H02_STATUS,
        "target_outcomes_evaluated": False,
        "trading_signals_generated": False,
    }


def preflight_gate(
    *,
    implementation_fingerprint: str,
    contract_fingerprint: str,
    complete_official_2027_calendar_frozen: bool,
    separate_explicit_target_observation_authorization: bool,
) -> Mapping[str, object]:
    _require_hex64(implementation_fingerprint, "implementation_fingerprint")
    _require_hex64(contract_fingerprint, "contract_fingerprint")
    authorized = bool(
        complete_official_2027_calendar_frozen
        and separate_explicit_target_observation_authorization
    )
    return {
        "document_type": "MICROSTRUCTURE_PROSPECTIVE_OBSERVATION_PREFLIGHT",
        "scientific_scope": SCIENTIFIC_SCOPE,
        "implementation_fingerprint": implementation_fingerprint,
        "contract_fingerprint": contract_fingerprint,
        "complete_official_2027_calendar_frozen": bool(complete_official_2027_calendar_frozen),
        "separate_explicit_target_observation_authorization": bool(
            separate_explicit_target_observation_authorization
        ),
        "target_observation_may_start": authorized,
        "status": (
            "ELIGIBLE_FOR_RUNTIME_PREFLIGHT_NOT_STARTED"
            if authorized
            else "OFFLINE_READY_TARGET_OBSERVATION_BLOCKED"
        ),
        "h02_status": H02_STATUS,
        "live_trading_authorized": False,
        "exchange_mutation_authorized": False,
        "mexc_2025_09_through_2025_12_authorized": False,
    }


def observation_receipt_template() -> Mapping[str, object]:
    return {
        "document_type": "MICROSTRUCTURE_PROSPECTIVE_OBSERVATION_RECEIPT",
        "version": "0.1",
        "status": "TEMPLATE_NOT_EXECUTED",
        "target_observation_started": False,
        "target_outcomes_evaluated": False,
        "trading_signals_generated": False,
        "h02_status": H02_STATUS,
        "session_manifest_fingerprints": [],
        "segment_receipt_fingerprints": [],
        "completeness_receipt_fingerprint": None,
        "clock_diagnostic_fingerprints": [],
        "event_window_extraction_fingerprint": None,
        "scientific_classification": None,
        "note": "Template only. Infrastructure PASS is not edge evidence.",
    }


def audit_chain_fingerprint(previous_fingerprint: str | None, record: Mapping[str, object]) -> str:
    if previous_fingerprint is not None:
        _require_hex64(previous_fingerprint, "previous_fingerprint")
    return canonical_fingerprint(
        {
            "previous_fingerprint": previous_fingerprint,
            "record": record,
        }
    )


def governance_receipt() -> Mapping[str, object]:
    return {
        "scientific_scope": SCIENTIFIC_SCOPE,
        "h02_status": H02_STATUS,
        "target_observation_authorized_by_this_module": TARGET_OBSERVATION_AUTHORIZED,
        "network_access_in_this_module": False,
        "credentials_loaded_by_this_module": False,
        "exchange_mutation_authorized": False,
        "live_trading_authorized": False,
        "target_outcomes_accessed": False,
        "directional_signals_generated": False,
        "mexc_2025_09_through_2025_12_accessed": False,
        "stop_condition": (
            "STOP_AFTER_OFFLINE_COLLECTOR_PREPARATION_AND_CI_"
            "AT_CALENDAR_AND_EXPLICIT_OBSERVATION_AUTHORIZATION_GATE"
        ),
    }
