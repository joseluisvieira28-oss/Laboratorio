# NVDA CROSS-VENUE SOURCE GATE — V0.6.1 TECHNICAL AMENDMENT

Date: 2026-10-04
Status: SOURCE-ONLY / PRE-OUTCOME / TECHNICAL SOURCE ADJUSTMENT

## V0.6 incident

The V0.6 source probe stopped before producing a source verdict because the GitHub-hosted runner received HTTP 451 from Binance Futures due datacenter-location restrictions.

No historical outcomes, lead/lag returns or directional performance were opened.

## Source adjustment

The next source family is explicitly narrowed to:

`Bitget NVDAUSDT -> MEXC NVIDIA_USDT`

This is scientifically legitimate because MEXC public contract metadata explicitly lists `BITGET_FUTURE` as one of the NVIDIA index origins.

Binance remains documentary corroboration only and is not required by V0.6.1 runtime.

Pyth is excluded from V0.6.1 because current Hermes access requires an API key.

## V0.6.1 PASS rule

`NVDA_BITGET_MEXC_SOURCE_PASS` requires:
- MEXC `NVIDIA_USDT` identity present;
- MEXC `indexOrigin` includes `BITGET_FUTURE`;
- Bitget public `NVDAUSDT` USDT-FUTURES instrument present;
- both live prices available and within 500 bps;
- both venues expose public 1-minute candles;
- no account/API key/private endpoint.

Even on PASS, historical outcomes remain CLOSED until a separate pre-outcome freeze.
