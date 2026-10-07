# News Shock Lab V0.3 — Two-Event Reopening Gate V0.2

Date: 2026-10-07
Branch: `news-shock-v03-public-source-recovery-v0.1`
Parent terminal record preserved: `NEWS SHOCK LAB V0.3: FORMALLY CLOSED — SOURCE_BLOCKED`

## Verdict

**TWO-EVENT REOPENING GATE: PASS**
**SOURCE ROUTE: FEASIBLE**
**V0.3 HYPOTHESIS: STILL UNTESTED**

This PASS applies only to the exact two-event reopening condition frozen in the 2026-09-21 closeout. It is not a 2021 census pass, surprise-corpus pass, or permission to open market outcomes.

## Event 1 — CPI 2021-01-13

Frozen T0: `2021-01-13T13:30:00Z`.

The publisher-hosted Danske Bank Research PDF created and last modified on 2021-01-08 contains all four required consensus fields: headline CPI MoM 0.4%, headline CPI YoY 1.3%, core CPI MoM 0.1%, core CPI YoY 1.6%.

Evidence: PDF SHA-256 `a6515f7d42778c3eedb263f201a001f9dc2ad45eca63fb491ab2fb9edf739c79`; CreationDate `2021-01-08T11:58:59Z`; ModDate `2021-01-08T12:10:08Z`; Actions run `37657905625`; artifact `11499386948`.

**CPI: 4/4 PASS.**

## Event 2 — NFP 2021-01-08

Frozen T0: `2021-01-08T13:30:00Z`.

Dow Jones Newswires / Wall Street Journal “Data Week Ahead” survey is preserved in two distinct pre-release wire publications:

- 2021-01-04 wire: original `01-04-21 1412ET` = `2021-01-04T19:12:00Z`; mirror Published `19:12Z`, Modified `19:13Z`.
- 2021-01-07 wire: original `01-07-21 1014ET` = `2021-01-07T15:14:00Z`; mirror Published `15:14Z`, Modified `15:15Z`.

Both preserve the same WSJ survey values: payrolls +50K; unemployment 6.8%; AHE MoM +0.2%; AHE YoY +4.5%. The later record states forecasts were last updated Monday afternoon. The latest modification is 80,100 seconds before T0.

Direct provider download from GitHub Actions was HTTP 403. That transport limitation is recorded separately. No raw-provider hash is claimed. A normalized evidence record is preserved and SHA-256 hashed as `1f14d86fc19c5bc9e3b04de4ba3ba86457bd30cd193ced51bfe2e4b5eeb087e5`.

**NFP: 4/4 PASS.**

## Conflict handling

Other legitimate pre-release sources report different payroll consensus snapshots, including a Credit Agricole/eFXdata witness at 68K. Nothing is averaged or silently reconciled. Vendor identity and snapshot time remain explicit.

## Reopening requirements

| Requirement | CPI | NFP |
|---|---:|---:|
| exact frozen event | PASS | PASS |
| all 4 required fields | PASS | PASS |
| timestamp/vintage strictly before T0 | PASS | PASS |
| timezone resolvable | PASS | PASS |
| event/field identity | PASS | PASS |
| source provenance | PASS | PASS |
| immutable/version-auditable evidence | PASS — static PDF metadata | PASS — two pre-T0 wire versions + Published/Modified chronology |
| post-release recollection sole proof | NO | NO |

## Scientific consequence

The exact 2026-09-21 reopening condition is satisfied.

Authorized next step is to freeze a consecutive, non-cherry-picked source-recovery census before researching additional events. The census must preserve every qualifying vendor snapshot separately and never average conflicting vendors.

No BTC/ETH prices, taker flow, Treasury yields, continuation/reversal, PnL, 2025/2026 protected outcomes, merge to main, live trading, or exchange mutation are authorized. A separate pre-outcome activation freeze remains mandatory after source coverage is adjudicated.
