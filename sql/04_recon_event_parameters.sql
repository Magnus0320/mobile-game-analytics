-- 04_recon_event_parameters.sql
-- Recon checklist item 6, in part: the complete distinct event_params key list
-- with volumes, and the coverage of ga_session_id.
--
-- On "engagement-related event parameters": item 6 asks for the distinct list of
-- those. Deciding which parameters count as engagement-related is a judgement
-- about meaning, and this session is barred from making the ones that shade into
-- metric definition (§10.4). This query therefore returns EVERY distinct
-- parameter key with its volumes -- a superset that contains the answer and
-- selects nothing. The architecture session picks from a complete list.
--
-- Which value slot each key populates is reported too, because a key whose
-- values are entirely null in every slot is present in name only, and that is
-- the same placeholder problem item 13 exists to catch.
--
-- This query runs before the revenue query so that item 9 can be aimed at a
-- parameter key if one turns out to carry revenue, rather than assuming
-- event_value_in_usd is the only candidate.
--
-- Columns read: event_params, event_name, user_pseudo_id.
-- Shard range 20180612-20181003, the 114 contiguous shards query 00 established.
--
-- Output columns: param_key, occurrences, distinct_event_names, distinct_users,
--                 with_string_value, with_int_value, with_float_value,
--                 with_double_value

WITH base AS (
  SELECT
    event_name,
    user_pseudo_id,
    event_params
  FROM `firebase-public-project.analytics_153293282.events_*`
  WHERE _TABLE_SUFFIX BETWEEN '20180612' AND '20181003'
)

SELECT
  p.key                                          AS param_key,
  COUNT(*)                                       AS occurrences,
  COUNT(DISTINCT event_name)                     AS distinct_event_names,
  COUNT(DISTINCT user_pseudo_id)                 AS distinct_users,
  COUNTIF(p.value.string_value IS NOT NULL)      AS with_string_value,
  COUNTIF(p.value.int_value    IS NOT NULL)      AS with_int_value,
  COUNTIF(p.value.float_value  IS NOT NULL)      AS with_float_value,
  COUNTIF(p.value.double_value IS NOT NULL)      AS with_double_value
FROM base, UNNEST(event_params) AS p
GROUP BY param_key
ORDER BY occurrences DESC
