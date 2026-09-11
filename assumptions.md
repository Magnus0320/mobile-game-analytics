# assumptions.md

Every judgement call in this project, with what was rejected and why. Seeded
2026-09-10 from `ARCHITECTURE.md` v1.0, before any data was loaded.

This file is the record that lets a reviewer tell a decision from an accident. If a
choice could reasonably have gone the other way, it belongs here.

---

## How to use this file

**Append-only.** Never edit, reword, renumber, or delete an existing entry — not even
your own, not even to fix a decision that turned out wrong. To change a decision,
append a new entry with `Kind: supersedes A-NNN` naming the entry it replaces. The
one permitted edit to an existing entry is changing its `Status` line to
`superseded by A-NNN`; nothing else in an existing entry may be touched. IDs are
permanent and never reused.

**Who writes here.** Every session — architecture and implementation alike. The
architecture session owns `ARCHITECTURE.md`; everyone owns this file, in append
mode.

**When to append.** The moment you make a call that a reviewer could question:
a threshold, an exclusion, a definition, a library choice, a tie-break, a
discrepancy you resolved. If you catch yourself thinking "this is obviously fine",
that is the entry most worth writing down.

### Entry format

Copy this shape exactly. Prose in full sentences; no bare fragments.

```
### A-NNN — <short title>
- **Kind:** decision | finding | challenge | supersedes A-NNN
- **Part:** 3 | 1 | 2 | project-wide
- **Date:** YYYY-MM-DD
- **Status:** active | superseded by A-NNN
- **Decision:** One sentence, imperative, with literal values. No ranges, no "TBD".
- **Alternatives rejected:** Each alternative that was genuinely considered, with
  the specific reason it lost. "Not applicable" is only acceptable when there was
  no alternative.
- **Reason:** Why this one wins, on product or statistical grounds. Not "it is
  standard practice".
- **Affects:** Which metrics, files, or conclusions depend on this. Be concrete.
- **Falsifiable by:** What observation or argument would force a revision. If
  nothing could, say so and explain why.
```

**Kinds:**

- `decision` — a call that was made and is now binding.
- `finding` — something learned from the data that a later decision depends on
  (a row count, a schema fact, a checksum). Findings have no alternatives; write
  "Not applicable — this is an observation" and record how it was observed.
- `challenge` — an implementation session's objection to something in
  `ARCHITECTURE.md`. Write it, stop, and relay it to the architecture session. Do
  not deviate on your own authority.
- `supersedes A-NNN` — replaces an earlier decision. Must state what changed and
  whether any already-published number is affected.

### Entries expected from later parts

Reserved so nobody is surprised: Parts 1 and 2 will add entries covering the
**operational definition of a session**, **day boundaries and timezone semantics for
D1/D7/D30**, and the **treatment of users with events but no install event in the
window**. Those cannot be written yet — see `ARCHITECTURE.md` §10.

---

## Part 3 — pre-registration decisions

### A-001 — `gate_30` is the incumbent, `gate_40` is the proposed change
- **Kind:** decision
- **Part:** 3
- **Date:** 2026-09-10
- **Status:** superseded by A-036
- **Decision:** Treat `gate_30` as the control arm (shipped baseline) and `gate_40` as the variant, and define every effect as variant minus control.
- **Alternatives rejected:** Treating `gate_40` as the incumbent — the experiment is described as moving the gate from level 30 to level 40, which puts 30 in the "before" position. Treating the arms symmetrically with no control — a decision rule needs a default to fall back to, and "change nothing" is that default.
- **Reason:** The decision under test is whether to make a change, so the arm representing "no change" must be the reference; otherwise the null result has no natural recommendation.
- **Affects:** The sign of every reported effect, the direction of decision rules R1–R3, and the framing of the whole write-up.
- **Falsifiable by:** Documentation or the dataset author stating that `gate_40` was the live configuration. This flips the sign convention but not the logic. Flagged as open question 1.

### A-002 — 7-day retention is the sole primary metric
- **Kind:** decision
- **Part:** 3
- **Date:** 2026-09-10
- **Status:** active
- **Decision:** `retention_7` is the single primary metric; the recommendation is driven by it alone.
- **Alternatives rejected:** `retention_1` as primary — on day 1 most of each arm has not yet reached level 30, so the two arms are the same product for most of the population and the metric is dominated by never-exposed players. A composite or averaged retention score — it has no product meaning, nobody would act on it, and it hides which horizon moved. `sum_gamerounds` — heavily skewed, its 14-day window does not align with either retention flag, and it is an engagement description rather than a decision variable. Two co-primary metrics — that is the structure that produced the disagreement across the public notebooks.
- **Reason:** A gate is a pacing device, and pacing acts on habit formation over days rather than on first impressions; D7 is the earliest available metric on the right side of that mechanism, the one with the most treatment actually delivered, and the one that feeds an LTV argument a product manager would act on.
- **Affects:** Alpha allocation, the power calculation, the bootstrap quantity, and every branch of the decision rule.
- **Falsifiable by:** Evidence that players typically reach level 30 within the first day, which would make D1 an exposed-population metric. Nothing in this dataset can show that — see `ARCHITECTURE.md` §6.1.

### A-003 — 1-day retention is a guardrail, not a second hypothesis
- **Kind:** decision
- **Part:** 3
- **Date:** 2026-09-10
- **Status:** active — `Alternatives rejected` field superseded by A-041
- **Decision:** Report `retention_1` with a point estimate and a 95% bootstrap interval, allocate it no alpha, make no confirmatory significance claim on it, and let it hold a recommendation but never create one.
- **Alternatives rejected:** Co-primary with a correction — see A-007. Dropping it entirely — a metric that can detect harm is worth reporting even when it cannot justify action. A gated hierarchical test (test D1 only if D7 is significant) — defensible, but it removes the guardrail in the one case where a guardrail matters most, a null primary hiding a D1 regression.
- **Reason:** Guardrails exist to catch harm, so their power should be asymmetric: adverse movement triggers investigation, favourable movement triggers nothing.
- **Affects:** Decision rules R7 and R8; the wording permitted in the write-up ("the interval excludes zero", never "was significant").
- **Falsifiable by:** A stakeholder deciding D1 is itself a shipping criterion, which would require a new pre-registration with alpha split accordingly.

### A-004 — Alpha is 0.05, two-sided
- **Kind:** decision
- **Part:** 3
- **Date:** 2026-09-10
- **Status:** active
- **Decision:** Test the primary metric at alpha = 0.05, two-sided, with the whole of alpha spent on that one test.
- **Alternatives rejected:** One-sided at 0.05 — the direction is not known in advance and both directions are product-plausible and actionable; a one-sided test here would be a decision to only be able to discover good news. Alpha = 0.01 — buys specificity the decision does not need while costing sensitivity on the only test that matters. Alpha = 0.10 — loosens the bar on a change with real downstream cost.
- **Reason:** A later gate could plausibly help (less early friction) or hurt (faster content burn, weaker pacing), and a studio would act on either finding, so the test must be able to see both tails.
- **Affects:** The p-value threshold in rules R1–R5 and the power calculation.
- **Falsifiable by:** Nothing after the fact. Switching to one-sided at any point invalidates the pre-registration (`ARCHITECTURE.md` §1.7).

### A-005 — Minimum detectable effect and action threshold: 1.00 percentage point absolute
- **Kind:** decision
- **Part:** 3
- **Date:** 2026-09-10
- **Status:** active — confirmed and owned 2026-09-10; open question 3 closed, no longer provisional
- **Decision:** Fix the smallest effect worth acting on at 1.00 pp absolute on D7 retention, and use that same number both as the effect size the power calculation is evaluated at and as the action threshold in the decision rule.
- **Alternatives rejected:** A relative threshold (for example 5%) — it moves with the observed baseline, so the bar would be set by the data rather than by the business. 0.50 pp — smaller than the week-to-week noise a live title sees from acquisition mix and seasonality, so an effect that size could not be verified or managed after launch. 2.00 pp — larger than a pacing change plausibly delivers, so the bar would be unmeetable by construction. Fixing the threshold after seeing the effect — the failure this document exists to prevent.
- **Reason:** Moving a gate is cheap to implement but not cheap to own (it re-tunes the progression and monetization curve behind it), an effect below about a point is invisible against live-ops noise, and a full point against a typical casual-title D7 base is a mid-single-digit relative change in the cohort that generates essentially all revenue.
- **Affects:** The power table, rules R1, R2, R4 and R5, and the practical-equivalence conclusion available under R4.
- **Falsifiable by:** A real studio supplying its own decision threshold. Flagged as open question 3.

### A-006 — No multiple-comparison correction
- **Kind:** decision
- **Part:** 3
- **Date:** 2026-09-10
- **Status:** active
- **Decision:** Apply no formal multiplicity correction; the primary/secondary split carries the burden, because exactly one test is decision-eligible.
- **Alternatives rejected:** Bonferroni at 0.025 per metric — it buys inferential rights to a metric already declared unable to drive the decision, and pays by halving sensitivity on the test that matters; worse, correcting across two metrics implies both are decision-eligible, quietly restoring the two-hypotheses-one-headline structure. Benjamini–Hochberg — designed for many exploratory hypotheses, not two, one of which is not a hypothesis. Correcting after seeing the p-values — invalidates the pre-registration.
- **Reason:** A family-wise error rate is a property of a family of decisions; with one decision-eligible test the FWER is 0.05 by construction rather than by adjustment.
- **Affects:** The threshold in R1–R5, and the accepted residual risk that the uncorrected guardrail interval will occasionally exclude zero under a true null.
- **Falsifiable by:** Adding a third decision-eligible metric, which would require a fresh pre-registration with an explicit alpha allocation.

### A-007 — The estimand is the intention-to-treat effect on assigned players
- **Kind:** decision
- **Part:** 3
- **Date:** 2026-09-10
- **Status:** active
- **Decision:** Define the target quantity as the difference in D7 retention among all players assigned to each arm, regardless of exposure, and name it as such in the report.
- **Alternatives rejected:** The effect on players who actually reached a gate (complier-average / treated-population effect) — not identifiable, because no field records whether any player reached level 30 or 40. Restricting to players above some `sum_gamerounds` value as a proxy for exposure — that conditions on a post-treatment outcome, which breaks randomisation and would manufacture a biased comparison out of a clean one.
- **Reason:** ITT is the only estimand this data identifies, and stating it plainly prevents the write-up from silently overclaiming an effect on exposed players.
- **Affects:** The interpretation of every result, the dilution argument in the negative-results section, and the prohibition on outcome-based row filtering.
- **Falsifiable by:** An exposure field appearing in a future version of the dataset.

### A-008 — Expected allocation is 1:1
- **Kind:** decision
- **Part:** 3
- **Date:** 2026-09-10
- **Status:** active — confirmed 2026-09-10 as a permanent unknown; open question 2 closed (see A-046)
- **Decision:** Run the SRM test against a hypothesised allocation of exactly 0.5 / 0.5 between `gate_30` and `gate_40`.
- **Alternatives rejected:** Inferring the intended ratio from the observed counts — circular; it would make the SRM test unable to fail by construction. Skipping the SRM check because the design ratio is undocumented — the check is the single most valuable integrity signal available in this dataset.
- **Reason:** The dataset is documented as a two-arm split with no stated weighting, and 1:1 maximises power for a fixed total sample, which is what a competent team would have chosen.
- **Affects:** The SRM null, and therefore whether rule R0 can fire at all.
- **Falsifiable by:** Documentation of a weighted design, which would make the SRM p-value as specified meaningless and require re-running against the true ratio. Flagged as open question 2.

### A-009 — The decision rule is fixed before the result, including conflict resolution
- **Kind:** decision
- **Part:** 3
- **Date:** 2026-09-10
- **Status:** superseded by A-037
- **Decision:** Derive the recommendation mechanically from the rule table in `ARCHITECTURE.md` §1.6, evaluate rules in order, take the first match, and name the rule that fired in the write-up.
- **Alternatives rejected:** Reporting the result and letting a reader draw the conclusion — that is how a p-value near 0.05 becomes whatever the analyst wanted. A significance-only rule with no threshold condition — it would recommend shipping on a statistically detectable but commercially trivial effect. Deciding what counts as inconclusive after seeing the interval.
- **Reason:** Fixing the mapping from result to recommendation in advance is the only thing that makes the recommendation evidence rather than opinion.
- **Affects:** The recommendation section of the report, and its verifiability against the pre-registration commit.
- **Falsifiable by:** Nothing after results are seen. A pre-result change is possible but must supersede this entry and be committed before the first `src/` commit.

---

## Part 3 — sample ratio mismatch protocol

### A-010 — SRM is tested with a two-sided exact binomial test, chi-square reported alongside
- **Kind:** decision
- **Part:** 3
- **Date:** 2026-09-10
- **Status:** active
- **Decision:** Use a two-sided exact binomial test of the `gate_30` count against p = 0.5 as the primary SRM test, and report the 1-df chi-square goodness-of-fit statistic next to it.
- **Alternatives rejected:** Chi-square alone — it forces a continuity-correction decision that would then have to be defended. G-test — no advantage at this sample size and less familiar to reviewers. Eyeballing the counts — not a test.
- **Reason:** The exact test has no correction question at all, and at roughly 90,000 rows it agrees with chi-square well beyond reported precision, so the cleaner option costs nothing; reporting both gives a reviewer the form they expect plus a cross-check.
- **Affects:** The SRM p-value that rule R0 keys on.
- **Falsifiable by:** Not applicable — either test answers the same question here.

### A-011 — SRM failure threshold is p < 0.001
- **Kind:** decision
- **Part:** 3
- **Date:** 2026-09-10
- **Status:** active
- **Decision:** Declare SRM failure at p < 0.001, and report the exact SRM p-value whether or not it trips.
- **Alternatives rejected:** p < 0.05 (matching alpha) — about one in twenty clean experiments would trip an alarm whose consequence is withholding the headline, an unacceptable false-alarm rate for a gate on the deliverable. p < 0.0001 — over-tightens with no corresponding gain, since real assignment bugs are already caught with near certainty at 0.001 for this n. A fixed absolute imbalance tolerance (for example "within 1%") — it does not scale with sample size and has no error interpretation.
- **Reason:** SRM is a data-quality alarm on a nuisance parameter rather than a hypothesis of interest, so it is tuned for specificity; the bugs it exists to catch produce gross imbalance that 0.001 still detects easily, and the costs are asymmetric — a false alarm discards a valid experiment, while a small missed imbalance shifts arm weights rather than within-arm rates.
- **Affects:** Whether rule R0 fires and the recommendation is withheld.
- **Falsifiable by:** Nothing in this data. In a live experimentation platform the threshold would be calibrated against the observed false-alarm rate across many tests.

### A-012 — If SRM trips, the analysis continues and the recommendation is withheld
- **Kind:** decision
- **Part:** 3
- **Date:** 2026-09-10
- **Status:** active
- **Decision:** On SRM failure, compute and report the full analysis, fire rule R0 so that no recommendation is issued, add the diagnostic subsection specified in `ARCHITECTURE.md` §2.4, and treat the downgrade as permanent for this deliverable; re-randomisation, post-stratification or inverse-propensity reweighting, trimming rows from the larger arm, and re-testing SRM on any subset are all forbidden.
- **Alternatives rejected:** Stop and publish nothing — wasteful and less informative than a labelled analysis, and it hides a real finding about the dataset. Continue unchanged with a caveat sentence — a caveat next to a confident recommendation is not a caveat, it is decoration. Reweight to restore balance — repairs the symptom by introducing a selection process after assignment, a larger problem than the one being fixed. Trim the larger arm — same objection, plus it discards real assignments.
- **Reason:** A failed integrity check means the arms may not be comparable, which undermines the recommendation but not the value of reporting what the data shows; and because the input is a static public CSV with no assignment log and no upstream owner, there is no path from "SRM tripped" back to "resolved".
- **Affects:** The recommendation section; the presence of the diagnostic subsection; the statement that no covariate-balance check is possible because every non-assignment field is post-treatment.
- **Falsifiable by:** Access to the original assignment logs, which do not exist for this dataset.

---

## Part 3 — power and inference

