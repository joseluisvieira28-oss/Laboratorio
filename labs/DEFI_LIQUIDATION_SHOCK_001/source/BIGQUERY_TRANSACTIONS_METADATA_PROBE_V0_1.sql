-- DEFI-LIQUIDATION-SHOCK-001
-- BIGQUERY TRANSACTIONS METADATA PROBE V0.1
-- READ-ONLY / SOURCE-ONLY / OUTCOME-BLIND
--
-- Purpose:
--   Inspect only BigQuery metadata for the public Solana Transactions table so
--   the lab can design a low-cost successful-transaction filter before the
--   historical liquidation census.
--
-- This query does NOT scan transaction rows and does NOT inspect prices, returns,
-- PnL, direction, future labels, or market outcomes.

SELECT
  column_name,
  data_type,
  is_partitioning_column,
  clustering_ordinal_position
FROM `bigquery-public-data.crypto_solana_mainnet_us.INFORMATION_SCHEMA.COLUMNS`
WHERE table_name = 'Transactions'
ORDER BY ordinal_position;
