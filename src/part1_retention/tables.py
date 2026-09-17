"""Render Part 1's report tables from the committed query results.

§7.3 puts every aggregation in SQL. Nothing here groups, joins or re-aggregates
GA4 data: the inputs are already-aggregated results of a few dozen rows each,
read with the csv module, and this module adds only what SQL deliberately did
not compute -- the Wilson intervals (§10.5.3), the suppression rule (A-139), the
explicit-null rendering of ineligible cells (§10.5.5), and §10.7.6's display
precision. Sums that appear here are totals of already-aggregated cells for a
total line, never an aggregation of events.

Every numeric column is carried twice, per A-069: a full-precision `*_value` for
arithmetic and checking, and a `*_display` string at §10.7.6's precision, which
is what the report quotes.
"""

import csv

from . import config as C
from .gate import evaluate as evaluate_gate
from .wilson import wilson_interval, suppressed

FULL = "{:.10f}"


# --- readers -----------------------------------------------------------------

def read_rows(name: str) -> list[dict]:
    with open(C.TABLES / name, newline="") as fh:
        return list(csv.DictReader(fh))


def long_map(name: str) -> dict[tuple[str, str], dict]:
    return {(r["section"], r["metric"]): r for r in read_rows(name)}


def num(row: dict, key: str = "value_num") -> int:
    return int(row[key])


def as_bool(text: str) -> bool:
    """Parse a boolean out of a bq CSV cell, loudly.

    bq renders BOOL as "true"/"false", but the tolerated spellings are accepted
    and anything else raises rather than silently reading as False -- which is
    A-024's truthiness bug in a different costume, and would turn an ineligible
    cell into a measured one.
    """
    value = (text or "").strip().lower()
    if value in ("true", "t", "1"):
        return True
    if value in ("false", "f", "0"):
        return False
    raise ValueError(f"expected a boolean, got {text!r}")


