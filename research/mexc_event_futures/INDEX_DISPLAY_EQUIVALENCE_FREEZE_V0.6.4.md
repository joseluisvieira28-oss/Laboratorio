# MEXC EVENT FUTURES LAB — INDEX DISPLAY EQUIVALENCE SOURCE FREEZE V0.6.4

Date: 2026-10-02
Status: SOURCE-ONLY / READ-ONLY / FAIL-CLOSED

## Prior source result

V0.6.3.4 passed the current Event Futures product matrix source gate:
- 20/20 current asset × horizon payout cells captured from the public DOM.
- BTCUSDT and ETHUSDT currently expose 10m / 30m / 1H / 1D.
- NVDAUSDT, MUUSDT and SPCXUSDT currently expose 10m / 30m / 1H / 4H.

The same observations showed a visible chart source labeled "Index" whose current candle Close was numerically close to the public standard-futures index endpoint.

## V0.6.4 mission

Test whether the Event Futures public page's live visible **Index chart current Close** tracks the public MEXC contract index endpoint closely enough to support a source-equivalence candidate.

This is NOT a settlement-equivalence proof.

## Frozen assets

- BTCUSDT -> BTC_USDT
- ETHUSDT -> ETH_USDT
- NVDAUSDT -> NVIDIA_USDT
- MUUSDT -> MUSTOCK_USDT
- SPCXUSDT -> SPCXSTOCK_USDT

## Frozen sampling

Per asset:
- 12 consecutive observations;
- approximately 2 seconds apart;
- DOM index Close captured first;
- public contract index GET captured immediately after DOM read.

Total target pairs: 60.

## Frozen metrics

For each paired observation:

`difference_bps = abs(dom_close - public_index) / public_index × 10000`

Gate:
- at least 55 valid pairs of 60;
- at least 95% of valid pairs <= 1.0 bp;
- median difference <= 0.25 bp.

If passed, verdict:
`PASS_CURRENT_DISPLAY_EQUIVALENCE_CANDIDATE`

This permits calling the public endpoint a current-display equivalence candidate only.

It does NOT prove:
- Event Futures entry reference semantics;
- expiry settlement tick;
- rounding;
- historical equivalence;
- payout pricing model.

## Read-only boundary

- public page and public GET endpoint only;
- abort all non-GET browser requests;
- no horizon interaction required;
- no Up/Down click;
- no amount;
- no order;
- no authentication;
- no account mutation;
- no trading;
- no merge to main.
