# News Shock Lab V0.3 — Static Document Recovery V0.2

Date: 2026-10-07  
Branch: `news-shock-v03-public-source-recovery-v0.1`

## Verdict

**PARTIAL_SOURCE — STRONGLY UPGRADED**

The exact two frozen reopening events now have **field-complete, clearly pre-release, static institutional document evidence**:

- CPI 2021-01-13: **4/4 consensus fields**
- NFP 2021-01-08: **4/4 consensus fields**

This materially supersedes the factual premise behind the old statement that no field-complete public route had been demonstrated. The old closeout remains historically preserved and is not rewritten.

This is still **not SOURCE PASS** because the inherited gate also requires immutable versioning or an auditable version history, and no independent archive capture, vendor revision ID, or equivalent version-control proof has yet been recovered.

## CPI frozen event — static institutional PDF

Danske Bank, *Weekly Focus*, internally dated **8 January 2021**, contains the calendar for Wednesday 13 January 2021 and lists:

| Field | Consensus |
|---|---:|
| CPI headline MoM | 0.4% |
| CPI headline YoY | 1.3% |
| CPI core MoM | 0.1% |
| CPI core YoY | 1.6% |

The document date is five calendar days before frozen T0, so pre-T0 chronology does not depend on same-day timezone inference.

Source:  
`https://research.danskebank.com/link/WeeklyFocus080120/%24file/WeeklyFocus_080120.pdf`

## NFP frozen event — static institutional PDF

The Baker Group, *Lunch with Lester*, internally dated **31 December 2020**, contains the future 8 January 2021 economic calendar with:

| Field | Consensus |
|---|---:|
| Change in Nonfarm Payrolls | 68k |
| Unemployment Rate | 6.8% |
| Average Hourly Earnings MoM | 0.2% |
| Average Hourly Earnings YoY | 4.5% |

The document predates frozen T0 by eight calendar days.

A particularly strong anti-hindsight witness is preserved inside the table: the 8-Jan rows contain forecast values while their `Actual` cells remain blank/`--`. This is structurally consistent with a document prepared before those releases occurred.

Source:  
`https://creditunions.com/wp-content/uploads/2022/04/wk201231-1.pdf`

## Gate status

| Requirement | CPI | NFP |
|---|---:|---:|
| Exact frozen event | PASS | PASS |
| Required fields | 4/4 PASS | 4/4 PASS |
| Explicit consensus values | PASS | PASS |
| Pre-T0 chronology | PASS | PASS |
| Static document form | PASS | PASS |
| Internal anti-hindsight evidence | HIGH | VERY HIGH |
| Immutable version / auditable revision history | **UNRESOLVED** | **UNRESOLVED** |

## Why this is not yet promoted to SOURCE PASS

The 2026-09-21 reopening rule explicitly required an immutable version or auditable version history. A static PDF with an internal pre-release date is much stronger than a mutable calendar page, but the present mission did not independently recover:

- a pre-T0 archive capture;
- a publisher-side immutable revision/version identifier;
- a cryptographically timestamped historical copy;
- or another external audit chain proving the current bytes are identical to the pre-T0 bytes.

Therefore the correct fail-closed verdict remains **PARTIAL_SOURCE**, not PASS.

## Scientific consequence

The blocker is now narrow:

> **We no longer lack the consensus fields. We lack only independent version immutability/audit history.**

No new census, surprise calculation, outcome opening, backtest, BTC/ETH reaction study, yield-response study, trading inference, or main merge is authorized yet.

## Next legitimate attack

Search only for independent version-proof for these two exact static documents, for example:

1. pre-T0 or contemporaneous archive captures;
2. publisher CMS/document metadata exposing original publication and revision history;
3. mirrored institutional copies with independent timestamps and matching content;
4. content hashes preserved in contemporaneous repositories or distribution systems.

Do not weaken the inherited gate.
