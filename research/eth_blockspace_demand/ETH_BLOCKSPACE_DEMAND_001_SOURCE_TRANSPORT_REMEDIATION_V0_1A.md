# ETH-BLOCKSPACE-DEMAND-001 — SOURCE TRANSPORT REMEDIATION V0.1A

Date: 2026-09-19
Status: **FROZEN BEFORE REMEDIATED SOURCE PROBE / OUTCOME-BLIND**

The first source-only run `35440306457` returned
`SOURCE_ACQUISITION_TECHNICAL_FAILURE` with 2/4 frozen blocks reaching the
unchanged >=2-provider quorum. No market outcome, return, PnL, or 2025/2026
source was accessed.

This is a transport remediation only.

Unchanged:
- exact four frozen blocks: 13,000,000; 15,000,000; 18,000,000; 21,000,000;
- Ethereum mainnet;
- exact required block-header fields;
- >=2 independent usable providers per block;
- exact block-hash agreement;
- pre-2025 timestamp firewall;
- all PASS/failure classifications.

Added public read-only RPC candidates:
- `https://eth.llamarpc.com`
- `https://rpc.flashbots.net`

The original three providers remain. No provider may be selected or dropped
based on economic values; the gate uses all five and retains the same >=2 quorum.

The remediated receipt may expose only provider/block availability, identity
agreement and field-sanity status. It must not print or persist base-fee,
gas-used or gas-limit numeric values.

No outcome access is authorized.
