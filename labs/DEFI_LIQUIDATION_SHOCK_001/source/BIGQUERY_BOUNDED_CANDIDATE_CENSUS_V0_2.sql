-- DEFI-LIQUIDATION-SHOCK-001
-- BIGQUERY BOUNDED CANDIDATE CENSUS V0.2
-- READ-ONLY / SOURCE-ONLY / OUTCOME-BLIND / FAIL-CLOSED
--
-- PURPOSE
--   Enumerate liquidation-reference candidates for exactly ONE protocol and ONE
--   bounded time chunk, while reconciling transaction execution state from the
--   public Transactions table BEFORE any Helius archival verification.
--
-- IMPORTANT
--   - This is a SOURCE CENSUS only. It reads no prices, returns, PnL, direction,
--     future labels or market outcomes.
--   - Successful execution does NOT by itself grant historical decoder authority.
--   - Failed transactions are retained as liquidation attempts and MUST NOT be
--     counted as realized forced-flow events.
--   - V0.1 `err IS NULL` semantics are retired. The frozen canonical execution
--     predicate is `status = 'Success'`, with status/err consistency checked.
--   - Run a BigQuery dry run / estimate before every instantiated chunk.
--   - Operational hard stop: DO NOT RUN if estimated bytes > 100 GB.
--
-- DEFAULT TEMPLATE CHUNK
--   The defaults below are deliberately only ONE UTC day for Drift. Change only
--   protocol/date bounds as authorized by BOUNDED_CENSUS_PLAN_V0.1.md.

DECLARE chunk_start TIMESTAMP DEFAULT TIMESTAMP('2024-12-15T00:00:00Z');
DECLARE chunk_end   TIMESTAMP DEFAULT TIMESTAMP('2024-12-16T00:00:00Z');
DECLARE target_program_id STRING DEFAULT 'dRiftyHA39MWEi3m9aunc5MzRF1JYuBsbn6VPcn33UH';

ASSERT chunk_start >= TIMESTAMP('2021-01-01T00:00:00Z')
  AS 'chunk_start precedes frozen source window';
ASSERT chunk_end <= TIMESTAMP('2025-01-01T00:00:00Z')
  AS 'chunk_end exceeds frozen source window';
ASSERT chunk_end > chunk_start
  AS 'chunk_end must be after chunk_start';
ASSERT TIMESTAMP_DIFF(chunk_end, chunk_start, HOUR) <= 168
  AS 'bounded census chunk may not exceed 7 days';
ASSERT target_program_id IN (
  'So1endDq2YkqhipRh3WViPa8hdiSpxWy6z3Z6tMCpAo',
  'MFv2hWf31Z9kbCa1snEPYctwafyhdvnV7FZnsebVacA',
  'KLend2g3cP87fffoy8q1mQqGKjrxjC8boSyAYavgmjD',
  'dRiftyHA39MWEi3m9aunc5MzRF1JYuBsbn6VPcn33UH'
) AS 'target_program_id is outside the frozen protocol registry';

CREATE TEMP FUNCTION b58_prefix_hex(input STRING, take_bytes INT64)
RETURNS STRING
LANGUAGE js AS r"""
  if (input === null || input === undefined || input.length === 0) return null;
  var alphabet = '123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz';
  var map = {};
  for (var i = 0; i < alphabet.length; i++) map[alphabet[i]] = i;

  var bytes = [0];
  for (var pos = 0; pos < input.length; pos++) {
    var ch = input[pos];
    var value = map[ch];
    if (value === undefined) return null;
    var carry = value;
    for (var j = 0; j < bytes.length; j++) {
      var x = bytes[j] * 58 + carry;
      bytes[j] = x & 255;
      carry = Math.floor(x / 256);
    }
    while (carry > 0) {
      bytes.push(carry & 255);
      carry = Math.floor(carry / 256);
    }
  }

  var leading = 0;
  while (leading < input.length && input[leading] === '1') leading++;
  var decoded = [];
  for (var z = 0; z < leading; z++) decoded.push(0);
  for (var k = bytes.length - 1; k >= 0; k--) decoded.push(bytes[k]);

  if (leading === input.length) decoded = decoded.slice(0, leading);
  else if (decoded.length > leading && decoded[leading] === 0 && bytes.length === 1 && bytes[0] === 0) {
    decoded.splice(leading, 1);
  }

  var n = Math.min(Number(take_bytes), decoded.length);
  var out = '';
  for (var q = 0; q < n; q++) {
    var h = decoded[q].toString(16);
    if (h.length < 2) h = '0' + h;
    out += h;
  }
  return out;
""";

