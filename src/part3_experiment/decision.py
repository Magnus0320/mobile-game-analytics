"""§7.7 step 18: the three-stage decision pipeline of §1.6.

The rules are of THREE DIFFERENT KINDS, evaluated in three separate stages and
not in one flat first-match sweep:

  Stage 1  preconditions (R0, R6) — tested before any outcome branch; either can
           set the recommendation on its own and stops the pipeline.
  Stage 2  outcome branches (R1-R5) — mutually exclusive and exhaustive over the
           remaining space, so EXACTLY ONE fires.
  Stage 3  modifiers (R7-R10) — applied to whichever branch fired. They can
           qualify a recommendation; they can never replace it or create one.

A single first-match ordering over all three kinds is what made the modifiers
unreachable in v1.0 of ARCHITECTURE.md: R1-R5 already partition the outcome
space, so control never arrived at R6, R7 or R8 (A-037).

Every stage evaluates all of its conditions independently and asserts the arity
of the result (A-061). An if/elif chain would make "exactly one fired" true by
construction, which would leave §7.7 step 20's assertion verifying nothing.

This module reads no power figure. R4 and R5 are selected solely by where CI7
sits relative to +/-1.00 pp, exactly as §1.6 defines them (A-062).
"""

from __future__ import annotations

from dataclasses import dataclass, field

from . import config
from .run_state import RunState, SelfVerificationFailure

KEEP = "Keep the gate at level 30."
MOVE = "Move the gate to level 40."
MOVE_CONDITIONAL = (
    "Move the gate to level 40 only after the D1 regression is explained."
)

STAGE2_RATIONALE = {
    "R1": "An actionable benefit is both detected and bounded away from the threshold.",
    "R2": ("A real effect was detected but the interval does not establish it clears "
           "the action bar. The follow-up is a revenue-powered test, not a re-run of "
           "this one."),
    "R3": ("Report the estimated retention cost of the move with its interval; the "
           "backlog item is closed on retention grounds."),
    "R4": ("The experiment rules out any D7 effect large enough to act on. This is "
           "practical equivalence at the action threshold, not a failed test."),
    "R5": ("The experiment neither detected nor ruled out an actionable effect. This "
           "must NOT be written as 'there is no difference between the arms'."),
}

STAGE3_EFFECT = {
    "R7": ("Unchanged. Explicit no-op: a positive D1 result never upgrades R2-R5 "
           "into a move."),
    "R8": ("Downgraded to conditional: move the gate only after the D1 regression is "
           "explained. A D7 gain bought with a D1 loss may be a composition effect "
           "rather than a genuine improvement."),
    "R9": ("Unchanged — the recommendation is already the conservative one. Report "
           "the regression and name it in §6.4 as a follow-up hypothesis."),
    "R10": "Unchanged. The guardrail was checked and was quiet.",
}


def contains_zero(low: float, high: float) -> bool:
    """Closed containment (A-060), so R10 and {R7, R8, R9} partition cleanly."""
    return low <= 0.0 <= high


@dataclass
class Decision:
    precondition: str | None = None
    precondition_detail: str = ""
    stage2_branch: str = ""
    stage2_conditions: dict[str, bool] = field(default_factory=dict)
    stage2_drives_recommendation: bool = True
    stage3_modifier: str | None = None
    stage3_conditions: dict[str, bool] = field(default_factory=dict)
    recommendation: str | None = None
    recommendation_withheld: bool = False
    rule_path: str = ""


def evaluate_stage2(primary: dict, mde: float = config.MDE_PP,
                    alpha: float = config.ALPHA) -> tuple[str, dict[str, bool]]:
    """Boundary conventions are §1.6's, encoded literally: a CI7 lower bound of
    exactly +1.00 pp counts as NOT clearing the threshold (R2), and an interval
    endpoint of exactly +/-1.00 pp counts as WITHIN the threshold (R4)."""
    p = primary["p_value"]
    delta = primary["delta_pp"]
    lo = primary["bootstrap_ci_low_pp"]
    hi = primary["bootstrap_ci_high_pp"]
    significant = p < alpha

    conditions = {
        "R1": bool(significant and lo > mde),
        "R2": bool(significant and delta > 0 and lo <= mde),
        "R3": bool(significant and delta < 0),
        "R4": bool((not significant) and (-mde <= lo) and (hi <= mde)),
        "R5": bool((not significant) and (lo < -mde or hi > mde)),
    }
    fired = [rule for rule, hit in conditions.items() if hit]
    if len(fired) != 1:
        raise SelfVerificationFailure(
            "§1.6 Stage 2 must have exactly one branch fire; "
            f"{len(fired)} fired: {fired}. Conditions: {conditions}. "
            f"Inputs: p={p!r}, delta_pp={delta!r}, ci=({lo!r}, {hi!r}), mde={mde!r}. "
            "No branch is invented to cover a state the pre-registration does not "
            "describe (A-061): if this is the delta==0 case, the pre-registration "
            "has a genuine gap and needs an amendment, not a patch."
        )
    return fired[0], conditions


