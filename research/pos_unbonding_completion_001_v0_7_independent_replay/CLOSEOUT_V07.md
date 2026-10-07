# V0.7 INDEPENDENT REPLAY CLOSEOUT

Verdict: **SOURCE_HISTORICAL_REPLAY_BLOCKED**.
Not NO_EDGE. This is an operational/implementation block in this run, not a finding that Coreum history is unreplayable or unavailable. No census or market outcome was opened. No CRO extension was opened: local executor/toolchain absence does not establish a chain-specific history failure justifying adaptive fallback.

Parent V0.6: d80bac3e5ef55384a9d5e73541ab650d424d4f5f.
Prospective published freeze: 8bc913d321e5063480f33a67b705193269aac603.
Branch: pos-unbonding-v07-independent-replay-2026-10-07.
Existing V0.7 IBC/source-B branches preserved and not promoted as deterministic application replay.

## Evidence obtained
Official CoreumFoundation source revision 47b7632f4236ec86ffacbfe882524f82b19b398f. Genesis coreum-mainnet-1, initial height 1, genesis time 2023-03-12T00:00:00Z, exact bytes SHA256 5be3b3e0fee69842c4c73eb5f54eb64684420736473f0f5cef0ba6b81d44f253. Historical v1 genesis bytes differ but parsed JSON has no semantic differences. Empty top-level validators require application-derived genesis validator set, still unverified.

Official v1/v2/v3 release inventory, immutable commits, go.mod and upgrade handlers saved. v1 uses Go 1.18 and informalsystems Tendermint 0.34.26; v2 Go 1.18 and CometBFT 0.34.27 replacement; v3 Go 1.20 and CometBFT 0.37.2. Exact dependency bytes are preserved. Candidate binary receipts are separate from an authenticated activation ledger.

Official archive raw blocks 1/2, 5M/5M+1, 10M/10M+1, 15M/15M+1, commits and validator pages saved with SHA256. All three reported block hashes match inherited anchors. Source-A AppliedPlan hints: v2=6,947,500; v3=13,480,000. Empty patch-plan responses do not prove no patch upgrades. These are unverified Source A outputs, not local state or independent computation. No block_results queried.

## Exact outstanding blockers
- Local environment: Go and Docker absent; WSL executable exists but reports Windows Subsystem for Linux not installed. No runnable Linux Coreum application environment. No build/replay attempted under a fabricated environment.
- Correct binary activation sequence remains incomplete: no independently executed on-chain governance/upgrade ledger, patch equivalence or full prefix proof.
- Typed canonical block importer, consensus hash/commit-signature verifier, genesis validator linkage and deterministic application executor have not been implemented or run. Python acquisition is transport only.
- No contiguous 1..15M block acquisition, locally generated ABCI results/state, AppHash comparisons, replay pilot or checkpoint chain. Sparse anchor retrieval is not coverage or replay validation.
- 15M is 2024-01-23, so further contiguous replay is required to cover the full frozen 2024 interval.

No evidence supports calling historical block transport incomplete: sampled requests succeeded. No evidence supports claiming old official releases unavailable: inventory succeeded. No measured evidence supports claiming GitHub Actions categorically infeasible. LOCAL_WORK_RUNNER_PLAN.md specifies the missing importer/executor, toolchains, pilot measurement and genesis-derived checkpoint strategy; it is a runner plan, not executable replay. Actions workflow only audits committed receipts and was not dispatched.

## G2 adjudication and scientific boundary
Independent transport: NO (raw blocks from Source A).
Independent computation/replay: NOT ESTABLISHED (no local execution).
Cryptographic consensus authenticity/continuous completeness: NOT ESTABLISHED.
G2: NOT PASS. A future authentic, contiguous replay may provide independently computed application evidence under the expressly authorized V0.7 route; it cannot claim two independent block providers. Coreum alone cannot satisfy the >=5-chain global gate.
G1/G3/G4/G5 remain unpassed or untested; no >=40 material-chain-day assertion. Materiality 10 bps, actual complete_unbonding and cancellation/slash/hold gates unchanged. Zero prices/returns/PnL/market outcomes, trading/orders/wallet/account/private endpoints/spending. main untouched.

## Reproduction and saved artifacts
Run acquisition/inventory scripts only for source capability; all raw responses and checksum receipts are committed. audit_receipts.py validates saved-byte integrity without network access and always reports replay_pass=false and census_authorized=false. binary_receipts.json records downloaded candidates or precise failures; executable binaries are kept outside Git and can be reacquired using pin_candidate_binaries.py. Existing immutable receipts should be copied to a new run directory before any rerun, because acquisition scripts write their local receipt filenames.
