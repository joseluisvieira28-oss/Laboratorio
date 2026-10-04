# MEXC ↔ HYPERLIQUID NAS100 — SOURCE BINDING AMENDMENT V0.5.1

Date: 2026-10-04
Status: PRE-OUTCOME SOURCE CORRECTION / OUTCOMES STILL CLOSED

## V0.5 result

Run 37193291935 returned:

`SOURCE_BLOCKED_HYPERLIQUID_NAS100_IDENTITY`

The gate opened zero historical outcomes and performed no lead/lag scoring.

## Root cause

The V0.5 semantic scanner recognized aliases such as:
- NAS100
- NASDAQ100
- USTECH
- US100
- TECH100
- NDX

but omitted the Hyperliquid trade.xyz ticker:

`xyz:XYZ100`

The exact `xyz:XYZ100` instrument was already present in the captured Hyperliquid `xyz` metadata, but the scanner did not classify it as a Nasdaq-100 candidate.

## Independent source evidence

Current public references identify `XYZ100` as the Nasdaq-100 perpetual on Hyperliquid's trade.xyz HIP-3 DEX.

The source correction is therefore:

`NAS100 / Nasdaq-100 -> Hyperliquid xyz:XYZ100`

This amendment does not use or inspect any historical trading outcome.

## Required targeted proof

Before source PASS:
1. verify `xyz:XYZ100` exists in public Hyperliquid xyz metadata;
2. capture its public asset context and L2 book;
3. capture contemporaneous MEXC `NAS100_USDT` index price;
4. require the live price scale to match within 250 bps;
5. require public/no-auth market data only.

PASS verdict:
`HYPERLIQUID_NAS100_SOURCE_PASS__XYZ_XYZ100`

Even after PASS, outcomes remain CLOSED until a new pre-outcome lead/lag freeze is committed.
