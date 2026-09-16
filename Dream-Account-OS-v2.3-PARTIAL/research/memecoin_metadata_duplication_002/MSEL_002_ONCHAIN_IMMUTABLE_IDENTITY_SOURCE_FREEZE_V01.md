# MSEL-002 — On-Chain Immutable Identity Reuse — Source / Prevalence Freeze V0.1

Status: `SOURCE_PREVALENCE_FROZEN / ECONOMIC_OUTCOMES_LOCKED`

This is the source-remediated continuation of the independent MSEL-002 copycat/metadata-reuse mechanism. It is NOT a rescue or retune of MSEL-001 Pilot25 V14. The unavailable pump.fun website metadata in the public CCS'26 deposit is not approximated with fuzzy matching.

## Primary source-remediated exposure

`PRIOR_EXACT_IMMUTABLE_IDENTITY_REUSE_6H`

At candidate launch C, exposure is TRUE iff there exists an earlier Pump CREATE launch P satisfying all of:

1. `slot(P) < slot(C)`; same-slot predecessors are not accepted because transaction index is not required by this source route;
2. `0 < block_time(C) - block_time(P) <= 21,600 seconds`;
3. exact UTF-8 `name(P) == name(C)` with no case-folding, trimming, Unicode normalization or fuzzy matching;
4. exact UTF-8 `symbol(P) == symbol(C)` with the same no-normalization rule;
5. CREATE `uri` values canonicalize to the same immutable content-addressed target;
6. `origin_creator(P) != origin_creator(C)` as exact Solana addresses.

Same exact creator repeats are recorded as `SAME_CREATOR_CLONE_6H`, never primary exposure.

Different creator addresses are NOT asserted to be different beneficial owners. Creator/funder clustering remains a later sensitivity requirement if the mechanism reaches economic validation.

## Immutable URI canonicalization — frozen

Accept only these forms:

### IPFS

- `ipfs://<CID>[/path...]`
- HTTP(S) path-gateway URI containing `/ipfs/<CID>[/path...]`
- HTTP(S) subdomain-gateway URI whose first hostname label is `<CID>` and a later hostname label is exactly `ipfs`

Canonical form:
`ipfs://<CID>[/path...]`

Rules:
- CID bytes/string are kept exactly as supplied; no case conversion;
- query and fragment are dropped only for HTTP(S) gateway wrappers;
- path after the CID is retained exactly except a leading slash is normalized to one slash.

### Arweave

- `ar://<TXID>[/path...]`
- `https://arweave.net/<TXID>[/path...]`
- `http://arweave.net/<TXID>[/path...]`

Canonical form:
`ar://<TXID>[/path...]`

All other URI forms are `NON_IMMUTABLE_OR_UNSUPPORTED` and cannot create primary exposure.

No URI is dereferenced. No current HTTP metadata or pump.fun API is queried. The feature is constructed entirely from information committed in the CREATE instruction and knowable at launch.

## Historical protocol authority

Pump program:
`6EF8rrecthR5Dkzon8Nwu78hRvfCKubJ14M5uBEwF6P`

Pump Token Mint Authority, independently documented by the CCS'26 paper:
`TSLvdd1pWpHVjahSpsvCXUbgwsL3JAcvokwaKt1eokM`

Official IDL authority immediately before the study window:
`pump-fun/pump-public-docs@7645c16c68ae9dd3a7487b543edcdc94adf7b5e0`

Pinned `idl/pump.json` Git blob SHA:
`5ef1cbb696a0957cc7e4e191652d439d797982e9`

Frozen CREATE discriminator:
`[24,30,200,40,5,28,7,119]`

Frozen CREATE args:
`name:string, symbol:string, uri:string, creator:pubkey`

## Blind time-window selection

Eligible source regime:
`[2025-09-01T00:00:00Z, 2025-11-01T00:00:00Z)`

This interval is entirely before the Mayhem regime used as a separate population by MSEL governance.

Seed:
`MSEL-002-URI-REUSE-V1|blind|source-prevalence|2026-09-16`

Deterministic mapping:

1. `d = SHA256(seed UTF-8)`;
2. `r = unsigned_big_endian(d[0:8])`;
3. total eligible seconds = `5,270,400`;
4. full pilot span = `43,200` seconds (12h);
5. `offset = r mod (5,270,400 - 43,200)`;
6. source start = `2025-09-01T00:00:00Z + offset seconds`;
7. warmup/reference window = first 21,600 seconds (6h);
8. candidate window = next 21,600 seconds (6h).

No alignment to day/hour boundaries is permitted after mapping.

The 6h lookback is a pre-outcome low-latency-copy mechanism definition, not a parameter to widen if prevalence is low.

## Source acquisition route

Primary source is standard read-only Solana JSON-RPC.

1. locate slots bracketing source-start and source-end with `getBlockTime` and confirmed-slot queries;
2. find nearby transactions containing the Token Mint Authority to create time-local signature anchors;
3. use `getSignaturesForAddress(Token Mint Authority)` from the end anchor backward only until before source-start;
4. fetch full transactions by `getTransaction`;
5. retain only successful transactions containing a valid Pump CREATE under the pinned IDL;
6. preserve raw signature pages and full raw transaction responses with SHA-256 receipts before derived feature rows.

Provider may be Helius archival RPC when an authorized key is available; otherwise standard Solana public RPC may be attempted. Provider substitution is allowed only before any row-level prevalence is opened and must preserve exact raw JSON-RPC evidence; if historical coverage cannot be proven, classify `SOURCE_ACCESS_BLOCKED`.

No transaction submission or chain mutation is permitted.

## Source/prevalence gates — frozen before rows

Candidate CREATE sample must satisfy ALL before any future economic outcome may be acquired:

1. `candidate_create_count >= 2,000`;
2. `immutable_uri_candidate_count >= 500`;
3. `primary_cross_creator_exposed_count >= 30`;
4. `primary_unique_identity_groups >= 10`;
5. `primary_unique_candidate_creators >= 20`;
6. largest single immutable-identity group contributes `<= 50%` of primary exposed candidates;
7. source start/end boundaries proven;
8. all retained CREATE rows have unique mint + signature/instruction identity;
9. zero unresolved decode/schema ambiguity among rows used for primary exposure.

If any sample gate fails, classification is `INSUFFICIENT_SAMPLE` or `SOURCE_DATA_FAILURE` as applicable. Do NOT widen the 6h lookback, loosen exact-match rules, add fuzzy matching, include same-creator clones, move the time window, or search a second window as rescue.

## What Source/Prevalence Stage may compute

Allowed:
- launch counts;
- immutable URI eligibility counts;
- primary exposure count/rate;
- same-creator clone count as descriptive negative-control population;
- exact identity-group sizes;
- creator counts;
- URI scheme counts;
- source integrity statistics.

Forbidden:
- price returns;
- sell/buy outcomes after candidate launch;
- graduation/migration status;
- liquidity survival;
- future transaction path;
- +100% winner / -80% catastrophe labels;
- any MSEL-001 V14 outcome joins;
- post-prevalence changes to source/prevalence thresholds.

## Next authority if Source/Prevalence passes

A separate economic-outcome freeze must be committed BEFORE acquiring or decoding any post-launch candidate outcomes. It must include migration/PumpSwap continuity from the start rather than relying on absence of migration in a sample.

Governance remains research-only / fail-closed / no live trading / no exchange or chain mutation / no main merge / no Render / no post-outcome tuning.
