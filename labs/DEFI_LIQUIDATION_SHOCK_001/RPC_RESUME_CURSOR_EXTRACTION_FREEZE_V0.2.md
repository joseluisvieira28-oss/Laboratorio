# DEFI-LIQUIDATION-SHOCK-001 — RPC RESUME CURSOR EXTRACTION FREEZE V0.2

Date: 2026-09-22
Status: FROZEN PRE-EXECUTION / SOURCE-ONLY / OUTCOME-BLIND

Purpose:
Extract deterministic resume cursors from the exact final signature pages already produced by the two page-cap-blocked first-success crawls. This step performs no new Solana source request and opens no economic outcome.

## Marginfi parent
- run: 35715833295
- artifact: 10694211179
- artifact digest: sha256:86575189d1f19809f5a373d2e393761f263175960ecf496e7dfd82d421e5fea3
- parent classification: MARGINFI_FIRST_SUCCESS_BOUNDARY_RPC_HISTORY_BLOCKED
- reason: max_pages_reached_before_lower_boundary
- final page: dls_marginfi_rpc_boundary_v01/signatures_page_5000.json

## Save 0x0c parent
- run: 35716197055
- artifact: 10695241107
- artifact digest: sha256:bef6757fdbd5657e33567e53e31ea5eea410e3a6d1d773e633e7427b4800bbf8
- parent classification: SAVE0C_FIRST_SUCCESS_BOUNDARY_RPC_HISTORY_BLOCKED
- reason: max_pages_reached_before_lower_boundary
- final page: dls_save0c_rpc_boundary_v01/signatures_page_5000.json

For each page:
- require non-empty JSON-RPC result array;
- take the final row only;
- persist signature, slot, blockTime, err, page SHA256 and parent run/artifact IDs;
- no transaction body is inspected.

Valid extraction classification:
- MARGINFI_RPC_RESUME_CURSOR_EXTRACTED
- SAVE0C_RPC_RESUME_CURSOR_EXTRACTED

Any missing/malformed final page fails closed.

Firewall: prices=false; returns=false; pnl=false; direction=false; event_outcomes=false; live_trading=false; orders=false; wallets=false; exchange_mutation=false; paid_source=false; merge_main=false.
