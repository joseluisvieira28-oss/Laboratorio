# PMD-001 — V0.12 Historical Decoder Compatibility Receipt

Status: **PASS ON AVAILABLE HISTORICAL PROBE EVIDENCE — SOURCE-ONLY / NO OUTCOME AUTHORITY**

## Purpose

Validate the frozen V0.12 Pump `TradeEvent` decoder against real historical PMD-001 transaction evidence that existed before V0.12, rather than relying only on synthetic unit fixtures.

## Frozen evidence inspected

- Original PMD-001 public-RPC source-rebuild probe artifact: `PMD-001-source-rebuild-preoutcome-v01.zip`
- Historical mint: `9af7PmWRca2QYmknQehoLH19jG5ss9ajYFpgL8dMpump`
- Raw file: `pmd_public_rpc_probe_v01/raw/9af7PmWRca2QYmknQehoLH19jG5ss9ajYFpgL8dMpump.jsonl`
- Raw transaction rows inspected: **37**
- No post-migration price, return, direction, PnL, or economic label was read.

## Deterministic compatibility findings

Using the same exact Pump program, mint, bonding-curve-PDA account matching and the frozen legacy + v2 instruction discriminator logic used by V0.12:

- exact Pump BUY instruction intents found: **7**
- successful exact BUY intents: **4**
- failed exact BUY intents: **3**
- failed intents carried on-chain `InstructionError ... Custom 6005`
- decodable `TradeEvent` records for successful intents: **4 / 4**
- decodable `TradeEvent` records for failed intents: **0 / 3**
- successful-intent historical decode coverage in this probe: **100%**
- decoded sides: **4 BUY / 0 SELL**
- decoded SOL amounts: `17.074022483`, `31.497570755`, `26.806924136`, `9.626841686`
- decoded SOL total: **85.005359060 SOL**
- observed `TradeEvent` discriminator: `bddb7fd34ee661ee`

The absence of events on the three failed BUY attempts is consistent with fail-closed transaction semantics and must not be counted as missing successful economic flow.

## Interpretation

This receipt establishes **historical parser compatibility on the available real probe**, not full-population coverage. The full V0.12 run must still measure decoder completeness over the exact V0.7 source population. Any successful target trade that cannot be deterministically decoded remains `undecoded`; it must never be silently treated as zero flow.

## Authority

- source validation only
- exploratory infrastructure only
- `promotion_authority = false`
- no edge / setup / diamond conclusion may be drawn from this receipt