### A-013 — Power is reported descriptively for a fixed-n dataset
- **Kind:** decision
- **Part:** 3
- **Date:** 2026-09-10
- **Status:** active
- **Decision:** Report power for a two-sided two-proportion z-test at alpha = 0.05 on `retention_7` only, using the observed control-arm rate as baseline and the observed arm sizes, as three numbers: power at a 1.00 pp absolute effect, the detectable effect at 80% power, and the detectable effect at 95% power — plus one sentence comparing the 80%-power detectable effect against the 1.00 pp action threshold.
- **Alternatives rejected:** Omitting power because the sample cannot be changed — then a null result cannot be distinguished from an underpowered one, which is exactly the distinction rules R4 and R5 turn on. Presenting it as a sample-size calculation — dishonest for a fixed dataset. Powering on the guardrail metric — it is not decision-eligible, so its power is descriptive at best.
- **Reason:** The useful question for a fixed sample is "what could this experiment have seen", and answering it before the results are read is what makes a null finding interpretable rather than an excuse.
- **Affects:** Whether rule R4 (practical equivalence) or rule R5 (inconclusive) is available; the sensitivity paragraph of the report.
- **Falsifiable by:** Not applicable — the sample size is what it is.

### A-014 — Observed-effect post-hoc power is banned
- **Kind:** decision
- **Part:** 3
- **Date:** 2026-09-10
- **Status:** active
- **Decision:** Never compute power at the observed effect size or present such a figure as the study's power; the only effect sizes power is evaluated at are 1.00 pp and the two inverse-solved values in A-013.
- **Alternatives rejected:** Reporting observed-effect power "for completeness" — it is a monotone re-expression of the p-value, so it adds no information, and its only practical use is dressing a null result up as a near-miss.
- **Reason:** It is a known statistical error, and a reviewer who knows these datasets will read it as a tell.
- **Affects:** The power section; listed in `ARCHITECTURE.md` §1.7 as invalidating.
- **Falsifiable by:** Not applicable.

### A-015 — Pooled variance for the test, unpooled for the interval
- **Kind:** decision
- **Part:** 3
- **Date:** 2026-09-10
- **Status:** active
- **Decision:** Compute the z-test p-value with the pooled (common-proportion) standard error and the analytic confidence interval with the unpooled (Wald) standard error, and state the asymmetry explicitly in the report.
- **Alternatives rejected:** Pooled for both — the pooled SE is the null variance and is the wrong variance for estimating a non-zero difference. Unpooled for both — loses the correct null variance for the test. Leaving the asymmetry unexplained — a reader who spots two standard errors with no explanation will assume a bug.
- **Reason:** Testing whether a difference is zero and estimating how large it is are different problems with different correct variance estimators.
- **Affects:** The p-value, the analytic interval, and the explanatory paragraph that accompanies them.
- **Falsifiable by:** Not applicable — this is standard and deliberate.

### A-016 — No continuity correction
- **Kind:** decision
- **Part:** 3
- **Date:** 2026-09-10
- **Status:** active
- **Decision:** Apply no continuity correction to the two-proportion z-test.
- **Alternatives rejected:** Yates' correction — it is a conservative adjustment for small expected cell counts, and with tens of thousands of observations per cell it would shift the p-value by an amount invisible at reported precision while making the test inconsistent with the uncorrected interval printed beside it.
- **Reason:** One source of truth for the standard error at a sample size where the normal approximation is accurate far beyond the precision of the decision.
- **Affects:** The primary p-value.
- **Falsifiable by:** An arm shrinking to the point where an expected cell count falls below about 10, which cannot happen with this fixed dataset.

### A-017 — Bootstrap: 10,000 stratified resamples of the D7 difference
- **Kind:** decision
- **Part:** 3
- **Date:** 2026-09-10
- **Status:** active
- **Decision:** Bootstrap the quantity mean(`retention_7` | `gate_40`) − mean(`retention_7` | `gate_30`), in percentage points, with 10,000 resamples drawn with replacement within each arm to that arm's observed size, and report the bootstrap Monte Carlo standard error alongside the interval; the same procedure produces the guardrail interval on `retention_1`.
- **Alternatives rejected:** 1,000 resamples — Monte Carlo error on the tail percentiles becomes comparable to the two-decimal reporting precision. 100,000 resamples — no visible gain at this precision for ten times the runtime. Pooling both arms and resampling the combination — destroys the arm structure and estimates the wrong sampling distribution. Bootstrapping each arm's rate separately and differencing the intervals — that discards the correlation structure and is not a valid interval for the difference.
- **Reason:** Stratified resampling preserves the observed allocation in every replicate, which is what makes the replicate distribution an estimate of the sampling distribution of the difference; 10,000 is the smallest count whose Monte Carlo noise is negligible at reported precision.
- **Affects:** The interval used for the action-threshold condition in rules R1, R2, R4 and R5.
- **Falsifiable by:** Monte Carlo error turning out to be non-negligible at two decimal places, which would require a pre-result entry raising the count for all estimates — never a post-result re-run.

### A-018 — Single RNG seed, literal value 20260910
- **Kind:** decision
- **Part:** 3
- **Date:** 2026-09-10
- **Status:** active
- **Decision:** Define `RANDOM_SEED = 20260910` in exactly one module, import it everywhere, construct every generator explicitly from it, and derive any additional streams by spawning from it rather than introducing a second literal.
- **Alternatives rejected:** A per-module seed — makes reproduction depend on reading every file. Legacy global seeding — order-dependent and silently non-reproducible under refactoring. No seed — the bootstrap interval would change on every run, which breaks the reproduce-exactly claim outright. An arbitrary value like 42 — carries no provenance; the design date does.
- **Reason:** One seed in one place is the only version of this policy that a reader can verify at a glance, and bit-identical interval endpoints across runs are part of the credibility claim.
- **Affects:** Every bootstrap figure; the run manifest; the byte-identity rule for committed outputs.
- **Falsifiable by:** Not applicable. A second seed literal anywhere in the repository is a defect, not an alternative.

### A-019 — Percentile bootstrap interval, with BCa reserved for skewed statistics
- **Kind:** decision
- **Part:** 3
- **Date:** 2026-09-10
- **Status:** active
- **Decision:** Use the percentile method for intervals on retention differences; if any interval is ever reported on a `sum_gamerounds` statistic, use BCa there instead.
- **Alternatives rejected:** BCa for the retention difference — its bias-correction and acceleration terms are built for biased or skewed statistics, and here they would correct for skew that is not present, at the cost of an extra jackknife pass and a harder method to defend. Basic (reverse-percentile) — applies a bias correction with no reason to believe bias exists, and can place an endpoint outside the feasible range for a proportion difference. Normal-approximation bootstrap — then the bootstrap adds nothing the analytic Wald interval does not already give.
- **Reason:** A difference of two proportions at these sample sizes is smooth, essentially unbiased, and near-symmetric, so percentile is correctly calibrated and maximally simple; `sum_gamerounds` is heavily right-skewed, so the same reasoning points the other way there. The method follows the shape of the statistic.
- **Affects:** Both reported intervals, and any future engagement-statistic interval.
- **Falsifiable by:** Visible skew in the bootstrap replicate distribution of the difference, which would justify a pre-result entry switching to BCa.

### A-020 — Roles fixed for reconciling the z-test and the bootstrap
- **Kind:** decision
- **Part:** 3
- **Date:** 2026-09-10
- **Status:** active
- **Decision:** Treat the z-test as the confirmatory instrument deciding the significance condition and the bootstrap interval as the estimation instrument deciding the action-threshold condition; report both prominently, resolve any conflict to the conservative branch (keep the gate at level 30), report the conflict itself as a finding with its likely cause, and never re-run the bootstrap with a different seed or resample count to resolve one.
- **Alternatives rejected:** Reporting only whichever agrees with the narrative — the failure mode this project exists to avoid. Averaging the two — meaningless, they answer different questions. Letting the bootstrap override the test — alpha was pre-registered against the test, so the test is what the significance claim is entitled to rest on. Re-seeding until they agree — p-hacking with extra steps.
- **Reason:** The two instruments share a point estimate and can only disagree near the alpha boundary, where the discrepancy is on the order of the bootstrap's own Monte Carlo error; assigning each a fixed role in advance means a borderline result cannot be resolved by choice.
- **Affects:** Rule R6; the reported Monte Carlo standard error, which is what lets a reader judge whether a conflict is real.
- **Falsifiable by:** A conflict far from the alpha boundary, which would indicate a bug rather than a statistical subtlety and would need debugging, not adjudication.

---

## Part 3 — data handling

### A-021 — The extreme `sum_gamerounds` outlier is kept
- **Kind:** decision
- **Part:** 3
- **Date:** 2026-09-10
- **Status:** active
- **Decision:** Keep the extreme-`sum_gamerounds` row in the primary analysis and in the SRM count; report `sum_gamerounds` statistics both with and without it, with the retained version primary, alongside the median and a stated winsorised or trimmed summary; disclose the value and its arm explicitly.
- **Alternatives rejected:** Dropping it, as most public notebooks do — removing rows from a randomised experiment after assignment on the basis of an outcome variable is a post-randomisation selection process, and it perturbs the arm count that the integrity check in §2 depends on, putting a cleaning judgement upstream of a randomisation test. Dropping it only for engagement statistics and keeping it for retention — defensible, but it produces two populations in one report and the both-ways presentation achieves the same transparency without that. Winsorising the whole column silently — hides the observation rather than disclosing it.
- **Reason:** The primary metric is a boolean, so one row moves an arm's proportion by at most 1/n — on the order of 0.002 pp against a 1.00 pp threshold — while dropping it costs intention-to-treat integrity and contaminates the SRM count. The value is more likely a logging artefact or an automated client than a human, but this dataset contains nothing that can adjudicate that, and the honest move is to say so rather than to delete it.
- **Affects:** Can affect the `sum_gamerounds` mean and any interval on it, and engagement plot scaling. Cannot materially affect the retention proportions, the z-test conclusion, the intervals at reported precision, the SRM p-value, or the recommendation.
- **Falsifiable by:** A documented data-quality flag identifying the row as non-human, which would justify reporting it as excluded-and-disclosed rather than retained — and would still require the both-ways presentation.

### A-022 — Duplicate `userid` policy, with a 0.1% integrity threshold
- **Kind:** decision
- **Part:** 3
- **Date:** 2026-09-10
- **Status:** active — `Affects` field superseded by A-039
- **Decision:** Assert uniqueness and report the result; if duplicates exist, handle them by case — same arm with identical values, keep one and report the count; same arm with conflicting values, exclude the `userid` and report the count; across arms, exclude from both arms and report the count and arms — and if cross-arm duplicates exceed 0.1% of total rows, fire the §2.4 integrity downgrade.
- **Alternatives rejected:** Silent `drop_duplicates` — it converts a signal about the export or the assignment service into a quietly smaller dataset. Keeping cross-arm duplicates — those users cannot be attributed to a treatment at all. Assuming uniqueness without asserting it — the assumption is free to check and expensive to get wrong.
- **Reason:** A duplicate identifier in an A/B export means either double-logging or a user in both arms, and those have different consequences, so the policy has to distinguish them; 0.1% is set low because cross-arm contamination attacks the identifying assumption rather than merely adding noise.
- **Affects:** Denominators, the SRM count, and whether rule R0 fires.
- **Falsifiable by:** The assertion passing, which makes the branches moot — record that as a finding.

### A-023 — Null policy: no imputation, per-metric exclusion, 0.5% integrity threshold
- **Kind:** decision
- **Part:** 3
- **Date:** 2026-09-10
- **Status:** active — `Affects` field superseded by A-040; `Decision` field superseded by A-050
- **Decision:** Never impute; exclude a row with a null `version` from everything; exclude a row with a null retention flag from that metric only, printing the exclusion count and the denominator actually used next to every affected statistic; treat a null `sum_gamerounds` as affecting engagement descriptives only; and fire the §2.4 integrity downgrade if nulls in the primary metric exceed 0.5% of either arm. Report differential missingness between arms even below the threshold.
- **Alternatives rejected:** Imputing retention as `False` — fabricates the outcome being measured and biases both arms toward whichever has more missingness. Dropping any row with any null — discards usable primary-metric data because of a missing engagement value. Complete-case analysis across all columns — same objection, and it silently changes the population between metrics.
- **Reason:** In a randomised experiment the outcome is the measurement, so inventing one is not a cleaning step; and missingness that differs by arm is itself a finding about the experiment rather than a nuisance.
- **Affects:** Denominators for each metric, the reported exclusion counts, and whether rule R0 fires.
- **Falsifiable by:** No nulls being present, which makes the policy moot — record that as a finding.

### A-024 — Retention booleans are coerced through an enumerated whitelist
- **Kind:** decision
- **Part:** 3
- **Date:** 2026-09-10
- **Status:** active — `Decision` field superseded by A-049
- **Decision:** Map an explicit whitelist of accepted tokens to booleans and raise on anything outside it; ban truthiness coercion; and assert after coercion that each column holds exactly two distinct values, that each coerced value's count equals its source token's pre-coercion count, that `version` is exactly the set {`gate_30`, `gate_40`}, and that `sum_gamerounds` is a non-negative integer type. Any assertion failure is a hard stop.
- **Alternatives rejected:** Casting the column directly to `bool` — the string `"False"` becomes `True`, producing a wrong retention rate that looks entirely plausible and passes every eyeball check; this is the highest-consequence silent bug available in this dataset. Relying on the CSV reader's dtype inference — it varies with the export's formatting and with library version. Mapping unknown tokens to `False` — turns a data problem into a wrong number.
- **Reason:** The whole project rests on two proportions, so the coercion that produces them must be impossible to get wrong quietly, and count-preservation assertions are what make that checkable rather than assumed.
- **Affects:** Both retention rates, and therefore every downstream number.
- **Falsifiable by:** Not applicable — the whitelist can be extended, but never loosened into truthiness.

### A-025 — Raw data is not committed; provenance is recorded instead
- **Kind:** decision
- **Part:** 3
- **Date:** 2026-09-10
- **Status:** active
- **Decision:** Keep `data/raw/` git-ignored, document the fetch step in the README, and record the dataset slug, file name, row count, and SHA-256 of the CSV as a `finding` entry in this file; the entrypoint verifies the checksum before running.
- **Alternatives rejected:** Committing the CSV — genuinely better for one-command reproduction, but it redistributes someone else's dataset, which is not ours to grant. Recording no checksum — then "reproduces exactly" is a claim nobody can check, and a silently different input would produce silently different numbers.
- **Reason:** A checksum plus a documented fetch gives a reader the ability to verify the input without the project redistributing it.
- **Affects:** The reproducibility claim, `.gitignore`, and the README setup section.
- **Falsifiable by:** Confirmation that the dataset's licence permits redistribution, which would make committing it the better choice. Flagged as open question 4.

---

## Project-wide — repository and reproducibility

### A-026 — Python 3.12
- **Kind:** decision
- **Part:** project-wide
- **Date:** 2026-09-10
- **Status:** active — `Falsifiable by` field superseded by A-042
- **Decision:** Pin the interpreter minor version to 3.12 in `.python-version`, and have the initialising session record the exact patch version it used as a `finding` entry here; the minor version may not change without a superseding entry.
- **Alternatives rejected:** An unpinned interpreter — the bootstrap's reproducibility depends on the numpy/Python stack, so "any recent Python" quietly breaks bit-identical output. Pinning the patch version in the file itself — it would fail on a machine that has a different patch of the same minor for no analytical reason.
- **Reason:** The minor version is the granularity at which behaviour changes matter here; the patch is recorded for provenance rather than enforced.
- **Affects:** The clean-checkout sequence and the run manifest.
- **Falsifiable by:** A required dependency dropping 3.12 support. Flagged as open question 6.

### A-027 — venv plus pip, with a resolved lock file
- **Kind:** decision
- **Part:** project-wide
- **Date:** 2026-09-10
- **Status:** active
- **Decision:** Use `venv` and `pip`; pin direct dependencies with `==` in `requirements.txt` and install for reproduction from a fully resolved `requirements.lock.txt`; permitted libraries for Part 3 are `pandas`, `numpy`, `scipy`, `statsmodels`, `matplotlib`, and adding a dependency requires a new entry here.
- **Alternatives rejected:** `uv` — faster and genuinely nicer, but it adds a tool a reviewer must install before they can reproduce anything. Poetry — same objection plus a lock format that is not readable as a plain list. An unpinned `requirements.txt` — transitive drift is exactly what breaks bit-identical bootstrap output.
- **Reason:** The lowest-assumption toolchain a reviewer can run is the one that makes the reproducibility claim credible; the loose file documents intent and the lock file guarantees the environment.
- **Affects:** The clean-checkout sequence, the run manifest, and the byte-identity rule for committed outputs.
- **Falsifiable by:** A preference for `uv`, which is a one-line change to the setup instructions. Flagged as open question 5.

