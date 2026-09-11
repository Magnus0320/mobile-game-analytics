"""§7.7 step 8: the sample ratio mismatch test, on the assignment population.

The denominator is the literal rule of §2.2: the number of raw rows carrying a
valid coerced arm label, fixed BEFORE any exclusion. Duplicate userids, nulls in
either retention flag, and the extreme sum_gamerounds row are all counted here,
including rows excluded from the metric analysis moments later. Execution order
is what enforces it — this step runs before steps 10 and 11 (A-052).
"""

from __future__ import annotations

import pandas as pd
from scipy import stats

from . import config
from .run_state import RunState


def srm_test(coerced, unassignable: pd.Series, state: RunState) -> dict:
    assignable = ~unassignable
    counts = {
        arm: int((assignable & (coerced.arm == arm)).sum()) for arm in config.ARMS
    }
    n = counts[config.ARM_CONTROL] + counts[config.ARM_VARIANT]

    # Primary test: two-sided exact binomial of the gate_30 count against p=0.5.
    # Exact rather than chi-square as primary because it removes the
    # continuity-correction question entirely (§2.2, A-010).
    binom = stats.binomtest(counts[config.ARM_CONTROL], n, config.SRM_NULL_P,
                            alternative="two-sided")
    exact_p = float(binom.pvalue)

    # Chi-square goodness-of-fit (1 df) reported alongside, because it is the
    # form a reviewer with an experimentation background expects, and agreement
    # between the two is itself a small reassurance (§2.2).
    expected = n * config.SRM_NULL_P
    chi2_stat = sum((counts[a] - expected) ** 2 / expected for a in config.ARMS)
    chi2_p = float(stats.chi2.sf(chi2_stat, df=1))

    observed_share = counts[config.ARM_CONTROL] / n if n else float("nan")
    tripped = exact_p < config.SRM_FAIL_P

    result = {
        "n": n,
        "control_count": counts[config.ARM_CONTROL],
        "variant_count": counts[config.ARM_VARIANT],
        "expected_per_arm": expected,
        "observed_control_share": observed_share,
        "imbalance_rows": counts[config.ARM_CONTROL] - counts[config.ARM_VARIANT],
        "exact_binomial_p": exact_p,
        "chi2_statistic": float(chi2_stat),
        "chi2_df": 1,
        "chi2_p": chi2_p,
        "failure_threshold": config.SRM_FAIL_P,
        "tripped": bool(tripped),
    }

    state.record_denominator("srm_n", n)
    for arm in config.ARMS:
        state.record_denominator(f"assigned.{arm}", counts[arm])

    # Reported unconditionally, whether or not it trips. An SRM check that is
    # only mentioned when it fails is not a check (§2.2).
    state.finding(
        step=8,
        finding_id="srm.result",
        description=(
            "Sample ratio mismatch tested on the assignment population against a "
            "hypothesised 1:1 allocation (A-008), by two-sided exact binomial test "
            "with the 1-df chi-square goodness-of-fit statistic reported alongside. "
            "The denominator is fixed before any exclusion (§2.2)."
        ),
        values=result,
    )

    if tripped:
        state.downgrade(
            step=8,
            source="srm",
            detail=(
                f"SRM exact binomial p = {exact_p:.3g} is below the "
                f"{config.SRM_FAIL_P} failure threshold (§2.3). Assignment "
                "integrity is not established. The full analysis is still computed "
                "and reported; only the recommendation is withheld (§2.4). This "
                "downgrade is permanent for this deliverable: the input is a static "
                "public CSV with no assignment log and no upstream owner, so there "
                "is no path from 'SRM tripped' back to 'resolved'."
            ),
            values=result,
        )
    return result
