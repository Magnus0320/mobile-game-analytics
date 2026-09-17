"""Part 1's rendering entrypoint. Execution order lives here (§7.2, §7.5).

BigQuery is not touched from Python at all: the SQL in sql/10-18 has already run
through src/part1_retention/run_query.sh, and its results sit in
outputs/tables/part1_q*.csv with a provenance sidecar each. This entrypoint turns
those into the report tables §10.5.7 requires, draws the figures from those
tables, and verifies what it wrote.

  1  population reconciliation        -> part1_01   (§10.5.7 item 1, report's first table)
  2  cohort inventory                 -> part1_02   (item 2)
  3  classic retention, weekly+pooled -> part1_03, part1_04 (items 3, 4)
  4  rolling retention, weekly+pooled -> part1_05, part1_06 (item 5)
  5  retention by segment             -> part1_07   (item 6)
  6  day key offset observed          -> part1_09   (§10.5.2's reporting requirement)
  7  data handling record             -> part1_08   (item 7)
  8  figures, from the tables above
  9  self-verification, which raises rather than warns
"""

import sys

from . import config as C
from . import figures, tables, verify
from .gate import evaluate as evaluate_gate


def main() -> int:
    written = []

    pop_rows = tables.read_rows("part1_q10_population_and_duplicates.csv")
    inventory_rows = tables.read_rows("part1_q12_cohort_inventory.csv")
    classic_rows = tables.read_rows("part1_q13_classic_retention.csv")
    rolling_rows = tables.read_rows("part1_q14_rolling_retention.csv")
    constancy_rows = tables.read_rows("part1_q15_segment_constancy.csv")
    segment_rows = tables.read_rows("part1_q16_retention_by_segment.csv")
    offset_rows = tables.read_rows("part1_q11_day_key_offset.csv")

    name, population_stats = tables.population(pop_rows)
    written.append(name)

    name, cohort_stats = tables.cohort_inventory(inventory_rows)
    written.append(name)

    names, _ = tables.retention(classic_rows, "classic",
                                "part1_03_classic_retention_weekly.csv",
                                "part1_04_classic_retention_pooled.csv")
    written += names
    names, _ = tables.retention(rolling_rows, "rolling",
                                "part1_05_rolling_retention_weekly.csv",
                                "part1_06_rolling_retention_pooled.csv")
    written += names

    constancy = {(r["section"], r["metric"]): r for r in constancy_rows}
    country_share_part1 = int(
        constancy[("geo_country", "share_non_constant_part1_ppm")]["value_num"]) / 1_000_000.0
    name, segment_stats = tables.segments(segment_rows, country_share_part1)
    written.append(name)

    name, offset_stats = tables.day_key(offset_rows)
    written.append(name)

    gate_result = evaluate_gate()
    sensitivity = (tables.sensitivity_rows(gate_result["selected_offset"])
                   if gate_result["gate_met"] else None)
    primary_pooled_d7 = next(
        r for r in tables.read_rows("part1_04_classic_retention_pooled.csv")
        if int(r["horizon_days"]) == 7)
    written.append(tables.data_handling(pop_rows, constancy_rows, gate_result,
                                        sensitivity, primary_pooled_d7, cohort_stats))

    written += figures.build_all(
        tables.read_rows("part1_04_classic_retention_pooled.csv"),
        tables.read_rows("part1_06_rolling_retention_pooled.csv"),
        tables.read_rows("part1_07_retention_by_segment.csv"))

    print("\nwrote:")
    for name in sorted(written):
        print(f"  outputs/{'figures' if name.endswith('.png') else 'tables'}/{name}")

    print("\nself-verification (§7.5):")
    for note in verify.run_all():
        print(f"  ok — {note}")

    print(f"\npopulation: {population_stats['with_first_open']:,} of "
          f"{population_stats['total']:,} users have a first_open event; "
          f"{population_stats['share_pct']:.2f}% of the sample is excluded from Part 1 (§10.5.1)")
    print(f"day key: observed offset "
          f"{', '.join(f'UTC{h:+03d}:00' for h in offset_stats['observed'])}, dating "
          f"{offset_stats['agreement_pct']:.4f}% of rows; no offset dates every row (A-143)")
    print(f"first_open_time gate: "
          f"{'met' if gate_result['gate_met'] else 'NOT met'} — the check "
          f"{'ran' if sensitivity else 'is omitted, and the share is reported instead'}")
    if segment_stats["country_dropped"]:
        print("country segmentation: DROPPED above §10.7.5's 25.0% non-constancy trigger")
    elif segment_stats["country_caveated"]:
        print("country segmentation: reported with §10.7.5's caveat")
    return 0


if __name__ == "__main__":
    sys.exit(main())
