# THREE CANAS 100 USDT × 10 — MEXC PUBLIC QUOTE FIELD RECEIPT
UTC date 2026-10-14. User relayed the following output from a manual PowerShell public GET-only query against MEXC Futures. **User-supplied observation; not independently API-fetched or authenticated by the assistant.** The printed `BookUTC` timestamps refer to the snapshot, not perpetual executable freshness. No account/auth/private read, no exchange mutation, no order placed.

## Public field observation
| Field | SOL_USDT | BNB_USDT |
|---|---:|---:|
| Ask | 104.31 USDT | 730.8 USDT |
| Bid | 104.30 USDT | 730.7 USDT |
| ContractSize | 0.1 base per contract | 0.01 base per contract |
| minVol | 1 contract | 1 contract |
| volUnit | 1 contract | 1 contract |
| Public maxLeverage | 300 | 200 |
| Public apiAllowed | True | True |
| Book timestamp (UTC) | 2026-10-14 18:59:34 | 2026-10-14 18:59:35 |
| Observed displayed spread | 0.9587 bps mid | 1.3685 bps mid |

**Interpretation:** 10x is lower than public maxLeverage but *not* proof account leverage tier, regional rights, API key permissions, maker/taker fees or minimum notional. Public `apiAllowed: True` is product metadata, not user-specific key authorization. The user declared account available equity 100 USDT, zero positions; account state remains UNVERIFIED.

## Reproducible capital/risk sizing from exactly this timestamped input
Scenario model: 10x ISOLATED, original V5 4% LONG stop on modeled entry, first book ask entry, per-side **8bps hypothetical taker + 2bps adverse slip** and initial **5bps funding debit reserve** on opening notional (not venue-exact mark funding, not personal fee).

For base qty Q, entry=ask×1.0002, original initial stop=entry×0.96, adverse model stop execution=stop×0.9998; `risk=Q × (entry - adverse_stop + entry×0.0008 + adverse_stop×0.0008 + entry×0.0005)` and `initial_margin=Q×entry/10`. Stop quotes may need further venue tick rounding, which is UNCHECKED.

| Quantity | SOL_USDT | BNB_USDT |
|---|---:|---:|
| 1 min contract = base qty | 0.1 SOL | 0.01 BNB |
| Gross ask notional | 10.431 USDT | 7.308 USDT |
| Entry assumed adverse slipped | 104.330862 USDT | 730.94616 USDT |
| Initial stop price unrounded | 100.15762752 USDT | 701.7083136 USDT |
| Stop market fill assumed after slip | 100.137595994496 | 701.56797193728 |
| Price component of modeled stop loss | 0.4193266005504 USDT | 0.2937818806272 USDT |
| Entry fee projected | 0.00834646896 USDT | 0.00584756928 USDT |
| Stop exit fee projected | 0.00801100767956 USDT | 0.00561254377550 USDT |
| Funding debit reserve | 0.0052165431 USDT | 0.0036547308 USDT |
| **Full modeled loss at stop** | **0.4409006203 USDT** | **0.3088967245 USDT** |
| 10x initial model margin | 1.04330862 USDT | 0.73094616 USDT |
| Stress hypothetical 5bps slip each side loss | 0.4440360896 USDT | 0.3110934467 USDT |

Per-strategy nominal modeled loss ≤0.50 USDT: 1 contract PASS, 2 contracts SOL model 0.8818012406 USDT **FAIL**, 2 contracts BNB model 0.617793449 USDT **FAIL**. Thus max 1 minimum contract per *independent protected logical strategy* at the fixed 0.50 USDT trade-loss budget in this scenario. With one SOL and one BNB, combined projected cash stop loss is **0.7497973448 USDT** and margin **1.77425478 USDT**. This is not 1.50 USDT guaranteed risk and 10x does not multiply a fixed-notional stop-risk by ten.

## SOL collisions, physical slots and other blockers
- Two original logical SOL strategies share **SOL_USDT**. With 1 SOL minimum contract per signal, simultaneous 2-long signals would target 2 contracts (0.2 SOL) with total theoretical price/fee/funding stop loss 0.88180124 USDT (under SOL group ceiling 1.00 USDT), **but physical position netting, order-level broker stops, fill segmentation, partials and independent strategy ownership are UNPROVEN**. Therefore the PRELIVE policy blocks the SECOND concurrent physical SOL entry. Only 2 distinct simultaneous symbols potentially available until broker-specific safety is demonstrated: SOL_USDT + BNB_USDT.
- Account holdings, existing resting orders, fee schedule, leverage actual mode, contract price tick/trigger mark vs last, initial/maintenance margin tiers, minimum notional, stop acceptance and amendments, recovery after crash, signed strategy signal parity and live-like prospective costed expectancy are still NOT_CHECKED. Orderbook 20-level quantity is not validated at the observed timestamp by this receipt; top ask/bid alone is insufficient for full notional depth/fill proof. **No stop-ACK receipt**.
- Quotes can become stale immediately; STOP using these specific 2026-10-14 18:59:xx UTC prices as live entrance references after that snapshot. Never arm using archived public quotes. A negative or missing live-like gate means NO_LIVE_GO.

**VERDICT:** `PUBLIC_CONTRACT_MIN_STEP_SOURCE_REPORTED` + `HYPOTHETICAL_ONE_CONTRACT_SIZING_PASS_BASE_AND_STRESS` / `BROKER_ACCOUNT_FEES_STOPS_NETTING_UNVERIFIED` / `NO_LIVE_GO`. Preserve raw user observations; no changed original V5 signal/exit/stop science, no protected 2026 holdout, no orders, no main merge.
