# MEXC ↔ HYPERLIQUID NAS100 — SOURCE GATE CLOSEOUT V0.5

Date: 2026-10-04
Run: 37193291935
Artifact SHA256: `dfe1a51e455df9e1d6f04271d1212f8a5db30d4e769ad9c3c8c5176500d9c691`

## Public MEXC evidence

`NAS100_USDT` contract metadata:
- `indexOrigin=["HYPERLIQUID"]`
- `apiAllowed=true`
- `isZeroFeeSymbol=true`

Source-probe MEXC index snapshot:
- NAS100 index price: ~30,788

## Hyperliquid candidates

The public Hyperliquid metadata scan found two semantic candidates:
- `km:USTECH` — mark ~733.79, oracle ~732.18, no live BBO at probe time;
- `mkts:USTECH` — mid ~751.105, mark/oracle ~751.01.

Both are US-tech / Nasdaq-100-style synthetic perpetual markets, but neither is on the same numerical scale as the MEXC NAS100 index.

The MEXC public NAS100 product states that the contract is based on the NAS100 / Nasdaq-100 index, but the public materials inspected do not disclose a transformation/normalization formula connecting the MEXC ~30k index level to the Hyperliquid ~700 USTECH contracts.

## Verdict

`SOURCE_BLOCKED_HYPERLIQUID_NAS100_IDENTITY`

No historical outcomes or lead/lag returns were opened.

Do not infer a scaling factor from the live snapshot and do not choose a candidate by later performance.

## Governance

- outcomes opened: 0
- no account reads
- no wallets
- no private endpoints
- no orders
- no mutation
- no live trading authorization

## Next mine

NVIDIA is next because MEXC public metadata identifies multiple explicit external price sources and both Binance Futures and Bitget publicly list `NVDAUSDT` equity perpetuals tracking NVIDIA common stock.
