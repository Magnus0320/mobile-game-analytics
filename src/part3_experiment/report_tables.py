"""§7.7 step 19 (tables). Every number in prose must exist in one of these files.

Each numeric row carries BOTH a full-precision `value` and a `value_display`
rendered at §4.1's reporting precision (A-069). The decision rule is evaluated on
`value`, because a rounded CI endpoint could cross the 1.00 pp threshold in
either direction; the report and README quote `value_display`, so every printed
figure is literally findable in a committed file.

Tables are written byte-deterministically: fixed column order, an explicit float
format, "\\n" terminators, no index, and no locale, path or timestamp leakage.
"""

from __future__ import annotations

import csv
from pathlib import Path
from typing import Any, Iterable, Sequence

from . import config

KV_COLUMNS = ("quantity", "value", "value_display", "unit", "note")


def _fmt_full(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, float):
        return config.FULL_PRECISION_FMT.format(value)
    return str(value)


def display(value: Any, unit: str) -> str:
    """§4.1 reporting precision: two decimals in pp, p-values to three sig figs,
    no asterisk or star notation anywhere, and never a p rounded to zero."""
    if value is None or value == "":
        return ""
    if unit == "text":
        return str(value)
    if isinstance(value, bool):
        return "yes" if value else "no"
    if unit == "count":
        return f"{int(value):,}"
    if unit == "pp":
        return f"{float(value):.{config.PP_DECIMALS}f}"
    if unit == "p":
        p = float(value)
        if p == 0.0:
            return "<1e-300"
        return f"{p:.{config.PVALUE_SIGFIGS}g}"
    if unit == "power":
        return f"{float(value):.4f}"
    if unit == "proportion":
        return f"{float(value):.6f}"
    if unit == "share":
        return f"{float(value) * 100:.4f}%"
    if unit == "se":
        # Six decimals, because the pooled and unpooled standard errors coincide
        # to four here by arithmetic accident and the report argues they are
        # distinct quantities. A display that hides the difference would make
        # that argument uncheckable against the file.
        return f"{float(value):.6f}"
    if unit == "statistic":
        return f"{float(value):.4f}"
    return _fmt_full(value)


def write_csv(path: Path, columns: Sequence[str],
              rows: Iterable[dict[str, Any]]) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.writer(fh, lineterminator="\n", quoting=csv.QUOTE_MINIMAL)
        writer.writerow(columns)
        for row in rows:
            writer.writerow([_fmt_full(row.get(c)) for c in columns])
    return path


def kv(quantity: str, value: Any, unit: str, note: str = "") -> dict[str, Any]:
    return {"quantity": quantity, "value": value,
            "value_display": display(value, unit), "unit": unit, "note": note}


def _p(name: str) -> Path:
    return config.TABLES_DIR / name


