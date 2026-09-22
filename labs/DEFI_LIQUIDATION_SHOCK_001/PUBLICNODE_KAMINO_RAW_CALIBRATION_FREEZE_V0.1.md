# DEFI-LIQUIDATION-SHOCK-001 — PUBLICNODE KAMINO RAW CALIBRATION FREEZE V0.1

Date: 2026-09-22
Status: FROZEN PRE-EXECUTION / SOURCE-ONLY / OUTCOME-BLIND

Purpose: test whether the keyless PublicNode Solana RPC can reproduce the exact 16/16 already-frozen Kamino RAW verification set from 2024-12-15.

Scientific identity is unchanged from KAMINO_PUBLIC_RPC_RAW_VERIFICATION_FREEZE_V0.1:
- Program: KLend2g3cP87fffoy8q1mQqGKjrxjC8boSyAYavgmjD
- Discriminator: b1479abce2854a37
- Candidate set: exactly the same 16 signatures/slots embedded in verify_kamino_public_rpc_v0_1.py
- Success predicate: exact slot, meta.err == null, exact program ID, exact discriminator prefix.

Transport-only change:
- from https://api.mainnet-beta.solana.com
- to https://solana-rpc.publicnode.com

Implementation rule: execute a byte-identical copy of the existing frozen verifier except for the RPC endpoint constant. No candidate, slot, discriminator, retry logic, success logic, or classification may change.

Routing:
- 16/16 => PUBLICNODE_KAMINO_RAW_CALIBRATION_PASS
- partial transport/null => PUBLICNODE_KAMINO_RAW_CALIBRATION_PARTIAL_OR_HISTORY_BLOCKED
- content mismatch => PUBLICNODE_KAMINO_RAW_CALIBRATION_CONTENT_MISMATCH_FAIL_CLOSED

A PASS does not prove archive pagination to 2023 and does not grant SOURCE_DATA_PASS. It only permits a separate prospective pagination/archive viability probe.

Firewall: prices=false, returns=false, pnl=false, direction=false, live trading=false, orders=false, wallets=false, exchange mutation=false, paid source=false, account creation=false, merge main=false.
