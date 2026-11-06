# V3 collector integration — 6 November 2026

**Technical GO for manual quote-only collection; expiry economics NO-GO; LIVE NO-GO.**
No prospective collection initiated: **0/20**. No scheduler/workflow added.
The CLI only performs a controlled diagnostic. Prospective mode is a library
entry point; it does not run automatically. This verdict does not authorize
orders, economic conclusions or any infrastructure activation.

## Tested behavior

`collector.py` uses four allowlisted public GETs: USDC option instruments,
BTC_USDC index and concurrent call/put books (five levels). No auth, private
methods, retries or arbitrary host. Redirects refused, timeout 15s, response
bound 12MB. Raw successful/error HTTP bodies are saved before validation;
transport errors are recorded even when no response bytes exist.

ATM selection follows V2's nearest complete call/put strike with lower strike
tie-break, <=1% moneyness, next-day 08:00 UTC expiry. Selected metadata must
match BTC/USDC/linear identity, symbol/strike/side/expiry, size 1, minimum .01,
taker rate .0003 and positive tick. Changed terms fail closed. Books enforce
>=.05 top depth, quote age -3..10s, <=1s skew and <=10s distance to index
receipt for **each** book. This index endpoint has no market-event timestamp;
the recorded client receipt is explicitly used, not invented source time.

Prospective mode enforces [08:05,08:10) UTC on all starts, receipts and decision.
One exclusive daily claim is made before requests, so failures cannot be
silently replaced by a better snapshot. At 20 valid receipts it stops. Each
attempt has its own directory; raw files, manifest and receipt use exclusive
creation and fsync. Invalid attempts retain error reasons, available raw bytes,
hashes and manifest. Crashes/disk failure can leave an incomplete claimed
attempt; retain it as incomplete, never delete/retry as a fresh session.
Never run multiple independent roots for the same prospective cohort.

Immutability is application-level non-overwrite plus hash detection, not WORM
storage or external timestamp proof. Repository commits anchor the evidence.
Precommit protocol and collector hashes are recorded. Production operations
must retain the same cohort root and separately reconcile incomplete attempts.

## Python verification

Python 3.12.14, existing pip-free venv, zero installed dependencies. Executed:

```
.v3-offline/Scripts/python.exe research/deribit_v3_microstructure/run_checks.py --out research/deribit_v3_microstructure/verification-published-2026-11-06
```

**66/66 PASS**, no failures/errors: V2 30, Economic Proof Engine 14, V3 22.
Socket connections denied during the suite. New tests cover complete session,
exclusive writes/day claims, bounds/late decision, bad metadata/expiry/moneyness,
ATM tie-break, disallowed endpoints, failed decoding retaining both concurrent
responses, HTTP 429 retaining body, 20-session cap and saved-observation tamper.
See `tests-published-2026-11-06.txt` and matching receipt/source hashes.
Earlier 63/65-pass receipts are retained as intermediate evidence. An initial
standalone run failed due to Windows temporary-folder permissions; the existing
workspace-temp harness resolved it, without modifying V2. Legacy synthetic
settlement stdout is fixture behavior, not real PnL or validated delivery fees.

## Controlled public observation (not cohort)

Exactly four public requests; no retries. Decision 2026-11-06 09:05:12.663282 UTC,
outside frozen window. Exact six evidence files are packaged losslessly in
`controlled-observation-2026-11-06.zip`; originals also remain locally under
`controlled-evidence/controlled_observation/`. ZIP extraction is offline only.
Index 75770.97; ATM BTC_USDC-7NOV26-76000-C/P, expiry 7 November 08:00 UTC.
Call bid/ask 585/620; put 800/855. Best bid/ask size call 5.73/10,
put 4.2/4.2. Book skew 149ms; per-book index distances 1203.942/1352.942ms;
quote ages 1389.869/1540.005ms. Technical PASS, **prospective=false**, PnL null.
Four raw response SHA256 and manifest SHA256 preserved. `audit_controlled.py`
recalculates hashes, ATM/expiry and book synchronization from saved data;
`controlled-audit-2026-11-06.json` records PASS. It shares the tested validation
functions, so it is a second offline execution, not independent implementation.
The observation retains the exact collector hash used; subsequent local changes
only add HTTP-error retention, locale-independent month naming, cohort cap and
fee reference. Their behavior is covered by the final suite, without a second
market observation. Historical pinned replay stays 3 attempts, 2 technically
valid rejections, 0 V2 cost-gate passes, separate from this diagnostic and V3.

## Delivery audit and unresolved blocker

Rechecked 6 November:
[Fees](https://support.deribit.com/hc/en-us/articles/25944746248989-Fees), marked
updated 5 November 09:16, exempts daily options but separately lists USDC linear
options at .015%, capped at 12.5% option value. The
[linear guide](https://support.deribit.com/hc/en-us/articles/31424932728093-Linear-USDC-Options),
updated 15 September, describes the usual ITM option delivery fee during
conversion into expiry futures, with no second fee on the generated futures.
Neither expressly resolves **BTC_USDC daily** precedence. Search found no
authoritative product-specific clarification. **delivery_fee_status=UNVERIFIED;
net_pnl=null**. No weekday inference and no invented zero charge. Forced
liquidation is distinct; it cannot resolve the expiry fee classification.
No support message or account/private fee query was sent.

## Boundaries and remaining scientific work

GO applies only to manual technical quote capture under the tested rules;
no 20-session collection was started here. Entry/expiry cash flows, forecasts,
paired economics, maker/combo execution and the full preregistered downstream
analysis are not certified by this collector or diagnostic. Fees block economic
conclusions, not preservation of public quote evidence. Stop technical capture
on integrity failures and retain rejected attempts. LIVE remains NO-GO.

Changed only V3 files. Frozen V2, Economic Proof Engine sources, main and workflow
files unchanged. No orders, exchange credentials, paid resources, schedules,
merges or expenses.
