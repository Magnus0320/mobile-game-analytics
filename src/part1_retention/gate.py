"""§10.7.3's 99.0% gate on the first_open_time sensitivity check.

The gate is evaluated here, from the committed results of query 11 (which whole-
hour UTC offsets date this export) and query 17 (agreement under each offset).
A-141 fixed the selection rule before either number existed, and A-142 replaced
its zone criterion after query 11 showed that criterion to be unsatisfiable --
no constant offset dates every row, the feasible interval being empty by 93
seconds (A-143). What stands:

  * the zone is the whole-hour offset with the HIGHEST row-level agreement in
    query 11, which measures the day key and knows nothing about
    first_open_time; on this export that is UTC-07:00 at 99.9785% of rows,
    against 97.3586% for the runner-up, a margin of 149,335 rows;
  * if two offsets tie exactly on row agreement, the LOWER of their agreement
    shares is taken against the gate -- the conservative direction A-141 chose,
    kept, since the check exists to probe an unverified field and must not run
    because a favourable zone was chosen for it;
  * the check runs only at >= 99.0%. Below it, query 18 is never executed and the
    observed share is reported in its place.

Run as a module it exits 0 when the gate is met and 1 when it is not, which is
what run_part1.sh branches on.
"""

import csv
import sys

from .config import FOT_AGREEMENT_GATE, TABLES


def _rows(name):
    with open(TABLES / name, newline="") as fh:
        return list(csv.DictReader(fh))


def day_key_offsets() -> tuple[dict[int, int], int]:
    """Row-level agreement per whole-hour offset, from query 11."""
    total = None
    matches = {}
    for row in _rows("part1_q11_day_key_offset.csv"):
        if row["section"] == "window" and row["metric"] == "total_rows":
            total = int(row["value_num"])
        elif row["section"] == "offset_candidate":
            hours = int(row["metric"].split("utc")[1].split("_")[0])
            matches[hours] = int(row["value_num"])
    if total is None:
        raise SystemExit("query 11 result carries no total_rows")
    return matches, total


def selected_offsets() -> tuple[list[int], int, int, int]:
    """A-142: the offset(s) with the highest row-level agreement.

    Returns (offsets, rows matching, total rows, runner-up rows matching). More
    than one offset comes back only on an exact tie, which is when A-141's
    take-the-lower rule applies.
    """
    matches, total = day_key_offsets()
    best = max(matches.values())
    runner_up = max((m for m in matches.values() if m != best), default=0)
    return sorted(h for h, m in matches.items() if m == best), best, total, runner_up


def agreement_by_offset() -> dict[int, tuple[int, int]]:
    """offset hours -> (users agreeing, users compared), from query 17."""
    out, compared = {}, None
    for row in _rows("part1_q17_first_open_time_agreement.csv"):
        if row["section"] == "coverage" and row["metric"] == "users_with_both":
            compared = int(row["value_num"])
    for row in _rows("part1_q17_first_open_time_agreement.csv"):
        if row["section"] == "agreement":
            hours = int(row["metric"].split("utc")[1].split("_")[0])
            out[hours] = (int(row["value_num"]), compared)
    return out


def evaluate() -> dict:
    """Apply A-141 as amended by A-142, and return the whole basis of the decision."""
    offsets, rows_matching, total_rows, runner_up = selected_offsets()
    agreement = agreement_by_offset()
    per_offset = {h: agreement[h] for h in offsets if h in agreement}
    if not per_offset:
        return {
            "feasible_offsets": offsets,
            "total_rows": total_rows,
            "day_key_rows_matching": rows_matching,
            "day_key_runner_up_rows": runner_up,
            "selected_offset": None,
            "agreeing": None,
            "compared": None,
            "share": None,
            "gate": FOT_AGREEMENT_GATE,
            "gate_met": False,
            "reason": "the selected offset has no agreement figure",
        }
    # A-141, kept by A-142: on a tie, the lower share, never the better of them.
    selected = min(per_offset, key=lambda h: per_offset[h][0] / per_offset[h][1])
    agreeing, compared = per_offset[selected]
    share = agreeing / compared
    return {
        "feasible_offsets": offsets,
        "total_rows": total_rows,
        "day_key_rows_matching": rows_matching,
        "day_key_runner_up_rows": runner_up,
        "selected_offset": selected,
        "agreeing": agreeing,
        "compared": compared,
        "share": share,
        "gate": FOT_AGREEMENT_GATE,
        "gate_met": share >= FOT_AGREEMENT_GATE,
        "reason": ("agreement at or above the 99.0% gate"
                   if share >= FOT_AGREEMENT_GATE
                   else "agreement below the 99.0% gate; §10.7.3 omits the check"),
        "per_offset": per_offset,
    }


def main() -> int:
    result = evaluate()
    offsets = ", ".join(f"UTC{h:+03d}:00" for h in result["feasible_offsets"]) or "none"
    total = result["total_rows"]
    print(f"day key: highest-agreement whole-hour offset (query 11, A-142): {offsets}")
    print(f"         {result['day_key_rows_matching']:,} of {total:,} rows "
          f"= {100 * result['day_key_rows_matching'] / total:.4f}%, against "
          f"{100 * result['day_key_runner_up_rows'] / total:.4f}% for the runner-up")
    if result["share"] is None:
        print("no agreement figure at a feasible offset; the gate cannot be met")
        return 1
    print(f"selected offset: UTC{result['selected_offset']:+03d}:00")
    print(f"agreement: {result['agreeing']} of {result['compared']} users "
          f"= {result['share'] * 100:.2f}%  against a {result['gate'] * 100:.1f}% gate")
    print("GATE MET — §10.7.3's check runs" if result["gate_met"]
          else "GATE NOT MET — §10.7.3 omits the check; the share is reported instead")
    return 0 if result["gate_met"] else 1


if __name__ == "__main__":
    sys.exit(main())
