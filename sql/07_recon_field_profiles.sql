-- 07_recon_field_profiles.sql
-- Recon checklist items 13 and 7.
--
--   item 13  this dataset is documented as obfuscated, with placeholder and null
--            values in some fields. Which of the fields Parts 1 and 2 would rely
--            on actually carry usable values? Per field: the null rate, the
--            distinct-value count, and the top values with their shares.
--   item  7  what platforms are present, and does the mobile-game framing hold?
--            The platform field is one of the fields at risk, which is why
--            item 13 feeds item 7 rather than the reverse.
--
-- §10.2 item 13 fixes the consequence in advance: a field whose distinct set is a
-- single value, or is dominated by one placeholder, or whose null rate exceeds
-- 50%, cannot support segmentation; such a segment is DROPPED, not reported.
-- This query establishes the profile. It does not decide any segmentation --
-- that is the architecture session's call under §10.4.
--
-- One scan only. The base table is exploded into (field, value) pairs and
-- aggregated once; the per-field summary and the top-50 values are both derived
-- from that already-aggregated result, so the event table is never read twice.
--
-- Query 01 established that all ten of these field paths exist on all 114 shards,
-- so none of the null counts below can be an absent column rather than an absent
-- value -- unlike event_value_in_usd, which query 05 had to guard.
--
-- Columns read: platform, geo.country, geo.region, device.category,
-- device.operating_system, device.language, traffic_source.name,
-- traffic_source.medium, traffic_source.source, app_info.version,
-- user_pseudo_id. Shard range 20180612-20181003.
--
-- Output columns: field, row_kind, value, events, users, event_share_ppm,
--                 value_rank, distinct_non_null_values, null_events,
--                 null_share_ppm

WITH base AS (
  SELECT
    user_pseudo_id,
    [STRUCT('platform'                 AS field, platform                 AS value),
     STRUCT('geo.country',                       geo.country),
     STRUCT('geo.region',                        geo.region),
     STRUCT('device.category',                   device.category),
     STRUCT('device.operating_system',           device.operating_system),
     STRUCT('device.language',                   device.language),
     STRUCT('traffic_source.name',               traffic_source.name),
     STRUCT('traffic_source.medium',             traffic_source.medium),
     STRUCT('traffic_source.source',             traffic_source.source),
     STRUCT('app_info.version',                  app_info.version)
    ] AS fields
  FROM `firebase-public-project.analytics_153293282.events_*`
  WHERE _TABLE_SUFFIX BETWEEN '20180612' AND '20181003'
),

by_value AS (
  SELECT
    f.field                        AS field,
    f.value                        AS value,
    COUNT(*)                       AS events,
    COUNT(DISTINCT user_pseudo_id) AS users
  FROM base, UNNEST(fields) AS f
  GROUP BY field, value
),

per_field AS (
  SELECT
    field,
    SUM(events)                                   AS total_events,
    COUNTIF(value IS NOT NULL)                    AS distinct_non_null_values,
    SUM(IF(value IS NULL, events, 0))             AS null_events
  FROM by_value
  GROUP BY field
),

ranked AS (
  SELECT
    v.field,
    v.value,
    v.events,
    v.users,
    CAST(ROUND(v.events * 1000000 / p.total_events) AS INT64) AS event_share_ppm,
    ROW_NUMBER() OVER (PARTITION BY v.field ORDER BY v.events DESC, v.value) AS value_rank
  FROM by_value v
  JOIN per_field p USING (field)
)

SELECT
  field,
  'summary'                                                    AS row_kind,
  CAST(NULL AS STRING)                                         AS value,
  total_events                                                 AS events,
  CAST(NULL AS INT64)                                          AS users,
  CAST(NULL AS INT64)                                          AS event_share_ppm,
  CAST(NULL AS INT64)                                          AS value_rank,
  distinct_non_null_values,
  null_events,
  CAST(ROUND(null_events * 1000000 / total_events) AS INT64)   AS null_share_ppm
FROM per_field

UNION ALL

SELECT
  field,
  'value'                                                      AS row_kind,
  value,
  events,
  users,
  event_share_ppm,
  value_rank,
  CAST(NULL AS INT64),
  CAST(NULL AS INT64),
  CAST(NULL AS INT64)
FROM ranked
WHERE value_rank <= 50

ORDER BY field, row_kind, value_rank
