"""§7.7 steps 5-7 and 9-12: the structural gate, coercion, and data-quality checks.

The §5 preamble's two-class taxonomy governs everything here. Step 5 is the
single structural gate: past it, no token value can stop the run, and every
remaining fault is counted, reported and thresholded rather than fatal.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

import numpy as np
import pandas as pd
from pandas.arrays import BooleanArray, IntegerArray

from . import config
from .run_state import RunState, StructuralFault

_NON_NEGATIVE_INT_RE = re.compile(r"^[0-9]+$")


# ---------------------------------------------------------------------------
# Step 5 — the single structural gate (§5.4, §7.7 step 5, A-053)
# ---------------------------------------------------------------------------

def _trimmed(df: pd.DataFrame, column: str) -> pd.Series:
    """§5.4: comparison is on the trimmed value."""
    return df[column].astype("string").str.strip()


def _raise_structural(column: str, offenders: dict[str, int]) -> None:
    shown = sorted(offenders.items(), key=lambda kv: (-kv[1], kv[0]))[:10]
    detail = "\n".join(f"    {value!r}: {count} row(s)" for value, count in shown)
    more = "" if len(offenders) <= 10 else f"\n    ... and {len(offenders) - 10} more"
    raise StructuralFault(
        f"Structural fault in column {column!r}: value(s) outside the column's "
        f"token sets (§5.4).\n"
        f"  {len(offenders)} distinct offending value(s):\n{detail}{more}\n"
        "  An unrecognised present value is a structural fault, not a data-quality "
        "fault (§5 preamble): it almost always means the wrong file, a mangled "
        "export, a wrong delimiter, or a different revision of the dataset. The "
        "remedy is to fetch the right file, never to clean this one. No statistic "
        "has been computed and no output has been written."
    )


def structural_gate(df: pd.DataFrame, state: RunState) -> dict[str, dict[str, int]]:
    """Validate all four columns before any statistic exists. Hard stop on any
    value outside its sets, naming the column, the value and its row count.

    Returns the pre-coercion trimmed-token counts per column, which step 9's
    count-conservation assertions are checked against.
    """
    token_counts: dict[str, dict[str, int]] = {}

    # version — the arm set plus the missing set
    trimmed = _trimmed(df, config.ARM_COLUMN)
    counts = trimmed.value_counts()
    token_counts[config.ARM_COLUMN] = {str(k): int(v) for k, v in counts.items()}
    allowed = config.ARM_TOKENS | config.MISSING_TOKENS
    bad = {v: c for v, c in token_counts[config.ARM_COLUMN].items() if v not in allowed}
    if bad:
        _raise_structural(config.ARM_COLUMN, bad)

    # retention flags — true, false and missing sets
    for column in config.RETENTION_COLUMNS:
        trimmed = _trimmed(df, column)
        counts = trimmed.value_counts()
        token_counts[column] = {str(k): int(v) for k, v in counts.items()}
        allowed = config.TRUE_TOKENS | config.FALSE_TOKENS | config.MISSING_TOKENS
        bad = {v: c for v, c in token_counts[column].items() if v not in allowed}
        if bad:
            _raise_structural(column, bad)

    # sum_gamerounds — a non-negative integer, or a value in the missing set
    trimmed = _trimmed(df, config.ENGAGEMENT_COLUMN)
    counts = trimmed.value_counts()
    token_counts[config.ENGAGEMENT_COLUMN] = {str(k): int(v) for k, v in counts.items()}
    bad = {
        v: c for v, c in token_counts[config.ENGAGEMENT_COLUMN].items()
        if v not in config.MISSING_TOKENS and not _NON_NEGATIVE_INT_RE.match(v)
    }
    if bad:
        _raise_structural(config.ENGAGEMENT_COLUMN, bad)

    state.finding(
        step=5,
        finding_id="structural.gate_passed",
        description=(
            "Every value in version, retention_1, retention_7 and sum_gamerounds "
            "lies inside its column's token sets. The file is the file "
            "ARCHITECTURE.md describes."
        ),
        values={
            "distinct_tokens": {c: len(t) for c, t in token_counts.items()},
        },
    )
    return token_counts


# ---------------------------------------------------------------------------
# Step 6 — three-state coercion (§5.4, A-049)
# ---------------------------------------------------------------------------

@dataclass
class Coerced:
    """The coerced frame. Missing is an explicit state, never a sentinel value."""

    userid: pd.Series
    arm: pd.Series              # "string" dtype, pd.NA where missing
    retention: dict[str, pd.Series] = field(default_factory=dict)  # "boolean"
    gamerounds: pd.Series | None = None                            # "Int64"
    n_raw: int = 0


def _coerce_retention(trimmed: pd.Series) -> pd.Series:
    """Map an enumerated token set to a three-state boolean column.

    Truthiness coercion is banned (§5.4): `bool("False")` is `True`, which
    produces a wrong retention rate that passes every eyeball check. Values are
    set from set membership only, and the missing mask is carried separately so
    no sentinel can ever compare equal to False.
    """
    values = trimmed.isin(config.TRUE_TOKENS).to_numpy(dtype=bool)
    is_false = trimmed.isin(config.FALSE_TOKENS).to_numpy(dtype=bool)
    missing = ~(values | is_false)
    return pd.Series(BooleanArray(values, missing), index=trimmed.index)


def coerce(df: pd.DataFrame) -> Coerced:
    """§7.7 step 6. Safe because step 5 passed. No row is dropped, no value guessed."""
    arm_trimmed = _trimmed(df, config.ARM_COLUMN)
    arm_missing = arm_trimmed.isin(config.MISSING_TOKENS)
    arm = arm_trimmed.mask(arm_missing)  # pd.NA where missing

    retention = {
        column: _coerce_retention(_trimmed(df, column))
        for column in config.RETENTION_COLUMNS
    }

    rounds_trimmed = _trimmed(df, config.ENGAGEMENT_COLUMN)
    rounds_missing = rounds_trimmed.isin(config.MISSING_TOKENS).to_numpy(dtype=bool)
    rounds_values = np.zeros(len(rounds_trimmed), dtype="int64")
    present = ~rounds_missing
    if present.any():
        rounds_values[present] = (
            rounds_trimmed.to_numpy()[present].astype("int64")
        )
    gamerounds = pd.Series(
        IntegerArray(rounds_values, rounds_missing), index=rounds_trimmed.index
    )

    return Coerced(
        userid=df[config.ID_COLUMN].astype("string"),
        arm=arm,
        retention=retention,
        gamerounds=gamerounds,
        n_raw=int(len(df)),
    )


# ---------------------------------------------------------------------------
# Step 7 — partition off unassignable rows (§2.2, §5.3, A-051)
# ---------------------------------------------------------------------------

def partition_unassignable(coerced: Coerced, state: RunState) -> pd.Series:
    """Unassignable means a MISSING version and nothing else (A-051).

    A version present but not an arm label is structural and already stopped the
    run at step 5; it never reaches this threshold.
    """
    unassignable = coerced.arm.isna()
    n_unassignable = int(unassignable.sum())
    share = n_unassignable / coerced.n_raw if coerced.n_raw else 0.0

    state.record_denominator("unassignable_rows", n_unassignable)
    state.finding(
        step=7,
        finding_id="unassignable.count",
        description=(
            "Rows whose version is missing were never assigned, so they enter "
            "neither arm of the SRM denominator and are excluded from everything."
        ),
        values={"count": n_unassignable, "share_of_raw_rows": share,
                "raw_rows": coerced.n_raw,
                "threshold": config.UNASSIGNABLE_THRESHOLD},
    )

    if share > config.UNASSIGNABLE_THRESHOLD:
        state.downgrade(
            step=7,
            source="unassignable_rows",
            detail=(
                f"{n_unassignable} rows ({share:.4%} of raw rows) have a missing "
                f"version, exceeding the {config.UNASSIGNABLE_THRESHOLD:.1%} "
                "threshold in §2.2. A missing assignment is a failure of the "
                "assignment or logging mechanism itself."
            ),
            values={"count": n_unassignable, "share": share},
        )
    return unassignable


# ---------------------------------------------------------------------------
# Step 9 — post-coercion assertion group (§5.4, A-049)
# ---------------------------------------------------------------------------

def assert_coercion(
    coerced: Coerced,
    token_counts: dict[str, dict[str, int]],
    state: RunState,
) -> None:
    """Every failure here is a hard stop: it means coercion did not preserve
    the file it was given, which is structural by definition (§5.4)."""

    def fail(message: str) -> None:
        raise StructuralFault(f"Post-coercion assertion failed (§5.4): {message}")

    n_raw = coerced.n_raw
    results: dict[str, object] = {}

    def missing_total(column: str) -> int:
        return sum(c for tok, c in token_counts[column].items()
                   if tok in config.MISSING_TOKENS)

    for column in config.RETENTION_COLUMNS:
        series = coerced.retention[column]
        present = series.dropna()

        observed = set(bool(v) for v in pd.unique(present.to_numpy(dtype=bool))) \
            if len(present) else set()
        if observed != {True, False}:
            fail(
                f"non-missing values of {column!r} form {sorted(observed)}, "
                "not exactly {False, True}"
            )

        n_true = int((series == True).sum())   # noqa: E712 - explicit, not truthiness
        n_false = int((series == False).sum())  # noqa: E712
        n_missing = int(series.isna().sum())
        if n_true + n_false + n_missing != n_raw:
            fail(
                f"{column!r} state counts {n_true}+{n_false}+{n_missing} "
                f"do not sum to the raw row count {n_raw}"
            )

        src_true = sum(c for tok, c in token_counts[column].items()
                       if tok in config.TRUE_TOKENS)
        src_false = sum(c for tok, c in token_counts[column].items()
                        if tok in config.FALSE_TOKENS)
        src_missing = missing_total(column)
        if (n_true, n_false, n_missing) != (src_true, src_false, src_missing):
            fail(
                f"{column!r} coerced counts (T={n_true}, F={n_false}, "
                f"M={n_missing}) do not equal pre-coercion source-token counts "
                f"(T={src_true}, F={src_false}, M={src_missing})"
            )
        results[column] = {"true": n_true, "false": n_false, "missing": n_missing}

    arm_present = coerced.arm.dropna()
    observed_arms = set(str(v) for v in pd.unique(arm_present.to_numpy()))
    if observed_arms != set(config.ARMS):
        fail(
            f"non-missing values of {config.ARM_COLUMN!r} form "
            f"{sorted(observed_arms)}, not exactly {sorted(config.ARMS)}"
        )
    n_arm_missing = int(coerced.arm.isna().sum())
    if n_arm_missing != missing_total(config.ARM_COLUMN):
        fail(
            f"{config.ARM_COLUMN!r} missing count {n_arm_missing} does not equal "
            f"its pre-coercion missing-token total {missing_total(config.ARM_COLUMN)}"
        )
    results[config.ARM_COLUMN] = {
        "arms": sorted(observed_arms), "missing": n_arm_missing
    }

    rounds = coerced.gamerounds
    if str(rounds.dtype) != "Int64":
        fail(f"{config.ENGAGEMENT_COLUMN!r} is {rounds.dtype}, not a nullable integer")
    present_rounds = rounds.dropna()
    if len(present_rounds) and int(present_rounds.min()) < 0:
        fail(f"{config.ENGAGEMENT_COLUMN!r} contains a negative value")
    results[config.ENGAGEMENT_COLUMN] = {
        "missing": int(rounds.isna().sum()),
        "min": int(present_rounds.min()) if len(present_rounds) else None,
        "max": int(present_rounds.max()) if len(present_rounds) else None,
    }

    state.finding(
        step=9,
        finding_id="coercion.assertions_passed",
        description=(
            "Three-state coercion preserved the file: non-missing retention "
            "values are exactly {True, False}, state counts sum to the raw row "
            "count, every coerced state count equals its pre-coercion source-token "
            "total, version's non-missing values are exactly the arm set with the "
            "unassignable count equal to its missing count, and sum_gamerounds is "
            "a non-negative nullable integer."
        ),
        values=results,
    )


# ---------------------------------------------------------------------------
# Step 10 — uniqueness of userid, duplicates classified by case (§5.2, A-066)
# ---------------------------------------------------------------------------

@dataclass
class DuplicateReport:
    n_duplicate_ids: int = 0
    same_arm_identical_ids: list[str] = field(default_factory=list)
    same_arm_conflicting_ids: list[str] = field(default_factory=list)
    cross_arm_ids: list[str] = field(default_factory=list)
    cross_arm_arms: list[str] = field(default_factory=list)
    rows_dropped_as_export_artefact: int = 0
    excluded_ids: set[str] = field(default_factory=set)
    drop_row_positions: set[int] = field(default_factory=set)

    @property
    def is_clean(self) -> bool:
        return self.n_duplicate_ids == 0


def _comparable(value) -> object:
    """A tuple element that treats two missing values as agreeing (A-066)."""
    return None if pd.isna(value) else value


def check_uniqueness(
    coerced: Coerced, unassignable: pd.Series, state: RunState
) -> DuplicateReport:
    """§7.7 step 10. Counts are findings; cross-arm duplicates past 0.1% of raw
    rows are a downgrade. These exclusions do not alter the SRM denominator — it
    was fixed two steps ago, which is what makes §2.2's rule true in code."""
    report = DuplicateReport()
    assignable = ~unassignable

    ids = coerced.userid
    dup_all = ids[ids.duplicated(keep=False)]
    n_dup_ids_all = int(dup_all.nunique())

    sub_ids = ids[assignable]
    counts = sub_ids.value_counts()
    dup_ids = [str(i) for i in counts[counts > 1].index]
    report.n_duplicate_ids = len(dup_ids)

    if dup_ids:
        frame = pd.DataFrame(
            {
                "pos": np.arange(len(ids)),
                "userid": ids,
                "arm": coerced.arm,
                config.RETENTION_COLUMNS[0]: coerced.retention[config.RETENTION_COLUMNS[0]],
                config.RETENTION_COLUMNS[1]: coerced.retention[config.RETENTION_COLUMNS[1]],
                config.ENGAGEMENT_COLUMN: coerced.gamerounds,
            }
        )[assignable.to_numpy()]
        wanted = frame[frame["userid"].isin(dup_ids)]

        for uid, group in wanted.groupby("userid", sort=True):
            arms = sorted(set(str(a) for a in group["arm"]))
            if len(arms) > 1:
                report.cross_arm_ids.append(str(uid))
                report.cross_arm_arms.append("|".join(arms))
                report.excluded_ids.add(str(uid))
                continue
            signatures = {
                tuple(
                    _comparable(row[c])
                    for c in (*config.RETENTION_COLUMNS, config.ENGAGEMENT_COLUMN)
                )
                for _, row in group.iterrows()
            }
            if len(signatures) == 1:
                report.same_arm_identical_ids.append(str(uid))
                keep = int(group["pos"].min())
                extra = [int(p) for p in group["pos"] if int(p) != keep]
                report.drop_row_positions.update(extra)
                report.rows_dropped_as_export_artefact += len(extra)
            else:
                report.same_arm_conflicting_ids.append(str(uid))
                report.excluded_ids.add(str(uid))

    n_cross = len(report.cross_arm_ids)
    share_cross = n_cross / coerced.n_raw if coerced.n_raw else 0.0

    state.finding(
        step=10,
        finding_id="duplicates.uniqueness_assertion",
        description=(
            "userid uniqueness was asserted rather than assumed, and the result is "
            "reported whether or not duplicates exist (§5.2)."
            + ("" if report.is_clean else " Duplicates were found and classified by case.")
        ),
        values={
            "unique_assignable_userids": int(sub_ids.nunique()),
            "assignable_rows": int(assignable.sum()),
            "duplicate_userids_assignable": report.n_duplicate_ids,
            "duplicate_userids_all_rows": n_dup_ids_all,
            "same_arm_identical": len(report.same_arm_identical_ids),
            "same_arm_conflicting": len(report.same_arm_conflicting_ids),
            "cross_arm": n_cross,
            "cross_arm_share_of_raw_rows": share_cross,
            "rows_dropped_as_export_artefact": report.rows_dropped_as_export_artefact,
            "userids_excluded_from_metrics": len(report.excluded_ids),
        },
    )

    if n_dup_ids_all != report.n_duplicate_ids:
        state.finding(
            step=10,
            finding_id="duplicates.span_unassignable",
            description=(
                "Some duplicated userids involve a row whose version is missing. "
                "Unassignable rows are excluded from everything (§5.3), so they take "
                "no part in the §5.2 classification; recorded so the difference in "
                "duplicate-id counts is not mistaken for an inconsistency."
            ),
            values={"duplicate_userids_all_rows": n_dup_ids_all,
                    "duplicate_userids_assignable": report.n_duplicate_ids},
        )

    if share_cross > config.CROSS_ARM_DUPLICATE_THRESHOLD:
        state.downgrade(
            step=10,
            source="cross_arm_duplicates",
            detail=(
                f"{n_cross} cross-arm duplicate userids ({share_cross:.4%} of raw "
                f"rows) exceed the {config.CROSS_ARM_DUPLICATE_THRESHOLD:.1%} "
                "threshold in §5.2. Cross-arm contamination attacks the identifying "
                "assumption rather than merely adding noise."
            ),
            values={"count": n_cross, "share": share_cross},
        )
    return report


