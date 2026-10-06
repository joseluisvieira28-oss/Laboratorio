# TOKEN-MIGRATION-FORCED-CONVERSION-BASIS-001
## V0.1 SOURCE GATE — CANDIDATE CENSUS / RECEIPT
Date: 2026-10-06
Branch: token-migration-forced-conversion-basis-v0.1-source-2026-10-06
Freeze commit: 6cbcac109b3afa796d8993dc80ce57c1b2d73427

IMPORTANT: No market prices / returns / basis values were opened or inspected in this source gate.

## Discovery frame
Source-only discovery across:
- official project / protocol migration documentation;
- official governance / foundation posts;
- official exchange token-swap notices as discovery and lifecycle corroboration;
- public chain/explorer references when surfaced by authoritative migration material.

No candidate was added or removed based on subsequent price behaviour.

## Candidate census (2022-2025)

| Programme | Period | Deterministic conversion evidence | Hard economic/end boundary evidence | On-chain activation / contract evidence at required standard | Historical OLD+NEW contemporaneous market-data capability proven without opening values? | Source-gate status |
|---|---|---|---|---|---|---|
| THORChain BNB.RUNE / ETH.RUNE -> THOR.RUNE | 2022 | YES: redemption starts 1.0 and deterministic kill-switch decays to 0 | YES: kill switch activated from block 6,500,000; support ultimately removed | PARTIAL-STRONG: protocol/block mechanism documented; exact tx/contract receipt still not captured | NOT PROVEN | PROVISIONAL_STRONG |
| GALA v1 -> GALA v2 | 2023 | YES: 1:1 snapshot/drop | YES: 15-May-2023 cutover; v1 utility/support ceases | PARTIAL: new contract documented; mechanism is snapshot/drop rather than migration contract; activation tx/block not captured | NOT PROVEN | PROVISIONAL_STRONG |
| Merit Circle MC -> BEAM | 2023-2024 | YES: 1 MC = 100 BEAM | YES: migration began 26-Oct-2023 and closed 26-Oct-2024; utility transferred | PARTIAL: migration portal and governance path documented; migration-contract address + activation tx/block not yet captured | NOT PROVEN | PROVISIONAL_STRONG |
| Stratis legacy STRAX -> StratisEVM STRAX | 2024 | YES: exchange corroboration states 1 old STRAX = 10 new STRAX | YES: on-chain burn window to 20-Mar-2024; off-chain proofing window closes 29-Dec-2024 | PARTIAL-STRONG: irreversible on-chain burn mechanism documented; exact activation tx/block not captured | NOT PROVEN | PROVISIONAL_STRONG |
| Router Protocol ROUTE v1 -> ROUTE v2 | 2024-2025 | YES: 1 old = 33.33 new | YES: final DAO-set deadline 25-Aug-2025; unmigrated v1 treated burned and equivalent v2 burned | PARTIAL-STRONG: OLD/NEW contract addresses documented; migration portal exists; activation tx/block not captured | NOT PROVEN | PROVISIONAL_STRONG |
| RFOX / VFOX -> JUICE (JUC) | 2024-2025 | YES: RFOX 1:1; VFOX 1:20 | YES: window closed 10-Jul-2025; old tokens no longer supported | PARTIAL: official portal/process documented; migration-contract address + activation tx/block not captured | NOT PROVEN | PROVISIONAL |
| Centrifuge legacy CFG/WCFG -> new CFG | 2025 | YES: 1:1 | YES: official governance migration deadline Nov/Dec-2025 | PARTIAL: new token contract documented; migration contract activation tx/block not captured | NOT PROVEN | PROVISIONAL |
| IAGON IAG ERC20 -> Cardano native token | 2023-2024 | conversion programme documented; exact ratio not established in retained authoritative source excerpt | YES: requests close 05-Apr-2024; old ERC20 has no protocol utility | FAIL required standard: documented manual/queued process to designated address, not a proven deterministic migration contract | NOT PROVEN | REJECT / INCOMPLETE_MECHANISM |
| VEMP legacy multichain -> Horizon token | 2024-2025 | YES in surfaced migration notice: 1:1 | YES: 02-Dec-2024 to 31-Jan-2025; unmigrated legacy becomes non-functional | INCOMPLETE: primary project source / activation tx not captured; discovery source is secondary | NOT PROVEN | PROVISIONAL_SOURCE_WEAK |
| Lybra LBR v1 -> LBR v2 | 2023 | deadline/migration documented; exact deterministic ratio not established in retained source excerpt | YES: V1 LBR deadline 30-Sep-2023; post-deadline V1 described as untradable | PARTIAL: migration exists but contract/activation receipt not captured | NOT PROVEN | PROVISIONAL |
| Galxe GAL -> Gravity G | 2024-2025 | YES: 1 GAL = 60 G; GAL burned on migration | SOFT/FAIL: portal promised at least one year, and holders retained GAL after window even though utility moved | migration portal/new contract documented but exact immutable cutoff absent | NOT PROVEN | REJECT_NO_IMMUTABLE_END |
| Ellipsis EPS -> EPX | 2022 | YES: 1 EPS = 88 EPX; one-way migration | FAIL: official docs explicitly say migration contract never closes / no deadline | migration contract exists, but no qualifying hard end | NOT PROVEN | REJECT_NO_DEADLINE |
| QuickSwap old QUICK -> new QUICK | 2022-2023 | YES: 1 old = 1000 new; conversion contract | FAIL: official 2022 docs explicitly state no deadline | conversion contract + OLD/NEW contracts documented, activation receipt not captured | NOT PROVEN | REJECT_NO_DEADLINE |
| Anyswap ANY -> Multichain MULTI | 2021-2022 exchange transition | YES: 1:1 one-way | FAIL: source states no time limit; first public conversion signal is Dec-2021 | conversion path documented; outside clean 2022-25 signal frame | NOT PROVEN | REJECT_NO_DEADLINE / SIGNAL_PREWINDOW |
| FEG legacy -> upgraded FEG | 2023-2025 | migration across versions documented | FAIL for initial 2023 programme: contemporaneous communication said no time limit; later manual-upgrade closure is a later programme state | multiple versions/contracts complicate one-programme independence and immutable pre-outcome boundary | NOT PROVEN | REJECT_AMBIGUOUS_PROGRAMME |
| BinaryX old BNX -> new BNX | 2023 | YES: 1 old = 100 new; new contract documented | exchange cutoff exists but global immutable migration deadline not proven | new contract documented; migration contract/activation tx not captured | NOT PROVEN | INCOMPLETE |
| Cocos-BCX COCOS -> COMBO | 2023 | YES: 1:1; new contracts documented | exchange legacy support ends; global immutable migration deadline not proven | token contracts documented; migration contract/activation tx not captured | NOT PROVEN | INCOMPLETE |
| Virtua TVK -> VANRY | 2023 | YES: 1:1 via exchange conversion | global immutable migration deadline not proven | new/old lifecycle evidence incomplete at on-chain activation level | NOT PROVEN | INCOMPLETE |
| Frontier FRONT -> Self Chain SLF | 2024 | YES: 1:1; exchange conversion and old-withdrawal retirement | global immutable migration deadline not proven | on-chain activation/migrator receipt not captured | NOT PROVEN | INCOMPLETE |
| Render RNDR -> RENDER | 2024 | YES: 1:1 | project transition clear, but immutable final migration deadline not established in authoritative source retained here | migration mechanics known but exact activation / deadline evidence incomplete | NOT PROVEN | INCOMPLETE |
| EOS -> Vaulta A | 2025 | YES: 1:1 | exchange cutover exists; globally immutable holder deadline not proven | protocol rebrand/swap but required migrator activation receipt not captured | NOT PROVEN | INCOMPLETE |