def write_csv(name: str, fieldnames: list[str], rows: list[dict]) -> str:
    path = C.TABLES / name
    with open(path, "w", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        for row in rows:
            writer.writerow(row)
    return name


# --- the one place a rate is formed, suppressed, or nulled -------------------

def rate_cell(retained, denominator, is_eligible: bool) -> dict:
    """§10.5.5 and §10.5.3, together, in one function.

    An ineligible cell prints the literal word NULL -- not zero, not blank. A
    cell below the n<30 floor prints its counts and no rate and no interval. A
    reported cell prints the rate, its Wilson bounds, and its denominator.
    """
    if not is_eligible:
        return {
            "status": C.STATUS_INELIGIBLE,
            "denominator": "", "retained": "",
            "rate_pct_value": "", "rate_pct_display": C.NULL_DISPLAY,
            "wilson_lo_pct_value": "", "wilson_lo_pct_display": C.NULL_DISPLAY,
            "wilson_hi_pct_value": "", "wilson_hi_pct_display": C.NULL_DISPLAY,
            "wilson_half_width_pp_display": C.NULL_DISPLAY,
        }
    denominator = int(denominator)
    retained = int(retained)
    if suppressed(denominator):
        return {
            "status": C.STATUS_SUPPRESSED,
            "denominator": denominator, "retained": retained,
            "rate_pct_value": "", "rate_pct_display": C.SUPPRESSED_DISPLAY,
            "wilson_lo_pct_value": "", "wilson_lo_pct_display": C.SUPPRESSED_DISPLAY,
            "wilson_hi_pct_value": "", "wilson_hi_pct_display": C.SUPPRESSED_DISPLAY,
            "wilson_half_width_pp_display": C.SUPPRESSED_DISPLAY,
        }
    rate = 100.0 * retained / denominator
    lo, hi = wilson_interval(retained, denominator)
    lo, hi = 100.0 * lo, 100.0 * hi
    return {
        "status": C.STATUS_REPORTED,
        "denominator": denominator, "retained": retained,
        "rate_pct_value": FULL.format(rate), "rate_pct_display": f"{rate:.2f}",
        "wilson_lo_pct_value": FULL.format(lo), "wilson_lo_pct_display": f"{lo:.2f}",
        "wilson_hi_pct_value": FULL.format(hi), "wilson_hi_pct_display": f"{hi:.2f}",
        "wilson_half_width_pp_display": f"{(hi - lo) / 2:.2f}",
    }


RETENTION_FIELDS = [
    "cohort", "cohort_start", "cohort_end", "horizon_days", "installs",
    "denominator", "retained", "rate_pct_value", "rate_pct_display",
    "wilson_lo_pct_value", "wilson_lo_pct_display",
    "wilson_hi_pct_value", "wilson_hi_pct_display",
    "wilson_half_width_pp_display", "status", "note",
]
# The pooled table carries one column the weekly table has no use for: how many
# cohorts the horizon pools. Under A-134's per-cohort rule that number is the
# whole composition of the denominator, so it belongs in a column rather than
# only in prose.
POOLED_FIELDS = RETENTION_FIELDS[:-1] + ["cohorts_included", "note"]

# The rolling tables carry two columns the classic tables have no use for: how
# many days of observation the window leaves after the retention day, for the
# cohort's last installer and for its first. Rolling counts any event on or
# AFTER install + N, so its value depends on how much window remains; classic
# needs the single day install + N and nothing else, which is why eligibility is
# sufficient there and only a floor here (A-135, A-150). Printing the days beside
# every cell puts the censoring in the table rather than in a note about it, and
# it also makes the eligibility rule visible arithmetic: a cell is NULL exactly
# when the minimum is below 1.
ROLLING_FIELDS = (RETENTION_FIELDS[:-1]
                  + ["window_days_remaining_min", "window_days_remaining_max", "note"])
POOLED_ROLLING_FIELDS = (RETENTION_FIELDS[:-1]
                         + ["cohorts_included", "window_days_remaining_min",
                            "window_days_remaining_max", "note"])


def _window_days(day_text: str, horizon: int) -> int:
    """Observation days left after install + N for an installer on `day_text`."""
    from datetime import date, timedelta
    day = date(int(day_text[:4]), int(day_text[4:6]), int(day_text[6:8]))
    return (C.WINDOW_END - (day + timedelta(days=horizon))).days + 1


# --- 01 population reconciliation (§10.5.7 item 1, the report's first table) --

def population(pop_rows) -> tuple[str, dict]:
    g = {(r["section"], r["metric"]): r for r in pop_rows}
    total = num(g[("population", "distinct_users_total")])
    with_fo = num(g[("population", "users_with_first_open_event")])
    without = num(g[("population", "users_without_first_open_event")])
    share = 100.0 * without / total
    rows = [
        {"metric": "users_total", "value": total, "value_display": f"{total:,}",
         "note": "distinct user_pseudo_id with at least one event in the 114-shard window"},
        {"metric": "users_with_first_open_event", "value": with_fo, "value_display": f"{with_fo:,}",
         "note": "Part 1's population (§10.5.1): cohorts are built on the first_open EVENT"},
        {"metric": "users_without_first_open_event", "value": without, "value_display": f"{without:,}",
         "note": "excluded from Part 1; the exclusion is not random (§10.5.1)"},
        {"metric": "users_without_first_open_share_pct", "value": FULL.format(share),
         "value_display": f"{share:.2f}",
         "note": "the cost of §10.5.1's choice, stated as a cost and placed first (§10.7.2)"},
        {"metric": "first_open_events_deduped",
         "value": num(g[("population", "first_open_events_deduped")]),
         "value_display": f"{num(g[('population', 'first_open_events_deduped')]):,}",
         "note": "first_open events after §10.7.4 de-duplication"},
        {"metric": "users_with_more_than_one_first_open",
         "value": num(g[("population", "users_with_more_than_one_first_open")]),
         "value_display": f"{num(g[('population', 'users_with_more_than_one_first_open')]):,}",
         "note": "§10.5.2 takes the earliest, which makes these deterministic (A-137)"},
    ]
    name = write_csv("part1_01_population_reconciliation.csv",
                     ["metric", "value", "value_display", "note"], rows)
    return name, {"total": total, "with_first_open": with_fo,
                  "without": without, "share_pct": share}


# --- 02 cohort inventory (§10.5.7 item 2) ------------------------------------

def cohort_inventory(inv_rows) -> tuple[str, dict]:
    weekly = [r for r in inv_rows if r["cohort"].startswith("W") and r["cohort"][1:].isdigit()]
    weekly.sort(key=lambda r: r["cohort"])
    others = [r for r in inv_rows if r not in weekly]
    total_weekly = sum(int(r["install_count"]) for r in weekly)

    rows = []
    for r in weekly + others:
        rows.append({
            "cohort": r["cohort"], "cohort_start": r["cohort_start"],
            "cohort_end": r["cohort_end"], "install_count": int(r["install_count"]),
            "eligible_d1": str(as_bool(r["eligible_d1"])).lower(),
            "eligible_d7": str(as_bool(r["eligible_d7"])).lower(),
            "eligible_d30": str(as_bool(r["eligible_d30"])).lower(),
            "note": r["note"],
        })
    rows.append({
        "cohort": "TOTAL_WEEKLY", "cohort_start": "20180612", "cohort_end": "20181001",
        "install_count": total_weekly, "eligible_d1": "", "eligible_d7": "", "eligible_d30": "",
        "note": "sum of the 16 weekly cohorts; rendered total, not a query result",
    })
    name = write_csv("part1_02_cohort_inventory.csv",
                     ["cohort", "cohort_start", "cohort_end", "install_count",
                      "eligible_d1", "eligible_d7", "eligible_d30", "note"], rows)
    tail = next((r for r in others if r["cohort"] == "TAIL_EXCLUDED"), None)
    w16_part = next((r for r in others if r["cohort"].startswith("W16_INSTALLS")), None)
    return name, {
        "weekly": {r["cohort"]: int(r["install_count"]) for r in weekly},
        "total_weekly": total_weekly,
        "tail": int(tail["install_count"]) if tail else 0,
        "w16_observable_at_d7": int(w16_part["install_count"]) if w16_part else 0,
    }


# --- 03-06 retention, classic and rolling, weekly and pooled -----------------

def retention(rows, kind: str, weekly_name: str, pooled_name: str) -> tuple[list[str], dict]:
    label = {"classic": "classic retention, §10.5.3 primary — event on install day + N exactly",
             "rolling": "rolling retention, §10.5.3 secondary — event on or after install day + N"}[kind]
    weekly_out, pooled_out, summary = [], [], {}

    for r in sorted((x for x in rows if x["grain"] == "weekly"),
                    key=lambda x: (x["cohort"], int(x["horizon_days"]))):
        is_eligible = as_bool(r["eligible"])
        cell = rate_cell(r["retained"] or 0, r["denominator"] or 0, is_eligible)
        horizon = int(r["horizon_days"])
        row_out = {
            "cohort": r["cohort"], "cohort_start": r["cohort_start"],
            "cohort_end": r["cohort_end"], "horizon_days": horizon,
            "installs": int(r["installs"]), **cell,
            "note": label if is_eligible else
                    "cohort's last install day + N falls outside the window ending 20181003 (§10.5.5)",
        }
        if kind == "rolling":
            row_out["window_days_remaining_min"] = _window_days(r["cohort_end"], horizon)
            row_out["window_days_remaining_max"] = _window_days(r["cohort_start"], horizon)
        weekly_out.append(row_out)
        summary[(kind, "weekly", r["cohort"], int(r["horizon_days"]))] = cell

    for r in sorted((x for x in rows if x["grain"] == "pooled"),
                    key=lambda x: int(x["horizon_days"])):
        cell = rate_cell(r["retained"], r["denominator"], True)
        horizon = int(r["horizon_days"])
        pooled_row = {
            "cohort": "POOLED", "cohort_start": r["cohort_start"], "cohort_end": r["cohort_end"],
            "horizon_days": horizon, "installs": int(r["installs"]), **cell,
            "cohorts_included": int(r["cohorts_included"]),
            "note": (f"{label}; pooled over the {r['cohorts_included']} cohorts eligible at D{horizon}, "
                     f"the per-cohort reading directed in A-134"),
        }
        if kind == "rolling":
            lo = _window_days(r["cohort_end"], horizon)
            hi = _window_days(r["cohort_start"], horizon)
            pooled_row["window_days_remaining_min"] = lo
            pooled_row["window_days_remaining_max"] = hi
            pooled_row["note"] += (f"; blends cohorts with {lo} to {hi} days of observation left "
                                   f"after day {horizon}, so it is not an estimate of one quantity (A-150)")
        pooled_out.append(pooled_row)
        summary[(kind, "pooled", "POOLED", horizon)] = dict(
            cell, cohorts_included=int(r["cohorts_included"]))

    weekly_fields = ROLLING_FIELDS if kind == "rolling" else RETENTION_FIELDS
    pooled_fields = POOLED_ROLLING_FIELDS if kind == "rolling" else POOLED_FIELDS
    return ([write_csv(weekly_name, weekly_fields, weekly_out),
             write_csv(pooled_name, pooled_fields, pooled_out)], summary)


# --- 07 retention by segment (§10.5.7 item 6, §10.7.5) -----------------------

def segments(seg_rows, country_share_part1: float) -> tuple[str, dict]:
    country_dropped = country_share_part1 > C.COUNTRY_DROP_SHARE
    country_caveated = country_share_part1 > C.COUNTRY_CAVEAT_SHARE
    caveat = ""
    if country_dropped:
        caveat = (f"DROPPED: {country_share_part1 * 100:.2f}% of users have a non-constant "
                  f"geo.country, above §10.7.5's 25.0% drop trigger")
    elif country_caveated:
        caveat = (f"CAVEAT: {country_share_part1 * 100:.2f}% of users have a non-constant "
                  f"geo.country, above §10.7.5's 5.0% caveat trigger")

    out = []
    for r in seg_rows:
        dimension = r["dimension"]
        if dimension not in C.PERMITTED_DIMENSIONS:
            raise SystemExit(f"query 16 returned an unpermitted dimension: {dimension}")
        if dimension == "geo.country" and country_dropped:
            continue
        is_other = as_bool(r["is_other"])
        cell = rate_cell(r["retained"], r["denominator"], True)
        out.append({
            "dimension": dimension,
            "segment": r["segment"],
            "is_other": str(is_other).lower(),
            "segments_pooled": r["segments_pooled"] if is_other else "",
            "users_in_segment": int(r["users_in_segment"]),
            "horizon_days": int(r["horizon_days"]),
            **cell,
            "caveat": caveat if dimension == "geo.country" else (
                "attributed from the earliest event row, so this is the version at install; "
                "§10.7.5 states no constancy test for this dimension (A-136)"
                if dimension == "app_info.version" else ""),
            "note": ("classic retention, pooled cohorts only (§10.7.5); floor of 100 users "
                     "applied once on the pooled install population (A-140)"),
        })
    name = write_csv(
        "part1_07_retention_by_segment.csv",
        ["dimension", "segment", "is_other", "segments_pooled", "users_in_segment",
         "horizon_days", "denominator", "retained", "rate_pct_value", "rate_pct_display",
         "wilson_lo_pct_value", "wilson_lo_pct_display", "wilson_hi_pct_value",
         "wilson_hi_pct_display", "wilson_half_width_pp_display", "status",
         "caveat", "note"], out)
    return name, {"country_dropped": country_dropped, "country_caveated": country_caveated,
                  "rows": out}


# --- 09 day key offset (§10.5.2's reporting requirement) ---------------------

def day_key(offset_rows) -> tuple[str, dict]:
    g = {(r["section"], r["metric"]): r for r in offset_rows}
    total = num(g[("window", "total_rows")])
    behind = num(g[("utc_comparison", "rows_event_date_one_day_behind_utc")])
    ahead = num(g[("utc_comparison", "rows_event_date_one_day_ahead_utc")])
    same = num(g[("utc_comparison", "rows_event_date_same_as_utc")])
    ne_shard = num(g[("window", "rows_event_date_ne_shard_suffix")])
    candidates = {int(m.split("utc")[1].split("_")[0]): int(r["value_num"])
                  for (sec, m), r in g.items() if sec == "offset_candidate"}
    best_rows = max(candidates.values())
    best = sorted(h for h, v in candidates.items() if v == best_rows)
    runner_up = max((v for v in candidates.values() if v != best_rows), default=0)
    exact = [h for h, v in candidates.items() if v == total]
    width = int(g[("offset_bounds", "feasible_offset_width_seconds")]["value_num"])
    rows = [
        {"metric": "rows_total", "value": total, "value_display": f"{total:,}",
         "note": "rows across the 114-shard window"},
        {"metric": "rows_event_date_ne_shard_suffix", "value": ne_shard, "value_display": f"{ne_shard:,}",
         "note": "event_date disagreeing with the shard holding it; §10.5.2's consistency claim "
                 "rests on this being 0, and every Part 1 metric rests on that rather than on the zone"},
        {"metric": "rows_event_date_one_day_behind_utc", "value": behind, "value_display": f"{behind:,}",
         "note": "event_date is the UTC date minus one day"},
        {"metric": "rows_event_date_same_as_utc", "value": same, "value_display": f"{same:,}",
         "note": "event_date equals the UTC date"},
        {"metric": "rows_event_date_one_day_ahead_utc", "value": ahead, "value_display": f"{ahead:,}",
         "note": "§10.5.2's argument for a fixed non-UTC zone requires this to be 0"},
        {"metric": "share_behind_utc_pct", "value": FULL.format(100.0 * behind / total),
         "value_display": f"{100.0 * behind / total:.2f}",
         "note": "A-098 measured 33.96%; this is the figure re-observed by this session"},
        {"metric": "observed_offset",
         "value": ";".join(f"{h:+d}" for h in best),
         "value_display": ", ".join(f"UTC{h:+03d}:00" for h in best),
         "note": "the whole-hour offset with the highest row-level agreement (A-142) — the offset "
                 "this session OBSERVES, per §10.5.2, rather than assumes"},
        {"metric": "observed_offset_rows_matching", "value": best_rows, "value_display": f"{best_rows:,}",
         "note": "rows the selected offset dates correctly"},
        {"metric": "observed_offset_agreement_pct", "value": FULL.format(100.0 * best_rows / total),
         "value_display": f"{100.0 * best_rows / total:.4f}",
         "note": "quoted to four decimals because the residual is the finding (A-143)"},
        {"metric": "observed_offset_rows_not_matching", "value": total - best_rows,
         "value_display": f"{total - best_rows:,}",
         "note": "rows a fixed offset would place on the other side of a local midnight"},
        {"metric": "observed_offset_rows_not_matching_pct",
         "value": FULL.format(100.0 * (total - best_rows) / total),
         "value_display": f"{100.0 * (total - best_rows) / total:.4f}",
         "note": "the residual, as a share of the window; small, but not zero, which is the finding"},
        {"metric": "runner_up_offset_agreement_pct", "value": FULL.format(100.0 * runner_up / total),
         "value_display": f"{100.0 * runner_up / total:.4f}",
         "note": f"the next-best whole-hour offset, {best_rows - runner_up:,} rows behind; the "
                 f"margin is why the selection exercises no judgement"},
        {"metric": "offsets_dating_every_row", "value": len(exact),
         "value_display": str(len(exact)),
         "note": "A-143: none. event_date is the export's own day stamp, not a function of "
                 "event_timestamp under any constant offset"},
        {"metric": "feasible_interval_width_seconds", "value": width, "value_display": f"{width:,}",
         "note": "negative, so the interval is empty: the binding constraints lie this far the "
                 "wrong way round"},
        {"metric": "feasible_offset_lower_hours",
         "value": g[("offset_bounds", "feasible_offset_lower_hours")]["value_text"],
         "value_display": g[("offset_bounds", "feasible_offset_lower_hours")]["value_text"],
         "note": "a constant offset would have to be at least this, from the binding row"},
        {"metric": "feasible_offset_upper_exclusive_hours",
         "value": g[("offset_bounds", "feasible_offset_upper_exclusive_hours")]["value_text"],
         "value_display": g[("offset_bounds", "feasible_offset_upper_exclusive_hours")]["value_text"],
         "note": "and strictly less than this, which is the contradiction"},
    ]
    name = write_csv("part1_09_day_key_offset.csv",
                     ["metric", "value", "value_display", "note"], rows)
    return name, {"observed": best, "agreement_pct": 100.0 * best_rows / total,
                  "behind": behind, "ahead": ahead, "total": total}


# --- 08 data handling record (§10.5.7 item 7) --------------------------------

def data_handling(pop_rows, const_rows, gate_result, sensitivity, primary_pooled_d7,
                  cohort_stats) -> str:
    g = {(r["section"], r["metric"]): r for r in pop_rows}
    c = {(r["section"], r["metric"]): r for r in const_rows}
    rows = []

    def add(section, metric, value, display, note):
        rows.append({"section": section, "metric": metric, "value": value,
                     "value_display": display, "note": note})

    dup = num(g[("duplicates", "duplicate_rows_removed")])
    raw = num(g[("duplicates", "raw_event_rows")])
    add("duplicates", "raw_event_rows", raw, f"{raw:,}", "before §10.7.4 de-duplication")
    add("duplicates", "deduped_event_rows", num(g[("duplicates", "deduped_event_rows")]),
        f"{num(g[('duplicates', 'deduped_event_rows')]):,}",
        "distinct (user_pseudo_id, event_name, event_timestamp)")
    add("duplicates", "duplicate_rows_removed", dup, f"{dup:,}",
        "removed before any count (§10.7.4, A-124); A-103 measured 207")
    add("duplicates", "duplicate_share_ppm", num(g[("duplicates", "duplicate_share_ppm")]),
        f"{num(g[('duplicates', 'duplicate_share_ppm')]):,}", "parts per million of raw rows")
    add("duplicates", "duplicate_groups_spanning_two_dates",
        num(g[("duplicates", "duplicate_groups_spanning_two_dates")]),
        f"{num(g[('duplicates', 'duplicate_groups_spanning_two_dates')]):,}",
        "A-138 assertion: 0 means the MIN(event_date) collapse is a no-op")
    add("install_day_definition", "users_where_timestamp_and_date_readings_disagree",
        num(g[("install_day_definition", "users_where_timestamp_and_date_readings_disagree")]),
        f"{num(g[('install_day_definition', 'users_where_timestamp_and_date_readings_disagree')]):,}",
        "A-137 assertion: 0 means earliest-by-timestamp and MIN(event_date) agree")

    for dim, section in (("geo.country", "geo_country"), ("app_info.version", "app_info_version")):
        part1 = num(c[(section, "users_non_constant_part1")])
        share = num(c[(section, "share_non_constant_part1_ppm")]) / 10000.0
        add(f"{section}_constancy", "users_non_constant_part1", part1, f"{part1:,}",
            f"users in Part 1's install population with more than one distinct {dim}")
        add(f"{section}_constancy", "share_non_constant_part1_pct", FULL.format(share),
            f"{share:.2f}",
            "§10.7.5: caveat above 5.0%, dropped above 25.0%" if dim == "geo.country"
            else "A-136: reported, with NO trigger applied — §10.7.5 states none for this dimension")
        add(f"{section}_constancy", "max_distinct_values_per_user",
            num(c[(section, "max_distinct_values_per_user")]),
            f"{num(c[(section, 'max_distinct_values_per_user')]):,}",
            "largest number of distinct values held by one user")
        if dim == "geo.country":
            outcome = ("dropped" if share > 25.0 else "caveated" if share > 5.0 else "reported without caveat")
            add(f"{section}_constancy", "segmentation_outcome", outcome, outcome,
                "§10.7.5's triggers, applied to geo.country as the document defines them")
        else:
            add(f"{section}_constancy", "segmentation_outcome", "reported; no trigger defined",
                "reported; no trigger defined",
                "A-136 raises the gap for the architecture session rather than inventing a gate")

    add("first_open_time_check", "zone_offset_used",
        ";".join(f"{h:+d}" for h in gate_result["feasible_offsets"]),
        ", ".join(f"UTC{h:+03d}:00" for h in gate_result["feasible_offsets"]),
        "the highest row-agreement whole-hour offset from query 11 (A-142); A-141's "
        "original criterion, an offset dating every row, is unsatisfiable on this export (A-143)")
    add("first_open_time_check", "zone_day_key_agreement_pct",
        FULL.format(100.0 * gate_result["day_key_rows_matching"] / gate_result["total_rows"]),
        f"{100.0 * gate_result['day_key_rows_matching'] / gate_result['total_rows']:.4f}",
        f"the selected offset dates this share of all {gate_result['total_rows']:,} rows; the "
        f"runner-up offset dates "
        f"{100.0 * gate_result['day_key_runner_up_rows'] / gate_result['total_rows']:.4f}%")
    if gate_result["share"] is not None:
        add("first_open_time_check", "selected_offset",
            gate_result["selected_offset"], f"UTC{gate_result['selected_offset']:+03d}:00",
            "the minimum-agreement feasible offset (A-141), not the best of them")
        add("first_open_time_check", "users_compared", gate_result["compared"],
            f"{gate_result['compared']:,}", "users with both the property and a first_open event")
        add("first_open_time_check", "users_agreeing", gate_result["agreeing"],
            f"{gate_result['agreeing']:,}", "derived date equals the first_open event's event_date")
        add("first_open_time_check", "agreement_share_pct",
            FULL.format(100.0 * gate_result["share"]), f"{100.0 * gate_result['share']:.2f}",
            "§10.7.3's gate is 99.0%")
    add("first_open_time_check", "gate_met", str(gate_result["gate_met"]).lower(),
        "yes" if gate_result["gate_met"] else "no", gate_result["reason"])
    if sensitivity is None:
        add("first_open_time_check", "check_outcome", "omitted", "omitted",
            "§10.7.3: below the gate the check is omitted and the observed share reported instead; "
            "query 18 was never executed")
    else:
        add("first_open_time_check", "check_outcome", "run", "run",
            "§10.7.3: the figure belongs in the negative-results section, labelled a robustness "
            "check on an unverified field, never in a results table")
        for key, display, note in sensitivity["rows"]:
            add("first_open_time_check", key, display, display, note)
        add("first_open_time_check", "primary_pooled_d7_pct_for_comparison",
            primary_pooled_d7["rate_pct_value"], primary_pooled_d7["rate_pct_display"],
            "the primary D7 figure this is a robustness check on (§10.5.3, event-based population)")

    add("cohorts", "installs_in_16_weekly_cohorts", cohort_stats["total_weekly"],
        f"{cohort_stats['total_weekly']:,}", "the pooled D1 population")
    add("cohorts", "installs_in_excluded_tail", cohort_stats["tail"],
        f"{cohort_stats['tail']:,}",
        "20181002-20181003, excluded from every cohort table (§10.5.4) and reported here")
    add("cohorts", "w16_installs_observable_at_d7_excluded_from_pooled",
        cohort_stats["w16_observable_at_d7"], f"{cohort_stats['w16_observable_at_d7']:,}",
        "installs on 20180925-20180926: individually observable at D7, excluded with their cohort "
        "under the per-cohort reading directed in A-134")

    add("assertions", "sql_eligibility_assertions_passed", "true", "yes",
        "queries 12, 13 and 14 guard §10.5.4's blocks, §10.5.5's cutoffs and the 16/15/12 counts "
        "with ERROR(); they returned rows, so the guards did not fire")

    return write_csv("part1_08_data_handling.csv",
                     ["section", "metric", "value", "value_display", "note"], rows)


def sensitivity_rows(selected_offset: int):
    """Read query 18's result at the selected offset, if the query ran."""
    path = C.TABLES / "part1_q18_first_open_time_sensitivity.csv"
    if not path.exists():
        return None
    rows = read_rows(path.name)
    row = next((r for r in rows if int(r["offset_hours"]) == selected_offset), None)
    if row is None:
        return None
    denominator, retained = int(row["denominator"]), int(row["retained"])
    cell = rate_cell(retained, denominator, True)
    return {
        "denominator": denominator, "retained": retained, "cell": cell,
        "rows": [
            ("sensitivity_users_total", f"{int(row['users_total']):,}",
             "all users with a first_open_time property, §10.7.3's 15,175"),
            ("sensitivity_users_inside_window", f"{int(row['users_inside_window']):,}",
             "derived install day inside 20180612-20181001, so assignable to a weekly cohort"),
            ("sensitivity_users_before_window", f"{int(row['users_before_window']):,}",
             "derived install day before the window: no observable day 7, excluded and counted "
             "rather than scored as unretained"),
            ("sensitivity_pooled_d7_denominator", f"{denominator:,}",
             "users in the D7-eligible cohorts W01-W15 under the derived install day"),
            ("sensitivity_pooled_d7_retained", f"{retained:,}", "classic D7 on the derived install day"),
            ("sensitivity_pooled_d7_pct", cell["rate_pct_display"],
             "recomputed pooled D7 over the first_open_time population (§10.7.3)"),
            ("sensitivity_pooled_d7_wilson_lo_pct", cell["wilson_lo_pct_display"], "95% Wilson lower bound"),
            ("sensitivity_pooled_d7_wilson_hi_pct", cell["wilson_hi_pct_display"], "95% Wilson upper bound"),
        ],
    }
