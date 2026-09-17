-- 17_part1_first_open_time_agreement.sql
-- §10.7.3's GATE, and only the gate. The sensitivity check itself is query 18 and
-- runs only if this one clears 99.0%.
--
--   §10.7.3  "Run the check only if first_open_time's derived date equals the
--            first_open event's event_date for >= 99.0% of the 4,319 users who
--            have both -- otherwise the property's semantics are not established
--            even for the overlapping population, the check is OMITTED, and the
--            observed agreement share is reported instead."
--   A-141    The unit is determined by magnitude and reported, not assumed:
--            microseconds at or above 1e15, milliseconds at or above 1e12,
--            seconds below that. The date is derived in the same property-local
--            zone the day key uses, so this query reports agreement under every
--            whole-hour offset from -12 to +14 and the renderer selects the
--            offsets query 11 showed to be feasible, taking the MINIMUM agreement
--            across them against the gate. Computing every candidate here rather
--            than hardcoding one keeps the zone out of this file: the selection
--            rule was fixed in A-141 before any of these numbers existed, and the
--            full table is committed so a reader can apply it themselves.
--
-- Why the minimum rather than the best: the check exists to probe an unverified
-- field, so it must not run because a favourable zone was chosen for it.
--
-- first_open_time is populated for all 15,175 users on 5,699,844 rows (A-109),
-- carrying an int_value and a set_timestamp. This query reads the property's
-- VALUE -- what it says -- not its set_timestamp, which records when GA4 wrote it.
--
-- Columns read: event_date, event_name, event_timestamp, user_properties,
-- user_pseudo_id. Shard range 20180612-20181003.
--
-- Output columns: section, metric, value_num, value_text, note

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
    MIN(first_open_time)        AS fot_value,
    COUNT(DISTINCT first_open_time) AS fot_distinct_values,
    -- The install day Part 1 actually uses (A-137), for the users that have one.
    ARRAY_AGG(IF(event_name = 'first_open', event_date, NULL)
              IGNORE NULLS ORDER BY event_timestamp ASC, event_date ASC
              LIMIT 1)[SAFE_OFFSET(0)] AS install_event_date
  FROM deduped
  GROUP BY user_pseudo_id
),

typed AS (
  SELECT
    user_pseudo_id,
    fot_value,
    fot_distinct_values,
    install_event_date,
    CASE
      WHEN fot_value >= 1000000000000000 THEN 'microseconds'
      WHEN fot_value >= 1000000000000    THEN 'milliseconds'
      WHEN fot_value IS NOT NULL         THEN 'seconds'
      ELSE NULL
    END AS fot_unit,
    CASE
      WHEN fot_value >= 1000000000000000 THEN TIMESTAMP_MICROS(fot_value)
      WHEN fot_value >= 1000000000000    THEN TIMESTAMP_MILLIS(fot_value)
      WHEN fot_value IS NOT NULL         THEN TIMESTAMP_SECONDS(fot_value)
      ELSE NULL
    END AS fot_ts
  FROM per_user
),

summary AS (
  SELECT
    COUNT(*)                                                       AS users_total,
    COUNTIF(fot_value IS NOT NULL)                                 AS users_with_property,
    COUNTIF(install_event_date IS NOT NULL)                        AS users_with_event,
    COUNTIF(fot_value IS NOT NULL AND install_event_date IS NOT NULL) AS users_with_both,
    COUNTIF(fot_distinct_values > 1)                               AS users_with_varying_property,
    COUNTIF(fot_unit = 'microseconds')                             AS users_unit_microseconds,
    COUNTIF(fot_unit = 'milliseconds')                             AS users_unit_milliseconds,
    COUNTIF(fot_unit = 'seconds')                                  AS users_unit_seconds,
    MIN(fot_value)                                                 AS fot_min_value,
    MAX(fot_value)                                                 AS fot_max_value,
    MIN(fot_ts)                                                    AS fot_min_ts,
    MAX(fot_ts)                                                    AS fot_max_ts,
    -- GA4 is documented as recording this property at a coarser granularity than
    -- the event stream. Measured rather than assumed, because A-141 says a
    -- rounded field is a different finding from a disagreeing one.
    COUNTIF(fot_unit IS NOT NULL AND MOD(UNIX_MILLIS(fot_ts), 3600000) = 0) AS users_value_on_exact_hour,
    COUNTIF(fot_unit IS NOT NULL AND MOD(UNIX_MILLIS(fot_ts), 1000) = 0)    AS users_value_on_exact_second
  FROM typed
),

