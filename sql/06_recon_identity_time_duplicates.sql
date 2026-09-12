-- 06_recon_identity_time_duplicates.sql
-- Recon checklist items 4, 3 and 8, in one scan.
--
--   item 4  is user_id populated, or is user_pseudo_id the only identifier?
--   item 3  what unit and zone is event_timestamp in, how does
--           user_first_touch_timestamp relate to the first_open event's own
--           timestamp, and is a property-local day boundary available at all?
--   item 8  are there duplicate event rows on the natural key
--           (user_pseudo_id, event_name, event_timestamp)?
--
-- On item 3 and the §10.4 gate: this query reports how the export's three
-- day-bearing fields relate to one another -- event_date, the UTC date implied
-- by event_timestamp, and the shard suffix -- and whether a timezone offset
-- field carries usable values. It does NOT choose a day boundary, and no part of
-- it may be read as choosing one. Those are facts about the export; the boundary
-- is the architecture session's to fix.
--
-- Every figure is computed from a single aggregation over one scan, then
-- unpivoted into long form, so the base table is read once.
--
-- Columns read: event_date, event_name, event_timestamp,
-- user_first_touch_timestamp, user_id, user_pseudo_id,
-- device.time_zone_offset_seconds. Shard range 20180612-20181003.
--
-- Output columns: section, metric, value_num, value_text, note

WITH base AS (
  SELECT
    _TABLE_SUFFIX                      AS shard_suffix,
    event_date,
    event_name,
    event_timestamp,
    user_first_touch_timestamp,
    user_id,
    user_pseudo_id,
    device.time_zone_offset_seconds    AS tz_offset_seconds
  FROM `firebase-public-project.analytics_153293282.events_*`
  WHERE _TABLE_SUFFIX BETWEEN '20180612' AND '20181003'
),

agg AS (
  SELECT
    COUNT(*)                                                     AS total_rows,
    COUNT(DISTINCT CONCAT(user_pseudo_id, '|', event_name, '|',
                          CAST(event_timestamp AS STRING)))      AS distinct_natural_keys,

    COUNTIF(user_id IS NULL)                                     AS user_id_null_rows,
    COUNT(DISTINCT user_id)                                      AS distinct_user_id,
    COUNT(DISTINCT user_pseudo_id)                               AS distinct_user_pseudo_id,

    MIN(event_timestamp)                                         AS min_event_timestamp,
    MAX(event_timestamp)                                         AS max_event_timestamp,
    COUNTIF(user_first_touch_timestamp IS NULL)                  AS first_touch_null_rows,

    -- Day-bearing fields compared against one another. Facts, not a boundary.
    COUNTIF(event_date != shard_suffix)                          AS event_date_ne_shard,
    COUNTIF(event_date != FORMAT_TIMESTAMP('%Y%m%d',
              TIMESTAMP_MICROS(event_timestamp), 'UTC'))         AS event_date_ne_utc_date,

    COUNTIF(tz_offset_seconds IS NULL)                           AS tz_offset_null_rows,
    COUNT(DISTINCT tz_offset_seconds)                            AS tz_offset_distinct,

    -- first_open rows only: the event's own timestamp minus the user's recorded
    -- first-touch timestamp, in seconds. IGNORE NULLS confines it to first_open.
    APPROX_QUANTILES(
      IF(event_name = 'first_open' AND user_first_touch_timestamp IS NOT NULL,
         DIV(event_timestamp - user_first_touch_timestamp, 1000000), NULL),
      100 IGNORE NULLS)                                          AS fo_gap_seconds_q,
    COUNTIF(event_name = 'first_open')                           AS first_open_rows,

    -- The share of the gap distribution that exceeds one day, measured exactly
    -- rather than bounded by a percentile. Item 3's problematic condition turns
    -- on it, and "under 1%" is not an artefact anyone can check.
    COUNTIF(event_name = 'first_open'
            AND ABS(event_timestamp - user_first_touch_timestamp) > 86400000000)
                                                                 AS fo_gap_over_one_day_rows,
    COUNT(DISTINCT IF(event_name = 'first_open'
            AND ABS(event_timestamp - user_first_touch_timestamp) > 86400000000,
            user_pseudo_id, NULL))                               AS fo_gap_over_one_day_users,
    COUNT(DISTINCT IF(event_name = 'first_open', user_pseudo_id, NULL))
                                                                 AS fo_users_total,

    -- How event_date sits against the UTC date of the same row's timestamp,
    -- bucketed. A bounded, one-sided offset is evidence the export dates rows in
    -- a fixed non-UTC zone. Which zone, and which boundary any metric should
    -- use, are not this session's to decide (§10.4).
    COUNTIF(DATE_DIFF(PARSE_DATE('%Y%m%d', event_date),
                      DATE(TIMESTAMP_MICROS(event_timestamp), 'UTC'), DAY) = -1)
                                                                 AS event_date_minus_one_day,
    COUNTIF(DATE_DIFF(PARSE_DATE('%Y%m%d', event_date),
                      DATE(TIMESTAMP_MICROS(event_timestamp), 'UTC'), DAY) = 0)
                                                                 AS event_date_same_day,
    COUNTIF(DATE_DIFF(PARSE_DATE('%Y%m%d', event_date),
                      DATE(TIMESTAMP_MICROS(event_timestamp), 'UTC'), DAY) = 1)
                                                                 AS event_date_plus_one_day
  FROM base
)

