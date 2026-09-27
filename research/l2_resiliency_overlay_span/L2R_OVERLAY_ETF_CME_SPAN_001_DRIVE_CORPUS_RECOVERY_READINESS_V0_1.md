# L2R-OVERLAY-ETF-CME-SPAN-001 — DRIVE CORPUS RECOVERY READINESS RECEIPT V0.1

Date: 2026-09-27
Scope: SOURCE TRANSPORT READINESS ONLY.
No L2 directional outcome, overlay outcome, 2026 data, PnL or trading result was opened.

## Drive corpus discovery

Two independent byte-preserving transport layouts are present in Google Drive:

### 32 MiB layout
Folder: L2R_2025_DRIVE_PARTS_32MiB
Master manifest Drive ID: 1CyBlooXmDOjtzC4uyoyZAkcfi15FI-4_

Master purpose:
Byte-preserving Drive transport split for L2-RESILIENCY-001 2025 RAW.

part_size_target_bytes = 33,554,432
scientific_changes = false

Archives:
- 20250530.zip — 3,090,700,320 bytes — SHA256 1f5c59b04cf8a51638a32f0aa7ffd7b5a29a6906bd4f3a3881df716b4bbbabce — 93 parts
- 20250907.zip — 2,088,567,760 bytes — SHA256 b1aeda17292fc4358a7f396a683a27c46c769df71e74baf47a463d1b871f28a3 — 63 parts
- 20251227.zip — 2,333,757,454 bytes — SHA256 0683727131ac8e3cbc45a47edd57fd9ec69a996eb5eaed40a2ce6bda86d1b54c — 70 parts

Drive folder listing confirms all expected part names/counts are physically present.
Each archive folder also contains one non-part parts_manifest.json sidecar.

### 220 MiB layout
Folder: L2R_2025_DRIVE_PARTS_220MiB
Master manifest Drive ID: 1jZskszrxqha0fwZax_XLG3BNj1DR8Rff

Master purpose:
Byte-preserving Drive transport split for L2-RESILIENCY-001 2025 RAW.

part_size_target_bytes = 230,686,720
scientific_changes = false

Archives:
- 20250530.zip — 3,090,700,320 bytes — SHA256 1f5c59b04cf8a51638a32f0aa7ffd7b5a29a6906bd4f3a3881df716b4bbbabce — 14 parts
- 20250907.zip — 2,088,567,760 bytes — SHA256 b1aeda17292fc4358a7f396a683a27c46c769df71e74baf47a463d1b871f28a3 — 10 parts
- 20251227.zip — 2,333,757,454 bytes — SHA256 0683727131ac8e3cbc45a47edd57fd9ec69a996eb5eaed40a2ce6bda86d1b54c — 11 parts

Drive folder listing confirms all expected part names/counts are physically present.
Each archive folder also contains one non-part parts_manifest.json sidecar.

## Cross-layout consistency

Both layouts independently declare the exact same:
- source filenames;
- original archive byte sizes;
- original archive SHA256 values;
- byte-concatenation reassembly rule.

Therefore the corpus is no longer considered missing from Drive.

This receipt does NOT assert that every part byte has been independently re-hashed in ChatGPT's local runtime.
The current runtime cannot mount the multi-gigabyte downloaded attachment set reliably.

## Existing authoritative restoration gate

The repository already contains:
research/l2_resiliency/RUN_L2R_2025_DRIVE_RESTORE_AND_VALIDATION_V01B.ps1

That frozen restorer requires, before validation:
1. locate either Drive parts layout;
2. verify every part size;
3. SHA256 every part against the chosen master manifest;
4. concatenate parts in ascending sequence;
5. verify each reconstructed ZIP exact byte size and SHA256;
6. extract resumably;
7. require exactly 8,400 BTC.lz4 objects;
8. require exactly 8,975,275,014 raw bytes;
9. rebuild the frozen verified manifest;
10. require manifest SHA256:
   767e75594864344c75dd2669ec4fad8c738710c218322b11fd43a83077ef17c3;
11. require frozen validation runner SHA256 before the one-shot is opened.

Any mismatch fails closed.

## One-shot firewall

The L2R overlay one-shot has NOT been consumed by this recovery work.

Do not open the one-shot until the existing restore script reports all frozen corpus/archive/manifest hashes PASS.

No scientific rule changed.
Promotion credit = 0.
