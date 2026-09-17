-- 11_part1_day_key_offset.sql
-- §10.5.2's standing requirement on this session: "the build session REPORTS THE
-- OFFSET IT OBSERVES rather than assuming that figure."
--
-- §10.5.2 fixes the day key as event_date and rejects a UTC-recomputed date and a
-- device-local date, on A-098's evidence that event_date sits one day behind the
-- UTC date on 33.96% of rows and is never ahead -- the signature of a fixed
-- non-UTC zone, "consistent with UTC-07:00". This query does not assume that
-- figure. It measures the offset two independent ways:
--
--   (a) BOUNDS. For a row to be dated in a fixed zone whose offset is `off`
--       seconds, event_date must be the local date of event_timestamp, i.e.
--           event_date_midnight <= event_timestamp + off < event_date_midnight + 24h
--       so every row constrains off to [lower, lower + 86400), where
--           lower = event_date_midnight - event_timestamp.
--       The whole range is therefore feasible only for
--           off in [MAX(lower), MIN(lower) + 86400).
--       An empty interval would mean no single constant offset dates this export.
--
--   (b) CANDIDATES. For every whole hour from -12 to +14, the count of rows whose
--       local date under that offset equals event_date. An offset that dates all
--       5,700,000 rows correctly is feasible; anything less is not.
--
-- (b) is what A-141 consumes: the zone used to date first_open_time is the
-- whole-hour offset shown feasible here, and if several are feasible the
-- agreement share is taken at its minimum across them.
--
-- The row counts behind A-098's one-sided offset are re-measured too, because
-- §10.5.2's whole argument for event_date rests on the offset being one-sided and
-- consistent rather than noisy.
--
-- Columns read: event_date, event_timestamp. Shard range 20180612-20181003.
--
-- Output columns: section, metric, value_num, value_text, note

WITH base AS (
  SELECT
    _TABLE_SUFFIX     AS shard_suffix,
    event_date,
    event_timestamp
  FROM `firebase-public-project.analytics_153293282.events_*`
  WHERE _TABLE_SUFFIX BETWEEN '20180612' AND '20181003'
),

bounds AS (
  SELECT
    COUNT(*) AS total_rows,
    COUNTIF(event_date != shard_suffix) AS rows_event_date_ne_shard,
    COUNTIF(DATE_DIFF(PARSE_DATE('%Y%m%d', event_date),
                      DATE(TIMESTAMP_MICROS(event_timestamp), 'UTC'), DAY) = -1) AS rows_one_day_behind_utc,
    COUNTIF(DATE_DIFF(PARSE_DATE('%Y%m%d', event_date),
                      DATE(TIMESTAMP_MICROS(event_timestamp), 'UTC'), DAY) = 0) AS rows_same_as_utc,
    COUNTIF(DATE_DIFF(PARSE_DATE('%Y%m%d', event_date),
                      DATE(TIMESTAMP_MICROS(event_timestamp), 'UTC'), DAY) = 1) AS rows_one_day_ahead_utc,
    -- The binding constraints on a constant offset, in seconds.
    MAX(TIMESTAMP_DIFF(TIMESTAMP(PARSE_DATE('%Y%m%d', event_date)),
                       TIMESTAMP_MICROS(event_timestamp), SECOND)) AS offset_lower_bound_seconds,
    MIN(TIMESTAMP_DIFF(TIMESTAMP(PARSE_DATE('%Y%m%d', event_date)),
                       TIMESTAMP_MICROS(event_timestamp), SECOND)) AS min_lower_seconds
  FROM base
),

candidates AS (
  SELECT
    h AS offset_hours,
    COUNTIF(FORMAT_TIMESTAMP('%Y%m%d', TIMESTAMP_MICROS(event_timestamp),
                             FORMAT('%+03d:00', h)) = event_date) AS rows_matching
  FROM base, UNNEST(GENERATE_ARRAY(-12, 14)) AS h
  GROUP BY offset_hours
)

SELECT 'window' AS section, 'total_rows' AS metric,
       total_rows AS value_num, CAST(NULL AS STRING) AS value_text,
       'rows across the full shard range' AS note
FROM bounds
UNION ALL SELECT 'window', 'rows_event_date_ne_shard_suffix', rows_event_date_ne_shard, NULL,
  'event_date disagreeing with the shard it is stored in; A-098 measured 0' FROM bounds

UNION ALL SELECT 'utc_comparison', 'rows_event_date_one_day_behind_utc', rows_one_day_behind_utc, NULL,
  'event_date is the UTC date minus one day' FROM bounds
UNION ALL SELECT 'utc_comparison', 'rows_event_date_same_as_utc', rows_same_as_utc, NULL,
  'event_date equals the UTC date' FROM bounds
UNION ALL SELECT 'utc_comparison', 'rows_event_date_one_day_ahead_utc', rows_one_day_ahead_utc, NULL,
  'event_date is the UTC date plus one day; §10.5.2 rests on this being 0' FROM bounds
UNION ALL SELECT 'utc_comparison', 'rows_behind_utc_share_ppm',
  CAST(ROUND(rows_one_day_behind_utc * 1000000 / total_rows) AS INT64), NULL,
  'parts per million; A-098 measured 33.96%' FROM bounds

UNION ALL SELECT 'offset_bounds', 'feasible_offset_lower_seconds', offset_lower_bound_seconds, NULL,
  'a constant offset must be at least this many seconds from UTC' FROM bounds
UNION ALL SELECT 'offset_bounds', 'feasible_offset_upper_exclusive_seconds', min_lower_seconds + 86400, NULL,
  'and strictly less than this' FROM bounds
UNION ALL SELECT 'offset_bounds', 'feasible_offset_width_seconds',
  (min_lower_seconds + 86400) - offset_lower_bound_seconds, NULL,
  'width of the feasible interval; a negative value would mean no constant offset fits' FROM bounds
UNION ALL SELECT 'offset_bounds', 'feasible_offset_lower_hours', NULL,
  FORMAT('%.4f', offset_lower_bound_seconds / 3600), 'lower bound in hours' FROM bounds
UNION ALL SELECT 'offset_bounds', 'feasible_offset_upper_exclusive_hours', NULL,
  FORMAT('%.4f', (min_lower_seconds + 86400) / 3600), 'upper bound in hours, exclusive' FROM bounds

UNION ALL
SELECT 'offset_candidate', FORMAT('utc%+03d_00_rows_matching', offset_hours),
       rows_matching, NULL,
       'rows whose local date under this whole-hour offset equals event_date; a feasible offset matches every row'
FROM candidates
ORDER BY section, metric
