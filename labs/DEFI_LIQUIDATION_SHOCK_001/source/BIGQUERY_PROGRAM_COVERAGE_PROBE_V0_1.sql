-- DEFI-LIQUIDATION-SHOCK-001
-- BIGQUERY PROGRAM COVERAGE PROBE V0.1
-- READ-ONLY / SOURCE-ONLY / OUTCOME-BLIND
--
-- Purpose:
--   Verify that the public Solana BigQuery Instructions table contains historical
--   instruction rows for the frozen protocol program IDs during 2021-2024.
--
-- This query does NOT inspect prices, returns, PnL, market direction, or outcomes.
-- It reads only block_timestamp and program_id and returns source-coverage counts.
--
-- Dataset:
--   bigquery-public-data.crypto_solana_mainnet_us.Instructions
--
-- Frozen source window: [2021-01-01T00:00:00Z, 2025-01-01T00:00:00Z)

WITH protocol_registry AS (
  SELECT 'save_solend' AS protocol, 'So1endDq2YkqhipRh3WViPa8hdiSpxWy6z3Z6tMCpAo' AS program_id UNION ALL
  SELECT 'marginfi_v2', 'MFv2hWf31Z9kbCa1snEPYctwafyhdvnV7FZnsebVacA' UNION ALL
  SELECT 'kamino_lend', 'KLend2g3cP87fffoy8q1mQqGKjrxjC8boSyAYavgmjD' UNION ALL
  SELECT 'drift_v2', 'dRiftyHA39MWEi3m9aunc5MzRF1JYuBsbn6VPcn33UH'
),
coverage AS (
  SELECT
    p.protocol,
    i.program_id,
    COUNT(*) AS instruction_rows,
    COUNT(DISTINCT i.tx_signature) AS distinct_transactions,
    MIN(i.block_timestamp) AS first_instruction_utc,
    MAX(i.block_timestamp) AS last_instruction_utc,
    COUNTIF(i.parent_index IS NULL) AS outer_instruction_rows,
    COUNTIF(i.parent_index IS NOT NULL) AS inner_cpi_instruction_rows
  FROM `bigquery-public-data.crypto_solana_mainnet_us.Instructions` AS i
  JOIN protocol_registry AS p
    ON i.program_id = p.program_id
  WHERE i.block_timestamp >= TIMESTAMP('2021-01-01T00:00:00Z')
    AND i.block_timestamp <  TIMESTAMP('2025-01-01T00:00:00Z')
  GROUP BY p.protocol, i.program_id
)
SELECT
  p.protocol,
  p.program_id,
  COALESCE(c.instruction_rows, 0) AS instruction_rows,
  COALESCE(c.distinct_transactions, 0) AS distinct_transactions,
  c.first_instruction_utc,
  c.last_instruction_utc,
  COALESCE(c.outer_instruction_rows, 0) AS outer_instruction_rows,
  COALESCE(c.inner_cpi_instruction_rows, 0) AS inner_cpi_instruction_rows,
  'SOURCE_COVERAGE_ONLY_NOT_AN_EDGE_RESULT' AS classification
FROM protocol_registry AS p
LEFT JOIN coverage AS c USING (protocol, program_id)
ORDER BY protocol;
