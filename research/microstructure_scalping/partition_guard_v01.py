"""Partition guard. Fail closed if protected 2026 data is requested."""
import datetime as dt

DISCOVERY_START=dt.date(2023,1,18)
DISCOVERY_END=dt.date(2024,12,31)
OOS_START=dt.date(2025,1,1)
OOS_END=dt.date(2025,12,31)
HOLDOUT_START=dt.date(2026,1,1)


def authorize_date(date_text: str, phase: str) -> bool:
    d=dt.date.fromisoformat(date_text)
    phase=phase.upper()
    if d >= HOLDOUT_START:
        raise PermissionError("PROTECTED_2026_HOLDOUT_LOCKED")
    if phase=="DISCOVERY":
        if not (DISCOVERY_START <= d <= DISCOVERY_END):
            raise PermissionError("DATE_OUTSIDE_DISCOVERY")
        return True
    if phase=="OOS":
        if not (OOS_START <= d <= OOS_END):
            raise PermissionError("DATE_OUTSIDE_OOS")
        return True
    raise ValueError("UNKNOWN_PHASE")
