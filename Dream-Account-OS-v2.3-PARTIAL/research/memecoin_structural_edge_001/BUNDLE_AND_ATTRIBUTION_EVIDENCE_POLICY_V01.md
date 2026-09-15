# MSEL-001 — BUNDLE & ATTRIBUTION EVIDENCE POLICY V0.1

Status: FROZEN PRE-OUTCOME  
Purpose: prevent strong labels from being assigned to weak historical evidence.

## 1. Bundle terminology

`bundle` is a high-confidence label. It may be used only when an explicit historical bundle identifier or equivalent primary evidence exists.

The following are NOT sufficient by themselves to label transactions as one Jito bundle:

- same slot;
- adjacent transaction positions;
- identical fee payer;
- identical compute-budget settings;
- a transfer to a known Jito tip account;
- similar transaction templates;
- same funder.

Jito bundle-status APIs are recent-history interfaces and are not treated as a complete historical bundle archive. Therefore the June 2025 pilot must not infer historical bundle membership from absent bundle-status records.

## 2. Allowed neutral historical proxies

Use mechanically descriptive names:

- `same_slot_cohort_share`
- `same_fee_payer_share`
- `same_funder_cluster_share`
- `jito_tip_detected_share`
- `near_adjacent_tx_position_share`
- `shared_tx_template_share`

These are structural proxies, not proof of common ownership or bundling.

## 3. Wallet linkage evidence ladder

### Tier A — direct / strong
- explicit transfer between wallets before snapshot;
- same wallet/account identity;
- explicit common authority/signature relation in transaction data;
- deterministic protocol-owned account relation.

### Tier B — strong but contextual
- direct funding from the same low-degree funder before snapshot;
- repeated coordinated participation already observed in prior launches only;
- same fee payer across multiple otherwise distinct wallets within the launch window.

### Tier C — weak / proxy
- same slot;
- same compute budget;
- same transaction template;
- shared high-degree service/CEX funder;
- temporal proximity alone.

Hard economic clustering must not be based only on Tier C evidence.

## 4. High-degree funder firewall

A common exchange, bridge, faucet, payment service, market-maker router or other high-degree funding hub may fund many unrelated wallets. Therefore:

- shared service funders do not automatically merge wallets;
- keep `shared_funder` and `shared_funder_degree` as separate features;
- mark known/likely service hubs where possible;
- creator-linked concentration must report both conservative and aggressive clustering sensitivity.

## 5. Point-in-time funding rule

For snapshot T, only transfers/funding events with chain timestamp/slot <= T are allowed.

Forbidden:

- later replenishments used to infer an earlier relation;
- later creator launches used to classify a wallet as related in an earlier launch;
- future cluster construction propagated backward.

## 6. Launch identity fields

Never collapse:

- `origin_creator`
- `tx_user`
- `fee_payer`
- `seed_buyer`
- `first_external_buyer`
- `curve_creator_at_snapshot`
- `fee_owner_at_snapshot`

If two roles share an address, record equality explicitly. Do not discard the role distinction.

## 7. Organic buyer definition — pilot

A buyer can count toward the strict organic-buyer metric only if, by the snapshot:

1. buyer is not a known protocol account;
2. buyer is not the bonding curve / pool / fee recipient;
3. buyer is not origin creator / tx user / seed buyer unless explicitly measuring creator demand;
4. no Tier-A evidence links buyer to creator cluster;
5. buyer's purchase is not merely an internal transfer masquerading as external acquisition.

Tier-B/Tier-C linkage does not automatically exclude a buyer; instead it creates sensitivity variants.

## 8. Organicity Ratio — preregistered family

Candidate family, NOT a validated edge:

`strict_external_net_inflow / gross_buy_sell_turnover`

Report alongside:

- raw turnover;
- unique external buyers;
- creator-cluster-adjusted turnover;
- same-funder-adjusted turnover;
- conservative / aggressive linkage sensitivity.

No single arbitrary wallet-clustering heuristic may define the final result.

## 9. Holder reconstruction

BUY/SELL events do not prove current holdings because direct SPL transfers can occur before T+5.

Required for concentration metrics:

- reconstruct all Pump buys/sells through snapshot;
- reconstruct target-mint token transfers through snapshot;
- follow transfer counterparties until the window is closed or explicitly mark unresolved transfer escape;
- reconcile aggregate token balances against known supply/curve holdings within deterministic tolerances.

If transfer closure fails materially, holder-concentration features are `UNAVAILABLE`, not imputed.

## 10. Metadata / copycat evidence

Safe point-in-time fields:

- on-chain create name;
- on-chain create symbol;
- on-chain URI string;
- immutable content identifiers such as IPFS CID where directly encoded.

Unsafe without archive proof:

- current HTTP image at a mutable URL;
- current website content;
- current social profile bio/followers;
- metadata fetched later from an overwriteable endpoint and treated as launch-time content.

Copycat corpus must contain only tokens whose create event preceded the current launch.

## 11. Negative controls

Every structural linkage family must be challenged with at least one control:

- activity-matched wallet placebo;
- same-slot placebo from unrelated launches;
- high-degree-funder placebo;
- creator-cluster permutation preserving cluster size;
- transaction-template placebo where common SDK routing is plausible.

If a proxy performs no better than its matched placebo, it is not promoted as causal or predictive evidence.
