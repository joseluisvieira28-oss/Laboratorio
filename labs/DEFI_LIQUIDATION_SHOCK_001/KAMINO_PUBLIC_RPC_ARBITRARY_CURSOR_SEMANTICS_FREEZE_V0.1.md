# DEFI-LIQUIDATION-SHOCK-001 — PUBLIC RPC ARBITRARY CURSOR SEMANTICS PROBE V0.1

Date: 2026-09-22
Status: FROZEN PRE-EXECUTION / SOURCE-TRANSPORT ONLY / OUTCOME-BLIND

Purpose: test whether Solana getSignaturesForAddress before/until cursors can be anchored by ordinary transaction signatures from blocks near the exact frozen Kamino chunk boundaries, enabling direct chronological chunk access without sequentially paging millions of Kamino program signatures.

Target chunk #1:
- start: 2023-11-17T13:25:35Z
- end exclusive: 2023-11-24T13:25:35Z
- program: KLend2g3cP87fffoy8q1mQqGKjrxjC8boSyAYavgmjD

Procedure:
1. use getBlockTime only to locate slots nearest each fixed UTC boundary;
2. use getBlock(transactionDetails=signatures) to obtain an ordinary finalized transaction signature from each boundary-near block;
3. call getSignaturesForAddress with the program address using these arbitrary signatures as before/until cursors;
4. test cursor acceptance and returned blockTime containment only;
5. do not fetch transaction bodies or inspect instruction data.

No liquidation classification, prices, returns, PnL, direction, thresholds, market outcomes, trading, wallets, exchange mutation, or paid source.

This probe cannot establish a first-success boundary. A positive result only authorizes a separately frozen bounded chunk acquisition design.