def evaluate_stage3(guardrail: dict, stage2_branch: str) -> tuple[str, dict[str, bool]]:
    delta1 = guardrail["delta_pp"]
    lo = guardrail["bootstrap_ci_low_pp"]
    hi = guardrail["bootstrap_ci_high_pp"]
    quiet = contains_zero(lo, hi)
    excludes_zero = not quiet

    conditions = {
        "R7": bool(delta1 > 0 and excludes_zero),
        "R8": bool(delta1 < 0 and excludes_zero and stage2_branch == "R1"),
        "R9": bool(delta1 < 0 and excludes_zero
                   and stage2_branch in {"R2", "R3", "R4", "R5"}),
        "R10": bool(quiet),
    }
    applied = [rule for rule, hit in conditions.items() if hit]
    if len(applied) != 1:
        raise SelfVerificationFailure(
            "§1.6 Stage 3 must have exactly one modifier apply; "
            f"{len(applied)} applied: {applied}. Conditions: {conditions}. "
            f"Inputs: delta1_pp={delta1!r}, ci=({lo!r}, {hi!r}), "
            f"stage2_branch={stage2_branch!r}. No modifier is invented to cover a "
            "state the pre-registration does not describe (A-061)."
        )
    return applied[0], conditions


def evaluate(primary: dict, guardrail: dict, conflict: dict,
             state: RunState) -> Decision:
    """Runs after every downgrade flag can have been set, so R0 is known before
    any branch is evaluated (§7.7's third load-bearing ordering constraint)."""
    decision = Decision()

    # --- Stage 2 is always computed, even when a precondition fires, because
    # §1.6 requires it reported for transparency.
    decision.stage2_branch, decision.stage2_conditions = evaluate_stage2(primary)

    # --- Stage 1 — preconditions, R0 then R6, in that order.
    if state.is_downgraded:
        decision.precondition = "R0"
        decision.precondition_detail = "; ".join(d.detail for d in state.downgrades)
        decision.recommendation = None
        decision.recommendation_withheld = True
        decision.stage2_drives_recommendation = False
    elif conflict["conflict"]:
        decision.precondition = "R6"
        decision.precondition_detail = (
            f"z-test and bootstrap conflict ({conflict['case']}); resolved to the "
            "conservative branch per §4.3."
        )
        decision.recommendation = KEEP
        decision.stage2_drives_recommendation = False

    if decision.precondition is not None:
        # Stage 3 is not applied when Stage 1 fired (§1.6).
        decision.rule_path = (
            f"Stage 1: {decision.precondition} fired | "
            f"Stage 2: {decision.stage2_branch} (computed, does not drive) | "
            "Stage 3: not applied"
        )
    else:
        # --- Stage 2 drives the recommendation.
        branch = decision.stage2_branch
        decision.recommendation = MOVE if branch == "R1" else KEEP

        # --- Stage 3 — modifiers qualify; they never replace or create.
        decision.stage3_modifier, decision.stage3_conditions = evaluate_stage3(
            guardrail, branch
        )
        if decision.stage3_modifier == "R8":
            decision.recommendation = MOVE_CONDITIONAL
        decision.rule_path = (
            f"Stage 1: clean | Stage 2: {branch} | "
            f"Stage 3: {decision.stage3_modifier}"
        )

    state.finding(
        step=18,
        finding_id="decision.pipeline",
        description=(
            "Recommendation derived mechanically from §1.6's three stages. The "
            "write-up quotes the full path — precondition state, branch, modifier — "
            "by rule name. No other consideration may alter it."
        ),
        values={
            "precondition": decision.precondition or "clean",
            "stage2_branch": decision.stage2_branch,
            "stage2_drives_recommendation": decision.stage2_drives_recommendation,
            "stage3_modifier": decision.stage3_modifier or "not applied",
            "recommendation": decision.recommendation or "WITHHELD",
            "recommendation_withheld": decision.recommendation_withheld,
            "rule_path": decision.rule_path,
        },
    )
    return decision
