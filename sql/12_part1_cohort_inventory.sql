-- 12_part1_cohort_inventory.sql
-- Part 1 output 2 (§10.5.7): the sixteen weekly cohorts with their install
-- counts, the excluded tail count, and per-horizon eligibility exactly as
-- §10.5.5 fixes it.
--
--   §10.5.4  Weeks are fixed 7-day blocks anchored at the first shard, not ISO
--            weeks. 114 days is 16 whole weeks plus 2 days, and the
--            20181002-20181003 tail is excluded from every cohort table with its
--            install count reported.
--   §10.5.5  A cohort is measurable at day N only if its LAST install day plus N
--            falls inside the window ending 20181003, giving cutoffs of
--            20181002 / 20180926 / 20180903 and 16 / 15 / 12 eligible cohorts.
--   A-134    The pooled denominator is the union of the cohorts eligible at that
--            horizon, as directed. The W16 installs of 20180925-20180926 are
--            individually observable at D7 but belong to a cohort that is not,
--            so they are excluded from pooled D7 -- and counted here rather than
--            disappearing.
--
-- THE ASSERTIONS ARE THE POINT OF THIS FILE, not decoration. Three ERROR()
-- guards sit in a WHERE clause, so they are evaluated before any row is
-- returned: the block boundaries, the three cutoff dates, and the 16/15/12
-- eligibility counts. If the arithmetic here ever disagrees with §10.5.5's
-- literals the query fails loudly rather than returning a table that quietly
-- means something else. A failure is an implementation defect on this side; the
-- document's numbers were verified independently before this session began.
--
-- Columns read: event_date, event_name, event_timestamp, user_pseudo_id.
-- Shard range 20180612-20181003.
--
-- Output columns: cohort, cohort_start, cohort_end, install_count,
--                 eligible_d1, eligible_d7, eligible_d30, note

WITH install_days AS (
  -- §10.7.4 de-duplication and A-137's install-day definition, in one pass.
  SELECT
    user_pseudo_id,
    PARSE_DATE('%Y%m%d',
      ARRAY_AGG(IF(event_name = 'first_open', event_date, NULL)
                IGNORE NULLS ORDER BY event_timestamp ASC, event_date ASC
                LIMIT 1)[OFFSET(0)]) AS install_day
  FROM (
    SELECT user_pseudo_id, event_name, event_timestamp, MIN(event_date) AS event_date
    FROM `firebase-public-project.analytics_153293282.events_*`
    WHERE _TABLE_SUFFIX BETWEEN '20180612' AND '20181003'
    GROUP BY user_pseudo_id, event_name, event_timestamp
  )
  WHERE event_name = 'first_open'
  GROUP BY user_pseudo_id
),

blocks AS (
  SELECT
    idx AS cohort_index,
    FORMAT('W%02d', idx) AS cohort,
    DATE_ADD(DATE '2018-06-12', INTERVAL (idx - 1) * 7 DAY) AS cohort_start,
    DATE_ADD(DATE '2018-06-12', INTERVAL (idx - 1) * 7 + 6 DAY) AS cohort_end
  FROM UNNEST(GENERATE_ARRAY(1, 16)) AS idx
),

assigned AS (
  SELECT
    install_day,
    DIV(DATE_DIFF(install_day, DATE '2018-06-12', DAY), 7) + 1 AS cohort_index
  FROM install_days
),

counts AS (
  SELECT cohort_index, COUNT(*) AS install_count
  FROM assigned
  GROUP BY cohort_index
),

assertions AS (
  SELECT
    IF((SELECT MIN(cohort_start) FROM blocks) = DATE '2018-06-12'
       AND (SELECT MAX(cohort_end) FROM blocks) = DATE '2018-10-01'
       AND (SELECT COUNT(*) FROM blocks) = 16
       AND (SELECT COUNT(*) FROM blocks WHERE DATE_DIFF(cohort_end, cohort_start, DAY) != 6) = 0,
       1,
       ERROR('§10.5.4 block assertion failed: the 16 anchored 7-day blocks must run W01 20180612-20180618 through W16 20180925-20181001'))
      AS blocks_ok,
    IF(DATE_SUB(DATE '2018-10-03', INTERVAL 1 DAY) = DATE '2018-10-02'
       AND DATE_SUB(DATE '2018-10-03', INTERVAL 7 DAY) = DATE '2018-09-26'
       AND DATE_SUB(DATE '2018-10-03', INTERVAL 30 DAY) = DATE '2018-09-03',
       1,
       ERROR('§10.5.5 cutoff assertion failed: window end 20181003 minus 1/7/30 days must be 20181002/20180926/20180903'))
      AS cutoffs_ok,
    IF((SELECT COUNTIF(DATE_ADD(cohort_end, INTERVAL 1 DAY) <= DATE '2018-10-03') FROM blocks) = 16
       AND (SELECT COUNTIF(DATE_ADD(cohort_end, INTERVAL 7 DAY) <= DATE '2018-10-03') FROM blocks) = 15
       AND (SELECT COUNTIF(DATE_ADD(cohort_end, INTERVAL 30 DAY) <= DATE '2018-10-03') FROM blocks) = 12,
       1,
       ERROR('§10.5.5 eligibility assertion failed: expected exactly 16/15/12 eligible cohorts at D1/D7/D30'))
      AS eligibility_ok
)

SELECT
  b.cohort,
  FORMAT_DATE('%Y%m%d', b.cohort_start) AS cohort_start,
  FORMAT_DATE('%Y%m%d', b.cohort_end)   AS cohort_end,
  IFNULL(c.install_count, 0)            AS install_count,
  DATE_ADD(b.cohort_end, INTERVAL 1 DAY)  <= DATE '2018-10-03' AS eligible_d1,
  DATE_ADD(b.cohort_end, INTERVAL 7 DAY)  <= DATE '2018-10-03' AS eligible_d7,
  DATE_ADD(b.cohort_end, INTERVAL 30 DAY) <= DATE '2018-10-03' AS eligible_d30,
  'weekly cohort, §10.5.4' AS note
FROM blocks b
LEFT JOIN counts c USING (cohort_index)
CROSS JOIN assertions a
WHERE a.blocks_ok + a.cutoffs_ok + a.eligibility_ok = 3

UNION ALL
SELECT
  'TAIL_EXCLUDED', '20181002', '20181003',
  (SELECT IFNULL(SUM(install_count), 0) FROM counts WHERE cohort_index = 17),
  FALSE, FALSE, FALSE,
  'the 2-day remainder, excluded from every cohort table per §10.5.4; reported as an excluded figure, never folded into W16'

UNION ALL
SELECT
  'W16_INSTALLS_20180925_20180926', '20180925', '20180926',
  (SELECT COUNT(*) FROM assigned WHERE cohort_index = 16 AND install_day <= DATE '2018-09-26'),
  TRUE, FALSE, FALSE,
  'installs individually observable at D7 (install day <= 20180926) whose cohort W16 is not; excluded from pooled D7 under the per-cohort reading directed in A-134'

ORDER BY cohort