candidates AS (
  SELECT
    h AS offset_hours,
    COUNTIF(FORMAT_TIMESTAMP('%Y%m%d', fot_ts, FORMAT('%+03d:00', h)) = install_event_date) AS users_agreeing,
    COUNT(*) AS users_compared
  FROM typed, UNNEST(GENERATE_ARRAY(-12, 14)) AS h
  WHERE install_event_date IS NOT NULL AND fot_ts IS NOT NULL
  GROUP BY offset_hours
)

SELECT 'coverage' AS section, 'users_total' AS metric,
       users_total AS value_num, CAST(NULL AS STRING) AS value_text,
       'distinct users in the shard range' AS note
FROM summary
UNION ALL SELECT 'coverage', 'users_with_first_open_time_property', users_with_property, NULL,
  'A-109 recorded this as all 15,175' FROM summary
UNION ALL SELECT 'coverage', 'users_with_first_open_event', users_with_event, NULL,
  'Part 1 population, §10.5.1' FROM summary
UNION ALL SELECT 'coverage', 'users_with_both', users_with_both, NULL,
  'the denominator §10.7.3 names for the 99.0% gate' FROM summary
UNION ALL SELECT 'coverage', 'users_whose_property_varies_across_rows', users_with_varying_property, NULL,
  'a user property should be constant per user; expected 0' FROM summary

UNION ALL SELECT 'unit', 'users_unit_microseconds', users_unit_microseconds, NULL,
  'A-141 magnitude rule: value >= 1e15' FROM summary
UNION ALL SELECT 'unit', 'users_unit_milliseconds', users_unit_milliseconds, NULL,
  'A-141 magnitude rule: 1e12 <= value < 1e15' FROM summary
UNION ALL SELECT 'unit', 'users_unit_seconds', users_unit_seconds, NULL,
  'A-141 magnitude rule: value < 1e12' FROM summary
UNION ALL SELECT 'unit', 'first_open_time_min_value', fot_min_value, NULL,
  'raw INT64 value' FROM summary
UNION ALL SELECT 'unit', 'first_open_time_max_value', fot_max_value, NULL,
  'raw INT64 value' FROM summary
UNION ALL SELECT 'unit', 'first_open_time_min_as_utc', NULL,
  FORMAT_TIMESTAMP('%Y-%m-%d %H:%M:%E*S UTC', fot_min_ts, 'UTC'),
  'the earliest install time the property claims; may predate the window' FROM summary
UNION ALL SELECT 'unit', 'first_open_time_max_as_utc', NULL,
  FORMAT_TIMESTAMP('%Y-%m-%d %H:%M:%E*S UTC', fot_max_ts, 'UTC'),
  'the latest install time the property claims' FROM summary

UNION ALL SELECT 'granularity', 'users_value_on_exact_hour', users_value_on_exact_hour, NULL,
  'values landing exactly on an hour boundary; GA4 is documented as rounding this property' FROM summary
UNION ALL SELECT 'granularity', 'users_value_on_exact_second', users_value_on_exact_second, NULL,
  'values landing exactly on a second boundary' FROM summary

UNION ALL
SELECT 'agreement', FORMAT('utc%+03d_00_users_agreeing', offset_hours),
       users_agreeing, NULL,
       FORMAT('of %d users with both; the gate is 99.0%% and A-141 reads it at the MINIMUM over the offsets query 11 shows feasible', users_compared)
FROM candidates
ORDER BY section, metric
