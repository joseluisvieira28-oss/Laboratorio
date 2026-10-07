# News Shock Lab V0.3 — 2021 Static Consensus Census V0.1

Date: 2026-10-07  
Branch: `news-shock-v03-public-source-recovery-v0.1`  
Freeze: `NEWS-SHOCK-V03-STATIC-CONSENSUS-CENSUS-2021-001`

## Verdict

**PARTIAL_SOURCE / COVERAGE_BLOCKED**

The prospectively frozen single-family, no-fallback 2021 source route does **not** meet its coverage gate.

### Frozen thresholds

- complete events: **>=20/24**
- CPI complete: **>=10/12**
- NFP complete: **>=10/12**
- accepted complete-event provenance: **100%**

### Observed source-only coverage

- complete events: **8/24**
- complete CPI: **7/12**
- complete NFP: **1/12**
- one additional NFP event (2021-12-03) is static/pre-T0 but only **3/4** required consensus fields were reproducibly recovered, so it is incomplete.

Result:

- total coverage: **FAIL — 8 < 20**
- CPI: **FAIL — 7 < 10**
- NFP: **FAIL — 1 < 10**

## Accepted complete CPI events

1. 2021-01-13 — Danske Weekly Focus 08-Jan — 4/4
2. 2021-03-10 — Danske Weekly Focus 05-Mar — 4/4
3. 2021-06-10 — Danske Weekly Focus 04-Jun — 4/4
4. 2021-08-11 — Danske Vacation Wrap-Up 08-Aug — 4/4
5. 2021-09-14 — Danske Weekly Focus 10-Sep — 4/4
6. 2021-11-10 — Danske Weekly Focus 05-Nov — 4/4
7. 2021-12-10 — Danske Weekly Focus 03-Dec — 4/4

For December the frozen rule uses the **Consensus** column; Danske Bank's own forecast column is not substituted.

## Accepted complete NFP event

- 2021-01-08 — Baker Group / Lunch with Lester, printed 31-Dec-2020 — 4/4.

For 2021-12-03 a pre-T0 Baker static document was recovered with payrolls, unemployment and AHE YoY, but the AHE MoM field could not be reproduced under the present access path. It remains incomplete. No inference or historical-memory substitution is permitted.

## Rejected / unresolved handling

The remaining events were not silently omitted. They remain in the 24-event census as `SOURCE_NOT_RECOVERED`.

That status means only:

> no qualifying issue-specific static document was recovered under this frozen source family and current public-access/search path.

It does **not** assert that an edition never existed.

A Baker document for the February NFP was located only in a state with the actual release values already populated; it was rejected as post-release evidence under the unchanged anti-hindsight rule.

Direct guessed historical URLs and search-index lookups were also attempted for missing issues. Transport/cache failures were not converted into 404/nonexistence claims.

## Scientific interpretation

The earlier two-event reopening result remains valid:

**SOURCE_ROUTE_FEASIBLE / PASS** for the exact frozen CPI and NFP reopening sample.

But that proved **capability**, not adequate historical coverage.

The new consecutive 2021 census demonstrates that this particular prospectively frozen design —

- CPI = Danske Bank Weekly Focus only
- NFP = Baker Group only
- fallback = NONE

— cannot support the required corpus at the frozen coverage thresholds.

This is a source-coverage failure only.

It is **not**:
- `NO_EDGE`;
- a failed macro-surprise hypothesis;
- evidence that consensus data cannot be recovered by another prospectively frozen source design;
- authorization to lower the thresholds or cherry-pick another provider event by event.

## Outcome boundary

No BTC/ETH price, return, taker flow, Treasury-yield response, continuation/reversal, PnL, 2025/2026 protected outcome or trading result was opened.

The V0.3 hypothesis remains **UNTESTED**.

## Legitimate next route

A future attempt must be a **new prospective source design**, frozen before collecting its census. It may, for example, use a deterministic provider hierarchy or separate homogeneous vendor series, but it cannot retrofit Reuters/Scotiabank/TeleTrade/etc. into this failed V0.1 census.

The present route closes as:

**2021 STATIC CONSENSUS CENSUS V0.1 — PARTIAL_SOURCE / COVERAGE_BLOCKED**
