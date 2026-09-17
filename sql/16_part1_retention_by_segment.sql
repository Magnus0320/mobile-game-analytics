-- 16_part1_retention_by_segment.sql
-- Part 1 output 6 (§10.5.7): retention by segment, pooled only.
--
--   §10.7.5  Permitted dimensions, and only these five: geo.country (155 values,
--            0% null), platform, device.category, device.language,
--            app_info.version. geo.region is dropped at 88.57% null and
--            traffic_source.* is dropped at 99.4-99.9% two-bucket concentration;
--            neither appears here, and no metric is segmented by them.
--            Attribution is by the user's EARLIEST EVENT ROW, ties broken by
--            lowest event_timestamp then by alphabetically lowest event_name.
--            Segmentation applies to POOLED cohorts only and is never crossed
--            with the weekly cohorts -- about 54 users per cell would fall below
--            §10.5.3's suppression floor for most cells.
--   A-140    The >= 100-user floor is evaluated ONCE, on the pooled install
--            population of the sixteen weekly cohorts, so that segment
--            membership and the single "Other" row are identical across D1, D7
--            and D30 and the three columns can be read across. Sub-floor segments
--            are pooled into one Other row with its own count and the number of
--            segments pooled -- never dropped, never itemised (§10.7.5).
--   A-134    Each horizon's denominator is the segment's users whose COHORT is
--            eligible at that horizon, the same per-cohort rule the pooled
--            retention tables use, so the segment denominators sum to the pooled
--            denominator at every horizon.
--   §10.5.3  Classic retention only -- the primary. Rolling stays in its own
--            labelled table (query 14). Suppression at n<30 and the Wilson
--            interval are Python's (A-139); this query returns integers.
--
-- Columns read: app_info.version, device.category, device.language, event_date,
-- event_name, event_timestamp, geo.country, platform, user_pseudo_id.
-- Shard range 20180612-20181003.
--
-- Output columns: dimension, segment, is_other, segments_pooled,
--                 users_in_segment, horizon_days, denominator, retained

WITH deduped AS (
  SELECT
    user_pseudo_id,
    event_name,
    event_timestamp,
    MIN(event_date)         AS event_date,
    MIN(geo.country)        AS country,
    MIN(platform)           AS platform,
    MIN(device.category)    AS device_category,
    MIN(device.language)    AS device_language,
    MIN(app_info.version)   AS app_version
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
                LIMIT 1)[SAFE_OFFSET(0)])                AS install_day,
    ARRAY_AGG(DISTINCT PARSE_DATE('%Y%m%d', event_date)) AS active_days,
    -- §10.7.5's attribution rule, literally: earliest event row, ties by lowest
    -- event_timestamp then alphabetically lowest event_name.
    ARRAY_AGG(STRUCT(country, platform, device_category, device_language, app_version)
              ORDER BY event_timestamp ASC, event_name ASC
              LIMIT 1)[OFFSET(0)]                        AS seg
  FROM deduped
  GROUP BY user_pseudo_id
),

cohorted AS (
  SELECT
    install_day,
    active_days,
    seg,
    DIV(DATE_DIFF(install_day, DATE '2018-06-12', DAY), 7) + 1 AS cohort_index
  FROM per_user
  WHERE install_day IS NOT NULL
),

-- The sixteen weekly cohorts only: the 20181002-03 tail is excluded from every
-- cohort table (§10.5.4), and the pooled population is what the floor is read on.
in_population AS (
  SELECT * FROM cohorted WHERE cohort_index BETWEEN 1 AND 16
),

seg_long AS (
  SELECT
    p.install_day, p.active_days, p.cohort_index,
    d.dimension, d.value
  FROM in_population p,
       UNNEST([STRUCT('geo.country'      AS dimension, p.seg.country         AS value),
               STRUCT('platform',              p.seg.platform),
               STRUCT('device.category',       p.seg.device_category),
               STRUCT('device.language',       p.seg.device_language),
               STRUCT('app_info.version',      p.seg.app_version)]) AS d
),

floor_counts AS (
  SELECT dimension, value, COUNT(*) AS users_in_value
  FROM seg_long
  GROUP BY dimension, value
),

labelled AS (
  SELECT
    s.*,
    -- A-140: the floor is applied once, here, on the pooled install population.
    IF(f.users_in_value >= 100, s.value, 'Other') AS segment,
    f.users_in_value >= 100                       AS above_floor
  FROM seg_long s
  JOIN floor_counts f USING (dimension, value)
)

SELECT
  dimension,
  segment,
  NOT LOGICAL_OR(above_floor)                                   AS is_other,
  COUNT(DISTINCT IF(above_floor, NULL, value))                  AS segments_pooled,
  COUNT(*)                                                      AS users_in_segment,
  h                                                             AS horizon_days,
  COUNTIF(DATE_ADD(DATE_ADD(DATE '2018-06-12',
            INTERVAL (cohort_index - 1) * 7 + 6 DAY),
            INTERVAL h DAY) <= DATE '2018-10-03')               AS denominator,
  COUNTIF(DATE_ADD(DATE_ADD(DATE '2018-06-12',
            INTERVAL (cohort_index - 1) * 7 + 6 DAY),
            INTERVAL h DAY) <= DATE '2018-10-03'
          AND DATE_ADD(install_day, INTERVAL h DAY) IN UNNEST(active_days))
                                                                AS retained
FROM labelled, UNNEST([1, 7, 30]) AS h
GROUP BY dimension, segment, horizon_days
ORDER BY dimension, is_other, users_in_segment DESC, segment, horizon_days
