"""The 95% Wilson score interval (§10.5.3), and the one suppression rule.

§10.5.3 chose Wilson over Wald because cohort denominators run from tens to
thousands and Wald misbehaves at small n and near 0 or 1, and over a bootstrap
because a closed form on a single proportion needs no seed and no resample
count. A-139 keeps the z constant and the suppression cutoff each in exactly one
place: a rule written five times is five chances for one of them to be written
as <= 30.
"""

from statistics import NormalDist

from .config import SUPPRESSION_FLOOR

# The 97.5th percentile of the standard normal, taken from the standard library
# rather than typed as 1.96, which is not that number. Its exact double is
# 1.9599639845400534; A-139 quotes it as 1.959963984540054, which is the same
# value one unit in the last place out. The constant is DERIVED here rather than
# written down, so the code carries the exact value whatever the entry rounds to,
# and the discrepancy is recorded as a finding rather than corrected in an
# append-only entry.
Z_95 = NormalDist().inv_cdf(0.975)


def wilson_interval(successes: int, n: int, z: float = Z_95) -> tuple[float, float]:
    """Return (lower, upper) as proportions in [0, 1].

    centre     = (p + z^2/2n) / (1 + z^2/n)
    half-width = z/(1 + z^2/n) * sqrt(p(1-p)/n + z^2/4n^2)
    """
    if n <= 0:
        raise ValueError("Wilson interval is undefined for n = 0")
    if not 0 <= successes <= n:
        raise ValueError(f"successes {successes} outside 0..{n}")
    p = successes / n
    z2 = z * z
    denom = 1.0 + z2 / n
    centre = (p + z2 / (2 * n)) / denom
    half = (z / denom) * ((p * (1 - p) / n + z2 / (4 * n * n)) ** 0.5)
    return max(0.0, centre - half), min(1.0, centre + half)


def suppressed(n: int | None) -> bool:
    """§10.5.3's floor, in the one place it is applied: a cell whose denominator
    is below 30 is reported as a count only -- no rate, no interval."""
    return n is None or n < SUPPRESSION_FLOOR
