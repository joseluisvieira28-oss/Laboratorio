# NVIDIA Event-10M PAPER custody/expiry gate V0.7
FROZEN 29 Oct 2026 before ALL November outcomes. Parent #283 model untouched.

Mission: prepare an independently auditable read-only *single* future signal:
1. Existing frozen V0.5 --decision must capture four public sources and produce a sealed decision.json, in November 2026, NY predeclared decision slot.
2. Store exact decision.json as a completed GitHub Actions uploaded artifact BEFORE the ten-minute target. No outcome request before this.
3. Independently retrieve GitHub Actions artifact metadata and download exact ZIP bytes through GitHub's read-only API with a narrowly scoped temporary GITHUB_TOKEN (GitHub metadata, **no exchange account/login**), verify artifact name/repo/run, created_at BEFORE expiry, ZIP sha256 vs reported digest, exactly ONE decision.json member byte-for-byte matching original raw file. Any mismatch, late upload or authentication fault = CUSTODY_BLOCKED. Do not rely only on a self-asserted timestamp.
4. Only after actual pre-outcome GitHub verification open anonymous public MEXC NVIDIA_USDT WebSocket INDEX ticks. Require exact first exchange timestamp at/after expiry target, within 5sec; receive timestamp >=exchange timestamp <=5sec later; otherwise SOURCE_BLOCKED. Only INDEX_SHADOW outcome, no executed real Event Futures prices.
5. No live order, real trading, account/wallet/private endpoint, paid feeds, pre-existing NVIDIA Oct5–30 protected forward, or September 2026 protected holdout.

CAVEAT: MEXC public INDEX is NOT independently proven equal to the platform's server-chosen Event Futures order openPrice and settlement. Yahoo is not exchange-native primary Nasdaq real-time feed. Therefore numerical binary EV remains provisional even if index-shadow resolves and is not profitable edge certification.

Activation: existing branch-only workflows do not activate scheduled automatic prospective collection. Per GitHub documentation, workflow_dispatch requires registration on default branch. **main must not be changed**, thus the included operator workflow is a dormant reviewable blueprint. Do not claim it runs. The user will need an authorized external read-only runner or explicitly approve default-branch minimal trigger in a separate change, without merging scientific code. Actual prospective records cannot exist on Oct29 for Nov2-30.

Acceptance gate for economic promotion remains: >=60 resolved non-tie qualified paper signals, >=15 distinct market sessions, exact payout direction from pre-decision product snapshot, independent cash as-of observation + server price parity proof, positive time-block bootstrapped lower 95% bound, multiplicity adjustment, positive chronological thirds. No optimization after outcomes.
