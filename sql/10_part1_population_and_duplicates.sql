-- 10_part1_population_and_duplicates.sql
-- Part 1 outputs 1 and 7 (ARCHITECTURE.md §10.5.7): the population
-- reconciliation, and the duplicate-row accounting §10.7.4 requires.
--
--   §10.5.1  Part 1's population is the users with a first_open EVENT. This
--            query recomputes the three figures §10.5.7 item 1 names -- total
--            users, users with a first_open, users without -- rather than
--            transcribing them from A-097. Per A-079 the CSV is the source of
--            truth for every number, so if these disagree with the recon the
--            disagreement is the finding.
--   §10.7.4  De-duplicate on (user_pseudo_id, event_name, event_timestamp)
--            before any count, and report the rows removed (A-124, A-138).
--   A-137    Install day is the event_date of the lowest-timestamp first_open.
--            This query asserts that reading agrees with MIN(event_date) and
--            reports the number of users where it does not.
--
-- One scan. Every figure is derived from a single aggregation to per-user grain
-- and then folded to totals, so the event table is read exactly once: the
-- deduplication, the distinct-user counts and the first_open detail all come
-- from the same pass rather than from three references to the same CTE.
--
-- Columns read: event_date, event_name, event_timestamp, user_pseudo_id.
-- Shard range 20180612-20181003.
--
-- Output columns: section, metric, value_num, value_text, note

WITH per_user AS (
  SELECT
    user_pseudo_id,

    -- Raw rows, before §10.7.4's de-duplication.
    COUNT(*)                                                          AS rows_raw,
    -- The natural key §10.7.4 names, counted within the user.
    COUNT(DISTINCT FORMAT('%s|%d', event_name, event_timestamp))      AS keys_natural,
    -- The same key with event_date appended. If this exceeds keys_natural, a
    -- duplicate group straddles two dates and A-138's MIN(event_date) collapse
    -- is not a no-op. Expected equal.
    COUNT(DISTINCT FORMAT('%s|%d|%s', event_name, event_timestamp, event_date))
                                                                      AS keys_natural_with_date,

    COUNTIF(event_name = 'first_open')                                AS first_open_rows_raw,
    COUNT(DISTINCT IF(event_name = 'first_open',
                      FORMAT('%d', event_timestamp), NULL))           AS first_open_events_deduped,

    -- A-137: install day read two ways. earliest_by_timestamp is the definition;
    -- min_event_date is the check.
    ARRAY_AGG(IF(event_name = 'first_open', event_date, NULL)
              IGNORE NULLS ORDER BY event_timestamp ASC, event_date ASC
              LIMIT 1)[SAFE_OFFSET(0)]                                AS install_day_by_timestamp,
    MIN(IF(event_name = 'first_open', event_date, NULL))              AS install_day_by_min_date
  FROM `firebase-public-project.analytics_153293282.events_*`
  WHERE _TABLE_SUFFIX BETWEEN '20180612' AND '20181003'
  GROUP BY user_pseudo_id
),

agg AS (
  SELECT
    SUM(rows_raw)                                                     AS raw_event_rows,
    SUM(keys_natural)                                                 AS deduped_event_rows,
    SUM(rows_raw) - SUM(keys_natural)                                 AS duplicate_rows_removed,
    SUM(keys_natural_with_date) - SUM(keys_natural)                   AS duplicate_groups_spanning_two_dates,

    COUNT(*)                                                          AS users_total,
    COUNTIF(install_day_by_timestamp IS NOT NULL)                     AS users_with_first_open,
    COUNTIF(install_day_by_timestamp IS NULL)                         AS users_without_first_open,

    SUM(first_open_rows_raw)                                          AS first_open_rows_raw,
    SUM(first_open_events_deduped)                                    AS first_open_events_deduped,
    COUNTIF(first_open_events_deduped > 1)                            AS users_with_repeat_first_open,
    MAX(first_open_events_deduped)                                    AS max_first_open_per_user,

    COUNTIF(install_day_by_timestamp IS NOT NULL
            AND install_day_by_timestamp != install_day_by_min_date)  AS install_day_reading_disagrees
  FROM per_user
)

SELECT 'population' AS section, 'distinct_users_total' AS metric,
       users_total AS value_num, CAST(NULL AS STRING) AS value_text,
       'distinct user_pseudo_id with at least one event in the shard range; §10.6.2 and §10.3 denominator' AS note
FROM agg
UNION ALL SELECT 'population', 'users_with_first_open_event', users_with_first_open, NULL,
  'Part 1 population per §10.5.1 -- users with at least one first_open EVENT' FROM agg
UNION ALL SELECT 'population', 'users_without_first_open_event', users_without_first_open, NULL,
  'excluded from Part 1 by §10.5.1; the exclusion is not random (§10.5.1)' FROM agg
UNION ALL SELECT 'population', 'users_without_first_open_share_ppm',
  CAST(ROUND(users_without_first_open * 1000000 / users_total) AS INT64), NULL,
  'parts per million of all users; §10.5.7 item 1 reports this as a percentage' FROM agg
UNION ALL SELECT 'population', 'first_open_events_deduped', first_open_events_deduped, NULL,
  'first_open events after §10.7.4 de-duplication' FROM agg
UNION ALL SELECT 'population', 'first_open_rows_raw', first_open_rows_raw, NULL,
  'first_open rows before de-duplication' FROM agg
UNION ALL SELECT 'population', 'users_with_more_than_one_first_open', users_with_repeat_first_open, NULL,
  'users with two or more deduped first_open events; §10.5.2 takes the earliest' FROM agg
UNION ALL SELECT 'population', 'max_first_open_events_per_user', max_first_open_per_user, NULL,
  'largest number of deduped first_open events held by one user' FROM agg

UNION ALL SELECT 'duplicates', 'raw_event_rows', raw_event_rows, NULL,
  'rows across the full shard range, before de-duplication' FROM agg
UNION ALL SELECT 'duplicates', 'deduped_event_rows', deduped_event_rows, NULL,
  'distinct (user_pseudo_id, event_name, event_timestamp)' FROM agg
UNION ALL SELECT 'duplicates', 'duplicate_rows_removed', duplicate_rows_removed, NULL,
  'removed before any count, per §10.7.4 and A-124' FROM agg
UNION ALL SELECT 'duplicates', 'duplicate_share_ppm',
  CAST(ROUND(duplicate_rows_removed * 1000000 / raw_event_rows) AS INT64), NULL,
  'parts per million of raw rows' FROM agg
UNION ALL SELECT 'duplicates', 'duplicate_groups_spanning_two_dates', duplicate_groups_spanning_two_dates, NULL,
  'A-138 assertion: expected 0, meaning MIN(event_date) in the collapse is a no-op' FROM agg

UNION ALL SELECT 'install_day_definition', 'users_where_timestamp_and_date_readings_disagree',
  install_day_reading_disagrees, NULL,
  'A-137 assertion: users whose earliest-by-timestamp first_open date differs from MIN(event_date); expected 0' FROM agg
ORDER BY section, metric
