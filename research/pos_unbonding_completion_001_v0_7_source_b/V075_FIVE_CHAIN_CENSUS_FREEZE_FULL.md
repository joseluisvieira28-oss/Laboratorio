# POS-UNBONDING-COMPLETION-SUPPLY-RELEASE-001 — V0.7.5 FIVE-CHAIN COMPLETION CENSUS FREEZE

Date: 2026-10-07
Parent Coreum Source-B proof commit: 18c50101516d1b75c93fe30456cb7f42b53b5da7
Pre-count freeze branch marker: unbonding-v075-census-freeze-7d2ee458-2026-10-07
Canonical pre-count local freeze SHA256: 7d2ee45837d7b6e07365a90db922815f63a183906e59f15a223acf891de6c8d5
Market outcomes opened: NO
Five-chain completion/materiality counts opened before this freeze: NO

## Locked chains

1. Cosmos Hub / ATOM
2. Osmosis / OSMO
3. Celestia / TIA
4. dYdX Chain / DYDX
5. Coreum / COREUM

No substitution after counts.

## Census sources

ATOM:
- CitizenWeb3 archive block index
- CryptoCrew archive block index
- full independent completion-height sets must match exactly.

OSMO:
- Validatus archive block index
- rpc.osmosis.zone independent historical raw path.

TIA:
- KJNodes historical block index
- Numia independent historical raw path.

DYDX:
- Kingnodes archive block index
- Polkachu archive block index
- full independent completion-height sets must match exactly.

COREUM:
- TX Foundation historical archive as census authority
- independent cryptographic Source B: successful Coreum IBC headers committed on Osmosis, certified by V0.7.4.

## Interval

Actual T_completion in 2023-01-01T00:00:00Z through 2024-12-31T23:59:59.999999999Z.
Later-genesis chains begin at genesis.

## Complete census rule

For each selected chain:

1. Determine exact height bounds by canonical timestamps.
2. Fully paginate `block_search` for `complete_unbonding.amount EXISTS` over the frozen range.
3. Unique returned heights count must equal global reported total_count.
4. Re-run the same query month-by-month; monthly total_count sum must equal global total_count.
5. Fetch `block_results` for every returned completion height.
6. Every indexed height must contain at least one actual `complete_unbonding` lifecycle event.
7. Preserve final amount, delegator, validator, event phase, canonical height and block time.
8. Remove exact duplicate records only.

ATOM and DYDX require exact equality of the two complete independent index height sets.

OSMO and TIA require independent raw audits at the first and last returned completion block of every calendar quarter. Block hash and time must match the independent source; when both sources expose block_results, event digests must match.

COREUM keeps the two V0.7.4 IBC checkpoints as the independent consensus anchors. Same-operator mirrors are not independent.

Any pagination, monthly/global count, canonical-block or cross-source mismatch is fail-closed.

## Materiality

Inherited unchanged:

`R_d` = final native principal actually released by qualifying complete_unbonding events on UTC chain-day d.

`B_d` = canonical historical bonded native tokens immediately before UTC day d.

`M_d = R_d / B_d`.

MATERIAL iff `M_d >= 0.001` (10 bps / 0.10%).

Hard gate:

**>=40 MATERIAL chain-days TOTAL AND >=1 MATERIAL day from EACH of the five locked chains.**

B_d must use explicit historical state. Current-state substitution is forbidden.

## Firewall

No prices, returns, PnL, trading, orders, wallets, authenticated/private exchange endpoints or market outcomes.

NO_EDGE cannot be issued from V0.7.5.
