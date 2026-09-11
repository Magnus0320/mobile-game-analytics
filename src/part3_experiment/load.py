"""§7.7 steps 2-4: verify the input, read it as text, check the column set."""

from __future__ import annotations

import hashlib
import re
from pathlib import Path

import pandas as pd

from . import config
from .run_state import RunState, StructuralFault

_SHA256_RE = re.compile(r"`([0-9a-f]{64})`")
_ROWCOUNT_RE = re.compile(r"row count of ([0-9]+) data rows")


def sha256_of_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as fh:
        for block in iter(lambda: fh.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def read_recorded_provenance(
    assumptions_path: Path = config.ASSUMPTIONS_PATH,
    entry_id: str = config.PROVENANCE_ENTRY_ID,
) -> tuple[str, int]:
    """Parse the recorded SHA-256 and row count out of assumptions.md (A-064).

    The checksum is deliberately not duplicated into code: §7.7 step 2 verifies
    against "the value recorded in assumptions.md", and a second copy would give
    the one authoritative value two sources of truth. The parse is strict and
    fails loudly, so markdown brittleness cannot degrade into a skipped check.
    """
    if not assumptions_path.exists():
        raise FileNotFoundError(f"assumptions.md not found at {assumptions_path}")

    text = assumptions_path.read_text(encoding="utf-8")
    lines = text.splitlines()

    starts = [i for i, ln in enumerate(lines) if ln.startswith(f"### {entry_id} ")]
    if len(starts) != 1:
        raise StructuralFault(
            f"Expected exactly one assumptions.md entry heading for {entry_id}, "
            f"found {len(starts)}. The dataset provenance entry required by §5.5 "
            f"must exist and be unique before the run can verify its input."
        )
    start = starts[0]
    end = next((i for i in range(start + 1, len(lines))
                if lines[i].startswith("### A-")), len(lines))
    block = "\n".join(lines[start:end])

    hashes = _SHA256_RE.findall(block)
    if len(hashes) != 1:
        raise StructuralFault(
            f"Expected exactly one backticked 64-hex-character SHA-256 in "
            f"assumptions.md entry {entry_id}, found {len(hashes)}."
        )

    counts = _ROWCOUNT_RE.findall(block)
    if len(counts) != 1:
        raise StructuralFault(
            f"Expected exactly one 'row count of N data rows' phrase in "
            f"assumptions.md entry {entry_id}, found {len(counts)}."
        )

    return hashes[0], int(counts[0])


def verify_input(state: RunState, csv_path: Path = config.RAW_CSV_PATH) -> dict:
    """§7.7 step 2. Hard stop on a missing file or a checksum mismatch."""
    if not csv_path.exists():
        raise FileNotFoundError(
            f"Raw input not found at {csv_path}. data/raw/ is git-ignored (§5.5); "
            f"fetch the dataset as documented in the README before running."
        )

    expected_sha, recorded_rows = read_recorded_provenance()
    actual_sha = sha256_of_file(csv_path)

    if actual_sha != expected_sha:
        raise StructuralFault(
            "Input SHA-256 does not match the value recorded in assumptions.md "
            f"entry {config.PROVENANCE_ENTRY_ID}.\n"
            f"  expected: {expected_sha}\n"
            f"  actual:   {actual_sha}\n"
            f"  file:     {csv_path}\n"
            "A different copy may be a different revision of the file, which is "
            "precisely what this check exists to catch. Do not proceed."
        )

    # Recorded as a denominator so §7.7 step 20 asserts it equals the raw row
    # count pandas actually sees. The provenance figure and the computed figure
    # therefore cannot disagree by one and send a reader hunting for a phantom
    # off-by-one: A-072 states the counting convention, and this enforces it.
    state.record_denominator("recorded_row_count", recorded_rows)

    state.finding(
        step=2,
        finding_id="input.checksum_verified",
        description=(
            "Raw input located and its SHA-256 verified against the value "
            f"recorded in assumptions.md entry {config.PROVENANCE_ENTRY_ID}."
        ),
        values={
            "dataset_slug": config.DATASET_SLUG,
            "file_name": csv_path.name,
            "sha256": actual_sha,
            "recorded_row_count": recorded_rows,
        },
    )
    return {"sha256": actual_sha, "recorded_row_count": recorded_rows,
            "path": str(csv_path), "file_name": csv_path.name}


def read_raw_text(csv_path: Path = config.RAW_CSV_PATH) -> pd.DataFrame:
    """§7.7 step 3. Every column as text, no dtype inference, NA filtering OFF.

    `na_filter=False` and `keep_default_na=False` are load-bearing (A-059).
    Without them pandas converts empty fields and the tokens NA, N/A, NaN, nan,
    null, NULL and None into float NaN *before* §5.4's token sets ever see them,
    at which point the missing-set comparison runs against objects that are not
    strings and the per-spelling source-token counts step 9 asserts on are
    unrecoverable. This is the same class of silent bug as the truthiness
    coercion §5.4 bans.
    """
    return pd.read_csv(
        csv_path,
        dtype=str,
        na_filter=False,
        keep_default_na=False,
        engine="c",
    )


def check_columns(df: pd.DataFrame, state: RunState) -> None:
    """§7.7 step 4. Record the raw row count; hard stop on a column-set mismatch."""
    actual = frozenset(df.columns)
    if actual != config.EXPECTED_COLUMN_SET:
        missing = sorted(config.EXPECTED_COLUMN_SET - actual)
        unexpected = sorted(actual - config.EXPECTED_COLUMN_SET)
        raise StructuralFault(
            "Column set is not the five columns ARCHITECTURE.md describes.\n"
            f"  expected: {sorted(config.EXPECTED_COLUMN_SET)}\n"
            f"  actual:   {sorted(actual)}\n"
            f"  missing:  {missing}\n"
            f"  unexpected: {unexpected}"
        )

    n_raw = int(len(df))
    state.record_denominator("raw_rows", n_raw)
    state.finding(
        step=4,
        finding_id="input.raw_shape",
        description="Raw row count and column set recorded.",
        values={"raw_rows": n_raw, "columns": list(df.columns)},
    )

    recorded = state.denominators.get("recorded_row_count")
    if recorded is not None:
        state.finding(
            step=4,
            finding_id="input.row_count_vs_record",
            description=(
                "Raw row count pandas sees, compared against the data-row count "
                f"recorded in assumptions.md {config.PROVENANCE_ENTRY_ID}. Both "
                "exclude the header row. Step 20 asserts they are equal."
            ),
            values={"recorded": recorded, "observed": n_raw,
                    "agree": bool(recorded == n_raw)},
        )

    if n_raw != config.DOCUMENTED_ROW_COUNT:
        state.finding(
            step=4,
            finding_id="input.row_count_mismatch",
            description=(
                "Raw row count differs from the documented size of the dataset. "
                "Reported as a finding; nothing in the analysis is adjusted for it."
            ),
            values={"documented": config.DOCUMENTED_ROW_COUNT, "observed": n_raw,
                    "difference": n_raw - config.DOCUMENTED_ROW_COUNT},
        )
