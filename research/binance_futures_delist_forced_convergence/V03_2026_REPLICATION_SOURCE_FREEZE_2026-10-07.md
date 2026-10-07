# BINANCE-FUTURES-DELIST-FORCED-CONVERGENCE-001
## V0.3 2026 INDEPENDENT REPLICATION SOURCE FREEZE
Date: 2026-10-07
Status: FROZEN BEFORE ANY 2026 MARKET OUTCOME

### Purpose
Independent 2026 replication of the already-frozen V0.2/V0.2.1 forced-settlement convergence mechanism.

This is NOT a rescue by changing thresholds. The later outcome protocol, if source gate passes, must copy V0.2/V0.2.1 exactly.

### Frozen source calendar
Settlement timestamps:
- 2026-01-01 00:00 UTC through 2026-09-30 23:59 UTC.
October 2026 is excluded to avoid incomplete/current-month archive effects.

### Official source authority
Binance public CMS:
- article list endpoint;
- article detail endpoint.

Market archive capability is checked only by official Data Vision .CHECKSUM sidecars.
No ZIP/candle/metrics values may be opened at source stage.

### Eligible source observation
One USDⓈ-M perpetual contract observation if:
1. official Binance article is published before settlement;
2. article explicitly states remaining positions will be closed and automatically settled;
3. exact UTC settlement timestamp maps unambiguously to the symbol;
4. settlement timestamp lies in the frozen source calendar;
5. daily Data Vision sidecars exist for markPriceKlines, indexPriceKlines and metrics around the settlement day;
6. event is not superseded by a later official Binance notice.

Multiple symbols in one article are separate contract observations but share article-cluster identity.

### Source gate
SOURCE_PASS requires ALL:
- >=12 exact contract observations;
- >=10 distinct article clusters;
- 100% mark/index/metrics sidecar coverage for included observations;
- canonical article provenance resolved;
- zero 2026 market value opened.

If exact observations <12 or clusters <10 after complete enumeration:
INSUFFICIENT_SAMPLE_2026.

If official enumeration/provenance/sidecar capability cannot be defended:
SOURCE_BLOCKED.

### If source gate passes
Commit a separate immutable V0.3 PRE-OUTCOME REPLICATION FREEZE before opening any 2026 market value.

That freeze must copy V0.2/V0.2.1 exactly:
- T-60m to T-1m event window;
- matched control one day earlier;
- mark/index premium definition;
- signed convergence;
- OI T-60m to near T-5m;
- same +15/+10 bps convergence gates;
- same 65% hit-rate gate;
- same 20% event OI decay gate;
- same +10pp excess OI gate;
- same leave-one-out and concentration gates;
- same >=10 cluster gate.

### Governance
Research only.
No main merge.
No trading/orders/accounts/wallets/private endpoints/exchange mutation.
No post-outcome tuning.