### A-028 — Notebooks are never the source of a number
- **Kind:** decision
- **Part:** project-wide
- **Date:** 2026-09-10
- **Status:** active
- **Decision:** Exclude notebooks from the reproducible path entirely; if a `.ipynb` is ever produced it is a presentation artefact generated from the scripts, which remain the source of truth.
- **Alternatives rejected:** Notebook-first analysis with committed outputs — a notebook's real execution order is not recoverable from the file, so "run this and you get my numbers" becomes unverifiable. Notebooks with an enforced execute-in-order check — added machinery to make a worse format almost as trustworthy as scripts.
- **Reason:** Unverifiable numbers are the specific failure this project is built to avoid, and hidden execution order is the most common way they happen.
- **Affects:** Repository layout and the clean-checkout rule.
- **Falsifiable by:** Not applicable.

### A-029 — Aggregation in SQL for Parts 1 and 2, Python for Part 3
- **Kind:** decision
- **Part:** project-wide
- **Date:** 2026-09-10
- **Status:** active
- **Decision:** Run every aggregation, join, filter, cohort assignment, and window function for Parts 1 and 2 in BigQuery SQL, with Python limited to executing a query and rendering an already-aggregated result of at most a few thousand rows; run Part 3's inference in Python. Loading GA4 raw events into pandas for consistency, and pushing the bootstrap into SQL for consistency, are both prohibited.
- **Alternatives rejected:** pandas throughout — the GA4 events table is nested, date-sharded and far larger than local memory, and re-deriving cohort definitions in pandas guarantees they drift from the SQL. SQL throughout — the z-test, exact binomial test, seeded bootstrap and power curve would require reimplementing distribution functions in SQL, which is dramatically less auditable, not more.
- **Reason:** One principle applied to two inputs: computation happens where the data lives and where the operation is naturally expressible. A partitioned warehouse-scale event table yields SQL; a 90,000-row flat file plus an inference procedure yields Python. Descriptive aggregation inside Part 3 stays in pandas, because the boundary is about where the data lives rather than a house preference for SQL.
- **Affects:** Directory layout, what each part's session is allowed to write, and the explanatory paragraph in `ARCHITECTURE.md` §7.3 that keeps this from reading as an inconsistency.
- **Falsifiable by:** Not applicable — the reasoning is about data location and expressibility, both of which are fixed.

### A-030 — Ordinal prefixes for SQL, importable names for Python
- **Kind:** decision
- **Part:** project-wide
- **Date:** 2026-09-10
- **Status:** active
- **Decision:** Name SQL files `NN_partX_<purpose>.sql` with a globally sequenced two-digit execution ordinal and reserved ranges (01–29 Part 1, 30–59 Part 2, 60–89 shared, 90–99 QA), leaving gaps so insertions never force a renumber; name Python modules with importable `snake_case` and no numeric prefix, expressing execution order in the single entrypoint instead.
- **Alternatives rejected:** Ordinal prefixes on Python modules — a leading digit is an illegal identifier, so it forces `importlib` workarounds and makes the code harder to test. No ordinals on SQL — execution order would then live only in prose, and a reader could not infer it from a directory listing. Contiguous numbering with no gaps — inserting one query later would renumber the rest and break every reference in the reports.
- **Reason:** SQL files are executed and Python modules are imported, so the clearest ordering signal differs; putting Part 3's order in the entrypoint also puts it somewhere a reviewer reads top to bottom.
- **Affects:** File naming across the repository; the paragraph in §7.2 explaining the difference.
- **Falsifiable by:** Not applicable.

### A-031 — Reporting precision and notation
- **Kind:** decision
- **Part:** project-wide
- **Date:** 2026-09-10
- **Status:** active
- **Decision:** Report retention rates and effects to two decimal places in percentage points, report exact p-values to three significant figures, and use no asterisk or star significance notation anywhere in the repository.
- **Alternatives rejected:** "p < 0.05" — discards the information that distinguishes a borderline result from a decisive one, which is exactly the information rules R1–R5 and §4.3 need. Star notation — compresses a continuous quantity into a category and invites reading significance as effect size. Rounding p to zero — implies impossibility.
- **Reason:** The decision rule depends on how close the p-value is to the boundary, so the reported precision has to preserve that.
- **Affects:** Every number in the reports and the README.
- **Falsifiable by:** Not applicable.

### A-032 — The README opens with exactly three PM-actionable sentences
- **Kind:** decision
- **Part:** project-wide
- **Date:** 2026-09-10
- **Status:** active
- **Decision:** Open `README.md` with exactly three sentences before any heading or badge — what was tested and on how many players over what horizon; the estimated D7 effect with its interval; the recommendation and the one thing that would change it — written only after Part 3's numbers exist, each figure traceable to a file in `outputs/`, and asserting nothing the negative-results section says the data cannot support.
- **Alternatives rejected:** A conventional project-description opener — a reviewer's first ten seconds are spent on whatever is at the top, and "this repository contains" spends them on nothing. A one-paragraph executive summary — long enough to hedge, and hedging is what it would fill with. Methodology in the opener — the reader who needs the method will scroll.
- **Reason:** The deliverable is a decision, so the artefact should lead with the decision; constraining it to three sentences forces the analysis to have actually reached one.
- **Affects:** `README.md`; indirectly, the discipline of the recommendation section.
- **Falsifiable by:** Not applicable.

### A-033 — The negative-results section is a required deliverable, placed before the recommendation
- **Kind:** decision
- **Part:** 3
- **Date:** 2026-09-10
- **Status:** active
- **Decision:** End Part 3's analysis with a top-level "What this experiment does not support" section, positioned after the results and before the recommendation, containing the four labelled subsections specified in `ARCHITECTURE.md` §6, with every "what would be required" item naming a specific measurement.
- **Alternatives rejected:** A limitations list at the end — read last, if at all, and it reads as ritual. A caveats footnote — actively worse than nothing, because it signals the author knew and chose to bury it. Folding limitations into the discussion — they get diluted, and the reader cannot tell which claims are bounded by which limitation.
- **Reason:** The reader should know the boundary of the claim before reading the claim; and on this dataset the dilution from unmeasured exposure is large enough that a null result means something quite different from "gate placement does not matter", which the write-up has to say out loud.
- **Affects:** Report structure and the constraint that no README claim may contradict this section.
- **Falsifiable by:** Not applicable.

### A-034 — `ARCHITECTURE.md` is read-only to implementation sessions; ownership is by path
- **Kind:** decision
- **Part:** project-wide
- **Date:** 2026-09-10
- **Status:** active
- **Decision:** Give each part's session an explicit list of owned paths (`ARCHITECTURE.md` §8); make `ARCHITECTURE.md` writable only by the architecture session; route disagreements through a `challenge` entry here; keep this file append-only for everyone; and treat `requirements*.txt`, `.python-version` and `.gitignore` as append-only after Part 3 creates them.
- **Alternatives rejected:** Letting the analysis session edit the architecture document — a pre-registration the analyst can edit is not a pre-registration. A single session building everything — no collision problem, but no ability to add parts later without re-deriving context. Ownership by convention rather than an explicit path list — collisions get discovered as merge conflicts.
- **Reason:** The pre-registration only has force if the party being constrained by it cannot rewrite it; and explicit path lists are what let later sessions be added without stepping on finished work.
- **Affects:** What each session may write; the change protocol in §11.
- **Falsifiable by:** Not applicable.

### A-035 — No public analysis of Cookie Cats is consulted before the numbers are final
- **Kind:** decision
- **Part:** 3
- **Date:** 2026-09-10
- **Status:** active
- **Decision:** Do not read, search for, or reference any existing public analysis of this dataset until Part 3's numbers are final; afterwards, any comparison is framed as comparison, not as corroboration.
- **Alternatives rejected:** Reading a few notebooks first to see what to expect — it anchors the analysis on someone else's conclusion and makes every subsequent judgement call suspect, including the ones made honestly. Reading them to check the arithmetic afterwards — acceptable once the numbers are locked, which is what this entry permits.
- **Reason:** The disagreement across public analyses of this dataset comes from choosing an interpretation after seeing a p-value; the only defence that actually works is not knowing the expected answer while the decisions are being made.
- **Affects:** The credibility of every entry above; listed in `ARCHITECTURE.md` §1.7 as invalidating.
- **Falsifiable by:** Not applicable.

---

## Amendment pass — `ARCHITECTURE.md` v1.1 (2026-09-10)

All entries below were written before any data access and before the repository was
initialised. `A-047` records the two bookkeeping conventions this pass introduced
(Status-line annotation and partial supersession), since the append-only rule means
the format section above can only be extended by a new entry, never edited.

### A-036 — `gate_30` as control is confirmed, not assumed
- **Kind:** supersedes A-001
- **Part:** 3
- **Date:** 2026-09-10
- **Status:** active
- **Decision:** Record `gate_30` as the control group and `gate_40` as the moved-gate group as a **confirmed fact**, on the basis that the Kaggle dataset card states it directly; the sign convention in `ARCHITECTURE.md` §1.6 is unchanged.
- **Alternatives rejected:** Leaving A-001 as an assumption — it is no longer one, and carrying a confirmed fact as an open assumption misleads a reviewer about how much of the design rests on guesswork. Treating the dataset card as off-limits under A-035 — the card states the experimental design, not anyone's analysis or result, so reading it cannot anchor the analysis on a conclusion; A-035 is untouched and still binding.
- **Reason:** The distinction between "we assumed this" and "the dataset documents this" is exactly the kind of thing a reviewer who knows the dataset will check, and it is free to get right.
- **Affects:** Open question 1 (now closed); `ARCHITECTURE.md` §9 item 1; the framing of every reported effect. Nothing in the arithmetic changes, because A-001's assumed direction was correct.
- **Falsifiable by:** The dataset card being amended or contradicted by the data's own provenance, neither of which is expected.

### A-037 — Decision rules are evaluated in three stages, not one flat sweep
- **Kind:** supersedes A-009
- **Part:** 3
- **Date:** 2026-09-10
- **Status:** active
- **Decision:** Evaluate the decision rules in three stages — Stage 1 preconditions (R0, R6) tested first and able to set the recommendation alone; Stage 2 outcome branches (R1–R5), mutually exclusive and exhaustive so exactly one fires; Stage 3 modifiers (R7–R10) applied to whichever branch fired — with a `CI₇` lower bound of exactly +1.00 pp counting as not clearing the threshold and an endpoint of exactly ±1.00 pp counting as within it, and with the reachability trace in §1.6 kept as part of the deliverable.
- **Alternatives rejected:** The v1.0 flat first-match ordering — see the honest record below; it made three rules dead code. Reordering the flat table to put R6, R7 and R8 first — it would make the modifiers reachable but they would then fire before any branch existed to modify, which is incoherent. Merging the guardrail conditions into the R1–R5 conditions — it doubles the branch count, and every added branch is another place for a gap to hide. Renaming the rules to P/B/M prefixes to signal the kinds — clearer in isolation, but `assumptions.md` is append-only and A-001, A-004, A-005, A-006, A-008, A-010, A-012, A-013, A-017, A-020, A-022, A-023 and A-031 all cite the R-labels; renaming would strand those citations in a file that cannot be edited to follow, so the labels were kept and the kinds are carried by the stage headings instead.
- **Reason:** The three kinds answer different questions — is this experiment usable, what did it show, does the guardrail qualify it — and a single evaluation order over all three cannot express that. R1–R5 already partition the outcome space, so anything placed after them in a first-match sweep is unreachable by construction.
- **Affects:** `ARCHITECTURE.md` §1.6 in full; §4.3 item 2; the requirement that the write-up quote the whole path (precondition state, branch, modifier) rather than a single rule name; §7.7 step 18 and the step 20 assertion that exactly one branch fired.
- **Honest record of what v1.0 broke:** under v1.0 the guardrail behaviour specified in §1.2 and A-003 **was not reachable**. R8 existed to downgrade a significant D7 gain to "investigate first" when D1 had regressed, but that case matched R1 and stopped there, so the downgrade could never fire; R7 and R6 were dead for the same reason. A-003's stated asymmetry — a guardrail that can hold a recommendation but never create one — was therefore void in v1.0 as written, not merely unclear. It is recorded here rather than quietly fixed because a pre-registration whose defects are silently patched is worth no more than one that was never written.
- **Falsifiable by:** A traced case that reaches no recommendation, or two, under the staged structure. The §1.6 trace and the step 20 assertion exist to catch that.

### A-038 — The SRM denominator is the assignment population, fixed before any exclusion
- **Kind:** decision
- **Part:** 3
- **Date:** 2026-09-10
- **Status:** active — `Decision` field superseded by A-052
- **Decision:** Define SRM n as the count of raw input rows whose `version` is exactly `gate_30` or `gate_40` after whitelist coercion, fixed before any other exclusion, so that duplicate `userid`s, retention nulls, and the extreme `sum_gamerounds` row are all counted in it; treat rows with a null or out-of-whitelist `version` as unassignable, count them separately, and fire the integrity downgrade if they exceed 0.1% of raw rows; report post-exclusion arm counts as a descriptive differential-exclusion check with no test and no threshold; and enforce the ordering in code by running SRM at step 7 of §7.7, ahead of duplicate and null handling at steps 10 and 11.
- **Alternatives rejected:** Running SRM on the post-exclusion analysis population — it puts cleaning judgements upstream of an integrity test, which A-021 and §5.1 forbid, and it lets a null-handling decision change whether the experiment is declared valid. Running SRM both ways and reporting both — two SRM p-values with no rule for which governs is worse than one; the second would be quoted whenever it was more convenient. Attaching a second SRM test to the cleaned population — same objection, and it would give an integrity p-value to a population selected after assignment. Leaving it unspecified, as v1.0 did — the document then argued both ways, and the implementation session would have had to guess.
- **Reason:** SRM asks one question — was assignment balanced — and the only property of a row that bears on it is that the row was assigned. What happens to a row afterwards, for reasons unrelated to assignment, must not be able to move the count. Unassignable rows are the exception because they were never assigned at all, so there is nothing for the test to say about them; that is a failure of the assignment or logging mechanism itself, which is why it gets the same 0.1% threshold as a cross-arm duplicate rather than the looser 0.5% used for missing outcomes.
- **Affects:** `ARCHITECTURE.md` §2.2, §5.1, §5.2, §5.3 and §7.7; the SRM p-value and therefore whether R0 fires; the reported denominators for each metric.
- **Falsifiable by:** Discovering that unassignable rows are systematically related to arm assignment — which cannot be checked here, since an unassignable row has no arm. Recorded as a limitation for §6.3 if any such rows exist.

### A-039 — A-022's `Affects` field corrected: duplicates do not enter the SRM denominator
- **Kind:** supersedes A-022
- **Part:** 3
- **Date:** 2026-09-10
- **Status:** active
- **Supersedes scope:** the `Affects` field of A-022 only. Its decision, thresholds and reasoning stand unchanged.
- **Decision:** Replace A-022's `Affects` with: per-metric denominators, the reported duplicate counts, and whether R0 fires via the 0.1% cross-arm threshold — **not** the SRM count, which is fixed before this check runs (A-038).
- **Alternatives rejected:** Leaving the field as written — it contradicted A-021's principle and was one of the two statements that left the SRM denominator ambiguous.
- **Reason:** Duplicates can still trigger the integrity downgrade, but through their own threshold rather than by moving the SRM count; those are different mechanisms and the entry conflated them.
- **Affects:** Reading of A-022; §5.2.
- **Falsifiable by:** Not applicable — this is a correction, not a new call.