WITH reference_encodings AS (
  SELECT 'save_solend' AS protocol, 'lending' AS family,
         'So1endDq2YkqhipRh3WViPa8hdiSpxWy6z3Z6tMCpAo' AS program_id,
         'LiquidateObligation' AS match_name, '0c' AS prefix_hex,
         'native_u8_tag' AS encoding, 'REFERENCE_ONLY' AS authority UNION ALL
  SELECT 'save_solend', 'lending', 'So1endDq2YkqhipRh3WViPa8hdiSpxWy6z3Z6tMCpAo',
         'LiquidateObligationAndRedeemReserveCollateral', '11',
         'native_u8_tag', 'REFERENCE_ONLY' UNION ALL
  SELECT 'marginfi_v2', 'lending', 'MFv2hWf31Z9kbCa1snEPYctwafyhdvnV7FZnsebVacA',
         'lending_account_liquidate', 'd6a997d5fba756db',
         'anchor_discriminator_8', 'REFERENCE_ONLY' UNION ALL
  SELECT 'kamino_lend', 'lending', 'KLend2g3cP87fffoy8q1mQqGKjrxjC8boSyAYavgmjD',
         'liquidateObligationAndRedeemReserveCollateral', 'b1479acce2854a37',
         'anchor_discriminator_8', 'REFERENCE_ONLY' UNION ALL
  SELECT 'drift_v2', 'perps_spot_margin', 'dRiftyHA39MWEi3m9aunc5MzRF1JYuBsbn6VPcn33UH',
         'liquidate_perp', '4b2377f7bf128b02', 'anchor_discriminator_8', 'REFERENCE_ONLY' UNION ALL
  SELECT 'drift_v2', 'perps_spot_margin', 'dRiftyHA39MWEi3m9aunc5MzRF1JYuBsbn6VPcn33UH',
         'liquidate_spot', '6b00802923e5fb12', 'anchor_discriminator_8', 'REFERENCE_ONLY' UNION ALL
  SELECT 'drift_v2', 'perps_spot_margin', 'dRiftyHA39MWEi3m9aunc5MzRF1JYuBsbn6VPcn33UH',
         'liquidate_borrow_for_perp_pnl', 'a911205acf94d11b', 'anchor_discriminator_8', 'REFERENCE_ONLY' UNION ALL
  SELECT 'drift_v2', 'perps_spot_margin', 'dRiftyHA39MWEi3m9aunc5MzRF1JYuBsbn6VPcn33UH',
         'liquidate_perp_pnl_for_deposit', 'ed4bc6ebe9ba4b23', 'anchor_discriminator_8', 'REFERENCE_ONLY' UNION ALL
  SELECT 'drift_v2', 'perps_spot_margin', 'dRiftyHA39MWEi3m9aunc5MzRF1JYuBsbn6VPcn33UH',
         'liquidate_spot_with_swap_begin', '0c2bb0539cfb750d', 'anchor_discriminator_8', 'REFERENCE_ONLY' UNION ALL
  SELECT 'drift_v2', 'perps_spot_margin', 'dRiftyHA39MWEi3m9aunc5MzRF1JYuBsbn6VPcn33UH',
         'liquidate_spot_with_swap_end', '8e58a3a0df4b37e1', 'anchor_discriminator_8', 'REFERENCE_ONLY'
),
refs AS (
  SELECT *
  FROM reference_encodings
  WHERE program_id = target_program_id
),
tx_state AS (
  SELECT
    block_slot,
    block_timestamp,
    signature,
    status,
    err,
    CASE
      WHEN status = 'Success' AND COALESCE(err, '') = '' THEN 'SUCCESS_CONSISTENT'
      WHEN status = 'Fail' AND COALESCE(err, '') != '' THEN 'FAIL_CONSISTENT'
      ELSE 'STATUS_ERR_INCONSISTENT'
    END AS status_err_consistency
  FROM `bigquery-public-data.crypto_solana_mainnet_us.Transactions`
  WHERE block_timestamp >= chunk_start
    AND block_timestamp < chunk_end
),
source_rows AS (
  SELECT
    i.block_slot,
    i.block_timestamp,
    i.tx_signature,
    i.index AS instruction_index,
    i.parent_index,
    i.program_id,
    i.data,
    i.instruction_type,
    t.status,
    t.err,
    t.status_err_consistency
  FROM `bigquery-public-data.crypto_solana_mainnet_us.Instructions` AS i
  JOIN tx_state AS t
    ON t.signature = i.tx_signature
   AND t.block_slot = i.block_slot
  WHERE i.block_timestamp >= chunk_start
    AND i.block_timestamp < chunk_end
    AND i.program_id = target_program_id
    AND i.data IS NOT NULL
),
decoded AS (
  SELECT
    s.*,
    b58_prefix_hex(s.data, 8) AS data_prefix_8_hex
  FROM source_rows AS s
),
candidates AS (
  SELECT
    r.protocol,
    r.family,
    d.program_id,
    r.match_name,
    r.encoding,
    r.prefix_hex AS reference_prefix_hex,
    r.authority,
    d.block_slot,
    d.block_timestamp,
    d.tx_signature,
    d.instruction_index,
    d.parent_index,
    d.instruction_type,
    d.data,
    d.data_prefix_8_hex,
    d.status,
    d.err,
    d.status_err_consistency
  FROM decoded AS d
  JOIN refs AS r
    ON STARTS_WITH(d.data_prefix_8_hex, r.prefix_hex)
)
SELECT
  protocol,
  family,
  program_id,
  match_name,
  encoding,
  reference_prefix_hex,
  authority,
  block_slot,
  block_timestamp,
  tx_signature,
  instruction_index,
  parent_index,
  CASE WHEN parent_index IS NULL THEN 'outer' ELSE 'inner' END AS instruction_location,
  instruction_type,
  data,
  data_prefix_8_hex,
  status,
  err,
  status_err_consistency,
  CASE
    WHEN status_err_consistency = 'STATUS_ERR_INCONSISTENT'
      THEN 'SOURCE_ANOMALY_FAIL_CLOSED'
    WHEN status = 'Fail'
      THEN 'LIQUIDATION_ATTEMPT_FAILED_NOT_REALIZED'
    WHEN status = 'Success'
      THEN 'SUCCESSFUL_REFERENCE_CANDIDATE_PENDING_HISTORICAL_AUTHORITY_AND_RAW_CLASS_VALIDATION'
    ELSE 'SOURCE_ANOMALY_FAIL_CLOSED'
  END AS classification
FROM candidates
ORDER BY block_timestamp, block_slot, tx_signature, parent_index, instruction_index;
