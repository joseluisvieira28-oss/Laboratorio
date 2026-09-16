-- DEFI-LIQUIDATION-SHOCK-001
-- BIGQUERY RAW VALIDATION SAMPLE V0.1
-- READ-ONLY / SOURCE-ONLY / OUTCOME-BLIND
--
-- Purpose:
--   Produce a small deterministic sample of the already-registered 2024-12-15
--   liquidation-reference candidates for raw archival RPC reconciliation.
--
-- This is NOT a trading/outcome query. No prices, returns, PnL, direction or
-- future labels are read.
--
-- Sampling rule frozen before raw RPC inspection:
--   Within each protocol + match_name + outer/inner location group, select the
--   first 3 candidate instruction rows in canonical order:
--     block_slot, tx_signature, instruction_index, parent_index.
--   If a group has fewer than 3 rows, retain all available rows.
--
-- Window: [2024-12-15T00:00:00Z, 2024-12-16T00:00:00Z)

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
    b58_prefix_hex(i.data, 8) AS data_prefix_8_hex
  FROM `bigquery-public-data.crypto_solana_mainnet_us.Instructions` AS i
  WHERE i.block_timestamp >= TIMESTAMP('2024-12-15T00:00:00Z')
    AND i.block_timestamp <  TIMESTAMP('2024-12-16T00:00:00Z')
    AND i.program_id IN (
      'So1endDq2YkqhipRh3WViPa8hdiSpxWy6z3Z6tMCpAo',
      'MFv2hWf31Z9kbCa1snEPYctwafyhdvnV7FZnsebVacA',
      'KLend2g3cP87fffoy8q1mQqGKjrxjC8boSyAYavgmjD',
      'dRiftyHA39MWEi3m9aunc5MzRF1JYuBsbn6VPcn33UH'
    )
    AND i.data IS NOT NULL
),
candidates AS (
  SELECT
    r.protocol,
    r.family,
    s.program_id,
    r.match_name,
    r.encoding,
    r.prefix_hex AS reference_prefix_hex,
    r.authority,
    s.block_slot,
    s.block_timestamp,
    s.tx_signature,
    s.instruction_index,
    s.parent_index,
    s.instruction_type,
    s.data,
    s.data_prefix_8_hex,
    IF(s.parent_index IS NULL, 'outer', 'inner') AS instruction_location
  FROM source_rows AS s
  JOIN reference_encodings AS r
    ON s.program_id = r.program_id
   AND STARTS_WITH(s.data_prefix_8_hex, r.prefix_hex)
),
ranked AS (
  SELECT
    *,
    ROW_NUMBER() OVER (
      PARTITION BY protocol, match_name, instruction_location
      ORDER BY block_slot, tx_signature, instruction_index, parent_index
    ) AS sample_rank
  FROM candidates
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
  instruction_type,
  data,
  data_prefix_8_hex,
  instruction_location,
  sample_rank,
  'RAW_VALIDATION_SAMPLE_REQUIRES_RPC_RECONCILIATION' AS classification
FROM ranked
WHERE sample_rank <= 3
ORDER BY protocol, match_name, instruction_location, sample_rank;
