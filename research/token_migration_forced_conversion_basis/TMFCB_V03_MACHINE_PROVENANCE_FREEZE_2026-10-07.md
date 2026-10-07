# TOKEN-MIGRATION-FORCED-CONVERSION-BASIS-001 — V0.3 MACHINE-READABLE IMMUTABLE PROVENANCE FREEZE

Date: 2026-10-07
Branch: token-migration-forced-conversion-basis-001-v0.3-machine-provenance-2026-10-07
Parent V0.2 closeout: 13df86034ee5bd1ba6a8019bda68ab34426520ae

## Purpose

Remediate V0.2 SOURCE_BLOCKED using machine-readable, non-price-bearing provenance only.

V0.1 and V0.2 remain authoritative. This V0.3 MUST NOT:
- change the economic hypothesis;
- change the >=12 minimum independent-programme sample;
- open OHLC, trades, realised prices, returns, spreads or basis;
- use price-bearing explorer HTML;
- use post-outcome performance for selection;
- open 2026 market outcomes;
- touch AAVE-GOV-LT-FORCED-DELEVERAGING-001;
- merge or alter main;
- trade, place orders, use wallets, account reads, private/authenticated exchange endpoints, or spend money.

## Machine-readable source hierarchy

Permitted:
1. first-party GitHub repositories, deployment manifests, governance specs and raw source files;
2. unauthenticated public JSON-RPC calls restricted to:
   - eth_getCode
   - eth_getTransactionReceipt for PRE-IDENTIFIED tx hashes
   - eth_getBlockByNumber for timestamps
   - eth_getLogs only for migration/disable/deployment events or pool-creation metadata;
3. public chain RPC equivalents that return no token price;
4. exchange public metadata/listing/delisting/symbol endpoints that do NOT return OHLC/trade/mark/index prices;
5. DEX factory metadata and pool-creation events, including token0/token1/pool/fee tier, but NOT swap events, reserve values, amounts, sqrtPriceX96, tick, implied prices or TVL;
6. CoinGecko / similar ID and symbol metadata only, never market_data/history/OHLC.

Forbidden:
- explorer web pages rendering live token prices;
- token quote APIs;
- market chart APIs;
- swap/reserve state that can directly reveal contemporaneous price;
- realised return or basis commentary;
- manual fallback to a venue discovered after any outcome is opened.

## Required package for FULLY_CLOSED status

Each independent programme must have, before any outcome access:

A. IDENTITY
- OLD token contract/native identity.
- NEW token contract/native identity.

B. CONVERSION
- deterministic fixed ratio or formula from first-party/governance/contract evidence.

C. ACTIVATION
- migration/converter/snapshot/utility-cutover mechanism.
- activation tx hash + block + timestamp OR an equivalent immutable block/timestamp boundary from canonical chain/governance evidence.

D. ECONOMIC BOUNDARY
One V0.2 class:
- FIXED_DEADLINE
- SNAPSHOT_DEPRECATION
- CHAIN_HALT
- PERMANENT_CONVERTER_DISABLE
- PROTOCOL_UTILITY_CUTOVER

and an exact block/timestamp/deadline/disable event sufficient to freeze T_end later.

E. CONTEMPORANEOUS OBSERVABILITY
- prove BOTH OLD and NEW existed as transferable/tradable market assets for a non-zero interval after T_signal and before T_end/effective boundary;
- proof may use listing timestamps, pool creation events, token deployment timestamps and venue metadata only;
- do not inspect prices.

F. PRICE-SOURCE MAP
Freeze one source stack per programme before any outcome value:
1. same venue + same quote;
2. public DEX pools with common quote;
3. two public venues normalized to a common quote only if same-venue overlap impossible.

The exact venue/pool/token/quote identities must be committed.

## Candidate order

Priority based solely on V0.2 mechanism strength and source feasibility, not market outcome:
1. OGV -> OGN
2. MPL -> SYRUP
3. CUDOS -> FET
4. LBR v1 -> LBR v2
5. RAINI -> RST
6. PLA -> PDA
7. MATIC -> POL
8. GAL -> G
9. MFT -> HIFI
10. KEEP + NU -> T (one programme)
11. tBTC v1 -> tBTC v2
12. RNDR -> RENDER
13. ASI programme AGIX/OCEAN -> FET
14. CQT -> CXT
15. BIT -> MNT (only after canonical ratio conflict resolution)

Contamination exclusions inherited:
- MC -> BEAM
- RBN -> AEVO
- BNX old -> BNX new
- OMI if contaminated discovery surface encountered

## Gate logic

SOURCE_GATE_PASS iff >=12 independent programmes reach FULLY_CLOSED with evidence A-F.

If exhaustive V0.3 establishes <12 programmes can ever satisfy A-F under frozen rules:
- INSUFFICIENT_SAMPLE.

If >=12 plausible programmes remain but machine-readable provenance cannot defensibly close A-F:
- SOURCE_BLOCKED.

On SOURCE_GATE_PASS:
- create a separate PRE-OUTCOME ANALYSIS FREEZE before any market price request;
- do not run Development before that freeze.

No outcome access is authorized by this V0.3 freeze itself.
