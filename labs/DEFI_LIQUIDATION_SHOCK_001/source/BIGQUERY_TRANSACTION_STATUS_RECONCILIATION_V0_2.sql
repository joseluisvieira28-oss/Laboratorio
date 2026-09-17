-- DEFI-LIQUIDATION-SHOCK-001
-- BIGQUERY TRANSACTION STATUS RECONCILIATION V0.2
-- READ-ONLY / SOURCE-ONLY / OUTCOME-BLIND
--
-- Technical correction to V0.1:
-- the public Transactions.err field uses an empty string for successful rows
-- in the frozen 23-signature sample, so `err IS NULL` is NOT a valid success
-- predicate. `status = 'Success'` is the canonical execution-state predicate.
--
-- No prices, returns, PnL, direction, trading or protected outcomes are read.

SELECT
  block_slot,
  block_timestamp,
  signature,
  status,
  err,
  (status = 'Success') AS inferred_success_from_status,
  (COALESCE(err, '') = '') AS err_is_empty_or_null,
  CASE
    WHEN status = 'Success' AND COALESCE(err, '') = '' THEN 'SUCCESS_CONSISTENT'
    WHEN status = 'Fail'    AND COALESCE(err, '') != '' THEN 'FAIL_CONSISTENT'
    ELSE 'STATUS_ERR_INCONSISTENT'
  END AS status_err_consistency
FROM `bigquery-public-data.crypto_solana_mainnet_us.Transactions`
WHERE block_timestamp >= TIMESTAMP('2024-12-15T00:00:00Z')
  AND block_timestamp <  TIMESTAMP('2024-12-16T00:00:00Z')
  AND signature IN (
    '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'
  )
ORDER BY signature;
