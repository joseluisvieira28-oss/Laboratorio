# LCOD BORROW-LOG BLOCK-PIN UNIVERSE GATE V0.1

Frozen: 2026-09-25
Stage: SOURCE / POPULATION COMPLETENESS
Outcomes: CLOSED

## Authority pins

Aave V4 contract source:
aave/aave-v4 @ 40232a0a91150d8ee5cab42bd3ddd0baf4ffff9f

ISpoke.Borrow event:
Borrow(uint256 indexed reserveId, address indexed caller, address indexed user,
       uint256 drawnShares, uint256 drawnAmount)

The position owner `user` is indexed and therefore recoverable directly from
canonical Ethereum logs.

Aave Address Book:
aave-dao/aave-address-book @ f08dbd218a1da7ea1ac3bb0e387652fdb9f98042

Pinned Ethereum V4 ALL_SPOKES lending universe (13):
- 0x973a023A77420ba610f06b3858aD991Df6d85A08
- 0x58131E79531caB1d52301228d1f7b842F26B9649
- 0xba1B3D55D249692b669A164024A838309B7508AF
- 0xD8B93635b8C6d0fF98CbE90b5988E3F2d1Cd9da1
- 0x65407b940966954b23dfA3caA5C0702bB42984DC
- 0x7EC68b5695e803e98a21a9A05d744F28b0a7753D
- 0x94e7A5dCbE816e498b89aB752661904E2F56c485
- 0xAD75cE6354f87F3135cE10621d385d8D1e2562C2
- 0x956d8e0A89cfa3744428C4641b5a53B56167a7f9
- 0xbF10BDfE177dE0336aFD7fcCF80A904E15386219
- 0x3131FE68C4722e726fe6B2819ED68e514395B9a4
- 0xe1900480ac69f0B296841Cd01cC37546d92F35Cd
- 0x774b9655413c34809c1f1b16b654465A89EBE989

Treasury and tokenization spokes are excluded because they are not lending
position spokes in Address Book ALL_SPOKES.

## Canonical universe construction

At run start:
1. choose one Ethereum `finalized` block N;
2. fetch every Borrow event for all 13 pinned spokes from genesis through N;
3. derive candidate pairs (spoke, indexed user), deduplicated;
4. at exactly block N, call getUserAccountData(user) on the same spoke;
5. retain only pairs with totalDebtValueRay > 0.

The resulting debt-bearing pair set is the canonical LCOD population for N.

No current-holder API is allowed to define the population.

## Transport

Historical event acquisition may use SQD Ethereum mainnet archive because prior
LCOD/CCLM source work proved archive transport and raw-response hashing.

Every accepted event must preserve:
- spoke;
- user topic;
- transaction hash where supplied;
- log index;
- block number;
- raw response SHA256.

## PASS

BORROW_LOG_BLOCK_PIN_UNIVERSE_PASS requires:
- all 13 pinned spokes queried;
- zero malformed Borrow topics;
- zero unresolved archive transport error;
- every candidate pair evaluated at the same block N;
- >=1 current debt-bearing pair;
- no raw wallet address persisted in the durable receipt;
- current-holder comparison, if performed, is diagnostic only and cannot add a
  pair absent from canonical Borrow history.

This gate proves a block-pinned current borrower population can be reconstructed
from canonical onchain history. It does NOT compute a shock curve or any market
outcome.
