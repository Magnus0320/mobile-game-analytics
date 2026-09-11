"""The seeded stratified bootstrap of §4.2.

Resampling scheme: each arm is resampled with replacement to its OWN observed
size, so every replicate preserves the observed allocation. Pooling the arms and
resampling the combination would destroy the arm structure and estimate the wrong
sampling distribution.

The resample is performed literally, by drawing row indices (A-063). Drawing each
replicate's success count from Binomial(n, k/n) would be an exact identity rather
than an approximation and would run far faster, but a reviewer checking that the
bootstrap does what §4.2 describes should be able to see the resampling.
"""

from __future__ import annotations

import numpy as np

from . import config


def stratified_replicates(
    control: np.ndarray,
    variant: np.ndarray,
    rng: np.random.Generator,
    n_resamples: int = config.N_RESAMPLES,
    chunk: int = config.BOOTSTRAP_CHUNK,
) -> np.ndarray:
    """Replicates of (variant rate - control rate), in percentage points."""
    if control.dtype != np.bool_ or variant.dtype != np.bool_:
        raise TypeError("bootstrap inputs must be boolean arrays with no missing state")

    n_control = control.size
    n_variant = variant.size
    out = np.empty(n_resamples, dtype=np.float64)

    done = 0
    while done < n_resamples:
        k = min(chunk, n_resamples - done)
        idx_c = rng.integers(0, n_control, size=(k, n_control))
        idx_v = rng.integers(0, n_variant, size=(k, n_variant))
        rate_c = control[idx_c].mean(axis=1)
        rate_v = variant[idx_v].mean(axis=1)
        out[done:done + k] = (rate_v - rate_c) * 100.0
        done += k
    return out


def percentile_interval(replicates: np.ndarray,
                        level: float = config.CI_LEVEL) -> tuple[float, float]:
    """Percentile interval (§4.2, A-019), linear interpolation (A-071).

    Percentile rather than BCa: the statistic is a difference of two proportions —
    smooth, essentially unbiased and near-symmetric at these sample sizes — so
    BCa would correct for skew that is not present. Basic (reverse-percentile) is
    rejected for the same reason, and it can place an endpoint outside the
    feasible range for a proportion difference.
    """
    tail = (1.0 - level) / 2.0 * 100.0
    lo, hi = np.percentile(replicates, [tail, 100.0 - tail],
                           method=config.PERCENTILE_METHOD)
    return float(lo), float(hi)


def monte_carlo_se(replicates: np.ndarray) -> float:
    """The bootstrap standard error of the estimate (§4.2).

    Reported alongside the interval so a reader can tell resampling noise from
    substance; this is also what §4.3 needs to judge a test/bootstrap conflict.
    """
    return float(np.std(replicates, ddof=1))


def endpoint_monte_carlo_se(replicates: np.ndarray,
                            level: float = config.CI_LEVEL) -> tuple[float, float]:
    """Supplementary: Monte Carlo error of the two percentile ENDPOINTS.

    §4.2 defines "Monte Carlo error" as the bootstrap SE of the estimate, which
    `monte_carlo_se` returns and which is the figure reported under that name.
    This additional quantity is labelled separately and exists because §4.3 asks
    the reader to judge whether a conflict is on the order of the bootstrap's own
    resampling noise, which is a question about the endpoints.
    """
    b = replicates.size
    tail = (1.0 - level) / 2.0
    density_se = []
    for q in (tail, 1.0 - tail):
        lo, hi = np.percentile(
            replicates,
            [max(0.0, (q - 0.01)) * 100.0, min(1.0, (q + 0.01)) * 100.0],
            method=config.PERCENTILE_METHOD,
        )
        density = (hi - lo) / 0.02 if hi > lo else np.nan
        density_se.append(float(density * np.sqrt(q * (1 - q) / b)))
    return density_se[0], density_se[1]
