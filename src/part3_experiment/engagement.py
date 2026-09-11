"""§7.7 step 17: sum_gamerounds descriptives, with and without the extreme row.

§5.1's decision is to KEEP the extreme observation in the primary analysis and
report a both-ways sensitivity check on sum_gamerounds statistics only, with the
retained version primary in all cases. Silent deletion is a defect. The value is
disclosed with its arm and described as implausible-but-unverifiable: a value of
that size is more likely a logging artefact or an automated client than a human,
but this dataset contains nothing that can distinguish those.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from . import config
from .run_state import RunState


def engagement_descriptives(coerced, unassignable: pd.Series, duplicates,
                            state: RunState) -> dict:
    assignable = (~unassignable).to_numpy()
    positions = np.arange(coerced.n_raw)
    excluded_by_id = coerced.userid.isin(duplicates.excluded_ids).to_numpy()
    dropped_artefact = np.isin(positions, list(duplicates.drop_row_positions))
    present = (~coerced.gamerounds.isna()).to_numpy()
    keep = assignable & ~excluded_by_id & ~dropped_artefact & present

    n_missing = int(((~present) & assignable).sum())
    rounds = coerced.gamerounds[keep].to_numpy(dtype="int64")
    arms = coerced.arm[keep].to_numpy()
    state.record_denominator("engagement.all", int(rounds.size))

    # The extreme row is the MAXIMUM, with ties handled explicitly (A-067).
    # No outlier-detection rule is applied: §5.1 speaks of one specific known
    # observation, not of a class, and a fence or z-score cutoff could reach
    # further than the document authorises.
    max_value = int(rounds.max())
    is_max = rounds == max_value
    n_tied = int(is_max.sum())
    max_arms = sorted(set(str(a) for a in arms[is_max]))

    # A single pooled cap, applied to both arms, so the difference between the
    # reported means does not partly reflect a difference between the caps (A-068).
    cap = float(np.percentile(rounds, config.WINSOR_PERCENTILE))

    def summarise(values: np.ndarray) -> dict:
        winsorised = np.minimum(values, cap)
        return {
            "n": int(values.size),
            "mean": float(values.mean()),
            "median": float(np.median(values)),
            "std": float(values.std(ddof=1)) if values.size > 1 else float("nan"),
            "min": int(values.min()), "max": int(values.max()),
            "winsorised_mean": float(winsorised.mean()),
        }

    rows = []
    for arm in (*config.ARMS, "both"):
        sel = np.ones(rounds.size, dtype=bool) if arm == "both" else (arms == arm)
        with_row = summarise(rounds[sel])
        without = summarise(rounds[sel & ~is_max]) if (sel & ~is_max).any() else None
        for label, summary in (("with_extreme", with_row), ("without_extreme", without)):
            if summary is None:
                continue
            rows.append({"arm": arm, "variant": label, **summary})
        state.record_denominator(f"engagement.{arm}", int(sel.sum()))

    # Binned distribution for the figure, so the figure derives from a table.
    edges = [0, 1, 2, 5, 10, 20, 30, 50, 75, 100, 150, 200, 300, 500, 1000]
    bins = []
    for arm in config.ARMS:
        values = rounds[arms == arm]
        for i, low in enumerate(edges):
            high = edges[i + 1] if i + 1 < len(edges) else None
            count = int(((values >= low) & (values < high)).sum()) if high is not None \
                else int((values >= low).sum())
            bins.append({"arm": arm, "bin_low": low,
                         "bin_high": high if high is not None else -1,
                         "count": count})

    result = {
        "rows": rows,
        "bins": bins,
        "winsor_percentile": config.WINSOR_PERCENTILE,
        "winsor_cap": cap,
        "extreme_value": max_value,
        "extreme_arm": "|".join(max_arms),
        "extreme_tied_rows": n_tied,
        "missing_sum_gamerounds": n_missing,
        "n_analysed": int(rounds.size),
    }

    state.finding(
        step=17,
        finding_id="engagement.descriptives",
        description=(
            "sum_gamerounds summarised with and without the extreme observation, "
            "with the retained version primary in all cases (§5.1, A-021), "
            f"alongside the median and a mean winsorised at the pooled "
            f"{config.WINSOR_PERCENTILE:.0f}th percentile (cap {cap:.0f}). The "
            "extreme value is disclosed with its arm; it is "
            "implausible-but-unverifiable, and this dataset contains nothing that "
            "can adjudicate whether it is a human, a logging artefact or an "
            "automated client. It is kept because removing rows from a randomised "
            "experiment on the basis of an outcome variable is a post-randomisation "
            "selection process, and because it is already counted in the SRM "
            "denominator fixed at step 8."
        ),
        values={k: v for k, v in result.items() if k not in ("rows", "bins")},
    )
    if n_missing:
        state.finding(
            step=17,
            finding_id="engagement.missing",
            description=(
                "Missing sum_gamerounds values affect engagement descriptives only "
                "and have no effect on the retention analysis (§5.3)."
            ),
            values={"missing": n_missing},
        )
    return result
