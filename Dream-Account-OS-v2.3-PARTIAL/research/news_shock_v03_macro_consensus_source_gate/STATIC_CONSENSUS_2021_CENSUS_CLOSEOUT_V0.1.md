# News Shock Lab V0.3 — Static Consensus 2021 Census Closeout V0.1

Date: 2026-10-07  
Branch: `news-shock-v03-public-source-recovery-v0.1`

## Verdict

**COVERAGE_BLOCKED — STATIC CPI/Baker NFP ROUTE FAILS FROZEN 2021 GATE**

The prospectively frozen source-only census was executed on GitHub Actions without opening any market outcomes.

Frozen gate:
- >=20/24 complete events
- >=10/12 CPI
- >=10/12 NFP
- 100% provenance

Canonical diagnostic run: `37680455007`  
Artifact ID: `11508148947`  
Artifact digest: `sha256:203f72780bb572b198978fa474214dbf48ed7e28112892019393f1d03edd6955`

## Result

- CPI complete: **10/12**
- NFP complete: **1/12**
- Total complete: **11/24**

The route therefore fails the frozen gate.

### CPI

Danske Bank Weekly Focus achieved the frozen minimum exactly: **10/12** complete. July and August were incomplete because the weekly publication route did not provide qualifying issues for those release windows.

### NFP

All 12 Baker Group PDFs were retrievable and carried dated/printed-as-of audit trails. Payroll and unemployment fields were generally present, and AHE YoY was present across most of the year.

However, the frozen NFP specification requires **both AHE MoM and AHE YoY**. The diagnostic rerun explicitly searched the flattened PDF text for Average Hourly Earnings MoM and YoY. Only the January frozen event demonstrated both required AHE dimensions. The remaining months lacked a defensible AHE MoM field in the frozen source family.

This is not a transport failure and not a parser-only failure: the second diagnostic used whole-document flattened-text searches and preserved snippets showing the available rows. The source family is structurally field-incomplete for the required NFP schema.

## Scientific consequence

This route is closed as **COVERAGE_BLOCKED**. The gate may not be lowered and Baker Group may not be silently supplemented inside this frozen route.

This does **not** test the macro-surprise hypothesis and is not `NO_EDGE`.

## Outcome boundary

No BTC/ETH prices, returns, taker flow, Treasury-yield response, continuation/reversal, PnL, 2025/2026 protected outcomes, trading, exchange mutation, or main merge were used.
