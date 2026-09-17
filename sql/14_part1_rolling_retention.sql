-- 14_part1_rolling_retention.sql
-- Part 1 output 5 (§10.5.7): rolling retention by weekly cohort, and pooled, at
-- D1, D7 and D30 -- the SECONDARY metric, in its own labelled table.
--
--   §10.5.3  Rolling retention: a user is retained at day N if they have at
--            least one event with event_date >= install day + N. Classic, the
--            primary, requires equality exactly and lives in query 13. Neither
--            may be presented without its label, which is why these are two
--            files and two tables rather than two columns of one.
--   A-135    Eligibility binds this table identically to classic -- 16 / 15 / 12
--            cohorts at D1 / D7 / D30 -- as directed. A cohort that cannot be
--            observed to install day + N cannot be measured at N by either
--            definition: a rolling D30 on a cohort whose window is short counts
--            only the part of the ">= install + 30" tail that fits inside the
--            export, so it would be truncated and understated. §10.5.5 exists to
--            prevent exactly that artefact, and this is a challenge entry rather
--            than a decision because §10.5.3 and §10.5.5 do not say which way it
--            goes.
--   §10.5.5  Ineligible cells are NULL, never zero and never omitted -- the same
--            four-layer chain as classic, so both tables are null on the same
--            cells and the renderer's "rolling >= classic" assertion is defined
--            everywhere it runs.
--
-- Rolling retention is computed from the user's LAST active day rather than from
-- the set of active days: having any event on or after install + N is exactly
-- MAX(event_date) >= install + N, and stating it that way makes the bound
-- obvious. No rate and no interval is computed here (A-139).
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
    MAX(PARSE_DATE('%Y%m%d', event_date))                    AS last_active_day
  FROM deduped
  GROUP BY user_pseudo_id
),

cohorted AS (
  SELECT
    install_day,
    last_active_day,
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
    -- Rolling: an event on or after install day + N.
    COUNTIF(c.last_active_day >= DATE_ADD(c.install_day, INTERVAL h DAY)) AS retained
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
