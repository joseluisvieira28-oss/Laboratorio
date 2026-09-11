from __future__ import annotations

"""H02 prospective session-eligibility gate for synthetic/offline research only.

H02 inherits H01 signal formation and H01 post-TP1 management unchanged.  The only
new rule in this module is a deterministic UTC entry-time eligibility gate.  This
module does not load market data, evaluate H02 outcomes, classify H02, unlock any
stage, access a network, mutate an exchange, or authorize live trading.
"""

from datetime import datetime, timezone

from research.phase_b_signal_formation_v01 import SignalGeometry


HYPOTHESIS_ID = "H02_US_EU_OVERLAP_SESSION_GATE"
FAMILY_ID = "PBR03_SESSION_GATED_MANAGED_BREAKOUT_RETEST_LONG"
FREEZE_FINGERPRINT = "b7ccfacd438c9554df9de42e51683d3a6c5d52be3301371f96dd30a6e5b4dbb4"
SESSION_START_HOUR_UTC = 13
SESSION_END_HOUR_UTC_EXCLUSIVE = 17
TIMEFRAME_MS = 15 * 60 * 1000

NEW_MARKET_DATA_ACCESS_AUTHORIZED = False
VALIDATION_2025_09_THROUGH_2025_12_AUTHORIZED = False
HOLDOUT_2026_AUTHORIZED = False
NETWORK_DOWNLOAD_AUTHORIZED = False
LIVE_AUTHORIZED = False
EXCHANGE_MUTATION_AUTHORIZED = False


def is_h02_entry_open_time_eligible(entry_open_time_ms: int) -> bool:
    """Return whether an actual signal entry-open timestamp is inside the H02 UTC gate.

    Frozen rule: 13:00:00 UTC inclusive through 17:00:00 UTC exclusive, with no DST
    adjustment.  The timestamp must itself sit on the frozen 15-minute bar grid.
    No market data are loaded by this function.
    """

    if not isinstance(entry_open_time_ms, int) or isinstance(entry_open_time_ms, bool):
        raise TypeError("entry_open_time_ms must be an integer millisecond timestamp")
    if entry_open_time_ms < 0:
        raise ValueError("entry_open_time_ms must be non-negative")
    if entry_open_time_ms % TIMEFRAME_MS != 0:
        raise ValueError("entry_open_time_ms must align to an exact 15-minute UTC boundary")

    hour_utc = datetime.fromtimestamp(entry_open_time_ms / 1000.0, tz=timezone.utc).hour
    return SESSION_START_HOUR_UTC <= hour_utc < SESSION_END_HOUR_UTC_EXCLUSIVE


def is_h02_signal_eligible(signal: SignalGeometry) -> bool:
    """Apply only the frozen H02 session gate to an already-defined H01/P00 geometry."""

    if not isinstance(signal, SignalGeometry):
        raise TypeError("signal must be a SignalGeometry")
    return is_h02_entry_open_time_eligible(signal.entry_open_time)
