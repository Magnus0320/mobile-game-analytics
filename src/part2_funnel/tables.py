"""Render Part 2's report tables from the committed query results.

§7.3 puts every aggregation in SQL. Nothing here groups, joins or re-aggregates
GA4 data: the inputs are already-aggregated results of a few dozen rows each,
read with the csv module, and this module adds only what SQL deliberately did
not compute -- the Wilson intervals (§10.6.4), the suppression rule (A-163), the
rates, and §10.7.6's display precision. Sums here are totals of already-
aggregated cells, never an aggregation of events.

Every numeric column is carried twice, per A-069: a full-precision `*_value` for
arithmetic and checking, and a `*_display` string at §10.7.6's precision, which
is what the report quotes.
"""

import csv

from . import config as C
from . import markdown
from .wilson import suppressed, wilson_interval

FULL = "{:.10f}"


# --- readers -----------------------------------------------------------------

def read_rows(name: str) -> list[dict]:
    with open(C.TABLES / name, newline="") as fh:
        return list(csv.DictReader(fh))


def keyed(name: str, *key_fields: str) -> dict:
    return {tuple(r[k] for k in key_fields): r for r in read_rows(name)}


def as_bool(text: str) -> bool:
    """Parse a boolean out of a bq CSV cell, loudly.

    Anything unrecognised raises rather than silently reading as False, which is
    A-024's truthiness bug in a different costume.
    """
    value = (text or "").strip().lower()
    if value in ("true", "t", "1"):
        return True
    if value in ("false", "f", "0"):
        return False
    raise ValueError(f"expected a boolean, got {text!r}")


