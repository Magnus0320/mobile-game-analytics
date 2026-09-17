-- 18_part1_first_open_time_sensitivity.sql
-- §10.7.3's sensitivity check. THIS QUERY RUNS ONLY IF QUERY 17 CLEARED 99.0%.
-- If the gate failed it is never executed, no row of it exists, and the observed
-- agreement share is reported in its place -- which is what §10.7.3 requires, and
-- why the gate is a separate query rather than a column of this one.
--
--   §10.7.3  "Derive install day from the first_open_time user property for all
--            15,175 users and recompute pooled D7." The figure belongs in the
--            negative-results section, labelled a robustness check on an
--            unverified field, with the agreement share beside it. It never
--            enters a results table and never becomes a headline.
--   A-141    Unit by magnitude; the date derived in the property-local zone, with
--            the offsets query 11 showed feasible selected by the renderer.
--
-- One thing this query must decide and therefore states plainly: the derived
-- population is run through the SAME cohort machinery as the primary. A derived
-- install day is assigned to the sixteen anchored weekly blocks, and pooled D7 is
-- taken over the D7-eligible cohorts W01-W15, exactly as query 13 does. Users
-- whose derived install day falls outside 20180612-20181001 are excluded and
-- COUNTED, not scored: a user whose property says they installed in May has no
-- observable day 7 inside this window, and counting them as unretained would
-- manufacture the false zero §10.5.5 exists to prevent. Like-for-like is the only
-- comparison worth making, since the whole question is what the 71.54% exclusion
-- costs.
--
-- Columns read: event_date, event_name, event_timestamp, user_properties,
-- user_pseudo_id. Shard range 20180612-20181003.
--
-- Output columns: offset_hours, users_total, users_with_property,
--                 users_inside_window, users_before_window, users_after_window,
--                 denominator, retained

WITH base AS (
  SELECT
    user_pseudo_id,
    event_name,
    event_timestamp,
    event_date,
    (SELECT p.value.int_value
     FROM UNNEST(user_properties) p
     WHERE p.key = 'first_open_time'
     LIMIT 1) AS first_open_time
  FROM `firebase-public-project.analytics_153293282.events_*`
  WHERE _TABLE_SUFFIX BETWEEN '20180612' AND '20181003'
),

deduped AS (
  SELECT
    user_pseudo_id, event_name, event_timestamp,
    MIN(event_date)      AS event_date,
    MIN(first_open_time) AS first_open_time
  FROM base
  GROUP BY user_pseudo_id, event_name, event_timestamp
),

per_user AS (
  SELECT
    user_pseudo_id,
    MIN(first_open_time) AS fot_value,
    ARRAY_AGG(DISTINCT PARSE_DATE('%Y%m%d', event_date)) AS active_days
  FROM deduped
  GROUP BY user_pseudo_id
),

typed AS (
  SELECT
    user_pseudo_id,
    active_days,
    CASE
      WHEN fot_value >= 1000000000000000 THEN TIMESTAMP_MICROS(fot_value)
      WHEN fot_value >= 1000000000000    THEN TIMESTAMP_MILLIS(fot_value)
      WHEN fot_value IS NOT NULL         THEN TIMESTAMP_SECONDS(fot_value)
      ELSE NULL
    END AS fot_ts
  FROM per_user
),

derived AS (
  SELECT
    t.user_pseudo_id,
    t.active_days,
    h AS offset_hours,
    IF(t.fot_ts IS NULL, NULL,
       DATE(t.fot_ts, FORMAT('%+03d:00', h))) AS install_day
  FROM typed t, UNNEST(GENERATE_ARRAY(-12, 14)) AS h
)

SELECT
  offset_hours,
  COUNT(*)                                                     AS users_total,
  COUNTIF(install_day IS NOT NULL)                             AS users_with_property,
  COUNTIF(install_day BETWEEN DATE '2018-06-12' AND DATE '2018-10-01') AS users_inside_window,
  COUNTIF(install_day < DATE '2018-06-12')                     AS users_before_window,
  COUNTIF(install_day > DATE '2018-10-01')                     AS users_after_window,
  -- Pooled D7 over the D7-eligible cohorts W01-W15, i.e. derived install day on
  -- or before 20180924 (W15's last day), which is the per-cohort rule query 13
  -- applies to the primary population (A-134).
  COUNTIF(install_day BETWEEN DATE '2018-06-12' AND DATE '2018-09-24') AS denominator,
  COUNTIF(install_day BETWEEN DATE '2018-06-12' AND DATE '2018-09-24'
          AND DATE_ADD(install_day, INTERVAL 7 DAY) IN UNNEST(active_days)) AS retained
FROM derived
GROUP BY offset_hours
ORDER BY offset_hours