SELECT 'item_8_duplicates' AS section, 'total_event_rows' AS metric,
       total_rows AS value_num, CAST(NULL AS STRING) AS value_text,
       'rows across the full shard range' AS note FROM agg
UNION ALL SELECT 'item_8_duplicates', 'distinct_natural_keys', distinct_natural_keys, NULL,
  'distinct (user_pseudo_id, event_name, event_timestamp)' FROM agg
UNION ALL SELECT 'item_8_duplicates', 'duplicate_rows', total_rows - distinct_natural_keys, NULL,
  'total minus distinct on the natural key' FROM agg
UNION ALL SELECT 'item_8_duplicates', 'duplicate_share_ppm',
  CAST(ROUND((total_rows - distinct_natural_keys) * 1000000 / total_rows) AS INT64), NULL,
  'parts per million; §10.2 item 8 is problematic above 0.1% = 1000 ppm' FROM agg

UNION ALL SELECT 'item_4_identifier', 'user_id_null_rows', user_id_null_rows, NULL,
  'rows with a NULL user_id' FROM agg
UNION ALL SELECT 'item_4_identifier', 'user_id_null_share_ppm',
  CAST(ROUND(user_id_null_rows * 1000000 / total_rows) AS INT64), NULL,
  'parts per million of all rows' FROM agg
UNION ALL SELECT 'item_4_identifier', 'distinct_user_id', distinct_user_id, NULL,
  'distinct non-null user_id values' FROM agg
UNION ALL SELECT 'item_4_identifier', 'distinct_user_pseudo_id', distinct_user_pseudo_id, NULL,
  'distinct user_pseudo_id values; §10.3 and A-084 denominator' FROM agg

UNION ALL SELECT 'item_3_timestamps', 'min_event_timestamp', min_event_timestamp, NULL,
  'raw INT64 value' FROM agg
UNION ALL SELECT 'item_3_timestamps', 'max_event_timestamp', max_event_timestamp, NULL,
  'raw INT64 value' FROM agg
UNION ALL SELECT 'item_3_timestamps', 'min_event_timestamp_as_micros_utc', NULL,
  FORMAT_TIMESTAMP('%Y-%m-%d %H:%M:%E*S UTC', TIMESTAMP_MICROS(min_event_timestamp), 'UTC'),
  'if this lands inside the shard range, the unit is microseconds' FROM agg
