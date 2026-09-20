"""Literals from ARCHITECTURE.md §10.6 and §10.7, in one place.

Nothing here is a judgement. Every value is quoted from the document, with the
section that fixes it, so a reader can check the code against the specification
without reading the code. The SQL asserts the load-bearing ones independently
(A-171) and verify.py re-checks them against the written CSVs.
"""

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
TABLES = REPO_ROOT / "outputs" / "tables"
FIGURES = REPO_ROOT / "outputs" / "figures"
REPORT = REPO_ROOT / "reports" / "part2_progression_funnel.md"

# --- the window and the sample (§10.7.1, A-096) ------------------------------
SHARD_FIRST = "20180612"
SHARD_LAST = "20181003"
SHARD_COUNT = 114
SHARD_ROWS = 50000                  # every shard holds exactly this many
RAW_ROWS = 5700000                  # 114 x 50,000

# --- population and counting unit (§10.6.2) ----------------------------------
POPULATION = 15175                  # all distinct user_pseudo_id in the range
# first_open is NOT a funnel step; the funnel begins at "present in the window".

# --- the four steps (§10.6.3), fixed by the document -------------------------
STEPS = ("S0", "S1", "S2", "S3")
STEP_EVENT = {
    "S0": None,                     # presence in the window, not an event test
    "S1": "level_start_quickplay",
    "S2": "level_end_quickplay",
    "S3": "level_complete_quickplay",
}
STEP_LABEL = {
    "S0": "Present in the window",
    "S1": "Started a level",
    "S2": "Finished a level attempt",
    "S3": "Completed a level",
}
# §10.6.3 prints these "so the build session can check its own arithmetic
# against a known figure". They are invariant under §10.7.4 (A-171).
EXPECTED_RAW = {"S0": 15175, "S1": 10166, "S2": 8168, "S3": 5676}

# --- §10.6.4's two reporting triggers, and §10.6.5's ---------------------------
OUT_OF_ORDER_TRIGGER = 0.010        # above 1.0% of the step's raw population
LEVEL_END_TRIGGER = 0.010           # above 1.0% shortfall

# §10.6.5's quoted event-level figures, on the recon's RAW counts. Part 2's are
# de-duplicated (§10.7.4, A-166), so these are the comparison, not the answer.
RESCOPE_QUOTED_LEVEL_END = {
    "level_end_quickplay": 349729,
    "level_complete_quickplay": 191088,
    "level_fail_quickplay": 137035,
}
LEVEL_END_EVENT = "level_end_quickplay"
LEVEL_END_OUTCOMES = ("level_complete_quickplay", "level_fail_quickplay")

# --- §10.6.5's seven diagnostics: reported once, never steps -------------------
DIAGNOSTIC_EVENTS = (
    "screen_view", "user_engagement", "session_start", "post_score",
    "level_fail_quickplay", "spend_virtual_currency", "in_app_purchase",
)

# --- A-172's parallel track: a labelled diagnostic, never a step --------------
NONQUICKPLAY_START = "level_start"

# --- §10.6.1's re-scope thresholds, from §10.3 -------------------------------
RESCOPE_EVENT_THRESHOLD = 1000      # at least 1,000 revenue-positive events
RESCOPE_COVERAGE_THRESHOLD = 0.005  # at least 0.5% of the denominator

# --- rates, intervals, suppression (§10.5.3 via §10.6.4, §10.7.6) ------------
SUPPRESSION_FLOOR = 30              # below this, a count only: no rate, no interval
RATE_DECIMALS = 2                   # §10.7.6: two decimal places in pp

# --- segmentation (§10.7.5 as generalised by A-154, A-174) -------------------
PERMITTED_DIMENSIONS = (
    "geo.country", "platform", "device.category", "device.language", "app_info.version",
)
SEGMENT_FLOOR = 200                 # Part 2: report individually at >= 200 users at S0
OTHER_LABEL = "Other"
CONSTANCY_CAVEAT_SHARE = 0.050      # above 5.0%: caveat naming the share
CONSTANCY_DROP_SHARE = 0.250        # above 25.0%: that dimension is dropped
# A-154: name what earliest-event attribution measures, in the table's caption.
ATTRIBUTION_MEANING = {
    "app_info.version": "version at install",
    "device.language": "language at first observed event",
    "geo.country": "country at first observed event",
    "platform": "platform at first observed event",
    "device.category": "device category at first observed event",
}

# --- cell status vocabulary --------------------------------------------------
STATUS_REPORTED = "reported"
STATUS_SUPPRESSED = "suppressed_n_lt_30"
STATUS_NOT_APPLICABLE = "not_applicable"
NULL_DISPLAY = "NULL"
SUPPRESSED_DISPLAY = "suppressed (n<30)"
