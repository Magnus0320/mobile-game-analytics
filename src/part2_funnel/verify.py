"""Self-verification: re-read what was written and assert it says what it should.

§7.5's self-verification bullet, in Part 2's terms. Every assertion here is about
a rule the document states or an identity the arithmetic forces, not about a
number the data happened to produce, so a failure means the implementation is
wrong rather than the world being surprising. A failure raises; the outputs on
disk are then the product of a failed run and must not be committed.
"""

import csv
import re

from . import audit
from . import config as C
from .report_figures import read_register
from .tables import as_bool, read_rows


class VerificationError(AssertionError):
    pass


def _require(condition, message):
    if not condition:
        raise VerificationError(message)


def _q31():
    rows = read_rows("part2_q31_progression_matrix_and_funnel.csv")
    scalars = {(r["section"], r["key"]): int(r["users"]) for r in rows if r["section"] != "pattern"}
    patterns = [r for r in rows if r["section"] == "pattern"]
    return scalars, patterns


def check_matrix_reconciles():
    """The 32-pattern matrix and SQL's own marginals are two derivations of the
    same numbers inside one query. They must agree."""
    scalars, patterns = _q31()
    flags = [{k: as_bool(p[k]) for k in ("s1", "s2", "s3", "fail_quickplay", "np_start")}
             | {"n": int(p["users"])} for p in patterns]
    total = sum(f["n"] for f in flags)
    _require(total == C.POPULATION,
             f"the progression matrix sums to {total}, not {C.POPULATION}")

    def count(predicate):
        return sum(f["n"] for f in flags if predicate(f))

    expected = {
        ("funnel_raw", "S0"): count(lambda f: True),
        ("funnel_raw", "S1"): count(lambda f: f["s1"]),
        ("funnel_raw", "S2"): count(lambda f: f["s2"]),
        ("funnel_raw", "S3"): count(lambda f: f["s3"]),
        ("funnel_strict", "S0"): count(lambda f: True),
        ("funnel_strict", "S1"): count(lambda f: f["s1"]),
        ("funnel_strict", "S2"): count(lambda f: f["s1"] and f["s2"]),
        ("funnel_strict", "S3"): count(lambda f: f["s1"] and f["s2"] and f["s3"]),
        ("out_of_order", "s2_without_s1"): count(lambda f: f["s2"] and not f["s1"]),
        ("out_of_order", "s3_without_s2"): count(lambda f: f["s3"] and not f["s2"]),
        ("out_of_order", "s3_without_s1"): count(lambda f: f["s3"] and not f["s1"]),
        ("level_end_user", "users_end"): count(lambda f: f["s2"]),
        ("level_end_user", "users_complete"): count(lambda f: f["s3"]),
        ("level_end_user", "users_fail"): count(lambda f: f["fail_quickplay"]),
        ("level_end_user", "users_complete_or_fail"): count(lambda f: f["s3"] or f["fail_quickplay"]),
        ("level_end_user", "users_complete_and_fail"): count(lambda f: f["s3"] and f["fail_quickplay"]),
        ("level_end_user", "end_without_outcome"):
            count(lambda f: f["s2"] and not f["s3"] and not f["fail_quickplay"]),
        ("level_end_user", "outcome_without_end"):
            count(lambda f: (f["s3"] or f["fail_quickplay"]) and not f["s2"]),
        ("parallel_track", "users_nonquickplay_start"): count(lambda f: f["np_start"]),
        ("parallel_track", "users_without_s1"): count(lambda f: not f["s1"]),
        ("parallel_track", "users_without_s1_with_nonquickplay_start"):
            count(lambda f: not f["s1"] and f["np_start"]),
        ("parallel_track", "users_in_both_modes"): count(lambda f: f["s1"] and f["np_start"]),
        ("parallel_track", "users_with_neither_start"):
            count(lambda f: not f["s1"] and not f["np_start"]),
    }
    for key, value in expected.items():
        _require(scalars[key] == value,
                 f"{key}: SQL returned {scalars[key]}, the matrix sums to {value}")
    return f"the 32-pattern matrix sums to {C.POPULATION:,} and reproduces all {len(expected)} of SQL's own marginals"


