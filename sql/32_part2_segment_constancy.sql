-- 32_part2_segment_constancy.sql
-- §10.7.5 as generalised by A-154: the non-constant share for EVERY permitted
-- segment dimension, on Part 2's own population.
--
--   §10.7.5  Five permitted dimensions and only these: geo.country (155 values,
--            0% null), platform, device.category, device.language,
--            app_info.version. geo.region is dropped at 88.57% null and
--            traffic_source.* at 99.4-99.9% two-bucket concentration; neither
--            appears here and no metric is segmented by them (A-168 quotes the
--            recon's committed profiles for the descriptive line that documents
--            why).
--   A-154    v1.5 required this test for geo.country alone -- the dimension
--            where instability is LEAST likely -- and omitted it from
--            app_info.version, where it is most likely. v1.6 applies the 5.0%
--            caveat trigger and the 25.0% drop trigger PER DIMENSION,
--            independently. This query measures all five; A-169 applies the
--            triggers in the rendering layer, so no query text depends on a
--            number a query produced.
--   A-169    Part 1 measured 1.62% (geo.country) and 1.97% (app_info.version) on
--            its 4,319-user INSTALL population. Part 2's population is all
--            15,175 and includes the 10,856 users whose installs predate the
--            window, whose longer observed lives make a higher share plausible.
--            The shares are not transferable and are re-measured here.
--
-- A user is non-constant on a dimension if they carry more than one distinct
-- value across their own (de-duplicated) event rows. NULL is folded to a
-- sentinel rather than skipped, because a field null on some of a user's rows
-- and populated on others IS non-constancy, and COUNT(DISTINCT) would hide it.
-- users_with_any_null is returned so that case is visible if it occurs.
--
-- SQL returns integers only; the share is formed once, in Python (§7.3, A-163).
--
-- Columns read: user_pseudo_id, event_name, event_timestamp, geo.country,
-- platform, device.category, device.language, app_info.version.
-- Shard range 20180612-20181003.
--
-- Output columns: dimension, users_total, users_non_constant,
--                 max_distinct_per_user, users_with_any_null,
--                 distinct_values_overall

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

seg_long AS (
  SELECT
    d.user_pseudo_id,
    u.dimension,
    IFNULL(u.value, '(null)') AS value
  FROM deduped d,
       UNNEST([STRUCT('geo.country'      AS dimension, d.country         AS value),
               STRUCT('platform',              d.platform),
               STRUCT('device.category',       d.device_category),
               STRUCT('device.language',       d.device_language),
               STRUCT('app_info.version',      d.app_version)]) AS u
),

per_user_dim AS (
  SELECT
    dimension,
    user_pseudo_id,
    COUNT(DISTINCT value)           AS n_values,
    LOGICAL_OR(value = '(null)')    AS has_null
  FROM seg_long
  GROUP BY dimension, user_pseudo_id
),

overall AS (
  SELECT dimension, COUNT(DISTINCT value) AS distinct_values_overall
  FROM seg_long
  GROUP BY dimension
)

SELECT
  p.dimension,
  COUNT(*)                        AS users_total,
  COUNTIF(p.n_values > 1)         AS users_non_constant,
  MAX(p.n_values)                 AS max_distinct_per_user,
  COUNTIF(p.has_null)             AS users_with_any_null,
  ANY_VALUE(o.distinct_values_overall) AS distinct_values_overall
FROM per_user_dim p
JOIN overall o USING (dimension)
GROUP BY p.dimension
ORDER BY p.dimension
