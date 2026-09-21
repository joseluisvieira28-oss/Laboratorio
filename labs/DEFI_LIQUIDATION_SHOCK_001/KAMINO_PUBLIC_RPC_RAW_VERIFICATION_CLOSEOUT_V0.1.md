# DEFI-LIQUIDATION-SHOCK-001 — KAMINO PUBLIC RPC RAW VERIFICATION CLOSEOUT V0.1

Date: 2026-09-21  
Status: **SOURCE-ONLY RAW VERIFICATION PASS / GLOBAL SOURCE_DATA_PASS NOT GRANTED**

## Frozen input

The corrected BigQuery smoke V0.2 produced 41 candidate rows on 2024-12-15:
- 16 successful unique reference transactions;
- 25 failed unique attempts;
- 0 source anomalies.

The 16 successful signatures were frozen before this RAW-verification run. No candidate was added, removed or substituted after execution began.

## Execution

GitHub Actions run: `35648053418`  
Job: `106493326506`  
Head commit: `ef18e5ec4cd9a9fc0d374df3ab9706f48a61752e`  
Source endpoint: official public Solana mainnet RPC `https://api.mainnet-beta.solana.com`  
Method: `getTransaction` / `jsonParsed`

For every frozen candidate the verifier required:
1. non-null transaction;
2. exact BigQuery slot match;
3. `meta.err == null`;
4. exact Kamino program ID;
5. decoded instruction data beginning with corrected discriminator `b1479abce2854a37`.

## Result

Classification: **KAMINO_SMOKE_RAW_VERIFICATION_PASS**

- candidates: 16
- RAW verified: **16 / 16**
- transport blocked: **0**
- content mismatches: **0**
- slot mismatches: **0**
- transaction execution failures among the frozen success set: **0**

Each row independently resolved to:
`RAW_VERIFIED_SUCCESSFUL_KAMINO_LIQUIDATION_REFERENCE`

This proves that the corrected Kamino liquidation decoder maps to realized successful on-chain transactions by 2024-12-15.

It does **not** establish the earliest historical Kamino first-success boundary and does **not** establish an economic edge.

## Evidence

GitHub artifact:
- artifact ID: `10660941294`
- workflow artifact SHA256: `644b9a23442194b919b8336672ba1055e297d674728c400a4ee7f9866cef6dd4`
- artifact size: 244,937 bytes

Drive evidence copy:
- file: `DLS_KAMINO_PUBLIC_RPC_RAWVERIFY_EVIDENCE_V0.1.zip`
- Drive ID: `1wZr0bL7HoamFzTTy_12wx7WOAIB4pEFl`

## Scientific routing

The prerequisite "corrected Kamino candidate path is sound" is now satisfied.

The already-frozen chronological first-success boundary plan may therefore proceed. Kamino's first-success search must still begin from its source-supported boundary `2023-11-17T13:25:35Z` and proceed chronologically under the frozen authority.

Global `SOURCE_DATA_PASS` remains **false** until all required historical boundaries, census completeness, realized population, RAW class validation and numerical sample-gate requirements are satisfied.

## Firewall

- prices queried: false
- returns computed: false
- PnL computed: false
- direction tested: false
- market outcomes opened: false
- live trading: false
- orders: false
- wallets: false
- exchange mutation: false
- paid source: false
- merge to main: false
