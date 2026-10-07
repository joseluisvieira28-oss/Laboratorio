# TOKEN-MIGRATION-FORCED-CONVERSION-BASIS-001 — V0.3 MACHINE-READABLE IMMUTABLE PROVENANCE CLOSEOUT

Date: 2026-10-07
Branch: token-migration-forced-conversion-basis-001-v0.3-machine-provenance-2026-10-07

Authoritative parents:
- V0.1 source/mechanism freeze: 5cc8367326740217aed08252c139486f8a84fbe5
- V0.1 closeout SOURCE_BLOCKED: ec7bc2aff28dc1663375ba59edcec4901e0f9d02
- V0.2 remediation freeze: f121b6c10d1d9e4d0e798876536fa37a73af8531
- V0.2 closeout SOURCE_BLOCKED: 13df86034ee5bd1ba6a8019bda68ab34426520ae
- V0.3 machine provenance freeze: 2a91abbd243a814039e6845ff782f5fdaacd56a5

## Verdict

SOURCE_BLOCKED

This remains a source/provenance verdict. The economic hypothesis was NOT tested.

No OHLC, trades, realised market prices, returns, conversion-adjusted basis, Development result, 2026 outcome, trading action, wallet/account read, private exchange endpoint or exchange mutation was opened or executed.

AAVE-GOV-LT-FORCED-DELEVERAGING-001 remained untouched.

## Why V0.3 does NOT pass SOURCE_GATE

V0.3 materially improved first-party machine-readable provenance. Several programmes now have high-quality canonical code/deployment evidence. However the frozen gate requires >=12 independent programmes with ALL A-F closed:

A. OLD/NEW identity
B. deterministic ratio/formula
C. immutable activation tx/block/timestamp or equivalent boundary
D. exact economic boundary
E. proven non-zero contemporaneous OLD/NEW market observability
F. exact outcome-blind price-source map frozen before outcome access

V0.3 did not close E/F for >=12 programmes. It also did not close C/D for enough of the remaining candidates.

The machine-readable public Ethereum RPC route was tested and proved operationally unreliable for the required historical provenance. Public endpoints could return latest block metadata and one preidentified receipt, but repeatedly failed or returned null for historical eth_getCode / receipts needed across the candidate set. The DEX factory metadata probe therefore could not defensibly establish historical common-quote pool existence.

Under the V0.3 stopping rule, because >=12 plausible programmes remain but the provenance stack cannot close A-F, the required verdict is SOURCE_BLOCKED, not INSUFFICIENT_SAMPLE.

## First-party provenance materially closed/improved

### OGV -> OGN

First-party repo: OriginProtocol/ousd-governance

Canonical identities:
- OGV: 0x9c354503C38481a7A7a51629142963F98eCC12D0
- OGN: 0x8207c1FfC5B6804F6024322CcF34F29c3541Ae26
- MIGRATOR: 0x95c347D6214614A780847b8aAF4f96Eb84f4da6d
- MIGRATOR_IMPL: 0x936B7855c3f20b09685770467f7621AC41B03063
- MIGRATION_ZAPPER: 0xC202CDa20A8C34C7a282890eAE2Bb9CC0B115877

Canonical contract evidence:
- Migrator.CONVERSION_RATE = 0.09137 ether
- _migrate burns OGV and transfers OGN at the fixed conversion rate.
- start() establishes a 365-day migration period.
- governance deployment script starts migration, revokes OGV governance roles and moves buyback/rewards architecture toward OGN.

First-party build/deployments.json:
- 011_OgnOgvMigration execution timestamp: 1716485925
- 012_MigrationZapper: 1716910212
- 013_UpgradeMigrator: 1717736099

Status:
- A: strong
- B: closed
- C: strong canonical execution timestamp / deployment manifest; exact chain receipt not independently re-fetched by V0.3 public RPC
- D: strong finite 365-day rule
- E/F: NOT CLOSED

### MPL -> SYRUP

First-party repos:
- maple-labs/address-registry
- maple-labs/maple-docs
- maple-labs/mpl-migration

Canonical identities:
- MPL: 0x33349B282065b0284d756F0577FB39c158F935e6
- SYRUP: 0x643C4E15d7d62Ad0aBeC4a9BD4b001aA3Ef52d66
- SYRUP migrator: 0x9c9499edD0cd2dCBc3C9Dd5070bAf54777AD8F2C
- stSYRUP: 0xc7E8b36E0766D9B04c93De68A9D47dD11f260B45

Canonical economic evidence:
- MIP-010: 1 MPL = 100 SYRUP
- final extension: 2025-05-19 14:00 UTC through 2025-05-21 14:00 UTC
- after final window conversion mechanism permanently disabled
- SYRUP/stSYRUP become sole governance tokens
- MPL/xMPL lose governance, staking benefits and protocol utility

