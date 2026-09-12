-- 03_recon_event_vocabulary.sql
-- Recon checklist items 10, 2 and 5, in one scan of two columns.
--
--   item 10  the complete distinct event_name list with event counts and
--            distinct-user counts, established empirically over the full range
--   item  2  distinct users overall, and distinct users with >= 1 first_open
--   item  5  per-shard event volumes, including first_open
--
-- The grand-total row is also the literal denominator ARCHITECTURE.md §10.3 and
-- A-084 fix for Part 2's scope rule: distinct user_pseudo_id values with at
-- least one event of any kind in the full shard range, users with no first_open
-- included, no trailing-window exclusion.
--
-- On item 5 and the word "day": this query groups by _TABLE_SUFFIX, which is the
-- export's own shard key. It is NOT a day boundary, and none is defined here or
-- anywhere else by this session -- §10.4 forbids it, and item 3 is what
-- establishes the facts that bear on one. Read these rows as per-shard volumes.
--
-- Shard range 20180612-20181003 is the range established by query 00 from table
-- metadata: 114 shards, contiguous, no missing dates.
--
-- Columns read: event_name, user_pseudo_id. _TABLE_SUFFIX is a pseudo column and
-- costs nothing.
--
-- Output columns: scope, shard_suffix, event_name, events, distinct_users

WITH scanned AS (
  SELECT
    _TABLE_SUFFIX AS shard_suffix,
    event_name,
    user_pseudo_id
  FROM `firebase-public-project.analytics_153293282.events_*`
  WHERE _TABLE_SUFFIX BETWEEN '20180612' AND '20181003'
),

-- The grouping and the labelling are separate stages: a SELECT alias that
-- repeats a grouped column's name shadows that column inside GROUP BY.
grouped AS (
  SELECT
    GROUPING(shard_suffix)         AS g_shard,
    GROUPING(event_name)           AS g_event,
    shard_suffix,
    event_name,
    COUNT(*)                       AS events,
    COUNT(DISTINCT user_pseudo_id) AS distinct_users
  FROM scanned
  GROUP BY GROUPING SETS ((shard_suffix, event_name), (event_name), ())
)

SELECT
  CASE
    WHEN g_shard = 0 THEN 'per_shard_per_event'
    WHEN g_event = 0 THEN 'all_shards_per_event'
    ELSE 'all_shards_all_events'
  END                                  AS scope,
  IF(g_shard = 0, shard_suffix, NULL)  AS shard_suffix,
  IF(g_event = 0, event_name,   NULL)  AS event_name,
  events,
  distinct_users
FROM grouped
ORDER BY scope, events DESC, shard_suffix, event_name
