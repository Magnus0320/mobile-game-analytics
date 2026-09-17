"""Self-verification: re-read what was written and assert it says what it should.

§7.5's self-verification bullet, in Part 1's terms. Every assertion here is about
a rule the document states, not about a number the data happened to produce, so a
failure means the implementation is wrong rather than the world being surprising.
A failure raises; the outputs on disk are then the product of a failed run and
must not be committed (A-070's discipline, carried across).
"""

import csv

from . import config as C


class VerificationError(AssertionError):
    pass


def _read(name):
    with open(C.TABLES / name, newline="") as fh:
        return list(csv.DictReader(fh))


def _require(condition, message):
    if not condition:
        raise VerificationError(message)


def check_eligibility_literals():
    """§10.5.5's 16 / 15 / 12, recomputed from the anchored blocks."""
    for horizon, expected in C.ELIGIBLE_COHORTS.items():
        got = sum(1 for i in range(1, C.N_COHORTS + 1) if C.eligible(i, horizon))
        _require(got == expected,
                 f"§10.5.5 eligibility: D{horizon} should have {expected} eligible cohorts, computed {got}")
    for horizon, cutoff in C.CUTOFFS.items():
        from datetime import timedelta
        _require(C.WINDOW_END - timedelta(days=horizon) == cutoff,
                 f"§10.5.5 cutoff for D{horizon} should be {cutoff}")
    _require(C.cohort_bounds(1)[0].strftime("%Y%m%d") == "20180612"
             and C.cohort_bounds(16)[1].strftime("%Y%m%d") == "20181001",
             "§10.5.4 blocks: W01 must start 20180612 and W16 must end 20181001")


def check_weekly(name, label):
    rows = _read(name)
    _require(len(rows) == C.N_COHORTS * len(C.HORIZONS),
             f"{label}: expected {C.N_COHORTS * len(C.HORIZONS)} cells, found {len(rows)}")
    for horizon, expected in C.ELIGIBLE_COHORTS.items():
        cells = [r for r in rows if int(r["horizon_days"]) == horizon]
        measured = [r for r in cells if r["status"] in (C.STATUS_REPORTED, C.STATUS_SUPPRESSED)]
        ineligible = [r for r in cells if r["status"] == C.STATUS_INELIGIBLE]
        _require(len(measured) == expected,
                 f"{label} D{horizon}: expected {expected} measurable cohorts, found {len(measured)}")
        _require(len(measured) + len(ineligible) == C.N_COHORTS,
                 f"{label} D{horizon}: every one of the {C.N_COHORTS} cohorts must appear")
        for r in ineligible:
            _require(r["rate_pct_display"] == C.NULL_DISPLAY,
                     f"{label} {r['cohort']} D{horizon}: an ineligible cell must display "
                     f"{C.NULL_DISPLAY!r}, found {r['rate_pct_display']!r}")
            _require(r["denominator"] == "" and r["retained"] == "",
                     f"{label} {r['cohort']} D{horizon}: an ineligible cell carries no counts")
            _require(r["installs"] != "",
                     f"{label} {r['cohort']} D{horizon}: §10.5.5 still shows the install count")
    for r in rows:
        if r["status"] == C.STATUS_REPORTED:
            _require(r["denominator"] != "", f"{label}: a rate with no denominator")
            _require(int(r["denominator"]) >= C.SUPPRESSION_FLOOR,
                     f"{label}: a rate on n={r['denominator']}, below §10.5.3's floor of 30")
            _require(int(r["retained"]) <= int(r["denominator"]),
                     f"{label}: retained exceeds the denominator")
            _require(float(r["wilson_lo_pct_value"]) <= float(r["rate_pct_value"])
                     <= float(r["wilson_hi_pct_value"]),
                     f"{label}: the point estimate falls outside its own Wilson interval")
        elif r["status"] == C.STATUS_SUPPRESSED:
            _require(r["rate_pct_value"] == "" and r["retained"] != "",
                     f"{label}: a suppressed cell prints its count and no rate (§10.5.3)")
    return rows


def check_pooled_matches_weekly(weekly_rows, pooled_name, label):
    """A-134's per-cohort rule makes this an exact identity at every horizon."""
    pooled = _read(pooled_name)
    _require(len(pooled) == len(C.HORIZONS), f"{label}: one pooled row per horizon")
    for row in pooled:
        horizon = int(row["horizon_days"])
        eligible = [r for r in weekly_rows
                    if int(r["horizon_days"]) == horizon and r["status"] != C.STATUS_INELIGIBLE]
        _require(len(eligible) == C.ELIGIBLE_COHORTS[horizon],
                 f"{label}: D{horizon} pools {C.ELIGIBLE_COHORTS[horizon]} cohorts")
        denominator = sum(int(r["denominator"]) for r in eligible)
        retained = sum(int(r["retained"]) for r in eligible)
        _require(int(row["denominator"]) == denominator,
                 f"{label} pooled D{horizon}: denominator {row['denominator']} is not the sum "
                 f"{denominator} of its eligible weekly cells — A-134's per-cohort rule requires it")
        _require(int(row["retained"]) == retained,
                 f"{label} pooled D{horizon}: retained {row['retained']} is not the sum {retained}")
    return pooled


