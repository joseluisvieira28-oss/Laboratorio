# MSEL-002 — Uniblock Transport Qualification Freeze V0.1

Status: **FROZEN BEFORE EXECUTION / SOURCE-ONLY / ECONOMIC OUTCOMES LOCKED**
Date: 2026-09-19
Branch: `memecoin-metadata-duplication-v0.1`

## Purpose

Qualify an alternative standard read-only Solana JSON-RPC transport for the already-frozen
`PRIOR_EXACT_IMMUTABLE_IDENTITY_REUSE_6H` source/prevalence experiment.

The scientific window, identity definition, thresholds, Pump program, Token Mint Authority,
IDL, discriminator and economic-outcome lock remain unchanged.

## Why this remediation is allowed

The frozen source authority explicitly permits provider substitution before completion of
row-level prevalence when exact raw JSON-RPC evidence and point-in-time semantics are preserved.

The prior official-mainnet V0.2 run proved both frozen time boundaries and enumerated 9,564
successful Token Mint Authority signatures in the exact 12h window, but was cancelled by
wall-clock/rate-limit pressure after fetching only a partial transaction set.

Vibe Station subsequently failed because its provider history starts after the frozen source
start. This is a transport limitation, not a source-mechanism result.

## Frozen qualification target

Provider:
`https://api.uniblock.dev/uni/v1/json-rpc?chainId=solana`

Frozen source timestamps remain:
- source_start: `1757101139`
- candidate_start: `1757122739`
- source_end: `1757144339`

Qualification may:
- prove start/end slot boundaries;
- find the same end anchor semantics;
- enumerate successful Token Mint Authority signatures inside the frozen 12h window;
- persist raw JSON-RPC responses and hashes;
- compare count and deterministic signature-set SHA256 with an independently reacquired official-mainnet signature census.

Qualification MUST NOT:
- fetch candidate future outcomes;
- compute prevalence labels;
- compute graduation/migration/trading outcomes;
- change the 6h lookback, window, identity rules or sample gates.

A PASS only qualifies Uniblock as an alternative transport for the existing frozen source/prevalence collector.