Status:
- A: closed
- B: closed
- C: contract identity strong; deployment receipt not closed by public RPC
- D: closed by first-party finite deadline + permanent disable rule
- E/F: NOT CLOSED

### tBTC v1 -> tBTC v2

First-party repo: threshold-network/tbtc-v2

Canonical deployment manifest:
- v1: 0x8dAEBADE922dF735c38C80C7eBD708Af50815fAa
- v2: 0x18084fbA666a33d37592fA2633fD49a74DD93a88
- VendingMachineV2: 0xcE1F983c29f7A6C0C0dFA78C4D8Fe7bdfe026d4B
- VendingMachineV2 deployment tx: 0x5bc28acae7868f6d7a954c5d193f19bd72ee04fade07d616c8d6ed89091e8750
- deployment block: 16741270
- v2 token deployment tx: 0x52538ac60ce0a5672aa77991e9f030ca6eed76db0bf027821ed5170b29971ba2
- v2 deployment block: 13042356
- VendingMachineV2 constructor binds v1 and v2 identities
- exchange() implements v1 -> v2 exchange; event Exchanged exists

Status:
- A: closed
- B: fixed 1:1 mechanism supported by VendingMachine design / prior first-party migration source
- C: closed from canonical deployment manifest
- D: historical v1 sunset is strong but exact immutable end/effective block not completely closed in this V0.3 package
- E/F: NOT CLOSED

### KEEP + NU -> T

First-party repos:
- threshold-network/solidity-contracts
- threshold-network/docs

Canonical identities:
- NU: 0x4fE83213D56308330EC302a8BD641f1d0113A4Cc
- KEEP: 0x85eee30c52b0b379b046fb0f85f4f3dc3009afec
- T: 0xCdF7028ceAB81fA0C6971208e83fa7872994beE5
- NU vending machine: 0x1CCA7E410eE41739792eA0A24e00349Dd247680e
- KEEP vending machine: 0xE47c80e8c23f6B4A1aE41c34837a0599D5D16bb0

Canonical deployment evidence:
- T deployment tx: 0xdfc479f92a88c0a7a2148227c0d4c07db077df75ced4b0409465459a6b1a2454
- T deployment block: 13912436
- NU vending machine tx: 0x448ce43a7b3b1bdae0abfc60f7325e41a456fd47b3eecd66c873ab92baf14b31
- NU vending machine block: 13912444

V0.3 public RPC independently recovered the T deployment receipt:
- block 13912436
- block hash: 0xbfc68de83f2c428cd0d55861fd2d63b16e3ac3226814788d2782fc52621be0c9
- timestamp_unix: 1640944196
- status: 1
- deployed address: 0xcdf7028ceab81fa0c6971208e83fa7872994bee5

Important exclusion pressure:
First-party Threshold docs explicitly state liquid KEEP and NU vending machines were designed to remain available indefinitely and there is no migration deadline.

Therefore the programme cannot qualify through FIXED_DEADLINE. It can only enter if a defensible PROTOCOL_UTILITY_CUTOVER is immutably pinned.

Status:
- A: closed
- B: deterministic conversion architecture strong
- C: strong / partially independently verified
- D: NOT CLOSED to V0.3 standard
- E/F: NOT CLOSED

### MFT -> HIFI

First-party repo: hifi-finance/hifi-governance

Canonical contract code:
- MFT = 0xDF2C7238198Ad8B389666574f2d8bc411A4b7428
- Hifi contract source hard-codes swapRatio = 100
- swap(mftAmount) transfers MFT to address(1) and mints HIFI = mftAmount / 100
- Swap event emitted
- official docs identify HIFI at 0x4b9278b94a1112cAD404048903b8d343a810B07e

Status:
- A: strong
- B: closed from contract source
- C: deployment receipt not closed
- D: exact economic cutover boundary not closed
- E/F: NOT CLOSED

### Polygon MATIC -> POL

First-party Polygon repositories confirm:
- MATIC: 0x7d1afa7b718fb893db30a3abc0cfc608aacfebb0
- POL: 0x455e53CBB86018Ac2B8092FdCD39d8444aFFc3F6
- canonical migration architecture in Polygon Improvement Proposals / pol-token repository
- 1:1 conversion architecture

Status:
- A/B: strong
- C/D: exact outcome-study activation/end boundary still not fully closed
- E/F: NOT CLOSED

### GAL -> G

First-party Galxe repositories confirm:
- GAL: 0x5fAa989Af96Af85384b8a938c2EdE4A7378D9875
- G: 0x9C7BEBa8F6eF6643aBd725e45a4E8387eF260649