### A-040 — A-023's `Affects` field corrected, and unassignable rows given a threshold
- **Kind:** supersedes A-023
- **Part:** 3
- **Date:** 2026-09-10
- **Status:** active — `Decision` field superseded by A-051
- **Supersedes scope:** the `Affects` field of A-023, plus an addition to its `version`-null handling. Its no-imputation rule, per-metric exclusion rule and 0.5% primary-metric threshold stand unchanged.
- **Decision:** Replace A-023's `Affects` with: per-metric denominators, the reported exclusion counts, and whether R0 fires via the 0.5% primary-metric threshold — **not** the SRM count (A-038). Add that a row with a null or out-of-whitelist `version` is unassignable, enters neither SRM arm, and fires the integrity downgrade if such rows exceed **0.1%** of raw rows.
- **Alternatives rejected:** Leaving nulls with no threshold of their own on the `version` column — a batch of unassignable rows is an assignment-mechanism failure and would otherwise pass unremarked. Folding unassignable rows into the 0.5% outcome-null threshold — wrong class of fault and too loose for it.
- **Reason:** Missing outcomes cost information; missing assignments cost the identifying assumption. The thresholds should differ accordingly.
- **Affects:** Reading of A-023; §2.2 and §5.3; §7.7 step 6.
- **Falsifiable by:** Not applicable.

### A-041 — A-003's rejected-alternative cross-reference corrected
- **Kind:** supersedes A-003
- **Part:** 3
- **Date:** 2026-09-10
- **Status:** active
- **Supersedes scope:** the `Alternatives rejected` field of A-003 only. Its decision and reasoning stand unchanged.
- **Decision:** A-003's first rejected alternative should read "co-primary with a correction — **see A-006**", the multiple-comparison entry. A-007 is the estimand entry and carries no multiplicity argument.
- **Alternatives rejected:** Not applicable — this is a factual correction.
- **Reason:** A cross-reference that points at the wrong entry is worse than none: it sends a reviewer looking for an argument that is not there and makes the rest of the file's references suspect.
- **Affects:** Reading of A-003. Note also that the guardrail behaviour A-003 specifies is only actually reachable under the staged evaluation in A-037; under v1.0 it was not.
- **Falsifiable by:** Not applicable.

### A-042 — A-026's open-question reference corrected
- **Kind:** supersedes A-026
- **Part:** project-wide
- **Date:** 2026-09-10
- **Status:** active
- **Supersedes scope:** the `Falsifiable by` field of A-026 only. Its 3.12 pin and reasoning stand unchanged.
- **Decision:** A-026's `Falsifiable by` should read "a required dependency dropping 3.12 support" with **no open-question reference attached**. The interpreter minor version was never an open question: §9 question 5 covers the toolchain (venv plus pip, A-027) and question 6 covers dataset provenance, which is unrelated.
- **Alternatives rejected:** Re-pointing it at question 5 — the toolchain question is about the packaging tool, not the interpreter version, and merging them would misrepresent what was actually asked.
- **Reason:** Same as A-041: a wrong reference costs a reviewer's trust in every other one.
- **Affects:** Reading of A-026; §9.
- **Falsifiable by:** Not applicable.

### A-043 — Figure reproducibility is a same-machine guarantee; tables carry the cross-machine claim
- **Kind:** decision
- **Part:** project-wide
- **Date:** 2026-09-10
- **Status:** active
- **Decision:** Require byte-identical reproduction across machines for `outputs/tables/*` and `outputs/run_manifest.json` (timestamp exempt), and for figures require only that (i) every figure is generated from a committed table, so its numbers and labels reproduce byte-identically even when its pixels do not, and (ii) a re-run on the same machine with the same lock file produces byte-identical PNGs — supported by an explicit `Agg` backend, fixed figure size, DPI and font family with a declared fallback, explicit PNG metadata so no creation date is embedded, no timestamps or random jitter in any figure, and the `matplotlib` version and backend recorded in the manifest.
- **Alternatives rejected:** Keeping the v1.0 rule that PNGs may differ "only in embedded metadata" — matplotlib does not produce byte-identical PNGs across versions, platforms or font configurations, so the first re-run on another machine would falsify a reproducibility claim printed in the document, which costs more credibility than the rule ever bought. Committing no figures — then a reader has to run the project to see anything, and the README's three sentences lose their supporting picture. Pinning fonts by shipping a font file — fixes cross-machine rendering but adds a binary asset and a licence question for a benefit no reader needs. Rendering to SVG instead — more reproducible in principle, still not byte-identical, and it trades a real problem for a fiddlier one.
- **Reason:** A reproducibility claim is only worth making if it survives being tested. The thing that actually needs to reproduce is the numbers, and routing every figure through a committed table makes that true by construction while leaving the pixel-level promise scoped to where it can be kept.
- **Affects:** §7.5; §7.7 steps 19 and 20; the manifest's contents; the rule that no figure is the sole record of a value.
- **Falsifiable by:** A demonstrated deterministic PNG pipeline across the platforms in use, which would allow the stronger rule to be restored.

### A-044 — The entrypoint's execution order is specified, with three failure classes
- **Kind:** decision
- **Part:** 3
- **Date:** 2026-09-10
- **Status:** active — `Decision` field superseded by A-053
- **Decision:** Fix the 20-step order in `ARCHITECTURE.md` §7.7 as the definition of what `run_part3.py` contains, label every step **hard stop**, **downgrade** or **finding**, and treat two orderings as load-bearing: the SRM test runs before duplicate and null handling, and the decision pipeline runs after every downgrade flag can have been set.
- **Alternatives rejected:** Leaving order to the implementation session, as v1.0 did — §7.5 said order lives in the entrypoint but no section said what the order was, so the one part of the design that guarantees the SRM denominator rule was left to chance. Specifying order only as prose inside §7.5 — it would be read as narrative rather than as a specification. A two-way stop/continue split instead of three classes — it cannot express the SRM trip, which must continue to completion with the recommendation withheld.
- **Reason:** Several decisions in this document are only true if the steps happen in a particular order, so the order is part of the design rather than an implementation detail; and a failure taxonomy is what stops an implementer from turning a downgrade into an exception or a finding into a silent pass.
- **Affects:** §7.7 in full; §2.2's denominator rule; §7.5's self-verification bullet; what the Part 3 session is expected to build.
- **Falsifiable by:** A step turning out to depend on a later one, which would require a superseding entry rather than a quiet reorder.

### A-045 — The §11 change log records four labelled fields per version, and there is no separate changelog file
- **Kind:** decision
- **Part:** project-wide
- **Date:** 2026-09-10
- **Status:** active
- **Decision:** Require every version entry in §11 to record sections touched, the substantive change per section, the `assumptions.md` entries added or superseded or annotated, and an explicit yes/no on whether §1–§6 were touched together with the effect on the pre-registration freeze; and keep §11 plus `assumptions.md` as the only record, with git as permanent history — no `CHANGELOG.md`.
- **Alternatives rejected:** The v1.0 one-line note — for a document this size a reader cannot tell from it whether a change touched a frozen pre-registration section or a naming convention, which is the one thing the log most needs to answer. A separate changelog file — a third record of the same decisions that drifts out of sync with the other two, and a drifted record is worse than none. Relying on git log alone — it is not available until the repository is initialised, and it records commits rather than document versions.
- **Reason:** The freeze in §11 is the mechanism that makes the pre-registration verifiable, so whether a change crossed it must be checkable from the log without re-reading the document.
- **Affects:** §11; every future version of `ARCHITECTURE.md`.
- **Falsifiable by:** Not applicable.

### A-046 — Open questions 1 through 6 are resolved
- **Kind:** decision
- **Part:** project-wide
- **Date:** 2026-09-10
- **Status:** active
- **Decision:** Close all six open questions: (1) `gate_30` as control is confirmed from the Kaggle dataset card (A-036); (2) the 1:1 allocation is kept and recorded as a permanent unknown, with a mandatory conditional statement in the report that a weighted original design would make the SRM p-value uninterpretable; (3) the 1.00 pp threshold is kept and owned rather than provisional; (4) raw data stays git-ignored with a fetch step and SHA-256 (A-025); (5) the toolchain stays venv plus pip with a resolved lock file (A-027); (6) the calendar window and game version are stated as unknown with no external dating attempted.
- **Alternatives rejected:** For (2), dropping the SRM check because the design ratio is undocumented — it is the single most valuable integrity signal available in this dataset, and a stated conditional preserves the honest reading without discarding it. For (2), inferring the ratio from the observed counts — circular, and it would make the test unable to fail. For (6), attempting to date the experiment from external sources — it would be speculation presented as provenance, and §6.3 is stronger for saying plainly that the window is unknown.
- **Reason:** Open questions with stated defaults keep work unblocked, but leaving them open once answered leaves a reader unable to tell which parts of the design are settled; and a question that can never be answered, like (2), is better recorded as a permanent unknown with a consequence attached than left looking pending.
- **Affects:** §9 in full; §2.1's required conditional statement; the Status lines of A-005 and A-008.
- **Falsifiable by:** New public documentation of the experiment's design ratio or calendar window, which would reopen (2) and (6) respectively.

### A-047 — Two append-only bookkeeping conventions
- **Kind:** decision
- **Part:** project-wide
- **Date:** 2026-09-10
- **Status:** active
- **Decision:** Extend the file's conventions in two ways, since the format section above cannot be edited: **(i) Status-line annotation** — the `Status` line may carry a short annotation beyond `active` or `superseded by A-NNN`, such as a confirmation date or a named field that a later entry replaces, because the Status line is the only part of an existing entry that may be edited; **(ii) partial supersession** — a superseding entry may add a `Supersedes scope` field naming the single field it replaces, leaving the rest of the target entry in force, and the target's Status then reads `active — <field> superseded by A-NNN` rather than fully superseded.
- **Alternatives rejected:** Declaring a whole entry superseded to fix one wrong cross-reference — it overstates the change and buries a still-valid decision under a supersession notice. Editing the target entry's body to fix the reference in place — forbidden by the append-only rule, and the rule is worth more than the tidiness. Rewriting the format section to document these conventions there — also forbidden; recording them as an entry is the only append-only way to extend the format.
- **Reason:** Append-only is what makes this file evidence rather than a document that can be groomed after the fact, so the conventions have to bend around it rather than the reverse — and a correction should be as narrow as the mistake.
- **Affects:** How A-039 through A-042 are read; the Status lines of A-001, A-003, A-005, A-008, A-009, A-022, A-023 and A-026; how every future correction is recorded.
- **Falsifiable by:** Not applicable.

---

## Amendment pass — `ARCHITECTURE.md` v1.2 (2026-09-10)

Two defects of the same class as v1.1's: a specified behaviour that the execution
order made unreachable. Both traced to one root cause — coercion was total and
hard-stopping, which pre-empted the count-report-threshold machinery built on top of
it. Written before any data access and before the repository was initialised.

### A-048 — Structural faults stop the run; data-quality faults are counted
- **Kind:** decision
- **Part:** project-wide
- **Date:** 2026-09-10
- **Status:** active
- **Decision:** Sort every data fault into one of two classes and let the class alone determine the response — **structural** (the file is not the file the document describes: hard stop at §7.7 step 5, nothing computed, nothing written) or **data-quality** (the file is right and values are absent or duplicated: counted, reported, and downgrade-triggering only past a stated threshold). The governing rule is that **an absent value is a data-quality fault and an unrecognised present value is structural.** Classified accordingly: a missing `version` is data-quality (unassignable, 0.1%); a `version` present but not an arm label is structural; a missing retention flag is data-quality (per-metric exclusion, 0.5%); a retention flag present but in neither the true nor the false token set is structural; a missing `sum_gamerounds` is data-quality (engagement descriptives only); a `sum_gamerounds` present but not a non-negative integer is structural; a duplicate `userid` is data-quality (§5.2, 0.1% cross-arm). The extreme `sum_gamerounds` value is neither — it is a valid observation (A-021).
- **Alternatives rejected:** Treating every unrecognised value as a data-quality fault and counting it — it would require mapping an unknown token to a retention outcome or an arm, which is imputation of the outcome variable under another name, banned by A-023; and a third arm label counted as "0.02% of rows" would let an analysis proceed on a file the pre-registration does not describe. Treating every missing value as structural and stopping — internally consistent, and it is effectively what v1.0 and v1.1 did by accident, but it deletes the entire §5.3 policy along with the 0.5% threshold and the differential-missingness reporting, which are the parts of the data-handling section a reviewer would actually check. Per-column validation at the point of use rather than one gate — a structural fault in a retention column would then be found after the SRM test, discarding a number already computed from a file that turned out to be the wrong file. Making the distinction case-by-case in each subsection — that is exactly what produced these two defects.
- **Reason:** A missing value is self-describing: we know precisely what we do not know, and there is a defined, disclosable response. An unrecognised non-empty value is not — acting on it means guessing what the producer meant. And for a fixed public CSV, an unrecognised token almost always means the wrong file, a mangled export, a wrong delimiter, or a different dataset revision, where the remedy is to fetch the right file rather than to clean this one. Drawing the line once, in the §5 preamble, is what stops four sections from each assuming a different one.
- **Affects:** New preamble to `ARCHITECTURE.md` §5; §5.3, §5.4, §2.2 and §7.7 all reconciled to it; the failure-class labels in §7.7; whether the run stops or downgrades for each case above.
- **Falsifiable by:** An unrecognised token whose meaning is documented by the dataset's producer — then it belongs in a token set, added by a superseding entry, rather than being reclassified.

### A-049 — Coercion is three-state, and the two-distinct-values assertion is replaced
- **Kind:** supersedes A-024
- **Part:** 3
- **Date:** 2026-09-10
- **Status:** active
- **Supersedes scope:** the `Decision` field of A-024 only. Its ban on truthiness coercion, its hard-stop-on-unrecognised principle, and its reasoning stand unchanged and are the reason this entry keeps enumerated sets rather than loosening them.
- **Decision:** Replace A-024's coercion rule with a three-state scheme: enumerated **true**, **false** and **missing** token sets for each retention column, and the arm set {`gate_30`, `gate_40`} plus the same missing set for `version`, with `sum_gamerounds` a non-negative integer or a missing value. A value in the missing set coerces to an explicit missing state and the run continues; only a value outside all of a column's sets hard-stops. Replace the assertion "each coerced column contains exactly two distinct values" with: each retention column's **non-missing** values form exactly {`True`, `False`}; `count(True) + count(False) + count(missing)` equals the raw row count; each state's count equals the total count of its source tokens before coercion, with the missing state summed across every missing spelling that occurred; `version`'s non-missing values are exactly the arm set and its unassignable count equals its missing count; `sum_gamerounds` is a non-negative integer among non-missing values.
- **Alternatives rejected:** Keeping the two-distinct-values assertion alongside a permitted missing state — the two are incompatible: a column with excluded nulls holds three states, so the assertion would be false by construction on any file the policy is meant to handle. Dropping the assertion and asserting nothing — it is the check that catches the truthiness bug A-024 exists to prevent. Encoding missing as a sentinel value inside the boolean domain — a sentinel that compares equal to `False` in any arithmetic is the same silent-wrong-rate failure in a new costume.
- **Reason:** Count conservation across three states is a strictly stronger check than counting distinct values, and it is the one that actually verifies coercion preserved the file. The assertion had to change because the policy changed; leaving both in place would have replaced an unreachable policy with an unsatisfiable assertion.
- **Affects:** `ARCHITECTURE.md` §5.4 in full; §7.7 steps 5, 6 and 9; the reachability of §5.3; the assertion set that §7.7 step 20 re-checks.
- **Falsifiable by:** A missing spelling in the file that is not in the enumerated missing set — which hard-stops rather than passing silently, and is then added to the set by a superseding entry.

### A-050 — A-023's missing-value policy is unchanged and now reachable
- **Kind:** supersedes A-023
- **Part:** 3
- **Date:** 2026-09-10
- **Status:** active
- **Supersedes scope:** the `Decision` field of A-023, restated so that it names the coercion behaviour it depends on. Its substance — no imputation, per-metric rather than whole-row exclusion, the 0.5% primary-metric threshold, and reporting differential missingness below the threshold — is unchanged. Its `Affects` field remains as corrected by A-040.
- **Decision:** A-023's policy stands, and its execution now depends explicitly on A-049's missing state: a recognised missing marker in a retention column coerces to that state at §7.7 step 6 and the run continues, arriving at step 11 with the missing counts intact. A missing `version` remains whole-row unassignable at the 0.1% threshold; a `version` present but not an arm label is not a null at all and is out of this entry's scope (A-051).
- **Alternatives rejected:** Deleting A-023 as unreachable and stopping the run on any missing value — see A-048; it would discard the 0.5% threshold and the differential-missingness reporting, which are among the few checks in this document that would actually catch a broken export. Rewriting the policy to whole-row exclusion for retention nulls — it discards usable primary-metric data because a guardrail value is absent, and it silently changes the population between metrics.
- **Honest record of what v1.0 and v1.1 broke:** A-023's retention-null policy **could not run** in either version. §5.4 made coercion raise on any token outside the true and false sets, and §7.7 made that a hard stop; a null is outside those sets, so the first missing retention value terminated the run at coercion and step 11 was never reached. Per-metric exclusion, the 0.5% threshold, the differential-missingness requirement and the printed denominators were therefore dead specification for two versions — the same defect class as v1.1's unreachable modifier rules, in a different section. It is recorded rather than quietly repaired because a document that only claims to have checks is worth less than one whose checks are known to execute.
- **Affects:** `ARCHITECTURE.md` §5.3; §7.7 steps 6 and 11; the per-metric denominators reported next to every affected statistic.
- **Falsifiable by:** A traced missing value that still fails to reach step 11 under the revised order.

