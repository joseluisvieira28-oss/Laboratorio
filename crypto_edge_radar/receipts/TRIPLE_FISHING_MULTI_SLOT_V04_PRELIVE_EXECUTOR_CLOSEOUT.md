# TRIPLE FISHING MULTI-SLOT V0.4 — PRE-LIVE EXECUTOR CLOSEOUT

Date: 2026-10-02
Branch: `triple-fishing-multislot-v04-2026-10-02`

## Verdict

`EXECUTOR_V04_PRELIVE_PASS__LOCAL_READY_CHECK_AND_CONTROLLED_HANDOVER_REMAIN`

The three-slot small-fish execution architecture is implemented, fault-tested and packaged for Windows.

It is deliberately **not live-armed from the repository**. The final real-account gate must be performed on the operator PC with authenticated read-only MEXC access before an ACTIVE V0.4 authority may be issued.

## Frozen capacity and risk

- maximum simultaneous positions: 3
- one active position per symbol
- no late chase
- no blind resend
- isolated margin only
- Auto Margin Add OFF
- aggregate max notional: 30 USDT
- aggregate max initial margin: 14 USDT
- daily realized-loss kill: 5 USDT
- rolling 7-day realized-loss kill: 5 USDT

Lanes:
- OPTIONS V2.1: BTC_USDT LONG/SHORT, 1x, max 10 USDT notional, max one position; notional preserves parent weight
- BNB Launchpool: BNB_USDT LONG, 5x, max 10 USDT notional / 2 USDT initial margin, max one position
- DH03: frozen six-symbol universe, LONG, 5x, max 10 USDT notional / 2 USDT initial margin per position, one active per symbol, protective TP/SL required

If the current MEXC venue minimum exceeds the lane's 10 USDT notional cap, the signal is rejected. Size is never raised to chase venue minimums.

## Executor implementation

Implemented:
- durable capacity-three reservation ledger;
- deterministic external OIDs and intent-before-transport exactly-once flow;
- equal-target arbitration gives one eligible signal per lane first, then deterministically fills spare capacity;
- symbol collision and lane-cap blocking;
- OPTIONS 1x transport separated from 5x BNB/DH03 transport;
- aggregate risk/capacity/accounting gates;
- fresh Hedge Mode and clock check before every new entry;
- current contract/minimum, fee and spread/friction checks;
- independent active-session lifecycle for up to three positions;
- DH03 protective TP/SL ownership;
- independent scheduled exits;
- kill switch blocks new entries and drives owned positions toward exit;
- entry unknown-ACK recovery without blind resend;
- exit unknown-ACK recovery without blind resend;
- restart/reconciliation with multiple simultaneous positions;
- per-position close reconciliation and exact reservation release;
- realized-loss continuity across V0.4, V0.3 and legacy receipt roots;
- OPTIONS historical accounting correction overlay continuity.

## Production-path tests

Canonical latest Windows pre-live build:
- run: `37002662000`
- source head: `b82e7d1e4189db6914e264bc763c664d06bd1ed6`
- conclusion: SUCCESS
- production/fault-injection tests: **33 PASS**

The tests include:
- three distinct positions active simultaneously;
- fourth position rejected at capacity;
- same-symbol conflict rejection;
- OPTIONS exact 1x mapping;
- BNB/DH03 exact 5x mapping;
- unknown entry ACK accepted by synthetic exchange then recovered without second submission;
- unknown exit ACK accepted then reconciled without second exit submission;
- three-position restart/recovery;
- kill switch exit management for all three positions;
- readiness tamper blocks new entry but does not trap owned exits;
- draft repository authority cannot activate the executor.

## Windows artifact

Artifact:
- ID: `11223574491`
- name: `mexc-triple-fishing-multislot-v04-windows-prelive`
- size: 23,441,566 bytes
- SHA256: `903a46dd54dc98da2e441318d6cdf1046d5f98eae21767529ed221138eab7921`
- expiry: 2026-10-16T11:45:41Z

The bundle contains:
- `MEXCTripleFishingOperatorV04.exe`
- `MEXCTripleFishingMultiSlotReadyV04.exe`
- one-shot read-only Ready Check;
- guarded V0.4 runtime;
- status, emergency-stop and flat-only disarm scripts;
- controlled arm script;
- frozen V0.4 policy, draft authority, manifest and governance freeze.

The build contains **no ACTIVE authority and no armed marker**.

## Activation binding

New entries require all of the following:
1. a PASS V0.4 readiness receipt from the operator PC;
2. an ACTIVE authority with ID `OPERATOR-FUTURES-GLOBAL-V0.4-ACTIVE`;
3. that ACTIVE authority must bind the exact SHA256 of the readiness receipt;
4. the armed marker must bind both the exact readiness-receipt SHA256 and exact ACTIVE-authority SHA256;
5. no kill switch;
6. fresh per-entry Hedge Mode, server-clock, account, portfolio, loss-kill, contract, minimum-size, fees and friction gates.

The current repository only contains `OPERATOR_FUTURES_GLOBAL_AUTHORITY_V04_DRAFT.json`; therefore the executor fails closed before order submission if somebody launches the EXE prematurely.

## Remaining operator-PC gate

Run:
`Ready_Check_MEXC_Triple_Fishing_V04.ps1`

It performs authenticated MEXC **GET/read-only** checks only and writes:
`%LOCALAPPDATA%\CryptoLab\TripleFishingV04\live_state\triple_ready_v04.json`

It also prints:
`READY_RECEIPT_SHA256=<sha256>`

The Ready Check validates:
- account equity and available balance;
- Hedge Mode;
- zero open positions/orders/TP-SL for initial controlled handover;
- current contract/minimum-size feasibility;
- current fee data;
- server clock;
- empty V0.4 ledger;
- legacy armed markers;
- daily/rolling loss continuity and receipt accounting.

If it fails, do not bypass the blocker.

If it passes, the exact receipt/hash becomes the input to the controlled activation/handover step.

## Governance

- current V0.3 authority automatically replaced: FALSE
- V0.4 ACTIVE authority included in repository: FALSE
- V0.4 armed marker included: FALSE
- real orders created by this work: FALSE
- exchange mutation by this work: FALSE
- main merge: FALSE

At closeout, the software side is ready for the operator-PC gate. Claiming that three-slot live trading is already active would be false.
