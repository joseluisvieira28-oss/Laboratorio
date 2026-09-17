-- DEFI-LIQUIDATION-SHOCK-001
-- ANCHOR LIQUIDATION LOG LOCATOR V0.1
-- SOURCE-ONLY / OUTCOME-BLIND / NON-AUTHORITATIVE LOCATOR
--
-- Purpose:
--   Narrow historical date ranges cheaply before running Base58 UDF decoding.
--   This query uses Instructions.program_id to bind the transaction to one
--   frozen protocol and then searches transaction logs for Anchor instruction
--   names. It is a LOCATOR only; every located row still requires exact
--   discriminator-byte confirmation and, where required, archival RAW validation.
--
-- Applicable only to Anchor protocols/classes in this lab: Drift v2, marginfi v2,
-- Kamino Lend. Do NOT use it as authority for native Save/Solend tags.
--
-- Dry-run first. HARD STOP >100 GB.

DECLARE chunk_start TIMESTAMP DEFAULT TIMESTAMP('2024-12-01T00:00:00Z');
DECLARE chunk_end   TIMESTAMP DEFAULT TIMESTAMP('2025-01-01T00:00:00Z');
DECLARE target_program_id STRING DEFAULT 'KLend2g3cP87fffoy8q1mQqGKjrxjC8boSyAYavgmjD';

ASSERT chunk_start >= TIMESTAMP('2021-01-01T00:00:00Z') AS 'before frozen window';
ASSERT chunk_end <= TIMESTAMP('2025-01-01T00:00:00Z') AS 'after frozen window';
ASSERT chunk_end > chunk_start AS 'invalid bounds';
ASSERT TIMESTAMP_DIFF(chunk_end,chunk_start,DAY) <= 31 AS 'locator chunk may not exceed 31 days';
ASSERT target_program_id IN (
  'MFv2hWf31Z9kbCa1snEPYctwafyhdvnV7FZnsebVacA',
  'KLend2g3cP87fffoy8q1mQqGKjrxjC8boSyAYavgmjD',
  'dRiftyHA39MWEi3m9aunc5MzRF1JYuBsbn6VPcn33UH'
) AS 'locator limited to frozen Anchor protocols';

WITH program_txs AS (
  SELECT DISTINCT i.block_slot,i.block_timestamp,i.tx_signature
  FROM `bigquery-public-data.crypto_solana_mainnet_us.Instructions` i
  WHERE i.block_timestamp >= chunk_start
    AND i.block_timestamp < chunk_end
    AND i.program_id = target_program_id
),
tx AS (
  SELECT t.block_slot,t.block_timestamp,t.signature,t.status,t.err,t.log_messages
  FROM `bigquery-public-data.crypto_solana_mainnet_us.Transactions` t
  WHERE t.block_timestamp >= chunk_start
    AND t.block_timestamp < chunk_end
),
joined AS (
  SELECT p.block_slot,p.block_timestamp,p.tx_signature,t.status,t.err,t.log_messages
  FROM program_txs p
  JOIN tx t ON t.signature=p.tx_signature AND t.block_slot=p.block_slot
),
located AS (
  SELECT
    j.block_slot,j.block_timestamp,j.tx_signature,j.status,j.err,log_line,
    CASE
      WHEN target_program_id='MFv2hWf31Z9kbCa1snEPYctwafyhdvnV7FZnsebVacA'
           AND STRPOS(log_line,'Instruction: LendingAccountLiquidate')>0
        THEN 'lending_account_liquidate'
      WHEN target_program_id='KLend2g3cP87fffoy8q1mQqGKjrxjC8boSyAYavgmjD'
           AND STRPOS(log_line,'Instruction: LiquidateObligationAndRedeemReserveCollateral')>0
        THEN 'liquidate_obligation_and_redeem_reserve_collateral'
      WHEN target_program_id='dRiftyHA39MWEi3m9aunc5MzRF1JYuBsbn6VPcn33UH'
           AND STRPOS(log_line,'Instruction: LiquidatePerpPnlForDeposit')>0
        THEN 'liquidate_perp_pnl_for_deposit'
      WHEN target_program_id='dRiftyHA39MWEi3m9aunc5MzRF1JYuBsbn6VPcn33UH'
           AND STRPOS(log_line,'Instruction: LiquidateBorrowForPerpPnl')>0
        THEN 'liquidate_borrow_for_perp_pnl'
      WHEN target_program_id='dRiftyHA39MWEi3m9aunc5MzRF1JYuBsbn6VPcn33UH'
           AND STRPOS(log_line,'Instruction: LiquidateSpot')>0
        THEN 'liquidate_spot'
      WHEN target_program_id='dRiftyHA39MWEi3m9aunc5MzRF1JYuBsbn6VPcn33UH'
           AND STRPOS(log_line,'Instruction: LiquidatePerp')>0
        THEN 'liquidate_perp'
      ELSE NULL
    END AS located_class
  FROM joined j, UNNEST(j.log_messages) AS log_line
)
SELECT
  block_slot,block_timestamp,tx_signature,located_class,status,err,
  CASE
    WHEN status='Success' AND COALESCE(err,'')='' THEN 'LOCATED_SUCCESS_REQUIRES_BYTE_CONFIRMATION'
    WHEN status='Fail' AND COALESCE(err,'')!='' THEN 'LOCATED_FAILED_ATTEMPT_REQUIRES_BYTE_CONFIRMATION'
    ELSE 'SOURCE_ANOMALY_FAIL_CLOSED'
  END AS locator_classification
FROM located
WHERE located_class IS NOT NULL
ORDER BY block_timestamp,block_slot,tx_signature,located_class;
