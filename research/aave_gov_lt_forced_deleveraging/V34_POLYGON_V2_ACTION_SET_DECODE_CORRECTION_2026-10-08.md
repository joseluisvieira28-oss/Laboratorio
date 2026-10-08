# AAVE-GOV-LT-FORCED-DELEVERAGING-001 — Polygon V2 action-set decode correction

Date: 2026-10-08 UTC
Status: SOURCE ONLY / HYPOTHESIS NOT TESTED / 2026 CLOSED

## Scope

Correct a field-decoding error in the V18 Polygon governance-lineage receipt. The raw
transaction/log evidence is preserved unchanged in Actions artifact 11528645096
(run 37727070200, digest sha256:d6cb79f4321226f8bc1eec1189bd389105514043ed60afc07b9af163e8a3edc7).

V18 correctly identified two V2 execution transactions at the PolygonBridgeExecutor
`0xdc9A35B16DB4e126cFeDC41322b3a36454B1F772`, but interpreted indexed topic[1]
(the initiatorExecution address) as the action-set id. The event data itself contains the
action-set id as its first 32-byte word.

## Corrected raw-log decoding

### AIP-233 / stablecoin eMode

Effect tx:
`0x83afad9ff0c38534100b1a4626f99642d4250e93c04cd289b240c6768c4fe0c9`

Effect block: `43299439`
Effect timestamp: `1685387698`

Raw ActionsSetExecuted log:
- executor: `0xdc9a35b16db4e126cfedc41322b3a36454b1f772`
- topic[1] initiatorExecution: `0x7d0219c7037819b3f5d73e235c595189c3f8c224`
- data word[0]: `0x2b` = **43**

Correct action-set id: **43**.

The sequential Polygon V3 configurator audit independently identifies this same transaction as
the category-1 stablecoin eMode LT decrease `9750 -> 9500`.

### AIP-288 / CRV

Effect tx:
`0x8d128ca9c637576b6a0d967da565cff139a492a749108fed2ac35f4e9bf888a9`

Effect block: `46180710`
Effect timestamp: `1691767153`

Raw ActionsSetExecuted log:
- executor: `0xdc9a35b16db4e126cfedc41322b3a36454b1f772`
- topic[1] initiatorExecution: `0x3999d49bbad3a7375b0376bdf2ba4f2e3c9f5177`
- data word[0]: `0x35` = **53**

Correct action-set id: **53**.

Pinned legacy Seatbelt report
`reports/Aave/0xEC568fffba86c094cf06b22134B23074DFE2252c/288_Polygon_53.md`
at commit `f1d1c1090ac51d01e557135c41076dab8f4b0e74` independently identifies Polygon
action set 53 and the CRV LT change `7500 -> 6500`, LTV `7000 -> 3500`.

## Scientific effect

This correction strengthens V2 cross-chain lineage; it does not add or remove a shock, change
a signal/effect boundary, open borrower/economic outcomes, or alter the V26/V31/V33 source
universe. AIP-233 remains one coordinated cross-chain shock and AIP-288 remains one shock.

The V18 numeric `action_set_id` values derived from topic[1] are superseded for these two V2
rows only. All raw hashes and original receipts remain preserved.
