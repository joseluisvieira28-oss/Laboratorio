#!/usr/bin/env python3
"""Synthetic QA for L2 source-time normalizer V0.2. No market data."""
from l2r_source_time_normalizer_v02 import SegmentNormalizer, NormalizationFailure


def main() -> int:
    n = SegmentNormalizer()

    a = n.consume("2024-09-01T00:00:00.100000000Z", 1725148800000)
    assert a.classification == "BASELINE" and a.accepted_for_state

    b = n.consume("2024-09-01T00:00:00.700000000Z", 1725148800600)
    assert b.classification == "FORWARD_PAYLOAD" and b.accepted_for_state

    c = n.consume("2024-09-01T00:00:00.800000000Z", 1725148800100)
    assert c.classification == "STALE_LATE_PAYLOAD"
    assert not c.accepted_for_state
    assert c.last_accepted_payload_ms == b.payload_ms
    assert c.rewind_ms == 500

    d = n.consume("2024-09-01T00:00:01.000000000Z", 1725148800600)
    assert d.classification == "EQUAL_PAYLOAD_TIME" and d.accepted_for_state

    try:
        n.consume("2024-09-01T00:00:00.900000000Z", 1725148800700)
    except NormalizationFailure:
        pass
    else:
        raise AssertionError("backwards envelope did not fail closed")

    n.reset_for_missing_hour_boundary()
    e = n.consume("2024-09-01T02:00:00.100000000Z", 1725156000000)
    assert e.classification == "BASELINE"

    n2 = SegmentNormalizer()
    try:
        n2.consume("2024-09-01T00:00:00.100000000Z", 1725148800200)
    except NormalizationFailure:
        pass
    else:
        raise AssertionError("future payload did not fail closed")

    print("L2_SOURCE_TIME_NORMALIZER_V02_SYNTHETIC_PASS | NO SWEEPS | NO OUTCOMES | NO PNL")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
