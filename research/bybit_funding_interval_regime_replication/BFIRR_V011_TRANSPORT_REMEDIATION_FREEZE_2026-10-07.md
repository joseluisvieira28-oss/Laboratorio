# BFIRR V0.1.1 TRANSPORT REMEDIATION FREEZE
Date: 2026-10-07

Trigger:
- Initial source-gate run 37572356217 failed before enumeration with HTTP 403 from https://api.bybit.com.
- No premium-index outcome was opened.
- No fundingRate value was read or used.

Allowed technical remediation:
- Add official Bybit mainnet fallback host https://api.bytick.com.
- Retry the exact same public endpoints and exact same query semantics on the fallback host.
- Preserve event definition, calendar, thresholds, settlement-timestamp rules and verdict taxonomy unchanged.

Forbidden:
- no premium-index values;
- no fundingRate values;
- no event-rule changes;
- no threshold relaxation;
- no 2026;
- no main merge/trading/private endpoints.

The failed run 37572356217 remains preserved.
