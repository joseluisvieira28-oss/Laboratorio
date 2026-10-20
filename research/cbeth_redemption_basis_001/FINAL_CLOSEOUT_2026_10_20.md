# cbETH: CLOSED — PREDICTOR_INSUFFICIENT_SAMPLE

20 October 2026. Research only. Draft PR #263 against the original scientific
branch #128; no main merge. **No deployable net edge proved.**

## Definitive new result

The existing September 27 protocol was executed without changing its scientific
rules. Genuine public Ethereum state was obtained free of charge:

| Frozen gate | Actual observation | Decision |
|---|---|---|
| Protocol conversion anchor | All five historical sentinels plus current finalized block | SOURCE_PASS |
| Direct cbETH/WETH market source | Four pools discovered; three qualified | SOURCE_PASS |
| Direct versus Multicall bytes | 9/9 exact comparisons at three fixed blocks | PASS |
| Daily source census | 731/731 valid days, 2023–2024, no missing days | PREDICTOR_CENSUS_PASS |
| Calibration | 457/457 days, original nearest-rank q10/q90 | STATE_CALIBRATION_PASS |
| Discovery source coverage | 184/184 days, 2024H2 | PASS |
| De-clustered transition events | **3 total / 2 DISCOUNT_EXTREME / 1 PREMIUM_EXTREME** | **FAIL against 20 / 6 / 6** |

**Canonical terminal verdict: PREDICTOR_INSUFFICIENT_SAMPLE. Close this exact
LAB_ID under its original no-rescue tree.** The convergence program was NOT
executed. No economic outcome statistic or PnL was opened. Historical 2025 OOS
and protected 2026 outcomes remain shut. Current finalized source-only state
and the five source sentinels are the ones explicitly required by the parent
source protocol; they are not a historical 2026 outcome study.

This is **not NO_EDGE**, COST_CEILING_FAIL, SOURCE_BLOCKED or a profitable
candidate. The source works; the predeclared scientific sample does not exist
at the required size in the frozen window. Do not relabel a sample failure as
evidence that all cbETH opportunities are unprofitable.

Immutable selected pool: `0x840DEEef2f115Cf50DA625F7368C24af6fE74410`, fee tier
500, selected by historical coverage, then finalized liquidity, then fee.
Calibration q10 = approximately -58.48735 bps; q90 = -3.47031 bps. These are
relative distribution tails: PREMIUM_EXTREME does not necessarily mean a
positive absolute premium to redemption. Neither threshold may be retuned.

## Economic interpretation and resource decision

Potential concession payer: a holder selling cbETH to obtain immediate liquidity.
Neither that payer's concession nor our capture of it is established as net PnL.
The on-chain exchange rate is an accounting conversion anchor, not an executable
public cash-redemption bid. Coinbase's official wrapping/unwrapping instructions
require an eligible region/account and return the underlying staked asset.
There is no proof here of this user's eligibility, waiting time, executable
trade size, gas/MEV, redemption fees, financing or net cashflows.

Therefore the realistically capturable economic ceiling is **unmeasured**, not
zero or positive. No costs were fitted after inspecting the source sample.
The parent explicitly forbids PnL/cost fitting at this stage. Its sample failure
is enough to stop this exact study before building a bot or committing capital.
No pool swap, tail removal, alternate quantile, clock, window or horizon rescue.
No additional collector or recurring automation was created.

Official references reviewed before source execution:
- https://help.coinbase.com/en/coinbase/coinbase-staking/staking/wrap-unwrap-staked-eth
- https://www.coinbase.com/cbeth
- https://blockmachine.io/docs/ethereum-rpc
- https://ethereum.publicnode.com/

## Chronology, transport and reproducibility

Original parent HEAD: `41909a1ac0f86166e7fac4a3deb9f9c9a120b35d`.
The economic/predictor freeze predates observations: original design commit
`f7524d8610c7748d5afff7ba315b03a49a662d5d`, design blob
`00864da8c28785bfdf64780226576017da160929`.

Local necessary-source transport freeze:
`fcccadced87d26723c5f652d117fb5e6d3f8af48`, 08:49:20 UTC, before the local
08:50 necessary-anchor observation and full source gate at 08:50:32 UTC.
Git push failed because the local credential helper could not run; connector
publication commit `0c204170fd449eb4be0bfed31eb7df24c872a0f0` followed. Do not
mistake the later publication time for the original parent scientific freeze.