### A-051 — A-040's "unassignable" is narrowed to missing `version` only
- **Kind:** supersedes A-040
- **Part:** 3
- **Date:** 2026-09-10
- **Status:** active
- **Supersedes scope:** the `Decision` field of A-040 only, specifically its definition of unassignable. Its 0.1% threshold for missing-`version` rows and its `Affects` correction stand unchanged.
- **Decision:** Unassignable means a `version` that is **missing** — an empty field or a recognised missing token — and nothing else. A `version` value that is present but is neither `gate_30` nor `gate_40` is a structural fault: it hard-stops at §7.7 step 5 and never reaches the 0.1% threshold. A-040's phrasing "null or out-of-whitelist" is withdrawn.
- **Alternatives rejected:** Counting an unrecognised arm label against the 0.1% threshold, as A-040's wording implied — it directly contradicted §7.7 step 5, which hard-stopped on exactly those values, so one of the two had to go; and it would allow the analysis to proceed on a file containing an arm the pre-registration does not describe. Widening the arm set to accept a third value — the entire design in §1 is a two-arm comparison, so a third arm is a different experiment, not a wider one.
- **Reason:** A missing assignment and an unrecognised assignment fail differently. The first is a logging gap in the right experiment; the second is evidence this is not that experiment.
- **Affects:** `ARCHITECTURE.md` §2.2 and §5.3; §7.7 steps 5 and 7; the SRM denominator's exclusion set.
- **Falsifiable by:** Documentation showing a third arm label was part of the original design, which would invalidate far more of this document than this entry.

### A-052 — A-038's denominator rule restated for the revised step order
- **Kind:** supersedes A-038
- **Part:** 3
- **Date:** 2026-09-10
- **Status:** active
- **Supersedes scope:** the `Decision` field of A-038, in two respects only — the step numbers and the definition of the excluded set. Its principle (the SRM denominator is the assignment population, fixed before any exclusion), its descriptive differential-exclusion check, and its reasoning stand unchanged.
- **Decision:** SRM n remains the count of raw rows carrying a valid coerced arm label, fixed before any other exclusion. Two corrections: the excluded set is rows whose `version` is **missing** (A-051), not "null or out-of-whitelist"; and the SRM test now runs at **§7.7 step 8**, not step 7, because the structural gate and coercion were separated into steps 5 and 6. The ordering guarantee is unchanged in substance — SRM still precedes the duplicate and missing-value handling at steps 10 and 11.
- **Alternatives rejected:** Leaving the step reference stale — a specification that cites a step number which now does something else is exactly the kind of drift that produced Defect 6. Renumbering the later steps to keep SRM at 7 — it would restale every other step reference in the document and in this file for no gain.
- **Reason:** The denominator rule is only true if the code runs in the stated order, so the entry that states the rule has to cite the order correctly.
- **Affects:** `ARCHITECTURE.md` §2.2 and §7.7; how the Part 3 session sequences the entrypoint.
- **Falsifiable by:** Not applicable — this is a correction, not a new call.

### A-053 — A-044's execution order revised: a single structural gate
- **Kind:** supersedes A-044
- **Part:** 3
- **Date:** 2026-09-10
- **Status:** active
- **Supersedes scope:** the `Decision` field of A-044, in respect of steps 5 to 9 and 11 only. Its three failure classes (hard stop / downgrade / finding), its 20-step shape, and its principle that ordering is part of the design stand unchanged.
- **Decision:** Restructure §7.7 steps 5 to 9 into: **5** structural validation of every value in all four columns against its token sets, the single point where a token value can stop the run; **6** coercion to three-state representations; **7** partition of unassignable rows with the 0.1% downgrade; **8** the SRM test; **9** the revised three-state assertion group. Relabel step 11 as the missing-value check and note that it is reachable. Add a third load-bearing ordering constraint — the structural gate precedes every statistic — and the invariant that every hard stop precedes step 19's output write, so a run that reaches step 19 has already established that the file is the file.
- **Alternatives rejected:** Validating each column at the point of first use — cheaper to write, but a structural fault in a retention column would surface after the SRM test, discarding a computed number and inviting the question of whether it was looked at first. Keeping validation and coercion in one step per column, as v1.1 had it — that is precisely the coupling that made a null fatal, because a single step cannot both raise on unrecognised values and admit missing ones without the two sets being enumerated separately first. Adding a twenty-first step for the gate — it is a replacement for work steps 5 and 8 already did, not an addition.
- **Reason:** Separating "is this the right file" from "what is missing from it" is what lets the first be fatal and the second be counted; keeping them in one operation forces both to behave the same way, which is how a document ends up specifying a policy its own execution order forbids.
- **Affects:** `ARCHITECTURE.md` §7.7 in full; §2.2's step references; §5.3's and §5.4's reachability claims; what the Part 3 session builds.
- **Falsifiable by:** A structural check that cannot be performed before coercion, which would force a second gate and a superseding entry.

---

## Part 3 implementation session — decisions taken before data access (2026-09-11)

Every entry in this pass was written and committed **before the CSV was fetched**, so
that each analysis-affecting choice demonstrably predates any data access. The pass
records the environment actually used, and the implementation calls that
`ARCHITECTURE.md` leaves under-specified. No `challenge` entry was warranted: nothing
in the document was found to be wrong, and nothing here deviates from it.

IDs are assigned in write order and are never reserved in advance.

### A-054 — Interpreter patch version and resolved direct dependency versions
- **Kind:** finding
- **Part:** project-wide
- **Date:** 2026-09-11
- **Status:** active
- **Decision:** Record that Part 3 was built and run on CPython **3.12.14** (`main`, built 2026-08-12, Clang 21.0.0), with direct dependencies resolved to `pandas==3.0.5`, `numpy==2.5.3`, `scipy==1.18.1`, `statsmodels==0.15.0` and `matplotlib==3.11.1`; the fully resolved transitive set is in `requirements.lock.txt`.
- **Alternatives rejected:** Not applicable — this is an observation. It was obtained by running `platform.python_version()` and `importlib.metadata.version()` inside the project virtual environment immediately after creating it, and by `pip freeze` for the lock file.
- **Reason:** A-026 requires the initialising session to record the exact patch version it used, because the patch is recorded for provenance rather than enforced; `.python-version` therefore carries the minor version `3.12` only, and a machine with a different 3.12 patch can still reproduce.
- **Affects:** The run manifest, the clean-checkout sequence, and the bit-identity claim for bootstrap interval endpoints, which is conditional on the `numpy` version recorded here.
- **Falsifiable by:** Not applicable — this is a record of what was used, not a claim about what must be used.

### A-055 — Python 3.12 is acquired through Homebrew, not through uv
- **Kind:** decision
- **Part:** project-wide
- **Date:** 2026-09-11
- **Status:** active
- **Decision:** Obtain the pinned interpreter with `brew install python@3.12` and create the project environment with that interpreter's own `python -m venv .venv`; name Homebrew in the README setup section as the route actually used, while noting that any source of a 3.12 interpreter works.
- **Alternatives rejected:** `uv python install 3.12` — uv was already present on the build machine and would have been faster and less invasive, but A-027 rejected uv precisely because it adds a tool a reviewer must install before they can reproduce anything, and §7.5's clean-checkout rule makes "create the environment at the pinned interpreter version" step one of the reproduction chain; acquiring the interpreter is therefore inside that chain, so the acquire-versus-manage distinction does not rescue it. Using the machine's existing 3.13.5 or 3.14.7 — §7.7 step 1 hard-stops on any interpreter minor other than 3.12, and A-026 forbids moving the minor without a superseding entry. Pinning the patch version in `.python-version` — A-026 rejected that, since it would fail on a machine carrying a different patch of the same minor for no analytical reason.
- **Reason:** The reproduction chain should assume as little as possible of the reviewer, and Homebrew is already the conventional macOS route for a versioned interpreter; choosing it keeps the whole chain expressible without introducing a second package tool alongside the venv-plus-pip toolchain A-027 settled on.
- **Affects:** The README setup section; the clean-checkout sequence; nothing in the analysis.
- **Falsifiable by:** A reviewer on a platform where Homebrew is unavailable, which changes the documented route but not the pin.

### A-056 — The Kaggle CLI is installed outside the project environment and appears in neither requirements file
- **Kind:** decision
- **Part:** 3
- **Date:** 2026-09-11
- **Status:** active
- **Decision:** Keep the Kaggle CLI out of `.venv`, out of `requirements.txt` and out of `requirements.lock.txt`; document the CLI fetch in the README as the canonical reproduction step per §5.5, and let a reproducer install that tool however they wish, outside the analysis environment.
- **Alternatives rejected:** Adding `kaggle` to `requirements.txt` with a new dependency entry — A-027 fixes the permitted Part 3 libraries as `pandas`, `numpy`, `scipy`, `statsmodels` and `matplotlib`, and a fetch tool does not belong in the environment that `requirements.lock.txt` certifies as the analysis environment; it would also make the lock file's transitive closure depend on an HTTP client stack that no analysis step imports. Vendoring a download script into `src/part3_experiment/` — the entrypoint would then have a network path inside it, and §7.7 step 2 is explicit that the run verifies an already-present file rather than fetching one.
- **Reason:** The lock file is a statement about what produced the numbers. A tool that never runs during the analysis, and whose absence cannot change a single reported figure, weakens that statement by being in it.
- **Affects:** `requirements.txt`, `requirements.lock.txt`, the README fetch step; nothing in the analysis.
- **Falsifiable by:** A future step that needs programmatic dataset access during the run itself, which would make the CLI an analysis dependency and require a superseding entry.

### A-057 — `run_part3.py` lives in `src/part3_experiment/`, not at the repository root
- **Kind:** decision
- **Part:** 3
- **Date:** 2026-09-11
- **Status:** active
- **Decision:** Place the entrypoint at `src/part3_experiment/run_part3.py` and have the root wrapper `run_part3.sh` invoke it as `python -m src.part3_experiment.run_part3`; create no `src/__init__.py`, leaving `src/` an implicit namespace package.
- **Alternatives rejected:** A root-level `run_part3.py`, which §7.2's phrasing ("plus a single entrypoint `run_part3.py`") could be read to suggest — §8's owned-path list is exhaustive ("It has these paths and no others"), does not include a root `run_part3.py`, and separately forbids "any module outside `src/part3_experiment/`", so a root entrypoint would be outside the session's ownership on two counts. Creating `src/__init__.py` to make `src` a regular package — that file is itself a module outside `src/part3_experiment/` and is forbidden by the same clause; implicit namespace packages make it unnecessary.
- **Reason:** §7.1's directory tree shows `run_part3.sh` at the root and Part 3's Python under `src/part3_experiment/`, and §8 is the binding statement of what this session may create. Where the two readings of §7.2 diverge, the ownership list governs, and it resolves the question without ambiguity.
- **Affects:** The invocation path in `run_part3.sh` and the README; where a reviewer looks for the twenty-step order.
- **Falsifiable by:** An amended §8 listing a root-level entrypoint among the owned paths.

### A-058 — Module set beyond the names illustrated in §7.2
- **Kind:** decision
- **Part:** 3
- **Date:** 2026-09-11
- **Status:** active
- **Decision:** Implement Part 3 as `config.py`, `run_state.py`, `load.py`, `checks.py`, `srm.py`, `power.py`, `bootstrap.py`, `inference.py`, `engagement.py`, `decision.py`, `report_tables.py`, `figures.py`, `manifest.py`, `verify.py` and the entrypoint `run_part3.py`, all in importable `snake_case` with no numeric prefixes, with execution order living solely in the entrypoint.
- **Alternatives rejected:** Restricting the set to exactly the six names §7.2 lists (`load`, `checks`, `inference`, `power`, `bootstrap`, `report_tables`) — §7.5 independently requires the single seed literal to live in one module that everything imports, which none of the six names describes, and folding the seed into `load.py` or `inference.py` would bury the one constant the reproducibility claim rests on. Putting the decision pipeline inside `inference.py` — §1.6's three-stage evaluation is the part of this project a reviewer will read most closely, and it deserves a file whose name says what it is. A single flat module containing all twenty steps — it would put execution order in two places, since the order would then be implicit in the file as well as explicit in the entrypoint.
- **Reason:** §7.2's binding rules are the naming style and the location of execution order, both of which hold here; the list of six names illustrates the style rather than enumerating a closed set, and §8 grants this session all of `src/part3_experiment/**`.
- **Affects:** The layout of `src/part3_experiment/`; which module a reviewer opens to check a given §7.7 step.
- **Falsifiable by:** An amended §7.2 stating the six names are exhaustive.

### A-059 — The raw CSV is read with pandas NA filtering disabled
- **Kind:** decision
- **Part:** 3
- **Date:** 2026-09-11
- **Status:** active
- **Decision:** Read the CSV with `dtype=str`, `na_filter=False` and `keep_default_na=False`, so that every field arrives at the §5.4 token sets as the exact text the file holds, and no value is converted before validation.
- **Alternatives rejected:** Reading with `dtype=str` alone, which §7.7 step 3's "every column as text, no dtype inference" might be read to permit — pandas still applies its default NA handling in that configuration, converting an empty field and the tokens `NA`, `N/A`, `NaN`, `nan`, `null`, `NULL` and `None` into float `NaN` **before** §5.4's sets ever see them. The missing-set comparison would then run against float objects that are not strings, so the three-state coercion would fail to match its own missing tokens, and the count-conservation assertion at step 9 would be checking a column the reader had already altered. Detecting the converted `NaN` values afterwards and mapping them back to the missing state — it cannot distinguish an empty field from the literal text `NaN`, so the per-spelling source-token counts §5.4 requires would be unrecoverable.
- **Reason:** This is the same class of silent bug as the truthiness coercion A-024 bans: a default conversion that produces a plausible-looking result while destroying the distinction the validation exists to check. §5.4's enumerated sets are only meaningful if they see the file's actual bytes, which requires the reader's own NA handling to be off.
- **Affects:** `load.py`; the reachability of §5.3 in practice; the step 9 count-conservation assertion; the per-spelling missing-token counts.
- **Falsifiable by:** Not applicable — no reading of §7.7 step 3 is served by letting the reader convert values before validation.

### A-060 — Closed containment is the boundary convention for "contains zero"
- **Kind:** decision
- **Part:** 3
- **Date:** 2026-09-11
- **Status:** active
- **Decision:** Treat an interval as containing zero when `lower <= 0 <= upper`, and as excluding zero otherwise, so that "contains zero" and "excludes zero" are exact complements wherever §1.6 uses them — in precondition R6 and in modifiers R7 through R10.
- **Alternatives rejected:** Open containment (`lower < 0 < upper`) — an endpoint of exactly zero would then count as excluding zero, which would let a guardrail interval touching zero trigger R8's downgrade or R7's no-op, and would make R10 and the set {R7, R8, R9} overlap rather than partition. Leaving the case unhandled — an endpoint of exactly 0.00 is reachable in a percentile bootstrap, whose endpoints are drawn from the empirical replicate distribution and can land on a value the statistic attains exactly.
- **Reason:** §1.6 fixes the analogous convention for the action threshold in the direction of inclusion — an endpoint of exactly ±1.00 pp counts as **within** the threshold — and applying the same direction to zero keeps the document's two boundary conventions consistent rather than opposed. It is also the conservative reading: an interval that merely touches zero has not established a sign.
- **Affects:** `decision.py`; whether R6 fires; which of R7 through R10 applies.
- **Falsifiable by:** An amendment to §1.6 fixing the opposite convention, which would be defensible but must be stated rather than inferred.

