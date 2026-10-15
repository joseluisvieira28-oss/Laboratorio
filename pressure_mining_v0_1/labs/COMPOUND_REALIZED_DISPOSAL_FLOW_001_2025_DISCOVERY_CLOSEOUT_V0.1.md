# COMPOUND-REALIZED-DISPOSAL-FLOW-001 — PROTECTED 2025 DISCOVERY CLOSEOUT V0.1

Date: 2026-09-28
Status: TERMINAL / DISCOVERY_FAIL_NO_PROMOTION / NO RESCUE

## Authoritative execution

GitHub Actions run: 36393478777
Job: 108834325570
Artifact: 10957865022
Artifact digest: sha256:58572307983a4264b32877762545c92854c57b9a6cf316f3657b12bcea30ffab
Receipt pre-self SHA256: eb5dd9e5b586c8b913872e21ca79dbe248c8b13210b729f795d398bc757d1600

Canonical freeze:
- commit 2191bbf741ced5f801d8ae4034bd126c3b91cbc8
- Git blob d36c24bffd8a0f16787e0b7cf72b2d7b60e2f430
- 30m horizon
- WETH/ETH, LINK, UNI, COMP
- short collateral vs BTC
- BASE20 / STRESS30
- deterministic same-asset 30m overlap suppression
- ISO-week cluster bootstrap, 10,000 resamples, seed 20260927
- original 12 PASS gates
- no rescue

## Sample

- N = 373
- unique ISO weeks = 35
- invalid missing-bar events = 0
- ETHUSDT = 167
- LINKUSDT = 93
- UNIUSDT = 78
- COMPUSDT = 35

Sample gates passed.

## Primary economics

- gross mean = +9.8696406757 bps
- BASE20 net mean = -10.1303593243 bps
- BASE PF = 0.8511858318
- BASE win rate = 36.461126%
- STRESS30 net mean = -20.1303593243 bps
- STRESS PF = 0.7303816122
- ISO-week bootstrap 95% CI on BASE mean = [-26.6280269698, +9.9269535538] bps

The frozen economic and statistical gates fail.

## Breadth

BASE20 mean by asset:
- COMPUSDT: -236.4030656510 bps / PF 0.1818399621
- ETHUSDT: -3.1711003635 bps / PF 0.9148815907
- LINKUSDT: +27.6460319600 bps / PF 1.5223598392
- UNIUSDT: +31.4612315158 bps / PF 1.5934887000

Every-asset-positive gate FAILS.

Leave-one-asset-out BASE mean:
- exclude COMP: +13.3002463604 bps
- exclude ETH: -15.7720886761 bps
- exclude LINK: -22.6775178580 bps
- exclude UNI: -21.1274579193 bps

Every leave-one-asset-out-positive gate FAILS.

## Temporal diagnostics

BASE20 mean by quarter:
- 2025-Q1: +12.6692412730 bps
- 2025-Q2: -0.5246006015 bps
- 2025-Q3: -40.1318477439 bps
- 2025-Q4: -26.7189975794 bps

These are diagnostics only and create no rescue path.

## Concentration

- largest positive event share = 19.8189479% -> PASS <=25%
- largest positive ISO-week share = 44.0677415% -> FAIL <=35%

## Frozen gate outcome

PASS:
- N >= 100
- >=20 ISO weeks
- all 4 assets >=10 events
- largest positive event share <=25%

FAIL:
- pooled BASE mean >0
- pooled BASE PF >1
- pooled STRESS mean >0
- pooled STRESS PF >1
- bootstrap lower95 >0
- every asset BASE mean >0
- every leave-one-asset-out BASE mean >0
- largest positive ISO-week share <=35%

## Final classification

DISCOVERY_FAIL_NO_PROMOTION

Exact 30m realized-disposal child is CLOSED.
No direction inversion, horizon change, asset filtering, fee reduction, routed-only subset, calendar rescue, alternate benchmark or other post-outcome rescue is authorized.

2026 market outcomes remain unopened.
No live trading, orders, exchange/wallet mutation, capital or main merge occurred.