def check_funnel():
    rows = {r["step"]: r for r in read_rows("part2_03_funnel.csv")}
    _require(set(rows) == set(C.STEPS), "the funnel table must carry exactly S0..S3")
    previous = None
    for step in C.STEPS:
        row = rows[step]
        strict, raw = int(row["users_strict"]), int(row["users_raw"])
        _require(raw == C.EXPECTED_RAW[step],
                 f"{step} raw is {raw}, §10.6.3 states {C.EXPECTED_RAW[step]}")
        _require(strict <= raw, f"{step}: strict {strict} exceeds raw {raw}")
        if previous is not None:
            _require(strict <= previous,
                     f"{step}: strict {strict} exceeds {previous}, so the funnel is not monotone — "
                     f"§10.6.4 makes monotonicity hold by construction")
        previous = strict
    _require(rows["S0"]["step_conversion_status"] == C.STATUS_NOT_APPLICABLE
             and rows["S0"]["step_conversion_pct_display"] == C.NULL_DISPLAY,
             "S0 has no predecessor, so its step-to-step cell must be an explicit null")
    return "the funnel is monotone by construction, every raw count matches §10.6.3, and S0's step-to-step cell is an explicit null"


def check_out_of_order_identity():
    scalars, _ = _q31()
    strict = {s: scalars[("funnel_strict", s)] for s in C.STEPS}
    raw = {s: scalars[("funnel_raw", s)] for s in C.STEPS}
    _require(strict["S2"] + scalars[("out_of_order", "s2_without_s1")] == raw["S2"],
             "strict S2 plus the users with S2 but not S1 must equal raw S2")
    _require(strict["S1"] == raw["S1"],
             "S0 is universal, so strict S1 and raw S1 must be the same number")
    return (f"strict S2 + s2_without_s1 = {strict['S2']:,} + "
            f"{scalars[('out_of_order', 's2_without_s1')]} = {raw['S2']:,} = raw S2")


def check_against_recon():
    """De-duplication cannot change a distinct-user count, and must remove exactly
    the duplicate rows it reports (A-166)."""
    recon = {r["event_name"]: r for r in read_rows("recon_03_event_vocabulary.csv")
             if r["scope"] == "all_shards_per_event"}
    mine = {r["key"]: r for r in read_rows("part2_q30_population_and_vocabulary.csv")
            if r["section"] == "event"}
    _require(set(recon) == set(mine),
             f"event vocabulary differs from the recon's: {set(recon) ^ set(mine)}")
    difference = 0
    for name, row in mine.items():
        _require(int(row["users"]) == int(recon[name]["distinct_users"]),
                 f"{name}: {row['users']} users, the recon measured "
                 f"{recon[name]['distinct_users']} — de-duplication cannot change this")
        _require(int(row["events_raw"]) == int(recon[name]["events"]),
                 f"{name}: raw events differ from the recon's")
        _require(int(row["events_deduped"]) <= int(row["events_raw"]),
                 f"{name}: de-duplication increased the event count")
        difference += int(row["events_raw"]) - int(row["events_deduped"])
    total = {(r["section"], r["key"]): r for r in
             read_rows("part2_q30_population_and_vocabulary.csv")}[("totals", "all_event_names")]
    _require(difference == int(total["duplicate_rows"]),
             f"per-event differences sum to {difference}, the reported duplicate count is "
             f"{total['duplicate_rows']}")
    return (f"all {len(mine)} event names reproduce the recon's distinct-user counts exactly, "
            f"and the per-event event-count differences sum to {difference}, the duplicate total")


