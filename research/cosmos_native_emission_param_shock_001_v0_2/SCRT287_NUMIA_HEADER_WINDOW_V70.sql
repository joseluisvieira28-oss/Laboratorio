-- PREPARED ONLY: no query has been submitted and no login attempted.
-- GoogleSQL; public chain header metadata only. Do not use SELECT *.
-- Use BigQuery sandbox without billing. Inspect dry-run bytes first.
-- Keep maximum bytes billed bounded; do not enable billing or purchase credits.
-- This window is discovery. Determine H offline with integer nanoseconds from
-- header.time, never from the microsecond TIMESTAMP column. Preserve all rows,
-- duplicates, complete header JSON, and signatures; do not deduplicate silently.
-- Rows beyond H+1 support checking the next header's last_block_id.
SELECT
  block_height,
  block_timestamp,
  chain_id,
  validators_hash,
  TO_JSON_STRING(header) AS header_json,
  TO_JSON_STRING(signatures) AS signatures_json,
  JSON_VALUE(header, '$.time') AS header_time_exact,
  JSON_VALUE(header, '$.last_block_id.hash') AS previous_block_hash
FROM `numia-data.secret.secret_blocks`
WHERE block_timestamp >= TIMESTAMP('2023-12-07 02:54:30+00')
  AND block_timestamp < TIMESTAMP('2023-12-07 02:56:00+00')
  AND chain_id = 'secret-4'
ORDER BY block_height;
