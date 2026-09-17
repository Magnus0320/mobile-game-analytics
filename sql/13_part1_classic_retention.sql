-- 13_part1_classic_retention.sql
-- Part 1 outputs 3 and 4 (§10.5.7): classic retention by weekly cohort, and
-- pooled, at D1, D7 and D30.
--
--   §10.5.3  PRIMARY metric, classic retention: a user is retained at day N if
--            they have at least one event whose event_date equals install day
--            plus N EXACTLY. Not "on or after" -- that is the rolling definition
--            and it lives in query 14.
--   §10.5.2  Day key is event_date; install day is the event_date of the user's
--            earliest first_open (A-137), and is day 0, never a retention day.
--   §10.5.5  Ineligible cells are NULL, never zero and never omitted. This query
--            emits a row for all 16 cohorts at all three horizons and sets
--            denominator and retained to SQL NULL where the cohort cannot be
--            observed, so no zero can leak into a cell that was never measured.
--            The numerator is not computed for such a cell at all.
--   A-134    The pooled figure at horizon N is the union of the cohorts eligible
--            at N -- W01-W16 at D1, W01-W15 at D7, W01-W12 at D30 -- as directed.
--            Every pooled denominator is therefore the plain sum of that
--            horizon's weekly denominators, which the renderer asserts.
--
-- No rate and no interval is computed here. SQL returns integers; §10.5.3's
-- Wilson interval and its n<30 suppression are Python's, in one place (A-139).
--
-- Columns read: event_date, event_name, event_timestamp, user_pseudo_id.
-- Shard range 20180612-20181003.
--
-- Output columns: grain, cohort, cohort_start, cohort_end, horizon_days,
--                 installs, eligible, denominator, retained, cohorts_included

WITH deduped AS (
  -- §10.7.4, A-138: the natural key, with a deterministic MIN() collapse.
  SELECT user_pseudo_id, event_name, event_timestamp, MIN(event_date) AS event_date
  FROM `firebase-public-project.analytics_153293282.events_*`
  WHERE _TABLE_SUFFIX BETWEEN '20180612' AND '20181003'
  GROUP BY user_pseudo_id, event_name, event_timestamp
),

per_user AS (
  SELECT
    user_pseudo_id,
    PARSE_DATE('%Y%m%d',
      ARRAY_AGG(IF(event_name = 'first_open', event_date, NULL)
                IGNORE NULLS ORDER BY event_timestamp ASC, event_date ASC
                LIMIT 1)[SAFE_OFFSET(0)])                    AS install_day,
    ARRAY_AGG(DISTINCT PARSE_DATE('%Y%m%d', event_date))     AS active_days
  FROM deduped
  GROUP BY user_pseudo_id
),

cohorted AS (
  SELECT
    install_day,
    active_days,
    DIV(DATE_DIFF(install_day, DATE '2018-06-12', DAY), 7) + 1 AS cohort_index
  FROM per_user
  WHERE install_day IS NOT NULL
),

blocks AS (
  SELECT
    idx AS cohort_index,
    FORMAT('W%02d', idx) AS cohort,
    DATE_ADD(DATE '2018-06-12', INTERVAL (idx - 1) * 7 DAY)     AS cohort_start,
    DATE_ADD(DATE '2018-06-12', INTERVAL (idx - 1) * 7 + 6 DAY) AS cohort_end
  FROM UNNEST(GENERATE_ARRAY(1, 16)) AS idx
),

assertions AS (
  SELECT
    IF((SELECT COUNTIF(DATE_ADD(cohort_end, INTERVAL 1 DAY)  <= DATE '2018-10-03') FROM blocks) = 16
       AND (SELECT COUNTIF(DATE_ADD(cohort_end, INTERVAL 7 DAY)  <= DATE '2018-10-03') FROM blocks) = 15
       AND (SELECT COUNTIF(DATE_ADD(cohort_end, INTERVAL 30 DAY) <= DATE '2018-10-03') FROM blocks) = 12
       AND (SELECT MAX(cohort_end) FROM blocks) = DATE '2018-10-01',
       1,
       ERROR('§10.5.5 eligibility assertion failed: expected exactly 16/15/12 eligible cohorts at D1/D7/D30 over blocks ending 20181001'))
      AS eligibility_ok
),

cells AS (
  SELECT
    c.cohort_index,
    h AS horizon_days,
    COUNT(*) AS installs,
    -- Classic: an event on install day + N exactly.
    COUNTIF(DATE_ADD(c.install_day, INTERVAL h DAY) IN UNNEST(c.active_days)) AS retained
  FROM cohorted c, UNNEST([1, 7, 30]) AS h
  GROUP BY cohort_index, horizon_days
),

weekly AS (
  SELECT
    b.cohort,
    b.cohort_start,
    b.cohort_end,
    h AS horizon_days,
    IFNULL(x.installs, 0) AS installs,
    DATE_ADD(b.cohort_end, INTERVAL h DAY) <= DATE '2018-10-03' AS eligible,
    IFNULL(x.retained, 0) AS retained_raw
  FROM blocks b
  CROSS JOIN UNNEST([1, 7, 30]) AS h
  CROSS JOIN assertions a
  LEFT JOIN cells x ON x.cohort_index = b.cohort_index AND x.horizon_days = h
  WHERE a.eligibility_ok = 1
)

SELECT
  'weekly' AS grain,
  cohort,
  FORMAT_DATE('%Y%m%d', cohort_start) AS cohort_start,
  FORMAT_DATE('%Y%m%d', cohort_end)   AS cohort_end,
  horizon_days,
  installs,
  eligible,
  IF(eligible, installs, NULL)     AS denominator,
  IF(eligible, retained_raw, NULL) AS retained,
  CAST(NULL AS INT64)              AS cohorts_included
FROM weekly

UNION ALL

SELECT
  'pooled',
  'POOLED',
  FORMAT_DATE('%Y%m%d', MIN(IF(eligible, cohort_start, NULL))),
  FORMAT_DATE('%Y%m%d', MAX(IF(eligible, cohort_end, NULL))),
  horizon_days,
  SUM(IF(eligible, installs, 0)),
  TRUE,
  SUM(IF(eligible, installs, 0)),
  SUM(IF(eligible, retained_raw, 0)),
  COUNTIF(eligible)
FROM weekly
GROUP BY horizon_days

ORDER BY grain DESC, cohort, horizon_days
