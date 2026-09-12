# News Shock Lab V0 — FOMC diagnostic execution trigger

Execution authorized only under the existing frozen diagnostic contract:
`NEWS_SHOCK_LAB_V0_FOMC_EVENT_STUDY_FREEZE.json`

Frozen fingerprint:
`ca2c9dae37a6e7ca53211388c19e2762a9e9a1640655af74c9560071b9234c78`

Constraints preserved:
- diagnostic historical event study only;
- official Binance public Spot data only;
- BTCUSDT and ETHUSDT, 1m;
- frozen FOMC event list and frozen control-day contract;
- no parameter search;
- no directional trading rule may be defined from this run;
- no trading authorization;
- no exchange mutation;
- no live trading;
- no merge to main;
- no Render deploy;
- 2026 remains locked and must not be accessed.

Run fail-closed. Stop at the frozen historical diagnostic receipt.
