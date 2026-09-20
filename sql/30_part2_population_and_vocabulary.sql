-- 30_part2_population_and_vocabulary.sql
-- Part 2's first query: what the data is, before any funnel is computed.
--
--   §10.7.2  Each report opens with a population reconciliation table. Part 2's
--            population is ALL 15,175 users (§10.6.2), so its reconciliation is
--            the mirror image of Part 1's: nobody is excluded, and the 4,319 /
--            10,856 split Part 1 had to live with is reported here precisely to
--            show that Part 2 does not inherit it.
--   §10.7.4  De-duplicate on (user_pseudo_id, event_name, event_timestamp)
--            before any count, and report the rows removed. A-166 implements
--            that as a GROUP BY on exactly that key, as A-138 did for Part 1,
--            and carries COUNT(*) per group so RAW and DEDUPED counts both fall
--            out of one pass. That is what makes the divergence from §10.6.5's
--            quoted event counts exactly attributable rather than merely small.
--   §10.6.6  Item 3 requires the diagnostic table "regenerated rather than
--            transcribed" and item 4 the level_end reconciliation at event
--            level. Both are read off the COMPLETE 37-name vocabulary below
--            rather than off a selected set, so the seven diagnostics and the
--            three reconciliation events are a visible selection from a
--            committed table (A-090's precedent).
--   A-171    The ERROR() guard asserts A-096's 5,700,000 rows and A-097's 15,175
--            distinct users. If it fires, that is an implementation defect and
--            it stops the run -- it is NOT evidence against the recon.
--
-- Columns read: user_pseudo_id, event_name, event_timestamp.
-- event_date is deliberately NOT read: the funnel is a whole-window presence
-- metric (§10.6.2), so no day key enters Part 2 at all.
-- Shard range 20180612-20181003.
--
-- Output columns: section, key, events_deduped, events_raw, duplicate_rows, users

WITH deduped AS (
  SELECT
    user_pseudo_id,
    event_name,
    event_timestamp,
    COUNT(*) AS row_copies          -- 1 for a unique row, 2+ for a duplicated one
  FROM `firebase-public-project.analytics_153293282.events_*`
  WHERE _TABLE_SUFFIX BETWEEN '20180612' AND '20181003'
  GROUP BY user_pseudo_id, event_name, event_timestamp
),

totals AS (
  SELECT
    COUNT(*)                        AS events_deduped,
    SUM(row_copies)                 AS events_raw,
    SUM(row_copies) - COUNT(*)      AS duplicate_rows,
    COUNT(DISTINCT user_pseudo_id)  AS users
  FROM deduped
),

-- A-171. IF() evaluates ERROR() only on the false branch, so a passing guard
-- costs nothing and a failing one returns no rows at all.
guard AS (
  SELECT IF(events_raw = 5700000 AND users = 15175, TRUE,
    ERROR(FORMAT(
      'A-171 guard failed: raw rows %d (A-096 expects 5,700,000), distinct users %d (A-097 expects 15,175). This is an implementation defect and stops the run, not evidence against the recon.',
      events_raw, users))) AS ok
  FROM totals
),

per_event AS (
  SELECT
    event_name,
    COUNT(*)                        AS events_deduped,
    SUM(row_copies)                 AS events_raw,
    SUM(row_copies) - COUNT(*)      AS duplicate_rows,
    COUNT(DISTINCT user_pseudo_id)  AS users
  FROM deduped
  GROUP BY event_name
),

installers AS (
  SELECT COUNT(DISTINCT user_pseudo_id) AS users_with_first_open
  FROM deduped
  WHERE event_name = 'first_open'
),

rows_out AS (
  SELECT 'totals' AS section, 'all_event_names' AS key,
         events_deduped, events_raw, duplicate_rows, users
  FROM totals

  UNION ALL
  -- Part 1's population, reported here to show Part 2 does not inherit it.
  SELECT 'population', 'users_with_first_open',
         CAST(NULL AS INT64), CAST(NULL AS INT64), CAST(NULL AS INT64),
         (SELECT users_with_first_open FROM installers)

  UNION ALL
  SELECT 'population', 'users_without_first_open',
         CAST(NULL AS INT64), CAST(NULL AS INT64), CAST(NULL AS INT64),
         (SELECT users FROM totals) - (SELECT users_with_first_open FROM installers)

  UNION ALL
  SELECT 'population', 'users_in_funnel_population',
         CAST(NULL AS INT64), CAST(NULL AS INT64), CAST(NULL AS INT64),
         (SELECT users FROM totals)

  UNION ALL
  SELECT 'population', 'users_excluded_from_funnel_population',
         CAST(NULL AS INT64), CAST(NULL AS INT64), CAST(NULL AS INT64), 0

  UNION ALL
  SELECT 'event', event_name, events_deduped, events_raw, duplicate_rows, users
  FROM per_event
)

SELECT r.section, r.key, r.events_deduped, r.events_raw, r.duplicate_rows, r.users
FROM rows_out r
CROSS JOIN guard g
WHERE g.ok
ORDER BY
  CASE r.section WHEN 'totals' THEN 0 WHEN 'population' THEN 1 ELSE 2 END,
  r.events_deduped DESC NULLS LAST,
  r.key
