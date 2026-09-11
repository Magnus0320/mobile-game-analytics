"""§7.7 steps 14-16: primary inference, conflict evaluation, guardrail inference."""

from __future__ import annotations

import math

import numpy as np
from scipy import stats

from . import bootstrap, config
from .run_state import RunState


def _rates(population) -> dict:
    n_c = population.denominators[config.ARM_CONTROL]
    n_v = population.denominators[config.ARM_VARIANT]
    k_c = population.successes[config.ARM_CONTROL]
    k_v = population.successes[config.ARM_VARIANT]
    p_c = k_c / n_c
    p_v = k_v / n_v
    return {
        "n_control": n_c, "n_variant": n_v,
        "successes_control": k_c, "successes_variant": k_v,
        "rate_control": p_c, "rate_variant": p_v,
        "rate_control_pp": p_c * 100.0, "rate_variant_pp": p_v * 100.0,
        "delta_pp": (p_v - p_c) * 100.0,
    }


def analytic_interval(p_c: float, n_c: int, p_v: float, n_v: int,
                      level: float = config.CI_LEVEL) -> tuple[float, float, float]:
    """Unpooled (Wald) interval on the difference, in percentage points.

    Unpooled for the interval and pooled for the test is deliberate (§4.1, A-015):
    estimating the difference is a different problem from testing whether it is
    zero, and under the alternative the two arms do not share a proportion.
    """
    se = math.sqrt(p_c * (1 - p_c) / n_c + p_v * (1 - p_v) / n_v)
    z = stats.norm.ppf(1 - (1 - level) / 2)
    delta = p_v - p_c
    return ((delta - z * se) * 100.0, (delta + z * se) * 100.0, se * 100.0)


def pooled_z_test(k_c: int, n_c: int, k_v: int, n_v: int) -> dict:
    """Two-sided two-proportion z-test, pooled variance, NO continuity correction.

    Pooled because under H0 the two arms share a single proportion, so the
    standard error is estimated from the combined success rate (§4.1). Yates'
    correction is omitted: with tens of thousands per cell it would shift the
    p-value by an amount invisible at reported precision while making the test
    inconsistent with the uncorrected interval printed beside it (A-016).
    """
    pooled = (k_c + k_v) / (n_c + n_v)
    se = math.sqrt(pooled * (1 - pooled) * (1 / n_c + 1 / n_v))
    delta = k_v / n_v - k_c / n_c
    z = delta / se
    p = float(2 * stats.norm.sf(abs(z)))
    return {"z_statistic": float(z), "p_value": p,
            "pooled_proportion": float(pooled), "se_pooled_pp": se * 100.0}


def primary_inference(population, rng: np.random.Generator, state: RunState) -> dict:
    """§7.7 step 14 on retention_7 — the single decision-eligible test."""
    r = _rates(population)
    test = pooled_z_test(r["successes_control"], r["n_control"],
                         r["successes_variant"], r["n_variant"])
    lo, hi, se_unpooled = analytic_interval(
        r["rate_control"], r["n_control"], r["rate_variant"], r["n_variant"]
    )
    replicates = bootstrap.stratified_replicates(
        population.values[config.ARM_CONTROL],
        population.values[config.ARM_VARIANT],
        rng,
    )
    boot_lo, boot_hi = bootstrap.percentile_interval(replicates)
    mc_se = bootstrap.monte_carlo_se(replicates)
    ep_lo_se, ep_hi_se = bootstrap.endpoint_monte_carlo_se(replicates)

    result = {
        **r, **test,
        "analytic_ci_low_pp": lo, "analytic_ci_high_pp": hi,
        "se_unpooled_pp": se_unpooled,
        "bootstrap_ci_low_pp": boot_lo, "bootstrap_ci_high_pp": boot_hi,
        "bootstrap_mc_se_pp": mc_se,
        "bootstrap_endpoint_mc_se_low_pp": ep_lo_se,
        "bootstrap_endpoint_mc_se_high_pp": ep_hi_se,
        "n_resamples": config.N_RESAMPLES,
        "alpha": config.ALPHA,
        "significant": bool(test["p_value"] < config.ALPHA),
    }
    state.finding(
        step=14,
        finding_id="primary.inference",
        description=(
            "Primary inference on retention_7: pooled-variance two-sided z-test, "
            "unpooled analytic interval, and the seeded stratified bootstrap with "
            f"{config.N_RESAMPLES} resamples giving the percentile interval and its "
            "Monte Carlo standard error. The estimand is the intention-to-treat "
            "effect on assigned players (§4.1, A-007)."
        ),
        values={k: v for k, v in result.items()},
    )
    return result, replicates


