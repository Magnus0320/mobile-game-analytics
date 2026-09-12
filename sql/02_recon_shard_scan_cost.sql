-- 02_recon_shard_scan_cost.sql
-- Recon checklist item 12: the per-day unit cost, as a BILLED figure.
--
-- Item 12's artefact requires "a billed-bytes figure for a full-column scan of
-- one shard as the per-day unit cost", and §10.1 requires the cost model to be
-- built on actuals rather than estimates. A dry-run estimate is therefore not an
-- answer to this item; the query has to run.
--
-- On the tension with §10.1's column rule, resolved rather than glossed:
-- §10.1 says "a query that reads a column no item asks about is a defect", and a
-- full-column scan reads every column by construction. Item 12 names this query
-- specifically, so the specific instruction governs the general one. Recorded in
-- assumptions.md rather than decided silently.
--
-- Shard: events_20181003, the last in the range. Chosen because item 1's
-- metadata shows it carries the widest schema of the window (the export gained
-- columns partway through) and is among the largest shards, so it is the
-- conservative end of the unit cost rather than the flattering one.
--
-- TO_JSON_STRING over the whole row forces every column to be read, and the SUM
-- keeps the read from being optimised away. The returned figures are incidental;
-- the artefact this query produces is its billed-bytes number, which the runner
-- records in the ledger and the sidecar.
--
-- Pairing this billed figure against the same shard's size_bytes from query 00
-- calibrates metadata size against billed bytes, so the remaining 113 shards can
-- be projected from free metadata instead of being scanned.
--
-- Output columns: shard, rows_scanned, total_row_json_bytes

SELECT
  '20181003'                          AS shard,
  COUNT(*)                            AS rows_scanned,
  SUM(LENGTH(TO_JSON_STRING(t)))      AS total_row_json_bytes
FROM `firebase-public-project.analytics_153293282.events_20181003` AS t