UNION ALL SELECT 'item_3_timestamps', 'max_event_timestamp_as_micros_utc', NULL,
  FORMAT_TIMESTAMP('%Y-%m-%d %H:%M:%E*S UTC', TIMESTAMP_MICROS(max_event_timestamp), 'UTC'),
  'if this lands inside the shard range, the unit is microseconds' FROM agg
UNION ALL SELECT 'item_3_timestamps', 'user_first_touch_timestamp_null_rows', first_touch_null_rows, NULL,
  'rows with no recorded first-touch timestamp' FROM agg
UNION ALL SELECT 'item_3_timestamps', 'rows_event_date_ne_shard_suffix', event_date_ne_shard, NULL,
  'event_date disagreeing with the shard it is stored in' FROM agg
UNION ALL SELECT 'item_3_timestamps', 'rows_event_date_ne_utc_date_of_timestamp', event_date_ne_utc_date, NULL,
  'event_date disagreeing with the UTC date implied by event_timestamp' FROM agg
UNION ALL SELECT 'item_3_timestamps', 'tz_offset_null_rows', tz_offset_null_rows, NULL,
  'device.time_zone_offset_seconds NULL' FROM agg
UNION ALL SELECT 'item_3_timestamps', 'tz_offset_distinct_values', tz_offset_distinct, NULL,
  'distinct device.time_zone_offset_seconds values; 1 or 0 means no usable local zone' FROM agg
UNION ALL SELECT 'item_3_timestamps', 'first_open_rows', first_open_rows, NULL,
  'first_open rows the gap distribution is computed over' FROM agg
UNION ALL SELECT 'item_3_timestamps', 'first_open_gap_seconds_min', fo_gap_seconds_q[OFFSET(0)], NULL,
  'first_open event_timestamp minus user_first_touch_timestamp, seconds' FROM agg
UNION ALL SELECT 'item_3_timestamps', 'first_open_gap_seconds_p50', fo_gap_seconds_q[OFFSET(50)], NULL,
  'median of the same gap' FROM agg
UNION ALL SELECT 'item_3_timestamps', 'first_open_gap_seconds_p99', fo_gap_seconds_q[OFFSET(99)], NULL,
  '99th percentile of the same gap' FROM agg
UNION ALL SELECT 'item_3_timestamps', 'first_open_gap_seconds_max', fo_gap_seconds_q[OFFSET(100)], NULL,
  'maximum of the same gap; 86400 seconds is one day' FROM agg
UNION ALL SELECT 'item_3_timestamps', 'first_open_gap_over_one_day_rows', fo_gap_over_one_day_rows, NULL,
  'first_open rows whose gap exceeds one day in absolute value' FROM agg
UNION ALL SELECT 'item_3_timestamps', 'first_open_gap_over_one_day_users', fo_gap_over_one_day_users, NULL,
  'distinct users behind those rows' FROM agg
UNION ALL SELECT 'item_3_timestamps', 'first_open_users_total', fo_users_total, NULL,
  'distinct users with at least one first_open; denominator for the share' FROM agg
UNION ALL SELECT 'item_3_timestamps', 'first_open_gap_over_one_day_share_ppm',
  CAST(ROUND(fo_gap_over_one_day_users * 1000000 / fo_users_total) AS INT64), NULL,
  'parts per million of users with a first_open; §10.2 item 3 fixes no threshold' FROM agg
UNION ALL SELECT 'item_3_timestamps', 'rows_event_date_one_day_behind_utc', event_date_minus_one_day, NULL,
  'event_date is the UTC date minus one day' FROM agg
UNION ALL SELECT 'item_3_timestamps', 'rows_event_date_same_as_utc', event_date_same_day, NULL,
  'event_date equals the UTC date' FROM agg
UNION ALL SELECT 'item_3_timestamps', 'rows_event_date_one_day_ahead_utc', event_date_plus_one_day, NULL,
  'event_date is the UTC date plus one day' FROM agg
ORDER BY section, metric
