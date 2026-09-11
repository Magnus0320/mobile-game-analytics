"""Part 3 entrypoint. The twenty steps of ARCHITECTURE.md §7.7, in that order.

§7.5 places execution order in the entrypoint and §7.7 is the definition of what
that order is, so this file is the single place it lives — and it is meant to be
read top to bottom.

Three of the orderings are load-bearing rather than incidental:

  * the STRUCTURAL GATE at step 5 runs before any statistic exists, so no number
    is ever computed from a file that turns out not to be the file the document
    describes;
  * the SRM TEST at step 8 runs before the duplicate and missing-value handling
    at steps 10 and 11, which is what makes §2.2's denominator rule true in the
    code rather than only in prose;
  * the DECISION PIPELINE at step 18 runs after every downgrade flag can have
    been set, so R0 is known before any branch is evaluated.

Each step is labelled with what a failure does: hard stop, downgrade, or finding.
A downgrade never raises and never skips a later step — the run continues to
completion with the full analysis reported and only the recommendation withheld.
"""

from __future__ import annotations

import sys

import numpy as np

from . import (checks, config, decision as decision_module, engagement, figures,
               inference, load, manifest, power, report_tables, srm, verify)
from .run_state import RunState


def main() -> int:
    state = RunState()

    # 1. Resolve and record the environment.                     [hard stop]
    environment = manifest.resolve_environment(state)

    # 2. Verify the input: locate the raw CSV, check its SHA-256
    #    against the value recorded in assumptions.md.           [hard stop]
    provenance = load.verify_input(state)

    # 3. Load the raw CSV with every column as text, no dtype
    #    inference, NA filtering off (A-059).                    [hard stop]
    raw = load.read_raw_text()

    # 4. Record the raw row count and column set; assert the
    #    column set is exactly the five expected columns.        [hard stop]
    load.check_columns(raw, state)
    raw_rows = int(len(raw))

    # 5. THE SINGLE STRUCTURAL GATE. Validate every value in all
    #    four columns against its token sets. Past this point no
    #    token value can stop the run.                           [hard stop]
    token_counts = checks.structural_gate(raw, state)

    # 6. Coerce version and the retention flags to their
    #    three-state representations. Safe because step 5 passed.[hard stop]
    coerced = checks.coerce(raw)

    # 7. Partition off unassignable rows (version missing).
    #                                   [finding; downgrade past 0.1% of raw]
    unassignable = checks.partition_unassignable(coerced, state)

    # 8. SRM TEST on the assignment population, BEFORE any other
    #    exclusion.            [finding, unconditional; downgrade if p<0.001]
    srm_result = srm.srm_test(coerced, unassignable, state)

    # 9. Post-coercion assertion group.                          [hard stop]
    checks.assert_coercion(coerced, token_counts, state)

    # 10. Uniqueness of userid, duplicates classified by case.
    #                        [findings; downgrade past 0.1% cross-arm of raw]
    duplicates = checks.check_uniqueness(coerced, unassignable, state)

    # 11. Missing-value check on the retention flags. Reachable
    #     because step 6 coerced missing markers to an explicit
    #     state instead of raising on them.
    #                  [findings; downgrade past 0.5% of EITHER arm, primary]
    missing = checks.check_missing_values(coerced, unassignable, state)

    # 12. Build the per-metric analysis populations, record each
    #     denominator, and report post-exclusion arm counts as the
    #     DESCRIPTIVE differential-exclusion check.                [finding]
    populations = checks.build_populations(
        coerced, unassignable, duplicates, missing["arm_assigned_counts"], state
    )

    # 13. Power on the primary metric, at the observed control
    #     rate and observed arm sizes. Never at the observed
    #     effect size (§1.7, A-014).                              [finding]
    primary_population = populations[config.PRIMARY_METRIC]
    control_rate = (primary_population.successes[config.ARM_CONTROL]
                    / primary_population.denominators[config.ARM_CONTROL])
    power_result = power.compute_power(
        control_rate,
        primary_population.denominators[config.ARM_CONTROL],
        primary_population.denominators[config.ARM_VARIANT],
    )
    state.finding(
        step=13,
        finding_id="power.computed",
        description=(
            "Power reported descriptively for a fixed-n dataset: it answers what "
            "this experiment could have seen, and is not a sample-size calculation "
            "(§3, A-013)."
        ),
        values={k: v for k, v in power_result.items() if k != "curve"},
    )

    # The two bootstrap streams are derived from the ONE seed by spawning, never
    # by inventing a second literal (§7.5, A-018, A-063).
    stream_primary, stream_guardrail = np.random.default_rng(
        config.RANDOM_SEED
    ).spawn(2)

    # 14. Primary inference: pooled-variance z-test, unpooled
    #     analytic interval, seeded stratified bootstrap.         [finding]
    primary_result, _ = inference.primary_inference(
        primary_population, stream_primary, state
    )

    # 15. Conflict evaluation. Sets precondition R6 if it fires.  [finding]
    conflict = inference.evaluate_conflict(primary_result, state)

    # 16. Guardrail inference on retention_1: the same estimators,
    #     interval only, no test decision.                        [finding]
    guardrail_result, _ = inference.guardrail_inference(
        populations[config.GUARDRAIL_METRIC], stream_guardrail, state
    )

    # 17. Engagement descriptives on sum_gamerounds, with and
    #     without the extreme row, plus median and the stated
    #     winsorised summary.                                     [finding]
    engagement_result = engagement.engagement_descriptives(
        coerced, unassignable, duplicates, state
    )

    # 18. THE DECISION PIPELINE: Stage 1 preconditions, then the
    #     Stage 2 branch, then Stage 3 modifiers. Runs after every
    #     downgrade flag can have been set.                       [finding]
    decision = decision_module.evaluate(
        primary_result, guardrail_result, conflict, state
    )

    # 19. Write outputs: tables, then figures generated FROM those
    #     tables, then the run manifest.
    tables = report_tables.write_all(
        raw_rows=raw_rows, provenance=provenance,
        unassignable=int(unassignable.sum()), duplicates=duplicates,
        missing=missing, populations=populations, srm=srm_result,
        power=power_result, primary=primary_result, guardrail=guardrail_result,
        conflict=conflict, engagement=engagement_result, decision=decision,
        state=state,
    )
    figure_paths = figures.write_all()
    manifest_path = manifest.write_manifest(
        environment=environment, provenance=provenance, raw_rows=raw_rows,
        decision=decision, srm=srm_result, primary=primary_result,
        guardrail=guardrail_result, state=state,
        outputs=[*tables, *figure_paths],
    )

    # 20. Self-verification: re-read the written outputs.        [hard stop]
    verification = verify.self_verify(
        state=state, decision=decision, primary=primary_result,
        guardrail=guardrail_result, conflict=conflict, populations=populations,
        srm=srm_result, outputs=[*tables, *figure_paths, manifest_path],
    )

    _summarise(state, decision, verification, tables, figure_paths, manifest_path)
    return 0


def _summarise(state, decision, verification, tables, figures_written,
               manifest_path) -> None:
    print(f"\nPart 3 complete — {len(tables)} tables, {len(figures_written)} figures, "
          f"1 manifest written.")
    print(f"  integrity downgrade: "
          f"{'YES — ' + ', '.join(d.source for d in state.downgrades) if state.is_downgraded else 'no'}")
    print(f"  rule path: {decision.rule_path}")
    print(f"  recommendation: {decision.recommendation or 'WITHHELD (R0)'}")
    print(f"  step 20 self-verification: {len(verification['checks'])} checks passed")
    for check in verification["checks"]:
        print(f"    - {check}")


if __name__ == "__main__":
    sys.exit(main())
