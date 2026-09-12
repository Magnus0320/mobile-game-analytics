-- 09_recon_user_properties.sql
-- Recon checklist item 6, closing the one gap query 04 left open.
--
-- Query 04 enumerated all 52 distinct event_params keys over the full range and
-- found no session identifier. That establishes the absence across the EVENT
-- parameter vocabulary only. user_properties is a separate repeated field with
-- its own key space, and this export's schema is not the modern GA4 one, so a
-- session identifier living there is a real possibility rather than a pedantic
-- one. Item 6's verdict turns on the absence being complete, so the remaining
-- key space is enumerated rather than assumed empty.
--
-- As in query 04, EVERY distinct key is returned with its volumes and the value
-- slots it populates. No key is filtered on a judgement about what it means.
--
-- This is the tenth and last query of the pass, which is the ceiling §7.2 sets
-- for the 00-09 recon range. The pass ends here regardless of what this returns.
--
-- Columns read: user_properties, user_pseudo_id. Shard range 20180612-20181003.
--
-- Output columns: user_property_key, occurrences, distinct_users,
--                 with_string_value, with_int_value, with_float_value,
--                 with_double_value, with_set_timestamp

SELECT
  p.key                                             AS user_property_key,
  COUNT(*)                                          AS occurrences,
  COUNT(DISTINCT user_pseudo_id)                    AS distinct_users,
  COUNTIF(p.value.string_value IS NOT NULL)         AS with_string_value,
  COUNTIF(p.value.int_value    IS NOT NULL)         AS with_int_value,
  COUNTIF(p.value.float_value  IS NOT NULL)         AS with_float_value,
  COUNTIF(p.value.double_value IS NOT NULL)         AS with_double_value,
  COUNTIF(p.value.set_timestamp_micros IS NOT NULL) AS with_set_timestamp
FROM `firebase-public-project.analytics_153293282.events_*`,
     UNNEST(user_properties) AS p
WHERE _TABLE_SUFFIX BETWEEN '20180612' AND '20181003'
GROUP BY user_property_key
ORDER BY occurrences DESC
