"""Literals from ARCHITECTURE.md §10.5 and §10.7, in one place.

Nothing here is a judgement. Every value is quoted from the document, with the
section that fixes it, so that a reader can check the code against the
specification without reading the code. The verification step asserts the
derived ones against the document's own stated results (16 / 15 / 12), and the
SQL asserts them again independently.
"""

from datetime import date
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
TABLES = REPO_ROOT / "outputs" / "tables"
FIGURES = REPO_ROOT / "outputs" / "figures"

# --- the window (§10.5.4, A-096) ---------------------------------------------
SHARD_FIRST = "20180612"
SHARD_LAST = "20181003"
ANCHOR = date(2018, 6, 12)          # W01 starts at the first shard, not an ISO week
WINDOW_END = date(2018, 10, 3)      # the last shard
N_COHORTS = 16                      # 114 days = 16 whole weeks + 2
TAIL_START = date(2018, 10, 2)      # the 2-day remainder, excluded from every
TAIL_END = date(2018, 10, 3)        # cohort table (§10.5.4)

# --- retention (§10.5.3, §10.5.5) --------------------------------------------
HORIZONS = (1, 7, 30)
# §10.5.5 states these three cutoffs literally; they are window end minus N.
CUTOFFS = {1: date(2018, 10, 2), 7: date(2018, 9, 26), 30: date(2018, 9, 3)}
# §10.5.5: "D1 runs on 16 cohorts, D7 on 15, and D30 on 12."
ELIGIBLE_COHORTS = {1: 16, 7: 15, 30: 12}
SUPPRESSION_FLOOR = 30              # §10.5.3: below this, a count only
RATE_DECIMALS = 2                   # §10.7.6: two decimal places in pp

# --- segmentation (§10.7.5, A-140) -------------------------------------------
PERMITTED_DIMENSIONS = (
    "geo.country", "platform", "device.category", "device.language", "app_info.version",
)
SEGMENT_FLOOR = 100                 # Part 1: report individually at >= 100 users
OTHER_LABEL = "Other"
COUNTRY_CAVEAT_SHARE = 0.050        # above 5.0%: caveat naming the share
COUNTRY_DROP_SHARE = 0.250          # above 25.0%: country segmentation dropped

# --- the first_open_time check (§10.7.3, A-141) ------------------------------
FOT_AGREEMENT_GATE = 0.990          # run the check only at >= 99.0%

# --- cell status vocabulary (§10.5.5) ----------------------------------------
# An ineligible cell is printed as explicitly null -- not zero, not blank, not
# omitted -- so the display string is the literal word, never an empty field.
STATUS_REPORTED = "reported"
STATUS_SUPPRESSED = "suppressed_n_lt_30"
STATUS_INELIGIBLE = "ineligible_window"
NULL_DISPLAY = "NULL"
SUPPRESSED_DISPLAY = "suppressed (n<30)"


def cohort_bounds(index: int) -> tuple[date, date]:
    """The inclusive day range of weekly cohort `index` (1-based), §10.5.4."""
    from datetime import timedelta
    start = ANCHOR + timedelta(days=(index - 1) * 7)
    return start, start + timedelta(days=6)


def eligible(index: int, horizon: int) -> bool:
    """§10.5.5: measurable at day N only if the cohort's LAST install day + N
    falls inside the window."""
    from datetime import timedelta
    _, end = cohort_bounds(index)
    return end + timedelta(days=horizon) <= WINDOW_END
