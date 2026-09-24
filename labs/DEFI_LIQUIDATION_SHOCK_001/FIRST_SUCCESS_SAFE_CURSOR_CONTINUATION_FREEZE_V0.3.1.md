# DEFI-LIQUIDATION-SHOCK-001 — FIRST-SUCCESS SAFE-CURSOR CONTINUATION FREEZE V0.3.1

Date: 2026-09-24
Status: FROZEN PRE-EXECUTION / SOURCE-ONLY / OUTCOME-BLIND / FAIL-CLOSED

## Purpose

Resume the cancelled V0.3 official-public-Solana-RPC first-success boundary crawls for Marginfi and Save/Solend 0x0c from the last independently accepted complete pages, without restarting the scientific page budget and without accepting orphan/incompletely evidenced pages.

This is technical continuation only. It does not change program IDs, instruction identities, discriminators/tags, lower boundaries, scientific windows, source, success semantics, ordering, or any economic hypothesis.

## Shared rules

- Transport: official public Solana RPC only.
- `getSignaturesForAddress` finalized, limit 1000, strictly `before` the accepted safe cursor.
- Unique signatures mandatory across accepted parent pages plus continuation pages.
- Block time must be non-increasing across the full parent + continuation sequence.
- V0.3 total page budget remains 5000 pages. V0.3.1 receives only the unused remainder.
- Accepted parent pages are part of the scientific continuity chain and MUST be included when Phase B later inspects successful RAW transactions oldest-to-newest.
- Parent pages beyond the independently accepted page are ignored even if present in a cancelled artifact.
- Lower boundary crossing is determined on the combined chronological crawl.
- RAW adjudication uses successful signatures only; exact slot, `meta.err == null`, exact program ID and exact discriminator/native tag are required.
- First exact RAW match in oldest-to-newest order is the first-success boundary PASS.
- Lower boundary crossed + no exact match in the complete accepted parent + continuation slice => NO_MATCH_IN_EARLIEST_SLICE.
- Exhausting the preserved total 5000-page budget before crossing lower boundary => RPC_HISTORY_BLOCKED.
- Any continuity/hash/structure/slot/meta inconsistency => SOURCE_ANOMALY_FAIL_CLOSED.
- No page count reset and no rescue budget.

## Marginfi V0.3.1

Scientific identity:
- program: `MFv2hWf31Z9kbCa1snEPYctwafyhdvnV7FZnsebVacA`
- instruction class: `lending_account_liquidate`
- discriminator: `d6a997d5fba756db`
- lower boundary: `2023-02-07T15:47:04Z`

Parent cancelled run:
- run: `35771014450`
- artifact ID: `10713843479`
- artifact name: `dls-marginfi-first-success-rpc-v03`
- artifact SHA256 from recovery receipt: `d33e966a59d76af2096920e4f169a406d7dcf7fcf4bf17509ab5000abdf727c3`

Accepted continuity:
- accepted parent pages: `1..205`
- accepted signatures: `205000`
- page 205 SHA256: `72fce2cff5cc66d3b8881fbd7e9b6d17743f2c8fb30370073fd337ca3276f6b0`
- resume-before signature: `53dZ2HZHdFMisHmhPS1BS4pXhaD98YggaS7zYwshBFwza5mntJTANDvWthxagjgxc39eTg8eCq5eoyqFfTrKVW6m`
- resume slot: `238600457`
- resume blockTime: `1703805655`
- cursor tx status: success
- checkpoint claimed page 206/signatures 206000 but page 206 was absent from the persisted artifact, therefore page 206 is NOT accepted.

Budget:
- total frozen V0.3 pages: `5000`
- accepted pages: `205`
- maximum new continuation pages: `4795`

## Save/Solend 0x0c V0.3.1

Scientific identity:
- program: `So1endDq2YkqhipRh3WViPa8hdiSpxWy6z3Z6tMCpAo`
- instruction class: `LiquidateObligation`
- native tag: `0x0c`
- lower boundary: `2021-12-08T00:00:00Z`
- scientific window: `[2021-12-08T00:00:00Z, 2025-01-01T00:00:00Z)`

Parent cancelled run:
- run: `35771022352`
- artifact ID: `10714501324`
- artifact name: `dls-save0c-first-success-rpc-v03`
- artifact SHA256 from recovery receipt: `b5284d198c7e5101bdd2ac5c0136c51248dbf002e1f42051e84091ab098bbf6b`

Accepted continuity:
- accepted parent pages: `1..217`
- accepted signatures: `217000`
- page 217 SHA256: `f21c44c8525bd11b0f1227d709cce16b1a79e10429570faa6766dfa1111a269c`
- resume-before signature: `4XfzrMP3m4vJSBmnsoqA9kG3pjRhjBvbCRrTeh3162FSzBoyVegaFxiCWxyaxrf5yxEGmtjoyM5qA5W9KUHLAyfu`
- resume slot: `175929092`
- resume blockTime: `1675484461`
- cursor tx status: failed with `InstructionError Custom 42`; cursor-only, never a realized event
- artifact contains page 218, but the cancellation recovery log did not establish page 218 as completed; page 218 is preserved as orphan evidence and MUST be ignored.

Budget:
- total frozen V0.3 pages: `5000`
- accepted pages: `217`
- maximum new continuation pages: `4783`

## Firewall

prices=false
returns=false
pnl=false
direction=false
event_outcomes=false
protected_2025_2026_market_outcomes=false
live_trading=false
orders=false
wallets=false
exchange_mutation=false
paid_source=false
account_creation=false
merge_main=false

A SOURCE/TRANSPORT blocker is never NO_EDGE.