def write_csv(name: str, fieldnames: list[str], rows: list[dict]) -> str:
    with open(C.TABLES / name, "w", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        for row in rows:
            writer.writerow(row)
    return name


# --- the one place a rate is formed, suppressed, or marked inapplicable -------

def rate_cell(numerator, denominator, prefix: str, applicable: bool = True) -> dict:
    """§10.6.4's rate, §10.5.3's floor and §10.7.6's precision, in one function."""
    if not applicable:
        return {
            f"{prefix}_status": C.STATUS_NOT_APPLICABLE,
            f"{prefix}_denominator": "", f"{prefix}_numerator": "",
            f"{prefix}_pct_value": "", f"{prefix}_pct_display": C.NULL_DISPLAY,
            f"{prefix}_lo_display": C.NULL_DISPLAY, f"{prefix}_hi_display": C.NULL_DISPLAY,
        }
    numerator, denominator = int(numerator), int(denominator)
    if suppressed(denominator):
        return {
            f"{prefix}_status": C.STATUS_SUPPRESSED,
            f"{prefix}_denominator": denominator, f"{prefix}_numerator": numerator,
            f"{prefix}_pct_value": "", f"{prefix}_pct_display": C.SUPPRESSED_DISPLAY,
            f"{prefix}_lo_display": C.SUPPRESSED_DISPLAY,
            f"{prefix}_hi_display": C.SUPPRESSED_DISPLAY,
        }
    rate = 100.0 * numerator / denominator
    lo, hi = (100.0 * x for x in wilson_interval(numerator, denominator))
    return {
        f"{prefix}_status": C.STATUS_REPORTED,
        f"{prefix}_denominator": denominator, f"{prefix}_numerator": numerator,
        f"{prefix}_pct_value": FULL.format(rate), f"{prefix}_pct_display": f"{rate:.2f}",
        f"{prefix}_lo_display": f"{lo:.2f}", f"{prefix}_hi_display": f"{hi:.2f}",
    }


def pct(numerator, denominator) -> float:
    return 100.0 * int(numerator) / int(denominator)


# --- 01 population reconciliation (§10.7.2) ----------------------------------

def population() -> tuple[str, dict]:
    src = keyed("part2_q30_population_and_vocabulary.csv", "section", "key")
    totals = src[("totals", "all_event_names")]
    users = int(totals["users"])
    with_fo = int(src[("population", "users_with_first_open")]["users"])
    without_fo = int(src[("population", "users_without_first_open")]["users"])
    rows = [
        {"metric": "distinct users with at least one event in the window",
         "users": users, "share_of_population_pct_display": "100.00",
         "note": "§10.6.2's population: ALL 15,175 users, per user, not Part 1's install cohort"},
        {"metric": "users excluded from the funnel population",
         "users": 0, "share_of_population_pct_display": "0.00",
         "note": "the funnel begins at 'present in the window', so every user in the sample is in S0"},
        {"metric": "of those, users with a first_open event",
         "users": with_fo, "share_of_population_pct_display": f"{pct(with_fo, users):.2f}",
         "note": "Part 1's population. first_open is NOT a funnel step (§10.6.2); this row is here to show Part 2 does not inherit Part 1's restriction"},
        {"metric": "of those, users with no first_open event",
         "users": without_fo, "share_of_population_pct_display": f"{pct(without_fo, users):.2f}",
         "note": "the 71.54% Part 1 had to exclude, and which Part 2 keeps"},
        {"metric": "raw event rows before §10.7.4 de-duplication",
         "users": int(totals["events_raw"]), "share_of_population_pct_display": "",
         "note": "114 shards x 50,000 rows (A-096); a row count, not a user count"},
        {"metric": "event rows after §10.7.4 de-duplication",
         "users": int(totals["events_deduped"]), "share_of_population_pct_display": "",
         "note": "distinct (user_pseudo_id, event_name, event_timestamp)"},
        {"metric": "duplicate rows removed",
         "users": int(totals["duplicate_rows"]), "share_of_population_pct_display": "",
         "note": "§10.7.4, A-124; A-103 measured 207 and this build reproduces it"},
    ]
    name = write_csv("part2_01_population_reconciliation.csv",
                     ["metric", "users", "share_of_population_pct_display", "note"], rows)
    return name, {"users": users, "with_first_open": with_fo,
                  "without_first_open": without_fo,
                  "events_raw": int(totals["events_raw"]),
                  "events_deduped": int(totals["events_deduped"]),
                  "duplicate_rows": int(totals["duplicate_rows"])}


# --- 03 the funnel (§10.6.3, §10.6.4) ----------------------------------------

def funnel() -> tuple[str, dict]:
    src = keyed("part2_q31_progression_matrix_and_funnel.csv", "section", "key")
    raw = {s: int(src[("funnel_raw", s)]["users"]) for s in C.STEPS}
    strict = {s: int(src[("funnel_strict", s)]["users"]) for s in C.STEPS}
    s0 = strict["S0"]
    rows = []
    for index, step in enumerate(C.STEPS):
        previous = C.STEPS[index - 1] if index else None
        row = {
            "step": step,
            "label": C.STEP_LABEL[step],
            "event_name": C.STEP_EVENT[step] or "(any event)",
            "users_raw": raw[step],
            "users_strict": strict[step],
            "strict_minus_raw": strict[step] - raw[step],
        }
        # cumulative share of S0 -- §10.6.3's own column, on the strict population
        row.update(rate_cell(strict[step], s0, "share_of_s0"))
        # step-to-step conversion on the strict population -- §10.6.4
        row.update(rate_cell(strict[step], strict[previous] if previous else 0,
                             "step_conversion", applicable=previous is not None))
        row["note"] = ("S0 has no predecessor, so its step-to-step cell is an "
                       "explicit null rather than a meaningless 100%"
                       if previous is None else
                       f"strict: users holding all of S0..{step}")
        rows.append(row)
    fields = (["step", "label", "event_name", "users_raw", "users_strict", "strict_minus_raw"]
              + [f"share_of_s0_{k}" for k in
                 ("numerator", "denominator", "pct_value", "pct_display", "lo_display", "hi_display", "status")]
              + [f"step_conversion_{k}" for k in
                 ("numerator", "denominator", "pct_value", "pct_display", "lo_display", "hi_display", "status")]
              + ["note"])
    name = write_csv("part2_03_funnel.csv", fields, rows)
    return name, {"raw": raw, "strict": strict}


# --- 04 out-of-order users (§10.6.4, A-170) ----------------------------------

def out_of_order(funnel_stats: dict) -> tuple[str, dict]:
    src = keyed("part2_q31_progression_matrix_and_funnel.csv", "section", "key")
    raw = funnel_stats["raw"]
    spec = [
        ("S2", "s2_without_s1", "has S2 but not S1", "S2", True),
        ("S3", "s3_without_s2", "has S3 but not S2", "S3", True),
        ("S3", "s3_without_s1", "has S3 but not S1", "S3", False),
    ]
    rows, stats = [], {}
    for step, key, description, denominator_step, triggered in spec:
        users = int(src[("out_of_order", key)]["users"])
        share_raw = pct(users, raw[denominator_step])
        share_pop = pct(users, C.POPULATION)
        fired = triggered and share_raw > C.OUT_OF_ORDER_TRIGGER * 100
        rows.append({
            "step": step, "violation": key, "description": description,
            "users": users,
            "raw_population_denominator": raw[denominator_step],
            "share_of_raw_pct_value": FULL.format(share_raw),
            "share_of_raw_pct_display": f"{share_raw:.2f}",
            "population_denominator": C.POPULATION,
            "share_of_population_pct_display": f"{share_pop:.2f}",
            "trigger_applied": "true" if triggered else "false",
            "trigger_pct": "1.0" if triggered else "",
            "trigger_fired": ("true" if fired else "false") if triggered else "",
            "note": ("§10.6.4 names this case and attaches the 1.0% trigger to it; "
                     "A-170 reads 'the step's raw population' as the step holding "
                     "the violation, and prints the share of the whole population beside it"
                     if triggered else
                     "printed for legibility (A-170), not a case §10.6.4 names: "
                     "a user with S3 and S2 but no S1 is already counted in s2_without_s1"),
        })
        stats[key] = {"users": users, "share_of_raw": share_raw, "fired": fired}
    fields = ["step", "violation", "description", "users", "raw_population_denominator",
              "share_of_raw_pct_value", "share_of_raw_pct_display",
              "population_denominator", "share_of_population_pct_display",
              "trigger_applied", "trigger_pct", "trigger_fired", "note"]
    name = write_csv("part2_04_out_of_order.csv", fields, rows)
    return name, stats


# --- 05 the progression matrix (the audit trail) -----------------------------

def progression_matrix() -> tuple[str, dict]:
    rows_in = [r for r in read_rows("part2_q31_progression_matrix_and_funnel.csv")
               if r["section"] == "pattern"]
    rows = []
    for row in sorted(rows_in, key=lambda r: -int(r["users"])):
        users = int(row["users"])
        rows.append({
            "s1_level_start_quickplay": "yes" if as_bool(row["s1"]) else "no",
            "s2_level_end_quickplay": "yes" if as_bool(row["s2"]) else "no",
            "s3_level_complete_quickplay": "yes" if as_bool(row["s3"]) else "no",
            "level_fail_quickplay": "yes" if as_bool(row["fail_quickplay"]) else "no",
            "level_start_nonquickplay": "yes" if as_bool(row["np_start"]) else "no",
            "users": users,
            "share_of_population_pct_display": f"{pct(users, C.POPULATION):.2f}",
        })
    fields = ["s1_level_start_quickplay", "s2_level_end_quickplay",
              "s3_level_complete_quickplay", "level_fail_quickplay",
              "level_start_nonquickplay", "users", "share_of_population_pct_display"]
    name = write_csv("part2_05_progression_matrix.csv", fields, rows)
    return name, {"patterns": len(rows), "total": sum(int(r["users"]) for r in rows)}


# --- 06 diagnostic events (§10.6.5) ------------------------------------------

WHY_NOT_A_STEP = {
    "screen_view": "UI navigation, not progression",
    "user_engagement": "a heartbeat, not an action",
    "session_start": "app-open, and unreliable: median 2 per user against 5.7M events (§10.5.6)",
    "post_score": "score submission, parallel to progression",
    "level_fail_quickplay": "the failure branch of an attempt, not a stage beyond it",
    "spend_virtual_currency": "economy action, and explicitly not revenue (§10.6.1)",
    "in_app_purchase": "coverage 0.178%; see §10.6.1",
}


def diagnostic_events() -> tuple[str, dict]:
    src = keyed("part2_q30_population_and_vocabulary.csv", "section", "key")
    rows = []
    for event in C.DIAGNOSTIC_EVENTS:
        row = src[("event", event)]
        users = int(row["users"])
        rows.append({
            "event_name": event,
            "events_deduped": int(row["events_deduped"]),
            "events_raw": int(row["events_raw"]),
            "duplicate_rows_removed": int(row["duplicate_rows"]),
            "users": users,
            "share_of_population_pct_display": f"{pct(users, C.POPULATION):.2f}",
            "why_not_a_step": WHY_NOT_A_STEP[event],
            "note": "regenerated, not transcribed (§10.6.6 item 3); counts are de-duplicated (§10.7.4), so events_raw is the recon's basis and events_deduped is this report's",
        })
    fields = ["event_name", "events_deduped", "events_raw", "duplicate_rows_removed",
              "users", "share_of_population_pct_display", "why_not_a_step", "note"]
    name = write_csv("part2_06_diagnostic_events.csv", fields, rows)
    return name, {}


# --- 07 the level_end reconciliation (§10.6.5, A-164) ------------------------

def level_end_reconciliation() -> tuple[str, dict]:
    """Event level as §10.6.5 fixes it; user level under A-164's directed reading,
    with the components of all three readings printed so any can be rebuilt."""
    vocab = keyed("part2_q30_population_and_vocabulary.csv", "section", "key")
    users = keyed("part2_q31_progression_matrix_and_funnel.csv", "section", "key")

    end = int(vocab[("event", C.LEVEL_END_EVENT)]["events_deduped"])
    end_raw = int(vocab[("event", C.LEVEL_END_EVENT)]["events_raw"])
    outcomes = {e: int(vocab[("event", e)]["events_deduped"]) for e in C.LEVEL_END_OUTCOMES}
    outcomes_raw = {e: int(vocab[("event", e)]["events_raw"]) for e in C.LEVEL_END_OUTCOMES}
    outcome_sum, outcome_sum_raw = sum(outcomes.values()), sum(outcomes_raw.values())
    shortfall, shortfall_raw = end - outcome_sum, end_raw - outcome_sum_raw

    u = {k: int(users[("level_end_user", k)]["users"]) for k in (
        "users_end", "users_complete", "users_fail", "users_complete_or_fail",
        "users_complete_and_fail", "end_without_outcome", "outcome_without_end")}

    r1 = pct(u["end_without_outcome"], u["users_end"])
    r2 = 100.0 * (u["users_complete"] + u["users_fail"] - u["users_end"]) / u["users_end"]
    r3 = pct(u["end_without_outcome"], u["users_complete_or_fail"])

    rows = [
        {"level": "event", "metric": "level_end_quickplay events", "value": end,
         "denominator": "", "pct_display": "", "reading": "",
         "note": f"de-duplicated (§10.7.4); the recon's raw count is {end_raw}"},
        {"level": "event", "metric": "level_complete_quickplay events",
         "value": outcomes["level_complete_quickplay"], "denominator": "", "pct_display": "",
         "reading": "", "note": f"de-duplicated; raw {outcomes_raw['level_complete_quickplay']}"},
        {"level": "event", "metric": "level_fail_quickplay events",
         "value": outcomes["level_fail_quickplay"], "denominator": "", "pct_display": "",
         "reading": "", "note": f"de-duplicated; raw {outcomes_raw['level_fail_quickplay']}"},
        {"level": "event", "metric": "complete + fail", "value": outcome_sum,
         "denominator": "", "pct_display": "", "reading": "",
         "note": f"raw {outcome_sum_raw}; §10.6.5 quotes 328,123 on the raw basis"},
        {"level": "event", "metric": "shortfall: ends carrying no outcome",
         "value": shortfall, "denominator": end,
         "pct_display": f"{pct(shortfall, end):.2f}", "reading": "",
         "note": f"§10.6.5 quotes 21,606 and 6.18% on the raw basis; the de-duplicated shortfall is {shortfall}, a difference of {shortfall_raw - shortfall} event(s), and the whole difference is the duplicate rows removed from the three events"},

        {"level": "user", "metric": "users with level_end_quickplay (S2)",
         "value": u["users_end"], "denominator": "", "pct_display": "", "reading": "",
         "note": "the denominator of A-164's directed reading"},
        {"level": "user", "metric": "users with level_complete_quickplay",
         "value": u["users_complete"], "denominator": "", "pct_display": "", "reading": "", "note": ""},
        {"level": "user", "metric": "users with level_fail_quickplay",
         "value": u["users_fail"], "denominator": "", "pct_display": "", "reading": "", "note": ""},
        {"level": "user", "metric": "users with either outcome (union)",
         "value": u["users_complete_or_fail"], "denominator": "", "pct_display": "", "reading": "",
         "note": "the denominator of reading 3"},
        {"level": "user", "metric": "users with BOTH outcomes",
         "value": u["users_complete_and_fail"], "denominator": "", "pct_display": "", "reading": "",
         "note": "the users the arithmetic parallel double-counts; this is why reading 2 returns an excess"},
        {"level": "user", "metric": "users with an outcome but no level_end_quickplay",
         "value": u["outcome_without_end"], "denominator": "", "pct_display": "", "reading": "",
         "note": "the reverse direction, printed so the reconciliation closes both ways"},

        {"level": "user", "metric": "shortfall: users with S2 and neither outcome",
         "value": u["end_without_outcome"], "denominator": u["users_end"],
         "pct_display": f"{r1:.2f}", "reading": "1 (DIRECTED)",
         "note": "A-164's directed reading, and the figure §10.6.5's 1.0% trigger is tested against"},
        {"level": "user", "metric": "arithmetic parallel: (complete + fail - end) / end",
         "value": u["users_complete"] + u["users_fail"] - u["users_end"],
         "denominator": u["users_end"], "pct_display": f"{r2:.2f}", "reading": "2",
         "note": "an EXCESS, not a shortfall: it exists only because users holding both outcomes are counted twice, so a shortfall trigger cannot fire against it for the reason it was written"},
        {"level": "user", "metric": "shortfall over the outcome union",
         "value": u["end_without_outcome"], "denominator": u["users_complete_or_fail"],
         "pct_display": f"{r3:.2f}", "reading": "3",
         "note": "reading 1's numerator over a denominator the event-level figure never uses"},
    ]
    fields = ["level", "metric", "value", "denominator", "pct_display", "reading", "note"]
    name = write_csv("part2_07_level_end_reconciliation.csv", fields, rows)
    stats = {
        "event_end": end, "event_outcome_sum": outcome_sum, "event_shortfall": shortfall,
        "event_shortfall_pct": pct(shortfall, end),
        "event_shortfall_raw": shortfall_raw,
        "reading1_pct": r1, "reading2_pct": r2, "reading3_pct": r3,
        "reading1_fired": r1 > C.LEVEL_END_TRIGGER * 100, **u,
    }
    return name, stats


# --- 08 segment constancy (§10.7.5 as generalised by A-154) ------------------

def segment_constancy() -> tuple[str, dict]:
    rows_in = read_rows("part2_q32_segment_constancy.csv")
    rows, outcome = [], {}
    for row in sorted(rows_in, key=lambda r: -int(r["users_non_constant"])):
        dimension = row["dimension"]
        non_constant, total = int(row["users_non_constant"]), int(row["users_total"])
        share = pct(non_constant, total)
        if share > C.CONSTANCY_DROP_SHARE * 100:
            verdict, action = "dropped", "dropped above §10.7.5's 25.0% trigger"
        elif share > C.CONSTANCY_CAVEAT_SHARE * 100:
            verdict, action = "caveated", "reported with a caveat naming the share, above §10.7.5's 5.0% trigger"
        else:
            verdict, action = "reported", "reported without a caveat; below §10.7.5's 5.0% trigger"
        outcome[dimension] = verdict
        rows.append({
            "dimension": dimension,
            "users_total": total,
            "users_non_constant": non_constant,
            "share_non_constant_pct_value": FULL.format(share),
            "share_non_constant_pct_display": f"{share:.2f}",
            "max_distinct_values_per_user": int(row["max_distinct_per_user"]),
            "users_with_any_null": int(row["users_with_any_null"]),
            "distinct_values_overall": int(row["distinct_values_overall"]),
            "segmentation_outcome": verdict,
            "attribution_means": C.ATTRIBUTION_MEANING[dimension],
            "note": action + "; triggers apply per dimension, independently (A-154)",
        })
    fields = ["dimension", "users_total", "users_non_constant",
              "share_non_constant_pct_value", "share_non_constant_pct_display",
              "max_distinct_values_per_user", "users_with_any_null",
              "distinct_values_overall", "segmentation_outcome",
              "attribution_means", "note"]
    name = write_csv("part2_08_segment_constancy.csv", fields, rows)
    return name, outcome


# --- 09 the funnel by segment (§10.6.6 item 5, §10.7.5, A-174) ---------------

def funnel_by_segment(constancy_outcome: dict) -> tuple[str, dict]:
    rows_in = read_rows("part2_q33_funnel_by_segment.csv")
    rows, stats = [], {}
    for row in rows_in:
        dimension = row["dimension"]
        if constancy_outcome.get(dimension) == "dropped":
            continue                      # §10.7.5's 25.0% trigger, applied here (A-169)
        strict = {"S0": int(row["users_s0"]), "S1": int(row["strict_s1"]),
                  "S2": int(row["strict_s2"]), "S3": int(row["strict_s3"])}
        raw = {"S0": int(row["users_s0"]), "S1": int(row["raw_s1"]),
               "S2": int(row["raw_s2"]), "S3": int(row["raw_s3"])}
        bucket = stats.setdefault(dimension, {"named": 0, "other_users": 0,
                                              "segments_pooled": 0, "s0": 0})
        bucket["s0"] += strict["S0"]
        if as_bool(row["is_other"]):
            bucket["other_users"] = strict["S0"]
            bucket["segments_pooled"] = int(row["segments_pooled"])
        else:
            bucket["named"] += 1
        for index, step in enumerate(C.STEPS):
            previous = C.STEPS[index - 1] if index else None
            cell = {
                "dimension": dimension,
                "segment": row["segment"],
                "is_other": row["is_other"],
                "segments_pooled": row["segments_pooled"] if as_bool(row["is_other"]) else "",
                "users_s0": strict["S0"],
                "step": step,
                "users_strict": strict[step],
                "users_raw": raw[step],
            }
            cell.update(rate_cell(strict[step], strict["S0"], "share_of_s0"))
            cell.update(rate_cell(strict[step], strict[previous] if previous else 0,
                                  "step_conversion", applicable=previous is not None))
            cell["caveat"] = (
                f"non-constant for {constancy_outcome.get(dimension)} share of users; "
                f"see part2_08_segment_constancy.csv"
                if constancy_outcome.get(dimension) == "caveated" else "")
            cell["attribution_means"] = C.ATTRIBUTION_MEANING[dimension]
            cell["note"] = ("attributed from the user's earliest event row (§10.7.5); "
                            "the >= 200-user floor is applied once, on S0 (A-174)")
            rows.append(cell)
    fields = (["dimension", "segment", "is_other", "segments_pooled", "users_s0",
               "step", "users_strict", "users_raw"]
              + [f"share_of_s0_{k}" for k in
                 ("numerator", "denominator", "pct_value", "pct_display", "lo_display", "hi_display", "status")]
              + [f"step_conversion_{k}" for k in
                 ("numerator", "denominator", "pct_value", "pct_display", "lo_display", "hi_display", "status")]
              + ["caveat", "attribution_means", "note"])
    name = write_csv("part2_09_funnel_by_segment.csv", fields, rows)
    return name, stats


# --- 02 data handling: the re-scope figures, duplicates, traffic source -------

def _recon_row(name, **predicates):
    for row in read_rows(name):
        if all(row[k] == v for k, v in predicates.items()):
            return row
    raise LookupError(f"{name}: no row matching {predicates}")


def data_handling(population_stats: dict) -> tuple[str, dict]:
    """§10.6.6 item 6: duplicate rows removed, plus the re-scope figures.

    The re-scope figures are QUOTED from the recon's committed result files and
    never recounted (A-167): §10.3's rule is evaluated once, and A-130 forbids
    re-counting after the verdict. The `in_app_purchase` DIAGNOSTIC count is a
    different quantity and is regenerated in part2_06.
    """
    purchase = _recon_row("recon_05_revenue_population.csv", event_name="in_app_purchase")
    spend = _recon_row("recon_05_revenue_population.csv", event_name="spend_virtual_currency")
    usd_col = _recon_row("recon_01_column_inventory.csv", field_path="event_value_in_usd")
    shards_without_usd = C.SHARD_COUNT - int(usd_col["shards_with_path"])

    revenue_events = int(purchase["price_param_positive_events"])
    revenue_users = int(purchase["price_param_positive_users"])
    coverage = pct(revenue_users, C.POPULATION)
    vocab = keyed("part2_q30_population_and_vocabulary.csv", "section", "key")
    affected = sum(1 for r in read_rows("part2_q30_population_and_vocabulary.csv")
                   if r["section"] == "event" and int(r["duplicate_rows"]) > 0)
    event_names = sum(1 for r in read_rows("part2_q30_population_and_vocabulary.csv")
                      if r["section"] == "event")

    traffic = []
    for field in ("traffic_source.name", "traffic_source.medium", "traffic_source.source"):
        values = sorted(((int(r["event_share_ppm"]), r["value"] or "(null)")
                         for r in read_rows("recon_07_field_profiles.csv")
                         if r["row_kind"] == "value" and r["field"] == field),
                        reverse=True)[:2]
        traffic.append((field, values, sum(p for p, _ in values) / 10000.0))

    rows = [
        {"section": "rescope", "metric": "revenue-positive purchase events",
         "value": revenue_events, "value_display": f"{revenue_events:,}",
         "note": "quoted from recon_05_revenue_population.csv, never recounted (A-167, A-130); a LOWER BOUND, because event_value_in_usd is absent from 15 of the 114 shards and only 24 of the 27 events carry a positive value in it, while all 27 carry a positive price parameter"},
        {"section": "rescope", "metric": "distinct users with such an event",
         "value": revenue_users, "value_display": f"{revenue_users:,}", "note": "quoted from recon_05_revenue_population.csv"},
        {"section": "rescope", "metric": "payer coverage of the 15,175-user denominator",
         "value": FULL.format(coverage), "value_display": f"{coverage:.3f}%",
         "note": "§10.3's denominator: distinct user_pseudo_id with any event in the range"},
        {"section": "rescope", "metric": "§10.3 event threshold",
         "value": C.RESCOPE_EVENT_THRESHOLD, "value_display": "1,000",
         "note": f"MISSED by a factor of {C.RESCOPE_EVENT_THRESHOLD / revenue_events:.0f}"},
        {"section": "rescope", "metric": "§10.3 coverage threshold",
         "value": C.RESCOPE_COVERAGE_THRESHOLD * 100, "value_display": "0.5%",
         "note": f"MISSED by a factor of {C.RESCOPE_COVERAGE_THRESHOLD * 100 / coverage:.1f}"},
        {"section": "rescope", "metric": "events with a positive event_value_in_usd",
         "value": int(purchase["usd_positive_events"]),
         "value_display": f"{int(purchase['usd_positive_events']):,}",
         "note": "the narrower revenue carrier; the price parameter is the larger and is the one counted"},
        {"section": "rescope", "metric": "shards with no event_value_in_usd column",
         "value": shards_without_usd, "value_display": f"{shards_without_usd:,}",
         "note": "of 114; why 27 is a floor rather than a census (§10.6.1, A-130)"},
        {"section": "rescope", "metric": "spend_virtual_currency events",
         "value": int(spend["events"]), "value_display": f"{int(spend['events']):,}",
         "note": "NOT revenue: a soft-currency sink, and §10.6.1 forbids presenting it as monetization, spend, or purchase behaviour"},
        {"section": "rescope", "metric": "spend_virtual_currency users",
         "value": int(spend["distinct_users"]), "value_display": f"{int(spend['distinct_users']):,}",
         "note": "see above"},

        {"section": "duplicates", "metric": "raw event rows",
         "value": population_stats["events_raw"], "value_display": f"{population_stats['events_raw']:,}",
         "note": "before §10.7.4 de-duplication"},
        {"section": "duplicates", "metric": "de-duplicated event rows",
         "value": population_stats["events_deduped"], "value_display": f"{population_stats['events_deduped']:,}",
         "note": "distinct (user_pseudo_id, event_name, event_timestamp)"},
        {"section": "duplicates", "metric": "duplicate rows removed",
         "value": population_stats["duplicate_rows"], "value_display": f"{population_stats['duplicate_rows']:,}",
         "note": "§10.7.4, A-124; A-103 measured 207 and this build reproduces it exactly"},
        {"section": "duplicates", "metric": "duplicate share, parts per million",
         "value": round(1e6 * population_stats["duplicate_rows"] / population_stats["events_raw"]),
         "value_display": f"{round(1e6 * population_stats['duplicate_rows'] / population_stats['events_raw']):,}",
         "note": "of raw rows"},
        {"section": "duplicates", "metric": "event names carrying at least one duplicate",
         "value": affected, "value_display": f"{affected:,}",
         "note": f"of {event_names} event names in the window; the per-name distribution is in part2_q30_population_and_vocabulary.csv"},
        {"section": "duplicates", "metric": "distinct event names in the window",
         "value": event_names, "value_display": f"{event_names:,}",
         "note": "the complete vocabulary; the four steps and seven diagnostics are a visible selection from it (A-090's precedent)"},

        {"section": "identity", "metric": "rows with a non-null user_id",
         "value": 0, "value_display": "0",
         "note": "user_id is NULL on all 5,700,000 rows (A-099), so 'a user' means a DEVICE-INSTALL throughout: one person on two devices is two users, a reinstall may be a new user, and no cross-device or unique-people claim is possible (§10.7.3)"},
    ]
    for field, values, total in traffic:
        rows.append({
            "section": "traffic_source", "metric": f"{field}: top two buckets",
            "value": FULL.format(total), "value_display": f"{total:.2f}%",
            "note": "; ".join(f"{name} at {ppm / 10000.0:.2f}%" for ppm, name in values)
                    + " — quoted from recon_07_field_profiles.csv (A-168). §10.7.5 drops traffic source: a dimension with one real bucket plus a placeholder cannot distinguish cohorts, and NO metric in this report is segmented by it",
        })
    fields = ["section", "metric", "value", "value_display", "note"]
    name = write_csv("part2_02_data_handling.csv", fields, rows)
    return name, {"revenue_events": revenue_events, "revenue_users": revenue_users,
                  "coverage": coverage, "shards_without_usd": shards_without_usd,
                  "event_names": event_names, "duplicate_event_names": affected}


# --- 10 the non-quickplay parallel track (A-172): a diagnostic, never a step --

def parallel_track() -> tuple[str, dict]:
    src = keyed("part2_q31_progression_matrix_and_funnel.csv", "section", "key")
    vocab = keyed("part2_q30_population_and_vocabulary.csv", "section", "key")
    g = lambda k: int(src[("parallel_track", k)]["users"])
    without_s1 = g("users_without_s1")
    with_np = g("users_without_s1_with_nonquickplay_start")
    either = C.POPULATION - g("users_with_neither_start")
    rows = [
        {"metric": "users with no level_start_quickplay (outside S1)",
         "users": without_s1, "share_of_population_pct_display": f"{pct(without_s1, C.POPULATION):.2f}",
         "note": "the users the funnel counts as not having started a level"},
        {"metric": "of those, users who started a NON-quickplay level",
         "users": with_np, "share_of_population_pct_display": f"{pct(with_np, C.POPULATION):.2f}",
         "note": f"{pct(with_np, without_s1):.2f}% of the users outside S1; they progressed in a mode §10.6.3's funnel does not cover"},
        {"metric": "users who started a level in EITHER mode",
         "users": either, "share_of_population_pct_display": f"{pct(either, C.POPULATION):.2f}",
         "note": "against S1's own share; the gap is what the funnel's mode restriction costs"},
        {"metric": "users who started a level in NEITHER mode",
         "users": g("users_with_neither_start"),
         "share_of_population_pct_display": f"{pct(g('users_with_neither_start'), C.POPULATION):.2f}",
         "note": "the users for whom 'did not start a level' is unqualified"},
        {"metric": "users with a non-quickplay level_start, all",
         "users": g("users_nonquickplay_start"),
         "share_of_population_pct_display": f"{pct(g('users_nonquickplay_start'), C.POPULATION):.2f}",
         "note": "matches the recon's own count for level_start exactly"},
        {"metric": "users active in BOTH modes",
         "users": g("users_in_both_modes"),
         "share_of_population_pct_display": f"{pct(g('users_in_both_modes'), C.POPULATION):.2f}",
         "note": "counted inside S1 by the funnel"},
        {"metric": "users with the plays_progressive user property",
         "users": int(_recon_row("recon_09_user_properties.csv",
                                 user_property_key="plays_progressive")["distinct_users"]),
         "share_of_population_pct_display": "",
         # A-182 names the plays_quickplay row only, but this note carried the same
         # inference in different words, so it is corrected with it and the fact is
         # disclosed rather than the row left standing.
         "note": "quoted from recon_09_user_properties.csv; close to the 4,774 users with an observed non-quickplay level start, but the plays_* properties have undocumented semantics and are not used here to compare the sizes of the two modes. Corrected 2026-09-22 (A-182): this note previously read 'points the same way as the event counts'"},
        {"metric": "users with the plays_quickplay user property",
         "users": int(_recon_row("recon_09_user_properties.csv",
                                 user_property_key="plays_quickplay")["distinct_users"]),
         "share_of_population_pct_display": "",
         # Corrected 2026-09-22 under A-181, recorded in A-182. This note previously
         # read "the mode the funnel DOES cover is the smaller of the two" -- an
         # inference from two property counts that the observed level starts reverse.
         "note": "quoted from recon_09_user_properties.csv; NOT a measure of mode participation -- 10,166 users have an observed level_start_quickplay against this property's 3,548, an undercount of about 2.9x, and the property's semantics are undocumented. Corrected 2026-09-22 (A-182): this note previously claimed the mode the funnel covers is the smaller of the two, which the observed level starts reverse"},
    ]
    name = write_csv("part2_10_parallel_track.csv",
                     ["metric", "users", "share_of_population_pct_display", "note"], rows)
    props = {k: int(_recon_row("recon_09_user_properties.csv",
                               user_property_key=k)["distinct_users"])
             for k in ("plays_progressive", "plays_quickplay")}
    return name, {"without_s1": without_s1, "without_s1_with_np": with_np,
                  **props,
                  "share_of_outside_s1": pct(with_np, without_s1),
                  "either_mode": either, "neither": g("users_with_neither_start"),
                  "np_users": g("users_nonquickplay_start"),
                  "both_modes": g("users_in_both_modes")}


# --- generated markdown views (A-165) ----------------------------------------
# A report table is not written, it is generated here from its committed CSV.
# audit.py regenerates each block and asserts byte-equality, so no cell in a
# report table is ever typed.

def _iv(row, prefix):
    if row[f"{prefix}_status"] == C.STATUS_NOT_APPLICABLE:
        return C.NULL_DISPLAY
    if row[f"{prefix}_status"] == C.STATUS_SUPPRESSED:
        return C.SUPPRESSED_DISPLAY
    return f"{row[f'{prefix}_pct_display']} [{row[f'{prefix}_lo_display']}, {row[f'{prefix}_hi_display']}]"


def view_population():
    rows = [[r["metric"], f"{int(r['users']):,}",
             r["share_of_population_pct_display"] + ("%" if r["share_of_population_pct_display"] else "")]
            for r in read_rows("part2_01_population_reconciliation.csv")]
    return markdown.table(["", "Count", "Share"], ["l", "r", "r"], rows)


def view_funnel():
    rows = []
    for r in read_rows("part2_03_funnel.csv"):
        rows.append([f"**{r['step']}**", r["label"], f"`{r['event_name']}`",
                     f"{int(r['users_strict']):,}", f"{int(r['users_raw']):,}",
                     _iv(r, "share_of_s0"), _iv(r, "step_conversion")])
    return markdown.table(
        ["Step", "What it means", "Event", "Strict", "Raw",
         "Share of S0 % [95% Wilson]", "Step-to-step % [95% Wilson]"],
        ["l", "l", "l", "r", "r", "r", "r"], rows)


def view_out_of_order():
    rows = [[r["step"], r["description"], f"{int(r['users']):,}",
             f"{int(r['raw_population_denominator']):,}",
             r["share_of_raw_pct_display"] + "%",
             r["share_of_population_pct_display"] + "%",
             {"true": "fired", "false": "not fired", "": "not applied"}[r["trigger_fired"]]]
            for r in read_rows("part2_04_out_of_order.csv")]
    return markdown.table(
        ["Step", "Violation", "Users", "Raw population", "Share of step", "Share of all users", "1.0% trigger"],
        ["l", "l", "r", "r", "r", "r", "l"], rows)


def view_matrix():
    rows = [[r["s1_level_start_quickplay"], r["s2_level_end_quickplay"],
             r["s3_level_complete_quickplay"], r["level_fail_quickplay"],
             r["level_start_nonquickplay"], f"{int(r['users']):,}",
             r["share_of_population_pct_display"] + "%"]
            for r in read_rows("part2_05_progression_matrix.csv")]
    return markdown.table(
        ["S1 start", "S2 end", "S3 complete", "fail", "non-quickplay start", "Users", "Share"],
        ["c", "c", "c", "c", "c", "r", "r"], rows)


def view_diagnostics():
    rows = [[f"`{r['event_name']}`", f"{int(r['events_deduped']):,}",
             f"{int(r['users']):,}", r["share_of_population_pct_display"] + "%",
             r["why_not_a_step"]]
            for r in read_rows("part2_06_diagnostic_events.csv")]
    return markdown.table(["Event", "Events", "Users", "Share of users", "Why not a step"],
                          ["l", "r", "r", "r", "l"], rows)


def _level_end(level):
    rows = []
    for r in read_rows("part2_07_level_end_reconciliation.csv"):
        if r["level"] != level:
            continue
        rows.append([r["metric"] + (f" — reading {r['reading']}" if r["reading"] else ""),
                     f"{int(r['value']):,}",
                     f"{int(r['denominator']):,}" if r["denominator"] else "",
                     r["pct_display"] + "%" if r["pct_display"] else ""])
    return markdown.table(["", "Count", "Denominator", "Share"], ["l", "r", "r", "r"], rows)


def view_level_end_event():
    return _level_end("event")


def view_level_end_user():
    return _level_end("user")


def view_constancy():
    rows = [[f"`{r['dimension']}`", f"{int(r['users_non_constant']):,}",
             r["share_non_constant_pct_display"] + "%",
             r["max_distinct_values_per_user"],
             r["attribution_means"], r["segmentation_outcome"]]
            for r in read_rows("part2_08_segment_constancy.csv")]
    return markdown.table(
        ["Dimension", "Non-constant users", "Share", "Max values per user",
         "Earliest-event value means", "Outcome"],
        ["l", "r", "r", "r", "l", "l"], rows)


def _segment_view(dimension):
    by_segment = {}
    for r in read_rows("part2_09_funnel_by_segment.csv"):
        if r["dimension"] != dimension:
            continue
        by_segment.setdefault(r["segment"], {})[r["step"]] = r
    rows = []
    for segment, steps in sorted(by_segment.items(),
                                 key=lambda kv: (kv[0] == C.OTHER_LABEL,
                                                 -int(kv[1]["S0"]["users_s0"]))):
        s0 = steps["S0"]
        label = segment
        if segment == C.OTHER_LABEL and s0["segments_pooled"]:
            label = f"Other ({int(s0['segments_pooled'])} segments)"
        rows.append([label, f"{int(s0['users_s0']):,}",
                     f"{int(steps['S1']['users_strict']):,}", _iv(steps["S1"], "step_conversion"),
                     f"{int(steps['S2']['users_strict']):,}", _iv(steps["S2"], "step_conversion"),
                     f"{int(steps['S3']['users_strict']):,}", _iv(steps["S3"], "step_conversion")])
    return markdown.table(
        ["Segment", "S0", "S1", "S0→S1 % [95% Wilson]", "S2", "S1→S2 %", "S3", "S2→S3 %"],
        ["l", "r", "r", "r", "r", "r", "r", "r"], rows)


def view_parallel_track():
    rows = [[r["metric"], f"{int(r['users']):,}",
             r["share_of_population_pct_display"] + ("%" if r["share_of_population_pct_display"] else "")]
            for r in read_rows("part2_10_parallel_track.csv")]
    return markdown.table(["", "Users", "Share of 15,175"], ["l", "r", "r"], rows)


def view_rescope():
    rows = [[r["metric"], r["value_display"]]
            for r in read_rows("part2_02_data_handling.csv") if r["section"] == "rescope"]
    return markdown.table(["", "Observed"], ["l", "r"], rows)


def view_ledger():
    rows = []
    for r in read_rows("part2_budget_ledger.csv"):
        rows.append([f"`{r['query_file'].split('/')[-1]}`",
                     f"{int(r['dry_run_estimate_bytes']):,}",
                     f"{int(r['bytes_billed']):,}",
                     f"{int(r['predicted_billed_bytes']):,}",
                     r["prediction_delta_bytes"]])
    return markdown.table(["Query", "Dry-run estimate", "Billed", "Predicted", "Delta"],
                          ["l", "r", "r", "r", "r"], rows)


def view_readme_summary():
    """The README's Part 2 summary table, generated like every other one.

    A-165 applies to the README as much as to the report: a figure a reader meets
    first is the one least worth typing by hand.
    """
    pop = {r["metric"]: r for r in read_rows("part2_01_population_reconciliation.csv")}
    f = {r["step"]: r for r in read_rows("part2_03_funnel.csv")}
    dh = {(r["section"], r["metric"]): r
          for r in read_rows("part2_02_data_handling.csv")}
    users = int(pop["distinct users with at least one event in the window"]["users"])

    def step(key, previous=None):
        row = f[key]
        cell = (f"**{int(row['users_strict']):,}** &middot; "
                f"{row['share_of_s0_pct_display']}% of S0")
        if previous:
            cell += (f" &middot; {row['step_conversion_pct_display']}% of {previous}, "
                     f"95% Wilson [{row['step_conversion_lo_display']}, "
                     f"{row['step_conversion_hi_display']}]")
        else:
            cell += (f", 95% Wilson [{row['share_of_s0_lo_display']}, "
                     f"{row['share_of_s0_hi_display']}]")
        return cell

    rows = [
        ["Population", f"{users:,} users with at least one event in the window — "
                       f"everyone in the sample, none excluded"],
        ["Counting unit", "Per user, whole-window presence; `first_open` is not a step"],
        ["S0 — present in the window",
         f"**{int(f['S0']['users_strict']):,}** &middot; "
         f"{f['S0']['share_of_s0_pct_display']}%, by construction"],
        ["S1 — started a level", step("S1")],
        ["S2 — finished an attempt", step("S2", "S1")],
        ["S3 — completed a level", step("S3", "S2")],
        ["Revenue",
         f"**Not answerable.** {dh[('rescope', 'revenue-positive purchase events')]['value_display']}"
         f" revenue-positive purchase events from "
         f"{dh[('rescope', 'distinct users with such an event')]['value_display']} users — "
         f"{dh[('rescope', 'payer coverage of the 15,175-user denominator')]['value_display']}"
         f" of users against a 0.5% bar, and that count is a floor"],
        ["Sampling",
         f"Every shard holds exactly **{C.SHARD_ROWS:,}** rows, so no count here is a "
         f"traffic figure"],
    ]
    return markdown.table(["", ""], ["l", "l"], rows)


VIEWS = {
    "readme_summary": view_readme_summary,
    "population": view_population,
    "funnel": view_funnel,
    "out_of_order": view_out_of_order,
    "matrix": view_matrix,
    "diagnostics": view_diagnostics,
    "level_end_event": view_level_end_event,
    "level_end_user": view_level_end_user,
    "constancy": view_constancy,
    "parallel_track": view_parallel_track,
    "rescope": view_rescope,
    "ledger": view_ledger,
}
for _dimension in C.PERMITTED_DIMENSIONS:
    VIEWS["segment_" + _dimension.replace(".", "_")] = (
        lambda d=_dimension: _segment_view(d))