def evaluate_conflict(primary: dict, state: RunState) -> dict:
    """§7.7 step 15 / §4.3. Sets precondition R6 if the two instruments disagree.

    They share a point estimate, so they cannot disagree about the sign. The two
    possible disagreements are enumerated by §4.3. Containment of zero is closed
    (A-060).
    """
    p = primary["p_value"]
    lo, hi = primary["bootstrap_ci_low_pp"], primary["bootstrap_ci_high_pp"]
    ci_contains_zero = bool(lo <= 0.0 <= hi)
    significant = bool(p < config.ALPHA)

    case = None
    if significant and ci_contains_zero:
        case = "p<alpha with CI containing zero"
    elif (not significant) and (not ci_contains_zero):
        case = "p>=alpha with CI excluding zero"

    conflict = case is not None
    result = {
        "conflict": conflict,
        "case": case,
        "p_value": p,
        "significant": significant,
        "ci_contains_zero": ci_contains_zero,
        "bootstrap_mc_se_pp": primary["bootstrap_mc_se_pp"],
    }

    state.finding(
        step=15,
        finding_id="conflict.evaluation",
        description=(
            "Reconciliation of the z-test and the bootstrap (§4.3). The z-test is "
            "the confirmatory instrument and decides significance; the bootstrap is "
            "the estimation instrument and decides the action-threshold comparison. "
            + (
                f"CONFLICT: {case}. Reported as a finding with its Monte Carlo "
                "error, which is what lets a reader judge whether the discrepancy "
                "is on the order of the bootstrap's own resampling noise. "
                "Re-running with a different seed or resample count to resolve it "
                "is forbidden (§4.3 item 4)."
                if conflict else
                "No conflict: the test and the interval agree."
            )
        ),
        values=result,
    )
    return result


def guardrail_inference(population, rng: np.random.Generator, state: RunState) -> dict:
    """§7.7 step 16 on retention_1 — the same estimators, INTERVAL ONLY.

    No p-value is computed here, deliberately. §1.2 allocates the guardrail no
    alpha and forbids any confirmatory significance claim; the write-up may say
    "the 95% interval excludes zero", which describes an interval, but never "the
    effect on D1 retention was significant". Not computing the test statistic at
    all is the strongest guarantee that it cannot leak into the write-up.
    """
    r = _rates(population)
    lo, hi, se_unpooled = analytic_interval(
        r["rate_control"], r["n_control"], r["rate_variant"], r["n_variant"]
    )
    replicates = bootstrap.stratified_replicates(
        population.values[config.ARM_CONTROL],
        population.values[config.ARM_VARIANT],
        rng,
    )
    boot_lo, boot_hi = bootstrap.percentile_interval(replicates)
    mc_se = bootstrap.monte_carlo_se(replicates)

    result = {
        **r,
        "analytic_ci_low_pp": lo, "analytic_ci_high_pp": hi,
        "se_unpooled_pp": se_unpooled,
        "bootstrap_ci_low_pp": boot_lo, "bootstrap_ci_high_pp": boot_hi,
        "bootstrap_mc_se_pp": mc_se,
        "n_resamples": config.N_RESAMPLES,
        "interval_excludes_zero": bool(not (boot_lo <= 0.0 <= boot_hi)),
        "test_performed": False,
    }
    state.finding(
        step=16,
        finding_id="guardrail.inference",
        description=(
            "Guardrail inference on retention_1: point estimate and 95% intervals "
            "reported with the same precision as the primary, with NO alpha "
            "allocated and NO test decision (§1.2, A-003). The guardrail can hold a "
            "recommendation but never create one."
        ),
        values=result,
    )
    return result, replicates
