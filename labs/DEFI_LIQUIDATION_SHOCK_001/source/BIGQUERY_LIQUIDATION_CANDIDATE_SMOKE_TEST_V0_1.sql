-- DEFI-LIQUIDATION-SHOCK-001
-- BIGQUERY LIQUIDATION CANDIDATE SMOKE TEST V0.1
-- READ-ONLY / SOURCE-ONLY / OUTCOME-BLIND
--
-- Purpose:
--   Validate the pre-registered candidate discriminator extraction on one bounded
--   historical day before any wider census/backfill.
--
-- Window: [2024-12-15T00:00:00Z, 2024-12-16T00:00:00Z)
--
-- IMPORTANT:
--   Matches are CANDIDATES only. They are not historically authoritative
--   liquidation events until version/IDL applicability and raw archival RPC
--   reconciliation are completed.
--
-- No prices, returns, PnL, direction, future labels, or market outcomes are read.

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
      carry = Math.floor(carry / 256);
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
program_ids AS (
  SELECT DISTINCT program_id FROM reference_encodings
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
  JOIN program_ids AS p USING (program_id)
  WHERE i.block_timestamp >= TIMESTAMP('2024-12-15T00:00:00Z')
    AND i.block_timestamp <  TIMESTAMP('2024-12-16T00:00:00Z')
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
    s.data_prefix_8_hex
  FROM source_rows AS s
  JOIN reference_encodings AS r
    ON s.program_id = r.program_id
   AND STARTS_WITH(s.data_prefix_8_hex, r.prefix_hex)
)
SELECT
  protocol,
  match_name,
  COUNT(*) AS candidate_instruction_rows,
  COUNT(DISTINCT tx_signature) AS candidate_transactions,
  COUNTIF(parent_index IS NULL) AS candidate_outer_rows,
  COUNTIF(parent_index IS NOT NULL) AS candidate_inner_cpi_rows,
  MIN(block_timestamp) AS first_candidate_utc,
  MAX(block_timestamp) AS last_candidate_utc,
  'CANDIDATE_REQUIRES_HISTORICAL_VERSION_AND_RAW_RPC_VALIDATION' AS classification
FROM candidates
GROUP BY protocol, match_name
ORDER BY protocol, match_name;
