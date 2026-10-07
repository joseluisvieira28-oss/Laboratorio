# V09 Avalanche Source Audit — 2026-10-07

Mission: `AAVE-GOV-LT-FORCED-DELEVERAGING-001`  
Mode: SOURCE-ONLY; no behavioral outcomes opened.

## Provenance

- Workflow run: [37570703748](https://github.com/joseluisvieira28-oss/Laboratorio/actions/runs/37570703748)
- Head: `1560b5bc8a89aca36b346666051d0bc11512c6bc`
- Artifact: `aave-gov-lt-avalanche-v09` (ID `11461296968`)
- Artifact ZIP SHA-256: `8bdfb3a469f81cb51750bca007d93d73c0da5dcfc3b5493c770981eaaaa06ced`
- `RECEIPT.json` SHA-256: `4c86ea8a63216915c0ec3d0c135037f111a17f9a1d9e9886373a59f118dd5737`
- `checkpoint.json` SHA-256: `e20831a7990ba6f6e3f5ee8b3f60eb425cf3d8241f527cc94ca01f4b5163247d`
- `requests.jsonl` SHA-256: `cd19ee5ef398408afaeb0ea47b6913a85fd1732c76000ed421574a5b69485d20`
- Public unauthenticated source: `https://api.avax.network/ext/bc/C/rpc`
- Configurator: `0x8145eddDf43f50276641b55bd3AD95944510021E` (Aave Address Book)

## Acquisition audit

- Continuous range: block `0` through `55159595`
- Terminal timestamp: `1735689598` (2024-12-31 23:59:58 UTC), greatest block not later than the frozen cutoff
- Accepted intervals: `2758`
- Coverage gaps: `0`
- Requests: `2788`; HTTP 200: `2788`
- Unique response hashes: `2787`
- Referenced raw responses missing: `0`
- Raw response hash mismatches: `0`
- Unique configurator events: `68/68`

## Event census and sequential state reconstruction

- `CollateralConfigurationChanged`: `53`
- `EModeCategoryAdded`: `5`
- `EModeAssetCategoryChanged`: `7`
- `Upgraded`: `3`
- Base-LT decrease rows after an observed prior state: `12`
- Distinct base-LT effect transactions: `8`
- eMode-LT decrease rows: `1`
- Distinct eMode-LT effect transactions: `1`
- Provisional Avalanche candidate effect transactions: `9`

The 9 effect transactions are not yet defensible independent economic shocks. Governance V2/V3 lineage, advance signal eligibility, proposal/payload clustering, and cross-chain clustering remain mandatory. Direct/Risk-Steward executions without an advance governance anchor remain timing-ineligible.

## Gate state

`SOURCE_GATE_PENDING / HYPOTHESIS_NOT_TESTED`

No behavioral outcomes, Development run, 2026 data, trading, or account activity were opened. The frozen V01/V02 authorities and all prior receipts remain unchanged.
