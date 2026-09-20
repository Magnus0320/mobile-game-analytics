-- 31_part2_progression_matrix_and_funnel.sql
-- Part 2's funnel, and the one table every count in it can be re-added from.
--
--   §10.6.2  Population: ALL 15,175 users with at least one event in the range.
--            Counting unit: PER USER. first_open is not a step; the funnel
--            begins at "present in the window", so S0 is the whole population.
--   §10.6.3  The four steps, fixed by the document and untouched here:
--              S0 present (15,175) -> S1 level_start_quickplay (10,166)
--              -> S2 level_end_quickplay (8,168)
--              -> S3 level_complete_quickplay (5,676)
--   §10.6.4  The funnel is STRICT: step k's population is users holding ALL of
--            S0..Sk. Raw per-step counts are reported beside the strict ones.
--            Out-of-order users -- S2 without S1, S3 without S2 -- are counted
--            and reported; A-170 tests their share against the step's own raw
--            population and prints s3_without_s1 beside them for legibility.
--   §10.6.5  The level_end reconciliation at USER level. A-164 is a CHALLENGE:
--            the event-level formula does not translate, because
--            users(complete) + users(fail) double-counts anyone holding both.
--            The directed reading is "ends with no outcome, over S2"; the
--            components of all three readings are returned so any of them can
--            be reconstructed.
--   A-172    level_start -- the NON-quickplay progression track -- rides along
--            as a labelled diagnostic flag and is NEVER a step. It reads
--            event_name, which this query already scans, so it costs no
--            additional bytes. It exists to bound what S1's share means for the
--            users who played the other mode.
--   A-171    The ERROR() guard asserts §10.6.3's four raw per-user counts. They
--            are invariant under §10.7.4, because a duplicate row carries the
--            same user and event name as its twin, so the guard can only fail
--            if this query is wrong. If it fires, that is an implementation
--            defect and it stops the run.
--
-- Every marginal below is computed in SQL (§7.3) AND is a sum over the pattern
-- matrix, so the two derivations cross-check each other in verify.py.
--
-- Columns read: user_pseudo_id, event_name, event_timestamp.
-- Shard range 20180612-20181003.
--
-- Output columns: section, key, users, s1, s2, s3, fail_quickplay, np_start

WITH deduped AS (
  SELECT user_pseudo_id, event_name, event_timestamp
  FROM `firebase-public-project.analytics_153293282.events_*`
  WHERE _TABLE_SUFFIX BETWEEN '20180612' AND '20181003'
  GROUP BY user_pseudo_id, event_name, event_timestamp
),

