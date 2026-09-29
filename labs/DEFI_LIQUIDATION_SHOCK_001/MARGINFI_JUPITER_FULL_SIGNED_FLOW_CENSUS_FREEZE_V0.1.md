# MARGINFI JUPITER FULL SOURCE CENSUS FREEZE V0.1

Date: 2026-09-29
Branch: dls-signed-flow-authority-v01
Status: FROZEN BEFORE CALIBRATION RESULT

Run only if:
- MARGINFI_JUPITER_ROUTE_CLASS_MEMBERSHIP_PASS; and
- MARGINFI_JUPITER_SWAP_DIRECTION_CALIBRATION_PASS.

Population:
- every member from the immutable Jan-2024 membership PASS artifact;
- no sampling;
- no amount, token, protocol or direction filter may be introduced after calibration.

Decoder:
- exactly MARGINFI_JUPITER_SWAP_EVENT_DECODER_IMPLEMENTATION_FREEZE_V0.1.md;
- no parser, route-root, bank-mint or direction rule may change after calibration.

Per-member source labels:
- DIRECTION_PROVEN
- DIRECTION_AMBIGUOUS
- SOURCE_EVIDENCE_INCOMPLETE
- CONTRADICTION

Full source PASS requires all:
1. non-incomplete source evidence rate >= 95%;
2. deterministic direction among non-incomplete members >= 90%;
3. contradictions = 0.

PASS:
MARGINFI_JUPITER_SIGNED_FLOW_SOURCE_PASS

Threshold miss with valid evidence:
MARGINFI_JUPITER_SIGNED_FLOW_SOURCE_PARTIAL

Source/layout/identity failure:
MARGINFI_JUPITER_SIGNED_FLOW_SOURCE_BLOCKED

No price, return, PnL, USD threshold, 2025/2026 outcome or execution authority is introduced here.
