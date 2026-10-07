# News Shock Lab V0.3 — Public Source Recovery Two-Event Probe V0.1

Date: 2026-10-07  
Branch: `news-shock-v03-public-source-recovery-v0.1`  
Parent terminal record: `NEWS SHOCK LAB V0.3: FORMALLY CLOSED — SOURCE_BLOCKED` at `fb1dff5d40ea8b5efbd0a9489e59bf40cb81f670`

## Verdict

**PARTIAL_SOURCE — NEW PUBLIC ROUTE FOUND; FIELD COMPLETENESS RECOVERED; VERSION AUDIT STILL BLOCKED**

The old closeout is preserved unchanged. This probe does not rewrite `D — NO DEFENSIBLE SOURCE IDENTIFIED` as if the evidence had existed on 2026-09-21. It records a genuinely new public-source input discovered on 2026-10-07 and applies the old reopening rules to the exact two frozen events.

This is **not SOURCE PASS**, **not NO_EDGE**, and **not an outcome test**.

## Frozen reopening test

The closeout requires these exact events before any new census can be authorized:

| Event | Frozen T0 | Required consensus fields |
|---|---|---|
| US_CPI_2021-01-13 | 2021-01-13 13:30 UTC | headline MoM, headline YoY, core MoM, core YoY |
| US_NFP_2021-01-08 | 2021-01-08 13:30 UTC | payrolls, unemployment, AHE MoM, AHE YoY |

Acceptance rules are inherited unchanged: field-explicit value, provenance, publication/vintage strictly pre-T0, timezone resolution, and immutable version or auditable version history.

## New evidence

### CPI — 4/4 fields recovered

TeleTrade historical article ID `3656123`, displayed `12.01.2021, 20:50`, is a schedule for the following day. Its table lists the 13:30 GMT U.S. CPI release and these forecasts:

- headline CPI MoM: **0.4%**
- headline CPI YoY: **1.3%**
- core CPI MoM: **0.1%**
- core CPI YoY: **1.6%**

Public route:  
`https://www.teletrade.org/vi/analytics/market-analysis/market-news/3656123`

The same article ID/content is visible under other TeleTrade locale paths and in the historical 12-Jan feed. The prior-calendar-day timestamp is sufficient to establish pre-T0 chronology independently of a narrow timezone interpretation.

**CPI field coverage: 4/4.**

### NFP — 4/4 fields recovered

TeleTrade historical article ID `3655582`, displayed `08.01.2021, 07:33`, carries an eFXdata report of Credit Agricole CIB Research before the U.S. jobs report. It states:

- consensus payrolls: **68k**
- unemployment rate expectation: **6.8%**
- average hourly earnings MoM: **0.2%**
- average hourly earnings YoY: **4.5%**

Public route:  
`https://www.teletrade.org/vi/analytics/market-analysis/market-news/3655582`

The 08-Jan historical TeleTrade feed preserves the 07:33 item. The same feed labels scheduled economic-calendar clocks in GMT and places the U.S. jobs release at 13:30 GMT, strongly supporting that the item existed before T0.

**NFP field coverage: 4/4.**

## What materially changed

The 2026-09-21 two-event institutional probe had **0/4 + 0/4** accepted consensus fields. The new public route now demonstrates **4/4 + 4/4 field-complete candidate consensus records** with pre-release chronology.

Therefore the statement “no public field-complete route is known” is no longer current.

However, the frozen acceptance test contains one additional requirement that is not yet satisfied: **immutable version or auditable version history**. Current public pages expose historical article IDs and timestamps, but this mission did not recover a pre-T0 archive capture, modification history, immutable vendor revision ID, or raw historical bytes proving that the currently visible text is byte-identical to the version at T0.

The NFP article timestamp timezone is also inferred from the historical feed’s GMT clock rather than exposed as independent timestamp metadata.

## Scientific adjudication

| Requirement | CPI | NFP |
|---|---:|---:|
| Correct frozen event | PASS | PASS |
| Required fields present | 4/4 PASS | 4/4 PASS |
| Pre-T0 chronology | PASS | STRONGLY SUPPORTED |
| Provenance URL/article identity | PASS | PASS |
| Explicit timestamp | PASS | PASS |
| Timezone independently resolved | chronology sufficient | PARTIAL / feed-clock inference |
| Immutable/auditable version history | **BLOCKED** | **BLOCKED** |

**Current status: PARTIAL_SOURCE.**

The route is materially better than the terminal 2026-09-21 evidence state, but the old reopening condition has not been fully cleared.

## Fail-closed consequence

Do **not**:
- build a new 2021 census yet;
- extend to 2022–2024;
- calculate macro surprises;
- open BTC/ETH returns, taker flow, yields, continuation/reversal, PnL or strategy outcomes;
- inspect 2025/2026 protected outcomes;
- alter the source hierarchy;
- merge to main.

## Smallest legitimate next attack

One of the following is sufficient to continue the reopening probe:

1. recover a pre-T0 archive capture or immutable snapshot for article IDs `3656123` and `3655582`;
2. obtain publisher metadata proving the articles' original publication timezone plus immutable/no-edit version history;
3. recover the upstream eFXdata/Credit Agricole original for the NFP item and a similarly auditable original source for the CPI table, each with pre-T0 chronology and version provenance.

If those checks pass on **both exact events**, issue a new `SOURCE_ROUTE_FEASIBLE/PASS` receipt and only then freeze a consecutive, non-cherry-picked census before opening any outcome.

## Safety / outcome boundary

No market outcome was used for source selection or acceptance. No strategy return, PnL, price response, taker-flow response or Treasury-yield response was computed. The V0.3 hypothesis remains **UNTESTED**.
