# V0.4.1 QUEUE-SUBSPACE CLOSEOUT

Date: 2026-10-07
Parent amendment: 023ceb3c26e603282ebf48fac150c3f4141e0881
Outcomes opened: NO

## Verdict

QUEUE_SUBSPACE_HISTORICAL_ROUTE_INVALID

The historical ABCI request /store/staking/subspace returned non-empty 0x41 queues and, on several chains, two independent providers returned identical payloads. However the payload is not historical state at the requested height.

Direct evidence:
- Cosmos Hub request at H=20,000,000 (block time 2024-04-14) returned queue keys encoding completion timestamps in October 2026.
- therefore the queue contents cannot be the staking queue at H=20,000,000.

Code-level cause:
- Cosmos SDK IAVL /key query calls GetVersioned(key, res.Height).
- the /subspace query instead runs KVStorePrefixIterator(st, subspace) over the store object without obtaining an immutable tree at res.Height.
- response height can therefore reflect the requested height while the prefix iteration is over the current store.

Disposition:
- do not use QUEUE_SUBSPACE_PROBE_V041 queue contents, pair counts or values as historical evidence;
- do not use those counts for materiality or sample gates;
- exact historical /key queries remain potentially valid because they are versioned;
- V0.4 continues only through other source routes frozen before event counts.

No market data was opened.
