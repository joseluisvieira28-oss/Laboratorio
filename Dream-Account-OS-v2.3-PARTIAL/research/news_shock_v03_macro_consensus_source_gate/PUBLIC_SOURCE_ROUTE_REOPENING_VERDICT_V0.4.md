# News Shock Lab V0.3 — Public Source Route Reopening Verdict V0.4

Date: 2026-10-07  
Branch: `news-shock-v03-public-source-recovery-v0.1`

## Verdict

**SOURCE_ROUTE_FEASIBLE / PASS**

This PASS is narrow: it clears the exact two-event reopening condition from the 2026-09-21 terminal closeout. It does **not** test the V0.3 hypothesis and does **not** authorize market outcomes.

The old closeout remains historically correct for the evidence available on 2026-09-21. A new public route was discovered on 2026-10-07.

## Why the previous PARTIAL_SOURCE is now adjudicated PASS

The inherited condition was not “Wayback capture required.” It required:

> immutable version **or auditable version history / audit trail** that distinguishes the contemporaneous forecast from later corrections.

No acceptance criterion is changed here.

### CPI — US_CPI_2021-01-13

Danske Bank’s *Weekly Focus* dated **8 January 2021** is an issue-specific static PDF on the original publisher domain. The report date is repeated throughout the issue. Its calendar for Wednesday 13 January contains:

- CPI headline MoM consensus: **0.4%**
- CPI headline YoY consensus: **1.3%**
- CPI core MoM consensus: **0.1%**
- CPI core YoY consensus: **1.6%**

The report is five calendar days before T0. The URL/filename identifies the specific 08-Jan edition. Separate adjacent Weekly Focus editions (18-Dec-2020 and 15-Jan-2021) remain separately addressable, which establishes edition-level versioning rather than a mutable calendar row.

**CPI: 4/4 fields + pre-T0 + provenance + auditable edition identity = PASS.**

### NFP — US_NFP_2021-01-08

The Baker Group’s *Lunch with Lester* dated **31 December 2020** contains:

- NFP consensus: **68k**
- unemployment rate: **6.8%**
- AHE MoM: **0.2%**
- AHE YoY: **4.5%**

The document embeds a stronger temporal/version witness than a simple header date:

> `This report was printed as of: 12/31/2020 9:31 AM`

and the future 8-Jan rows already contain estimates while the `Actual` column is still `--`.

That internal state distinguishes the contemporaneous forecast edition from a post-release populated calendar. The report identifies Bloomberg, LP as the source for its economic indicators.

**NFP: 4/4 fields + pre-T0 + provenance + auditable printed-as-of state = PASS.**

## Anti-hindsight decision

The two frozen events satisfy the original reopening test through **audit trail**, not through a newly invented weaker standard.

No post-release actual was used to choose the consensus value. No market price, BTC/ETH return, yield response, taker flow, continuation/reversal, PnL or protected 2025/2026 outcome was opened.

## Critical source-design finding

Consensus is not timeless. Different providers and snapshots can legitimately disagree (for example, NFP estimates changed between earlier weekly material and release-morning material). Therefore a full census may not cherry-pick the “best-looking” consensus.

Before collecting the next event, the lab must prospectively freeze:

1. source family by event family;
2. snapshot cadence/cutoff;
3. no-fallback or explicit fallback rule;
4. missing-data treatment;
5. conflict treatment.

## Consequence

The 2026-09-21 terminal state **SOURCE_BLOCKED** is legitimately reopened.

Current state:

**NEWS SHOCK LAB V0.3 — SOURCE ROUTE PASS / HYPOTHESIS STILL UNTESTED**

Next step is a consecutive, outcome-blind census under a new prospective freeze. Market outcomes remain closed.
