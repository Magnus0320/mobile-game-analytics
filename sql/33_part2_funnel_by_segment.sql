-- 33_part2_funnel_by_segment.sql
-- Part 2 output 5 (§10.6.6): the strict funnel by segment.
--
--   §10.7.5  Attribution is by the user's EARLIEST EVENT ROW, ties broken by
--            lowest event_timestamp then by alphabetically lowest event_name.
--            One deterministic rule for both parts.
--   A-154    Under that rule, "segment by app_info.version" means VERSION AT
--            INSTALL and "segment by device.language" means LANGUAGE AT FIRST
--            OBSERVED EVENT. A-174 requires the table's own caption to say so,
--            because a committed table is read on its own.
--   A-174    §10.7.5's floor -- a segment is reported individually only at
--            >= 200 users at S0, of 15,175 -- is evaluated ONCE, on S0, so that
--            segment membership and the single "Other (n segments)" row are
--            identical across S1, S2 and S3 and the columns can be read across.
--            Sub-floor segments are pooled into that one row with its own count
--            and the number of segments pooled: never dropped, never itemised.
--   §10.6.4  The funnel is strict, so a segment's S2 is users holding S1 AND S2
--            and its S3 is users holding S1 AND S2 AND S3. Raw per-step counts
--            are returned beside them so the segment table carries the same
--            strict/raw pair the pooled table does.
--   A-169    All five dimensions are computed unconditionally. §10.7.5's 5.0%
--            caveat and 25.0% drop triggers are applied in the rendering layer
--            from query 32's shares, so no line of this file depends on a
--            number any query produced.
--   §10.5.3  Suppression at n < 30 and the Wilson interval are Python's
--            (A-163); this query returns integers.
--
-- Columns read: user_pseudo_id, event_name, event_timestamp, geo.country,
-- platform, device.category, device.language, app_info.version.
-- Shard range 20180612-20181003.
--
-- Output columns: dimension, segment, is_other, segments_pooled, users_s0,
--                 strict_s1, strict_s2, strict_s3, raw_s1, raw_s2, raw_s3

WITH deduped AS (
  SELECT
    user_pseudo_id,
    event_name,
    event_timestamp,
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
    LOGICAL_OR(event_name = 'level_start_quickplay')    AS s1,
    LOGICAL_OR(event_name = 'level_end_quickplay')      AS s2,
    LOGICAL_OR(event_name = 'level_complete_quickplay') AS s3,
    -- §10.7.5's attribution rule, literally: earliest event row, ties by lowest
    -- event_timestamp then alphabetically lowest event_name.
    ARRAY_AGG(STRUCT(country, platform, device_category, device_language, app_version)
              ORDER BY event_timestamp ASC, event_name ASC
              LIMIT 1)[OFFSET(0)]                       AS seg
  FROM deduped
  GROUP BY user_pseudo_id
),

seg_long AS (
  SELECT
    p.s1, p.s2, p.s3,
    u.dimension, u.value
  FROM per_user p,
       UNNEST([STRUCT('geo.country'      AS dimension, p.seg.country         AS value),
               STRUCT('platform',              p.seg.platform),
               STRUCT('device.category',       p.seg.device_category),
               STRUCT('device.language',       p.seg.device_language),
               STRUCT('app_info.version',      p.seg.app_version)]) AS u
),

floor_counts AS (
  SELECT dimension, value, COUNT(*) AS users_in_value
  FROM seg_long
  GROUP BY dimension, value
),

labelled AS (
  SELECT
    s.*,
    -- A-174: the floor is applied once, here, on S0.
    IF(f.users_in_value >= 200, s.value, 'Other') AS segment,
    f.users_in_value >= 200                       AS above_floor
  FROM seg_long s
  JOIN floor_counts f USING (dimension, value)
)

SELECT
  dimension,
  segment,
  NOT LOGICAL_OR(above_floor)                    AS is_other,
  COUNT(DISTINCT IF(above_floor, NULL, value))   AS segments_pooled,
  COUNT(*)                                       AS users_s0,
  COUNTIF(s1)                                    AS strict_s1,
  COUNTIF(s1 AND s2)                             AS strict_s2,
  COUNTIF(s1 AND s2 AND s3)                      AS strict_s3,
  COUNTIF(s1)                                    AS raw_s1,
  COUNTIF(s2)                                    AS raw_s2,
  COUNTIF(s3)                                    AS raw_s3
FROM labelled
GROUP BY dimension, segment
ORDER BY dimension, is_other, users_s0 DESC, segment
