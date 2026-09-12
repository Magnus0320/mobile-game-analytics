-- 08_recon_event_repetition.sql
-- Recon checklist item 11: should funnel steps be counted per user or per
-- session? Artefact: for the progression events, events per user and events per
-- session, median and 90th percentile, plus whether a step repeats within a
-- single session.
--
-- Two departures from the item as written, both forced by what the pass found
-- rather than chosen here:
--
-- 1. PER SESSION IS NOT COMPUTABLE. Query 04 enumerated all 52 distinct
--    event_params keys over the full range and there is no ga_session_id among
--    them, nor any other session identifier. This export predates that field. No
--    per-session figure appears below because none can be produced, and
--    inventing a session proxy would be defining a session -- which §10.4
--    forbids this session outright. Item 11 is therefore reported against its
--    per-user half only, and resolved accordingly in the findings document.
--
-- 2. EVERY EVENT NAME, not "the progression events". Deciding which events are
--    progression events is the first half of defining a funnel step, and §8's
--    content gate bars this session from that. The table below covers the whole
--    vocabulary; the architecture session selects from it.
--
-- The per-shard grain is reported alongside the per-user grain because it is a
-- fact about how the export dates rows, and it bounds repetition within the
-- export's own day. It is NOT a session, NOT a day boundary, and must not be
-- read as either -- item 3 records what is known about the export's day
-- semantics, and the boundary itself remains unfixed.
--
-- Columns read: event_name, user_pseudo_id. _TABLE_SUFFIX is a pseudo column.
-- Shard range 20180612-20181003.
--
-- Output columns: event_name, events, users_with_event,
--                 events_per_user_p50, events_per_user_p90, events_per_user_max,
--                 users_with_more_than_one_event, users_repeating_share_ppm,
--                 user_shard_pairs, events_per_user_shard_p50,
--                 events_per_user_shard_p90, events_per_user_shard_max,
--                 user_shard_pairs_with_more_than_one,
--                 user_shard_pairs_repeating_share_ppm

WITH base AS (
  SELECT
    _TABLE_SUFFIX AS shard_suffix,
    event_name,
    user_pseudo_id
  FROM `firebase-public-project.analytics_153293282.events_*`
  WHERE _TABLE_SUFFIX BETWEEN '20180612' AND '20181003'
),

per_user AS (
  SELECT event_name, user_pseudo_id, COUNT(*) AS n
  FROM base
  GROUP BY event_name, user_pseudo_id
),

per_user_shard AS (
  SELECT event_name, user_pseudo_id, shard_suffix, COUNT(*) AS n
  FROM base
  GROUP BY event_name, user_pseudo_id, shard_suffix
),

u AS (
  SELECT
    event_name,
    SUM(n)                                                      AS events,
    COUNT(*)                                                    AS users_with_event,
    APPROX_QUANTILES(n, 100)[OFFSET(50)]                        AS events_per_user_p50,
    APPROX_QUANTILES(n, 100)[OFFSET(90)]                        AS events_per_user_p90,
    MAX(n)                                                      AS events_per_user_max,
    COUNTIF(n > 1)                                              AS users_with_more_than_one_event,
    CAST(ROUND(COUNTIF(n > 1) * 1000000 / COUNT(*)) AS INT64)   AS users_repeating_share_ppm
  FROM per_user
  GROUP BY event_name
),

us AS (
  SELECT
    event_name,
    COUNT(*)                                                    AS user_shard_pairs,
    APPROX_QUANTILES(n, 100)[OFFSET(50)]                        AS events_per_user_shard_p50,
    APPROX_QUANTILES(n, 100)[OFFSET(90)]                        AS events_per_user_shard_p90,
    MAX(n)                                                      AS events_per_user_shard_max,
    COUNTIF(n > 1)                                              AS user_shard_pairs_with_more_than_one,
    CAST(ROUND(COUNTIF(n > 1) * 1000000 / COUNT(*)) AS INT64)   AS user_shard_pairs_repeating_share_ppm
  FROM per_user_shard
  GROUP BY event_name
)

SELECT
  u.event_name,
  u.events,
  u.users_with_event,
  u.events_per_user_p50,
  u.events_per_user_p90,
  u.events_per_user_max,
  u.users_with_more_than_one_event,
  u.users_repeating_share_ppm,
  us.user_shard_pairs,
  us.events_per_user_shard_p50,
  us.events_per_user_shard_p90,
  us.events_per_user_shard_max,
  us.user_shard_pairs_with_more_than_one,
  us.user_shard_pairs_repeating_share_ppm
FROM u JOIN us USING (event_name)
ORDER BY u.events DESC
