-- 01_recon_column_inventory.sql
-- Supporting evidence for recon items 3, 6, 9 and 13: which columns and nested
-- field paths actually exist on this table, and whether the schema is stable
-- across shards.
--
-- INFORMATION_SCHEMA.COLUMN_FIELD_PATHS is dataset metadata, so this query
-- reads no event row and is expected to estimate and bill zero bytes. It runs
-- before every billed query in the pass, so that no query names a column whose
-- existence has not first been established (§10.1: a query that reads a column
-- no item asks about is a defect -- establishing what exists is how that rule
-- is kept).
--
-- A field_path present on some shards but not others is itself a finding: it
-- means the export schema changed inside the window.
--
-- Output columns: field_path, data_type, shards_with_path, first_shard, last_shard

SELECT
  field_path,
  data_type,
  COUNT(DISTINCT table_name) AS shards_with_path,
  MIN(table_name)            AS first_shard,
  MAX(table_name)            AS last_shard
FROM `firebase-public-project.analytics_153293282.INFORMATION_SCHEMA.COLUMN_FIELD_PATHS`
WHERE REGEXP_CONTAINS(table_name, r'^events_[0-9]{8}$')
GROUP BY field_path, data_type
ORDER BY field_path
