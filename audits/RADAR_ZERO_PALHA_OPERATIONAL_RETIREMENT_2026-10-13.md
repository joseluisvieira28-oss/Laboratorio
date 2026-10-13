# OPERAÇÃO ZERO PALHA — Retirada operacional do Radar v0.14.4

Data: 2026-10-13
Autoridade: pedido expresso do operador para retirar OPTIONS V2.1 e todas as canas sem edge líquido executável comprovado.
Estado: **GITHUB CLEANUP BRANCH; WINDOWS CUTOVER STILL REQUIRES OPERATOR INSTALLATION**.
Main: UNCHANGED. Exchange mutation: NONE. Trading: NONE. Render: UNCHANGED.

## Critério

**Só pode integrar a vista ativa do Radar uma estratégia com prova economicamente defensável, líquida de todos os custos, e elegibilidade operacional válida.** Nenhuma das oito na registry v3.7 possuía essa prova à data desta operação. Suspender ou retirar operacionalmente uma hipótese incompleta **não equivale** a declará-la cientificamente NO_EDGE.

## Retiradas (8/8)

| ID | Estado de retirada | Motivo sustentado |
|---|---|---|
| OPTIONS-SPOTPERP-001-V2.1 | OPERATOR_RETIRED + EXACT MEXC MARKET/MARKET 10X ROUTE NO-GO | Final audit 2026-10-13 PR #202; historical implied break-even 15.19bps vs 16bps fee-only, broker stop/forward economics not certified. Never reintroduce this exact fork. |
| TFG-DONCHIAN-REGIME-ADAPTATION-V1 | RETIRED UNPROVEN EXECUTION | Parent 1D 2026 protected FAIL, regime 12H current forward execution integrity FAIL; no valid capital evidence; do not conflate current implementation failure with proof every possible regime mechanism is dead. |
| ETF-CME-INSTFLOW-001 | RETIRED FRAGILE ECONOMICS | 2025 OOS marginal stress and leave-one-out FAIL; not robust executable net edge. Q4 2026 holdout remains sealed. |
| BNB-LAUNCHPOOL-DEMAND-001 | RETIRED NO PROSPECTIVE SAMPLE | 0/25 eligible causal prospective events as of Oct 8; no NO_EDGE claim. |
| HTF-DH03-12H-STANDALONE-FORWARD-V1 | RETIRED NO PROSPECTIVE EVIDENCE | Source/waiting first eligible signal; no capital proof. |
| CED1D-0031 | RETIRED INSUFFICIENT/ARCHIVE GAP | 14/60 forward at Oct 9; source 404 reported Oct 10; not a proven NO_EDGE. |
| EMA6H-50X200-REGIME-DEPENDENCY-001 | RETIRED TEMPORAL FRAGILITY | No adequate forward + execution + net-cost proof. |
| CRYPTO-INTRAWEEK-RV-001 / CIRV-HAR-DOW-BTCETH-001 | RETIRED M6 SHADOW ONLY | No demonstrated executable edge; remains an unproven hypothesis, not a rejection of all volatility mechanisms. |

Evidence:
- `audit/crypto-lab-net-edge-verdicts-2026-10-09/audits/CRYPTO_LAB_GLOBAL_NET_EDGE_VERDICTS_2026-10-09.md`
- `audit/radar-authority-economic-integrity-2026-10-10/audits/RADAR_AUTHORITY_ECONOMICS_INTEGRITY_AUDIT_2026-10-10.md`
- `audit/options-v21-10x-final-truth-gate-2026-10-13/audits/OPTIONS_V21_10X_FINAL_EXECUTION_VERDICT_2026-10-13.md`

## Implemented remote changes

- Active registry v3.7 (8 candidates) -> v3.8 (0 candidates, 0 focus); explicit retirement authority and no capital.
- Historical archive 44 -> 52 original evidence records preserved with explicit operator retirement reason and original status. Protected 5 research fronts remain scientifically distinct and are NOT live candidates.
- Windows source `windows_node_entry.py` recognizes intentional zero candidate mode and **does not start** DH03, forward supervisor (including OPTIONS, BNB, ETF, TFG and EMA6H), CIRV, or Render sentinel. Only offline diagnostic HTTP dashboard on loopback port 8787.
- Dashboard treats empty registry as intentional `NO_ACTIVE_CANDIDATES`, not `REGISTRY_DESYNC`, and displays no bots; it suppresses stale standing-authority routes **in this Radar's presentation**. Historical standing authority file is not modified/deleted; this does NOT revoke any separate trading executor.
- Regression gates assert empty active, 52 archive, no thread startups and fail-closed for stale candidates under retirement header.

## Operational boundary

**Nothing has changed yet on the operator's Windows computer.** The existing v0.14.4 EXE might still show and run the eight watch motors until safely stopped/upgraded. Independent `CryptoLab-OPTIONS-V21-Futures-AutoLive`, Triple Fishing V03/V04, BNB AutoLive and ConvexRadar have separate scheduled tasks and executable processes; a GitHub registry change does not disable them. No claim to have changed/disabled any independent motor.

The user previously reported MEXC Futures positions and open orders zero, but that is historical confirmation and must not be treated as fresh account proof for stopping any process that could be managing positions. Never blindly stop/kill an executor with an active Futures position, active order, TP/SL, or uncertain ledger. Do not delete DPAPI secrets, API keys, fills, receipts, ledger or scientific freezes.

The Radar V0.14.4 *public observer* can be replaced only after an explicit process/path identity check, complete backup and available zero-watcher build receipt, with the previous watchdog/task disabled; never kill unverified PIDs.

## Final meaning

**REMOTE CLEANUP DONE** once CI passes on the cleanup branch. **PC RADAR CLEANUP PENDING USER-SIDE CUTOVER** until operator runs the exact safe steps. Live trading go: NONE. No automatic rehabilitation of retired strategies under the same ID; new scientifically distinct families require independently frozen proposal and user consent.