Prior frozen evidence establishes 1 GAL = 60 G and utility transition.

Status:
- A/B: strong
- C/D: not fully closed
- E/F: NOT CLOSED

## Other candidates

CUDOS -> FET, LBR v1 -> v2, RAINI -> RST, PLA -> PDA, RNDR -> RENDER, ASI AGIX/OCEAN -> FET, CQT -> CXT and BIT -> MNT remain candidate/remediation records.

None may be promoted to FULLY_CLOSED merely from announcement-level evidence.

BIT -> MNT retains unresolved canonical-ratio conflict and is not admissible.

MC -> BEAM remains EXCLUDED_CONTAMINATED_V0.2.

## Machine probes and receipts

### Ethereum provenance probe

Script:
research/token_migration_forced_conversion_basis/tools/tmfcb_v03_eth_provenance_probe.py

Workflow:
.github/workflows/tmfcb-v03-eth-provenance.yml

Initial run:
- run id: 37592006289
- artifact id: 11468883104
- result: public RPC historical eth_getCode / receipt route failed broadly

Corrected run after a purely technical fix:
- commit: 7b9dcf7b12c5fa4bb9dae7c6117cb6c652746d04
- run id: 37592284528
- job id: 112696399478
- artifact id: 11468468536
- workflow conclusion: success
- latest block successfully resolved: 26139237
- T deployment receipt successfully recovered as recorded above
- historical eth_getCode still failed broadly across the target set
- several preidentified historical receipts remained null or block timestamp retrieval failed

The fix did NOT alter scientific rules. It replaced an upper-bound implementation defect with eth_getBlockByNumber("latest") and added public RPC redundancy.

### DEX factory metadata probe

Script:
research/token_migration_forced_conversion_basis/tools/tmfcb_v03_dex_factory_probe.py

Workflow:
.github/workflows/tmfcb-v03-dex-factory.yml

Source restricted to Uniswap V2 PairCreated metadata:
- factory: 0x5C69bEe701ef814a2B6a3EDD4B1652CB9cc5aA6f
- common quotes frozen: WETH, USDC, USDT, DAI
- no Swap events
- no reserves
- no token balances
- no sqrtPrice/tick
- no implied price/TVL

Initial run:
- run id: 37592174871
- artifact id: 11468647928
- historical RPC route failed before pair discovery

Corrected run:
- commit: d3ea62b70c756ac7566479869d34b93db702561f
- run id: 37592308973
- job id: 112696481416
- artifact id: 11469187433
- workflow conclusion: success
- latest block resolved: 26139238
- historical eth_getCode still failed for all candidate tokens before PairCreated search could proceed

Therefore the public/free RPC stack tested in V0.3 cannot be used as a defensible historical archive source for E/F at the required scale.

## Exact gate accounting

Plausible independent programmes available for continued source research: >=12
Programmes with materially strengthened first-party A-D evidence in V0.3: several
Programmes FULLY_CLOSED across A-F: <12
Required minimum FULLY_CLOSED: 12

Market price endpoints queried: 0
OHLC values opened: 0
Trade prices opened: 0
DEX reserves/swaps opened: 0
Realised returns calculated: 0
Conversion basis calculated: 0
Development runs: 0
2026 market outcomes opened: 0
Trading/orders/wallets/account reads/private exchange endpoints: 0

## Scientific interpretation

V0.3 did NOT show that forced-conversion basis has no edge.

It showed:
1. the economic mechanism exists in multiple real programmes;
2. first-party machine-readable contract/deployment evidence can close meaningful portions of provenance;
3. a number of programmes have strong deterministic conversion and deprecation/cutover mechanics;
4. the remaining decisive blocker is historical market-source provenance/observability plus exact immutable boundary closure for enough events;
5. the tested free public RPC route is not sufficiently reliable as an archive layer for a >=12-event study.

Passing the gate by substituting announcement dates for missing blocks, accepting unproven price overlap, or opening market data to discover which venue works would violate the frozen methodology.

## Stop rule

Verdict: SOURCE_BLOCKED

Do NOT create PRE-OUTCOME ANALYSIS FREEZE.
Do NOT open market prices.
Do NOT run Development.
Do NOT open 2026.
Do NOT rescue by subsets or alternate horizons.

A future source-remediation phase, if authorized, must preserve all freezes and solve the remaining source problem without outcome access. Legitimate routes include:
- first-party deployment manifests with embedded receipts/blocks;
- public archival datasets or RPC providers whose historical methods can be verified without price access;
- exchange listing/delisting archives exposing timestamps/symbol metadata only;
- DEX factory datasets containing PairCreated metadata only.

No requirement may be weakened merely to reach twelve events.
