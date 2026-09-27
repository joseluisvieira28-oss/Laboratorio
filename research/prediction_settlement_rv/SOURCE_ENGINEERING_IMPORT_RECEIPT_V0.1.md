# PREDICTION-SETTLEMENT-RV-001 — SOURCE ENGINEERING IMPORT RECEIPT V0.1

Date: 2026-09-27
Status: ENGINEERING_EVIDENCE_ONLY / NOT SCIENTIFIC_OUTCOME

## Sibling engineering lineage

Repository:
joseluisvieira28-oss/Laboratorio

Sibling branch:
prediction-oracle-basis-v0.1

Relevant pre-maturity source-only run:
- GitHub Actions run: 36339166888
- artifact: 10938710472
- artifact ZIP SHA256: a127636dfaf8c4662e754312f6933dbf2673752dbaf066496577ea69c600d0d0
- receipt JSON SHA256: 0371f2753c809243f8aec693abb229c6f6d6521aff07612dfdaeb16e22738fe0
- internal receipt SHA256 field: 7c1e98227d5385c7f270a0e944996803d6952972fb54ebaa4797abd1f9b21f42

Source-only findings:
- 20 same-time / same-nominal-strike pairs existed for resolution 2026-09-27T19:00:00Z;
- Polymarket rules identified Binance BTC/USDT 1h Close;
- Kalshi rules/reference identified CF Benchmarks BRTI;
- Kalshi threshold encoding preserved K - $0.01;
- Polymarket CLOB schema validated;
- Kalshi orderbook_fp schema validated;
- 20/20 matched pairs had machine-readable book routes;
- Kalshi had at least one depth side populated on 20/20;
- Polymarket had depth levels on both token books for 12/20 at the sampled source snapshot;
- no matured outcomes were read;
- no PnL or economic outputs were computed;
- no authenticated trading endpoint or order was used.

Separate Kalshi schema-only proof:
- run: 36339083776
- future KXBTCD book schema: orderbook_fp.yes_dollars / orderbook_fp.no_dollars
- non-empty levels are two-element arrays [price, quantity];
- no price/size values were printed in the diagnostic.

## Governance use

These facts justify source-engineering design only.
They do NOT satisfy this new lab's Source/Data Gate.

PREDICTION-SETTLEMENT-RV-001 must independently rerun source feasibility after its own authority freeze.