# ---------------------------------------------------------------------------
# Step 11 — missing values on the retention flags (§5.3, A-050, A-065)
# ---------------------------------------------------------------------------

def check_missing_values(
    coerced: Coerced, unassignable: pd.Series, state: RunState
) -> dict:
    """§7.7 step 11. Reachable because step 6 coerced missing markers to an
    explicit state instead of raising on them (A-050)."""
    assignable = ~unassignable
    arm_counts = {
        arm: int((assignable & (coerced.arm == arm)).sum()) for arm in config.ARMS
    }
    result: dict[str, dict] = {}

    for metric in config.RETENTION_COLUMNS:
        per_arm = {}
        for arm in config.ARMS:
            in_arm = assignable & (coerced.arm == arm)
            n_missing = int((in_arm & coerced.retention[metric].isna()).sum())
            assigned = arm_counts[arm]
            per_arm[arm] = {
                "missing": n_missing,
                "assigned": assigned,
                "share_of_arm": (n_missing / assigned) if assigned else 0.0,
            }
        result[metric] = per_arm

        shares = [per_arm[a]["share_of_arm"] for a in config.ARMS]
        state.finding(
            step=11,
            finding_id=f"missing.{metric}",
            description=(
                f"Missing values in {metric}, counted per arm and excluded from "
                "that metric only, never from the whole analysis (§5.3). "
                "Differential missingness between arms is reported regardless of "
                "whether any threshold is approached."
            ),
            values={
                **{f"{a}_missing": per_arm[a]["missing"] for a in config.ARMS},
                **{f"{a}_assigned": per_arm[a]["assigned"] for a in config.ARMS},
                **{f"{a}_share": per_arm[a]["share_of_arm"] for a in config.ARMS},
                "differential_pp": (shares[1] - shares[0]) * 100.0,
                "is_primary": metric == config.PRIMARY_METRIC,
            },
        )

        if metric == config.PRIMARY_METRIC:
            for arm in config.ARMS:
                share = per_arm[arm]["share_of_arm"]
                if share > config.PRIMARY_MISSING_THRESHOLD:
                    state.downgrade(
                        step=11,
                        source="primary_metric_missing",
                        detail=(
                            f"Missing {metric} values in arm {arm} are "
                            f"{share:.4%} of that arm's {arm_counts[arm]} assigned "
                            f"rows, exceeding the "
                            f"{config.PRIMARY_MISSING_THRESHOLD:.1%} threshold "
                            "in §5.3."
                        ),
                        values={"arm": arm, "share": share,
                                "missing": per_arm[arm]["missing"]},
                    )
    return {"arm_assigned_counts": arm_counts, "per_metric": result}