-- Whole-window presence, per user (§10.6.2). No day key is involved: a user
-- either has the event somewhere in the range or does not, which is why
-- §10.5.5's eligibility and §10.5.3's window-remaining columns do not reach
-- Part 2 (§10.6's head note, A-159).
per_user AS (
  SELECT
    user_pseudo_id,
    LOGICAL_OR(event_name = 'level_start_quickplay')    AS s1,
    LOGICAL_OR(event_name = 'level_end_quickplay')      AS s2,
    LOGICAL_OR(event_name = 'level_complete_quickplay') AS s3,
    LOGICAL_OR(event_name = 'level_fail_quickplay')     AS fail_quickplay,
    LOGICAL_OR(event_name = 'level_start')              AS np_start
  FROM deduped
  GROUP BY user_pseudo_id
),

marginals AS (
  SELECT
    -- §10.6.3's raw per-step counts
    COUNT(*)                                       AS raw_s0,
    COUNTIF(s1)                                    AS raw_s1,
    COUNTIF(s2)                                    AS raw_s2,
    COUNTIF(s3)                                    AS raw_s3,
    -- §10.6.4's strict cumulative counts: all of S0..Sk
    COUNT(*)                                       AS strict_s0,
    COUNTIF(s1)                                    AS strict_s1,
    COUNTIF(s1 AND s2)                             AS strict_s2,
    COUNTIF(s1 AND s2 AND s3)                      AS strict_s3,
    -- §10.6.4's out-of-order users
    COUNTIF(s2 AND NOT s1)                         AS s2_without_s1,
    COUNTIF(s3 AND NOT s2)                         AS s3_without_s2,
    COUNTIF(s3 AND NOT s1)                         AS s3_without_s1,
    -- §10.6.5 at user level: the components of A-164's three readings
    COUNTIF(s2)                                    AS users_end,
    COUNTIF(s3)                                    AS users_complete,
    COUNTIF(fail_quickplay)                        AS users_fail,
    COUNTIF(s3 OR fail_quickplay)                  AS users_complete_or_fail,
    COUNTIF(s3 AND fail_quickplay)                 AS users_complete_and_fail,
    COUNTIF(s2 AND NOT s3 AND NOT fail_quickplay)  AS end_without_outcome,
    COUNTIF((s3 OR fail_quickplay) AND NOT s2)     AS outcome_without_end,
    -- A-172's parallel track, diagnostic only
    COUNTIF(np_start)                              AS np_users,
    COUNTIF(NOT s1)                                AS users_without_s1,
    COUNTIF(NOT s1 AND np_start)                   AS users_without_s1_with_np,
    COUNTIF(s1 AND np_start)                       AS users_in_both_modes,
    COUNTIF(NOT s1 AND NOT np_start)               AS users_with_neither_start
  FROM per_user
),

guard AS (
  SELECT IF(raw_s0 = 15175 AND raw_s1 = 10166 AND raw_s2 = 8168 AND raw_s3 = 5676, TRUE,
    ERROR(FORMAT(
      'A-171 guard failed: raw per-user counts %d / %d / %d / %d, §10.6.3 expects 15175 / 10166 / 8168 / 5676. Distinct-user counts are invariant under §10.7.4 de-duplication, so this is an implementation defect and stops the run, not evidence against the recon.',
      raw_s0, raw_s1, raw_s2, raw_s3))) AS ok
  FROM marginals
),

pattern AS (
  SELECT
    'pattern' AS section,
    FORMAT('s1=%d s2=%d s3=%d fail=%d np=%d',
           CAST(s1 AS INT64), CAST(s2 AS INT64), CAST(s3 AS INT64),
           CAST(fail_quickplay AS INT64), CAST(np_start AS INT64)) AS key,
    COUNT(*) AS users,
    s1, s2, s3, fail_quickplay, np_start
  FROM per_user
  GROUP BY s1, s2, s3, fail_quickplay, np_start
),

scalars AS (
  SELECT u.section, u.key, u.users
  FROM marginals,
       UNNEST([
         STRUCT('funnel_raw'        AS section, 'S0' AS key, raw_s0    AS users),
         STRUCT('funnel_raw',            'S1', raw_s1),
         STRUCT('funnel_raw',            'S2', raw_s2),
         STRUCT('funnel_raw',            'S3', raw_s3),
         STRUCT('funnel_strict',         'S0', strict_s0),
         STRUCT('funnel_strict',         'S1', strict_s1),
         STRUCT('funnel_strict',         'S2', strict_s2),
         STRUCT('funnel_strict',         'S3', strict_s3),
         STRUCT('out_of_order',          's2_without_s1', s2_without_s1),
         STRUCT('out_of_order',          's3_without_s2', s3_without_s2),
         STRUCT('out_of_order',          's3_without_s1', s3_without_s1),
         STRUCT('level_end_user',        'users_end', users_end),
         STRUCT('level_end_user',        'users_complete', users_complete),
         STRUCT('level_end_user',        'users_fail', users_fail),
         STRUCT('level_end_user',        'users_complete_or_fail', users_complete_or_fail),
         STRUCT('level_end_user',        'users_complete_and_fail', users_complete_and_fail),
         STRUCT('level_end_user',        'end_without_outcome', end_without_outcome),
         STRUCT('level_end_user',        'outcome_without_end', outcome_without_end),
         STRUCT('parallel_track',        'users_nonquickplay_start', np_users),
         STRUCT('parallel_track',        'users_without_s1', users_without_s1),
         STRUCT('parallel_track',        'users_without_s1_with_nonquickplay_start', users_without_s1_with_np),
         STRUCT('parallel_track',        'users_in_both_modes', users_in_both_modes),
         STRUCT('parallel_track',        'users_with_neither_start', users_with_neither_start)
       ]) AS u
),

rows_out AS (
  SELECT section, key, users,
         CAST(NULL AS BOOL) AS s1, CAST(NULL AS BOOL) AS s2, CAST(NULL AS BOOL) AS s3,
         CAST(NULL AS BOOL) AS fail_quickplay, CAST(NULL AS BOOL) AS np_start
  FROM scalars
  UNION ALL
  SELECT section, key, users, s1, s2, s3, fail_quickplay, np_start FROM pattern
)

SELECT r.section, r.key, r.users, r.s1, r.s2, r.s3, r.fail_quickplay, r.np_start
FROM rows_out r
CROSS JOIN guard g
WHERE g.ok
ORDER BY
  CASE r.section
    WHEN 'funnel_raw' THEN 0 WHEN 'funnel_strict' THEN 1
    WHEN 'out_of_order' THEN 2 WHEN 'level_end_user' THEN 3
    WHEN 'parallel_track' THEN 4 ELSE 5 END,
  r.users DESC,
  r.key
