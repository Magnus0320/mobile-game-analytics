"""Part 2's rendering entrypoint. Execution order lives here (§7.2, §7.5).

BigQuery is not touched from Python at all: the SQL in sql/30-33 has already run
through src/part2_funnel/run_query.sh, and its results sit in
outputs/tables/part2_q3*.csv with a provenance sidecar each. This entrypoint turns
those into the report tables §10.6.6 requires, emits every derived figure as its
own committed cell (§7.5), draws the figures from those tables, and verifies and
audits what it wrote.

The order matters, and A-165 fixes the first two steps: the derived-figure
machinery is exercised BEFORE any funnel prose exists, and the audit's negative
self-test runs on every render.

  1  population reconciliation   -> part2_01   (§10.7.2, the report's first table)
  2  data handling + re-scope     -> part2_02   (§10.6.6 item 6, §10.6.1)
  3  the funnel                   -> part2_03   (item 1)
  4  out-of-order users           -> part2_04   (item 2)
  5  the progression matrix       -> part2_05   (the audit trail)
  6  diagnostic events            -> part2_06   (item 3)
  7  level_end reconciliation     -> part2_07   (item 4, A-164)
  8  segment constancy            -> part2_08   (§10.7.5, A-154)
  9  funnel by segment            -> part2_09   (item 5)
 10  the parallel track           -> part2_10   (A-172)
 11  the derived-figure register  -> part2_report_figures.csv
 12  figures, from the tables above
 13  self-verification and the audit, which raise rather than warn
"""

import csv
import sys

from . import config as C
from . import figures, register, tables, verify


def _ledger_stats() -> dict:
    rows = list(csv.DictReader(open(C.TABLES / "part2_budget_ledger.csv", newline="")))
    billed = [int(r["bytes_billed"]) for r in rows]
    deltas = [abs(int(r["prediction_delta_bytes"])) for r in rows]
    prior = sum(int(r["bytes_billed"]) for r in
                csv.DictReader(open(C.TABLES / "part1_budget_ledger.csv", newline="")))
    return {"rows": len(rows), "total": sum(billed), "largest": max(billed),
            "max_delta": max(deltas), "pair": sum(billed) + prior, "prior": prior}


def main() -> int:
    written = []

    name, population = tables.population();                 written.append(name)
    name, handling = tables.data_handling(population);       written.append(name)
    name, funnel = tables.funnel();                          written.append(name)
    name, out_of_order = tables.out_of_order(funnel);        written.append(name)
    name, matrix = tables.progression_matrix();              written.append(name)
    name, _ = tables.diagnostic_events();                    written.append(name)
    name, level_end = tables.level_end_reconciliation();     written.append(name)
    name, constancy_outcome = tables.segment_constancy();    written.append(name)
    name, segments = tables.funnel_by_segment(constancy_outcome); written.append(name)
    name, track = tables.parallel_track();                   written.append(name)

    constancy = {r["dimension"]: float(r["share_non_constant_pct_value"])
                 for r in tables.read_rows("part2_08_segment_constancy.csv")}
    stats = {"population": population, "handling": handling, "funnel": funnel,
             "out_of_order": out_of_order, "matrix": matrix, "level_end": level_end,
             "constancy": constancy, "segments": segments, "parallel_track": track,
             "ledger": _ledger_stats()}

    written.append(register.build(stats).write())

    # A-165: report tables are generated from their CSVs, never typed. --fill-tables
    # injects them; every later run regenerates and asserts byte-equality instead.
    if "--fill-tables" in sys.argv and C.REPORT.exists():
        from . import markdown
        C.REPORT.write_text(markdown.fill_blocks(C.REPORT.read_text(), tables.VIEWS))
        print(f"\nfilled the generated table blocks in {C.REPORT.name}")
    written += figures.build_all()

    print("\nwrote:")
    for name in sorted(written):
        print(f"  outputs/{'figures' if name.endswith('.png') else 'tables'}/{name}")

    print("\nself-verification and audit (§7.5):")
    for note in verify.run_all():
        print(f"  ok — {note}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
