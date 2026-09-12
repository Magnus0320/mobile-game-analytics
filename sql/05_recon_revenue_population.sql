-- 05_recon_revenue_population.sql
-- Recon checklist item 9: which purchase-shaped events exist, and are their
-- revenue values actually populated rather than zero or null?
--
-- This is the sole input to ARCHITECTURE.md §10.3's scope rule for Part 2, and
-- §10.3 forbids adjusting the purchase-event set to clear a threshold. This
-- query therefore computes the revenue columns for EVERY event name in the
-- vocabulary, not for a candidate set chosen by this session. The set is then a
-- visible selection from a complete table rather than a choice made here.
--
-- spend_virtual_currency appears as its own row and is explicitly NOT revenue
-- (§10.2 item 9): it is a soft-currency sink, and counting it as monetization is
-- how an unmonetized sample comes to look monetized.
--
-- Three candidate revenue carriers, established by queries 01 and 04 rather than
-- assumed:
--   event_value_in_usd   FLOAT64, top level -- present on only 99 of the 114
--                        shards (absent 20180612-20180626), so a null on an
--                        early shard means the COLUMN IS ABSENT, not that no
--                        revenue occurred. events_on_shards_with_usd_column
--                        carries the denominator that caveat needs.
--   price parameter      int_value, carried by in_app_purchase only (query 04)
--   user_ltv.revenue     FLOAT64, all shards -- a running per-user lifetime
--                        value carried on every row, NOT an event-level revenue
--                        figure. Reported as a diagnostic only; it must not be
--                        summed as purchase revenue.
--
-- "Revenue-positive" throughout means non-null AND strictly greater than zero.
--
-- Columns read: event_name, user_pseudo_id, event_value_in_usd, user_ltv.revenue,
-- event_params. Shard range 20180612-20181003.
--
-- Output columns: event_name, events, distinct_users,
--                 events_on_shards_with_usd_column,
--                 usd_positive_events, usd_positive_users,
--                 price_param_positive_events, price_param_positive_users,
--                 ltv_revenue_positive_events, ltv_revenue_positive_users

WITH base AS (
  SELECT
    event_name,
    user_pseudo_id,
    _TABLE_SUFFIX AS shard_suffix,
    event_value_in_usd,
    user_ltv.revenue AS ltv_revenue,
    (SELECT p.value.int_value
     FROM UNNEST(event_params) AS p
     WHERE p.key = 'price')                       AS price_param
  FROM `firebase-public-project.analytics_153293282.events_*`
  WHERE _TABLE_SUFFIX BETWEEN '20180612' AND '20181003'
),

per_event AS (
  SELECT
    event_name,
    COUNT(*)                                                          AS events,
    COUNT(DISTINCT user_pseudo_id)                                    AS distinct_users,
    COUNTIF(shard_suffix >= '20180627')                               AS events_on_shards_with_usd_column,
    COUNTIF(event_value_in_usd > 0)                                   AS usd_positive_events,
    COUNT(DISTINCT IF(event_value_in_usd > 0, user_pseudo_id, NULL))  AS usd_positive_users,
    COUNTIF(price_param > 0)                                          AS price_param_positive_events,
    COUNT(DISTINCT IF(price_param > 0, user_pseudo_id, NULL))         AS price_param_positive_users,
    COUNTIF(ltv_revenue > 0)                                          AS ltv_revenue_positive_events,
    COUNT(DISTINCT IF(ltv_revenue > 0, user_pseudo_id, NULL))         AS ltv_revenue_positive_users
  FROM base
  GROUP BY event_name
),

all_events AS (
  SELECT
    '__ALL_EVENTS__'                                                  AS event_name,
    COUNT(*)                                                          AS events,
    COUNT(DISTINCT user_pseudo_id)                                    AS distinct_users,
    COUNTIF(shard_suffix >= '20180627')                               AS events_on_shards_with_usd_column,
    COUNTIF(event_value_in_usd > 0)                                   AS usd_positive_events,
    COUNT(DISTINCT IF(event_value_in_usd > 0, user_pseudo_id, NULL))  AS usd_positive_users,
    COUNTIF(price_param > 0)                                          AS price_param_positive_events,
    COUNT(DISTINCT IF(price_param > 0, user_pseudo_id, NULL))         AS price_param_positive_users,
    COUNTIF(ltv_revenue > 0)                                          AS ltv_revenue_positive_events,
    COUNT(DISTINCT IF(ltv_revenue > 0, user_pseudo_id, NULL))         AS ltv_revenue_positive_users
  FROM base
)

SELECT * FROM per_event
UNION ALL
SELECT * FROM all_events
ORDER BY
  IF(event_name = '__ALL_EVENTS__', 0, 1),
  price_param_positive_events DESC,
  usd_positive_events DESC,
  events DESC
