# MSEL-002 — Migration Discovery Transport Amendment V0.1

Date: 2026-09-20
Status: **TRANSPORT-ONLY / PRE-OUTCOME**

Runs 35500546375 and 35500588031 failed before any migration outcome was acquired.

- run 35500546375: Node import compatibility failure before source access.
- run 35500588031: source client constructor compatibility failure after only the end-timestamp resolver; no migration stream was opened and no candidate outcome was observed.

The scientific freeze, cohort, source network, Pump/PumpSwap IDs, migrate discriminator, 24h/72h horizons, matched sets, statistics, thresholds and verdict gates remain unchanged.

Transport is replaced only by direct use of SQD's documented public `solana-mainnet/finalized-stream` HTTP endpoint with deterministic continuation from the last returned block + 1, fail-closed on 204/empty/no-progress responses, and bounded retry of transient HTTP statuses.

No outcome was used to choose this amendment.