def check_rates(name, prefixes):
    for row in read_rows(name):
        for prefix in prefixes:
            status = row[f"{prefix}_status"]
            if status == C.STATUS_REPORTED:
                denominator = int(row[f"{prefix}_denominator"])
                numerator = int(row[f"{prefix}_numerator"])
                _require(denominator >= C.SUPPRESSION_FLOOR,
                         f"{name}: a rate on n={denominator}, below §10.5.3's floor of 30")
                _require(numerator <= denominator, f"{name}: numerator exceeds its denominator")
                _require(float(row[f"{prefix}_lo_display"]) <= float(row[f"{prefix}_pct_display"])
                         <= float(row[f"{prefix}_hi_display"]),
                         f"{name}: a point estimate outside its own Wilson interval")
            elif status == C.STATUS_SUPPRESSED:
                _require(row[f"{prefix}_pct_value"] == "" and row[f"{prefix}_numerator"] != "",
                         f"{name}: a suppressed cell prints its count and no rate")
            elif status == C.STATUS_NOT_APPLICABLE:
                _require(row[f"{prefix}_pct_display"] == C.NULL_DISPLAY,
                         f"{name}: an inapplicable cell must print an explicit null")
            else:
                raise VerificationError(f"{name}: unknown cell status {status!r}")
    return f"{name}: every rate carries its denominator, sits on n >= 30, and contains its own point estimate"


def check_segments():
    rows = read_rows("part2_09_funnel_by_segment.csv")
    by_dimension = {}
    for row in rows:
        if row["step"] != "S0":
            continue
        by_dimension.setdefault(row["dimension"], []).append(row)
    for dimension, segments in by_dimension.items():
        total = sum(int(r["users_s0"]) for r in segments)
        _require(total == C.POPULATION,
                 f"{dimension}: segment users at S0 sum to {total}, not {C.POPULATION} — "
                 f"§10.7.5 pools rather than drops precisely so the shares still sum")
        for row in segments:
            if not as_bool(row["is_other"]):
                _require(int(row["users_s0"]) >= C.SEGMENT_FLOOR,
                         f"{dimension}/{row['segment']}: named at {row['users_s0']} users, "
                         f"below §10.7.5's Part 2 floor of {C.SEGMENT_FLOOR}")
    return (f"all {len(by_dimension)} reported dimensions sum to {C.POPULATION:,} users at S0, "
            f"and no named segment sits below the {C.SEGMENT_FLOOR}-user floor")


README = C.REPO_ROOT / "README.md"
# Only this part's own section. A-118 forbids this session the opener and the
# other parts' sections, and their figures are not this register's to check.
README_PART2 = re.compile(r"^## Part 2\b.*?(?=^## |\Z)", re.M | re.S)


def _audited_documents() -> list[tuple[str, str]]:
    documents = []
    if C.REPORT.exists():
        documents.append(("the report", C.REPORT.read_text()))
    if README.exists():
        match = README_PART2.search(README.read_text())
        if match and match.group(0).strip() != "## Part 2":
            documents.append(("the README's ## Part 2 section", match.group(0)))
    return documents


def check_register_and_audit():
    register = read_register()
    problems = audit.check_register(register)
    _require(not problems, "register integrity: " + "; ".join(problems))
    notes = audit.selftest()

    from .tables import VIEWS
    documents = _audited_documents()
    if documents:
        problems, used = [], set()
        for label, text in documents:
            used |= audit.used_figures(text, register)
            problems += [f"{label}: {p}" for p in audit.audit_tables(text, VIEWS)]
            problems += [f"{label}: {p}"
                         for p in audit.audit_prose(text, register, check_dead=False)]
        # A figure quoted in either document is accounted for; one quoted in
        # neither is a row nobody can check.
        problems += audit.dead_rows(register, used)
        _require(not problems, "audit:\n  - " + "\n  - ".join(problems))
    return (f"{len(register)} register rows resolve to their declared cells and are "
            f"quoted across {len(documents)} audited document(s); the audit self-test "
            f"{len(notes)} cases behaved as required")


def run_all() -> list[str]:
    return [
        check_matrix_reconciles(),
        check_funnel(),
        check_out_of_order_identity(),
        check_against_recon(),
        check_rates("part2_03_funnel.csv", ["share_of_s0", "step_conversion"]),
        check_rates("part2_09_funnel_by_segment.csv", ["share_of_s0", "step_conversion"]),
        check_segments(),
        check_register_and_audit(),
    ]
