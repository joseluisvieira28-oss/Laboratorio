-- DEFI-LIQUIDATION-SHOCK-001
-- KAMINO CORRECTED CANDIDATE SMOKE TEST V0.2
-- SOURCE-ONLY / OUTCOME-BLIND / READ-ONLY / VERIFIER-COMPATIBLE
--
-- Purpose:
--   Re-run the 2024-12-15 Kamino candidate smoke test after the V0.1
--   discriminator transcription error, and emit the exact generic columns
--   required by verify_bigquery_candidates_v0_1.py.
--
-- Correct discriminator: b1479abce2854a37
-- Retired wrong value:  b1479acce2854a37
--
-- DRY RUN FIRST. HARD STOP if estimated bytes >100 GB.

CREATE TEMP FUNCTION b58_prefix_hex(input STRING, take_bytes INT64)
RETURNS STRING
LANGUAGE js AS r"""
  if (input === null || input === undefined || input.length === 0) return null;
  var alphabet='123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz';
  var map={}; for(var i=0;i<alphabet.length;i++) map[alphabet[i]]=i;
  var bytes=[0];
  for(var pos=0;pos<input.length;pos++){
    var value=map[input[pos]]; if(value===undefined) return null;
    var carry=value;
    for(var j=0;j<bytes.length;j++){
      var x=bytes[j]*58+carry; bytes[j]=x&255; carry=Math.floor(x/256);
    }
    while(carry>0){bytes.push(carry&255);carry=Math.floor(carry/256);}
  }
  var leading=0; while(leading<input.length && input[leading]==='1') leading++;
  var decoded=[]; for(var z=0;z<leading;z++) decoded.push(0);
  for(var k=bytes.length-1;k>=0;k--) decoded.push(bytes[k]);
  if(leading===input.length) decoded=decoded.slice(0,leading);
  else if(decoded.length>leading && decoded[leading]===0 && bytes.length===1 && bytes[0]===0) decoded.splice(leading,1);
  var n=Math.min(Number(take_bytes),decoded.length),out='';
  for(var q=0;q<n;q++){var h=decoded[q].toString(16);if(h.length<2)h='0'+h;out+=h;}
  return out;
""";

WITH tx AS (
  SELECT block_slot,signature,status,err
  FROM `bigquery-public-data.crypto_solana_mainnet_us.Transactions`
  WHERE block_timestamp >= TIMESTAMP('2024-12-15T00:00:00Z')
    AND block_timestamp <  TIMESTAMP('2024-12-16T00:00:00Z')
),
ix AS (
  SELECT i.block_slot,i.block_timestamp,i.tx_signature,
         i.index AS instruction_index,i.parent_index,i.instruction_type,i.data,
         b58_prefix_hex(i.data,8) AS data_prefix_8_hex
  FROM `bigquery-public-data.crypto_solana_mainnet_us.Instructions` i
  WHERE i.block_timestamp >= TIMESTAMP('2024-12-15T00:00:00Z')
    AND i.block_timestamp <  TIMESTAMP('2024-12-16T00:00:00Z')
    AND i.program_id='KLend2g3cP87fffoy8q1mQqGKjrxjC8boSyAYavgmjD'
    AND i.data IS NOT NULL
)
SELECT
  'kamino_lend' AS protocol,
  'KLend2g3cP87fffoy8q1mQqGKjrxjC8boSyAYavgmjD' AS program_id,
  'liquidate_obligation_and_redeem_reserve_collateral' AS match_name,
  'b1479abce2854a37' AS reference_prefix_hex,
  TIMESTAMP('2023-11-17T13:25:35Z') AS source_supported_from,
  ix.block_slot,
  ix.block_timestamp,
  ix.tx_signature,
  ix.instruction_index,
  ix.parent_index,
  CASE WHEN ix.parent_index IS NULL THEN 'outer' ELSE 'inner' END AS instruction_location,
  ix.instruction_type,
  ix.data,
  ix.data_prefix_8_hex,
  tx.status,
  tx.err,
  CASE
    WHEN ix.block_timestamp < TIMESTAMP('2023-11-17T13:25:35Z')
      THEN 'PRE_SOURCE_AUTHORITY_BOUNDARY_FAIL_CLOSED'
    WHEN tx.status='Success' AND COALESCE(tx.err,'')=''
      THEN 'SUCCESSFUL_REFERENCE_CANDIDATE_REQUIRES_RAW_VALIDATION'
    WHEN tx.status='Fail' AND COALESCE(tx.err,'')!=''
      THEN 'LIQUIDATION_ATTEMPT_FAILED_NOT_REALIZED'
    ELSE 'SOURCE_ANOMALY_FAIL_CLOSED'
  END AS classification
FROM ix
JOIN tx ON tx.signature=ix.tx_signature AND tx.block_slot=ix.block_slot
WHERE ix.data_prefix_8_hex='b1479abce2854a37'
ORDER BY ix.block_timestamp,ix.block_slot,ix.tx_signature,ix.parent_index,ix.instruction_index;