def check_rolling_dominates(classic_rows, rolling_rows, label="weekly"):
    """Rolling >= classic at the same cohort and horizon, over REPORTED cells only.

    Under A-135 both tables are null on the same cells, so the comparison is
    defined wherever it runs; that is half the reason the reading was directed.
    """
    index = {(r["cohort"], r["horizon_days"]): r for r in classic_rows}
    compared = 0
    for r in rolling_rows:
        key = (r["cohort"], r["horizon_days"])
        other = index.get(key)
        _require(other is not None, f"{label}: {key} missing from the classic table")
        _require(other["status"] == r["status"],
                 f"{label}: {key} has status {r['status']} rolling and {other['status']} classic; "
                 f"A-135 makes both tables null on the same cells")
        if r["status"] == C.STATUS_REPORTED:
            _require(int(r["retained"]) >= int(other["retained"]),
                     f"{label}: rolling retention below classic at {key}, which the two "
                     f"definitions make impossible")
            compared += 1
    return compared


def check_population_and_cohorts():
    pop = {r["metric"]: r for r in _read("part1_01_population_reconciliation.csv")}
    total = int(pop["users_total"]["value"])
    with_fo = int(pop["users_with_first_open_event"]["value"])
    without = int(pop["users_without_first_open_event"]["value"])
    _require(with_fo + without == total,
             "population reconciliation: the two parts must sum to the total")

    inventory = _read("part1_02_cohort_inventory.csv")
    weekly = [r for r in inventory if r["cohort"].startswith("W") and r["cohort"][1:].isdigit()]
    _require(len(weekly) == C.N_COHORTS, f"cohort inventory: {C.N_COHORTS} weekly cohorts")
    tail = next(r for r in inventory if r["cohort"] == "TAIL_EXCLUDED")
    total_weekly = next(r for r in inventory if r["cohort"] == "TOTAL_WEEKLY")
    summed = sum(int(r["install_count"]) for r in weekly)
    _require(int(total_weekly["install_count"]) == summed,
             "cohort inventory: the total row must be the sum of the weekly rows")
    _require(summed + int(tail["install_count"]) == with_fo,
             f"cohort inventory: {summed} weekly installs plus {tail['install_count']} tail installs "
             f"must account for all {with_fo} users with a first_open event")
    for r in weekly:
        for horizon in C.HORIZONS:
            index = int(r["cohort"][1:])
            expected = "true" if C.eligible(index, horizon) else "false"
            _require(r[f"eligible_d{horizon}"] == expected,
                     f"cohort inventory: {r['cohort']} eligibility at D{horizon} disagrees with §10.5.5")
    return with_fo, summed


def check_segments(pooled_classic, total_weekly_installs):
    rows = _read("part1_07_retention_by_segment.csv")
    if not rows:
        return 0
    pooled = {int(r["horizon_days"]): int(r["denominator"]) for r in pooled_classic}
    dimensions = sorted({r["dimension"] for r in rows})
    for dimension in dimensions:
        _require(dimension in C.PERMITTED_DIMENSIONS,
                 f"segments: {dimension} is not one of §10.7.5's five permitted dimensions")
        for horizon in C.HORIZONS:
            cells = [r for r in rows
                     if r["dimension"] == dimension and int(r["horizon_days"]) == horizon]
            _require(cells, f"segments: {dimension} has no cells at D{horizon}")
            summed = sum(int(r["denominator"]) for r in cells)
            _require(summed == pooled[horizon],
                     f"segments: {dimension} denominators sum to {summed} at D{horizon}, "
                     f"but the pooled denominator is {pooled[horizon]} — §10.7.5 pools sub-floor "
                     f"segments rather than dropping them precisely so this holds")
        users = sum(int(r["users_in_segment"]) for r in cells)
        _require(users == total_weekly_installs,
                 f"segments: {dimension} covers {users} users, not the {total_weekly_installs} "
                 f"in the pooled install population")
        for r in cells:
            if r["is_other"] == "true":
                _require(int(r["users_in_segment"]) >= 0 and r["segments_pooled"] != "",
                         f"segments: the Other row must carry the number of segments pooled")
            else:
                _require(int(r["users_in_segment"]) >= C.SEGMENT_FLOOR,
                         f"segments: {r['segment']} is named with {r['users_in_segment']} users, "
                         f"below §10.7.5's floor of {C.SEGMENT_FLOOR}")
    return len(rows)


def run_all() -> list[str]:
    notes = []
    check_eligibility_literals()
    notes.append("§10.5.5's 16/15/12 and its three cutoff dates recomputed from the anchored blocks")

    classic_weekly = check_weekly("part1_03_classic_retention_weekly.csv", "classic weekly")
    rolling_weekly = check_weekly("part1_05_rolling_retention_weekly.csv", "rolling weekly")
    notes.append("both weekly tables: 48 cells each, 16/15/12 measurable, the rest explicitly NULL")

    classic_pooled = check_pooled_matches_weekly(
        classic_weekly, "part1_04_classic_retention_pooled.csv", "classic")
    rolling_pooled = check_pooled_matches_weekly(
        rolling_weekly, "part1_06_rolling_retention_pooled.csv", "rolling")
    notes.append("every pooled denominator and numerator equals the sum of its eligible weekly cells")

    compared = check_rolling_dominates(classic_weekly, rolling_weekly)
    check_rolling_dominates(classic_pooled, rolling_pooled, "pooled")
    notes.append(f"rolling >= classic on all {compared} reported weekly cells and all pooled cells")

    with_fo, total_weekly = check_population_and_cohorts()
    notes.append(f"cohort installs plus the excluded tail account for all {with_fo} users "
                 f"with a first_open event")

    segment_cells = check_segments(classic_pooled, total_weekly)
    notes.append(f"{segment_cells} segment cells: permitted dimensions only, denominators summing "
                 f"to the pooled denominator at every horizon, no named segment below the floor")
    return notes
