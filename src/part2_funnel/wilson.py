"""The 95% Wilson score interval, and the one suppression rule.

§10.6.4 applies §10.5.3's interval reasoning to the funnel unchanged: Wilson
rather than Wald because step denominators run from tens to thousands and Wald
misbehaves at small n and near 0 or 1, and rather than a bootstrap because a
closed form on a single proportion needs no seed and no resample count.

THIS IS A SECOND COPY of the logic A-139 fixed for Part 1, and the duplication is
deliberate (A-163). §8 lists the other build session's paths under what neither
build session may touch, so `src/part1_retention/wilson.py` is not imported: that
would make a completed, committed and reported part a runtime dependency of a
later one. The duplication is only dangerous if the two copies can disagree, so
in both of them the constant is DERIVED from the standard library rather than
written down. The files are two; the number is one.
"""

from statistics import NormalDist

from .config import SUPPRESSION_FLOOR

# The 97.5th percentile of the standard normal, taken from the standard library
# rather than typed as 1.96, which is not that number.
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
