"""§7.7 step 20: self-verification, by re-reading the outputs that were written.

This is the one hard stop that necessarily occurs AFTER outputs exist, so the
"no outputs are written" half of §7.7's hard-stop definition cannot hold here.
§7.7 scopes that invariant to data-driven stops — "steps 1-6 and the assertion
group at step 9 are the only places the run can terminate on the data" — so this
is a stop on the code's own consistency. The consequence is carried by commit
discipline: outputs from a run whose step 20 failed are never committed (A-070).
"""

from __future__ import annotations

import csv
import json
from pathlib import Path

from . import config, decision as decision_module
from .run_state import RunState, SelfVerificationFailure


def _kv(path: Path) -> dict[str, str]:
    with path.open(encoding="utf-8", newline="") as fh:
        return {r["quantity"]: r["value"] for r in csv.DictReader(fh)}


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise SelfVerificationFailure(
            f"§7.7 step 20 self-verification FAILED: {message}\n"
            "The files in outputs/ are the product of a failed run and must not "
            "be committed (A-070)."
        )


def self_verify(*, state: RunState, decision, primary: dict, guardrail: dict,
                conflict: dict, populations: dict, srm: dict,
                outputs: list[Path]) -> dict:
    checks: list[str] = []

    # --- every written output exists and is non-empty ----------------------
    for path in outputs:
        _require(path.exists() and path.stat().st_size > 0,
                 f"output {path} is missing or empty")
    checks.append(f"{len(outputs)} output files present and non-empty")

    # --- the step 9 assertions held ----------------------------------------
    ids = {f.finding_id for f in state.findings}
    _require("coercion.assertions_passed" in ids,
             "the step 9 post-coercion assertion group did not record a pass")
    _require("structural.gate_passed" in ids,
             "the step 5 structural gate did not record a pass")
    checks.append("step 5 gate and step 9 assertion group both recorded a pass")

    # --- every reported denominator equals the row count recorded for it ---
    rates_path = config.TABLES_DIR / "part3_05_retention_rates.csv"
    with rates_path.open(encoding="utf-8", newline="") as fh:
        for row in csv.DictReader(fh):
            key = f"{row['metric']}.{row['arm']}"
            recorded = state.denominators.get(key)
            _require(recorded is not None, f"no recorded denominator for {key}")
            _require(int(row["denominator"]) == recorded,
                     f"reported denominator for {key} is {row['denominator']} but "
                     f"{recorded} rows were recorded")
            in_memory = populations[row["metric"]].denominators[row["arm"]]
            _require(in_memory == recorded,
                     f"in-memory population size for {key} is {in_memory}, "
                     f"recorded {recorded}")
            successes = populations[row["metric"]].successes[row["arm"]]
            _require(int(row["successes"]) == successes,
                     f"reported successes for {key} disagree with the population")
    checks.append("every reported denominator equals its recorded row count")

    # --- the SRM denominator is the assignment population, not a cleaned one
    srm_table = _kv(config.TABLES_DIR / "part3_02_srm.csv")
    _require(int(srm_table["srm_n"]) == srm["n"], "SRM n was not written faithfully")
    _require(
        srm["n"] == srm["control_count"] + srm["variant_count"],
        "SRM n does not equal the sum of the two arm counts",
    )
    for metric in config.RETENTION_COLUMNS:
        for arm in config.ARMS:
            _require(
                populations[metric].denominators[arm]
                <= state.denominators[f"assigned.{arm}"],
                f"the {metric}/{arm} analysis population is larger than the arm's "
                "assignment count, so an exclusion moved the SRM denominator",
            )
    checks.append("SRM denominator is the assignment population, fixed before exclusions")

    # --- EXACTLY ONE Stage 2 branch fired ----------------------------------
    decision_table = _kv(config.TABLES_DIR / "part3_10_decision.csv")
    fired = [r for r in ("R1", "R2", "R3", "R4", "R5")
             if decision_table.get(f"stage2_condition.{r}") == "true"]
    _require(len(fired) == 1,
             f"exactly one Stage 2 branch must have fired; the written table shows "
             f"{len(fired)}: {fired}")
    _require(fired[0] == decision_table["stage2_branch"],
             f"the written Stage 2 branch {decision_table['stage2_branch']!r} is not "
             f"the branch whose condition is true ({fired[0]!r})")
    checks.append(f"exactly one Stage 2 branch fired: {fired[0]}")

    # --- Stage 3 is applied exactly when Stage 1 was clean ------------------
    clean = decision_table["precondition"] == "clean"
    applied = decision_table["stage3_modifier"]
    if clean:
        _require(applied in ("R7", "R8", "R9", "R10"),
                 f"Stage 1 was clean but no Stage 3 modifier was applied ({applied!r})")
        modifiers = [r for r in ("R7", "R8", "R9", "R10")
                     if decision_table.get(f"stage3_condition.{r}") == "true"]
        _require(len(modifiers) == 1,
                 f"exactly one Stage 3 modifier must apply; got {modifiers}")
    else:
        _require(applied == "not applied",
                 "a Stage 1 precondition fired, so Stage 3 must not be applied")
        _require(decision_table["stage2_drives_recommendation"] == "false",
                 "a Stage 1 precondition fired, so Stage 2 must not drive the "
                 "recommendation")
    checks.append("Stage 3 applied exactly when Stage 1 was clean")

    # --- the recorded recommendation equals what the pipeline produces ------
    replay_branch, replay_conditions = decision_module.evaluate_stage2(primary)
    _require(replay_branch == decision.stage2_branch,
             "re-evaluating Stage 2 from the recorded inputs gives "
             f"{replay_branch!r}, not the recorded {decision.stage2_branch!r}")

    replayed = decision_module.evaluate(primary, guardrail, conflict,
                                        _replay_state(state))
    recorded = decision_table["recommendation"]
    expected = replayed.recommendation or "WITHHELD"
    _require(recorded == expected,
             f"the recorded recommendation {recorded!r} is not the one the pipeline "
             f"produces from the same inputs ({expected!r})")
    _require(replayed.rule_path == decision_table["rule_path"],
             f"the recorded rule path {decision_table['rule_path']!r} is not the one "
             f"the pipeline produces ({replayed.rule_path!r})")
    checks.append("recorded recommendation equals the pipeline's own output")

    # --- R0 withholds the recommendation and nothing else ------------------
    if state.is_downgraded:
        _require(decision_table["recommendation"] == "WITHHELD",
                 "an integrity downgrade was set but a recommendation was issued")
        _require(decision_table["precondition"] == "R0",
                 "an integrity downgrade was set but precondition R0 did not fire")
        for name in ("part3_02_srm.csv", "part3_03_power.csv",
                     "part3_06_primary_inference.csv",
                     "part3_07_guardrail_inference.csv"):
            path = config.TABLES_DIR / name
            _require(path.exists() and path.stat().st_size > 0,
                     f"R0 fired but {name} was suppressed; §2.4 requires the full "
                     "analysis to be computed and reported, with only the "
                     "recommendation withheld")
        checks.append("R0: recommendation withheld, full analysis still reported")

    # --- the manifest round-trips ------------------------------------------
    manifest = json.loads(config.MANIFEST_PATH.read_text(encoding="utf-8"))
    _require(manifest["decision"]["recommendation"] == recorded,
             "the manifest's recommendation disagrees with the decision table")
    _require(manifest["environment"]["random_seed"] == config.RANDOM_SEED,
             "the manifest records a different seed than config")
    _require(manifest["preregistration"]["architecture_commit"]
             == config.PREREGISTRATION_COMMIT,
             "the manifest does not cite the pre-registration commit")
    checks.append("manifest round-trips and cites the pre-registration commit")

    return {"checks": checks, "passed": True}


def _replay_state(state: RunState) -> RunState:
    """A state carrying only the downgrade flags, so the replay sees the same
    Stage 1 input without appending duplicate findings to the real run."""
    replay = RunState()
    for entry in state.downgrades:
        replay.downgrades.append(entry)
    return replay
