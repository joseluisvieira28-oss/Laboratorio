# CROSS-ASSET-VOL-STRESS-001 — DISCOVERY IMPLEMENTATION FREEZE V0.1

**Frozen before first BTC outcome access.**

This file specifies implementation details not fully textualized in the parent authority. It does not alter the economic hypothesis or promotion gates.

## Source rebinding
Discovery must reacquire exactly seven official Cboe JSON responses, one for each year 2018–2024, from the prospectively frozen year-param endpoint. Every raw SHA-256 must equal the values in `DISCOVERY_AUTHORITY_V0.1.json`. Canonicalized settlement bytes must reproduce SHA-256 `48c16e171c06f61378ac216d75d76a22491b417ae904936c3538a34dfb6ab1be` before BTC market access.

Any mismatch hard-fails before BTC outcomes.

## Signal
Canonical settlement records are sorted ascending by provider `expire_date`.
For each record after the first:
- `delta_vx = current_settlement - previous_settlement`
- `delta_vx > 0`: direction = -1 (SHORT BTC)
- `delta_vx < 0`: direction = +1 (LONG BTC)
- `delta_vx == 0`: no candidate trade

No threshold or transform is applied.

## Timing
The pre-outcome timing addendum controls:
- entry date = provider `expire_date` + 2 calendar days;
- entry price = Binance BTCUSDT Spot daily UTC OPEN at entry date 00:00;
- exit date = entry date + 7 calendar days;
- exit price = Binance BTCUSDT Spot daily UTC OPEN at exit date 00:00.

A candidate is dropped if entry or exit lies outside 2018-01-01..2024-12-31 or if either exact daily bar is absent.

## Overlap
Candidates are processed in chronological entry order.
- if candidate entry < prior accepted exit: suppress candidate;
- if candidate entry == prior accepted exit: prior trade exits first and candidate may enter;
- otherwise candidate is accepted.

## Returns and costs
`gross_bps = direction * (exit_open / entry_open - 1.0) * 10000.0`

`net10_bps = gross_bps - 10.0`

`net20_bps = gross_bps - 20.0`

Profit Factor NET10 = sum of positive NET10 / absolute sum of negative NET10. If there are no negative trades, PF is positive infinity. Win rate NET10 = fraction with NET10 > 0. Exactly zero is not a win.

Calendar-year statistics are assigned by accepted **entry date year**.

## Bootstrap
Primary inference diagnostic/gate is mean NET10 block bootstrap:
- ordered accepted trade NET10 series;
- moving blocks = every overlapping contiguous block of exactly 4 trades;
- sample blocks uniformly with replacement using Python `random.Random(230911)`;
- concatenate sampled blocks until at least N observations, then truncate to N;
- 5,000 repetitions;
- each repetition statistic = arithmetic mean NET10;
- percentile 95% CI = linear-interpolated empirical 2.5th and 97.5th percentiles of sorted bootstrap means.

## Market source
Binance Data Vision Spot monthly BTCUSDT 1d ZIP files, exactly 2018-01 through 2024-12. Each ZIP SHA-256 must match its provider `.CHECKSUM` before extraction. No 2025/2026 URL is permitted.

## Promotion gates
Unchanged from authority: N>=300; mean NET10>0; PF NET10>1; bootstrap lower>0; >=5/7 non-negative entry-year means across 2018–2024; >=3/4 non-negative entry-year means across 2021–2024; all source/firewall gates pass.

N<300 => `INSUFFICIENT_SAMPLE`. Passing all gates => `SURVIVES_DISCOVERY` only, not a diamond/live authorization. Otherwise => `DISCOVERY_FAIL_NO_PROMOTION` with economics reported without rescue.
