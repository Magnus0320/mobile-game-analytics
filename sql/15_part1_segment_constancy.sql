-- 15_part1_segment_constancy.sql
-- §10.7.5's constancy check, run BEFORE the segment query so that the country
-- gate is known before any segmented rate exists.
--
--   §10.7.5  "Report the share of users whose geo.country is not constant across
--            their events. Above 5.0%, country segmentation is reported with a
--            caveat naming the share; above 25.0%, country segmentation is
--            DROPPED." Those two triggers are defined for geo.country and this
--            query measures exactly what they test.
--   A-136    §10.7.5 also permits app_info.version as a segment dimension and
--            requires NO constancy test for it -- while an app version is the
--            field most likely to change across a 114-day window, and §10.7.5
--            attributes every segment from the user's earliest event row, so
--            "segment by app version" silently means "version at install". This
--            query therefore measures the same share for app_info.version and
--            reports it as a finding. The 5.0% and 25.0% triggers are NOT
--            applied to it: inventing a gate the document does not state is the
--            one response A-129's standing rule forbids. The number goes to the
--            architecture session so the decision is made with it in view.
--
-- Both shares are reported over two populations -- all 15,175 users, and Part 1's
-- install population -- because §10.7.5 states the rule for both parts without
-- naming a population, and Part 1 segments its own. The gate is read on Part 1's
-- population, which is the one being segmented here; both are printed so a reader
-- can see either.
--
-- De-duplication (§10.7.4, A-138) runs first: a duplicated log row is not an
-- observation, so it must not be able to make a user look inconstant.
--
-- Columns read: app_info.version, event_name, event_timestamp, geo.country,
-- user_pseudo_id. Shard range 20180612-20181003.
--
-- Output columns: section, metric, value_num, value_text, note

WITH deduped AS (
  SELECT
    user_pseudo_id,
    event_name,
    event_timestamp,
    MIN(geo.country)      AS country,
    MIN(app_info.version) AS app_version
  FROM `firebase-public-project.analytics_153293282.events_*`
  WHERE _TABLE_SUFFIX BETWEEN '20180612' AND '20181003'
  GROUP BY user_pseudo_id, event_name, event_timestamp
),

per_user AS (
  SELECT
    user_pseudo_id,
    LOGICAL_OR(event_name = 'first_open') AS has_first_open,
    COUNT(DISTINCT country)     AS distinct_country,
    COUNT(DISTINCT app_version) AS distinct_app_version,
    COUNTIF(country IS NULL)     AS rows_null_country,
    COUNTIF(app_version IS NULL) AS rows_null_app_version
  FROM deduped
  GROUP BY user_pseudo_id
),

agg AS (
  SELECT
    COUNT(*)                                          AS users_all,
    COUNTIF(has_first_open)                           AS users_part1,

    COUNTIF(distinct_country > 1)                     AS nonconstant_country_all,
    COUNTIF(distinct_country > 1 AND has_first_open)  AS nonconstant_country_part1,
    MAX(distinct_country)                             AS max_distinct_country,
    COUNTIF(rows_null_country > 0)                    AS users_with_null_country_rows,

    COUNTIF(distinct_app_version > 1)                    AS nonconstant_app_version_all,
    COUNTIF(distinct_app_version > 1 AND has_first_open) AS nonconstant_app_version_part1,
    MAX(distinct_app_version)                            AS max_distinct_app_version,
    COUNTIF(rows_null_app_version > 0)                   AS users_with_null_app_version_rows,

    COUNTIF(distinct_app_version = 2)                    AS users_app_version_2,
    COUNTIF(distinct_app_version = 3)                    AS users_app_version_3,
    COUNTIF(distinct_app_version >= 4)                   AS users_app_version_4_plus,
    COUNTIF(distinct_country = 2)                        AS users_country_2,
    COUNTIF(distinct_country >= 3)                       AS users_country_3_plus
  FROM per_user
)

SELECT 'population' AS section, 'users_all' AS metric,
       users_all AS value_num, CAST(NULL AS STRING) AS value_text,
       'all distinct user_pseudo_id in the shard range' AS note
FROM agg
UNION ALL SELECT 'population', 'users_part1_install_population', users_part1, NULL,
  'users with at least one first_open event (§10.5.1); the population Part 1 segments' FROM agg

UNION ALL SELECT 'geo_country', 'users_non_constant_all', nonconstant_country_all, NULL,
  'users with more than one distinct geo.country across their deduped events' FROM agg
UNION ALL SELECT 'geo_country', 'users_non_constant_part1', nonconstant_country_part1, NULL,
  'the same, restricted to Part 1 install population' FROM agg
UNION ALL SELECT 'geo_country', 'share_non_constant_all_ppm',
  CAST(ROUND(nonconstant_country_all * 1000000 / users_all) AS INT64), NULL,
  'parts per million; §10.7.5 caveats above 5.0% = 50000 ppm and drops above 25.0% = 250000 ppm' FROM agg
UNION ALL SELECT 'geo_country', 'share_non_constant_part1_ppm',
  CAST(ROUND(nonconstant_country_part1 * 1000000 / users_part1) AS INT64), NULL,
  'parts per million of the Part 1 install population; this is the share the §10.7.5 triggers are read on' FROM agg
UNION ALL SELECT 'geo_country', 'max_distinct_values_per_user', max_distinct_country, NULL,
  'largest number of distinct countries held by one user' FROM agg
UNION ALL SELECT 'geo_country', 'users_with_two_values', users_country_2, NULL,
  'distribution detail' FROM agg
UNION ALL SELECT 'geo_country', 'users_with_three_or_more_values', users_country_3_plus, NULL,
  'distribution detail' FROM agg
UNION ALL SELECT 'geo_country', 'users_with_any_null_row', users_with_null_country_rows, NULL,
  'A-108 measured geo.country at 0% null over rows' FROM agg

UNION ALL SELECT 'app_info_version', 'users_non_constant_all', nonconstant_app_version_all, NULL,
  'A-136: measured and reported, with NO §10.7.5 trigger applied -- the document states none for this dimension' FROM agg
UNION ALL SELECT 'app_info_version', 'users_non_constant_part1', nonconstant_app_version_part1, NULL,
  'the same, restricted to Part 1 install population' FROM agg
UNION ALL SELECT 'app_info_version', 'share_non_constant_all_ppm',
  CAST(ROUND(nonconstant_app_version_all * 1000000 / users_all) AS INT64), NULL,
  'parts per million; reported for the architecture session, not tested against any threshold' FROM agg
UNION ALL SELECT 'app_info_version', 'share_non_constant_part1_ppm',
  CAST(ROUND(nonconstant_app_version_part1 * 1000000 / users_part1) AS INT64), NULL,
  'parts per million of the Part 1 install population' FROM agg
UNION ALL SELECT 'app_info_version', 'max_distinct_values_per_user', max_distinct_app_version, NULL,
  'largest number of distinct app versions held by one user' FROM agg
UNION ALL SELECT 'app_info_version', 'users_with_two_values', users_app_version_2, NULL,
  'distribution detail' FROM agg
UNION ALL SELECT 'app_info_version', 'users_with_three_values', users_app_version_3, NULL,
  'distribution detail' FROM agg
UNION ALL SELECT 'app_info_version', 'users_with_four_or_more_values', users_app_version_4_plus, NULL,
  'distribution detail' FROM agg
UNION ALL SELECT 'app_info_version', 'users_with_any_null_row', users_with_null_app_version_rows, NULL,
  'A-108 measured app_info.version at 0% null over rows' FROM agg
ORDER BY section, metric
