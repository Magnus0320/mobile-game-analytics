"""Build the derived-figure register (§7.5, A-158, A-165).

Every figure the report is allowed to quote gets a row here. A QUOTED row is
built by reading its declared cell; a DERIVED row is computed from declared cells
and becomes a committed cell of its own. After this module runs there is no
second class of figure for an audit to miss.
"""

from . import config as C
from .report_figures import Register

P1 = "part2_01_population_reconciliation.csv"
P2 = "part2_02_data_handling.csv"
P3 = "part2_03_funnel.csv"
P4 = "part2_04_out_of_order.csv"
P6 = "part2_06_diagnostic_events.csv"
P7 = "part2_07_level_end_reconciliation.csv"
P8 = "part2_08_segment_constancy.csv"
P9 = "part2_09_funnel_by_segment.csv"
P10 = "part2_10_parallel_track.csv"
LEDGER = "part2_budget_ledger.csv"
RECON0 = "recon_00_shard_inventory.csv"
PART1_DH = "part1_08_data_handling.csv"


def build(stats: dict) -> Register:
    r = Register()
    pop, funnel, ooo = stats["population"], stats["funnel"], stats["out_of_order"]
    lend, track, seg = stats["level_end"], stats["parallel_track"], stats["segments"]
    constancy, handling = stats["constancy"], stats["handling"]

    # --- population and the sample ------------------------------------------
    r.quoted("pop_users", f"{P1}:users:metric=distinct users with at least one event in the window",
             "count", "Every distinct user_pseudo_id with at least one event in the window: §10.6.2's funnel population")
    r.quoted("pop_excluded", f"{P1}:users:metric=users excluded from the funnel population",
             "count", "Users in the sample who are not in S0")
    r.quoted("pop_with_first_open", f"{P1}:users:metric=of those, users with a first_open event",
             "count", "Users with a first_open event: Part 1's population, which Part 2 does not restrict to")
    r.quoted("pop_without_first_open", f"{P1}:users:metric=of those, users with no first_open event",
             "count", "Users with events but no first_open in the window")
    r.derived("pop_without_first_open_pct",
              100.0 * pop["without_first_open"] / pop["users"], "pct",
              "Share of the funnel population with no first_open event: Part 1's exclusion, which Part 2 keeps",
              [f"{P1}:users:metric=of those, users with no first_open event",
               f"{P1}:users:metric=distinct users with at least one event in the window"])
    r.quoted("rows_raw", f"{P1}:users:metric=raw event rows before §10.7.4 de-duplication",
             "count", "Event rows in the window before de-duplication")
    r.quoted("rows_deduped", f"{P1}:users:metric=event rows after §10.7.4 de-duplication",
             "count", "Distinct (user_pseudo_id, event_name, event_timestamp) triples")
    r.quoted("dup_rows", f"{P1}:users:metric=duplicate rows removed",
             "count", "Rows removed by §10.7.4's de-duplication")
    r.derived("dup_ppm", 1e6 * pop["duplicate_rows"] / pop["events_raw"], "count",
              "Duplicate rows as parts per million of raw rows",
              [f"{P1}:users:metric=duplicate rows removed",
               f"{P1}:users:metric=raw event rows before §10.7.4 de-duplication"])
    r.quoted("dup_event_names", f"{P2}:value:section=duplicates&metric=event names carrying at least one duplicate",
             "count", "Distinct event names carrying at least one duplicate row")
    r.quoted("event_names_total", f"{P2}:value:section=duplicates&metric=distinct event names in the window",
             "count", "Distinct event_name values in the window")
    r.derived("shard_count", float(C.SHARD_COUNT), "count", "Daily shards in the window",
              [f"{RECON0}:value_num:row_kind=summary&key=shard_count"])
    r.derived("shard_rows", float(C.SHARD_ROWS), "count",
              "Rows in every shard: the minimum and the maximum are the same number, which is what makes it a sampling cap rather than traffic",
              [f"{RECON0}:value_num:row_kind=shard|min", f"{RECON0}:value_num:row_kind=shard|max"])

    # --- the re-scope statement (§10.6.1) -----------------------------------
    r.quoted("rescope_events", f"{P2}:value:section=rescope&metric=revenue-positive purchase events",
             "count", "Revenue-positive purchase events, quoted from the recon and never recounted")
    r.quoted("rescope_users", f"{P2}:value:section=rescope&metric=distinct users with such an event",
             "count", "Distinct users with a revenue-positive purchase event")
    r.derived("rescope_coverage_pct", handling["coverage"], "pct",
              "Payer coverage of the 15,175-user denominator, against §10.3's 0.5% bar",
              [f"{P2}:value:section=rescope&metric=distinct users with such an event",
               f"{P1}:users:metric=distinct users with at least one event in the window"])
    r.derived("rescope_event_factor", C.RESCOPE_EVENT_THRESHOLD / handling["revenue_events"], "ratio",
              "How far short of §10.3's 1,000-event threshold the observed count falls",
              [f"{P2}:value:section=rescope&metric=revenue-positive purchase events"])
    r.derived("rescope_coverage_factor", C.RESCOPE_COVERAGE_THRESHOLD * 100 / handling["coverage"], "ratio",
              "How far short of §10.3's 0.5% coverage threshold the observed share falls",
              [f"{P2}:value:section=rescope&metric=distinct users with such an event",
               f"{P1}:users:metric=distinct users with at least one event in the window"])
    r.quoted("rescope_usd_events", f"{P2}:value:section=rescope&metric=events with a positive event_value_in_usd",
             "count", "Purchase events carrying a positive event_value_in_usd, the narrower carrier")
    r.quoted("rescope_shards_without_usd", f"{P2}:value:section=rescope&metric=shards with no event_value_in_usd column",
             "count", "Shards on which event_value_in_usd does not exist as a column")
    r.quoted("spend_events", f"{P2}:value:section=rescope&metric=spend_virtual_currency events",
             "count", "spend_virtual_currency events: a soft-currency sink, explicitly not revenue")
    r.quoted("spend_users", f"{P2}:value:section=rescope&metric=spend_virtual_currency users",
             "count", "Users with at least one spend_virtual_currency event")

    # --- the funnel ---------------------------------------------------------
    for step in C.STEPS:
        r.quoted(f"{step.lower()}_strict", f"{P3}:users_strict:step={step}", "count",
                 f"{step} strict cumulative users: holders of all of S0..{step}")
        r.quoted(f"{step.lower()}_raw", f"{P3}:users_raw:step={step}", "count",
                 f"{step} raw users: holders of {step} regardless of the earlier steps")
        r.quoted(f"{step.lower()}_share_of_s0", f"{P3}:share_of_s0_pct_display:step={step}", "pct",
                 f"{step} strict users as a share of S0")
        if step != "S0":
            r.quoted(f"{step.lower()}_conversion", f"{P3}:step_conversion_pct_display:step={step}",
                     "pct", f"Step-to-step conversion into {step} from the previous strict population")
            r.quoted(f"{step.lower()}_conversion_lo", f"{P3}:step_conversion_lo_display:step={step}",
                     "pct", f"95% Wilson lower bound on the conversion into {step}")
            r.quoted(f"{step.lower()}_conversion_hi", f"{P3}:step_conversion_hi_display:step={step}",
                     "pct", f"95% Wilson upper bound on the conversion into {step}")
    strict = funnel["strict"]
    for previous, step in zip(C.STEPS, C.STEPS[1:]):
        lost = strict[previous] - strict[step]
        r.derived(f"drop_{previous.lower()}_{step.lower()}_users", float(lost), "count",
                  f"Users lost between {previous} and {step} on the strict population",
                  [f"{P3}:users_strict:step={previous}", f"{P3}:users_strict:step={step}"])
        r.derived(f"drop_{previous.lower()}_{step.lower()}_pp",
                  100.0 * lost / strict[previous], "pp",
                  f"Share of {previous}'s strict population lost before {step}",
                  [f"{P3}:users_strict:step={previous}", f"{P3}:users_strict:step={step}"])
    for step in ("S2", "S3"):
        r.derived(f"strict_raw_gap_{step.lower()}",
                  float(funnel["raw"][step] - strict[step]), "count",
                  f"Users holding {step} but not every earlier step: the gap between the raw and strict counts",
                  [f"{P3}:users_raw:step={step}", f"{P3}:users_strict:step={step}"])

    # --- out-of-order users -------------------------------------------------
    for key in ("s2_without_s1", "s3_without_s2", "s3_without_s1"):
        r.quoted(f"ooo_{key}", f"{P4}:users:violation={key}", "count",
                 f"Users matching the out-of-order pattern {key}")
        r.quoted(f"ooo_{key}_pct", f"{P4}:share_of_raw_pct_display:violation={key}", "pct",
                 f"{key} as a share of the step's own raw population (A-170)")

    # --- the level_end reconciliation ---------------------------------------
    r.quoted("le_events_end", f"{P7}:value:level=event&metric=level_end_quickplay events",
             "count", "De-duplicated level_end_quickplay events")
    r.quoted("le_events_outcomes", f"{P7}:value:level=event&metric=complete + fail",
             "count", "De-duplicated level_complete_quickplay plus level_fail_quickplay events")
    r.quoted("le_events_shortfall", f"{P7}:value:level=event&metric=shortfall: ends carrying no outcome",
             "count", "Ends carrying no outcome, at event level")
    r.quoted("le_events_shortfall_pct", f"{P7}:pct_display:level=event&metric=shortfall: ends carrying no outcome",
             "pct", "Event-level shortfall as a share of level_end_quickplay events")
    r.quoted("le_users_end", f"{P7}:value:level=user&metric=users with level_end_quickplay (S2)",
             "count", "Users with at least one level_end_quickplay event")
    r.quoted("le_users_complete", f"{P7}:value:level=user&metric=users with level_complete_quickplay",
             "count", "Users with at least one level_complete_quickplay event")
    r.quoted("le_users_fail", f"{P7}:value:level=user&metric=users with level_fail_quickplay",
             "count", "Users with at least one level_fail_quickplay event")
    r.quoted("le_users_union", f"{P7}:value:level=user&metric=users with either outcome (union)",
             "count", "Users with at least one outcome event of either kind")
    r.quoted("le_users_both", f"{P7}:value:level=user&metric=users with BOTH outcomes",
             "count", "Users holding both a complete and a fail: the users the arithmetic parallel double-counts")
    r.quoted("le_users_shortfall", f"{P7}:value:level=user&metric=shortfall: users with S2 and neither outcome",
             "count", "A-164 reading 1's numerator: users with S2 and neither outcome")
    r.quoted("le_reading1_pct", f"{P7}:pct_display:level=user&metric=shortfall: users with S2 and neither outcome",
             "pct", "A-164's directed reading, tested against §10.6.5's 1.0% trigger")
    r.quoted("le_reading2_pct", f"{P7}:pct_display:level=user&metric=arithmetic parallel: (complete + fail - end) / end",
             "pct", "A-164 reading 2: an excess, not a shortfall")
    r.quoted("le_reading3_pct", f"{P7}:pct_display:level=user&metric=shortfall over the outcome union",
             "pct", "A-164 reading 3: reading 1's numerator over the outcome union")
    r.quoted("le_outcome_without_end", f"{P7}:value:level=user&metric=users with an outcome but no level_end_quickplay",
             "count", "Users with an outcome event but no level_end_quickplay")

    # --- segmentation -------------------------------------------------------
    for dimension in C.PERMITTED_DIMENSIONS:
        slug = dimension.replace(".", "_")
        r.quoted(f"constancy_{slug}", f"{P8}:share_non_constant_pct_display:dimension={dimension}",
                 "pct", f"Share of users whose {dimension} is not constant across their own events")
        r.quoted(f"constancy_{slug}_users", f"{P8}:users_non_constant:dimension={dimension}",
                 "count", f"Users with more than one distinct {dimension}")
    r.quoted("part1_app_version_constancy",
             f"{PART1_DH}:value:section=app_info_version_constancy&metric=share_non_constant_part1_pct",
             "pct", "Part 1's app_info.version non-constant share, on its 4,319-user install population")
    r.derived("app_version_constancy_ratio",
              constancy["app_info.version"] / 1.968, "ratio",
              "How much larger Part 2's app_info.version non-constant share is than Part 1's",
              [f"{P8}:share_non_constant_pct_display:dimension=app_info.version",
               f"{PART1_DH}:value:section=app_info_version_constancy&metric=share_non_constant_part1_pct"])
    for dimension, bucket in seg.items():
        slug = dimension.replace(".", "_")
        r.derived(f"seg_{slug}_named", float(bucket["named"]), "count",
                  f"Segments of {dimension} named individually at the 200-user floor",
                  [f"{P9}:users_s0:dimension={dimension}&step=S0&is_other=false|count"])
        if bucket["segments_pooled"]:
            r.derived(f"seg_{slug}_pooled", float(bucket["segments_pooled"]), "count",
                      f"Segments of {dimension} pooled into the Other row",
                      [f"{P9}:segments_pooled:dimension={dimension}&segment=Other&step=S0"])
            r.derived(f"seg_{slug}_other_users", float(bucket["other_users"]), "count",
                      f"Users in the Other row for {dimension}",
                      [f"{P9}:users_s0:dimension={dimension}&segment=Other&step=S0"])

    # --- the parallel track (A-172) -----------------------------------------
    r.quoted("track_without_s1", f"{P10}:users:metric=users with no level_start_quickplay (outside S1)",
             "count", "Users the funnel counts as not having started a level")
    r.quoted("track_without_s1_with_np",
             f"{P10}:users:metric=of those, users who started a NON-quickplay level",
             "count", "Users outside S1 who started a level in the non-quickplay mode")
    r.derived("track_share_of_outside_s1", track["share_of_outside_s1"], "pct",
              "Share of the users outside S1 who started a non-quickplay level",
              [f"{P10}:users:metric=of those, users who started a NON-quickplay level",
               f"{P10}:users:metric=users with no level_start_quickplay (outside S1)"])
    r.quoted("track_either_mode", f"{P10}:users:metric=users who started a level in EITHER mode",
             "count", "Users who started a level in either mode")
    r.derived("track_either_mode_pct", 100.0 * track["either_mode"] / C.POPULATION, "pct",
              "Share of the population that started a level in either mode",
              [f"{P10}:users:metric=users who started a level in EITHER mode",
               f"{P1}:users:metric=distinct users with at least one event in the window"])
    r.quoted("track_neither", f"{P10}:users:metric=users who started a level in NEITHER mode",
             "count", "Users for whom 'did not start a level' is unqualified")
    r.quoted("track_np_users", f"{P10}:users:metric=users with a non-quickplay level_start, all",
             "count", "All users with a non-quickplay level_start event")
    r.quoted("track_both_modes", f"{P10}:users:metric=users active in BOTH modes", "count",
             "Users with a level start in both modes")
    r.quoted("track_plays_progressive", f"{P10}:users:metric=users with the plays_progressive user property",
             "count", "Users carrying the plays_progressive user property")
    r.quoted("track_plays_quickplay", f"{P10}:users:metric=users with the plays_quickplay user property",
             "count", "Users carrying the plays_quickplay user property")

    # --- diagnostics --------------------------------------------------------
    for event in C.DIAGNOSTIC_EVENTS:
        slug = event.replace(".", "_")
        r.quoted(f"diag_{slug}_users", f"{P6}:users:event_name={event}", "count",
                 f"Users with at least one {event} event")
        r.quoted(f"diag_{slug}_events", f"{P6}:events_deduped:event_name={event}", "count",
                 f"De-duplicated {event} events")

    # --- the byte ledger ----------------------------------------------------
    total = stats["ledger"]["total"]
    r.derived("ledger_total_bytes", float(total), "bytes",
              "Bytes billed across every Part 2 query",
              [f"{LEDGER}:bytes_billed:|sum"])
    r.derived("ledger_total_gib", total / 1073741824.0, "gib",
              "Bytes billed across every Part 2 query, in GiB",
              [f"{LEDGER}:bytes_billed:|sum"])
    r.derived("ledger_share_of_session", 100.0 * total / 21474836480, "pct",
              "Part 2's spend as a share of §10.1's 20 GiB per-session ceiling",
              [f"{LEDGER}:bytes_billed:|sum"])
    r.derived("ledger_queries", float(stats["ledger"]["rows"]), "count",
              "Query jobs Part 2 executed, re-runs included",
              [f"{LEDGER}:seq:|count"])
    r.derived("ledger_largest_gib", stats["ledger"]["largest"] / 1073741824.0, "gib",
              "The largest single Part 2 query, against §10.1's 4 GiB per-query ceiling",
              [f"{LEDGER}:bytes_billed:|max"])
    r.derived("ledger_pair_gib", stats["ledger"]["pair"] / 1073741824.0, "gib",
              "Bytes billed by both build sessions together, against §10.1's 40 GiB pair ceiling",
              [f"{LEDGER}:bytes_billed:|sum", "part1_budget_ledger.csv:bytes_billed:|sum"])
    r.derived("ledger_max_delta", float(stats["ledger"]["max_delta"]), "count",
              "The largest absolute miss of A-126's billing prediction across Part 2's queries, against a 1 MiB halt band",
              [f"{LEDGER}:prediction_delta_bytes:|max", f"{LEDGER}:prediction_delta_bytes:|min"])
    return r
