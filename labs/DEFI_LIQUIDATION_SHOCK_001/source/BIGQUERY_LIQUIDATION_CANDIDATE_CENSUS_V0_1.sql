-- DEFI-LIQUIDATION-SHOCK-001
-- BIGQUERY LIQUIDATION CANDIDATE CENSUS V0.1
-- READ-ONLY / SOURCE-ONLY / OUTCOME-BLIND
--
-- IMPORTANT:
--   This produces CANDIDATES only. A discriminator match is not historical
--   authority until the relevant historical program/IDL version is pinned and
--   the transaction is reconciled against raw archival RPC evidence.
--
-- No prices, returns, PnL, direction, future labels, or market outcomes are read.
-- Frozen source window: [2021-01-01T00:00:00Z, 2025-01-01T00:00:00Z)
--
-- `data` in the public Instructions table is Base58 for raw/unparsed instructions.
-- This temporary JavaScript UDF decodes only enough bytes to identify the
-- pre-registered instruction prefix. It avoids BigInt and performs byte-array
-- base conversion so it is portable inside BigQuery JavaScript UDFs.

CREATE TEMP FUNCTION b58_prefix_hex(input STRING, take_bytes INT64)
RETURNS STRING
LANGUAGE js AS r"""
  if (input === null || input === undefined || input.length === 0) return null;
  var alphabet = '123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz';
  var map = {};
  for (var i = 0; i < alphabet.length; i++) map[alphabet[i]] = i;

  // little-endian base-256 digits
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

  // For non-empty strings whose numeric value is zero, the conversion seed can
  // add one synthetic zero. Keep only the zeros represented by Base58 leading 1s.
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
  -- Save / Solend native enum tags. Historical applicability still must be pinned.
  SELECT 'save_solend' AS protocol, 'lending' AS family,
         'So1endDq2YkqhipRh3WViPa8hdiSpxWy6z3Z6tMCpAo' AS program_id,
         'LiquidateObligation' AS match_name, '0c' AS prefix_hex,
         'native_u8_tag' AS encoding, 'REFERENCE_ONLY' AS authority UNION ALL
  SELECT 'save_solend', 'lending', 'So1endDq2YkqhipRh3WViPa8hdiSpxWy6z3Z6tMCpAo',
         'LiquidateObligationAndRedeemReserveCollateral', '11',
         'native_u8_tag', 'REFERENCE_ONLY' UNION ALL

  -- marginfi v2 current/known Anchor discriminator.
  SELECT 'marginfi_v2', 'lending', 'MFv2hWf31Z9kbCa1snEPYctwafyhdvnV7FZnsebVacA',
         'lending_account_liquidate', 'd6a997d5fba756db',
         'anchor_discriminator_8', 'REFERENCE_ONLY' UNION ALL

  -- Kamino Lend current/known Anchor discriminator.
  SELECT 'kamino_lend', 'lending', 'KLend2g3cP87fffoy8q1mQqGKjrxjC8boSyAYavgmjD',
         'liquidateObligationAndRedeemReserveCollateral', 'b1479acce2854a37',
         'anchor_discriminator_8', 'REFERENCE_ONLY' UNION ALL

  -- Drift V2 liquidation family. These names/discriminators are reference-only
  -- until historical version mapping proves existence/completeness by interval.
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
  WHERE i.block_timestamp >= TIMESTAMP('2021-01-01T00:00:00Z')
    AND i.block_timestamp <  TIMESTAMP('2025-01-01T00:00:00Z')
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
  'CANDIDATE_REQUIRES_HISTORICAL_VERSION_AND_RAW_RPC_VALIDATION' AS classification
FROM candidates
ORDER BY block_timestamp, block_slot, tx_signature, parent_index, instruction_index;