# ---------------------------------------------------------------------------
# Step 12 — per-metric analysis populations and the descriptive
#           differential-exclusion check (§2.2, §5.3, §7.7 step 12)
# ---------------------------------------------------------------------------

@dataclass
class Population:
    metric: str
    values: dict[str, np.ndarray] = field(default_factory=dict)   # arm -> bool array
    denominators: dict[str, int] = field(default_factory=dict)
    successes: dict[str, int] = field(default_factory=dict)


def build_populations(
    coerced: Coerced,
    unassignable: pd.Series,
    duplicates: DuplicateReport,
    arm_assigned_counts: dict[str, int],
    state: RunState,
) -> dict[str, Population]:
    """Build each metric's population and record the denominator actually used."""
    assignable = (~unassignable).to_numpy()
    positions = np.arange(coerced.n_raw)

    excluded_by_id = coerced.userid.isin(duplicates.excluded_ids).to_numpy()
    dropped_artefact = np.isin(positions, list(duplicates.drop_row_positions))
    kept = assignable & ~excluded_by_id & ~dropped_artefact

    populations: dict[str, Population] = {}
    exclusion_rows = []

    for metric in config.RETENTION_COLUMNS:
        series = coerced.retention[metric]
        present = (~series.isna()).to_numpy()
        pop = Population(metric=metric)

        for arm in config.ARMS:
            in_arm = (coerced.arm == arm).to_numpy()
            mask = kept & present & in_arm
            # .to_numpy(dtype=bool) raises if any pd.NA survived into the
            # population, so a missing value can never be silently read as False.
            values = series[mask].to_numpy(dtype=bool)
            pop.values[arm] = values
            pop.denominators[arm] = int(values.size)
            pop.successes[arm] = int(values.sum())
            state.record_denominator(f"{metric}.{arm}", int(values.size))

            assigned = arm_assigned_counts[arm]
            exclusion_rows.append(
                {
                    "metric": metric,
                    "arm": arm,
                    "assigned": assigned,
                    "analysed": int(values.size),
                    "excluded": assigned - int(values.size),
                    "excluded_share_of_assigned": (
                        (assigned - int(values.size)) / assigned if assigned else 0.0
                    ),
                }
            )
        populations[metric] = pop

    state.finding(
        step=12,
        finding_id="populations.differential_exclusion",
        description=(
            "Post-exclusion arm counts reported next to the SRM result as a "
            "DESCRIPTIVE check on whether exclusions fell unevenly between arms "
            "(§2.2). No test and no threshold is attached: a second SRM-style test "
            "on a cleaned population would reintroduce exactly the "
            "cleaning-upstream-of-integrity problem the rule exists to prevent."
        ),
        values={"rows": exclusion_rows},
    )
    return populations