## Source observations that are outcome-free
1. Exchange auto-conversion notices provide useful ratio and service-cutoff evidence, but generally stop OLD trading before NEW trading starts. That does not establish contemporaneous OLD+NEW basis measurement on that venue.
2. Several protocol-level conversion contracts are deliberately open-ended (QuickSwap, Ellipsis, Anyswap), which violates the frozen immutable-end requirement.
3. Several hard-boundary programmes have strong official documentation but still lack retained activation transaction/block receipts at the required standard.
4. Per-event contemporaneous historical OLD+NEW market-data capability has NOT been proven for >=12 events without opening market values.
5. No authoritative complete registry of all 2022-2025 forced/economically-binding token migrations was identified. Exchange announcement archives are venue-specific and project documentation is heterogeneous.

## Gate accounting
- Raw discovered programmes: >=21
- Clearly rejected on frozen mechanism/end rules: >=5
- Provisional strong/qualified mechanism candidates: <12
- Fully defensible events satisfying ALL frozen evidence requirements including on-chain activation and outcome-free market-data capability: <12
- Complete-universe proof sufficient to convert the shortfall into INSUFFICIENT_SAMPLE: NOT AVAILABLE

Therefore the correct failure mode is SOURCE_BLOCKED, not INSUFFICIENT_SAMPLE.

## Key public source identities retained
- THORChain: https://blog.thorchain.org/dev-update-147-150 and https://medium.com/thorchain/upgrading-to-native-rune-a9d48e0bf40f
- Gala: https://news.gala.com/gala-games/introducing-galav2-a-new-era-for-the-gala-games-ecosystem/
- Stratis: https://www.stratisplatform.com/post/stratisevm-token-swap-schedule
- Beam / Merit Circle: https://medium.com/@onbeam/beam-token-migration-update-december-2023-acfbe22b00f7
- Router: https://routerprotocol.wordpress.com/2024/12/06/a-complete-route-migration-and-staking-guide-for-router-protocol-users/
- RFOX: https://www.rfox.com/blogs/rfox-vfox-token-migration-announcement
- Centrifuge: https://gov.centrifuge.io/t/centrifuge-token-migration-update/6860
- IAGON: https://blog.iagon.com/the-final-countdown-deadline-for-erc20-cnt-token-swap-requests-announced/
- Galxe: https://www.galxe.com/blog/gal-g
- Ellipsis: https://docs.ellipsis.finance/the-epx-token/migrating-eps-to-epx
- QuickSwap: https://blog.quickswap.exchange/posts/old-quick-vs-new-token-split
- Binance corroboration for multiple swaps: official Binance Support announcement archive/pages.

## Outcome access declaration
No price values, returns, spreads, conversion-adjusted basis values, post-signal performance, or 2026 outcomes were opened.
