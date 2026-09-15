from __future__ import annotations

from research.tfg_extreme_mr_30m_discovery_runner_v01 import (
    Candle,
    FIFTEEN_MIN_MS,
    THIRTY_MIN_MS,
    aggregate_15m_to_30m,
    derive_signals,
    ema_series,
    parse_ms,
)


def main() -> None:
    base = parse_ms("2024-01-01T00:00:00.000Z")

    source = [
        Candle(
            base + i * FIFTEEN_MIN_MS,
            100.0,
            101.0,
            99.0,
            100.0,
            1.0,
            base + (i + 1) * FIFTEEN_MIN_MS - 1,
        )
        for i in range(4)
    ]
    bars, incomplete = aggregate_15m_to_30m(source)
    assert len(bars) == 2 and incomplete == 0

    gap_bars, gap_incomplete = aggregate_15m_to_30m(source[1:])
    assert len(gap_bars) == 1 and gap_incomplete == 1

    const = ema_series([10.0] * 40, 20)
    assert const[19] == 10.0 and const[-1] == 10.0

    # Deterministic extreme-downside signal followed by an entry open below
    # the frozen EMA target and above the frozen stop. This tests plumbing only;
    # it does not change or tune any experiment parameter.
    daily: list[Candle] = []
    for i in range(45):
        t = base + i * THIRTY_MIN_MS
        daily.append(Candle(t, 100.0, 101.0, 99.0, 100.0, 1.0, t + THIRTY_MIN_MS - 1))

    i = 35
    t = daily[i].open_time
    daily[i] = Candle(t, 100.0, 100.5, 85.0, 86.0, 1.0, t + THIRTY_MIN_MS - 1)
    t2 = daily[i + 1].open_time
    daily[i + 1] = Candle(t2, 87.0, 92.0, 86.0, 90.0, 1.0, t2 + THIRTY_MIN_MS - 1)

    signals, raw, cancelled = derive_signals("BTCUSDT", daily)
    assert raw >= 1
    assert cancelled >= 0
    assert signals
    sig = signals[0]
    assert sig.entry < sig.target
    assert sig.stop < sig.entry

    print("TFG_EXTREME_MR_30M_SYNTHETIC_TEST_V02=PASS")


if __name__ == "__main__":
    main()
