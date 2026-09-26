# CCLM-002 PRIOR-ART BOUNDARY AUDIT V0.1

Date: 2026-09-24
Child: CCLM-CCTP-SETTLED-FLOW-002

## Known adjacent work

The lab does not claim novelty for generic propositions such as:
- large stablecoin transfers can coincide with or affect crypto return/volume dynamics;
- stablecoin markets can transmit liquidity/volatility spillovers;
- money flows can relate to cross-crypto return predictability.

Relevant examples reviewed before outcome access:
- Ante et al., "The impact of transparent money flows: Effects of stablecoin transfers on the returns and trading volume of Bitcoin"
  https://www.sciencedirect.com/science/article/pii/S0040162521002833
- Guo et al., "Cross-cryptocurrency return predictability"
  https://www.sciencedirect.com/science/article/pii/S0165188924000551
- Range CCTP flow analysis (descriptive user/route behavior, not our predictive design)
  https://range.org/blog/usdc-via-cctp-how-institutions-and-retail-users-move-money-cross-chain

## Narrow identity retained

CCLM-002 measures only completed CCTP V1 native-USDC migration where destination
MessageReceived and same-transaction MintAndWithdraw prove settlement.

Its candidate information variable is route-signed completed flow between
Ethereum and Avalanche. It is not:
- a generic token transfer;
- a treasury mint/burn series;
- a bridge UI aggregate;
- an unconfirmed source burn;
- a wallet-label or exchange-deposit heuristic.

The predictive experiment below therefore tests whether *completed directional
cross-chain dollar-liquidity migration* contains incremental short-horizon
information for the destination-chain native asset relative to BTC.

No novelty claim is made until empirical and prior-art review both survive.
