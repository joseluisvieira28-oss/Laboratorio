# CRYPTO-INDEX-REBALANCE-CONTINUATION-002 — TERMINAL CLOSEOUT V0.1

Date: 2026-10-01
Classification: **HOLDOUT_CONTINUATION_FAILED**
Trading authority: NONE

## Evidence chain

Source census:
- run: 36896436012
- artifact: 11179568574
- artifact SHA256: a958b731ffefaae7a8a6754653dd7b5f6b6da26c168859341ab9a25fe71c46f9
- 21/21 official pages
- 38 unique source legs
- 19 ADD / 19 REMOVE
- 7 change months
- no market outcomes opened

USD-M route gate:
- run: 36896713962
- artifact: 11179995821
- artifact SHA256: b3a7328fd0ca1bc0c117df59a579639e0303ed8d0e61c9fd09615dab6dfcd46b
- route identity: a5411273d65be311d40fea168f3b616375cb41f23cf4322f353abffdef7216f0
- 32 primary route-qualified legs
- 16 ADD / 16 REMOVE
- 6 primary change months
- zero price values opened

Final holdout:
- run: 36897186775
- artifact: 11180166411
- artifact SHA256: ac91e0d3d1b47148e5d6cb07be41ce68dbaf58ea289eaa8b49eed17ac4ced527
- 32 valid legs / 0 rejected
- 6 valid months
- both 2025 and 2026
- exact 1m USD-M OPEN boundaries
- entry 06:00 UTC implementation day
- exit 16:00 America/New_York implementation day
- costs frozen before outcomes: 20 bps fee floor / 30 bps BASE / 50 bps STRESS

## Primary metrics

- mean leg gross: +99.702273 bps
- mean leg BASE net: +69.702273 bps
- mean leg STRESS net: +49.702273 bps
- mean month gross: +93.292095 bps
- median month gross: +26.927683 bps
- bootstrap95 mean month gross: [-21.763365, +219.401962] bps
- ADD mean gross: +126.431214 bps
- REMOVE mean gross: +72.973333 bps
- positive gross months: 3 / 6
- positive STRESS months: 3 / 6
- leave-one-month-out positive fraction: 100%
- 2025 mean month gross: -3.624769 bps
- 2026 mean month gross: +190.208960 bps
- max absolute month concentration: 46.424081%

Month means:
- 2025-01: +54.192976 bps gross / +4.192976 bps STRESS
- 2025-07: -64.729672 bps gross / -114.729672 bps STRESS
- 2025-11: -0.337611 bps gross / -50.337611 bps STRESS
- 2026-02: -27.488105 bps gross / -77.488105 bps STRESS
- 2026-05: +345.795960 bps gross / +295.795960 bps STRESS
- 2026-07: +252.319024 bps gross / +202.319024 bps STRESS

## Frozen gate adjudication

PASS:
- A mean month gross >= 50 bps
- C median month gross > 0
- E LOMO positive >=80%
- F ADD and REMOVE means positive
- G BASE mean net positive
- H STRESS mean net positive
- I >=3 positive STRESS months

FAIL:
- B bootstrap lower bound >0
- D >=4 positive gross months
- J both 2025 and 2026 means positive
- K month concentration <=40%

Because ALL gates were pre-required, the terminal classification is HOLDOUT_CONTINUATION_FAILED.

## Interpretation

The average magnitude is economically material, but it is not temporally stable enough to survive the frozen confirmatory design.
The result is dominated by strong 2026-05 and 2026-07 months, while 2025 as a whole is slightly negative.

This identity MUST NOT be rescued by:
- selecting only 2026;
- dropping 2025-07 / 2025-11 / 2026-02;
- adding a regime filter;
- changing the entry time;
- changing costs;
- using 2026-09 as rescue;
- ADD-only or REMOVE-only selection;
- alternate venue or horizon.

Any future regime-dependent hypothesis must be a scientifically new identity with untouched future evidence.

No live trading.
No orders.
No exchange mutation.
No merge to main.