### A-061 — Stage 2 and Stage 3 are evaluated exhaustively under an arity assertion, and the two measure-zero gaps hard-stop
- **Kind:** decision
- **Part:** 3
- **Date:** 2026-09-11
- **Status:** active
- **Decision:** Evaluate all five Stage 2 conditions and all four Stage 3 conditions independently, collect the labels that fired, and assert that exactly one fired in each stage, hard-stopping otherwise; do **not** add a branch to cover either of the two states the §1.6 tables leave uncovered — `p₇ < 0.05` with `Δ₇` exactly zero, and `CI₁` excluding zero with `Δ₁` exactly zero — and disclose both in the report.
- **Alternatives rejected:** An `if`/`elif` chain taking the first match — it makes "exactly one branch fired" true by construction, so §7.7 step 20's assertion would verify nothing, and a genuine contradiction between the conditions would be silently absorbed by whichever branch came first. Adding a sixth branch or a fallback to cover the uncovered states — the recommendation for such a state is not pre-registered, so inventing one after reading §1.6 is precisely the after-the-fact rule-making this document exists to prevent, and it would be indistinguishable in the code from a rule that had been pre-registered. Widening R2 or R3 to take `Δ₇ >= 0` — it changes a pre-registered condition to close a gap that cannot occur.
- **Reason:** The first uncovered state is unreachable in fact, since the z statistic is `Δ / SE` and therefore `Δ = 0` implies `p = 1`; the second requires a percentile interval that excludes zero around a point estimate of exactly zero, which the interval's construction from the replicate distribution makes fantastically unlikely. An assertion that hard-stops is the honest response to a state the pre-registration does not cover: it fails loudly and visibly rather than quietly inventing an answer.
- **Affects:** `decision.py`; the meaning of §7.7 step 20's assertion; what happens in a state §1.6 does not describe.
- **Falsifiable by:** A run in which either assertion trips, which would mean the pre-registration has a genuine gap and needs an amendment rather than a patch.

### A-062 — Rules R4 and R5 are selected solely by `CI₇` against ±1.00 pp, with no power-based condition
- **Kind:** decision
- **Part:** 3
- **Date:** 2026-09-11
- **Status:** active
- **Decision:** Implement the R4 and R5 conditions exactly as §1.6 states them — R4 when `p₇ >= 0.05` and all of `CI₇` lies within ±1.00 pp, R5 when `p₇ >= 0.05` and `CI₇` extends beyond ±1.00 pp on either side — and implement no condition anywhere in the decision pipeline that reads the power calculation; compute and report §3's required comparison sentence between the 80%-power detectable effect and the 1.00 pp action threshold, and let it feed nothing.
- **Alternatives rejected:** Reading §3's sentence — that a sample able to detect effects smaller than the threshold makes a null result informative so "rule R4 becomes available", otherwise "rule R5 applies" — as a gate on branch selection. It would create a second, independent definition of R4 and R5 that can contradict §1.6's: a sample could be underpowered at 80% while still returning an interval entirely inside ±1.00 pp, and the two readings would then select different branches from the same result, with no stated rule for which governs. It would also make the branch depend on the observed control rate through the power calculation, which is a data-dependent input to a rule §1.6 defines purely on the interval.
- **Reason:** §1.6 is the mechanical authority for which rule fires and its table names only `p₇` and `CI₇`. §3's sentence is an interpretive claim about *why* a null result is or is not informative — it explains what R4 means, and the explanation happens to be sound, because an interval that fits inside ±1.00 pp is itself evidence the sample was sensitive enough to bound the effect. Reading commentary as a gate would put a second decision rule in the document without the reachability trace §1.6 supplies for the first.
- **Affects:** `decision.py`; `power.py`, whose output is reported but consumed by nothing; the §3 subsection of the report.
- **Falsifiable by:** An amendment moving the power condition into §1.6's rule table, where it would need its own boundary conventions and its own reachability trace.

### A-063 — The bootstrap resamples row indices within each arm, and independent streams are spawned from the one seed
- **Kind:** decision
- **Part:** 3
- **Date:** 2026-09-11
- **Status:** active
- **Decision:** Implement §4.2's stratified scheme literally — for each replicate, draw `n_arm` row indices with replacement from that arm's observed rows and take the mean of the resampled outcome vector — and derive the two metrics' independent streams with `numpy.random.default_rng(RANDOM_SEED).spawn(2)`, introducing no second seed literal anywhere in the repository.
- **Alternatives rejected:** Drawing each replicate's success count directly from `Binomial(n_arm, p̂_arm)` — this is not an approximation but an exact identity, since the number of successes in a with-replacement resample of size `n` from a 0/1 vector with `k` successes is distributed exactly `Binomial(n, k/n)`, and it would run in a fraction of the time; it was rejected because a reviewer checking that the bootstrap does what §4.2 describes should be able to see the resampling rather than have to verify a distributional argument first, and the runtime saved is worth less than that. Running both metrics off one generator sequentially — the D1 interval would then depend on the D7 bootstrap having run first and with exactly that many draws, so an unrelated change to the primary analysis would silently move the guardrail endpoints. Seeding a second generator with a derived literal such as `RANDOM_SEED + 1` — §7.5 names a second seed literal as a defect and prescribes spawning.
- **Reason:** §4.2 specifies a resampling scheme, and the most defensible implementation of a specified procedure is the one that looks like the specification. Spawning gives genuinely independent streams whose provenance is still the single seed, which is what makes the bit-identity claim checkable from one constant.
- **Affects:** `bootstrap.py`; both reported intervals and both Monte Carlo standard errors; the run manifest's seed record.
- **Falsifiable by:** Not applicable as a correctness matter — the two draw mechanisms have the same sampling distribution, so this is a choice about auditability rather than about the answer.

### A-064 — The step 2 checksum is read from `assumptions.md`, not duplicated in code
- **Kind:** decision
- **Part:** 3
- **Date:** 2026-09-11
- **Status:** active
- **Decision:** Have §7.7 step 2 parse the recorded SHA-256 out of the dataset-provenance `finding` entry in `assumptions.md` with an anchored pattern keyed to that entry's ID, and hard-stop if the value is absent, malformed, or matched more than once.
- **Alternatives rejected:** Copying the checksum into `config.py` as a constant — §7.7 step 2 says the file's hash is checked "against the value recorded in `assumptions.md`", and a second copy in code creates two sources of truth for the one value whose whole purpose is to be authoritative; if they ever drifted, the run would verify against the copy while a reader verified against the record. Passing the expected hash in as a command-line argument — it moves the authoritative value out of the repository entirely and makes the clean-checkout sequence depend on the operator typing it correctly. Reading the file's hash and merely printing it — that is not a check.
- **Reason:** `assumptions.md` is the provenance record a reader is directed to, and a verification step is only meaningful if it reads the same record the reader does. The parse is made strict, and failing loudly on an ambiguous or missing match keeps the brittleness of markdown parsing from degrading into a silently skipped check.
- **Affects:** `load.py`; the clean-checkout rule's "verify its SHA-256" step; what a reader must edit to point the run at a different revision of the dataset.
- **Falsifiable by:** A future need to run against several dataset revisions, which would justify a small structured provenance file that `assumptions.md` cites rather than an in-code constant.

### A-065 — Threshold denominators are fixed explicitly
- **Kind:** decision
- **Part:** 3
- **Date:** 2026-09-11
- **Status:** active
- **Decision:** Compute the unassignable-row threshold and the cross-arm duplicate threshold as a share of the **raw input row count**, and compute the primary-metric missing-value threshold as a share of **each arm's own assignment count** — the arm's share of the SRM denominator — firing the downgrade if either arm exceeds 0.5%.
- **Alternatives rejected:** Using the raw row count as the denominator for the missing-value threshold as well — §5.3 says "exceed 0.5% of either arm", which is a per-arm statement, and pooling the arms would let a concentrated regression in one arm hide beneath a combined rate roughly half its size. Using each arm's post-exclusion metric denominator — it is smaller than the assignment count by exactly the exclusions being measured, so the rate would be computed against a base the exclusions had already shrunk, which inflates it inconsistently. Using the assignment population for the 0.1% thresholds — §2.2 and §7.7 step 10 both say "of raw rows", and unassignable rows must be counted against a base that includes them, since they are the quantity being thresholded.
- **Reason:** Each threshold should be measured against the population whose failure it describes: a missing assignment is a failure over all raw rows, and a missing outcome is a failure within the arm it was assigned to.
- **Affects:** `checks.py`; which of the four downgrade sources can fire; the denominators reported in the data-quality table.
- **Falsifiable by:** Not applicable — these follow from the wording of §2.2, §5.2 and §5.3 rather than from a preference.

### A-066 — "Identical metric values" is defined for the same-arm duplicate case
- **Kind:** decision
- **Part:** 3
- **Date:** 2026-09-11
- **Status:** active
- **Decision:** For §5.2's same-arm duplicate branches, treat two rows sharing a `userid` as having identical metric values when their **coerced** `retention_1`, `retention_7` and `sum_gamerounds` all agree, counting two missing values in the same column as agreeing; any disagreement in any of the three makes the `userid` conflicting, which excludes it entirely from the metric analysis.
- **Alternatives rejected:** Comparing only the two retention flags and ignoring `sum_gamerounds` — two rows differing in rounds played are different observations of the player, and calling them an export artefact discards the evidence that they are not. Comparing the raw text rather than the coerced values — `True` and `1` are the same outcome under §5.4's token sets, and treating them as conflicting would exclude a user over a spelling difference. Treating two missing values as disagreeing — they carry the same information, and excluding a `userid` from a metric because both of its rows are equally silent about it adds nothing.
- **Reason:** §5.2's distinction is between a row duplicated by the export and a genuine conflict the data cannot resolve, and the operative question is whether the two rows say the same thing about the player. That question is asked of everything the rows record about the player, and it is asked after coercion, because coercion is what makes two spellings of one value comparable.
- **Affects:** `checks.py`; the duplicate counts reported by case; the per-metric denominators.
- **Falsifiable by:** Duplicates turning out not to exist, which makes the branch moot — recorded as a finding either way.

### A-067 — The extreme `sum_gamerounds` row is identified as the maximum, with ties handled explicitly
- **Kind:** decision
- **Part:** 3
- **Date:** 2026-09-11
- **Status:** active
- **Decision:** Identify §5.1's extreme row as the row holding the **maximum** `sum_gamerounds` value; if that maximum is held by more than one row, treat all tied rows as the excluded set for the "without" variant and report the tie and its count explicitly; disclose the value and its arm in every case.
- **Alternatives rejected:** Defining the outlier by a rule such as an interquartile-range fence or a z-score cutoff — that is a general outlier-detection policy, which §5.1 does not authorise and which could remove rows the document never contemplated; the section speaks of one specific known observation, not of a class. Hard-coding the expected value from the dataset's reputation — it would fail silently on a different revision of the file and would import an expectation this project has committed to establishing rather than assuming. Assuming the maximum is unique — an unreported tie would make the "without" figure exclude fewer rows than the reader thinks.
- **Reason:** §5.1 describes a single known extreme value and requires a both-ways presentation of it, so the implementation needs to locate exactly that observation without inventing an exclusion rule that could reach further. The maximum is the only definition that both finds it and cannot expand beyond it.
- **Affects:** `engagement.py`; the with-and-without `sum_gamerounds` figures; the disclosure §5.1 requires.
- **Falsifiable by:** The file containing several comparably extreme values rather than one, which would make "the extreme row" the wrong description and require an amendment to §5.1.

### A-068 — Engagement summaries are winsorised at the 99th percentile
- **Kind:** decision
- **Part:** 3
- **Date:** 2026-09-11
- **Status:** active
- **Decision:** Satisfy §5.1's requirement for "a stated winsorised or trimmed summary" with a mean winsorised at the **99th percentile of the pooled `sum_gamerounds` distribution**, applying that single pooled cap to both arms and reporting the cap value alongside the result.
- **Alternatives rejected:** Winsorising at each arm's own 99th percentile — the two arms would then be summarised under different caps, so the difference between the reported means would partly reflect the difference between the caps rather than the data. A 95th-percentile cap — it moves far more mass than is needed to address a single extreme observation and would obscure genuine heavy-tail behaviour that §5.1 wants visible. A trimmed mean instead — it discards the tail rather than bounding it, which reports a statistic about a subset of players while presenting it beside statistics about all of them.
- **Reason:** The summary exists so that no engagement claim rests on one row, and a pooled 99th-percentile cap achieves that while changing as little else as possible; stating the cap is what makes the figure interpretable rather than merely robust.
- **Affects:** `engagement.py`; the engagement table and the distribution figure; nothing in the retention analysis.
- **Falsifiable by:** Not applicable as a correctness matter — §5.1 permits a winsorised or a trimmed summary and requires only that the choice be stated.

### A-069 — Output tables carry both a full-precision value and a display-precision rendering
- **Kind:** decision
- **Part:** 3
- **Date:** 2026-09-11
- **Status:** active
- **Decision:** Give every numeric row in `outputs/tables/` both a `value` column at full precision, written with a fixed deterministic format, and a `value_display` column rendered at §4.1's reporting precision — two decimal places in percentage points for rates and effects, three significant figures for p-values — and require the report and README to quote the `value_display` string.
- **Alternatives rejected:** Storing only the rounded value — the decision rule compares a `CI₇` endpoint against 1.00 pp, and a rounded endpoint could cross that boundary in either direction, so the rule would be evaluated against a display artefact rather than the estimate. Storing only the full-precision value — §7.5 requires every number in prose to exist in a generated output file, and a figure rounded in the prose does not literally appear anywhere, so the check a reader would perform against the table would fail on the last digit. Rounding at write time and computing the decision from in-memory values — the committed table would then disagree with the computation it documents.
- **Reason:** The two requirements pull in opposite directions: the decision needs unrounded inputs and the reproducibility rule needs the printed figure to be findable in a file. Carrying both columns satisfies each without letting either corrupt the other.
- **Affects:** `report_tables.py`; every table under `outputs/tables/`; what the report and README are permitted to quote.
- **Falsifiable by:** Not applicable.

### A-070 — Step 20's hard stop occurs after outputs exist, and those outputs are never committed
- **Kind:** decision
- **Part:** 3
- **Date:** 2026-09-11
- **Status:** active
- **Decision:** Implement §7.7 step 20 as a raising hard stop whose exception states that the files on disk are the product of a failed run and must not be committed, and commit no output from any run whose step 20 did not pass.
- **Alternatives rejected:** Downgrading a step 20 failure to a warning so that the "no outputs are written" half of the hard-stop definition holds literally — a self-verification check that does not stop the run verifies nothing, and this is the step that asserts exactly one Stage 2 branch fired. Writing outputs to a staging directory and promoting them only after step 20 passes — it would satisfy the definition exactly, but it adds a path indirection to every write for a failure mode that is a bug rather than a data condition, and §7.7 step 19 names the final paths directly. Moving self-verification before the write — it cannot re-read written outputs, which is the substance of what step 20 does.
- **Reason:** §7.7's failure-class definition says a hard stop writes no outputs, and step 20 necessarily runs after step 19 has written them, so the definition cannot hold there on its own terms. The document scopes the invariant itself in the sentence that follows the step list — "steps 1–6 and the assertion group at step 9 are the only places the run can terminate **on the data**" — which makes step 20 a stop on the code's own consistency rather than on the input. The intent is unambiguous; only the label is imprecise, and the operational consequence is carried by the commit discipline recorded here.
- **Affects:** `verify.py`; `run_part3.sh`'s exit status; which runs produce committed artefacts.
- **Falsifiable by:** Not applicable — this records how an acknowledged imprecision in the failure-class label is resolved, not a choice between substantive alternatives.

