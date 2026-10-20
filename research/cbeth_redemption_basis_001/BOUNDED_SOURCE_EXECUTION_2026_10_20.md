# Bounded necessary-source execution — frozen before RPC observations

Parent: PR #128, commit 41909a1ac0f86166e7fac4a3deb9f9c9a120b35d.
This is a source transport gate, NOT a new trading family or a change to the
September 27 scientific protocol. No historical price/outcome is requested.

Execute one necessary condition first: canonical Ethereum block 16,000,000
and cbETH exchangeRate() at that exact block hash with requireCanonical=true.
Validate block number/hash/timestamp and a positive 32-byte uint256 response.
Original public transports: PublicNode headers, Blockmachine state.
If blocked, one independent free route: PublicNode for both header and state.
Two routes, one attempt per request, 12-second timeout, at most four requests
per host. One local host plus one GitHub Ubuntu host maximum (eight total).
The second host separates local transport restrictions from source availability.
Record raw response bytes, SHA256, request, UTC arrival and failures.
No credentials, no accounts, no transactions, no wallet methods.

Both necessary-condition routes fail => SOURCE_BLOCKED for these transports
on this host/time. This is not global source impossibility, economic NO_EDGE,
nor a judgement on the unexecuted full parent protocol. Stop bot engineering.
One route passes => NECESSARY_ANCHOR_PASS_ONLY; this is not full SOURCE_PASS.
Then execute the existing full source gate separately, with a disclosed bounded
transport adapter only if needed. Do not execute continuation/census/outcomes.

No change to sentinels, pools, fee tiers, clock, sample, threshold or outcomes.
Existing scientific costs are not selected or reduced here: parent source test
has no trading construction. Without full source AND verified redemption access,
net economic ceiling is unidentifiable; report it as unmeasured, never zero.
No 2026 historical holdout, basis, convergence or returns are read.

Prioritization: existing unexecuted cbETH source gate preferred over a new
family. Proposed concession payer is a seller needing liquidity; existence of
a discount, access to redemption and net surplus remain unproved.

Official accessibility sources reviewed before RPC:
- https://help.coinbase.com/en/coinbase/coinbase-staking/staking/wrap-unwrap-staked-eth
- https://www.coinbase.com/cbeth
- https://blockmachine.io/docs/ethereum-rpc
- https://ethereum.publicnode.com/

Coinbase wrapping/unwrapping depends on region/account eligibility; unwrapping
returns the underlying staked asset. Public conversion rate is not an enforceable
instant public cash-redemption quote. No account eligibility inferred.
