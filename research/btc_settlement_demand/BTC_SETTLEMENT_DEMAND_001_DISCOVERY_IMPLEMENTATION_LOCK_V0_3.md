BTC-SETTLEMENT-DEMAND-001 — DISCOVERY IMPLEMENTATION LOCK V0.3

FAMILY_ID: BTC-SETTLEMENT-DEMAND-001
MVE_ID: BSD-WOW7D-1D-001
DATE_LOCKED: 2026-09-14
STATUS: PRE-OUTCOME IMPLEMENTATION FROZEN / READY FOR SINGLE TRIGGER

Authority Git blob: 821e7d2eff241796aa948f8b90bea4b2fd0e7b1b
Authority text SHA256: 18a45507ac36e15a5824043b46e7a4f43e377cc2775e54893e88b26395b12c7e
Authority Drive ID: 1uE1QmcrIWUG-aV0kkFg1qXllQoQ5OJcX
Authority creation commit: 6fd4f4e9ae1f3bb030795919528229b44cdfee23

Discovery runner Git blob: 4376267147885c3a1f91c7dea67cd6efdda8dd59
Workflow hardening commit immediately before this lock: 172b418a1a531a53fab286f332e0145e64a1b248
Source Gate artifact: 10355248843
Source Gate ZIP SHA256: d58b3e06683d827f393760112927b8c9314cdfdfb6ae559fbf1301b29383f163
Bound raw source SHA256: e0488714ce6023589de3e9cd15524c5f1e643a0ae0028147c8cb830b313ffa7f
Bound source manifest SHA256: 108525b5d3c3f331f8aef4dbcfcec05c8ab0221ba7c8cbc179d8c944c239b9cd

The next commit is authorized to add ONLY:
.github/btc-settlement-demand-discovery-v03.trigger

The workflow has a trigger-only mutation firewall. Any change to authority, runner, workflow or research bytes in the trigger commit must stop execution before market outcomes.

User authorization already received for the one-shot 2018-2024 Discovery. 2025 and 2026 remain locked. No live trading, exchange mutation, main merge, Render deployment or post-outcome tuning is authorized.