### A-071 — Percentile endpoints are taken with linear interpolation between order statistics
- **Kind:** decision
- **Part:** 3
- **Date:** 2026-09-11
- **Status:** active
- **Decision:** Compute the 2.5% and 97.5% percentiles of the bootstrap replicate distribution with `numpy.percentile` under its default `linear` method, which interpolates between the two order statistics bracketing the requested rank, and state the method in the report.
- **Alternatives rejected:** The `lower` and `higher` methods, which snap each endpoint to an adjacent order statistic — they bias the interval systematically outward or inward by up to one replicate gap, and the direction of that bias differs between the two endpoints. The `nearest` method — it removes the bias but makes the endpoint a step function of the resample count, so an interval could shift discontinuously under a change §4.2 would treat as immaterial. Leaving the method to the library default without recording it — the default is what is being chosen here, and a reader checking an endpoint against the threshold is entitled to know how it was formed.
- **Reason:** With 10,000 replicates the requested ranks fall between order statistics rather than on them, so some convention is unavoidable; linear interpolation is the one that treats both tails symmetrically and varies smoothly with the resample count. The practical effect is bounded by the gap between adjacent replicates, on the order of a thousandth of a percentage point against a 1.00 pp threshold, but it is recorded rather than waved away because it is an input to the rule that selects the recommendation.
- **Affects:** `bootstrap.py`; both reported percentile intervals; the action-threshold comparison in rules R1, R2, R4 and R5.
- **Falsifiable by:** An endpoint landing close enough to ±1.00 pp that the interpolation method changes which rule fires, which would be reported explicitly as a knife-edge result rather than resolved silently.

---

## Part 3 implementation session — dataset provenance (2026-09-11)

### A-072 — Dataset provenance: slug, file name, row count and SHA-256 of the CSV as used
- **Kind:** finding
- **Part:** 3
- **Date:** 2026-09-11
- **Status:** active
- **Decision:** Record the input as Kaggle dataset slug `mursideyarkin/mobile-games-ab-testing-cookie-cats`, file name `cookie_cats.csv`, a row count of 90189 data rows, and SHA-256 `5ab54d761fbddcd50de7b88e4eaf7837cba4569474f50c043a4d17ee342c46bd`; the file is 2,707,297 bytes and its header line is `userid,version,sum_gamerounds,retention_1,retention_7`.
- **Alternatives rejected:** Not applicable — this is an observation. The SHA-256 was obtained with `shasum -a 256` on the file as placed in `data/raw/`. The row count was obtained two independent ways that were required to agree before it was recorded: a line-based count treating a final unterminated line as a record, and a quote-aware `csv.reader` count; both returned 90189. No value in any data row was read in the course of recording this entry.
- **Row count convention, stated explicitly:** the recorded figure is **data rows, excluding the header row**. This is the same quantity §7.7 step 4 records as the raw row count, so the provenance figure and the computed figure are directly comparable, and §7.7 step 20 asserts they are equal. Note that `wc -l` reports **90190** for this file, because it counts newline bytes and the file carries both a header line and a trailing newline; that figure is one greater than the data-row count and is not what this entry records. The distinction is written down because a silent one-row disagreement between the record and the analysis would send a reader hunting for an off-by-one in the wrong place.
- **Reason:** §5.5 keeps `data/raw/` git-ignored because redistributing a Kaggle dataset is not ours to grant, and records provenance here instead so that "reproduces exactly" is a claim a reader can check rather than take on trust. The entrypoint verifies this checksum at §7.7 step 2 before anything runs, reading the value from this entry rather than from a constant in code (A-064), so this file remains the single source of truth for it.
- **Affects:** §7.7 step 2's verification and therefore whether the run proceeds at all; the run manifest's input block; the README fetch step; the reproducibility claim in full.
- **Falsifiable by:** A different SHA-256 on a copy fetched from the same slug, which would mean the dataset was revised after this run and would make every number in the Part 3 report specific to the revision recorded here. That is precisely what this entry exists to detect.

### A-073 — The `userid` uniqueness assertion passed: no duplicates of any kind
- **Kind:** finding
- **Part:** 3
- **Date:** 2026-09-11
- **Status:** active
- **Decision:** Record that all 90189 `userid` values are distinct, so the duplicate count is zero in every one of §5.2's three cases — same arm with identical metric values, same arm with conflicting values, and across arms — and no row was dropped as an export artefact or excluded from any metric population on duplicate grounds.
- **Alternatives rejected:** Not applicable — this is an observation. It was obtained at §7.7 step 10 by comparing the count of distinct `userid` values against the number of assignable rows, and is recorded in `outputs/tables/part3_01_data_quality.csv` and in the findings table.
- **Reason:** A-022 asserts uniqueness rather than assuming it and states that the assertion passing is what would make its branches moot, to be recorded as a finding. This is that record. The cross-arm threshold of 0.1% was therefore never approached, and the cross-arm branch of rule R0 could not have fired.
- **Affects:** Confirms that the per-metric denominators equal the arm assignment counts exactly, with no duplicate-driven exclusions; closes the §5.2 branches for this dataset.
- **Falsifiable by:** A future revision of the dataset containing repeated identifiers, which would activate the classification logic that this run left unused.

### A-074 — No missing values anywhere, and no unassignable rows
- **Kind:** finding
- **Part:** 3
- **Date:** 2026-09-11
- **Status:** active
- **Decision:** Record that the file contains no value from the §5.4 missing set in any of the four validated columns: zero rows have a missing `version` and so the unassignable count is zero, zero rows have a missing `retention_1` or `retention_7` in either arm, and zero rows have a missing `sum_gamerounds`; differential missingness between arms is therefore exactly 0.00 pp on both retention metrics.
- **Alternatives rejected:** Not applicable — this is an observation. It was obtained at §7.7 steps 7, 11 and 17 after the three-state coercion at step 6, and the step 9 count-conservation assertions confirmed that the coerced state counts equal their pre-coercion source-token counts for every column.
- **Reason:** A-023 and A-050 state that no nulls being present is what would make the missing-value policy moot, to be recorded as a finding. This is that record. Consequently the 0.5% primary-metric threshold and the 0.1% unassignable threshold were never approached, neither could have fired rule R0, and every per-metric denominator equals its arm's assignment count: 44700 for `gate_30` and 45489 for `gate_40` on both metrics.
- **Affects:** The reported denominators, which are identical to the SRM arm counts; the differential-exclusion check, which is exactly even because there were no exclusions at all.
- **Falsifiable by:** A future revision of the dataset containing nulls, which would activate the per-metric exclusion path that this run left unused.

### A-075 — The SRM p-value is 0.00869: above the pre-registered failure threshold, below conventional alpha
- **Kind:** finding
- **Part:** 3
- **Date:** 2026-09-11
- **Status:** active
- **Decision:** Record that the assignment population splits 44700 `gate_30` against 45489 `gate_40` out of 90189, an excess of 789 rows in the variant arm and an observed control share of 0.495626 against the hypothesised 0.5; the two-sided exact binomial p-value is 0.00869223438909 and the 1-df chi-square goodness-of-fit statistic is 6.90240494961 with p = 0.00860798781084. Because 0.00869 is greater than the 0.001 failure threshold fixed in §2.3, SRM did **not** trip, rule R0 did **not** fire, and the recommendation is **not** withheld.
- **Alternatives rejected:** Not applicable — this is an observation. It was obtained at §7.7 step 8 on the assignment population, fixed before any exclusion, and is reported unconditionally per §2.2.
- **Reason:** Recorded as its own entry because this is the one number in the run where the pre-registration's threshold choice is load-bearing rather than incidental. The same p-value would be "significant" at the conventional 0.05 and would trip an alarm calibrated there. §2.3 fixed the threshold at 0.001 before any data was seen, on the stated grounds that SRM is a data-quality alarm on a nuisance parameter and is tuned for specificity, that the failure modes it exists to catch — a broken assignment service, a logging filter on one arm, a bot-traffic asymmetry — produce gross rather than marginal imbalance, and that a false alarm discards a valid experiment while a small missed imbalance shifts arm weights rather than within-arm rates. An imbalance of 0.44 percentage points off an even split is marginal by that standard. Had the threshold been chosen after seeing this p-value it would carry no weight at all, in either direction; it is recorded here so a reader can confirm the ordering from git rather than take it on trust.
- **Affects:** Whether rule R0 fires, and therefore whether a recommendation is issued at all. Also the §2.4 diagnostic subsection, which is not required here because the downgrade did not trigger, and the §2.1 conditional statement about weighted designs, which is required in the report regardless of this outcome.
- **Falsifiable by:** Documentation of the experiment's true design ratio. If the original allocation was weighted rather than 1:1, this p-value tests the wrong null and is uninterpretable — which is precisely the permanent unknown recorded in A-008 and A-046, and why §2.1 requires the conditional statement to be printed whether or not the test trips.

---

## Amendment pass — `ARCHITECTURE.md` v1.3 (2026-09-11)


**ID collision repaired.** This block was first appended as A-054 through A-060 and
renumbered to A-076 through A-082 on discovery that the Part 3 implementation
session had already taken A-054 through A-075. The convention that prevents a repeat
is A-083.

Part 3 is complete and committed; its pre-registration froze at v1.2, commit
`c6d72f83`. These entries specify the Parts 1 and 2 **recon pass** and nothing else.
Nothing here is superseded, because v1.3 adds specification where there was none
rather than correcting anything. No entry below defines a Part 1 or Part 2 metric,
cohort, funnel step or day boundary — that is the point of A-076's gate.

### A-076 — A dedicated recon session owns the recon pass
- **Kind:** decision
- **Part:** project-wide
- **Date:** 2026-09-11
- **Status:** active
- **Decision:** Assign the GA4 recon pass to a **dedicated recon session**, separate from the completed Part 3 session and from the future Part 1 and Part 2 build sessions, with the path list in `ARCHITECTURE.md` §8: it owns `sql/00_recon_*` through `sql/09_recon_*`, `src/recon/**`, `outputs/tables/recon_*.csv`, `reports/recon_ga4_sample.md`, a `## Dataset recon` README section, append-only access to `requirements*.txt` and `.gitignore`, and — uniquely — BigQuery access configuration under user application-default credentials with no credential file ever committed; and it is forbidden every Part 3 path, every `sql/` range outside `00`–`09`, every Part 1 and Part 2 path, and `ARCHITECTURE.md` itself. The gate is a content prohibition as well as a path one: **no metric definition, cohort definition, funnel step, day boundary or retention window**, in SQL, Python, prose, comments, drafts or "suggested" sections.
- **Alternatives rejected:** Giving recon to the Part 1 build session — it would mean a session that has just seen the shard ranges, null rates and event volumes is then asked to write the metric definitions, which is choosing definitions with the answers in front of it; separating the two makes the handover through the architecture session structural instead of a matter of discipline, for the same reason A-034 keeps `ARCHITECTURE.md` read-only to implementation sessions. Extending the Part 3 session — it is complete, committed, and cites a frozen pre-registration, and A-034 forbids it BigQuery access for a reason that has not changed. Leaving the owner unstated, as v1.0 through v1.2 did — the step gating two-thirds of the project was assigned to nobody, which is how a project stalls without anyone noticing which rule was the blocker. Letting the architecture session run the queries itself — it would then be both the party that establishes the facts and the party that writes the specification from them, which is the separation this whole document exists to maintain.
- **Reason:** The recon's value is that it produces facts nobody chose. That only survives if the session producing them cannot also use them, and path lists plus a content gate are what make "cannot" different from "should not".
- **Affects:** `ARCHITECTURE.md` §8 and §10.1; who may hold BigQuery credentials; the handover sequence in §10.4; the point at which Part 1 and Part 2 build sessions can be briefed at all.
- **Falsifiable by:** A recon item that cannot be answered without writing a candidate metric definition to test it — which would be a genuine conflict, and goes to the architecture session as a `challenge` rather than being resolved locally.

### A-077 — Recon SQL is committed, in a new `00`–`09` range
- **Kind:** decision
- **Part:** project-wide
- **Date:** 2026-09-11
- **Status:** active
- **Decision:** Commit the recon queries, and reserve `sql/00`–`sql/09` for them in §7.2, narrowing Part 1's range from `01`–`29` to `10`–`29` to make room.
- **Alternatives rejected:** Filing recon under the existing `90`–`99` QA range — QA queries validate build queries written against a specification, while recon establishes the facts a specification does not yet have; a directory listing should distinguish "this checked a query" from "this is why the spec says what it says". Placing recon in the shared `60`–`89` block — the numbering encodes execution order and recon runs before everything, so a number above the build ranges would misstate the order. Leaving recon uncommitted or in a scratch directory — the findings become the factual basis for two-thirds of the project's specification, and a fact whose query nobody can read is an assertion. Keeping Part 1 at `01`–`29` and starting recon at a letter or a `0x` prefix — inconsistent with a two-digit ordinal scheme for no gain.
- **Reason:** Renumbering Part 1 costs nothing today because no Part 1 SQL exists, and it buys a numbering in which reading the directory top to bottom is reading the project's actual order. The ten-slot ceiling is also a feature: recon is meant to be a handful of broad queries, so needing more than ten is a signal to re-scope rather than a limit to work around.
- **Affects:** §7.2's reserved ranges; §8's recon path list; A-030's range table as amended.
- **Falsifiable by:** A recon that genuinely needs more than ten queries, which per the reasoning above is evidence the pass is no longer cheap and bounded and should be re-scoped by the architecture session.

### A-078 — Recon byte budget: 50 GiB per query, 200 GiB total, dry run mandatory
- **Kind:** decision
- **Part:** project-wide
- **Date:** 2026-09-11
- **Status:** active — `Decision` field superseded by A-085
- **Decision:** Cap recon at **50 GiB** estimated bytes processed per query and **200 GiB** across the whole pass; dry-run every query and record the estimate before executing it; run a query only if the estimate is within the per-query ceiling and the remaining total; take the shard inventory from table metadata rather than a row scan; restrict the shard range and select only needed columns in every query; narrow and re-dry-run any query over ceiling and, if it still exceeds, record the item as **unanswered** with its reason and estimate and escalate to the architecture session; stop the pass entirely if the remaining total falls below 50 GiB. Raising a ceiling, enabling billing, and executing a query whose estimate was never taken are forbidden.
- **Alternatives rejected:** No ceiling, relying on the sandbox's own 1 TiB monthly limit as the backstop — the limit would then be hit by the build queries or a re-run rather than by the mistake that caused it, and §7.5's zero-cost re-runnability would fail silently. A single total ceiling with no per-query cap — one runaway query could consume the whole budget before anything was learned. A tighter total, such as 50 GiB — it would bite on legitimate questions and invite working around the rule. Estimating cost from table sizes instead of dry runs — dry run is exact and free, so an estimate is strictly worse. Enabling billing to remove the constraint — it defeats the point of a project that reproduces at zero cost from a clean checkout.
- **Reason:** 200 GiB is a fifth of the monthly allowance, leaving the rest for the Part 1 and Part 2 build queries plus at least one full re-run. Both ceilings are deliberately loose for a schema-and-counts pass, which is the design: a query that trips one is almost certainly wrong — an unfiltered shard range, a nested `SELECT *`, an accidental cross join — rather than legitimately expensive. A ceiling that only fires on mistakes is one nobody is tempted to argue with.
- **Affects:** §10.1; recon item 12; every recon query; whether a materialised extract becomes necessary.
- **Falsifiable by:** A dry-run estimate showing that an item essential to specifying Part 1 cannot be answered within 50 GiB, which goes to the architecture session as a re-scope decision rather than a ceiling increase.

### A-079 — Recon outputs: three artifacts, with numbers and interpretation split
- **Kind:** decision
- **Part:** project-wide
- **Date:** 2026-09-11
- **Status:** active
- **Decision:** Produce all three artifacts — committed `outputs/tables/recon_*.csv` result files, a `reports/recon_ga4_sample.md` checklist rendering with a verdict and dry-run estimate per item, and one `assumptions.md` `finding` entry per item a later decision rests on — with explicit precedence: **the CSVs are the source of truth for every number**, the `finding` entries are the source of truth for the **interpretation** of those numbers, and the report is a rendering of both. Where the report or a finding disagrees with a CSV, the CSV wins and the discrepancy is a defect.
- **Alternatives rejected:** `assumptions.md` findings alone — the file is append-only prose that cannot be regenerated, so making it the authority for a figure a re-run could change would guarantee a stale number nobody can correct. Committed CSVs alone — they carry no judgement about what a number means for the specification, and that judgement is exactly what the append-only record exists to hold. A single results file with the interpretation inline — it collapses a regenerated artefact and a permanent one into a format that can only be one or the other. Leaving precedence unstated — three artifacts with no ordering is three chances to quote whichever is most convenient.
- **Reason:** The number and what it implies have different lifecycles: one is regenerated by a re-run, the other is a decision that must survive being wrong. Keeping them in different files with a stated winner is what makes both trustworthy, and it follows §7.5's existing rule that every number in prose exists in a generated file.
- **Affects:** §10.1; §10.4's handover; what the architecture session reads to write the Part 1 and Part 2 sections.
- **Falsifiable by:** Not applicable — precedence is a convention, and this one is chosen to match the files' regenerability.