def write_all(*, raw_rows: int, provenance: dict, unassignable: int,
              duplicates, missing: dict, populations: dict, srm: dict,
              power: dict, primary: dict, guardrail: dict, conflict: dict,
              engagement: dict, decision, state) -> list[Path]:
    written: list[Path] = []
    arms = config.ARMS

    # 01 — data quality and denominators ------------------------------------
    rows = [
        kv("raw_rows", raw_rows, "count", "Rows in the raw input (§7.7 step 4)."),
        kv("documented_rows", config.DOCUMENTED_ROW_COUNT, "count",
           "Documented size of the dataset; a mismatch is a finding, not an adjustment."),
        kv("recorded_sha256", provenance["sha256"], "text",
           f"Verified at step 2 against assumptions.md {config.PROVENANCE_ENTRY_ID}."),
        kv("unassignable_rows", unassignable, "count",
           "version missing; never assigned, so in neither SRM arm (§2.2, A-051)."),
        kv("unassignable_share", unassignable / raw_rows, "share",
           f"Downgrade threshold {config.UNASSIGNABLE_THRESHOLD:.1%} of raw rows."),
        kv("duplicate_userids", duplicates.n_duplicate_ids, "count",
           "Uniqueness asserted, not assumed (§5.2)."),
        kv("duplicates_same_arm_identical", len(duplicates.same_arm_identical_ids),
           "count", "Export artefact: one row kept."),
        kv("duplicates_same_arm_conflicting",
           len(duplicates.same_arm_conflicting_ids), "count",
           "Unresolvable from this data: userid excluded from the metric analysis."),
        kv("duplicates_cross_arm", len(duplicates.cross_arm_ids), "count",
           "Cross-contaminated: excluded from both arms; ITT compromised for them."),
        kv("duplicates_cross_arm_share",
           len(duplicates.cross_arm_ids) / raw_rows, "share",
           f"Downgrade threshold {config.CROSS_ARM_DUPLICATE_THRESHOLD:.1%} of raw rows."),
        kv("rows_dropped_as_export_artefact",
           duplicates.rows_dropped_as_export_artefact, "count", ""),
    ]
    for metric in config.RETENTION_COLUMNS:
        for arm in arms:
            cell = missing["per_metric"][metric][arm]
            tag = "primary" if metric == config.PRIMARY_METRIC else "guardrail"
            rows.append(kv(f"missing.{metric}.{arm}", cell["missing"], "count",
                           f"{tag}; excluded from this metric only (§5.3)."))
            rows.append(kv(f"missing_share.{metric}.{arm}", cell["share_of_arm"],
                           "share",
                           "Share of that arm's assignment count (A-065)."
                           + (f" Downgrade threshold "
                              f"{config.PRIMARY_MISSING_THRESHOLD:.1%}."
                              if metric == config.PRIMARY_METRIC else "")))
        c, v = (missing["per_metric"][metric][a]["share_of_arm"] for a in arms)
        rows.append(kv(f"differential_missingness.{metric}", (v - c) * 100.0, "pp",
                       "Variant minus control; reported regardless of threshold (§5.3)."))
    for arm in arms:
        rows.append(kv(f"assigned.{arm}", srm[f"{'control' if arm == arms[0] else 'variant'}_count"],
                       "count", "SRM denominator component, fixed before any exclusion."))
    for metric in config.RETENTION_COLUMNS:
        for arm in arms:
            rows.append(kv(f"denominator.{metric}.{arm}",
                           populations[metric].denominators[arm], "count",
                           "Denominator actually used for this metric and arm."))
    written.append(write_csv(_p("part3_01_data_quality.csv"), KV_COLUMNS, rows))

    # 02 — SRM ---------------------------------------------------------------
    rows = [
        kv("srm_n", srm["n"], "count", "Assignment population (§2.2 literal rule)."),
        kv("control_count", srm["control_count"], "count", config.ARM_CONTROL),
        kv("variant_count", srm["variant_count"], "count", config.ARM_VARIANT),
        kv("expected_per_arm", srm["expected_per_arm"], "statistic",
           "Under the hypothesised 1:1 allocation (A-008)."),
        kv("observed_control_share", srm["observed_control_share"], "proportion", ""),
        kv("imbalance_rows", srm["imbalance_rows"], "count",
           "Difference BETWEEN ARMS: control minus variant."),
        kv("arm_gap_rows", abs(srm["imbalance_rows"]), "count",
           "Size of the gap between the two arm counts."),
        kv("excess_over_expectation_rows",
           abs(srm["variant_count"] - srm["expected_per_arm"]), "statistic",
           "Departure of EACH arm from the expected 1:1 count; half the arm gap."),
        kv("exact_binomial_p", srm["exact_binomial_p"], "p",
           "PRIMARY SRM test: two-sided exact binomial against p=0.5 (A-010)."),
        kv("chi2_statistic", srm["chi2_statistic"], "statistic",
           "Goodness-of-fit, 1 df, reported alongside as a cross-check."),
        kv("chi2_p", srm["chi2_p"], "p", ""),
        kv("failure_threshold", srm["failure_threshold"], "p", "§2.3, A-011."),
        kv("tripped", srm["tripped"], "text",
           "Reported unconditionally, whether or not it trips (§2.2)."),
    ]
    for row in state.findings:
        if row.finding_id == "populations.differential_exclusion":
            for rec in row.values["rows"]:
                rows.append(kv(
                    f"post_exclusion.{rec['metric']}.{rec['arm']}", rec["analysed"],
                    "count",
                    "Descriptive differential-exclusion check: no test, no threshold."))
    written.append(write_csv(_p("part3_02_srm.csv"), KV_COLUMNS, rows))

    # 03 — power -------------------------------------------------------------
    rows = [
        kv("baseline_control_rate_pp", power["baseline_control_rate"] * 100.0, "pp",
           "OBSERVED control-arm D7 rate, not an assumed figure (§3)."),
        kv("n_control", power["n_control"], "count", "Observed, not the nominal 1:1."),
        kv("n_variant", power["n_variant"], "count", "Observed, not the nominal 1:1."),
        kv("alpha", power["alpha"], "proportion", "Two-sided (§1.3)."),
        kv("power_at_1pp", power["power_at_mde"], "power",
           "Power to detect a 1.00 pp absolute difference at observed n and baseline."),
        kv("detectable_at_80_power_pp", power["detectable_at_80_pp"], "pp",
           "Smallest absolute difference detectable at 80% power."),
        kv("detectable_at_95_power_pp", power["detectable_at_95_pp"], "pp",
           "Smallest absolute difference detectable at 95% power."),
        kv("action_threshold_pp", config.MDE_PP, "pp", "§1.4, A-005."),
        kv("comparison_sentence", power["comparison_sentence"], "text",
           "Required by §3. Reported only; it feeds no decision branch (A-062)."),
    ]
    written.append(write_csv(_p("part3_03_power.csv"), KV_COLUMNS, rows))
    written.append(write_csv(
        _p("part3_04_power_curve.csv"), ("effect_pp", "power"), power["curve"]))

    # 05 — retention rates by arm -------------------------------------------
    rows = []
    for metric, block in (("retention_7", primary), ("retention_1", guardrail)):
        for arm, key in ((config.ARM_CONTROL, "control"), (config.ARM_VARIANT, "variant")):
            rate = block[f"rate_{key}_pp"]
            rows.append({
                "metric": metric, "arm": arm,
                "successes": block[f"successes_{key}"],
                "denominator": block[f"n_{key}"],
                "rate_pp": rate, "rate_pp_display": display(rate, "pp"),
                "role": "primary" if metric == config.PRIMARY_METRIC else "guardrail",
            })
    written.append(write_csv(
        _p("part3_05_retention_rates.csv"),
        ("metric", "arm", "successes", "denominator", "rate_pp", "rate_pp_display", "role"),
        rows))

    # 06 — primary inference -------------------------------------------------
    rows = [
        kv("delta_7_pp", primary["delta_pp"], "pp",
           "Variant minus control, ITT over all assigned players (§4.1, A-007)."),
        kv("z_statistic", primary["z_statistic"], "statistic",
           "Pooled-variance, two-sided, no continuity correction (§4.1)."),
        kv("p_value", primary["p_value"], "p",
           "The confirmatory instrument; alpha was pre-registered against it."),
        kv("alpha", config.ALPHA, "proportion", "§1.3, all of it on this one test."),
        kv("significant", primary["significant"], "text", ""),
        kv("se_pooled_pp", primary["se_pooled_pp"], "se",
           "Null variance: used for the TEST only (§4.1, A-015)."),
        kv("se_unpooled_pp", primary["se_unpooled_pp"], "se",
           "Used for the INTERVAL only. The asymmetry is deliberate, not a bug."),
        kv("analytic_ci_low_pp", primary["analytic_ci_low_pp"], "pp", "Unpooled Wald."),
        kv("analytic_ci_high_pp", primary["analytic_ci_high_pp"], "pp", "Unpooled Wald."),
        kv("bootstrap_ci_low_pp", primary["bootstrap_ci_low_pp"], "pp",
           "CI7: the estimation instrument; decides the action-threshold condition."),
        kv("bootstrap_ci_high_pp", primary["bootstrap_ci_high_pp"], "pp", ""),
        kv("bootstrap_mc_se_pp", primary["bootstrap_mc_se_pp"], "statistic",
           "Monte Carlo standard error as §4.2 defines it: the bootstrap SE of the estimate."),
        kv("bootstrap_endpoint_mc_se_low_pp",
           primary["bootstrap_endpoint_mc_se_low_pp"], "statistic",
           "Supplementary: MC error of the lower percentile endpoint."),
        kv("bootstrap_endpoint_mc_se_high_pp",
           primary["bootstrap_endpoint_mc_se_high_pp"], "statistic",
           "Supplementary: MC error of the upper percentile endpoint."),
        kv("n_resamples", primary["n_resamples"], "count", "§4.2, A-017."),
        kv("random_seed", config.RANDOM_SEED, "text", "§7.5, A-018."),
        kv("conflict", conflict["conflict"], "text",
           "z-test vs bootstrap (§4.3). Routes to precondition R6 if true."),
        kv("conflict_case", conflict["case"] or "none", "text", ""),
    ]
    written.append(write_csv(_p("part3_06_primary_inference.csv"), KV_COLUMNS, rows))

    # 07 — guardrail ---------------------------------------------------------
    rows = [
        kv("delta_1_pp", guardrail["delta_pp"], "pp", "Variant minus control."),
        kv("analytic_ci_low_pp", guardrail["analytic_ci_low_pp"], "pp", ""),
        kv("analytic_ci_high_pp", guardrail["analytic_ci_high_pp"], "pp", ""),
        kv("bootstrap_ci_low_pp", guardrail["bootstrap_ci_low_pp"], "pp", "CI1."),
        kv("bootstrap_ci_high_pp", guardrail["bootstrap_ci_high_pp"], "pp", "CI1."),
        kv("bootstrap_mc_se_pp", guardrail["bootstrap_mc_se_pp"], "statistic", ""),
        kv("interval_excludes_zero", guardrail["interval_excludes_zero"], "text",
           "A description of an interval, NOT a test decision (§1.2)."),
        kv("test_performed", guardrail["test_performed"], "text",
           "No alpha allocated and no p-value computed for the guardrail (§1.2, A-003)."),
    ]
    written.append(write_csv(_p("part3_07_guardrail_inference.csv"), KV_COLUMNS, rows))

    # 08 / 09 — engagement ---------------------------------------------------
    engagement_rows = [
        {**r,
         "n_display": display(r["n"], "count"),
         "mean_display": display(r["mean"], "pp"),
         "median_display": display(r["median"], "pp"),
         "max_display": display(r["max"], "count"),
         "winsorised_mean_display": display(r["winsorised_mean"], "pp")}
        for r in engagement["rows"]
    ]
    written.append(write_csv(
        _p("part3_08_engagement.csv"),
        ("arm", "variant", "n", "n_display", "mean", "mean_display",
         "median", "median_display", "std", "min", "max", "max_display",
         "winsorised_mean", "winsorised_mean_display"),
        engagement_rows))
    written.append(write_csv(
        _p("part3_10_engagement_distribution.csv"),
        ("arm", "bin_low", "bin_high", "count"), engagement["bins"]))

    rows = [
        kv("extreme_value_rounds", engagement["extreme_value"], "count",
           "§5.1: disclosed, kept in the primary analysis, never silently deleted."),
        kv("extreme_arm", engagement["extreme_arm"], "text", ""),
        kv("extreme_tied_rows", engagement["extreme_tied_rows"], "count",
           "Rows sharing the maximum value (A-067)."),
        kv("winsor_percentile", engagement["winsor_percentile"], "statistic",
           "Pooled cap applied identically to both arms (A-068)."),
        kv("winsor_cap_rounds", engagement["winsor_cap"], "count", ""),
        kv("missing_sum_gamerounds", engagement["missing_sum_gamerounds"], "count",
           "Affects engagement descriptives only (§5.3)."),
        kv("n_analysed", engagement["n_analysed"], "count", ""),
    ]
    written.append(write_csv(_p("part3_09_engagement_disclosure.csv"),
                             KV_COLUMNS, rows))

    # 10 — decision ----------------------------------------------------------
    rows = [
        kv("precondition", decision.precondition or "clean", "text",
           "Stage 1: R0 then R6."),
        kv("precondition_detail", decision.precondition_detail, "text", ""),
        kv("stage2_branch", decision.stage2_branch, "text",
           "Exactly one of R1-R5 fires; step 20 asserts it."),
        kv("stage2_drives_recommendation", decision.stage2_drives_recommendation,
           "text", "False when a Stage 1 precondition fired."),
        kv("stage3_modifier", decision.stage3_modifier or "not applied", "text",
           "Stage 3 is not applied when Stage 1 fired."),
        kv("recommendation", decision.recommendation or "WITHHELD", "text", ""),
        kv("recommendation_withheld", decision.recommendation_withheld, "text",
           "True only under R0 (§2.4)."),
        kv("rule_path", decision.rule_path, "text",
           "The full path the write-up must quote."),
    ]
    for rule, hit in decision.stage2_conditions.items():
        rows.append(kv(f"stage2_condition.{rule}", hit, "text",
                       STAGE_NOTE.get(rule, "")))
    for rule, hit in (decision.stage3_conditions or {}).items():
        rows.append(kv(f"stage3_condition.{rule}", hit, "text",
                       STAGE_NOTE.get(rule, "")))
    written.append(write_csv(_p("part3_11_decision.csv"), KV_COLUMNS, rows))

    # 11 — findings ----------------------------------------------------------
    rows = [
        {"step": f.step, "finding_id": f.finding_id, "description": f.description,
         "values": _compact(f.values)}
        for f in state.findings
    ]
    written.append(write_csv(
        _p("part3_12_findings.csv"),
        ("step", "finding_id", "description", "values"), rows))

    return written


STAGE_NOTE = {
    "R1": "p<0.05 and CI7 lower bound > +1.00 pp",
    "R2": "p<0.05, delta>0, CI7 lower bound <= +1.00 pp",
    "R3": "p<0.05 and delta<0",
    "R4": "p>=0.05 and all of CI7 within +/-1.00 pp",
    "R5": "p>=0.05 and CI7 extends beyond +/-1.00 pp",
    "R7": "delta1>0 with CI1 excluding zero (favourable guardrail)",
    "R8": "delta1<0, CI1 excludes zero, Stage 2 branch is R1",
    "R9": "delta1<0, CI1 excludes zero, Stage 2 branch is R2-R5",
    "R10": "CI1 contains zero (quiet guardrail)",
}


def _compact(values: dict) -> str:
    import json
    return json.dumps(values, sort_keys=True, separators=(",", ":"), default=str)
