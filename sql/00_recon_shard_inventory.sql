-- 00_recon_shard_inventory.sql
-- Recon checklist item 1 (shard range), and the per-shard size input to item 12.
--
-- ARCHITECTURE.md §10.1: "Shard inventory comes from table metadata, not from
-- scanning rows -- item 1 costs no query bytes and must not be answered with a
-- row scan." __TABLES__ is dataset metadata, so this query reads no event row
-- and is expected to estimate and bill zero bytes.
--
-- Artefact: min and max suffix, total shard count, the list of missing dates
-- between them, and per-shard row counts and sizes. Tables that are not
-- events_YYYYMMDD (intraday or anything else) are reported separately rather
-- than folded into the range.
--
-- Output columns: row_kind, key, value_num, value_text, note

WITH all_tables AS (
  SELECT
    table_id,
    row_count,
    size_bytes,
    REGEXP_EXTRACT(table_id, r'^events_([0-9]{8})$') AS suffix
  FROM `firebase-public-project.analytics_153293282.__TABLES__`
),
dated_shards AS (
  SELECT
    suffix,
    PARSE_DATE('%Y%m%d', suffix) AS shard_date,
    row_count,
    size_bytes
  FROM all_tables
  WHERE suffix IS NOT NULL
),
bounds AS (
  SELECT
    MIN(shard_date) AS min_date,
    MAX(shard_date) AS max_date,
    COUNT(*)        AS shard_count,
    SUM(row_count)  AS total_rows,
    SUM(size_bytes) AS total_size_bytes
  FROM dated_shards
),
calendar AS (
  SELECT day
  FROM bounds, UNNEST(GENERATE_DATE_ARRAY(min_date, max_date)) AS day
),
missing AS (
  SELECT c.day
  FROM calendar c
  LEFT JOIN dated_shards d ON d.shard_date = c.day
  WHERE d.suffix IS NULL
)

SELECT 'summary' AS row_kind, 'min_shard_suffix' AS key,
       NULL AS value_num, FORMAT_DATE('%Y%m%d', min_date) AS value_text,
       FORMAT_DATE('%A', min_date) AS note
FROM bounds
UNION ALL
SELECT 'summary', 'max_shard_suffix', NULL, FORMAT_DATE('%Y%m%d', max_date),
       FORMAT_DATE('%A', max_date)
FROM bounds
UNION ALL
SELECT 'summary', 'shard_count', shard_count, NULL,
       'tables matching events_YYYYMMDD'
FROM bounds
UNION ALL
SELECT 'summary', 'calendar_days_in_range', DATE_DIFF(max_date, min_date, DAY) + 1, NULL,
       'inclusive span between min and max suffix'
FROM bounds
UNION ALL
SELECT 'summary', 'missing_dates_in_range', (SELECT COUNT(*) FROM missing), NULL,
       'calendar days in range with no events_YYYYMMDD table'
FROM bounds
UNION ALL
SELECT 'summary', 'span_days_modulo_7', MOD(DATE_DIFF(max_date, min_date, DAY) + 1, 7), NULL,
       'zero means the inclusive span is a whole number of 7-day blocks'
FROM bounds
UNION ALL
SELECT 'summary', 'total_event_rows', total_rows, NULL,
       'summed from table metadata, not from a row scan'
FROM bounds
UNION ALL
SELECT 'summary', 'total_size_bytes', total_size_bytes, NULL,
       'summed from table metadata; logical bytes across all events_YYYYMMDD shards'
FROM bounds
UNION ALL
SELECT 'non_event_table', table_id, row_count, NULL,
       CONCAT('size_bytes=', CAST(size_bytes AS STRING))
FROM all_tables
WHERE suffix IS NULL
UNION ALL
SELECT 'missing_date', FORMAT_DATE('%Y%m%d', day), NULL, NULL,
       FORMAT_DATE('%A', day)
FROM missing
UNION ALL
SELECT 'shard', suffix, row_count, CAST(size_bytes AS STRING),
       FORMAT_DATE('%A', shard_date)
FROM dated_shards
ORDER BY row_kind, key
