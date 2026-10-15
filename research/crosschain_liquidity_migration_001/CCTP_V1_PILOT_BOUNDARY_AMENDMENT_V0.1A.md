# CCTP V1 PILOT TECHNICAL BOUNDARY AMENDMENT V0.1A

Date: 2026-09-24

Reason: preserve the original no-2025 source firewall while allowing destination settlement time.

Original source window end:
2024-12-31T23:59:59Z

Corrected source-cohort end:
2024-12-24T23:59:59Z

Destination pairing window may extend through:
2024-12-31T23:59:59Z

No 2025 block, log or transaction may be requested.

This is a pre-outcome source-boundary correction only. It prevents late-December source burns from being falsely classified as unpaired solely because their valid destination mint could occur after the protected-period boundary.

All other frozen semantics remain unchanged:
- CCTP V1 only;
- native USDC;
- Ethereum <-> Avalanche;
- Standard only;
- no market outcomes.
