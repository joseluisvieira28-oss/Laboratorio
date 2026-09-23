# DEFI-LIQUIDATION-SHOCK-001 — KAMINO PROGRAM SIGNATURE DAILY MANIFEST FREEZE V0.1

Date: 2026-09-23
Status: SOURCE-TRANSPORT INDEX ONLY / OUTCOME-BLIND / FAIL-CLOSED

Purpose:
Convert the already-preserved Kamino program-signature crawl into a compact daily source manifest so later daily censuses can prove exact queue reconstruction without repeatedly downloading multi-gigabyte parent artifacts.

This does NOT classify liquidation instructions and does not inspect transaction bodies.

## Frozen source lineage

Newer historical slice:
- run `35689367726`
- artifact `10681229919`
- name `dls-kamino-rpc-first-success-v01`
- SHA256 `bd0fd03a095e93fbdb95bfd6266686ee076b11ab863822f06430b1c77c6d3e74`

Older continuation slice:
- run `35704794316`
- artifact `10686881756`
- name `dls-kamino-rpc-first-success-v01b`
- SHA256 `15097adc6e833edfc99ab11f24c6c4057752b2df7c5de831567bdc6cc01ecf14`

Program:
`KLend2g3cP87fffoy8q1mQqGKjrxjC8boSyAYavgmjD`

## Input order

Within each artifact, `signatures_page_*.json` files are read in ascending page number and rows in their original API order, newest -> oldest.

Artifact order is prospectively fixed:
1. newer slice;
2. older continuation slice.

The join must be monotonic in blockTime. Any chronology inversion fails closed.

## Per-day manifest entry

For every UTC calendar day encountered:
- UTC date;
- first/newest and last/oldest program signature in source order;
- immediately newer adjacent program signature, if present;
- immediately older adjacent program signature, if present;
- row count;
- signature-level success count (`err == null`);
- signature-level failed count;
- canonical queue SHA256 where queue rows are exactly:
  `signature, slot, blockTime, err`
  sorted oldest -> newest by `(blockTime, slot, signature)`.

The manifest stores no transaction instruction data.

A daily entry is marked `rpc_reconstruction_anchor_pair_ready=true` only when both adjacent boundary signatures exist.

## Integrity

- every row must contain string signature, integer slot and non-null blockTime;
- blockTime must be globally non-increasing in source API order;
- rows in a daily canonical queue must have unique signatures;
- duplicate page-file paths or malformed JSON fail closed;
- the known continuation cursor relationship is recorded, not inferred as an economic fact.

No prices, amounts, returns, PnL, direction, market outcomes, liquidation-size thresholds, live trading, orders, wallets, exchange mutation, paid sources, account creation or main merge.
