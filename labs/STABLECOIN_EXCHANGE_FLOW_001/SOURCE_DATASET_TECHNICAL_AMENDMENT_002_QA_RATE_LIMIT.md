# STABLECOIN-EXCHANGE-FLOW-001 — SOURCE DATASET TECHNICAL AMENDMENT 002 — QA RATE LIMIT

STATUS: **FROZEN AFTER SOURCE DATA FAILURE AND BEFORE ANY BTC OUTCOME ACCESS**

LAB: `STABLECOIN-EXCHANGE-FLOW-001`  
MVE: `SEF-BINANCE-PUBLIC-USDT-ETH-1D-001`

## Trigger

Source-dataset run `34896944142` produced a structurally valid protected primary dataset but correctly classified the source gate as `DATA_FAILURE` because the frozen independent QA provider (`https://rpc.mevblocker.io`) returned HTTP 429 rate-limit responses for 23 of the 243 prospectively fixed QA balance calls.

The failed run reported:

- `boundary_invariants_pass = true`;
- `date_integrity_pass = true`;
- `net_flow_arithmetic_pass = true`;
- `boundary_rows = 780`;
- `signal_rows = 779`;
- `qa_calls_expected = 243`;
- `qa_calls_completed = 220`;
- `qa_error_count = 23`;
- every recorded QA error was an HTTP 429 transport/rate-limit failure;
- no BTC market data was accessed;
- no 2025/2026 data was accessed.

## Authorized technical remediation

The immutable output artifact from run `34896944142` may be reused without changing its primary source CSV, primary balances, boundary dates, boundary blocks, entity basket, signal definition or source semantics.

Repeat the **same complete frozen QA subset** only:

- baseline `2022-11-11`;
- every first calendar day present in the protected dataset;
- final boundary `2024-12-29`;
- all nine already-frozen Binance public Ethereum addresses;
- same exact boundary block for each date;
- same QA provider: `https://rpc.mevblocker.io`;
- same USDT contract and `balanceOf` call semantics.

Transport-only correction:

- issue QA calls sequentially;
- enforce a conservative minimum interval between requests;
- use bounded exponential backoff for HTTP 429 and transient transport errors;
- do not substitute or add a different QA provider for this remediation.

## Pass/fail rule

`SOURCE_DATASET_PASS` is allowed only if:

1. the original primary artifact hashes are preserved;
2. all 243 frozen QA calls complete successfully;
3. every QA balance equals the already-frozen primary balance exactly in raw USDT units;
4. no 2025/2026 access occurs;
5. no BTC price/outcome data is accessed.

Any unresolved call or any numerical mismatch remains fail-closed `DATA_FAILURE`.

## Prohibitions

This amendment does **not** authorize changing the address basket, date set, signal, outcome, horizon, costs, statistical test, promotion criteria, source meaning, 2025/2026 lock, or any other scientific parameter.