### A-080 — BigQuery-derived outputs carry provenance instead of byte-identity
- **Kind:** decision
- **Part:** project-wide
- **Date:** 2026-09-11
- **Status:** active — `Decision` field superseded by A-086
- **Decision:** Exempt recon result files — and, provisionally, later Part 1 and Part 2 result files — from §7.5's cross-machine byte-identity rule, requiring instead a **provenance line** on each: shard range covered, query job date, dry-run byte estimate, and row count. §7.5's rule stays fully in force for Part 3, whose input is a local CSV verified by checksum. Recorded as the stated default for §9's **open question 7**.
- **Alternatives rejected:** Claiming byte-identity for BigQuery-derived outputs — the source is an external table that no checksum covers, so the claim would be unverifiable at best and falsified by any upstream change at worst; A-043 already established that a reproducibility claim is only worth making if it survives being tested. Materialising a fixed extract table and checksumming it, restoring the strong rule — a real option, genuinely better for reproducibility, but it costs bytes against A-078's budget and interacts with recon item 12, so deciding it before the byte figures exist would be the guesswork this document keeps refusing to do. Dropping reproducibility claims for Parts 1 and 2 altogether — the provenance line is cheap and gives a reader enough to tell whether their re-run saw the same data.
- **Reason:** The honest guarantee differs by input: a checksummed local file supports byte-identity, an external table supports provenance. Stating which applies where is better than one rule that is true in half the repository.
- **Affects:** §7.5's scope; §9 question 7; §10.1's provenance requirement; the shape of the eventual Part 1 and Part 2 output contract.
- **Falsifiable by:** Item 12 showing a materialised extract is affordable, which would allow the stronger rule to be restored for Parts 1 and 2 by a superseding entry.

### A-081 — Part 2's scope is decided by rule: 1,000 revenue events and 0.5% of users
- **Kind:** decision
- **Part:** 2
- **Date:** 2026-09-11
- **Status:** active — `Decision` field superseded by A-084 in respect of the user-coverage denominator
- **Decision:** Define "revenue is populated" as **both** at least **1,000** revenue-positive purchase events **and** at least **0.5%** of users with at least one such event, measured over the full shard range from recon item 1, counting only non-null strictly-positive revenue values on purchase-shaped events and explicitly excluding `spend_virtual_currency`. Both thresholds met → Part 2 is specified as funnel and monetization. Either missed → Part 2 is re-scoped to a progression funnel only, may not be titled, introduced or summarised as monetization anywhere including the README, and must state that the sample does not support revenue analysis with the observed counts given. Evaluated **once**, from item 9's committed result file, before any Part 2 section is written; whichever side fires, the observed counts and both thresholds are printed.
- **Alternatives rejected:** v1.0's prose version — "if revenue is unpopulated the part must be re-scoped" is the right call but not a rule, so the scope of Part 2 could be chosen after seeing which version of it looked better, which is the §1.6 failure mode in a new section. A single event-count threshold — 1,000 events concentrated in twenty users is volume without coverage, and any monetization metric built on it is a description of a handful of people. A single user-coverage threshold — 0.5% of a tiny base is coverage without volume, and the cells are too small to compare. An OR between them — it lets each failure mode pass by borrowing the other's strength. Counting `spend_virtual_currency` toward the thresholds — it is a soft-currency sink, not revenue, and including it is precisely how an unmonetized sample comes to look monetized. Deciding the scope after the query and justifying it afterwards — the thing this rule exists to prevent.
- **Reason:** Below about a thousand revenue events, conversion by cohort, ARPPU and revenue per install all have cells where a single heavy spender or one unusual day dominates, so presenting them is presenting noise; and casual mobile titles convert in the low single digits of percent, so under one payer in 200 means the sample is truncated, obfuscated or unrepresentative. Both numbers are low enough that a genuinely populated sample clears them without effort, which is what makes the rule safe to fix in advance.
- **Affects:** Part 2's entire scope and title; recon item 9's artefact; what the eventual Part 2 section may claim.
- **Falsifiable by:** Item 9 returning counts straddling the thresholds in a way that reveals a third case worth naming — which must be raised as a `challenge` before the counts are read as a verdict, not after.

### A-082 — Recon items are executable: question, artefact, problematic answer
- **Kind:** decision
- **Part:** project-wide
- **Date:** 2026-09-11
- **Status:** active
- **Decision:** Restate §10's twelve questions as a thirteen-item checklist in which every item names its **question**, the exact **artefact** that answers it (a count, a min/max, a distinct list, a null rate), and what a **problematic answer** would be, resolving in the findings document to *answered*, *problematic* or *unanswered*. Item 10 establishes the event vocabulary **empirically** — the full distinct list with volumes — and treats the reported names (`level_start_quickplay`, `level_complete_quickplay`, `spend_virtual_currency`, `in_app_purchase`, and no tutorial event) as an input to verify rather than build on; if that holds, the funnel sketched as first_open → tutorial → first purchase has no referent for its middle step and is **abandoned rather than approximated**, with the real funnel defined by the architecture session from what item 10 finds. **Item 13 added**: the dataset is documented as obfuscated with placeholder and null values, so per-field null rates and distinct-value profiles are established for every field Parts 1 and 2 would rely on, and **every segmentation requirement — segment-by-country included — is contingent on it**; a field whose distinct set is a single value, is dominated by a placeholder, or is more than 50% null cannot support segmentation, such a segment is dropped rather than reported, and if no field survives, Parts 1 and 2 are specified without segmentation and say so.
- **Alternatives rejected:** Keeping the twelve as prose questions — an item a reader cannot tell has been answered is not a recon item, and a list of questions with no named artefact gets marked done by a session that read the schema and formed an impression. Trusting the reported event names and specifying the funnel now — they are second-hand, this pass is explicitly barred from writing funnel steps, and a funnel pre-registered against names that turn out not to exist is the failure §10's opening paragraph warns about. Approximating the sketched tutorial step with the nearest available event — it would preserve a funnel shape chosen before the schema was known, which is the wrong thing to preserve. Leaving obfuscation to be discovered during the build — a segmentation promised in a specification and then quietly dropped in the report is worse than one never promised.
- **Reason:** A checklist is only a gate if each item has a pass condition someone else can check. Naming the artefact converts twelve topics into thirteen answerable questions, and naming the problematic answer in advance means a bad finding is recognised as one rather than absorbed.
- **Affects:** §10.2 in full; §10.3's input (item 9); §10.4's handover, which requires every item resolved; the eventual Part 1 and Part 2 sections, including whether they may promise any segmentation at all.
- **Falsifiable by:** An item whose artefact turns out not to answer its question — which is recorded as *unanswered* with the reason and escalated, rather than marked answered on a near miss.

### A-083 — Entry IDs are allocated by re-reading the file immediately before appending
- **Kind:** decision
- **Part:** project-wide
- **Date:** 2026-09-11
- **Status:** active
- **Decision:** Before appending to this file, a session must re-read it and allocate IDs starting one above the highest `### A-NNN` heading present at that moment — not from whatever the highest ID was when the session last looked. If a collision is discovered after the fact, repair it by **renumbering the later append**, never by editing the earlier entries, and record the renumber in the later block. IDs are still never reused.
- **Alternatives rejected:** Reserving per-session ID blocks in advance — it wastes IDs, and a session that overruns its block has no defined next move. Timestamp-based or session-prefixed IDs — they would break every `A-NNN` cross-reference already written in `ARCHITECTURE.md` and in this file. Trusting the highest ID a session saw when it started — precisely what failed here: this amendment pass was drafted against a file ending at A-053 while the Part 3 implementation session had since appended A-054 through A-075, so the append duplicated seven IDs. Editing the earlier entries to move out of the way — forbidden by the append-only rule, and the earlier entries are the ones already cited elsewhere.
- **Reason:** Append-only plus multiple independent sessions means the file's tail is the only ID registry there is, and a session's memory of it goes stale the moment another session writes. Re-reading is the cheapest possible guard, and renumbering the newer block is the only repair that leaves existing cross-references intact.
- **Affects:** Every future append by any session; extends the A-047 bookkeeping conventions.
- **Falsifiable by:** Two sessions appending concurrently, which this convention cannot prevent — it makes the collision detectable and repairable rather than impossible.

---

## Amendment pass — `ARCHITECTURE.md` v1.4 (2026-09-11)

Two defects in §10, neither touching §1–§6. IDs allocated by re-reading this file
immediately before appending, per A-083: the highest heading present was A-083.

### A-084 — The user-coverage denominator is all distinct `user_pseudo_id` values with any event in the shard range
- **Kind:** supersedes A-081
- **Part:** 2
- **Date:** 2026-09-11
- **Status:** active
- **Supersedes scope:** the `Decision` field of A-081, in respect of the user-coverage threshold's denominator only. Its thresholds (1,000 events and 0.5%), its both-not-either requirement, its exclusion of `spend_virtual_currency`, its evaluate-once rule and its consequences on each side all stand unchanged.
- **Decision:** Define the denominator of the 0.5% user-coverage threshold as the count of **distinct `user_pseudo_id` values with at least one event of any kind in the full shard range established by recon item 1**, with users who have events but no `first_open` **included**, and no trailing-window exclusion. The numerator uses the same identifier over the same shard range. The denominator is fixed by `ARCHITECTURE.md` §10.3 and is **not re-selected** after item 2, item 4 or item 13 reports; a denominator shown to be unusable is a `challenge` raised before the counts are read as a verdict.
- **Alternatives rejected:** Users with at least one `first_open` (installers only) — it is the natural denominator for a cohort metric but the wrong one here, because it inflates the payer share by exactly the size of the gap item 2 measures, and a scope gate must never be easy in that direction; it is also internally inconsistent, since a purchase by a user with no `first_open` would count in the numerator while that user was excluded from the denominator. Users whose `first_open` falls early enough to allow a full observation window — defensible for a conversion metric, rejected because this is a sample-adequacy count over the whole extract rather than a cohort metric, and the exclusion would shrink the denominator and make the bar easier. Distinct `user_id` — its null rate is unknown until item 4, so the rule would rest on a fact the recon has not returned, and where `user_id` is sparse the denominator would silently shrink. Leaving "users" undefined, as A-081 did — recon will return at least two defensible counts, so the choice would be made with the numbers visible, which is precisely what §10.3 opens by saying it exists to prevent.
- **Reason:** The threshold is a sample-adequacy gate, so it should be computable from one unambiguous artefact and independent of every definition the recon has not settled — items 2, 3, 4 and 5 are all still open, and a gate must not depend on them. `user_pseudo_id` is the identifier a GA4 export always carries, so the denominator exists whatever item 4 finds; and where it over-counts people, one person on two devices counting twice, it over-counts in the direction that makes the bar harder. Every choice in this entry resolves the same way for that reason. This is the same correction §2.2 received in v1.2: name the population literally, in advance, so the count cannot be chosen after the fact.
- **Affects:** §10.3 in full; recon item 9's artefact, which must report both figures on this basis; Part 2's scope, and therefore its title and its claims.
- **Falsifiable by:** Item 13 showing `user_pseudo_id` obfuscated to a placeholder or a near-constant, which would leave the rule with no usable denominator — raised as a `challenge` before item 9's counts are read, and resolved by the architecture session rather than by substituting another population.

### A-085 — The recon byte budget is tracked in actual bytes billed, with a halt rule on divergence
- **Kind:** supersedes A-078
- **Part:** project-wide
- **Date:** 2026-09-11
- **Status:** active
- **Supersedes scope:** the `Decision` field of A-078. Both ceilings are unchanged at 50 GiB per query and 200 GiB total, as is the mandatory pre-flight dry run, the metadata-only shard inventory, the narrow-or-record-unanswered rule, and the prohibition on raising a ceiling or enabling billing. What changes is which quantity the running total is kept in, plus the halt rule.
- **Decision:** Keep the pre-flight gate exactly as it was — the estimate is the only number available before execution, so it authorises the query and is used for nothing else. After each query executes, read the **actual bytes billed** and bytes processed from the job statistics, record them in the recon results file beside the estimate together with the divergence as both an absolute figure and a ratio, and accumulate the **actuals** into the running total. Every divergence is a finding, in both directions, on every query. **Halt the pass** if a single query's billed bytes exceed its estimate by more than **2×** *and* by more than **10 GiB** absolute — both conditions required — or if a single query's billed bytes exceed the **50 GiB** per-query ceiling whatever it was estimated at. An under-billing divergence never halts. Stop the pass if the remaining total in actuals falls below 50 GiB.
- **Alternatives rejected:** Tracking estimates only, as A-078 did — the sandbox allowance is consumed by bytes billed, and the two quantities are not the same: BigQuery bills a minimum per table referenced regardless of estimate, which for a wildcard query touching many shards can dominate a cheap query outright, and for `_TABLE_SUFFIX`-filtered wildcards the predicted and billed bytes diverge depending on how shard pruning resolves. A pass could believe it had spent 180 GiB while the account recorded materially more or materially less, and in the first case the overrun would be discovered by the build queries failing. Recording actuals but keeping the total in estimates — it would put the real number in the file and then not use it, which is worse than not measuring. A ratio-only halt trigger — the per-table minimum makes a small query routinely exceed its estimate by a large multiple, so a ratio alone would halt the pass on a query that cost nothing. An absolute-only trigger — it would miss a systematic planning failure on small queries that predicts a large one. Treating a big divergence as a finding and continuing — see the reason below. Raising a ceiling to absorb an overrun — already forbidden by A-078 and still forbidden.
- **Reason:** The pre-flight gate is the only cost control the pass has and it is estimate-based, so once an estimate is demonstrably not predictive at that magnitude, every subsequent gate decision is unreliable and continuing means spending an unknown amount on the strength of a number known to be wrong. Halting costs almost nothing — recon is at most ten queries — and the recovery is to record what the divergence implies about the planner and let the architecture session either re-scope the remaining items or re-specify the queries against an explicit shard list so their cost becomes predictable. Under-billing gets recorded rather than halted because it costs nothing and is good news, but it is not merely good news: it means an estimate-based cost model overstates the Part 1 and Part 2 build cost and could force a materialised extract that is not actually needed, which is item 12's conclusion changing.
- **Affects:** §10.1's budget rule; §10.2 item 12's artefact and cost model; the recon results file's columns; the provenance line (A-086); the input to §9's open question 7.
- **Falsifiable by:** Job statistics not exposing billed bytes for a query the pass must run, which would leave the total untrackable in actuals and require a superseding decision rather than a silent fallback to estimates.

### A-086 — The provenance line carries both byte figures
- **Kind:** supersedes A-080
- **Part:** project-wide
- **Date:** 2026-09-11
- **Status:** active
- **Supersedes scope:** the `Decision` field of A-080, in respect of the provenance line's contents only. Its exemption of BigQuery-derived outputs from §7.5's cross-machine byte-identity rule, and its reservation of that question as §9's open question 7, both stand unchanged.
- **Decision:** The provenance line on each recon result file carries shard range covered, query job date, **dry-run estimate**, **actual bytes billed**, and row count. Both byte figures, not one.
- **Alternatives rejected:** The estimate alone, as A-080 specified — it records what authorised the query but not what it cost, so a reader cannot check that the budget was tracked as A-085 requires. The billed figure alone — it records the cost but hides whether the gate that authorised the query was accurate, which is the divergence item 12 needs. Putting the pair only in the results file and not on the provenance line — the provenance line is what travels with an output whose source cannot be checksummed, so it is where a reader looks to reconstruct what produced the file.
- **Reason:** Two numbers answer two different questions — what was permitted and what was spent — and the gap between them is itself a finding under A-085. A provenance line carrying one of them makes the other unverifiable from the artefact.
- **Affects:** §10.1's provenance requirement; every recon result file; what a reader can verify without re-running a query.
- **Falsifiable by:** Not applicable — this is an addition to a record, with no downside beyond one field.
