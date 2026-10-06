# CEX-TRANSFER-RAIL-RECOVERY-BASIS-001
## V0.1.1 SOURCE PARSER REMEDIATION FREEZE
Date: 2026-10-06
Parent scientific freeze: CTRRB_V01_SOURCE_MECHANISM_FREEZE_2026-10-06.md
Status: FROZEN BEFORE ANY MARKET OUTCOME

### Reason
The original source runner incorrectly assumed Coinbase Status history exposed /incidents/<id> anchors. Official HistoryIndex React props instead expose each 3-month page as structured JSON in data-react-props, with month/year coverage and incident rows containing code, name, message, timestamp and impact.

This remediation changes SOURCE EXTRACTION ONLY. It does not alter the economic hypothesis, sample gate, treatment, horizon, reference policy, or any outcome rule. No market outcome has been opened.

### Authoritative census frame
Use Coinbase Exchange official history:
https://status.exchange.coinbase.com/history?page=N

Decode the official HistoryIndex data-react-props.
Mechanically enumerate every month from January 2022 through December 2025.
Coverage is complete only if all 48 calendar months appear exactly in the official paginated sequence.

Group by official incident code. A code is one incident/shock.

### Frozen incident identity rule
To eliminate network/asset ambiguity BEFORE outcomes, primary V0.1 accepts only:
1. an exact token ticker/name explicitly named in the incident title; OR
2. an unambiguous native L1/L0 network where the network and native spot asset are one-to-one under the frozen alias table.

Reject:
- "multiple networks";
- generic L2/network incidents where the affected transferable asset set is not one token;
- ERC-20/multi-token incidents;
- fiat/payment incidents;
- titles with no deterministic frozen asset mapping;
- token migrations/delistings/trading-mode changes.

Frozen native/ticker mapping:
BTC=Bitcoin/Bitcoin Network
ETH=Ethereum/Ethereum Network
LTC=Litecoin
BCH=Bitcoin Cash
SOL=Solana
XRP=XRP/XRPL
ADA=Cardano
ALGO=Algorand
AVAX=Avalanche
ATOM=Cosmos
DOT=Polkadot
XLM=Stellar
FIL=Filecoin
NEAR=NEAR
STX=Stacks
VET=VeChain
TIA=Celestia
SEI=Sei
SUI=Sui
ZEC=Zcash
OSMO=Osmosis
KAVA=Kava
TAO=Bittensor
ICP=Internet Computer
APT=Aptos
HBAR=Hedera
XTZ=Tezos
DOGE=Dogecoin
EGLD=MultiversX
INJ=Injective
MINA=Mina

MATIC/POL is excluded from V0.1 because the 2024 token transition can contaminate identity over the study period.
Generic Arbitrum/Base/Optimism/Polygon network incidents are excluded unless a specific eligible token ticker is explicitly named.

### Frozen official-detail verification
For every mapped candidate, fetch:
https://status.exchange.coinbase.com/incidents/<official_code>

Eligibility requires official incident-detail text to prove:
- sends/receives/deposits/withdrawals/blockchain transactions impaired;
- spot buys/sells/trading explicitly unaffected or available;
- resolved/restored status;
- no planned/scheduled maintenance language;
- no trading outage/limit-only/suspension contamination.

If the incident-detail page is unavailable, reject rather than infer.

### Frozen time boundary extraction for source capability
The official history timestamp range is the source for incident start and end.
Parse local PST/PDT range using the history month/year.
If exact start/end cannot be deterministically parsed, reject.

These timestamps are SOURCE metadata only. T_recovery analysis semantics will be frozen separately only after SOURCE_GATE_PASS.

### Frozen market-data capability probe
Still no values may be logged, stored, compared or calculated.

Coinbase affected venue:
- exact {SYMBOL}-USD 1-minute candles around source end timestamp;
- record HTTP/schema/row count only.

Binance reference:
- exact {SYMBOL}USDT 1-minute monthly public archive on data.binance.vision for the source month;
- use HEAD/metadata only; do not download archive contents during source gate.

Event passes capability only if:
- Coinbase candle probe returns non-zero row count without logging contents;
- Binance Vision monthly archive returns HTTP 200 for the frozen symbol/month.

OKX remains optional second reference and is not required for V0.1 source pass. If not proven before outcomes it will not be used in Development.

### Sample gate remains unchanged
>=12 independent unplanned eligible incidents
>=4 unique assets
no single asset >40%
all with affected + frozen reference historical capability

2026 remains closed.
No outcomes have been opened.