The original full source script was run unchanged, with an external 240-second
process cap; it completed normally. Source and equivalence receipts are preserved.
The first sequential census was interrupted after a progress count of 50/731,
zero errors, to avoid unnecessary elapsed time. No distributions or events had
been inspected. Its transient partial rows were not a separate scientific trial.

Concurrency amendment `f63862775080cecc8bf2ce1224ab9dd2b684bb2c` was committed
before the adapted census. An initial adapter rejected Windows CRLF text before
any adapted RPC work; normalization fix
`2eb42de312fa0742c954c9f891c2d4ee49b025c5` then allowed execution. Eight workers
performed the original global binary search independently for each fixed day,
verified the predecessor, used exact blockHash/requireCanonical, and restored
calendar order. No scientific source file was edited. Completed census receipt:
09:13:05 UTC. All 731 checkpoints are represented in the preserved canonical rows.

Canonical census row-set SHA256:
`07ff2d7173232d11b68812def0909338f3baabf97f529417c7496d5283e92892`.
This digest is recomputed from the actual rows, not merely compared between
self-reported manifest fields. Compressed canonical data and byte-file hashes
are preserved in EVIDENCE_MANIFEST.json. Full source/census receipts contain
decoded state; they are not falsely advertised as raw RPC packet archives.
Raw bytes are retained for the bounded necessary-header/rate probe; Multicall
equivalence receipts additionally retain the exact nine direct/compressed values.

Offline reproduction:
`python research/cbeth_redemption_basis_001/verify_frozen_evidence.py`.
It checks original Git blob hashes, actual data digest, calendars, flags, pool
consistency, and reproduces calibration/sample results using unchanged parent
programs in an isolated directory. It must reject any outcome receipt in this
insufficient-sample state. Three adversarial parent-firewall tests and two
anchor/provenance tests are included. These checks are integrity evidence, not
an economic promotion.

Public-source Ubuntu run: **39396485826**, commit
`0c204170fd449eb4be0bfed31eb7df24c872a0f0`, SUCCESS. Necessary-anchor only,
2/2 tests; artifact **12250909731**, zip SHA256
`f7f03ef4812ded5aa207bcb5015a185361fc451fd4b9ed2e2e269b0ed7af3dd7`.
Full census was executed locally, not in that CI run. Offline final evidence
CI run/commit is linked in the PR description after execution.

## Real-state audit of prior work

GitHub API snapshots with exact branch heads are in
`receipts/diamond_cbeth_20261020/pr_audit_snapshot.json`.
All audited PRs are drafts and unmerged. Main remained
`75fb36c8337c3221b7551c513e049cd472dad231` when checked during this task.

| PR | Actual scientific/operational meaning preserved |
|---|---|
| #262 | Hardstop proposal tested on its branch; no main merge or PC installation. It does not prove every existing executor is off. |
| #260 | 0/3 OKX single-snapshot carry screens cover the hypothetical frozen cost model; not a universal funding no-edge. Exact test closed. |
| #261 | Current VRP execution routes have insufficient source/power. Historical IV-minus-RV phenomenon is not option-selling net profit. No rescue. |
| #259 | Aave SQD complete frozen census SOURCE_BLOCKED; one genuine event is not a complete sample or capturable keeper profit. No retry here. |
| #258 | Payer-first prioritization is governance, not an independent economic result. |
| #145 | Exact Compound 30m child DISCOVERY_FAIL_NO_PROMOTION. No asset exclusion, horizon change or subset rescue. |
| #172 / #192 | Coverage union correction below; outcomes remain shut. |

**Hyperliquid correction:** #262's narrow original-branch discussion omitted
the recovery branch's later receipts. The original branch has 6 in-window file
paths; recovery HEAD `0476a09b436dd222bdea70fe2eaee0a3a51a0ba0` has 30,
including those inherited 6. The union is 30, not 6 or 36. Even accepting every
file as valid and giving all 96 hours of Oct20–23, the optimistic maximum over
these two inspected branches is **126/336 <320**. This is a tree-path upper
bound, not full payload quality verification or the canonical terminal verdict.
Its frozen adjudicator remains unavailable until Oct24 00 UTC. No backfill,
remote collector operation or early trading outcome was attempted.

## Safety and final disposition

Zero orders, exchange/private account calls, wallets, money, credentials,
deployment, Render changes, main merge or remote executor management.
Public JSON-RPC eth_call is read-only. Sources/ project references untouched.

**Stop this exact cbETH study. No bot. No promotion. No claim of profitability.**
