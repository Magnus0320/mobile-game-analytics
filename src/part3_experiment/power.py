"""§7.7 step 13: power on the primary metric only (§3).

Descriptive of the sensitivity this fixed sample happens to have — it answers
"what could this experiment have seen". It is NOT a sample-size calculation and
the report may not phrase it as one (§3).

Power is never evaluated at the observed effect size (§1.7, A-014): observed-effect
post-hoc power is a monotone re-expression of the p-value and carries no
information the p-value does not.
"""

from __future__ import annotations

import math

from scipy import optimize, stats

from . import config


def power_at_effect(p_control: float, delta: float, n_control: int,
                    n_variant: int, alpha: float = config.ALPHA) -> float:
    """Power of a two-sided two-proportion z-test at an absolute difference.

    Pooled variance under the null and unpooled under the alternative, which is
    the same asymmetry §4.1 requires of the test and its interval.
    """
    p_variant = p_control + delta
    if not (0.0 <= p_variant <= 1.0):
        return float("nan")

    pooled = (n_control * p_control + n_variant * p_variant) / (n_control + n_variant)
    se_null = math.sqrt(pooled * (1 - pooled) * (1 / n_control + 1 / n_variant))
    se_alt = math.sqrt(
        p_control * (1 - p_control) / n_control
        + p_variant * (1 - p_variant) / n_variant
    )
    if se_alt == 0:
        return float("nan")

    z_crit = stats.norm.ppf(1 - alpha / 2)
    upper = (delta - z_crit * se_null) / se_alt
    lower = (-delta - z_crit * se_null) / se_alt
    return float(stats.norm.cdf(upper) + stats.norm.cdf(lower))


def detectable_effect(p_control: float, target_power: float, n_control: int,
                      n_variant: int, alpha: float = config.ALPHA) -> float:
    """Smallest absolute difference detectable at `target_power`, in proportion."""

    def gap(delta: float) -> float:
        return power_at_effect(p_control, delta, n_control, n_variant, alpha) - target_power

    hi = min(1.0 - p_control, p_control) if p_control < 0.5 else 1.0 - p_control
    hi = max(hi, 1e-6)
    lo = 1e-9
    if gap(hi) < 0:
        return float("nan")
    return float(optimize.brentq(gap, lo, hi, xtol=1e-12, rtol=1e-12))


def compute_power(p_control: float, n_control: int, n_variant: int) -> dict:
    """§3's three-row table, plus the curve behind the power figure."""
    mde = config.MDE_PP / 100.0
    power_at_mde = power_at_effect(p_control, mde, n_control, n_variant)
    detectable = {
        target: detectable_effect(p_control, target, n_control, n_variant)
        for target in config.POWER_TARGETS
    }

    d80_pp = detectable[0.80] * 100.0
    # §3 requires ONE sentence comparing the 80%-power detectable effect against
    # the 1.00 pp action threshold and stating which is larger. It is reported
    # because §3 requires it, and it feeds nothing: R4 and R5 are selected solely
    # by where CI7 sits relative to +/-1.00 pp (A-062).
    if d80_pp < config.MDE_PP:
        comparison = (
            f"The smallest effect detectable at 80% power is {d80_pp:.2f} pp, which "
            f"is smaller than the {config.MDE_PP:.2f} pp action threshold: this "
            "sample can detect effects smaller than the one we would act on."
        )
    elif d80_pp > config.MDE_PP:
        comparison = (
            f"The smallest effect detectable at 80% power is {d80_pp:.2f} pp, which "
            f"is larger than the {config.MDE_PP:.2f} pp action threshold: this "
            "sample cannot reliably detect effects at the size we would act on."
        )
    else:
        comparison = (
            f"The smallest effect detectable at 80% power is {d80_pp:.2f} pp, "
            f"exactly equal to the {config.MDE_PP:.2f} pp action threshold."
        )

    curve = []
    steps = 120
    for i in range(steps + 1):
        delta_pp = 3.0 * i / steps
        curve.append(
            {
                "effect_pp": delta_pp,
                "power": power_at_effect(p_control, delta_pp / 100.0,
                                         n_control, n_variant),
            }
        )

    return {
        "baseline_control_rate": p_control,
        "n_control": n_control,
        "n_variant": n_variant,
        "alpha": config.ALPHA,
        "effect_pp": config.MDE_PP,
        "power_at_mde": power_at_mde,
        "detectable_at_80_pp": detectable[0.80] * 100.0,
        "detectable_at_95_pp": detectable[0.95] * 100.0,
        "comparison_sentence": comparison,
        "curve": curve,
    }
