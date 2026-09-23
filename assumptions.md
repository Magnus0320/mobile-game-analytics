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
- **Status:** active — `Decision` field superseded by A-176
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
- **Status:** active — `Decision` field superseded by A-127
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
- **Status:** active — `Decision` field superseded by A-129
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
- **Status:** active — `Decision` field superseded by A-126
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

---

## Parts 1 and 2 recon session (2026-09-12)

The recon pass ARCHITECTURE.md §10.1–§10.4 specifies. IDs allocated by re-reading
this file immediately before appending, per A-083: the highest heading present was
A-086.

This session establishes facts and stops (§10.4). No entry below defines a Part 1
or Part 2 metric, cohort, funnel step, day boundary or retention window, and
several entries exist specifically to record where an item was executed in a way
that avoids making such a definition.

The eight decisions come first, then one challenge, then one finding per
checklist item.

### A-087 — Recon executes through the `bq` CLI; no Python client, and neither requirements file is touched
- **Kind:** decision
- **Part:** project-wide
- **Date:** 2026-09-12
- **Status:** active
- **Decision:** Run every recon query through the `bq` command-line tool shipped with the Google Cloud SDK — `bq query --dry_run` for §10.1's pre-flight estimate, `bq query --format=csv` for results, and `bq show -j --format=prettyjson` for actual bytes billed — and add **no** BigQuery Python client, leaving `.venv/`, `requirements.txt` and `requirements.lock.txt` byte-for-byte unmodified.
- **Alternatives rejected:** Installing `google-cloud-bigquery` into the existing `.venv` under a `-c requirements.lock.txt` constraint and appending the new pins to both requirements files, which is what §8's append-only permission appears to license — rejected because that permission was written for the Part 1 and Part 2 **build** sessions, which will need a client for work that produces analysis, and reading it as licence to alter the environment Part 3's lock file describes would mean a completed, committed and published part no longer reproduces from its own recorded environment, which §7.5's clean-checkout guarantee forbids. A separate `.venv-recon` — it leaves Part 3 untouched but makes both requirements files describe an environment that matches neither venv, and it needs a `.gitignore` line for a directory that exists only to avoid a decision. Writing the runner in Python against the REST API directly — more code, no dependency saved, and `bq` already exposes exactly the two job-statistics fields A-085 requires.
- **Reason:** A schema-and-counts pass needs a query client and nothing else, and `bq` is one. The reproducibility claim attached to a finished part is worth more than the convenience of a familiar library, and the cheapest way to keep that claim true is to not touch the environment it rests on.
- **Affects:** `src/recon/**`, which is shell rather than Python; the README's `## Dataset recon` section; the tooling the Part 1 and Part 2 build sessions inherit, which is **not** constrained by this entry.
- **Falsifiable by:** A checklist item that cannot be answered through `bq`. None was encountered; every one of the thirteen items was reachable with it. Had one not been, §8 requires a `challenge` entry naming the item rather than an install made on this session's own authority.

### A-088 — Authentication is user credentials in two forms, and the pass ran on the CLI account
- **Kind:** decision
- **Part:** project-wide
- **Date:** 2026-09-12
- **Status:** active — `Decision` field superseded by A-110 in respect of the authentication command sequence only
- **Decision:** Authenticate with `gcloud auth login` **and** `gcloud auth application-default login`, both run by the project author in their own terminal, and record plainly that `bq` authenticates against the **gcloud CLI account** rather than against application-default credentials, so the CLI account is the credential this pass actually used; the destination project id is supplied only through the `GOOGLE_CLOUD_PROJECT` environment variable and appears in no committed file.
- **Alternatives rejected:** Running only `gcloud auth application-default login`, which is what §8 and A-076 name — rejected because `bq` does not read ADC and would have failed with no credentialed account, so the literal instruction alone does not produce a working pass. A service-account key — forbidden outright by §8 and by A-076, and there is no circumstance in this project where one is acceptable. Hardcoding the project id in a query or a module — forbidden by §8. Having this session perform the OAuth flow — it is a browser consent the credential's owner must give, and a session that completes it is a session handling the user's credential.
- **Reason:** §8's two absolute rules are that authentication is by user credentials and that no credential file of any kind enters the repository. Both hold here: the credential is a user account, it lives in `~/.config/gcloud` outside the repository, and nothing was written into the tree. Recording which of the two credentials `bq` actually used matters because claiming the pass ran on ADC when it ran on the CLI account would be a false provenance statement about the one thing §8 regulates most tightly.
- **Affects:** §8's recon permissions; the README setup section; what a reader must reproduce to re-run the pass.
- **Falsifiable by:** A future `bq` release that reads application-default credentials directly, which would make the second command sufficient on its own and this entry's distinction historical.

### A-089 — The query cache is disabled on every recon query
- **Kind:** decision
- **Part:** project-wide
- **Date:** 2026-09-12
- **Status:** active
- **Decision:** Pass `--nouse_cache` on every recon query, so each execution performs a real scan and reports genuine job statistics.
- **Alternatives rejected:** Leaving the cache on, which is `bq`'s default — a cache hit bills zero bytes, so the running total A-085 requires in actuals would silently understate what the pass cost, every divergence figure item 12 needs would be meaningless on a cached query, and the per-day unit cost item 12 asks for would be fictitious the moment the query was re-run. Disabling it only for the unit-cost query — it would make one query's figures honest and leave the ledger's other rows depending on whether a given query happened to hit cache, which is a property of execution history rather than of the query.
- **Reason:** §10.1 makes the running total a record of what was actually spent, and item 12 makes the estimate-to-billed relationship an artefact in its own right. A cached zero is a true statement about one execution and a false basis for both. Paying the bytes twice costs a rounding error against a 200 GiB ceiling; a corrupted cost model would mislead the decision about whether Parts 1 and 2 need a materialised extract.
- **Affects:** Every row of `outputs/tables/recon_budget_ledger.csv`; item 12's cost model; the per-query divergence figures.
- **Falsifiable by:** Not applicable — the alternative produces numbers that cannot support the item they exist for.

### A-090 — Items 9 and 11 are computed over every event name, not over a selected candidate set
- **Kind:** decision
- **Part:** 2
- **Date:** 2026-09-12
- **Status:** active
- **Decision:** Compute item 9's revenue columns and item 11's repetition statistics for **every** event name in the vocabulary, rather than for the "candidate purchase event names" and "the progression events item 10 finds" that those items name, so that the purchase set and the progression set are visible selections from a complete table rather than choices made by this session.
- **Alternatives rejected:** Selecting a candidate purchase set by name — §10.3 states that adjusting the purchase-event set to clear a threshold invalidates the rule, and a set chosen by the session that then reads the counts cannot demonstrate it was not adjusted, even when it was not. Selecting the progression events for item 11 — naming which events are progression steps is the first half of defining a funnel step, which §8's content gate and §10.4 bar this session from. Computing both only for the events that looked relevant after item 10 returned — the same defect with an extra step.
- **Reason:** The cheapest way to prove a selection was not made with the answers visible is to make no selection. A complete table costs the same query and removes the question entirely; the architecture session then selects from an artefact it can check, which is the separation §10.1 exists to enforce.
- **Affects:** `sql/05_recon_revenue_population.sql` and `sql/08_recon_event_repetition.sql`; item 9's artefact and therefore §10.3's evaluation; item 11's artefact.
- **Falsifiable by:** An event vocabulary large enough that a complete table is impractical. At 37 event names it is not remotely so.

### A-091 — Item 5 is reported per shard suffix, and no day boundary is implied
- **Kind:** decision
- **Part:** 1
- **Date:** 2026-09-12
- **Status:** active
- **Decision:** Report item 5's `first_open` volumes grouped by `_TABLE_SUFFIX`, describe them throughout as **per-shard** rather than per-day, and state explicitly in the SQL, the results file and the findings document that this is the export's own shard key and not a day boundary of any kind.
- **Alternatives rejected:** Grouping by `event_date` — it is a different quantity from the shard suffix in principle, and choosing between them is choosing how a day is delimited. As it happens query 06 established that `event_date` equals the shard suffix on all 5,700,000 rows, so the two agree here; that agreement is a finding, not a licence to have picked one. Grouping by the UTC date of `event_timestamp` — it disagrees with `event_date` on 1,935,518 rows, so adopting it would have been picking a boundary outright. Calling the shard grouping "per calendar day", as item 5's artefact does — it reads as a day-boundary claim this session may not make.
- **Reason:** Item 5's artefact is worded as a count "per calendar day", but no calendar day is defined yet: item 3 exists to produce the facts bearing on one, and §10.4 reserves the choice to the architecture session. Reporting the shard grouping under its own name delivers the number the item needs while leaving the definition open.
- **Affects:** `sql/03_recon_event_vocabulary.sql`; item 5's artefact and verdict; the wording available to the architecture session when it does fix a boundary.
- **Falsifiable by:** Not applicable — this is a naming discipline, and the underlying counts are the same whatever they are called.

### A-092 — Item 12's full-column scan is run despite §10.1's column rule, and the specific instruction governs
- **Kind:** decision
- **Part:** project-wide
- **Date:** 2026-09-12
- **Status:** active
- **Decision:** Run `sql/02_recon_shard_scan_cost.sql`, a scan of **every** column of shard `events_20181003`, and record that it knowingly reads columns no checklist item asks about, because §10.2 item 12 requires "a billed-bytes figure for a full-column scan of one shard" while §10.1 states that "a query that reads a column no item asks about is a defect"; the specific requirement that names the query governs the general rule.
- **Alternatives rejected:** Answering item 12's unit cost from the dry-run estimate instead of executing — §10.2 item 12 says in terms that an estimate-based model is not an answer to the item, and §10.1 requires the cost model to be built on actuals. Answering it from the shard's `size_bytes` in table metadata — the same objection, and it would leave the metadata-to-billed relationship unmeasured, which is the very thing that makes the remaining 113 shards projectable without scanning them. Scanning a subset of columns and extrapolating — it is not a full-column scan and would understate the figure by an unknown factor. Treating the tension as a `challenge` and stopping — the conflict resolves cleanly on the specific-beats-general principle, and halting a pass over a rule that item 12 itself overrides would be obstruction rather than care.
- **Reason:** §10.1's column rule exists to stop a pass from scanning wide out of laziness, which is a rule about queries that answer some *other* item. Item 12's item is the cost of a wide scan, so for that one query the wide scan is the artefact rather than the waste. Recording the resolution matters more than the resolution itself: a reader who spots the conflict should find it already noticed.
- **Affects:** `sql/02_recon_shard_scan_cost.sql`; item 12's unit cost and the metadata-to-billed calibration built on it; 37.00 MiB of the 200 GiB total.
- **Falsifiable by:** The architecture session ruling that §10.1's column rule admits no exception, which would make item 12's unit cost unobtainable and require item 12 to be re-specified rather than this query re-run.

### A-093 — Provenance travels as a `.meta.json` sidecar, not as a comment line inside the CSV
- **Kind:** decision
- **Part:** project-wide
- **Date:** 2026-09-12
- **Status:** active
- **Decision:** Write A-086's five provenance fields — shard range covered, query job date, dry-run estimate, actual bytes billed, and row count — into a sidecar `outputs/tables/recon_NN_<name>.meta.json` beside each result file, leaving the CSVs bare-header exactly as Part 3's tables are, and carry the same figures machine-readably in `outputs/tables/recon_budget_ledger.csv`.
- **Alternatives rejected:** A leading `#` comment row inside each CSV, which is the most literal reading of A-086's "provenance line" — rejected because a `#` row gives any naive reader a malformed header and obliges every loader to pass `comment='#'`, in a repository whose central claim is that its outputs are checkable; a format that needs a special argument to parse correctly is a worse provenance carrier than one that does not. Provenance only in the ledger — A-086 requires it to travel *with* the output, because the ledger is one file and a result file may be read on its own. Extra provenance columns repeated on every data row — it corrupts the table's shape and repeats five constants thousands of times.
- **Reason:** A-086's requirement is that a reader holding one output file can reconstruct what produced it, and a sidecar satisfies that as fully as an in-file line while leaving the data file clean. **One boundary note, recorded rather than glossed:** §8 grants this session `outputs/tables/recon_*.csv` by extension, while its prohibition is framed as "any output file whose name does not begin `recon_`". The sidecars begin `recon_`, so they sit inside the prohibition's boundary but outside the grant's literal extension. The architecture session should tighten §8's path list either way when it next revises it.
- **Affects:** Every recon result file; §8's path list, which does not literally name `.meta.json`; what a reader can verify from a single artefact.
- **Falsifiable by:** The architecture session reading §8's grant strictly, which would move the provenance back inside the CSVs and require the loader caveat above.

### A-094 — The running total lives in a committed ledger, seeded with the two pre-session console queries
- **Kind:** decision
- **Part:** project-wide
- **Date:** 2026-09-12
- **Status:** active
- **Decision:** Keep §10.1's running total in `outputs/tables/recon_budget_ledger.csv`, one row per executed query carrying query file, job id, job date, shard range, dry-run estimate, bytes processed, bytes billed, divergence in bytes and as a ratio, the accumulated total and the remaining budget; and seed it before the first protocol query with the two manual console queries that ran before this session existed, recovering their **actual** billed bytes from `bq ls -j` job history rather than accepting an approximation, with their estimate, divergence and ratio fields reading `not_taken` because no dry run was ever performed on them.
- **Alternatives rejected:** Starting the total at zero — the pass would understate what the account had already spent, which is the one thing a budget ledger exists not to do. Seeding with the stated approximation of "roughly 20 MB" — job history carries the exact figure and it is **10,485,760 bytes**, so the approximation was over by nearly a factor of two; recording a guess when the fact is free is indefensible. Recording a reconstructed estimate for those two queries so their divergence could be computed — it would invent a number that was never taken and put it in the column that exists to record what authorised a query. Keeping the total in a scratch file — §10.1 makes it an artefact of the pass and item 12 reads from it.
- **Reason:** The ledger is the only place the budget rule is actually enforced rather than described, so it has to be committed, machine-readable, and honest about the rows whose provenance is weaker than the rest. Marking the two prior rows as outside the protocol is what lets a reader see that the pass knew the difference.
- **Affects:** §10.1's budget rule in practice; item 12's artefact; the halt rule's inputs; what re-running the pass would cost.
- **Falsifiable by:** Job history expiring before it is read, which would leave the prior queries' actuals unrecoverable and force the approximation this entry rejects.

### A-095 — CHALLENGE: four of §10.2's problematic conditions are stated without a threshold
- **Kind:** challenge
- **Part:** project-wide
- **Date:** 2026-09-12
- **Status:** active
- **Decision:** Raise for the architecture session that §10.2 states a problematic condition **without a number** for items 3, 7 and 11 — "disagreeing by more than a day for a **non-trivial share** of users", "a **material** web share", and "steps that repeat **heavily** within a session" — while the other items carry an explicit figure (5% for item 2, 100 for item 5, 0.1% for item 8, §10.3's two thresholds for item 9, 50% for item 13's null-rate test). This session reports the measured distribution for each, resolves each item on its artefact, and **invents no threshold**, because a threshold fixed by the session that is reading the numbers is the failure §10.3 opens by saying it exists to prevent.
- **Alternatives rejected:** Choosing a reasonable threshold for each and applying it — it makes this session the author of three gates while it holds the results, which is exactly the separation §10.1 and §10.4 are built to maintain. Marking the three items *unanswered* because their pass condition is unevaluable — the artefacts were produced in full and are genuinely informative, so recording them as unanswered would discard real evidence over a defect in the checklist rather than in the data. Absorbing the gap silently into a `decision` entry — this is an internal inconsistency in `ARCHITECTURE.md`, and §8 routes those to the architecture session as a challenge rather than leaving an implementation session to patch around them.
- **Reason:** A checklist is only a gate if each item has a pass condition someone else can check, which is A-082's own stated rationale. Three items do not, so for those three the checklist currently records a measurement rather than adjudicating one.
- **Additionally, surfaced by execution rather than by reading:** item 13 has the same defect in one of its three tests. Its null-rate test is quantified at 50%, and its single-value test is unambiguous, but "**dominated** by one placeholder" carries no figure — and the data makes this live rather than theoretical: `traffic_source.name` is 75.25% `(direct)` plus 24.66% null, so 99.91% of its rows fall in two buckets, one of which is a placeholder token, while `traffic_source.medium` and `traffic_source.source` are 99.79% and 99.39% two-valued. Whether those fields are "dominated" decides whether any traffic-source segmentation is permitted at all, and this session declines to decide it. The three items named above are reported as instructed; this fourth case is recorded here rather than in a separate entry so that the whole defect class sits in one place.
- **Affects:** The verdicts on items 3, 7 and 11; whether traffic-source segmentation is available to Part 1 or Part 2 under item 13; §10.2's status as an executable gate.
- **Falsifiable by:** The architecture session judging that these four conditions are deliberately qualitative and are meant to be exercised with the numbers in view by the party that writes the specification — which would make the design intentional, and this challenge simply wrong.

### A-096 — Item 1 finding: 114 contiguous shards, 20180612–20181003, but the range is not a whole number of weeks
- **Kind:** finding
- **Part:** project-wide
- **Date:** 2026-09-12
- **Status:** active
- **Decision:** Record that `firebase-public-project.analytics_153293282` holds exactly **114** tables matching `events_YYYYMMDD`, spanning **20180612** (a Tuesday) to **20181003** (a Wednesday), with **zero** missing dates across the 114 calendar days of that inclusive span and **no** `events_intraday_*` or other table of any kind; the shards total **5,700,000** rows and **4,151,085,667** logical bytes, and **every shard contains exactly 50,000 rows**. The inclusive span is 114 days, and 114 modulo 7 is **2**, so the window is sixteen whole weeks plus two days.
- **Alternatives rejected:** Not applicable — this is an observation. It was obtained from `__TABLES__` dataset metadata via `sql/00_recon_shard_inventory.sql`, with missing dates derived by a `GENERATE_DATE_ARRAY` anti-join against the shard list. The query's dry run and its execution both reported **0 bytes**, satisfying §10.1's requirement that item 1 be answered from table metadata at no query-byte cost rather than by a row scan.
- **Verdict: problematic.** Two of item 1's three conditions are clear — there are no gaps, and 114 shards is far above the 30 a D30 cohort would need — but the third fires: the range **does not cover whole weeks**, which §10.2 item 1 names as forcing a choice between a ragged window and discarding data. That choice belongs to the architecture session.
- **Prior unprotocolled observation, for the record:** a manual console query run before this session reported the same min, max, shard count and absence of gaps. The protocol result agrees with it exactly. The whole-weeks property was not noted at the time and is what changes this item's verdict.
- **Reason:** The shard range is the range every other query in the pass restricts itself to, and §10.3 binds Part 2's scope denominator to "the full shard range established by item 1", so this entry is the referent for that phrase. The uniform 50,000 rows per shard is recorded because it means daily volume is an artefact of how the sample was built rather than a property of the game's traffic, which bears on item 5 and on any per-day reading of any later metric.
- **Affects:** The `_TABLE_SUFFIX` literals in every billed recon query; §10.3's denominator; item 5's interpretation; whether Part 1's window is ragged or truncated.
- **Falsifiable by:** The public dataset gaining or losing shards, which would change the range and every count computed over it.

### A-097 — Item 2 finding: 71.54% of users have events but no `first_open`
- **Kind:** finding
- **Part:** 1
- **Date:** 2026-09-12
- **Status:** active
- **Decision:** Record that the full shard range contains **15,175** distinct `user_pseudo_id` values with at least one event of any kind, of which **4,319** have at least one `first_open` event, leaving **10,856** users — **71.54%** — with events but no install event in the window.
- **Alternatives rejected:** Not applicable — this is an observation. It was obtained from `sql/03_recon_event_vocabulary.sql`, whose `GROUPING SETS` produce the all-shards grand total and the all-shards `first_open` row from a single scan of `event_name` and `user_pseudo_id`.
- **Verdict: problematic.** §10.2 item 2 fixes the threshold at more than **5%** of users without a `first_open`; the observed figure is more than fourteen times that. §10.2 names the consequence: that population needs a stated treatment before any install-cohort definition exists, and it is the deferred "users with no install event" question the entry-format section of this file already reserved.
- **Reason:** This is the single largest obstacle to Part 1 as originally conceived. An install-cohort analysis that silently drops these users analyses 28% of the sample; one that keeps them needs a stated rule for users whose install is unobserved. Either way the choice must be made explicitly and in advance, and it is the architecture session's to make. A plausible mechanism — that these users installed before 20180612 and the window simply truncates their history — is **not** established by this pass and must not be assumed; nothing here distinguishes it from sampling.
- **Affects:** Any Part 1 install-cohort population; the denominator of any retention metric; §10.3's denominator, which A-084 deliberately includes these users in, making the scope bar harder rather than easier.
- **Falsifiable by:** A query establishing where these users' activity sits relative to the window edges, which would identify the mechanism without changing the count.

### A-098 — Item 3 finding: timestamps are microseconds, the export dates rows in a fixed non-UTC zone, and first-touch agrees with `first_open` for 99.72% of users
- **Kind:** finding
- **Part:** 1
- **Date:** 2026-09-12
- **Status:** active
- **Decision:** Record that `event_timestamp` is in **microseconds** — its minimum, 1528786810908005, is 2018-06-12 07:00:10.908005 UTC and its maximum, 1538636483482000, is 2018-10-04 07:01:23.482 UTC, both inside or immediately adjacent to the shard range; that `event_date` equals its own shard suffix on **all 5,700,000 rows**; that `event_date` differs from the UTC date implied by `event_timestamp` on **1,935,518 rows (33.96%)**, and that this difference is strictly one-sided — **1,935,518 rows are exactly one day behind** the UTC date and **zero rows are ahead** of it; that `device.time_zone_offset_seconds` is **non-null on every row** with **31** distinct values; that `user_first_touch_timestamp` is non-null on every row; and that the gap between a `first_open` event's own timestamp and the same row's `user_first_touch_timestamp` has median **0 seconds**, 99th percentile **81 seconds**, minimum **−94 seconds** and maximum **68,758,101 seconds** (about 795 days), with **13 rows belonging to 12 users** exceeding one day in absolute value — **0.28%** of the 4,319 users who have a `first_open`.
- **Alternatives rejected:** Not applicable — this is an observation. It was obtained from `sql/06_recon_identity_time_duplicates.sql` in a single scan, with all figures computed in one aggregation and then unpivoted. That query was **executed twice**: the first execution established the percentile shape, after which it was amended to measure the over-one-day share exactly rather than leave it bounded between 0% and 1%, and re-run. Both executions appear in the budget ledger, because both spent bytes.
- **Verdict: answered.** Item 3's problematic condition — the two timestamps disagreeing by more than a day for a "non-trivial share" of users — fixes no number, so this session reports 0.28% and adjudicates nothing. See the challenge in **A-095**.
- **Reason:** Recorded in this detail because item 3 is the input to a day boundary and this session may not fix one. The one-sided offset is the load-bearing fact: `event_date` is never ahead of the UTC date and is behind it on a third of rows, which is what a fixed negative UTC offset produces. That a device-level timezone field is fully populated with 31 distinct values means a property-local boundary and a device-local boundary are **both** available and are **different**, so the choice between them is real and must be made explicitly.
- **Affects:** Any D1, D7 or D30 boundary; whether install day is defined on `event_date`, on a UTC date, or on a device-local date; the reserved `assumptions.md` entry on day boundaries and timezone semantics.
- **Falsifiable by:** A documented statement of the property's configured reporting timezone, which would name the offset this pass can only bound.

### A-099 — Item 4 finding: `user_id` is null on every row; `user_pseudo_id` is the only identifier
- **Kind:** finding
- **Part:** project-wide
- **Date:** 2026-09-12
- **Status:** active
- **Decision:** Record that `user_id` is **NULL on all 5,700,000 rows** — a null rate of exactly 1,000,000 parts per million — so the count of distinct non-null `user_id` values is **zero**, while `user_pseudo_id` carries **15,175** distinct values.
- **Alternatives rejected:** Not applicable — this is an observation. It was obtained from `sql/06_recon_identity_time_duplicates.sql`. Query 01 had already established from `INFORMATION_SCHEMA.COLUMN_FIELD_PATHS` that `user_id` exists as a column on all 114 shards, so this is an absent value throughout and not an absent column on some shards — a distinction that mattered for `event_value_in_usd` and does not arise here.
- **Verdict: problematic.** This is item 4's stated problematic condition in its strongest form: `user_id` null throughout. §10.2 fixes the consequence — "a player" means a device-install rather than a person, cross-device deduplication is impossible, and the limitation must be stated plainly in Parts 1 and 2 rather than glossed.
- **Reason:** Every population count, retention denominator and funnel step in Parts 1 and 2 will be counted on `user_pseudo_id`, so every one of them counts device-installs. A player on two devices is two players throughout, and no analysis on this sample can say otherwise. A-084 already anticipated this and bound §10.3's denominator to `user_pseudo_id` regardless of what this item found, noting that where it over-counts people it over-counts in the direction that makes the scope bar harder; that reasoning is now confirmed rather than hypothetical.
- **Affects:** The meaning of "a user" everywhere in Parts 1 and 2; the required limitations section of both; §10.3's denominator, whose choice this vindicates.
- **Falsifiable by:** A revision of the public dataset that populates `user_id`, which would make cross-device deduplication possible and change what a player means.

### A-100 — Item 5 finding: median 38 `first_open` events per shard, against a threshold of 100
- **Kind:** finding
- **Part:** 1
- **Date:** 2026-09-12
- **Status:** active
- **Decision:** Record that `first_open` volume per shard has median **38**, mean **39.7**, minimum **1** and maximum **71**, across the **109** of 114 shards that carry the event at all — five shards contain no `first_open` event — for a range total of **4,322** `first_open` events.
- **Alternatives rejected:** Not applicable — this is an observation. It was obtained from the per-shard grouping set of `sql/03_recon_event_vocabulary.sql`. Per A-091 the grouping is by `_TABLE_SUFFIX`, the export's own shard key, and is **not** a day boundary; as it happens query 06 established that `event_date` equals the shard suffix on every row, so the two coincide here, but that coincidence is a finding rather than a choice this session made.
- **Verdict: problematic.** §10.2 item 5 fixes the threshold at a median daily install count below **100**; the observed median is 38, well under it. §10.2 names the consequence: day cohorts would produce retention curves that are mostly sampling noise, and the cohort grain becomes weekly.
- **Reason:** This interacts with A-096 in a way the architecture session needs both halves of. The grain must coarsen because daily install volume is too thin, but the window is sixteen weeks plus two days, so a weekly grain does not divide the range evenly either. Those two facts together constrain Part 1's cohort construction more tightly than either does alone. It also interacts with A-096's uniform 50,000 rows per shard: install volume here is a property of how the public sample was assembled, not of the title's acquisition.
- **Affects:** Part 1's cohort grain; the shape of every retention curve; how the two leftover days at the end of the range are handled.
- **Falsifiable by:** Nothing available in this dataset — the counts are what they are. A differently sampled export of the same property would change them entirely.

### A-101 — Item 6 finding: no session identifier exists anywhere in this export
- **Kind:** finding
- **Part:** project-wide
- **Date:** 2026-09-12
- **Status:** active
- **Decision:** Record that the full shard range carries **52** distinct `event_params` keys and that **none of them is `ga_session_id`**, nor `ga_session_number`, nor any other session identifier; the complete key list is committed in `outputs/tables/recon_04_event_parameters.csv`. A `session_start` event **does** exist — **74,353** events across **12,261** distinct users — but it carries no session id, so sessions can be counted as events and cannot be identified, grouped or joined.
- **Alternatives rejected:** Not applicable — this is an observation. It was obtained from `sql/04_recon_event_parameters.sql`, which unnests `event_params` over the full range and returns **every** distinct key with its volumes and which value slot it populates. Per A-090 the list is complete rather than filtered to keys this session judged engagement-related, so the absence is established over the whole parameter vocabulary rather than over a subset that might have excluded it.
- **Verdict: problematic.** §10.2 item 6's condition is "a null or constant session id"; an entirely absent one is that condition in its strongest form. §10.2 fixes the consequence: "returned on day 7" must then be defined on **event presence** rather than on sessions, which is a different definition and has to be stated as one. This session states the fact and defines nothing.
- **Reason:** This is the finding with the widest blast radius after A-097. It removes the per-session counting unit from item 11 entirely, it removes sessions-per-user as a candidate engagement measure, and it forces any Part 1 retention definition onto event presence. It is also the reason the funnel sketched in §10.2 item 10 cannot be repaired by counting per session: there is nothing to count per.
- **Affects:** Item 11, which is unanswerable in its per-session half (A-106); any Part 1 definition of a return visit; any Part 2 funnel counting unit; the reserved `assumptions.md` entry on the operational definition of a session, which must now record that no session can be operationally defined from this export without inventing one.
- **Falsifiable by:** A session identifier hiding in `user_properties` rather than `event_params`. This pass did not enumerate `user_properties` keys, so that possibility is open and is named here as the one place left to look.

### A-102 — Item 7 finding: Android and iOS only, mobile and tablet only, no web of any kind
- **Kind:** finding
- **Part:** project-wide
- **Date:** 2026-09-12
- **Status:** active
- **Decision:** Record that `platform` takes exactly two values over the full range — **ANDROID** (3,031,782 events, 7,410 distinct users, 53.19% of events) and **IOS** (2,668,218 events, 7,765 users, 46.81%) — with a null rate of **zero**; and that `device.category` likewise takes exactly two — **mobile** (4,167,158 events, 11,774 users, 73.11%) and **tablet** (1,532,842 events, 3,401 users, 26.89%) — also with a null rate of zero. There is **no web platform and no desktop category on any row**.
- **Alternatives rejected:** Not applicable — this is an observation. It was obtained from `sql/07_recon_field_profiles.sql`, which profiles both fields in the same single scan that answers item 13, so the two items rest on identical figures rather than on two separately-scanned versions of the same question.
- **Verdict: answered.** Item 7 has two problematic conditions and neither fires. There is no material web share, because there is no web share at all; and item 13 shows `platform` is not obfuscated — two distinct values, zero nulls, neither of them a placeholder token. The mobile-game framing holds for every one of the 5,700,000 rows, so no population filter is needed to establish it.
- **Reason:** Recorded because it is one of only three items that clear cleanly, and because its clearing is load-bearing in a negative way: it means any later population filter on platform would be removing nothing, so Parts 1 and 2 should not carry one for appearance's sake. The near-even Android/iOS split is also the one segmentation dimension this pass can confirm is both populated and balanced.
- **Affects:** Whether Parts 1 and 2 need a platform filter (they do not); the availability of platform and device-category as segmentation dimensions; item 13's field list, of which these are two.
- **Falsifiable by:** A revision of the public dataset adding a web stream, which would reintroduce the question this item exists to ask.

### A-103 — Item 8 finding: 207 duplicate event rows, 36 parts per million
- **Kind:** finding
- **Part:** project-wide
- **Date:** 2026-09-12
- **Status:** active
- **Decision:** Record that the full shard range holds **5,700,000** event rows against **5,699,793** distinct values of the natural key (`user_pseudo_id`, `event_name`, `event_timestamp`), leaving **207** duplicate rows — a share of **36 parts per million**, or **0.0036%**.
- **Alternatives rejected:** Not applicable — this is an observation. It was obtained from `sql/06_recon_identity_time_duplicates.sql` by comparing `COUNT(*)` against a `COUNT(DISTINCT)` over the three key fields concatenated, in the same scan that answers items 3 and 4.
- **Verdict: answered.** §10.2 item 8 fixes the threshold at a duplicate share above **0.1%**, which is 1,000 parts per million. The observed 36 ppm is roughly one twenty-eighth of that, so no downstream count needs a stated de-duplication step and Parts 1 and 2 need not name one.
- **Reason:** Recorded because item 8's consequence is conditional and the condition did not fire, which is worth stating explicitly rather than leaving as a silence — a check that is only mentioned when it fails is not a check, which is the principle §2.2 established for Part 3 and which applies here unchanged. The 207 rows are real and are disclosed; they are simply far too few to move any count a case study would report.
- **Affects:** Whether Parts 1 and 2 must specify de-duplication (they need not); the reliability of every event count in this pass, all of which are computed without de-duplicating.
- **Falsifiable by:** A materially different duplicate rate on a re-export, which would reopen the question for whichever counts were recomputed.

### A-104 — Item 9 finding: 27 revenue-positive purchase events and 0.178% payer coverage; §10.3 selects the re-scope branch
- **Kind:** finding
- **Part:** 2
- **Date:** 2026-09-12
- **Status:** active
- **Decision:** Record that over the full shard range the only purchase-shaped event is **`in_app_purchase`**, with **27 events** from **27 distinct users**, of which **27** carry a strictly positive `price` event parameter and **24** carry a strictly positive `event_value_in_usd`; that `spend_virtual_currency` shows **9,363 events** across **2,044 users** and is **excluded** from the revenue count per §10.2 item 9; and that measured against §10.3's denominator of **15,175** distinct `user_pseudo_id` values, **threshold 1 (at least 1,000 revenue-positive purchase events) is MISSED at 27**, and **threshold 2 (at least 0.5% of users, being 75.9 users) is MISSED at 27 users = 0.178%**. Both thresholds are missed, so **§10.3 selects the re-scope branch: Part 2 is a progression funnel only**, may not be titled, introduced or summarised as monetization anywhere including the README, and must state that this sample does not support revenue analysis with the observed counts given.
- **Alternatives rejected:** Not applicable — this is an observation. It was obtained from `sql/05_recon_revenue_population.sql`, which per A-090 computes the revenue columns for **every** event name rather than for a candidate set chosen by this session, so the purchase set is a visible selection from a complete committed table. The rule was evaluated **once**, from that file, before any Part 2 section existed — none exists now either.
- **The outcome does not depend on which revenue carrier is chosen, which is why it is safe to report:** the three candidates give 27 (`price` parameter), 24 (`event_value_in_usd`) and 27 (`in_app_purchase` events outright). The **most generous** of them still misses threshold 1 by a factor of **37** and threshold 2 by a factor of **2.8**. A caveat that cuts the same way: `event_value_in_usd` does not exist as a column on 15 of the 114 shards (absent 20180612–20180626, per query 01), so its figure is a lower bound — but the `price` parameter is present on all shards, and it is the larger number.
- **One number that must not be reached for:** `user_ltv.revenue` is strictly positive on 105,778 rows belonging to **146** distinct users, which is 0.96% of the denominator and would clear threshold 2. It is **not** a purchase event and must not be counted as one: it is a running per-user lifetime value carried on every row, accumulated over a history this window does not bound, and 146 users carry it while only 27 purchased inside the range. Substituting it to clear a threshold is exactly the manipulation §10.3 names as invalidating the rule, and it is recorded here so that the temptation is on the record as declined rather than unnoticed.
- **Reason:** This is the item §10.2 calls the sole input to Part 2's scope rule, evaluated once. The counts are printed here and in the findings document alongside both thresholds, whichever side fired, so a reader can see the rule was applied rather than chosen.
- **Affects:** Part 2's entire scope, title, framing and claims; the README, which may not describe Part 2 as monetization; what the architecture session may write into §10's successor.
- **Falsifiable by:** A revision of the public dataset carrying materially more purchase events. Nothing in the present extract could change the verdict, since the generous reading misses by more than an order of magnitude.

### A-105 — Item 10 finding: 37 event names, `in_app_purchase` present, no tutorial event
- **Kind:** finding
- **Part:** 2
- **Date:** 2026-09-12
- **Status:** active
- **Decision:** Record that the full shard range contains exactly **37** distinct `event_name` values, committed with event counts and distinct-user counts in `outputs/tables/recon_03_event_vocabulary.csv`; the largest are `screen_view` (2,247,623 events / 14,077 users), `user_engagement` (1,358,958 / 13,588), `level_start_quickplay` (523,430 / 10,166), `level_end_quickplay` (349,729 / 8,168) and `post_score` (242,051 / 8,580), and the smallest include `in_app_purchase` (27 / 27) and `notification_foreground` (1 / 1). Of the names §10.2 item 10 reports and requires verifying: `level_start_quickplay`, `level_complete_quickplay` (191,088 / 5,676), `spend_virtual_currency` (9,363 / 2,044) and `in_app_purchase` are **all present**, and there is **no tutorial event of any kind** — no event name over the full range contains the substring "tutorial".
- **Alternatives rejected:** Not applicable — this is an observation. It was obtained empirically from `sql/03_recon_event_vocabulary.sql` over all 114 shards as the whole distinct list, not as a check against names expected in advance.
- **Verdict: answered.** §10.2 says this item cannot fail and can only surprise. It surprised.
- **Prior unprotocolled observation, and the divergence — this is the finding:** a manual console query run before this session against **shard 20180612 alone** reported **31** distinct event names and **no `in_app_purchase`**, and that absence was carried into this session's brief as evidence the sample might be wholly unmonetized. Over the full range there are **37** names and `in_app_purchase` **does exist**. The single-shard observation was not wrong about its shard; it was extrapolated from one day to 114, and a 27-event behaviour spread across a 114-day window is absent from almost any single day one picks. This is precisely the failure mode §10.2 item 10 exists to prevent by requiring the vocabulary over the full range, and it is recorded because the protocol earned its cost here: the unprotocolled figure would have supported the right scope decision for the wrong reason, and would have stated in the report that the sample contains no purchase event at all, which is false.
- **The no-tutorial finding, by contrast, holds.** It was reported in §10.2, observed on one shard, and is now confirmed over all 114. §10.2 fixes the consequence: the funnel sketched as first_open → tutorial → first purchase has no referent for its middle step and is **abandoned rather than approximated**. This session writes no replacement funnel, per §8 and §10.4.
- **Reason:** Recorded in full because two-thirds of the project's remaining specification will be written from this list, and because the divergence above is the clearest available demonstration of why §10.1 separates the session that establishes facts from the session that uses them.
- **Affects:** Every Part 2 funnel step the architecture session may define; item 9's purchase set; item 11's progression events; the abandonment of the sketched funnel.
- **Falsifiable by:** A re-export with different event instrumentation, which would change the vocabulary wholesale.

### A-106 — Item 11 finding: per-user repetition measured for all 37 events; per-session not computable
- **Kind:** finding
- **Part:** 2
- **Date:** 2026-09-12
- **Status:** active
- **Decision:** Record that events-per-user was computed for **every** event name (A-090) and is committed in `outputs/tables/recon_08_event_repetition.csv`, showing heavy per-user repetition for progression events — `level_start_quickplay` has median 5 events per user, 90th percentile 54, maximum 24,641, with **81.9%** of its users recording more than one — against near-uniqueness for `first_open` (median 1, 90th percentile 1, maximum 2, **0.07%** of users repeating) and exact uniqueness for `in_app_purchase` (every one of its 27 users has exactly one). Repetition remains heavy within a single shard as well: `level_start_quickplay` shows median 3 and 90th percentile 25 per user-shard pair, with 76.4% of pairs above one. **Events per session, and whether a step repeats within a single session, could not be computed at all**, because no session identifier exists in either `event_params` (A-101) or `user_properties` (A-109).
- **Alternatives rejected:** Not applicable — this is an observation. It was obtained from `sql/08_recon_event_repetition.sql`. The per-shard grain is reported as a bounded fact about repetition within the export's own dating and is explicitly **not** a session and **not** a day boundary; substituting it for the missing session grain would have been defining a session, which §10.4 forbids this session outright.
- **Verdict: unanswered.** Item 11's artefact names events per user **and** events per session **and** within-session repetition; two of those three require a session identifier that does not exist. Per A-082, an item whose artefact does not answer its question is recorded as unanswered with the reason and escalated, rather than marked answered on a near miss. The per-user half is delivered in full and is real evidence; it is simply not the whole artefact.
- **Reason:** Recorded as unanswered rather than quietly downgraded because the reason matters more than the verdict: the counting-unit question item 11 asks cannot be resolved by measurement on this export, since one of the two candidate units is unavailable. That is a stronger and more useful statement than a threshold comparison would have been, and it belongs to the architecture session to act on.
- **Affects:** Any Part 2 funnel counting unit; the interpretation of every progression-event count, which repeats heavily per user; the reserved entry on the operational definition of a session.
- **Falsifiable by:** A session identifier being derived from some combination of existing fields, which would be a constructed definition rather than a measurement and is therefore the architecture session's to author, not this session's to discover.

### A-107 — Item 12 finding: billed bytes follow an exact rule, estimates are precise, and the wildcard minimum does not multiply
- **Kind:** finding
- **Part:** project-wide
- **Date:** 2026-09-12
- **Status:** active
- **Decision:** Record that the pass executed **13** query jobs (11 under protocol, plus the 2 pre-session console queries seeded per A-094) for a total of **5,259,657,216 bytes billed = 4.90 GiB**, which is **2.45%** of the 200 GiB recon ceiling and **0.48%** of the sandbox's 1 TiB monthly allowance; that the largest single query billed **1.01 GiB** against a 50 GiB per-query ceiling; that on every protocol query the **dry-run estimate equalled bytes processed exactly**; and that billed bytes follow the exact rule **billed = max(10 MiB, ceil(processed → whole MiB))**, which holds without exception on all 13 ledger rows. The per-day unit cost, from a full-column scan of shard `events_20181003`, is **38,797,312 bytes billed** against that shard's **38,133,989** bytes of table metadata, so metadata `size_bytes` predicts billed bytes to within the MiB rounding, and the full-range full-column cost projects to **4,151,085,667 bytes ≈ 3.87 GiB** from free metadata alone.
- **Alternatives rejected:** Not applicable — this is an observation. Every figure was read from job statistics via `bq show -j` after execution and accumulated in `outputs/tables/recon_budget_ledger.csv`, never from estimates, as §10.1 and A-085 require. Note that `sql/06_recon_identity_time_duplicates.sql` appears **twice** in the ledger: it was amended mid-pass to measure item 3's over-one-day share exactly and re-run, and both executions are recorded because both spent bytes.
- **Verdict: answered.** Item 12's first problematic condition does not fire and is not close: Parts 1 and 2's build queries plus a full re-run would need to exceed roughly 1,014 GiB of remaining monthly allowance, while this entire thirteen-query pass cost 4.90 GiB and the most expensive possible single query — every column of every shard — is 3.87 GiB. **No materialised extract is required** to keep §7.5's zero-cost re-runnability true.
- **On the second condition, reported rather than adjudicated:** §10.2 item 12 also names "a systematic divergence between estimated and billed bytes" as problematic in its own right. A divergence **is** systematic here — billed exceeds processed on every query that scans anything, always in the same direction. But it is exactly characterised and tightly bounded: it is MiB rounding plus a 10 MiB floor, never more than 1 MiB per query beyond the floor, with observed ratios from 1.0000 to 1.0174, the largest belonging to the smallest real scan. It is reported under that clause so a reader may disagree with the resolution; this session judges that a fully explained sub-MiB rounding rule is not the unpredictable planner behaviour the clause was written to catch, and resolves the item answered.
- **The finding §10.1 anticipated and the data contradicts:** §10.1 and A-085 both warn that BigQuery "bills a minimum per table referenced regardless of the estimate, which for a wildcard query touching many shards can dominate a cheap query's cost outright". That did **not** happen. A 114-shard wildcard scanning two columns billed **274 MiB**, not 114 × 10 MiB = 1.14 GiB. The 10 MiB minimum applies **per query, not per shard referenced**, so the cost model for Parts 1 and 2 is simply the scanned column bytes rounded up — and an estimate-based projection would have been very nearly right, which is worth stating precisely because A-085 was written on the expectation that it would not be.
- **Reason:** Item 12 requires a cost model built on actuals, and this is it, together with the two respects in which the actuals differ from what §10.1 predicted. Both differences make Parts 1 and 2 cheaper and more predictable than the budget rule assumed.
- **Affects:** §9's open question 7 on byte-identity for BigQuery-derived outputs, whose input this is; whether a materialised extract is needed (it is not); how the architecture session projects Part 1 and Part 2 build costs.
- **Falsifiable by:** A change to BigQuery's billing granularity or to how it prunes `_TABLE_SUFFIX` wildcards, either of which would invalidate the rule above while leaving the recorded per-query figures accurate for the date they were taken.

### A-108 — Item 13 finding: `geo.region` is unusable; segment-by-country survives
- **Kind:** finding
- **Part:** project-wide
- **Date:** 2026-09-12
- **Status:** active
- **Decision:** Record the null rate, distinct-value count and top values for all ten fields §10.2 item 13 names, committed in `outputs/tables/recon_07_field_profiles.csv`: **`geo.region` is 88.57% null** with 50 distinct non-null values and **fails** item 13's stated 50% null test; **`geo.country`** has **155** distinct values, **zero** nulls, and a top value of "United States" at 61.54% of events, and **passes** all three tests; `platform` (2 values, 0% null), `device.category` (2 values, 0% null), `device.operating_system` (2 values, 5.92% null), `device.language` (229 values, 0% null) and `app_info.version` (34 values, 0% null, top value "2.62" at 48.32%) all pass; and `traffic_source.name` (8 values, 24.66% null, `(direct)` at 75.25%), `traffic_source.medium` (8 values, 0.07% null, `(none)` at 75.25%) and `traffic_source.source` (9 values, 0.07% null, `(direct)` at 75.25%) pass the two quantified tests but are **99.91%, 99.79% and 99.39% concentrated in two buckets respectively**, one of which is a placeholder token in each case.
- **Alternatives rejected:** Not applicable — this is an observation. It was obtained from `sql/07_recon_field_profiles.sql` in a single scan, by exploding each row into (field, value) pairs and aggregating once; the per-field summary and the top-50 values are both derived from that aggregate, so the event table was read once rather than ten times. Query 01 had established that all ten field paths exist on all 114 shards, so no null count here can be an absent column.
- **Verdict: problematic**, on `geo.region`. §10.2 item 13 fixes the consequence in advance: a field this item shows to be a placeholder or predominantly null **is dropped, not reported**, so no Part 1 or Part 2 section may promise a region segmentation.
- **The consequence that was expected to fire and did not:** §10.2 item 13 names segment-by-country specifically as contingent on this item, and this session's brief anticipated it might not survive. It survives. `geo.country` is the best-populated segmentation dimension in the dataset — zero nulls, 155 distinct values, no placeholder domination — and on item 13's stated tests it clears comfortably. Platform, device category, device language and app version clear as well, so segmentation is available to Parts 1 and 2 on five dimensions rather than none.
- **The traffic-source fields are left undecided on purpose.** They pass every test §10.2 quantifies and fail the one it does not. Deciding whether 99.9% concentration in `(direct)` plus null constitutes "dominated by one placeholder" would be this session fixing a threshold while holding the numbers, which is what **A-095** challenges; the profile is reported and the judgement is deferred.
- **Reason:** Item 13 gates every segmentation requirement in both remaining parts, and the gate's outcome is mostly favourable, which is worth recording as precisely as an unfavourable one would be.
- **Affects:** Which segmentations Parts 1 and 2 may promise; the region segmentation, which is dropped; the country segmentation, which is permitted; item 7, which this item feeds and which it clears.
- **Falsifiable by:** A re-export with different obfuscation, which the dataset's documentation gives no reason to expect but which this pass cannot rule out.

### A-109 — Item 6 finding, completed: `user_properties` holds no session identifier either, but `first_open_time` covers every user
- **Kind:** finding
- **Part:** project-wide
- **Date:** 2026-09-12
- **Status:** active
- **Decision:** Record that `user_properties` carries **25** distinct keys over the full shard range, committed in `outputs/tables/recon_09_user_properties.csv`, and that **none is a session identifier** — closing the gap A-101 left open and establishing that no session id exists anywhere in this export, across both the event-parameter and user-property key spaces. Separately and importantly, record that the user property **`first_open_time` is populated for all 15,175 distinct users** on 5,699,844 rows, carrying an integer value and a set-timestamp, even though only 4,319 users have a `first_open` **event** (A-097).
- **Alternatives rejected:** Not applicable — this is an observation. It was obtained from `sql/09_recon_user_properties.sql`, the tenth and last query of the pass, which returns every distinct key with its volumes and populated value slots, filtered on no judgement about meaning. A-101's `Falsifiable by` field named this exact possibility as the one place left to look; this entry is the result of looking.
- **Why the `first_open_time` coverage matters, stated as a fact and not as a proposal:** item 2 found that 71.54% of users have no `first_open` event, which is the largest single obstacle to Part 1 as originally conceived. This pass now also records that an install-time value exists for **100%** of users in a different field. Whether those two facts can be reconciled — whether `first_open_time` is a usable install timestamp, how it relates to `user_first_touch_timestamp`, and whether it may stand in for a missing event — is **not** established here and is **not** this session's to decide: it is a question about how an install cohort is defined, which §8 and §10.4 bar this session from answering in code or in prose. It is recorded so the architecture session knows the field exists before it writes a population definition around the 4,319.
- **Also present, and noted without being pursued:** five `firebase_exp_*` keys (experiment membership, the largest on 6,894 users) and thirteen `_ltv_<CURRENCY>` keys, the largest being `_ltv_USD` on 109 users and `_ltv_JPY` on 10 — consistent with the 146 users A-104 records as carrying a positive `user_ltv.revenue`, and with revenue accumulated outside this window.
- **Reason:** Recorded as a separate entry because this file is append-only and A-101 was already written when this query ran; a later entry that closes an earlier one's stated gap is the append-only way to complete a finding. The `first_open_time` observation is the single most consequential thing this pass found that was not on the checklist.
- **Affects:** Item 6's verdict, which is now established across the whole key space; item 2's consequence and any Part 1 install-cohort population definition; the reserved entry on users with no install event in the window.
- **Falsifiable by:** `first_open_time` proving to carry a value that is not an install timestamp, which would remove the reconciliation this entry declines to make and leave A-097's obstacle standing unqualified.

### A-110 — A-088's authentication sequence includes a third command, `set-quota-project`
- **Kind:** supersedes A-088
- **Part:** project-wide
- **Date:** 2026-09-12
- **Status:** active
- **Supersedes scope:** the `Decision` field of A-088, in respect of the **authentication command sequence only**. Everything else in A-088 stands unchanged: that the credential is a user account and never a service-account key, that no credential file enters the repository, that `bq` authenticates against the gcloud CLI account rather than against application-default credentials, and that the project id reaches every query only through `GOOGLE_CLOUD_PROJECT`.
- **Decision:** Record that the authentication sequence actually used was **three** commands, not the two A-088 names: `gcloud auth login`, `gcloud auth application-default login`, and `gcloud auth application-default set-quota-project mobile-game-analytics-472301`. The third sets the project that application-default credentials bill quota against, so that a later client authenticating by ADC does not fail for want of a quota project on a sandbox with no billing attached.
- **Alternatives rejected:** Omitting the third command, which is what the approved plan specified — it leaves ADC without a quota project, so any future client authenticating that way would fail on a public-dataset query with a quota-project error that has nothing to do with the query; the pass itself would have been unaffected, since `bq` took the CLI account and its project came from `--project_id`. Setting a quota project on the CLI account instead via `gcloud config set project` — it would have made the project id an ambient default rather than an explicit argument, which weakens §8's requirement that the id travel in an environment variable and be passed deliberately.
- **Reason:** Recorded because it was an addition made during execution to a sequence the plan had already fixed, and a command that touches credential configuration should be on the record as approved rather than inferred later from shell history. It is also the one command in the sequence that names the project id directly, so its absence from the written record would leave a reader unable to reconstruct why ADC is configured as it is. Note that the id appears here, in `assumptions.md`, and in no committed query or module — §8 forbids hardcoding it in those, not recording it in the judgement log.
- **Affects:** The README's `## Dataset recon` setup block, which documents the two commands a reproducer strictly needs; what a future session authenticating by ADC will find already configured.
- **Falsifiable by:** A sandbox project that bills ADC quota without an explicit quota project, which would make the third command unnecessary rather than wrong.

### A-111 — The pass was reordered mid-flight, and the SQL files were renumbered to keep `NN` the execution order
- **Kind:** decision
- **Part:** project-wide
- **Date:** 2026-09-12
- **Status:** active
- **Decision:** Change the execution order agreed in the plan so that the event-parameter inventory ran **before** the revenue query, and renumber the SQL files so that `NN` continues to encode actual execution order as §7.2 requires: the final committed sequence is `00` shard inventory, `01` column inventory, `02` shard scan cost, `03` event vocabulary, `04` event parameters, `05` revenue population, `06` identity/time/duplicates, `07` field profiles, `08` event repetition, `09` user properties.
- **Alternatives rejected:** Keeping the planned order, in which the revenue query ran fourth and the parameter inventory eighth — rejected because query 01 established that this export carries no `ecommerce` and no `items` fields, and that `event_value_in_usd` is absent from 15 of the 114 shards, so the revenue query could not be aimed correctly until the full `event_params` key space was known; run in the planned order it would have checked `event_value_in_usd` alone and reported **24** revenue-positive events rather than 27, missing the `price` parameter entirely. Since item 9 is the sole input to §10.3's scope rule, aiming it at an incomplete set of revenue carriers would have understated the numerator on the one item where understating it is least acceptable. Keeping the planned **file numbers** while executing in a different order — §7.2 makes `NN` the execution order, so a directory listing would then have misstated what happened, which is the precise defect the numbering scheme exists to prevent. Renumbering after the fact to hide the change — the reordering is evidence about the dataset, not an embarrassment.
- **Reason:** The planned order was written before any query had run and rested on an assumption about where revenue lives that query 01 falsified. Reordering is what §10.1's dry-run-then-execute loop is for: each query informs the next, and a pass that cannot re-sequence on what it learns is not recon. Recording it matters because the approved plan states a different order, and a reader comparing plan to repository should find the difference already explained rather than have to infer it.
- **Affects:** The file numbering in `sql/`; item 9's artefact, which is materially more complete for the change (27 revenue-positive events rather than 24); the order the README documents for a reproducer.
- **Falsifiable by:** Not applicable — the pass ran in the order recorded here, and the numbering matches it.

---

## Amendment pass — `ARCHITECTURE.md` v1.5 (2026-09-12)

Parts 1 and 2 specified from the recon findings. IDs allocated by re-reading this file
per A-083: the highest heading present was A-111. Nothing in §1–§6 is touched; Part 3's
freeze at v1.2 / `c6d72f83` stands.

### A-112 — Part 1 cohorts are built on the `first_open` event, population 4,319
- **Kind:** decision
- **Part:** 1
- **Date:** 2026-09-12
- **Status:** active — `Decision` field superseded by A-157
- **Decision:** Build Part 1's install cohorts on the **`first_open` event**, restricting Part 1's population to the **4,319** users who have one (A-097), and not on the `first_open_time` user property that covers all 15,175 (A-109). Record the **71.54%** exclusion as a cost, disclose it as the first table of Part 1's report, state that the exclusion is **not random** — a user without `first_open` in the window installed before 20180612 or lost the event to sampling, so the 4,319 are systematically newer — and state that the resulting D1/D7/D30 figures describe users with an observed install event, not the sample's users generally and not the game's player base.
- **Alternatives rejected:** `first_open_time` over all 15,175 users — 3.5× the population, but its semantics are **unverified**: nothing in the recon establishes whether it is a true install timestamp or a value GA4 assigned when it first saw the user, and those differ exactly for the 10,856 users whose install predates the window, which is the population the property would be used to add. Using both and presenting whichever looks better — the failure mode this document exists to prevent. Using the property for cohorts and the event as a check — it inverts the reliability ordering, putting the unverified field in the headline. Abandoning install cohorts and reporting activity only — it discards the one question Part 1 exists to answer.
- **Reason:** A smaller defensible claim beats a larger unverifiable one. Every D1, D7 and D30 figure in Part 1 inherits the cohort definition, so an unverified proxy at that position puts the whole part on ground nobody has checked — and the cost of the alternative is fully disclosable, which an unverifiable foundation is not.
- **Affects:** §10.5.1; every Part 1 denominator; the required first table; the sensitivity check in A-123, which exists to quantify what this exclusion costs.
- **Falsifiable by:** Establishing `first_open_time`'s semantics — the 99.0%-agreement test in A-123 is the cheapest available probe, and passing it would justify revisiting this decision in a later version rather than mid-build.

### A-113 — The day key is `event_date`, and install day is the earliest `first_open`
- **Kind:** decision
- **Part:** 1
- **Date:** 2026-09-12
- **Status:** active
- **Decision:** Define every day boundary on **`event_date`**, and install day as the `event_date` of the user's **earliest** `first_open` event, with install day as **day 0** and never a retention day. The build session **reports the UTC offset it observes** rather than assuming one; no metric depends on the zone's identity.
- **Alternatives rejected:** A date recomputed from `event_timestamp` in UTC — it splits one local day across two keys for the 33.96% of rows where `event_date` is one day behind UTC (A-098), and it forfeits shard pruning, turning every query into a full-range scan. A device-local date from `device.time_zone_offset_seconds` (non-null on every row, 31 distinct values) — defensible in principle, but it gives every user a private day boundary so "day 7" stops being a single quantity, and it also forfeits pruning. Taking the latest `first_open` for the 3 users with two — arbitrary in the other direction; earliest is the install.
- **Reason:** `event_date` equals its own shard suffix on **all 5,700,000 rows** and is one day behind UTC on a third of them with **zero** rows ahead, which is the signature of a fixed non-UTC zone rather than noise. A consistent key that is also the partition key is the right basis for a day boundary; naming the zone is unnecessary, since consistency is what the metrics need and consistency is what the recon established.
- **Affects:** §10.5.2; D1, D7 and D30; §10.5.5's eligibility cutoffs; query cost, through pruning.
- **Falsifiable by:** `event_date` disagreeing with its shard suffix on any row, which A-098 measured at zero.

### A-114 — Classic retention is primary, rolling is secondary, with Wilson intervals and an n = 30 floor
- **Kind:** decision
- **Part:** 1
- **Date:** 2026-09-12
- **Status:** active — `Decision` field superseded by A-153
- **Decision:** Primary metric: **classic retention** — retained at day *N* if the user has at least one event whose `event_date` equals install day + *N* **exactly**, for *N* = 1, 7, 30. Secondary, in its own labelled table: **rolling retention** — at least one event with `event_date` **≥** install day + *N*. Every rate carries a **95% Wilson score interval** and its denominator; any cell with a denominator **below 30** is reported as a count only, with no rate and no interval. Rates to two decimal places in percentage points.
- **Alternatives rejected:** Reporting only one of the two — they are different quantities that the literature quotes interchangeably, and a reader who knows the space will ask which this is; reporting both costs two tables. Rolling as primary — it is bounded by the observation window in a way classic is not, so it is less comparable across cohorts. Wald intervals — they misbehave at small *n* and near 0 or 1, and cohort denominators here run from tens to thousands. Bootstrap intervals — a closed-form interval on a single proportion is exact enough and avoids a seed and a resample count for no gain. No suppression floor — at *n* = 30 a Wilson half-width around a 20% rate is already about 15 pp, and a rate nobody should read is better unprinted than printed with a caveat.
- **Reason:** D1/D7/D30 are conventionally classic, so the primary should be what a reader assumes unless told otherwise; and the interval plus denominator plus floor together stop a small-cohort rate from being read as a measurement.
- **Affects:** §10.5.3; every Part 1 rate; the weekly tables, where small cohorts make the floor bite; §10.7.5's decision not to cross segments with cohorts.
- **Falsifiable by:** Not applicable — both definitions are reported, so no reading is foreclosed.

### A-115 — Cohorts are weekly, in 16 fixed blocks anchored at the first shard, with the 2-day tail excluded
- **Kind:** decision
- **Part:** 1
- **Date:** 2026-09-12
- **Status:** active
- **Decision:** Use **weekly** install cohorts: 16 fixed 7-day blocks anchored at 20180612, W01 = 20180612–20180618 through W16 = 20180925–20181001, with installs on the **20181002–20181003 tail excluded from every cohort table** and their count reported. Also report a **single pooled cohort** as the headline D1/D7/D30 figures, with the weekly cohorts carrying the trend.
- **Alternatives rejected:** Daily cohorts — `first_open` per shard has median **38**, minimum 1, maximum 71, and **5 of 114 shards carry none** (A-100), against item 5's threshold of 100; a 38-user cohort gives a D7 Wilson half-width near 13 pp and A-114's floor would blank many cells outright. A single pooled cohort only — it is the most stable number available but it is not a cohort analysis, and it cannot show whether retention moved across the window. ISO weeks — 20180612 is a Tuesday, so W01 would be a 4-day cohort whose denominator is incomparable to every other. Folding the 2-day tail into W16 — it would make W16 a 9-day cohort with a denominator about 29% larger than its neighbours, distorting the very trend the weekly grain exists to show. Fortnightly cohorts — 8 cohorts of ~540 is stabler still, but it halves the trend resolution for a precision gain the Wilson intervals show is not needed.
- **Reason:** ~270 installs per week gives a D7 rate with a Wilson half-width near 5 pp, which is readable and comparable week to week, while 114 days divides into exactly 16 whole weeks plus 2 days (A-096) so anchored blocks waste only the 2-day remainder. Reporting pooled and weekly together separates the level from the trend instead of forcing one number to serve both.
- **Affects:** §10.5.4; §10.5.5's eligibility table; the cohort inventory output; §10.7.5's segment-crossing prohibition.
- **Falsifiable by:** Weekly install counts turning out badly uneven across the 16 blocks — the cohort inventory output is where that would show, and it would be a reported finding rather than a reason to re-grain mid-build.

### A-116 — Horizon eligibility is fixed by cutoff date, and ineligible cells are printed as null
- **Kind:** decision
- **Part:** 1
- **Date:** 2026-09-12
- **Status:** active — `Decision` field superseded by A-152
- **Decision:** A cohort is measurable at day *N* only if its **last** install day plus *N* falls inside the window ending 20181003, giving cutoffs of install day ≤ **20181002** for D1, ≤ **20180926** for D7 and ≤ **20180903** for D30 — so D1 runs on all 16 weekly cohorts, D7 on W01–W15, and D30 on W01–W12. An ineligible cell is printed as **explicitly null**, never zero, never blank and never omitted, with the cohort's install count still shown; a cohort excluded at one horizon still appears at the horizons it supports; and the pooled figures use a **different denominator per horizon**, printed beside each rate.
- **Alternatives rejected:** Omitting ineligible cohorts from the table — a reader would infer that only 12 cohorts exist. Printing zero — a false retention figure, and the worst available error here. Pooling D30 over all installs including those that could not be observed for 30 days — the same error as printing zero, with the arithmetic hidden inside a single number. Truncating the whole analysis to the D30-eligible window so all three horizons share one denominator — it would discard four cohorts of D1 and D7 data that are perfectly observable.
- **Reason:** Right-censoring is a property of the window, not of the cohorts, so it belongs in the table as a visible absence. A null says "not observable"; a zero says "nobody came back", and the two must never be confusable in a retention table.
- **Affects:** §10.5.5; every weekly retention table; the pooled denominators; what Part 1's negative-results section must say about the window.
- **Falsifiable by:** Not applicable — the cutoffs follow arithmetically from A-096's window and A-114's definitions.

### A-117 — Part 1 reports no session-level metric
- **Kind:** decision
- **Part:** 1
- **Date:** 2026-09-12
- **Status:** active
- **Decision:** Drop session-level analysis entirely from Part 1 — no sessions per user, no session length, no session-gap analysis, and none of the originally sketched `LAG`-over-session-gaps work. Count everything **per user** or **per user-shard**, in both parts, and state in the report that item 11's per-session half is permanently unanswered for this dataset.
- **Alternatives rejected:** Defining a session from event timestamps with a fixed inactivity threshold, 30 minutes being GA4's own default — legitimate as a stated convention, and rejected because the resulting session count is an artefact of the threshold sitting in a part whose other numbers are measurements, with nothing in the report able to tell a reader which is which. Using `session_start` as the boundary — it exists (74,353 events / 12,261 users) but carries no id, so attributing events to a session still needs an inactivity rule, and its own volume condemns it: **median 2 per user against 5,700,000 total events** (A-106) cannot describe the session structure of users with hundreds of events, so even the export's own marker is unreliable. Reporting session metrics with a caveat — a caveat does not make an invented quantity a measurement.
- **Reason:** No session identifier exists anywhere in this export — not in the 52 `event_params` keys, not in the 25 `user_properties` keys (A-101, A-109). The brief assumed a session concept the data does not carry, and the honest response is to drop the analysis and say why, not to manufacture the concept and label it carefully.
- **Affects:** §10.5.6; Part 1's output list; Part 2's counting unit (A-119); both negative-results sections.
- **Falsifiable by:** A session identifier appearing in a field neither A-101 nor A-109 profiled — both enumerated their whole key space, so this is close to excluded.

### A-118 — The README's three-sentence opener stays Part 3's, and no build session may touch it
- **Kind:** decision
- **Part:** project-wide
- **Date:** 2026-09-12
- **Status:** active — `Decision` field superseded by A-177; open question 8 closed 2026-09-20
- **Decision:** Leave §7.6's three-sentence opener as Part 3's, and forbid the Part 1 and Part 2 build sessions from modifying it; each owns only its own `## Part 1` or `## Part 2` heading. Recorded as the stated default for §9's **open question 8**, which stays open: whether the opener should become project-level is for the architecture session once both parts land.
- **Alternatives rejected:** Letting each build session extend the opener as its part completes — two sessions editing the same three sentences at the top of the README is a collision with no upside, and the sentences would stop being three. Rewriting the opener now as a project-level summary — it would have to describe results that do not exist yet, and §7.6 requires every figure in it to trace to a committed output. Giving the opener to Part 2 as the last session — it makes the README's most-read text the responsibility of whichever session happens to run last.
- **Reason:** Part 3 remains the highest-signal deliverable and the right thing for a reader to meet first, and a three-sentence opener only survives having exactly one owner.
- **Affects:** §7.6; §8's README grants for both build sessions; §9 question 8.
- **Falsifiable by:** Parts 1 or 2 turning out to carry the stronger headline, which is a judgement for the architecture session after the numbers exist.

### A-119 — Part 2's population is all 15,175 users, counted per user
- **Kind:** decision
- **Part:** 2
- **Date:** 2026-09-12
- **Status:** active
- **Decision:** Set Part 2's funnel population to **all 15,175 distinct `user_pseudo_id` values** with at least one event in the shard range, count **per user** rather than per event or per session, and make **`first_open` not a funnel step** — the funnel begins at "present in the window".
- **Alternatives rejected:** Part 1's 4,319-user install cohort — it would restrict Part 2 to 28.46% of the sample, duplicating Part 1's limitation for no new insight, and starting at `first_open` would make the funnel **non-monotone**, since 10,166 users started a level while only 4,319 have a `first_open`. Per-event counting — `level_start_quickplay` has median 5 events per user, 90th percentile 54, maximum 24,641, with **81.9%** of users repeating (A-106), so a per-event funnel counts one heavy player hundreds of times and calls it conversion. Per-session counting — no session identifier exists (A-117).
- **Reason:** A funnel step must be reachable by everyone in the denominator, and Part 2's question is progression through content rather than acquisition, so the acquisition-shaped restriction buys nothing and costs three quarters of the sample.
- **Affects:** §10.6.2; every Part 2 denominator; the step list in A-120; §10.7.5's Part 2 segment floor.
- **Falsifiable by:** Not applicable — the monotonicity argument is arithmetic from A-097 and A-105.

### A-120 — Four funnel steps, seven diagnostic events, and the sketched funnel abandoned
- **Kind:** decision
- **Part:** 2
- **Date:** 2026-09-12
- **Status:** active
- **Decision:** Fix the funnel as **S0** present in the window (15,175) → **S1** `level_start_quickplay` (10,166) → **S2** `level_end_quickplay` (8,168) → **S3** `level_complete_quickplay` (5,676). Report `screen_view`, `user_engagement`, `session_start`, `post_score`, `level_fail_quickplay`, `spend_virtual_currency` and `in_app_purchase` as **diagnostics in a labelled table, never as steps**. Abandon the sketched first_open → tutorial → first purchase funnel outright, substituting nothing for the missing tutorial step. `in_app_purchase` may not be a step.
- **Alternatives rejected:** Substituting `session_start` or `screen_view` for the absent tutorial step — it would preserve a funnel shape chosen before the schema was known, which is the wrong thing to preserve, and neither event is a progression stage. `session_start` as S1 — its 80.80% coverage is attractive but its median of 2 events per user makes the count a floor on an unreliable marker (A-117), and the funnel would then lean on the least trustworthy event in the export. `in_app_purchase` as a terminal step — 27 users, 0.178%, supports no comparison between any two groups. `level_fail_quickplay` as a step — it is the failure branch of an attempt, not a stage beyond it, and placing it in the chain would make the funnel non-monotone. `post_score` as a step — parallel to progression, not part of it.
- **Reason:** Item 10 established 37 event names and **no tutorial event of any kind** (A-105), so the original sketch has no referent; the four chosen events are the only ones that form a genuine content-progression chain, and they are monotone in raw user counts before any strictness is imposed.
- **Affects:** §10.6.3 and §10.6.5; every Part 2 conversion rate; the reconciliation requirement in A-121.
- **Falsifiable by:** An event among the 37 that is a progression stage and was missed — the vocabulary table in `outputs/tables/recon_03_event_vocabulary.csv` is the complete list a reviewer can check this against.

### A-121 — The funnel is strict, with raw counts beside it and two 1.0% reporting triggers
- **Kind:** decision
- **Part:** 2
- **Date:** 2026-09-12
- **Status:** active — `Decision` field superseded by A-175
- **Decision:** Compute the funnel **strictly** — step *k*'s population is users holding all of S0…S*k* — and report the strict cumulative count **beside** the raw per-step count in the same table. Count and report **out-of-order users** (S2 without S1, S3 without S2); a share above **1.0%** of the step's raw population is a reported finding with a stated interpretation. Report the **`level_end_quickplay` reconciliation** at event and user level: 349,729 against `level_complete_quickplay` plus `level_fail_quickplay` at 328,123, a shortfall of 21,606 events or **6.18%**; a shortfall above **1.0%** is a finding with a stated interpretation, is **not** silently reconciled, and does **not** redefine S2.
- **Alternatives rejected:** Raw per-step counts only — monotonicity would hold by luck rather than construction, and a funnel that can rise between steps is not a funnel. Strict counts only — the gap between strict and raw is the size of the out-of-order population, which is information about the export that a reader should see. Dropping out-of-order users silently — in an event log they usually mean an event was lost to sampling or emitted without its predecessor, and both bear on every count in the part. Redefining S2 as complete-or-fail to make the arithmetic close — it would fit the definition to the data and hide whatever the 6.18% actually is.
- **Reason:** Strictness makes the funnel well-formed; reporting raw alongside makes the strictness auditable; and both 1.0% triggers exist because a discrepancy that size in a log is a finding about the data rather than an inconvenience to smooth over.
- **Affects:** §10.6.4 and §10.6.5; Part 2's funnel table and its findings; what the negative-results section must cover.
- **Falsifiable by:** The reconciliation closing exactly, which would make the trigger moot and is worth recording either way.

### A-122 — The downsampling disclosure and the required shape of both reports
- **Kind:** decision
- **Part:** project-wide
- **Date:** 2026-09-12
- **Status:** active
- **Decision:** Require both reports to carry a top-level **downsampling disclosure** — that Parts 1 and 2 describe a **50,000-events-per-day sample** of this property and not the game's player base; that **no absolute count** may be presented as a measure of real traffic; that **no growth or trend claim** may be made from volume, since a rise in installs per week is a change in what the sample captured; and that the per-day sampling fraction is unknown and may not be uniform, so even cross-week rate comparisons could be affected. Require each report to open with the **population reconciliation** table, then the disclosure, then results — Part 2 adding its re-scope statement (A-130) before results — and to end with a **"What this does not support"** section in §6's shape, placed after results and before any recommendation, covering at minimum the sampling cap, Part 1's 71.54% exclusion and its direction, Part 2's unanswerable revenue and session questions, the absence of cross-device identity, and for each the specific measurement that would be required — never "further research is needed".
- **Alternatives rejected:** A footnote or a methods appendix — the uniform 50,000 rows per shard invalidates every volume reading in both parts, so burying it guarantees a reader forms a wrong impression before reaching it. Disclosing it once in the README only — the reports are what get read in isolation. Omitting the negative-results requirement because §6 already exists — §6 is frozen and scoped to Part 3, so the obligation has to be restated for these parts or it does not apply to them.
- **Reason:** Every shard holding exactly 50,000 rows (A-096) means daily volume is an artefact of sampling, and that fact bears on more of Parts 1 and 2 than any single result does. The report structure is fixed so the reader meets the population and the caveat before the numbers, which is the same ordering §6 chose for Part 3.
- **Affects:** §10.7.1 and §10.7.2; both reports' structure; what may be charted at all.
- **Falsifiable by:** Documentation of the sampling method that establishes a uniform fraction, which would soften the cross-week point but not the absolute-count one.

### A-123 — "A user" means a device-install, and the `first_open_time` check is gated at 99.0%
- **Kind:** decision
- **Part:** project-wide
- **Date:** 2026-09-12
- **Status:** active — `Decision` field superseded by A-155
- **Decision:** Treat `user_pseudo_id` as the sole identity throughout both parts and state in both reports that **"a user" means a device-install** — one person on two devices is two users, a reinstall may be a new user, and no cross-device claim, unique-people claim, or deduplication of people is possible, because `user_id` is NULL on all 5,700,000 rows (A-099). Separately, require Part 1 to attempt one **sensitivity check**: derive install day from the `first_open_time` user property for all 15,175 users and recompute pooled D7 — but **only if** that derived date equals the `first_open` event's `event_date` for **≥ 99.0%** of the 4,319 users who have both. Below that, the check is **omitted** and the observed agreement share is reported instead. When it runs, the figure belongs in the negative-results section, labelled a robustness check on an unverified field, with the agreement share beside it; it never enters a results table and never becomes a headline.
- **Alternatives rejected:** Using the word "users" without qualification — it reads as people, and every count in both parts would then overclaim. Omitting the sensitivity check — a reader will ask what discarding 71.54% costs, and the question deserves the best available answer even though the answer is not authoritative. Running it unconditionally — if `first_open_time` disagrees with the event date even for users who have both, the property's semantics are not established for the overlapping population either, and the check would import an unverified definition into the part that rejected it (A-112). Promoting it to a results table if it agrees closely — 99.0% agreement on the overlap says nothing about the 10,856 users who have no event to compare against, which is precisely the population the check extends to.
- **Reason:** Identity language is where this kind of case study most often overclaims, and the fix costs one sentence. The gated check is the compromise between answering a fair question and not building on an unverified field: the gate is what keeps it a check rather than a second definition.
- **Affects:** §10.7.3; both reports' wording; Part 1's data-handling output; A-112's cost disclosure.
- **Falsifiable by:** The check passing its gate and agreeing closely with the primary, which would be evidence for revisiting A-112 in a later version — not during the build.

### A-124 — The 207 duplicate rows are removed, unlike Part 3's outlier
- **Kind:** decision
- **Part:** project-wide
- **Date:** 2026-09-12
- **Status:** active
- **Decision:** De-duplicate on (`user_pseudo_id`, `event_name`, `event_timestamp`) before any count in both parts, report the **207** rows removed (A-103, **36 ppm**), and state the contrast with §5.1 in each report so it does not read as an inconsistency between parts.
- **Alternatives rejected:** Keeping duplicates, as §5.1 keeps Part 3's extreme row — that rule exists because removing a row after randomisation breaks intention-to-treat, and there is no randomisation and no ITT here, so the reasoning does not transfer. Keeping them on the grounds that 36 ppm cannot move a rate — true for rates, false for distinct-user counts and per-user event counts, both of which are sensitive to exact row duplication and both of which Part 2's funnel and A-121's repetition figures depend on. Reporting both ways — the removal is deterministic and the affected quantity is 36 ppm, so a second set of tables would be ceremony.
- **Reason:** A duplicated log row is not an observation of anything. The rule differs from Part 3's because the reason for Part 3's rule is absent here, and saying that explicitly is cheaper than letting a reader find two rules and assume one is a mistake.
- **Affects:** §10.7.4; every count in both parts; each report's data-handling record.
- **Falsifiable by:** The duplicate count differing materially from 207 at build time, which would be a finding about the source table rather than a reason to change the rule.

### A-125 — Segmentation: five dimensions permitted, four dropped, with numeric floors
- **Kind:** decision
- **Part:** project-wide
- **Date:** 2026-09-12
- **Status:** active — `Decision` field superseded by A-154
- **Decision:** Permit segmentation by **`geo.country`** (155 values, 0% null), **`platform`**, **`device.category`**, **`device.language`** and **`app_info.version`**. Drop **`geo.region`** at 88.57% null. Drop **`traffic_source.name`, `.medium` and `.source`**, reporting their concentration once as a single descriptive line to document why, and segmenting no metric by them. Attribute a user's segment from their **earliest event row**, ties broken by lowest `event_timestamp` then alphabetically lowest `event_name`. Report the share of users whose `geo.country` is not constant: above **5.0%** country segmentation carries a caveat naming the share, above **25.0%** it is dropped. Report a segment individually only at **≥ 100 users** in Part 1's eligible install population or **≥ 200 users** at S0 in Part 2; pool everything below the floor into one **"Other (n segments)"** row with its own count, never dropped and never itemised. Apply segmentation to **pooled cohorts only, never crossed with the weekly cohorts**.
- **Alternatives rejected:** Keeping `traffic_source.*` because it passes the null and distinct-count tests — it is **99.91%, 99.79% and 99.39%** concentrated in two buckets, one a placeholder in each case (A-108), so any segment comparison would pit under 1% of events against the rest and read as acquisition analysis while being noise. Keeping `geo.region` with a caveat — 88.57% null fails item 13's stated 50% test, and a caveat does not restore 88.57% of the data. Attributing country by modal value across a user's events — defensible, but it needs a tie rule of its own and diverges from Part 1's install-time framing; one deterministic rule for both parts is worth more than a marginally better one in each. Dropping sub-floor segments instead of pooling — it silently changes the denominator, so the shares would no longer sum. Crossing segments with weekly cohorts — 4,319 installs over 16 weeks and 5 countries is about 54 users per cell, below A-114's suppression floor for most cells, so the table would be mostly blanks.
- **Reason:** Item 13 gated segmentation and the gate's outcome was mostly favourable, so the specification says exactly which dimensions survived and which did not, with the number that decided each. The floors exist because a segment table's value is in its readable rows, and the pooling rule exists because a dropped row is a changed denominator.
- **Affects:** §10.7.5; both parts' segment outputs; what may be charted by country; §10.5.4's cohort grain, which the no-crossing rule protects.
- **Falsifiable by:** A non-constancy share above 25.0%, which drops country segmentation by this entry's own rule rather than by a new judgement.

### A-126 — Query ceilings reset from measurement, and the total-ceiling halt added
- **Kind:** supersedes A-085
- **Part:** project-wide
- **Date:** 2026-09-12
- **Status:** active
- **Supersedes scope:** the `Decision` field of A-085. Its reconciliation rule — the pre-flight gate on the estimate, actual bytes billed read from job statistics after execution, the running total kept in actuals, every divergence a finding in both directions — stands unchanged, as does the prohibition on raising a ceiling or enabling billing.
- **Decision:** Reset the ceilings to **4 GiB billed per query**, **20 GiB per build session** and **40 GiB across both build sessions**, carrying the protocol forward from recon to the Part 1 and Part 2 sessions. Replace the 2×/10 GiB divergence band with a **prediction**: billed = `max(10 MiB, ceil(estimate → MiB))`, and halt if actual billed differs from it by more than **1 MiB**. **Add the missing halt condition:** accumulated actuals breaching the session's total ceiling, checked before each query as predicted-plus-accumulated and after each query on actuals. Halt also if a single query's billed bytes exceed the per-query ceiling. Require any question answerable from table metadata to be answered from metadata at zero cost, and require a committed budget ledger per session.
- **Alternatives rejected:** Keeping 50 GiB and 200 GiB — they were set against the concern that the 10 MiB minimum applied **per shard**, which item 12 disproved: the minimum is per query, a 114-shard wildcard billed **274 MiB**, and the whole recon spent **4.90 GiB of 200 GiB**, 2.45% of a ceiling sized for a risk that was not real. Keeping the 2×/10 GiB band — the billing rule held exactly on 13 of 13 jobs and estimates equalled processed on every protocol query, so a tolerance band now hides a predictable quantity behind an allowance. Setting the per-query ceiling below 4 GiB — a full-column scan of the entire table costs 3.87 GiB, so a tighter ceiling would forbid a legitimate query. No total-ceiling halt, as v1.3 and v1.4 had it — a query could clear the pre-flight gate, bill under the per-query ceiling, stay inside the divergence band, and still push the running total past the total ceiling with nothing firing at all.
- **Reason:** A ceiling is only useful if it catches mistakes and never legitimate work, and the recon's actuals make both edges knowable: 4 GiB is the price of the most expensive honest query against this table, and the billing rule is exact enough to predict rather than tolerate. The total-ceiling halt closes the one gap that let a sequence of individually-permitted queries overrun the budget.
- **Affects:** §10.1 in full; both build sessions' query discipline; the required per-session ledger; §7.5's zero-cost re-runnability.
- **Falsifiable by:** The billing rule failing on a build query, which halts the session by this entry's own terms and is a finding about the planner, not a reason to widen the ceiling.

### A-127 — §8 grants by path prefix, and the dependency rule is scoped
- **Kind:** supersedes A-076
- **Part:** project-wide
- **Date:** 2026-09-12
- **Status:** active
- **Supersedes scope:** the `Decision` field of A-076, in respect of how the recon session's grants are expressed and what its append permission on the requirements files means. Its owner reasoning, its BigQuery credential rules and its content gate stand unchanged.
- **Decision:** Express every §8 grant and prohibition **by path prefix, never by extension** — the recon session owns `outputs/tables/recon_*`, covering the `.csv` results, the `.meta.json` provenance sidecars (A-093) and `recon_budget_ledger.csv` (A-094). Scope the dependency rule for every session: a session may add a dependency **only if resolution leaves every existing pin unchanged**; if it would move a pin that a completed part's lock file describes, the dependency is **not added** and the conflict is escalated to the architecture session. Name A-087's pattern as preferred: use a tool outside the project environment, as the recon did with the `bq` CLI, leaving both requirements files byte-for-byte unmodified.
- **Alternatives rejected:** Leaving the grant as `recon_*.csv` against a prohibition on "any output file whose name does not begin `recon_`" — the sidecars and the ledger fall into the gap between an extension-scoped grant and a prefix-scoped prohibition, so the files the recon actually produced were simultaneously ungranted and unforbidden. Widening the prohibition to match the extension instead — it would leave every future non-CSV output in the same gap. Leaving "append only" unqualified on the requirements files — it reads as licence to add a dependency whose resolution moves an existing pin, which silently breaks the clean-checkout guarantee of a part that is already finished and whose report cites its results; this nearly cost Part 3 that guarantee.
- **Reason:** A grant and its matching prohibition must be expressed in the same vocabulary or files fall between them, and "append-only" on a lock file means nothing unless it constrains resolution rather than only the diff.
- **Affects:** §8 in full; every session's permitted paths; the environment a completed part's reproducibility claim rests on.
- **Falsifiable by:** Not applicable — this is a correction to how a rule is written, not a change to what it intends.

### A-128 — Parts 1 and 2 are built by two sessions, run sequentially
- **Kind:** decision
- **Part:** project-wide
- **Date:** 2026-09-12
- **Status:** active
- **Decision:** Define **two** build sessions in §8 with explicit path lists — Part 1 owning `sql/10`–`29`, `src/part1_retention/**`, `outputs/*part1_*`, `reports/part1_retention_cohorts.md`, `run_part1.sh` and the README's `## Part 1` heading; Part 2 the corresponding `30`–`59`, `src/part2_funnel/**`, `outputs/*part2_*`, `reports/part2_progression_funnel.md`, `run_part2.sh` and `## Part 2` — and run them **sequentially, Part 1 then Part 2, never concurrently**. Neither touches Part 3's paths, the recon's paths, the README opener, or the other's paths. In the shared `60`–`89` range either may add a query and **neither may modify one the other committed**; a needed change is a copy under a new number with a recorded reason.
- **Alternatives rejected:** One session for both parts — no collision problem, but it carries Part 1's entire context into Part 2 for no benefit and produces one session owning two deliverables. Two sessions in parallel — it halves wall-clock and breaks A-083's re-read-before-append rule, which is only sufficient when no second session is appending at the same time; it also puts both sessions in the README at once. Allowing shared-SQL modification — it silently mutates the inputs of a part that is already committed and reported.
- **Reason:** Two deliverables with separable paths want two sessions; running them in order is what makes the collision rules sufficient rather than merely hopeful, and it lets Part 2 read Part 1's committed outputs — the population reconciliation, the country-constancy share — instead of recomputing them.
- **Affects:** §8; the order in which the remaining work happens; `assumptions.md` append safety.
- **Falsifiable by:** A Part 2 requirement that turns out to need something Part 1 did not produce, which is a `challenge` to the architecture session rather than grounds to run both at once.

### A-129 — Every condition in the Part 1 and Part 2 specifications carries a literal number
- **Kind:** supersedes A-082
- **Part:** project-wide
- **Date:** 2026-09-12
- **Status:** active
- **Supersedes scope:** the `Decision` field of A-082, extending its question/artefact/problematic-answer contract with a numeric requirement and recording the checklist as closed. Its item 10 and item 13 provisions stand and were both discharged (A-105, A-108).
- **Decision:** Uphold A-095's challenge: §10.2 stated a problematic condition **without a number** for items 3, 7, 11 and 13 while the other nine carried one. Record that all four closed on findings decisive enough that the omission did not bite — 0.28% of users for item 3, no web traffic at all for item 7, 81.9% repetition for item 11, null rates of 0% and 88.57% against a stated 50% test for item 13 — and that this was luck rather than method. **The standing rule from v1.5: every condition stated anywhere in §10.5, §10.6 or §10.7 carries a literal number.** Close the checklist, replacing its thirteen item texts with a what-it-established table pointing at A-096 through A-109.
- **Alternatives rejected:** Retroactively numbering the four conditions — the items are executed and closed, so it would be bookkeeping with no consequence. Dismissing the challenge because all four resolved cleanly — the challenge is about method, and the method was wrong even where the outcome was fine. Keeping the full item texts in the document alongside the specifications — they are in v1.4 and in git, and duplicating them would leave two versions of the checklist to drift.
- **Reason:** A condition a build session has to interpret is a condition the build session decides, which is the failure mode this whole document exists to prevent. The recon session was right to raise it, and the forward fix is worth more than a retroactive one.
- **Affects:** §10.2's closure; every condition in §10.5–§10.7; how future checklists are written.
- **Falsifiable by:** Not applicable — the rule constrains this document's authors, not the data.

### A-130 — §10.3's outcome recorded, and 27 must be presented as a lower bound
- **Kind:** decision
- **Part:** 2
- **Date:** 2026-09-12
- **Status:** active
- **Decision:** Record in §10.3 that the rule **fired** on item 9's counts — 27 revenue-positive events against a threshold of 1,000, short by a factor of **37**; 27 users being **0.178%** of 15,175 against 0.5%, short by a factor of **2.8** — selecting the progression-funnel branch, and that no judgement was exercised because the rule predates the query. Require Part 2's re-scope statement to present **27 as a lower bound rather than an exact count**, because `event_value_in_usd` is **absent from 15 of the 114 shards** and only **24** of the 27 events carry a strictly positive value in it while all 27 carry a positive `price` parameter. Rename the report to `reports/part2_progression_funnel.md`, since §10.3 forbids presenting Part 2 as monetization anywhere and a filename is a title.
- **Alternatives rejected:** Reporting 27 as exact — `event_value_in_usd`'s absence from 15 shards means the true count could be higher, and presenting a floor as a census is the kind of small overclaim a reader who knows this dataset catches first. Re-running the count on `price` alone to get a cleaner number — it would be re-counting after seeing the verdict, which A-081's evaluate-once rule forbids, and it cannot change the outcome. Keeping the filename `part2_funnel_monetization.md` — the file name is the first thing a reader sees in the repository, and §10.3's prohibition is on presentation, not only on prose.
- **Reason:** Nothing rests on the precision here: 27 could be wrong by an order of magnitude and still miss 1,000 by a factor of 3. That is exactly why saying "27, and that is a floor" costs nothing and buys the reader's trust in the numbers that do matter.
- **Affects:** §10.3 and §10.6.1; Part 2's title, filename, framing and README section.
- **Falsifiable by:** Not applicable — the outcome follows from A-104's counts against thresholds fixed in v1.3 and v1.4.

---

## Part 1 build session — decisions taken before the first query (2026-09-17)

Every entry in this block was written and committed **before the first Part 1 query
executed**, so that each call that shapes a number demonstrably predates the number.
IDs allocated by re-reading this file immediately before appending, per A-083: the
highest heading present was A-130.

Three of the eleven are `challenge` entries. None of the three is a reason to stop —
each is an ambiguity in `ARCHITECTURE.md` that has two faithful readings and no stated
adjudication, so the reading used was **directed by the project author** and is recorded
as directed rather than chosen. That is A-095's precedent: an implementation session that
holds the numbers does not get to settle a gap in the specification, even when its
preferred answer is the better one.

### A-131 — Part 1 runs on the `bq` CLI through its own runner and ledger, not the recon's
- **Kind:** decision
- **Part:** 1
- **Date:** 2026-09-17
- **Status:** active
- **Decision:** Execute every Part 1 query through the `bq` CLI exactly as A-087 did, but from this session's own `src/part1_retention/run_query.sh` and `src/part1_retention/budget.sh`, accumulating into `outputs/tables/part1_budget_ledger.csv`; install nothing, leave `.venv/`, `requirements.txt` and `requirements.lock.txt` byte-for-byte unmodified, and run the rendering layer on the interpreter and the `matplotlib` build that Part 3's lock file already pins.
- **Alternatives rejected:** Invoking `src/recon/run_recon_query.sh` and `src/recon/budget.sh` in place — §8 forbids this session `src/recon/**`, and the files are wrong for Part 1 on their own terms whatever the path rule said: `budget.sh` hardcodes the 50 GiB per-query and 200 GiB total ceilings that A-126 superseded with 4 GiB / 20 GiB / 40 GiB, carries A-085's 2×-and-10 GiB divergence band that A-126 replaced with a prediction, and writes the running total into `outputs/tables/recon_budget_ledger.csv`, a recon-prefixed output this session may not write. Copying the recon files into `src/part1_retention/` and editing the ceilings — the copy is fine, but presenting it as a copy would import the superseded halt rule's structure into a session governed by a different one; the ceilings and the halt rule are rewritten to A-126 rather than patched. Installing `google-cloud-bigquery` into `.venv` — A-127 scopes the dependency rule so that an addition is permitted only if resolution leaves every existing pin unchanged, and A-087 names using a tool outside the project environment as the preferred pattern rather than the exception. Running the rendering layer on `/usr/bin/python3` as the recon did — it carries no `matplotlib`, and §7.5 requires figures to be produced with an explicit backend, a fixed font configuration and pinned versions recorded in the environment.
- **Reason:** The recon's pattern is right and its ceilings are not, because v1.5 reset them from what the recon itself measured. Re-implementing the pattern under this session's own path is the only way to obey both §8's path list and §10.1's current numbers, and it keeps the completed part's environment untouched, which is the thing A-087 was protecting.
- **Affects:** `src/part1_retention/budget.sh` and `run_query.sh`; every row of `outputs/tables/part1_budget_ledger.csv`; the halt conditions that actually fire; the guarantee that Part 3 still reproduces from `requirements.lock.txt`.
- **Falsifiable by:** A Part 1 query that cannot be expressed through `bq`. None is expected: every query here is a single `SELECT` returning at most a few hundred rows.

### A-132 — The query cache is disabled on every Part 1 query, and under v1.5 the reason is the prediction band
- **Kind:** decision
- **Part:** 1
- **Date:** 2026-09-17
- **Status:** active
- **Decision:** Pass `--nouse_cache` on every Part 1 query, as A-089 did for the recon.
- **Alternatives rejected:** Leaving the cache at `bq`'s default — a cache hit bills zero bytes, and A-126 replaced A-085's tolerance band with a **prediction**: billed must equal `max(10 MiB, ceil(estimate → MiB))` to within 1 MiB or the session halts. A zero-billed cache hit misses that prediction by the whole prediction, so the cache would halt the session on a query that was entirely correct, and the only remedies available at that point — widening the band or raising a ceiling — are both forbidden. Disabling the cache only on re-runs — whether a query hits cache is a property of execution history rather than of the query, so the rule would make the halt condition depend on what happened to have been run before.
- **Reason:** Under v1.4's tolerance band a cached zero merely understated the ledger. Under v1.5's prediction it converts the session's only cost control into a false alarm, which is a strictly worse failure: the halt rule exists to stop the session when the cost model is wrong, and it must not fire when the cost model is right. Paying the bytes again costs a rounding error against a 20 GiB ceiling.
- **Affects:** Every Part 1 ledger row and every `.meta.json` sidecar; whether the halt rule is meaningful at all; the honesty of the session total.
- **Falsifiable by:** Not applicable — the alternative produces a halt on correct queries.

### A-133 — Raw query results are numbered by execution order, rendered report tables by report order
- **Kind:** decision
- **Part:** 1
- **Date:** 2026-09-17
- **Status:** active
- **Decision:** Write each query's result to `outputs/tables/part1_qNN_<purpose>.csv` with its `part1_qNN_<purpose>.meta.json` provenance sidecar, where `NN` is the SQL file's number and therefore its execution order (§7.2); write the rendered report tables to `outputs/tables/part1_NN_<name>.csv`, where `NN` is the order the table appears in the report (§7.2); and keep the ledger at §10.1's literal required name, `outputs/tables/part1_budget_ledger.csv`.
- **Alternatives rejected:** One file per query, doubling as the report table — the Wilson intervals, the suppression rule and the explicit-null rendering all belong to Python (§7.3 and §10.5.3), so the rendered table is a different artefact from the query result, and collapsing them would attach a provenance sidecar describing a scan to a file containing arithmetic that scan did not do. Rendering in place over the query result — it destroys the artefact the sidecar describes, so a reader could no longer check the rendering against its input. Numbering the raw results in report order — the report order is not fixed until the report is written, while §7.2 fixes the SQL number as execution order on the day the file is created. Putting the raw results outside `outputs/tables/` — §8 grants this session `outputs/tables/part1_*` by prefix and every extension, and a BigQuery-derived output that is not committed cannot carry A-080's provenance to a reader.
- **Reason:** §7.2 numbers outputs by report order and numbers SQL by execution order, and Part 1 has both kinds of artefact. Giving the raw results a `q` prefix keeps the two schemes legible side by side in one directory listing instead of forcing one artefact to carry the other's numbering.
- **Affects:** Every file under `outputs/tables/part1_*`; what a reader opens to check a rendered rate against the counts it came from; §10.1's provenance requirement.
- **Falsifiable by:** Not applicable — this is a naming convention, chosen so that the two required numbering schemes do not collide.

### A-134 — CHALLENGE: §10.5.5 does not say whether pooled eligibility is per install or per cohort
- **Kind:** challenge
- **Part:** 1
- **Date:** 2026-09-17
- **Status:** active
- **Decision:** Raise for the architecture session that §10.5.5 fixes the cutoffs as install day ≤ **20181002** / ≤ **20180926** / ≤ **20180903** and then says the pooled figures use "**all installs eligible at that horizon**", without stating which of two readings governs. Read **per install**, pooled D7 covers every install whose install day is on or before 20180926, which includes the W16 installs of 20180925 and 20180926 even though W16 itself is marked `—` at D7. Read **per cohort**, pooled D7 is exactly the union of W01–W15. D1 and D30 are identical under both readings, because W12 ends exactly on the D30 cutoff, so **only pooled D7 moves** — by the W16 installs falling on those two days. This session did not choose between them: the **per-cohort reading was directed by the project author**, and Part 1 implements pooled D1 = W01–W16, pooled D7 = W01–W15, pooled D30 = W01–W12, reporting the excluded 20180925–20180926 installs as an explicit count with their date range in the cohort inventory.
- **Alternatives rejected:** Choosing the per-install reading on this session's own authority because it is the more literal one — a build session holding the cohort counts is not the party that should settle what the specification means, which is A-095's finding and the reason §8 routes an internal inconsistency to the architecture session. Implementing both and reporting whichever reconciles better — two pooled D7 figures with no rule for which governs is exactly the structure §1.6 exists to prevent, one section over. Recording the outcome as a `decision` entry of this session's — it would put the session's name on an adjudication it did not make and would hide that the document is silent here. Marking the pooled table unanswerable until the document is amended — the ambiguity is worth one entry, not a stalled deliverable, and under either reading fifteen of the sixteen cohorts are pooled identically.
- **The reasoning recorded with the direction, since it is the architecture session's to weigh:** §10.5.5 states eligibility at cohort level and states it binary — 16 / 15 / 12. Under the per-install reading, W16 prints `NULL` in the weekly D7 table while contributing installs to pooled D7, so "eligible" means two different things in two tables about the same cohort. Under the per-cohort reading every pooled figure is the plain sum of its horizon's weekly cells, so the two tables reconcile by addition at every horizon, and a reader who sums the weekly column and finds a mismatch would suspect an error long before finding the explanation. It also matches the precedent §10.5.4 already set when it excluded the 20181002–03 tail rather than folding it into W16: a partial period inside a whole-period structure creates an artefact. And A-116's objection to discarding perfectly observable data does not bite, because those installs are reported at D1, where W16 is fully eligible, and their count at D7 is printed rather than dropped in silence.
- **Affects:** `sql/13_part1_classic_retention.sql` and `sql/14_part1_rolling_retention.sql`; the pooled D7 denominator and rate; `outputs/tables/part1_02_cohort_inventory.csv`, which carries the excluded count; §10.5.5, which should say which reading it means.
- **Falsifiable by:** The architecture session judging that "all installs eligible at that horizon" was always meant per install, which would make this entry a record of a resolved ambiguity rather than an open one — and would change one number, pooled D7, which is why it is worth fixing in the document rather than in a build session's head.

### A-135 — CHALLENGE: §10.5.3 and §10.5.5 do not say whether eligibility binds rolling retention
- **Kind:** challenge
- **Part:** 1
- **Date:** 2026-09-17
- **Status:** active
- **Decision:** Raise for the architecture session that §10.5.5's eligibility pattern — 16 cohorts at D1, 15 at D7, 12 at D30 — is stated in a subsection whose surrounding text is about the primary metric, and that nothing in §10.5.3, §10.5.5 or §10.5.7 says whether it governs the **secondary** rolling table; §10.5.7 item 5 asks only for "the same two shapes". Under the other reading the rolling table would carry all 16 cohorts at every horizon. This session did not choose: the **binding reading was directed by the project author**, and Part 1 applies the identical 16 / 15 / 12 pattern to rolling retention, with ineligible rolling cells printed as explicitly null through the same mechanism as classic.
- **Alternatives rejected:** Computing rolling on all 16 cohorts at every horizon — a cohort that cannot be observed to install day + *N* cannot be measured at *N* by either definition, so a rolling D30 on W13–W16 would count only the part of the ≥ install + 30 window that fits inside the export and would be truncated and understated; §10.5.5 exists to prevent exactly that artefact, and printing it beside twelve honest figures would be a worse error than printing a null. Computing it and marking it "partial" — a caveat does not repair a truncated denominator, and §10.5.3 already forbids presenting either definition without its label rather than with an excuse. Deciding it as this session's `decision` — same objection as A-134: the document is silent, and the silence is the architecture session's to close.
- **A second reason, which is about the code rather than the metric:** the self-verification asserts `rolling ≥ classic` at the same cohort and horizon, which is a true property of the two definitions. Under the non-binding reading that assertion is undefined wherever classic is null and rolling is a number, so the check would have to be weakened precisely where the two tables disagree most. Under the binding reading both tables are null on the same cells and the assertion runs over reported cells only, which keeps it a real check.
- **Affects:** `sql/14_part1_rolling_retention.sql`; the rolling weekly and pooled tables and their null cells; the `rolling ≥ classic` assertion in `src/part1_retention/verify.py`; §10.5.3 and §10.5.5, which should say whether eligibility is a property of the window or of the primary metric.
- **Falsifiable by:** The architecture session ruling that rolling retention is deliberately reported on all 16 cohorts because its ≥ form makes a truncated figure a legitimate lower bound — defensible, and it would need §10.5.3 to say so and to say how the truncation is labelled.

### A-136 — CHALLENGE: `app_info.version` is a permitted segment dimension with no constancy test
- **Kind:** challenge
- **Part:** 1
- **Date:** 2026-09-17
- **Status:** active
- **Decision:** Raise for the architecture session that §10.7.5 permits segmentation by `app_info.version` (34 values, 0% null, A-108) and requires a non-constancy check for **`geo.country` only**, with the 5.0% caveat trigger and the 25.0% drop trigger defined for country alone. App versions change over a 114-day window by nature — that is what a release is — so a user's version is the field most likely to vary across their own events, while country is among the least likely. Since §10.7.5 attributes every segment from the user's **earliest event row**, "segment by app version" silently means "**version at install**", which is a defensible quantity but not the one the phrase suggests. Part 1 therefore **measures** the non-constant share for `app_info.version` alongside `geo.country` and reports both as findings, and applies the 5.0% / 25.0% triggers to `geo.country` only, exactly as written. **No gate is invented for app version**, its segmentation is neither caveated nor dropped on this session's authority, and the measured share goes to the architecture session so that the decision is made with the number in view.
- **Alternatives rejected:** Applying country's 5.0% and 25.0% triggers to app version as the obvious generalisation — it would be this session fixing a gate while holding the numbers, which is the failure A-095 named and A-129 answered with the standing rule that every condition carries a literal number stated in the document rather than inferred by the session executing it. Not measuring it at all, on the grounds that §10.7.5 does not ask — the measurement costs about 30 MiB inside a query that is already running for country, and the architecture session cannot weigh a gap it has no figure for. Relabelling the dimension "app version at install" in the output — renaming a permitted dimension is a specification change, and this session may not make one; the observation belongs here instead. Dropping app-version segmentation pre-emptively — dropping a permitted dimension is as much an unauthorised decision as keeping a bad one.
- **Reason:** The constancy requirement in §10.7.5 exists because attribution from one row is only a description of the user when the field is stable across that user's rows. The requirement was attached to the dimension where instability is least likely and omitted from the one where it is most likely, which looks like an oversight rather than a judgement — but this session cannot tell the difference from inside, and inventing the missing threshold is the one response the document forbids.
- **Affects:** `sql/15_part1_segment_constancy.sql`, which measures both; the segment table's treatment of `app_info.version`; §10.7.5, which should say whether a constancy test applies to every permitted dimension or only to country, and with what numbers.
- **Falsifiable by:** The measured app-version non-constant share turning out to be negligible, which would make the gap harmless in this dataset — and would still leave the rule unstated for the next one, which is A-129's whole point.

### A-137 — Install day is the `event_date` of the user's lowest-timestamp `first_open`
- **Kind:** decision
- **Part:** 1
- **Date:** 2026-09-17
- **Status:** active
- **Decision:** Implement §10.5.2's "the `event_date` of the user's **earliest** `first_open` event" as the `event_date` carried by the `first_open` row with the lowest `event_timestamp` for that user, and assert in the same query that this equals `MIN(event_date)` over that user's `first_open` rows, reporting the number of users where the two disagree.
- **Alternatives rejected:** Taking `MIN(event_date)` alone — it is the same value whenever the two orderings agree and silently a different one when they do not, so using it without the assertion would hide the only case where the choice matters. Taking the latest `first_open` for the three users who have two (A-106: maximum 2 per user, 0.07% repeating) — §10.5.2 says earliest, and the earliest is the install. Leaving the tie unhandled and letting the query planner pick — it makes install day, and therefore the cohort assignment, non-deterministic across runs for those users.
- **Reason:** "Earliest event" is an ordering on time, and `event_timestamp` is the time field; `event_date` is a day key derived from it (§10.5.2). Ordering on the timestamp and reading the date off the winning row is the literal reading, and asserting the agreement means the distinction is checked rather than assumed for the three users where it could bite.
- **Affects:** `sql/10`, `12`, `13`, `14`, `16`; every cohort assignment and therefore every retention denominator; the data-handling record, which carries the disagreement count.
- **Falsifiable by:** The assertion failing, which would mean a user's `first_open` rows are ordered differently by date and by timestamp — a fact worth reporting in its own right, and the reason the assertion exists rather than a comment.

### A-138 — De-duplication is a GROUP BY on the natural key, with a MIN() collapse asserted to be a no-op
- **Kind:** decision
- **Part:** 1
- **Date:** 2026-09-17
- **Status:** active
- **Decision:** Implement §10.7.4's de-duplication as a `GROUP BY user_pseudo_id, event_name, event_timestamp` in the base CTE of every query that counts anything, taking `MIN()` of each remaining field the query reads — `event_date` and, where the query reads them, the five segment attributes — so the collapse is deterministic; and assert that the count of distinct 3-tuples equals the count of distinct 4-tuples including `event_date`, which establishes that no duplicate group straddles two dates and that the `MIN(event_date)` is a no-op.
- **Alternatives rejected:** `SELECT DISTINCT` over the three key columns plus `event_date` — that de-duplicates on a 4-tuple, not the natural key §10.7.4 names, so a duplicate pair carrying two different `event_date` values would survive as two rows and inflate a user's active-day set. `ANY_VALUE()` for the collapsed fields — it is not deterministic, so two runs could attribute a user to two different segments or two different install days from the same input. Skipping de-duplication in the retention queries because 207 rows at 36 ppm cannot move a rate — true of rates and false of the thing §10.7.4 actually protects, per-user distinct counts; and a rule applied only where it changes the answer is not a rule, it is a result. De-duplicating once into a materialised table and querying that — it puts a destination table outside the repository into the reproduction path, and A-107 established no materialised extract is needed.
- **Reason:** §10.7.4 fixes the key literally, so the implementation must group on exactly that key rather than on a convenient superset. The `MIN()` collapse is the deterministic way to carry the other fields through, and the assertion converts "the collapse probably does not matter" into a checked fact printed in the data-handling record.
- **Affects:** The base CTE of `sql/10`, `12`, `13`, `14`, `15`, `16`, `17`, `18`; the reported duplicate count; every distinct-user count in Part 1.
- **Falsifiable by:** The 3-tuple and 4-tuple counts disagreeing, which would mean a duplicated event was logged under two dates — a finding about the export, reported rather than absorbed.

### A-139 — The Wilson interval uses one z literal derived from the standard library, and suppression lives in exactly one function
- **Kind:** decision
- **Part:** 1
- **Date:** 2026-09-17
- **Status:** active
- **Decision:** Compute §10.5.3's 95% Wilson score interval in `src/part1_retention/wilson.py` with `z = statistics.NormalDist().inv_cdf(0.975) = 1.959963984540054`, defined once and imported everywhere, in the standard form `centre = (p̂ + z²/2n) / (1 + z²/n)` and `half-width = z/(1 + z²/n) · √(p̂(1−p̂)/n + z²/4n²)`; and apply §10.5.3's suppression rule — denominator below 30 prints the count and no rate and no interval — in exactly one function, which every table passes through.
- **Alternatives rejected:** Computing the interval in SQL — §7.3 puts aggregation in SQL and rendering in Python, and an interval computed from a count and a denominator is rendering; more practically, the formula would then be repeated in five query files and could drift between them. Adding `scipy` to the import path for `scipy.stats.norm.ppf` — it is already in `.venv`, so it would cost nothing, but the standard library gives the identical constant and keeps the rendering layer runnable without any third-party import except `matplotlib` for figures. Hardcoding 1.96 — it is not the 97.5th percentile, and at these denominators the difference is visible in the second decimal place the report prints. Applying the suppression test at each call site — the same rule written five times is five chances for one of them to be written as `<= 30` or to be skipped for the pooled table, and §10.5.3's floor is exactly the kind of rule that must not have exceptions nobody can find.
- **Reason:** §10.5.3 chose a closed form precisely so that no seed and no resample count enter Part 1, and the same spirit says the constant and the cutoff should each exist once. A single suppression function is also what makes the self-verification meaningful: it can assert that no rate anywhere sits on a denominator below 30, and that assertion is only informative if there is one place the rule could have been broken.
- **Affects:** `wilson.py` and `tables.py`; every interval in Part 1; the weekly tables, where small cohorts make the floor bite; the verification assertions.
- **Falsifiable by:** Not applicable as a correctness matter — the formula is standard and the constant is exact to the precision printed.

### A-140 — The segment floor is evaluated once, on the pooled install population, and segmentation covers classic retention only
- **Kind:** decision
- **Part:** 1
- **Date:** 2026-09-17
- **Status:** active
- **Decision:** Evaluate §10.7.5's "≥ 100 users in the eligible install population" **once**, against the pooled install population of the sixteen weekly cohorts, so that segment membership and the single "Other (n segments)" row are identical across D1, D7 and D30; then print each horizon's own denominator inside each segment, with §10.5.3's n < 30 suppression applying cell by cell. Segment the **classic** metric only — the primary — and leave rolling retention to its own labelled weekly and pooled tables. Attribute a user's segment from their earliest event row, ordered by `event_timestamp` then by alphabetically lowest `event_name`, after the A-138 de-duplication.
- **Alternatives rejected:** Re-evaluating the floor per horizon — a segment could then clear 100 users at D1 and fall into "Other" at D30, so the three columns of one table would describe three different partitions of the population and could not be read across; the "Other" row would also change meaning between columns while keeping its name. Segmenting rolling retention as well — §10.5.7 item 6 asks for one segment table and §10.5.3 makes rolling the secondary metric reported in its own labelled table; tripling the segment output for a secondary metric buys nothing a reader asked for. Dropping sub-floor segments instead of pooling them — §10.7.5 forbids it, and it would silently change the denominator so the shares no longer sum. Attributing by the modal value across a user's events — defensible, but it needs a tie rule of its own and diverges from the install-time framing §10.7.5 fixed for both parts.
- **Reason:** A segment table is read across its columns, so the partition has to be stable across them; the floor is about whether a segment is worth printing at all, which is a property of the population rather than of a horizon. The per-cell suppression floor then does the horizon-specific work, which is what §10.5.3 is for.
- **Affects:** `sql/16_part1_retention_by_segment.sql`; `outputs/tables/part1_07_retention_by_segment.csv`; which segments are named and which fall into "Other"; the verification that segment counts sum to the pooled population.
- **Falsifiable by:** A segment clearing the floor on the pooled population but falling below 30 at every horizon, which would print a named row with three suppressed cells — visible, correct under both rules, and worth reporting if it happens.

### A-141 — `first_open_time` is read as an integer epoch value and dated in the observed property-local zone
- **Kind:** decision
- **Part:** 1
- **Date:** 2026-09-17
- **Status:** active
- **Decision:** For §10.7.3's gated sensitivity check, take the `first_open_time` user property's `int_value` (populated for all 15,175 users, A-109), determine its unit by magnitude — microseconds at or above 1e15, milliseconds around 1e12, seconds around 1e9 — report the unit observed, and convert it to a date in the **same property-local zone the day key uses**, namely the whole-hour UTC offset shown by `sql/11_part1_day_key_offset.sql` to be consistent with `event_date` on all 5,700,000 rows. If more than one whole-hour offset is feasible, compute the agreement share under each and take the **minimum** against §10.7.3's 99.0% gate.
- **Alternatives rejected:** Converting in UTC — it would compare a UTC date against `event_date`, which A-098 shows is one day behind UTC on 33.96% of rows, so the check would fail its gate for a reason that is about the zone rather than about the property, and would report a disagreement the day key itself creates. Using the property's `set_timestamp_micros` instead of its value — that records when GA4 set the property, not what it says; §10.7.3 names the property's value. Taking the **maximum** agreement across feasible offsets, or picking the offset that maximises it — that is selecting the zone that lets the check run, on a field whose semantics are unverified, which inverts the gate's purpose. Running the check regardless of the gate and labelling the disagreement — §10.7.3 says the check is omitted below 99.0% and the observed share reported instead, and a robustness check on an unverified field is worth less than nothing if it is run after being told the field disagrees.
- **Reason:** The gate exists to establish that the property means what an install timestamp would mean, and that question is only asked honestly if the comparison is made on the same day key the rest of Part 1 uses. Taking the minimum across feasible offsets is the conservative direction: it can only make the check less likely to run, and the failure mode to avoid is a robustness figure that exists because a zone was chosen to produce it.
- **Affects:** `sql/17_part1_first_open_time_agreement.sql` and `sql/18_part1_first_open_time_sensitivity.sql`; whether query 18 runs at all; the negative-results paragraph §10.7.3 confines the figure to.
- **Falsifiable by:** `first_open_time` proving to be rounded rather than exact — GA4 is documented as recording it to a coarser granularity than the event stream — which would make a sub-day disagreement a property of the field rather than evidence against its semantics, and would be reported with the agreement share rather than hidden by it.

### A-142 — A-141's zone criterion was unsatisfiable, and is replaced by highest row agreement
- **Kind:** supersedes A-141
- **Part:** 1
- **Date:** 2026-09-17
- **Status:** active
- **Supersedes scope:** the **zone-selection criterion** of A-141 only. Its magnitude rule for the unit, its use of the property's `int_value` rather than its `set_timestamp_micros`, its refusal to run §10.7.3's check below the 99.0% gate, and its reason for taking the conservative direction all stand unchanged.
- **Decision:** A-141 said the date would be derived in "the whole-hour UTC offset shown by `sql/11_part1_day_key_offset.sql` to be consistent with `event_date` on **all 5,700,000 rows**". Query 11 has now established that **no such offset exists**: the feasible interval for a single constant offset is **empty**, its two binding constraints lying **93 seconds** the wrong way round (lower bound −25,201 s, upper bound −25,294 s exclusive). The criterion is therefore unsatisfiable, and as written it selects nothing, which would omit a check §10.7.3 requires Part 1 to attempt and report either way. Replace it with: **the whole-hour offset with the highest row-level agreement in query 11**, reporting that share; if two offsets tie exactly, take the lower of their agreement shares against the gate. On this export the rule selects **UTC−07:00**, which dates **5,698,777 of 5,700,000 rows (99.9785%)** against **5,549,442 (97.3586%)** for the runner-up UTC−06:00 — a margin of **149,335 rows**.
- **Alternatives rejected:** Keeping the criterion and omitting the check — it would report "the sensitivity check was not run" for a reason that has nothing to do with `first_open_time` and everything to do with a rule this session wrote, while §10.7.3 requires the check to be attempted and its outcome reported either way; a deliverable must not be voided by an implementation detail of its own gate. Widening "all rows" to a tolerance such as 99.9% — it invents a threshold where an argmax needs none, and A-129's standing rule is precisely that an invented number is worse than a stated one. Falling back to UTC on the grounds that no local zone fits exactly — `event_date` is one day behind UTC on 33.96% of rows, so UTC is the worst available reading and would fail §10.7.3's gate for a reason that is an artefact of the zone. Deriving the date from `device.time_zone_offset_seconds` per user — §10.5.2 rejected a device-local boundary for the metrics, and using one here would compare the property against a day key Part 1 does not use. Escalating to the architecture session and stopping — the defect is in **this session's own entry**, not in `ARCHITECTURE.md`; the append-only format's stated remedy for a decision that turns out wrong is a superseding entry, and §10.5.2 had already named UTC−07:00 as the offset the recon's evidence is "consistent with" and asked this session to observe rather than assume it, which is exactly what query 11 did.
- **The ordering problem, stated rather than buried:** this entry was written **after** query 17's agreement figures were visible. Under A-141 as written the check would have been **omitted**; under this entry it **runs**, because agreement at UTC−07:00 is 99.70% against a 99.0% gate. A reader is entitled to discount a rule changed in that position, so: the replacement depends on **query 11 alone**, which measures the day key and knows nothing about `first_open_time`; query 11's margin is 149,335 rows, so no defensible reading of it selects anything but UTC−07:00; and the one offset that would have failed the gate, UTC−06:00, is rejected by a figure taken before query 17 ran. The first rendering pass, with the check omitted under A-141, is recorded in this session's report so the counterfactual is on the record rather than only in this entry.
- **Reason:** A-141's criterion mistook `event_date` for a field derivable from `event_timestamp`. It is not: it is the export's own day stamp, and 1,223 rows — **0.0215%** — sit on the far side of a local midnight from where a constant −07:00 offset would put them, by no more than 93 seconds at the tightest. §10.5.2's argument for the day key never needed exactness: it rests on the key being **consistent**, which this session re-measured as `event_date` equal to its own shard suffix on all 5,700,000 rows, with zero rows ahead of UTC. A criterion stricter than the document's own claim is not conservatism; it is a rule that cannot be satisfied by correct data.
- **Affects:** `src/part1_retention/gate.py`; whether `sql/18_part1_first_open_time_sensitivity.sql` runs at all; the §10.7.3 figure and its placement in the negative-results section; `outputs/tables/part1_08_data_handling.csv`.
- **Falsifiable by:** The architecture session judging that a zone must date every row or not be used, which would omit §10.7.3's check and should then say so in §10.7.3 itself rather than leaving a build session to discover it.

### A-143 — Finding: no constant UTC offset dates every row, and the export's day key is its own stamp
- **Kind:** finding
- **Part:** 1
- **Date:** 2026-09-17
- **Status:** active
- **Decision:** Record that `event_date` equals its own shard suffix on **all 5,700,000 rows** (zero disagreements, confirming A-098), that it is one day behind the UTC date on **1,935,518 rows (33.96%)** and **never ahead** (zero rows), and that **no single constant UTC offset reproduces it on every row**: the feasible interval is empty by **93 seconds**, and the best whole-hour offset, **UTC−07:00**, dates **5,698,777 rows (99.9785%)**, leaving **1,223 rows (0.0215%)** that a fixed −07:00 zone would place on the other side of a local midnight.
- **Alternatives rejected:** Not applicable — this is an observation, from `sql/11_part1_day_key_offset.sql`, measured two independent ways: the binding bounds on a constant offset, and the row-level agreement of every whole hour from −12 to +14.
- **Reason:** §10.5.2 requires the build session to **report the offset it observes** rather than assume the "consistent with UTC−07:00" figure. It is observed, and it is very nearly exact — but "very nearly" is the finding. The 1,223 residual rows mean `event_date` is not a function of `event_timestamp` under any constant offset, so it is best described as the export's own day stamp, which happens to agree with a UTC−07:00 local date on all but 0.02% of rows. **No Part 1 metric is affected**, because every metric depends on the key being consistent rather than on the zone's identity, and the key is perfectly consistent with the shard it is stored in.
- **Affects:** §10.5.2's required statement that day *N* is a property-local day; A-142's zone selection; the report's day-key paragraph, which should say "the export's day stamp, agreeing with UTC−07:00 on 99.98% of rows" rather than "dated in UTC−07:00".
- **Falsifiable by:** A documented statement of the property's configured reporting timezone and of how the export assigns `event_date`, which would explain the 1,223 rows rather than leaving them measured but unexplained.

### A-144 — Finding: `first_open_time` is microsecond-precise, not hour-rounded, with one implausible value
- **Kind:** finding
- **Part:** 1
- **Date:** 2026-09-17
- **Status:** active
- **Decision:** Record that the `first_open_time` user property is populated for all **15,175** users and is **constant within every user** (zero users carry more than one value); that **15,174** values are microsecond-scale under A-141's magnitude rule and **one** is not; that the values are **not rounded** — **0** of 15,175 land on an exact hour boundary and only **13** on an exact second — contrary to GA4's documented behaviour of recording this property at a coarser granularity; and that the single non-microsecond value, **3,366,394,034,000**, is implausible under every reading (2076-09-03 as milliseconds, 1970-02-08 as microseconds) and falls outside the window under the rule A-141 fixed, so it is excluded from the sensitivity denominator and counted.
- **Alternatives rejected:** Not applicable — this is an observation from `sql/17_part1_first_open_time_agreement.sql`. The rounding test was written into that query before its results existed, precisely because A-141 anticipated that a rounded field would make a sub-day disagreement a property of the field rather than evidence against its semantics.
- **Reason:** It matters in two directions. The absence of rounding is why agreement with the `first_open` event's date reaches **99.70%** rather than the few points lower that hour-rounding would cost, so §10.7.3's gate clears on a field that is more precise than its documentation promises. And the one implausible value is the kind of thing a reader who knows GA4 would look for; recording it costs a sentence and its omission would be a small overclaim about a field Part 1 has already declined to build on.
- **Affects:** The §10.7.3 sensitivity check and its agreement share; the negative-results paragraph that carries it; nothing in the primary retention figures, which are built on the `first_open` event (§10.5.1, A-112).
- **Falsifiable by:** A re-export in which the property is hour-rounded, which is what the documentation describes and would lower the agreement share without changing what the check is worth.

### A-145 — Finding: the population reconciliation reproduces the recon exactly, and every data-handling assertion held
- **Kind:** finding
- **Part:** 1
- **Date:** 2026-09-17
- **Status:** active
- **Decision:** Record that Part 1 **recomputed** rather than transcribed §10.5.7 item 1's figures and got them exactly: **15,175** distinct users, **4,319** with a `first_open` event, **10,856** without, a **71.54%** exclusion (71.5387% unrounded). Also: **4,322** deduped `first_open` events across those users, **3** users with more than one and a maximum of 2 each; **207** duplicate rows removed at **36 ppm** of 5,700,000, matching A-103 exactly; **0** duplicate groups straddling two `event_date` values, so A-138's `MIN(event_date)` collapse is a measured no-op rather than an assumed one; and **0** users for whom the earliest-by-timestamp `first_open` date differs from `MIN(event_date)`, so A-137's install-day tie-break is a no-op too.
- **Alternatives rejected:** Not applicable — this is an observation, from `sql/10_part1_population_and_duplicates.sql`, computed in one pass at per-user grain after §10.7.4's de-duplication.
- **Reason:** A-079 makes the CSV the source of truth for every number, including numbers §10.5.7 quotes from the recon, so Part 1 had to recompute them and report a disagreement as a finding if one appeared. None did, at any of the three figures, which is worth stating: the recon's headline population numbers survive re-derivation through a different query, a different session and an added de-duplication step. The two assertions returning zero matter more than they look: each was written because the alternative reading was defensible, and each is now known to be immaterial on this export rather than assumed to be.
- **Affects:** `outputs/tables/part1_01_population_reconciliation.csv` and `part1_08_data_handling.csv`; the report's first table (§10.7.2); the standing of A-137 and A-138, both of which are confirmed inert here.
- **Falsifiable by:** A re-export changing any of the three population figures, which would change every denominator in Part 1 and is exactly what recomputing rather than transcribing exists to detect.

### A-146 — Finding: weekly install counts vary more than four-fold, and that is sampling rather than acquisition
- **Kind:** finding
- **Part:** 1
- **Date:** 2026-09-17
- **Status:** active
- **Decision:** Record that the sixteen weekly cohorts hold **4,191** installs between them with the **128** on the excluded 20181002–03 tail accounting for the rest of the 4,319, and that the per-cohort counts range from **95** (W03, 20180626–0702) to **415** (W08, 20180731–0806) — a **4.4×** spread around a mean of 262. Also record that **85** of W16's 278 installs fall on 20180925–26 and are therefore individually observable at D7 while their cohort is not, the figure A-134's directed per-cohort reading excludes from pooled D7.
- **Alternatives rejected:** Not applicable — this is an observation, from `sql/12_part1_cohort_inventory.sql`, whose ERROR() guards confirmed §10.5.4's block boundaries and §10.5.5's 16 / 15 / 12 eligibility before returning a row.
- **Reason:** §10.5.4 justified the weekly grain on an expectation of "~270 installs per cohort (4,319 over 16 weeks)". The mean is 262 and the estimate holds, but the **spread does not**, and it has a consequence §10.7.1 already governs: every shard holds exactly 50,000 rows, so a week with 415 observed installs did not acquire more players than a week with 95 — it is a week where installs were a larger share of a fixed sampled volume. **No growth, decline or acquisition claim may rest on these counts**, and the report says so where the inventory appears. The spread also means the weekly Wilson intervals are materially wider for some cohorts than §10.5.4's ~5 pp estimate: at n = 95 the D1 half-width is about 9 pp.
- **Affects:** `outputs/tables/part1_02_cohort_inventory.csv`; the width of every weekly interval; the §10.7.1 disclosure; any reading of the weekly trend.
- **Falsifiable by:** Documentation of the sampling method showing a uniform per-day fraction, which would make the counts proportional to real installs — and which §10.7.1 records as unresolvable from the data.

### A-147 — Finding: pooled classic retention is 21.74% / 5.67% / 2.09%, and the n = 30 floor never fired
- **Kind:** finding
- **Part:** 1
- **Date:** 2026-09-17
- **Status:** active
- **Decision:** Record pooled **classic** retention (§10.5.3's primary) as **D1 21.74%** (911 of 4,191, 95% Wilson 20.51–23.01), **D7 5.67%** (222 of 3,913, 4.99–6.44) and **D30 2.09%** (62 of 2,963, 1.64–2.67); and pooled **rolling** retention as **D1 47.01%** (1,970 of 4,191), **D7 29.03%** (1,136 of 3,913) and **D30 15.15%** (449 of 2,963). Record also that **no cell in either weekly table was suppressed**: the smallest cohort denominator is 95, three times §10.5.3's floor of 30, so the floor was checked on all 96 weekly cells and never bit. Weekly classic D1 runs from **13.28%** (W13) to **32.63%** (W03), and the three highest D1 cohorts are the three earliest.
- **Alternatives rejected:** Not applicable — this is an observation, from `sql/13_part1_classic_retention.sql` and `sql/14_part1_rolling_retention.sql`. Every pooled denominator and numerator was verified to equal the sum of its eligible weekly cells, which A-134's per-cohort reading makes an exact identity, and rolling was verified to be at or above classic on all 43 reported weekly cells and all pooled cells.
- **Reason:** Two things a reader will ask, answered here rather than left to the report. **First, the gap between the definitions is large** — rolling D30 is 7.2× classic D30 — which is precisely why §10.5.3 requires both and forbids presenting either without its label: a reader who met "15.15% D30 retention" without the word *rolling* would take away something the classic figure contradicts. **Second, the apparent decline in weekly D1 across the window is not a finding this data can support as a trend**: §10.7.1 makes the per-day sampling fraction unknown and possibly non-uniform, so a change in a rate across weeks cannot be separated from a change in what the sample captured. The report states the pattern and declines the causal reading.
- **Affects:** `outputs/tables/part1_03` through `part1_06`; the report's headline figures; the §10.7.1 caveat's wording.
- **Falsifiable by:** Nothing available in this dataset — the counts are what they are. A differently sampled export of the same property would change them wholesale.

### A-148 — Finding: all five permitted dimensions survive, and A-136's worry about app version did not bite
- **Kind:** finding
- **Part:** 1
- **Date:** 2026-09-17
- **Status:** active
- **Decision:** Record that **1.62%** of Part 1's install population (70 of 4,319) has a non-constant `geo.country` — **below §10.7.5's 5.0% caveat trigger**, so country segmentation is reported with no caveat and is not dropped — and that **1.97%** (85 of 4,319) has a non-constant `app_info.version`, the figure A-136 asked for and which §10.7.5 attaches no trigger to. Record the segment structure: `geo.country` names 5 segments and pools 110 into Other (n = 1,446); `device.language` names 6 and pools 124 (n = 940); `app_info.version` names 3 and pools 22 (n = 116); `platform` and `device.category` name both of their values and pool none. Every dimension's denominators sum exactly to the pooled denominator at all three horizons, and no named segment falls below the 100-user floor.
- **Alternatives rejected:** Not applicable — this is an observation, from `sql/15_part1_segment_constancy.sql` and `sql/16_part1_retention_by_segment.sql`.
- **Reason:** **A-136's premise was directionally right and quantitatively nearly irrelevant, and saying so is the point of having measured it.** App version does vary more than country — 1.97% against 1.62%, and 85 users against 70 — so the reasoning that a 114-day window spans releases holds. But at 1.97% it would not have tripped country's own 5.0% trigger had that trigger applied, so the missing test costs this dataset essentially nothing. The likely reason is that most of this population churns within days of installing and never meets a new release, which is the same fact the retention figures report. A-136 stands as a challenge about method — the dimension most likely to fail a constancy test is the one with no test — and its own `Falsifiable by` anticipated this outcome. The architecture session now has the number.
- **Affects:** `outputs/tables/part1_07_retention_by_segment.csv` and `part1_08_data_handling.csv`; the standing of A-136, which is answered on the numbers but not withdrawn; whether §10.7.5 needs a constancy test for every permitted dimension.
- **Falsifiable by:** A re-export spanning more releases, or a population with a longer observed life, either of which would raise the app-version share and could push it past a trigger that still does not exist.

### A-149 — Finding: §10.7.3's sensitivity check ran, and pooled D7 on the property population is 6.13% against 5.67%
- **Kind:** finding
- **Part:** 1
- **Date:** 2026-09-17
- **Status:** active
- **Decision:** Record that the §10.7.3 gate was **met** — the `first_open_time`-derived date equals the `first_open` event's `event_date` for **4,306 of 4,319** users, **99.70%**, against a 99.0% gate, at the UTC−07:00 zone A-142 selects — so the check **ran**. Deriving install day from the property for all 15,175 users places **9,106** of them **before** the window, **5,938** inside it and 131 after; pooled classic D7 over the D7-eligible cohorts of that derived population is **6.13%** (344 of 5,611, 95% Wilson 5.53–6.79) against the primary figure of **5.67%** (222 of 3,913, 4.99–6.44). The two intervals overlap across most of their width.
- **Alternatives rejected:** Not applicable — this is an observation, from `sql/17` and `sql/18`. The check was run only after the gate cleared; under A-141's original criterion it would have been omitted, and A-142 records why that criterion was replaced and that the replacement was written with query 17's numbers visible.
- **Reason:** This is the best available answer to the question §10.7.3 exists to ask — what does discarding 71.54% of the sample cost — and it is **not authoritative**, which is why §10.7.3 confines it to the negative-results section and forbids it from any results table. What it suggests: extending to the property population moves pooled D7 by about half a percentage point **upward**, not by a factor, so the event-based restriction does not look like it is hiding a wildly different population at this horizon. What it cannot establish: the property's semantics are still unverified for exactly the users it adds, since the 99.70% agreement is measured only on users who have both, and those are by definition the users whose install the window observed. Separately, that **9,106 users carry a derived install date before 20180612** is consistent with §10.5.1's statement that a user with no `first_open` in the window installed before it — **consistent with, not evidence for**, since it is the same unverified field making the claim.
- **Affects:** Part 1's negative-results section, which is where this figure lives; the standing of A-112's choice of the event over the property; §10.7.3's requirement, now discharged.
- **Falsifiable by:** Establishing `first_open_time`'s semantics directly — the 99.70% agreement is a probe, not a proof, and a documented statement of what the property records would replace the whole check with an answer.

### A-150 — Finding: rolling retention stays right-censored after eligibility, and its weekly trend is largely an artefact
- **Kind:** finding
- **Part:** 1
- **Date:** 2026-09-17
- **Status:** active
- **Decision:** Record that §10.5.5's eligibility rule, applied to rolling retention under A-135's directed reading, makes a rolling cell **measurable** but does not make it **comparable across cohorts**. Rolling at day *N* counts any event on or after install + *N*, so its value depends on how much window remains after that day — and the window remaining to a cohort's last installer falls from **101 days** (W01) to **3 days** (W15) at D7. Observed rolling D7 falls with it: **30.68%, 31.49%, 41.05%, 41.98%, 38.38%, 36.73%, 37.45%, 30.84%, 32.79%, 34.44%, 24.40%, 22.62%, 21.09%, 18.67%, 9.40%** for W01 through W15. The pooled rolling figures — D1 47.01%, D7 29.03%, D30 15.15% — are therefore a blend of differently censored cohorts, not an estimate of a single quantity.
- **Alternatives rejected:** Not applicable — this is an observation, read off `outputs/tables/part1_05_rolling_retention_weekly.csv` against the window arithmetic in §10.5.5.
- **Reason:** §10.5.3 already states the property — "rolling retention at day *N* is bounded by the observation window in a way classic is not" — and gives it as a reason classic is primary. This entry records how large the effect is on this export, because it governs what the report may say. **The rolling weekly table may not be read as a trend**: the decline from W01 to W15 is what a shrinking observation window produces mechanically, and no behavioural reading of it is available. Classic retention is immune, because an event on install day + *N* exactly needs one observable day rather than all of them, which is why its eligibility rule is sufficient and rolling's is not. A-135's directed reading is still the right one — it removes the cells with **no** observable window rather than pretending the rest are equivalent — but it is a floor, not a fix, and this entry is what stops the floor being mistaken for one.
- **Affects:** How `part1_05_rolling_retention_weekly.csv` and `outputs/figures/part1_02_rolling_retention_weekly.png` may be described; the report's rolling section and its negative-results section; the standing of §10.5.3's decision to make classic primary, which this supports.
- **Falsifiable by:** Not applicable as a matter of fact — the censoring follows arithmetically from the window. A longer export would shrink the effect without removing it, since the last cohort always has the least room.

### A-151 — The rolling tables carry the remaining observation window beside every cell
- **Kind:** decision
- **Part:** 1
- **Date:** 2026-09-17
- **Status:** active
- **Decision:** Print two columns beside every cell of `part1_05_rolling_retention_weekly.csv` and `part1_06_rolling_retention_pooled.csv`: `window_days_remaining_min` and `window_days_remaining_max`, the days of observation the window leaves after day *N* for the cohort's **last** and **first** installer. Directed by the project author, on the ground that A-150's censoring is a limitation **of the rolling table** rather than a note about it, and belongs where the table is read. The classic tables carry no such column, because classic needs the single day install + *N* and nothing after it.
- **Alternatives rejected:** Stating the censoring in the report only — a committed table is read on its own, and the figure it feeds is screenshotted on its own; a limitation that lives only in prose is one a reader meets after forming an impression. Printing a single "days remaining" figure for the cohort — a cohort spans seven install days, so its first and last installers differ by seven days of opportunity, and one number would hide which end it describes. Suppressing rolling cells whose remaining window is short — that is a threshold this session would be inventing, and §10.5.5's eligibility rule is the only cutoff the document states. Computing the column in SQL — it is date arithmetic over already-aggregated rows, so §7.3 puts it in the rendering layer with the intervals.
- **Reason:** The column makes two things visible that were previously only assertable. It shows the censoring **gradient** directly — 101 days for W01 at D7 against 3 for W15 — so a reader can see that the declining series is an artefact before anyone tells them. And because a cell is ineligible exactly when the minimum falls below 1, it turns §10.5.5's eligibility rule into arithmetic printed in the table: W16 at D7 shows −4, W13 at D30 shows −6, and the reason each prints NULL is on the same row as the NULL. W12 at D30 shows a minimum of **1**, which is why it qualifies at all and why its 5.90% is not comparable with W01's 15.34%.
- **Affects:** Both rolling tables and `outputs/figures/part1_02_rolling_retention_weekly.png`, whose subtitle now names the censoring; the report's rolling section; nothing in the classic tables or in any rate.
- **Falsifiable by:** Not applicable — the columns are derived arithmetic on figures already committed, and add no claim.

---

## Amendment pass — `ARCHITECTURE.md` v1.6 (2026-09-17)

Part 1's three challenges answered and four build defects fixed. IDs allocated by
re-reading this file per A-083: the highest heading present was A-151. §10.6 is
unaltered; §1–§6 untouched; Part 3's freeze at v1.2 / `c6d72f83` stands.

### A-152 — "Pooled at horizon N" means the union of eligible cohorts, per cohort
- **Kind:** supersedes A-116
- **Part:** 1
- **Date:** 2026-09-17
- **Status:** active
- **Supersedes scope:** the `Decision` field of A-116, in respect of the pooled denominator only. Its cutoffs, its null-not-zero rule and its per-horizon-denominator requirement stand unchanged. **Answers A-134.**
- **Decision:** Read "pooled at horizon *N*" as the **union of the cohorts eligible at *N***, not as a per-install re-selection: pooled D1 = W01–W16, pooled **D7 = W01–W15 exactly**, pooled D30 = W01–W12, with the **85** W16 installs falling on 20180925–20180926 excluded from pooled D7 and reported as an explicit count with their date range in the cohort inventory. The word **pooled** carries this meaning everywhere in §10.5–§10.7.
- **Alternatives rejected:** The per-install reading — pooled D7 would then include installs from a cohort the weekly table marks `—` at D7, so the pooled figure would rest on data the weekly table declares unmeasurable and the two tables would disagree by construction; it would also admit a fractional cohort, two days of W16, into a figure labelled as covering whole cohorts, with no row of its own anywhere for a reader to find. Reporting both readings — two pooled D7 figures differing by 85 installs is a distinction no reader can use and an invitation to quote whichever is higher. Leaving it ambiguous, as v1.5 did — a rule with two readings gets read both ways across three parts.
- **Reason:** Per cohort keeps the pooled and weekly tables over the **same population**, so any difference a reader sees between them is real rather than definitional. The effect here is narrow — **D1 and D30 are identical under both readings**, because W12 ends exactly on the D30 cutoff of 20180903 and W16 ends before the D1 cutoff of 20181002, so only D7 moves — and it is still worth fixing, because the ambiguity costs nothing to remove and compounds across parts.
- **Affects:** §10.5.5; Part 1's pooled D7 denominator and rate, already built this way under direction; the cohort inventory's excluded count; any future part that pools cohorts.
- **Falsifiable by:** Not applicable — this is a choice between two readings, and the document now names one.

### A-153 — Eligibility binds every window-bounded metric, and rolling stays censored anyway
- **Kind:** supersedes A-114
- **Part:** 1
- **Date:** 2026-09-17
- **Status:** active
- **Supersedes scope:** the `Decision` field of A-114, adding the eligibility binding and the censoring requirements. Its classic-primary choice, its rolling definition, its Wilson intervals and its n = 30 floor stand unchanged. **Answers A-135.**
- **Decision:** Establish that **observation-window eligibility is a property of the window, not of a metric's primary or secondary status**, and that it binds **every window-bounded metric** in this project — so §10.5.5's 16 / 15 / 12 pattern governs the rolling table, ineligible rolling cells print null through the same mechanism, and §10.5.7 item 5's "the same two shapes" means the same eligibility pattern. Separately, record that **rolling retention is right-censored by construction and eligibility does not repair it**: eligibility makes a cell measurable, not comparable. Therefore a weekly rolling series **may not be presented or described as a trend**, pooled rolling figures must be labelled a blend of differently censored cohorts, any rolling chart names the censoring in its subtitle, and **`window_days_remaining_min` and `window_days_remaining_max` are required beside every cell** of any table reporting a metric whose value depends on remaining window.
- **Alternatives rejected:** Leaving the rolling table at all 16 cohorts — it would print cells with **no** observable window at all, which is strictly worse than the censoring that remains. Treating eligibility as a primary-metric rule and leaving rolling unbound — it reads the pattern off the surrounding prose rather than off what the window can support. Dropping rolling retention entirely now that its weekly series is uninterpretable as a trend — rejected because its pooled figures still answer "what share ever came back on or after day *N*", which is a question readers ask, and because A-114's reason for reporting both definitions is unchanged. Keeping the window columns as a Part 1 nicety rather than a requirement — the columns are what make the censoring visible to a reader who was not told about it, and a limitation that depends on someone remembering to mention it is not a limitation the table carries.
- **Reason:** Rolling at day *N* counts any event on or after install + *N*, so its value depends on how much window remains after that day; the window remaining to a cohort's last installer falls from **101 days** (W01) to **3 days** (W15) at D7, and Part 1's rolling D7 tracked it from **30.68%** to **9.40%** (A-150). Classic is immune because an event on install + *N* **exactly** needs one observable day rather than all of them — which is why eligibility suffices for classic and is only a floor for rolling. The window columns turn that floor into arithmetic printed in the table: a cell is ineligible exactly when the minimum falls below 1, so the reason for a NULL sits on the NULL's own row (A-151).
- **Affects:** §10.5.3 and §10.5.5; both rolling tables and the rolling figure; how any future window-bounded metric must be tabulated; explicitly **not** Part 2's funnel, which is a whole-window presence metric.
- **Falsifiable by:** A window-bounded metric whose value does not vary with remaining window, which would need the column requirement narrowed rather than dropped.

### A-154 — The constancy test covers every attributed dimension, with per-dimension triggers
- **Kind:** supersedes A-125
- **Part:** project-wide
- **Date:** 2026-09-17
- **Status:** active
- **Supersedes scope:** the `Decision` field of A-125, in respect of the constancy requirement and its triggers only. Its permitted and dropped dimensions, its earliest-event attribution rule, its segment floors and its no-crossing rule stand unchanged. **Answers A-136.**
- **Decision:** Measure and report the non-constant share for **every** permitted segment dimension, not `geo.country` alone, and apply the **5.0%** caveat trigger and **25.0%** drop trigger **per dimension, independently**. Add that any report segmenting by a dimension whose earliest-event value differs in meaning from "the user's value" must say so in the table's caption — `app_info.version` means **version at install**, `device.language` means **language at first observed event**.
- **Alternatives rejected:** Keeping the test on `geo.country` alone — it was attached to the dimension where instability is **least** likely and omitted from the one where it is **most** likely, since app versions change over a 114-day window by nature; that looks like an oversight rather than a judgement. Setting a different, looser trigger for `app_info.version` on the ground that version drift is expected — it would encode the expectation as a licence, and the point of the test is to report the share so a reader can judge it. Dropping `app_info.version` as a dimension — version at install is a genuinely useful segment, and 1.97% non-constancy does not impugn it. Inventing the missing gate inside the build session — the one response this document forbids, and the Part 1 session correctly declined it.
- **Reason:** Attribution from a single row only describes the user when the field is stable across that user's rows, so the test belongs to the attribution rule rather than to one dimension. Part 1 measured both instead of guessing and found the worry **real in direction and small in size** — **1.97%** for `app_info.version` against **1.62%** for `geo.country` (A-148) — so the dimension without the test did vary more, and at that magnitude it cost this dataset nothing. Being right by luck on one export is not a reason to keep a rule attached to the wrong end.
- **Affects:** §10.7.5; Part 1's segment table captions; **Part 2's segment work, which must now measure all five**; any future part that segments.
- **Falsifiable by:** A dimension crossing 25.0%, which drops it by this entry's own rule rather than by a new judgement.

### A-155 — The zone selection rule has defined behaviour when no candidate is exact
- **Kind:** supersedes A-123
- **Part:** 1
- **Date:** 2026-09-17
- **Status:** active
- **Supersedes scope:** the `Decision` field of A-123, adding the zone selection rule it left unspecified. Its device-install identity language, its 99.0% gate, and the sensitivity check's confinement to the negative-results section stand unchanged.
- **Decision:** Derive the `first_open_time` date in the whole-hour UTC offset with the **highest row-level agreement with `event_date`**, reporting that agreement share and the **margin over the runner-up**, and breaking an exact tie by taking the **lower** of the tied offsets' agreement shares against the 99.0% gate. **The rule cannot select nothing.** If the best available agreement is itself below 99.0%, the selection stands and the check is omitted **by A-123's own gate**, with the agreement share reported as the reason. The selected offset must be chosen by a criterion **independent of the figure the check produces**.
- **Alternatives rejected:** An offset consistent with `event_date` on **all 5,700,000 rows**, as A-141 required — unsatisfiable by correct data: `event_date` is the export's own day stamp rather than a field derivable from `event_timestamp`, and A-143 found the feasible interval **empty by 93 seconds**, with 1,223 rows (**0.0215%**) sitting across a local midnight. As written it selected nothing, which omitted a required check for a reason having nothing to do with the field under test. Taking the **minimum** agreement across all candidate offsets, which was A-141's conservative spirit — it measures the worst zone rather than the export's zone, so it would fail the gate on every dataset regardless of the property's quality. Leaving the zone unspecified, as v1.5's §10.7.3 did — it forced the build session to invent a criterion, which is how an unsatisfiable one got written.
- **Reason:** §10.5.2's argument for the day key never claimed the key was derivable from the timestamp, only that it was **consistent**, which is established on all 5,700,000 rows. A criterion stricter than this document's own claim is not conservatism; it is a rule correct data cannot satisfy, and a rule that can select nothing hands the outcome to an accident. Highest agreement always selects and carries its own quality measure, so the gate — not the selection rule — decides whether the check runs.
- **Affects:** §10.7.3; whether the sensitivity query runs at all; the reported agreement share and margin; A-142, which this entry regularises.
- **Falsifiable by:** An export where the top two candidate offsets tie exactly, which the tie-break covers by taking the lower share against the gate.

### A-156 — A build session may not replace a selection criterion on its own authority
- **Kind:** decision
- **Part:** project-wide
- **Date:** 2026-09-17
- **Status:** active
- **Decision:** When a session finds a rule in `ARCHITECTURE.md` unsatisfiable by correct data it **stops**, appends a `challenge` naming the criterion, the evidence and the **margin of failure**, and **proceeds on the document's default for a failed gate** — for a gated optional step, omitting it and reporting the omission with its reason. The architecture session then replaces the criterion. Where a replacement is made under explicit direction from the project author, three disclosures are **mandatory and their absence voids the result**: that the replacement **inverts or weakens** the criterion it supersedes, named as such; that it was **written with the dependent results visible**, stated plainly rather than left to be inferred from commit order; and the **margin** by which the new criterion selects, measured **before** the dependent figures exist. In every case a criterion may only be replaced by one whose value **cannot be influenced by the figure the step will produce**.
- **Alternatives rejected:** Permitting a session to substitute its own criterion when the document's is unsatisfiable — it is the most understandable thing to do and the most corrosive, because the session is the party whose results depend on the choice, and A-142 shows the shape it takes: minimum became maximum, and the rule was written with the numbers on screen. Forbidding replacement absolutely — it leaves a session blocked by a rule that correct data cannot satisfy, with no defined move, which is how Part 1's first pass silently omitted a required check. Requiring disclosure without the independence test — disclosure makes a bad criterion visible, not acceptable; a criterion that reaches for the number the step is about is p-hacking however fully it is confessed.
- **Reason:** A-142 is the case this rule is built from, and it is the case that shows the line. Its replacement genuinely inverted its predecessor and was genuinely written with results visible — and it still stands, because row-level agreement with `event_date` is a property of the export rather than an output of the sensitivity check, so the inversion changed **which zone was chosen**, not **whether the answer looked good**. That independence is the whole distinction, and Part 1's report earned the result by disclosing all of it in §8.2 rather than explaining it away. The rule records both halves: the default is to stop and omit, and the exception survives only with the independence property plus the three disclosures.
- **Affects:** §10.7.7; every build session's response to an unsatisfiable rule; **Part 2, which inherits this rule unchanged**; how A-142 is read.
- **Falsifiable by:** Not applicable — this constrains sessions, not data.

### A-157 — A stated bias must name its direction
- **Kind:** supersedes A-112
- **Part:** project-wide
- **Date:** 2026-09-17
- **Status:** active
- **Supersedes scope:** the `Decision` field of A-112, in respect of the bias-direction disclosure only. Its choice of the `first_open` event over the property, its 4,319 population and its 71.54% cost disclosure stand unchanged.
- **Decision:** Complete §10.5.1's inference: the excluded 10,856 are, to that extent, an **established base**; an established base retains better than new installs; **therefore Part 1's retention figures sit below what a whole-population view would show — they understate it**; by how much is unknown and no report estimates it, with the §10.7.3 probe the only available measurement and confined to the negative-results section. General rule: **wherever any part of this project states that a figure is biased, it names which way, or states explicitly why the direction cannot be determined.**
- **Alternatives rejected:** Keeping "the direction of the bias is knowable" — that is a promise of a disclosure rather than a disclosure, and it leaves the reader to complete an inference the author has already made. Naming the direction and also estimating the magnitude — the magnitude is genuinely unknown, and the one probe available rests on an unverified field (A-155), so an estimate would be a guess wearing a number. Leaving the completion to each report — Part 1's report did complete it in §8.1, which is exactly how the document ended up **weaker than the report written against it**; the rule belongs upstream.
- **Reason:** A direction is either determinable or it is not. If it is, withholding it is a worse disclosure than saying nothing, because it signals the author knows and has chosen not to say; if it is not, saying so is itself the finding. The asymmetry here is knowable from the mechanism alone — newer installs against an established base — without any figure being estimated.
- **Affects:** §10.5.1; every negative-results section in the project, **Part 2's included**; the standing of Part 1's §8.1, which this brings the document up to.
- **Falsifiable by:** Evidence that the excluded population is not an established base — for instance that their absent `first_open` is a sampling artefact rather than a pre-window install — which would make the direction indeterminate and require saying so instead.

### A-158 — Derived figures are emitted as table cells, and the audit checks the declared cell
- **Kind:** decision
- **Part:** project-wide
- **Date:** 2026-09-17
- **Status:** active
- **Decision:** Distinguish a **quoted** figure, which appears verbatim as a cell of a committed table, from a **derived** one — a count of rows meeting a condition, a sum, a difference, a ratio, a cross-table percentage, an extremum, or any "*N* of *M*" statement. **Every derived figure in prose must be turned into a quoted one:** the renderer computes it and emits it as its own cell in `outputs/tables/<part>_report_figures.csv`, one row per figure carrying an id, the value, a one-line definition and the source tables, and the prose quotes that cell. **The audit checks the declared cell, not the corpus:** each prose figure is tagged with its table and column, and a number present somewhere in the tables but not in its declared cell **fails**. Exempt numerals are enumerated: dates and date ranges, section numbers, `ARCHITECTURE.md` and `assumptions.md` references, thresholds quoted from this document, and counts of this document's own items.
- **Alternatives rejected:** A second-pass recount by the session — that is the check that just failed, repeated by the party that wrote the prose, with the same failure mode. Forbidding derived figures in prose — "5 of the 48 cells are null" is exactly the sentence a reader needs, and banning it pushes the arithmetic onto the reader while making the report worse. Asserting derived figures inside the verify step without emitting them — the number would then exist in code and in prose but in no committed artefact, breaking §7.5's traceability and leaving a reader unable to check it without running the code. Keeping verbatim-presence-anywhere and adding more figures to the tables — presence anywhere is precisely the weak match that let "20" through.
- **Reason:** §7.5's rule catches **invention** and not **miscounting**. Part 1 proved it: a hand-written "20 ineligible cells" passed a pre-commit audit verifying that every prose figure appears verbatim in a committed table, because "20" happened to appear in the tables as an unrelated figure; the true count was **5**. The generated tables were correct and the error was in prose assembled around them, so a wrong number built from correct-looking parts satisfied a check designed for fabricated ones. Emitting derived figures as cells removes the second class of figure entirely, and checking the **declared** cell removes the accidental match.
- **Affects:** §7.5 and §10.7.6; every report's renderer and audit; **Part 2 most of all**, whose funnel report will be dense with "*N* of *M*" statements. **Not applied retroactively to Part 3**, whose report is not reopened.
- **Falsifiable by:** A derived figure that cannot be expressed as a table cell, which would be a figure whose definition is not reproducible and should not be in prose either.

### A-159 — §10.6 is unaltered by v1.6, and the four shared rules that bind Part 2
- **Kind:** decision
- **Part:** 2
- **Date:** 2026-09-17
- **Status:** active
- **Decision:** Record that **no Part 2 metric, population, funnel step, counting unit or output changes in v1.6** — §10.6.1 through §10.6.6 stand exactly as v1.5 wrote them — and state at §10.6's head which shared rules do bind Part 2: **§7.5's derived-figure rule** (A-158), **§10.7.5's per-dimension constancy rule** (A-154), **§10.7.7's criterion-replacement rule** (A-156) and **§10.5.1's bias-direction rule** (A-157). Record equally that **observation-window eligibility (A-153) and the window-remaining columns do not reach Part 2**, because its funnel is a **whole-window presence** metric — a user either has the event somewhere in the range or does not — with the proviso that a future time-boxed step, "started a level within *N* days of first event", would bring both into scope.
- **Alternatives rejected:** Saying nothing and letting the Part 2 session infer it — a session that has to derive "nothing changed for me" from a version it was not present for will either re-derive the whole section or miss one of the four rules that did change. Revisiting §10.6 in light of Part 1's findings anyway — Part 1 raised nothing that bears on a progression funnel over all 15,175 users, and reopening a specification with no defect to fix invites drift. Folding the four binding rules into §10.6 itself — they are shared rules and belong where every part reads them; duplicating them would create two copies to drift apart.
- **Reason:** The most expensive thing an amendment pass can leave behind is uncertainty about whether it applied to the work that has not started yet. Stating the boundary in both directions — what changed around Part 2 and what did not reach it — costs a paragraph and removes that entirely.
- **Affects:** §10.6's head note; what the Part 2 session must read before building; nothing in Part 2's specified content.
- **Falsifiable by:** Part 2 adding a time-boxed funnel step, which brings A-153 into scope by this entry's own proviso.

---

## Part 2 build session — decisions taken before the first query (2026-09-20)

Every entry in this block was written and committed **before the first Part 2 query
executed**, so that each call that shapes a number demonstrably predates the number.
IDs allocated by re-reading this file immediately before appending, per A-083: the
highest heading present was A-159.

One of the fifteen is a `challenge`. It is not a reason to stop — it is an ambiguity in
`ARCHITECTURE.md` that has three faithful readings and no stated adjudication, so the
reading used was **directed by the project author** and is recorded as directed rather
than chosen. That is A-095's precedent, followed by A-134, A-135 and A-136: an
implementation session that holds the numbers does not get to settle a gap in the
specification, even when its preferred answer is the better one.

### A-160 — Part 2 runs on the `bq` CLI through its own runner and ledger, with the pair total read from Part 1's ledger
- **Kind:** decision
- **Part:** 2
- **Date:** 2026-09-20
- **Status:** active
- **Decision:** Execute every Part 2 query through the `bq` CLI exactly as A-087 and A-131 did, from this session's own `src/part2_funnel/run_query.sh` and `src/part2_funnel/budget.sh`, accumulating into `outputs/tables/part2_budget_ledger.csv` under §10.1's ceilings of **4 GiB** per query, **20 GiB** per build session and **40 GiB** across both. Seed the pair figure by **reading the committed `outputs/tables/part1_budget_ledger.csv` at run time**, not by hardcoding Part 1's 4,604,297,216 bytes, so that `remaining_both_sessions_bytes` is derived from the artefact rather than from a literal. Install nothing, and leave `.venv/`, `requirements.txt` and `requirements.lock.txt` byte-for-byte unmodified.
- **Alternatives rejected:** Invoking `src/part1_retention/run_query.sh` and `budget.sh` in place — §8 forbids this session the other build session's paths, and A-131 set the precedent when Part 1 declined `src/recon/**` for exactly that reason; Part 1's `budget.sh` also computes the pair remainder as `40 GiB − its own running total`, which is right only for the session that goes first. Hardcoding Part 1's total as a constant — it is correct today and silently wrong the moment Part 1's ledger is corrected, and a budget figure that cannot follow its own source is the kind of number this project exists not to publish. Starting the pair total at zero — Part 2 would then believe it had 40 GiB when it has **35.71 GiB**, which is precisely what A-094 refused when it seeded the recon ledger with the two pre-session console queries rather than starting clean. Installing `google-cloud-bigquery` into `.venv` — A-127 permits an addition only if resolution leaves every existing pin unchanged, and A-087 names using a tool outside the project environment as the **preferred pattern** rather than the exception.
- **Reason:** The pattern is right and the arithmetic is session-dependent, so the pattern is re-implemented under this session's own path with the one number that differs taken from the committed record instead of from memory. That keeps §8's path list and §10.1's current ceilings both satisfied without editing anything a completed part owns, and it keeps Part 3's clean-checkout guarantee — the thing A-087 was protecting — untouched.
- **Affects:** `src/part2_funnel/budget.sh` and `run_query.sh`; every row of `outputs/tables/part2_budget_ledger.csv`; which halt conditions can fire; the honesty of the pair-ceiling figure this session reports.
- **Falsifiable by:** A Part 2 query that cannot be expressed through `bq`. None is expected: all four are a single `SELECT` returning at most a few dozen rows.

### A-161 — The query cache is disabled on every Part 2 query
- **Kind:** decision
- **Part:** 2
- **Date:** 2026-09-20
- **Status:** active
- **Decision:** Pass `--nouse_cache` on every Part 2 query, as A-089 did for the recon and A-132 for Part 1.
- **Alternatives rejected:** Leaving the cache at `bq`'s default — a cache hit bills zero bytes, and A-126 replaced A-085's tolerance band with a **prediction**: billed must equal `max(10 MiB, ceil(estimate → MiB))` to within 1 MiB or the session halts. A zero-billed cache hit misses that prediction by the whole prediction, so the cache would halt the session on a query that was entirely correct, and the only remedies available at that point — widening the band or raising a ceiling — are both forbidden. Disabling it only on re-runs — whether a query hits cache is a property of execution history rather than of the query, so the halt condition would depend on what happened to have been run before.
- **Reason:** The halt rule exists to stop the session when the cost model is wrong, and it must not fire when the cost model is right. Paying the bytes again costs a rounding error against a 20 GiB ceiling; a false halt costs the deliverable.
- **Affects:** Every Part 2 ledger row and every `.meta.json` sidecar; whether the halt rule is meaningful at all; the honesty of the session total.
- **Falsifiable by:** Not applicable — the alternative produces a halt on correct queries.

### A-162 — Raw query results are numbered by execution order, rendered report tables by report order
- **Kind:** decision
- **Part:** 2
- **Date:** 2026-09-20
- **Status:** active
- **Decision:** Write each query's result to `outputs/tables/part2_qNN_<purpose>.csv` with a `part2_qNN_<purpose>.meta.json` provenance sidecar, where `NN` is the SQL file's number and therefore its execution order (§7.2); write the rendered report tables to `outputs/tables/part2_NN_<name>.csv`, where `NN` is the order the table appears in the report; and keep the two files whose names §7.5 and §10.1 fix literally at those names — `outputs/tables/part2_report_figures.csv` and `outputs/tables/part2_budget_ledger.csv`.
- **Alternatives rejected:** One file per query, doubling as the report table — the Wilson intervals, the n<30 suppression and the derived-figure register all belong to Python (§7.3, §10.5.3, §7.5), so a rendered table is a different artefact from a query result, and collapsing them would attach a provenance sidecar describing a scan to a file containing arithmetic that scan did not do. Rendering in place over the query result — it destroys the artefact the sidecar describes, so a reader could no longer check the rendering against its input. Numbering the raw results in report order — report order is not fixed until the report is written, while §7.2 fixes the SQL number as execution order on the day the file is created. A different convention from Part 1's — a reader scanning `outputs/tables/` meets both parts in one listing, and two naming schemes for the same two kinds of artefact would read as carelessness.
- **Reason:** §7.2 numbers outputs by report order and numbers SQL by execution order, and Part 2 has both kinds of artefact, exactly as Part 1 did. A-133 settled this for Part 1 and the reasoning is unchanged; following it rather than re-deriving it keeps the repository legible across parts.
- **Affects:** Every file under `outputs/tables/part2_*`; what a reader opens to check a rendered rate against the counts it came from; §10.1's provenance requirement.
- **Falsifiable by:** Not applicable — this is a naming convention, chosen so the two required numbering schemes do not collide.

### A-163 — The Wilson interval is re-implemented under Part 2's own path, with the constant derived rather than written down
- **Kind:** decision
- **Part:** 2
- **Date:** 2026-09-20
- **Status:** active
- **Decision:** Implement §10.5.3's 95% Wilson score interval and its n<30 suppression rule in `src/part2_funnel/wilson.py`, a second copy of the logic A-139 fixed for Part 1, rather than importing `src/part1_retention/wilson.py`; and in both copies **derive** the constant as `statistics.NormalDist().inv_cdf(0.975)` rather than writing a literal, so that two files cannot hold two different numbers. Name the duplication in a comment at the head of the file so it does not read as an oversight.
- **Alternatives rejected:** Importing Part 1's module — §8 lists the other build session's paths under what neither build session may touch, and while importing is reading rather than writing, it makes a completed and reported part a runtime dependency of a later one, so a change to Part 1's tree would break Part 2 and a reader could no longer run either part from its own directory. Promoting the module to a shared `src/common/` — §8 grants no such path to either build session, and creating one is a specification change this session may not make; it is worth raising with the architecture session if a third part ever needs it. Copying the file and hardcoding `1.959963984540054` in the copy — two literals in two files is the drift A-139's single-definition rule exists to prevent, and the value is one unit in the last place from the exact double anyway. Writing `1.96` — it is not the 97.5th percentile, and at these denominators the difference shows in the second decimal place §10.7.6 prints.
- **Reason:** §8's path separation is worth more than the twenty lines it costs, and the duplication is only dangerous if the two copies can disagree. Deriving the constant from the standard library in both removes that possibility entirely: the files are two, the number is one, and neither can be edited into a different value without the other following.
- **Affects:** `src/part2_funnel/wilson.py`; every interval in Part 2; the segment table, where the 200-user floor still leaves cells that the n<30 rule can bite; the verification assertion that no rate anywhere sits on a denominator below 30.
- **Falsifiable by:** The architecture session granting a shared module path to both build sessions, which would make one copy correct and this entry historical.

### A-164 — CHALLENGE: §10.6.5 requires the `level_end` reconciliation at user level but fixes only the event-level arithmetic
- **Kind:** challenge
- **Part:** 2
- **Date:** 2026-09-20
- **Status:** active
- **Decision:** Raise for the architecture session that §10.6.5 requires the `level_end` reconciliation "at both event and user level" and states a **1.0%** trigger, but fixes only the event-level arithmetic — 349,729 `level_end_quickplay` events against 191,088 `level_complete_quickplay` plus 137,035 `level_fail_quickplay` = 328,123, a shortfall of 21,606 events or **6.18%**. That formula does not translate to users, because a user who both completed and failed a level appears in both outcome counts. Three readings are available. **(1) Ends with no outcome, over S2:** numerator the users holding `level_end_quickplay` and neither outcome event, denominator the **8,168** users with S2. **(2) The arithmetic parallel:** `(users(complete) + users(fail) − users(end)) / users(end)`, the direct translation of the event-level formula, which on this export returns **+47.1%** — an *excess* rather than a shortfall, arising entirely from double-counting — so a shortfall trigger tested against it can never fire for the reason it was written. **(3) Ends with no outcome, over the union:** reading 1's numerator over `|complete ∪ fail|`, a set the event-level figure never uses. This session did not choose between them: **reading 1 was directed by the project author**, and is the figure the 1.0% trigger is tested against; the components of all three are printed beside it so any of them can be reconstructed. §10.6.5 also does not say which of the three its 1.0% trigger applies to.
- **Alternatives rejected:** Choosing reading 2 on this session's own authority because it is the most literal translation of §10.6.5's own wording — a build session holding the counts is not the party that should settle what the specification means, which is A-095's finding and the reason §8 routes an internal inconsistency to the architecture session; and here the literal reading is also the one that cannot be tested against the stated trigger, which is a defect worth the architecture session seeing rather than a choice worth this session making. Reporting all three as co-equal figures — three reconciliation percentages with no rule for which governs is the structure §1.6 exists to prevent, several sections over. Recording the outcome as a `decision` entry of this session's — it would put this session's name on an adjudication it did not make and would hide that the document is silent here. Marking the user-level reconciliation unanswerable until the document is amended — §10.6.6 item 4 requires it, the ambiguity is worth one entry rather than a missing deliverable, and all three readings share a numerator or a denominator with the chosen one.
- **The reasoning recorded with the direction, since it is the architecture session's to weigh:** the event-level figure measures **ends that carry no outcome**, 21,606 of them. A user-level figure that measures anything else is not a reconciliation of it, and reading 2 measures something else — its +47.1% is a statement about how many users hold both outcomes, not about ends without one. Reading 3 shares the right numerator but divides by a population the event-level figure never touches.
- **Recorded as a fact about the export regardless of which reading governs:** 5,676 users with `level_complete_quickplay` plus 6,343 with `level_fail_quickplay` is **12,019** against **8,168** users with `level_end_quickplay`, so **at least 3,851 users hold both a complete and a fail**. That is a lower bound — it assumes every user with an outcome also has an end — and it is worth having in the record because it is the quantity that makes reading 2 return an excess.
- **Affects:** `sql/31_part2_progression_matrix_and_funnel.sql`; `outputs/tables/part2_07_level_end_reconciliation.csv`; whether §10.6.5's 1.0% trigger fires at user level; §10.6.5, which should say what the user-level comparison is and which reading its trigger applies to.
- **Falsifiable by:** The architecture session judging that the user-level reconciliation was always meant as reading 2 and that its trigger was meant to catch an excess rather than a shortfall — which would make this entry the record of a resolved ambiguity, and would change which number §10.6.5's trigger is tested against.

### A-165 — Derived figures are emitted as cells, report tables are generated and regenerated, and the audit is proved able to fail
- **Kind:** decision
- **Part:** 2
- **Date:** 2026-09-20
- **Status:** active
- **Decision:** Implement §7.5's quoted/derived rule and A-158 as three mechanisms, built and exercised **before any report prose exists**. **(1)** Every figure in prose has a row in `outputs/tables/part2_report_figures.csv` carrying `figure_id`, `kind` (`quoted` or `derived`), `value_display`, `value_num`, `unit`, a one-line `definition`, `source_tables` and `source_cells` as `file:column:rowkey` locators; a `quoted` row's value is **read out of its declared cell** by the renderer rather than retyped, and a `derived` row **is** the committed cell the prose quotes. **(2)** Prose figures carry an invisible `<!--fig:id-->` tag and the audit requires the token immediately preceding it to equal that row's `value_display` exactly — the **declared cell**, never the corpus. **(3)** Report tables are not tagged cell by cell: `markdown.py` generates the markdown block from the committed CSV, the report embeds exactly that block between `<!--table:FILE-->` and `<!--/table-->`, and the audit **regenerates the block and asserts byte-equality**, so no cell in a report table is ever typed. Everything remaining in prose must be tagged or on an enumerated exemption list — dates and date ranges, `§` section numbers, `A-NNN` and version references, step labels, and a literal allowlist of thresholds quoted from `ARCHITECTURE.md` (1.0%, 5.0%, 25.0%, 0.5%, 1,000, 200, 30, 95%) — and the scanner reads **spelled-out quantities as well as numerals**. Finally, `audit.selftest()` runs on every render and asserts the audit **rejects** four fixtures — Part 1's exact failure replanted, an untagged numeral, a spelled-out quantity, and a tag naming a `figure_id` that does not exist — and **accepts** one correct fixture, raising if any case behaves otherwise.
- **Alternatives rejected:** Keeping §7.5's pre-v1.6 rule that every prose figure appear verbatim somewhere in a committed table — that is the check Part 1's "20 ineligible cells" passed against a true count of 5, because "20" occurred in the tables as an unrelated figure; A-158 records why presence-anywhere is the weak match. A second-pass recount before committing — the same party rechecking its own prose with the same method, which is the failure repeated. Forbidding derived figures in prose — "5 of the 48 cells are null" is exactly the sentence a reader needs, and banning it pushes the arithmetic onto the reader. Asserting derived figures inside `verify.py` without emitting them — the number would exist in code and in prose but in no committed artefact, so a reader could not check it without running the code. Tagging table cells individually — a funnel report's tables carry hundreds of cells, the tags would swamp the source, and generating the block is strictly stronger anyway because it removes typing rather than checking it. Scanning digits only — "twenty" would have dodged the scanner, and a spelled-out wrong count is the same defect in words. Shipping the audit without a negative test — an audit that has never been observed to fail is an assertion, and Part 1's had never been observed to fail either.
- **Reason:** §7.5's old rule catches invention and not miscounting, and this report will be dense with the shape of figure that miscounts — step-to-step drop-offs, out-of-order shares, "*N* of *M*" statements, cross-table percentages. The declared-cell check removes the accidental match; generating tables removes the typed cell; the spelled-out scanner removes the obvious dodge; and the self-test is what distinguishes machinery that works from machinery that is merely present. The acceptance fixture is part of that: an audit that rejected everything would satisfy the four rejections alone.
- **Affects:** `src/part2_funnel/report_figures.py`, `markdown.py` and `audit.py`; `outputs/tables/part2_report_figures.csv`; every figure in `reports/part2_progression_funnel.md`; what a reviewer has to trust rather than check.
- **Falsifiable by:** A derived figure that cannot be expressed as a table cell — which would be a figure whose definition is not reproducible, and which should not be in prose either.

### A-166 — De-duplication runs in every base CTE, so the regenerated event counts diverge from §10.6.5's by exactly the duplicate count
- **Kind:** decision
- **Part:** 2
- **Date:** 2026-09-20
- **Status:** active
- **Decision:** Implement §10.7.4's de-duplication as a `GROUP BY user_pseudo_id, event_name, event_timestamp` in the base CTE of every Part 2 query, taking `MIN()` of any further field the query reads, exactly as A-138 fixed it for Part 1. Record in advance the consequence for §10.6.6 item 3, which requires the diagnostic table "regenerated rather than transcribed": §10.6.5's event counts are the recon's **raw** figures and the regenerated ones are **deduped**, so the two will differ, while **distinct-user counts must match exactly** because a duplicate row carries the same user and the same event name as its twin. Assert both halves in `verify.py`: every event's user count equals the recon's, every event's deduped count is at or below the recon's, and the total difference summed across all 37 event names equals exactly the measured duplicate count.
- **Alternatives rejected:** Regenerating the diagnostic table on the raw non-deduped basis so its numbers match §10.6.5's table — §10.7.4 says de-duplicate "before any count, in both parts", with no exception for a table that would look tidier without it, and matching the document's numbers by disobeying the document's rule is the wrong trade in both directions. Skipping de-duplication in the funnel query on the grounds that per-user presence is invariant under it — true, and irrelevant: A-138 already answered this, a rule applied only where it changes the answer "is not a rule, it is a result". Reporting only the deduped figures without the reconciliation — the difference is small and completely explainable, and an unexplained discrepancy against the specification's own table is exactly what a reader notices first. `SELECT DISTINCT` over the three key columns plus others — that de-duplicates on a wider tuple than §10.7.4's natural key, so a duplicated row carrying a different value in a fourth column would survive as two rows.
- **Reason:** The divergence is predictable, bounded and fully attributable before any query runs, which is the best time to say so. Predicting it in advance converts what would otherwise look like a discrepancy into a check: if the user counts do not match exactly, or if the event-count differences do not sum to the duplicate total, something is wrong with this implementation rather than with the export.
- **Affects:** The base CTE of `sql/30`–`33`; `outputs/tables/part2_06_diagnostic_events.csv` and `part2_07_level_end_reconciliation.csv`; the event-level shortfall percentage, which moves slightly from §10.6.5's 6.18%; the verification identities.
- **Falsifiable by:** The user counts disagreeing with the recon's, or the event-count differences failing to sum to the duplicate total — either of which is a defect in this implementation, reported rather than absorbed.

### A-167 — The re-scope figures are quoted from the recon's committed file and never re-counted, and the two 27s are different quantities
- **Kind:** decision
- **Part:** 2
- **Date:** 2026-09-20
- **Status:** active
- **Decision:** Take §10.6.1's required re-scope figures — **27** revenue-positive purchase events from **27** users, **0.178%** of the 15,175-user denominator against a **0.5%** bar and 1,000-event bar, with **24** of the 27 carrying a positive `event_value_in_usd` and all 27 a positive `price`, and `event_value_in_usd` absent from **15 of the 114** shards — from the recon's committed `outputs/tables/recon_05_revenue_population.csv` and `recon_01_column_inventory.csv`, mirrored into `outputs/tables/part2_02_data_handling.csv` with their source named, and **never recount them**. Record that the diagnostic table's `in_app_purchase` row **is** regenerated, because the count of `in_app_purchase` events is a different quantity from the count of revenue-positive purchase events, and state that distinction wherever both appear so the two 27s are not read as one number counted twice.
- **Alternatives rejected:** Recomputing the revenue-positive counts in a Part 2 query — §10.3 evaluates its rule **once**, from item 9's committed result file, and A-130 rejected re-running the count on `price` alone for a cleaner number on exactly these grounds: it would be re-counting after seeing the verdict, which A-081's evaluate-once rule forbids, and it cannot change the outcome. Presenting 27 as an exact count — §10.6.1 and A-130 require it as a **lower bound**, because `event_value_in_usd` is absent from 15 shards; presenting a floor as a census is the small overclaim a reader who knows this dataset catches first. Quoting the figures in prose without mirroring them into a `part2_*` table — §10.6.6 item 6 puts the re-scope figures in Part 2's own data-handling record, and a figure whose only home is another session's file is one a reader has to go looking for. Suppressing the `in_app_purchase` diagnostic row because 27 is small — §10.6.5 names it as one of the seven diagnostics and requires the table regenerated; omitting the row would hide the very coverage figure the re-scope rests on.
- **Reason:** The rule that decided Part 2's scope must not be re-evaluated by the session whose scope it decided, and the cheapest way to guarantee that is to spend no bytes on it at all. The two 27s coinciding is an accident of this export — every `in_app_purchase` event happens to carry a positive `price` — and an accident that makes two different quantities look like one is worth naming before it is relied on.
- **Affects:** `outputs/tables/part2_02_data_handling.csv`; the re-scope statement at the head of the report (§10.7.2); the diagnostic events table; the bytes not spent.
- **Falsifiable by:** The regenerated `in_app_purchase` diagnostic count differing from 27 — which would mean a duplicate row among the 27 and would be reported as a finding, without reopening §10.3's rule, whose thresholds 27 misses by 37× and 2.8×.

### A-168 — The traffic-source descriptive line is quoted from the recon's field profiles, not re-derived
- **Kind:** decision
- **Part:** 2
- **Date:** 2026-09-20
- **Status:** active
- **Decision:** Satisfy §10.7.5's requirement that traffic source be "reported once, as a single descriptive line stating the concentration, to document why it is not segmented" by quoting the concentration figures from the recon's committed `outputs/tables/recon_07_field_profiles.csv` — `traffic_source.name`, `.medium` and `.source` at **99.91%**, **99.79%** and **99.39%** in two buckets, one a placeholder in each case — rather than re-deriving them, following the precedent Part 1's report set in its §6.
- **Alternatives rejected:** Re-deriving the three fields' profiles in a Part 2 query — it would cost bytes to re-establish a fact whose only use is to document that a dimension is **not** used, and §10.1's column rule says a query that reads a column no item asks about is a defect. Omitting the line because no metric is segmented by traffic source — §10.7.5 requires it precisely so that the absence is documented rather than silent, on the same principle as §2.2's "a check that is only mentioned when it fails is not a check". Restating it without naming its source file — a figure whose provenance is not on the page is one a reader cannot check.
- **Reason:** The recon established these profiles in a scan that has already been paid for, they are committed and citable, and nothing about them changes with Part 2's population — they are properties of the event rows, not of a cohort. Part 1 resolved this the same way and consistency between the two reports is worth more than a second measurement of the same constant.
- **Affects:** `outputs/tables/part2_02_data_handling.csv`; the report's segmentation section; roughly 150 MiB not spent.
- **Falsifiable by:** The architecture session ruling that each part must derive its own field profiles, which would make both parts' reports quote a figure they did not compute and would need §10.7.5 to say so.

### A-169 — The per-dimension constancy triggers are applied in the renderer, never by editing SQL
- **Kind:** decision
- **Part:** 2
- **Date:** 2026-09-20
- **Status:** active
- **Decision:** Compute the funnel by segment for **all five** permitted dimensions unconditionally in `sql/33_part2_funnel_by_segment.sql`, and apply §10.7.5's per-dimension triggers as A-154 generalised them — caveat above **5.0%**, drop above **25.0%** — in the rendering layer, from the constancy shares `sql/32_part2_segment_constancy.sql` measures. No query text depends on a number any query produced. A dropped dimension still has its share reported in `outputs/tables/part2_08_segment_constancy.csv`, because that is what documents the drop.
- **Alternatives rejected:** Running query 32, reading the shares, and then writing query 33 over only the surviving dimensions — it is the obvious ordering and it makes the committed SQL a function of results this session had already seen, which is the appearance §10.1's whole separation exists to avoid, even where the rule being applied is mechanical. Computing only `geo.country`'s share, as v1.5's §10.7.5 had it — A-154 supersedes that and requires every attributed dimension. Applying the triggers to Part 1's measured shares — Part 1 measured **1.62%** and **1.97%** on its 4,319-user install population, and Part 2's population is all **15,175** including the 10,856 pre-window installs, whose longer observed lives make a materially higher share plausible; the shares are not transferable and the triggers are evaluated on this part's own population. Dropping a dimension pre-emptively because version drift is expected — dropping a permitted dimension is as much an unauthorised decision as keeping a bad one (A-136's finding).
- **Reason:** A rule fixed in advance and applied mechanically is a rule; the same rule applied by rewriting a query after seeing its input is indistinguishable, from outside, from having chosen the dimensions. Keeping the SQL constant costs one query's worth of columns on a dimension that might be dropped, and buys a query file whose text demonstrably predates every number in it.
- **Affects:** `sql/32` and `sql/33`; `outputs/tables/part2_08_segment_constancy.csv` and `part2_09_funnel_by_segment.csv`; which dimensions the report carries and which carry a caveat naming their share.
- **Falsifiable by:** A dimension crossing **25.0%**, which drops it by §10.7.5's own rule rather than by a new judgement — and which this entry's structure means costs bytes already spent.

### A-170 — Out-of-order shares are taken over the step's own raw population, with the alternatives printed
- **Kind:** decision
- **Part:** 2
- **Date:** 2026-09-20
- **Status:** active
- **Decision:** Read §10.6.4's "a share **above 1.0%** of the step's raw population" as the raw population of the step holding the violation — **8,168** for users with S2 but not S1, and **5,676** for users with S3 but not S2 — and test the 1.0% trigger against that. Print each count's share of the **15,175**-user population beside it so the two alternative readings are reconstructible, and print `s3_without_s1` alongside §10.6.4's two named cases so the full violation space is visible. Report all of them **whether or not** the trigger fires.
- **Alternatives rejected:** The predecessor step's raw population as the denominator — `|S2 ∧ ¬S1|` over S1's 10,166 — defensible as "the share of the step that was skipped", but "the step's raw population" most naturally names the step the clause is about, and this reading makes the trigger slightly harder to clear, which is the right direction for a reporting trigger. The whole 15,175-user population as the denominator — it makes every share smaller and the trigger correspondingly weaker, and it measures prevalence in the sample rather than in the step. Reporting the out-of-order counts only when the trigger fires — §10.6.4 says out-of-order users "are counted and reported" unconditionally and attaches only the *interpretation* to the 1.0% threshold; a check mentioned only when it fails is not a check (§2.2). Treating the missing `S3 ∧ ¬S1` case as a gap in §10.6.4 — it is not: a user with S3 and S2 but no S1 is already caught by `S2 ∧ ¬S1`, so the two named cases detect every out-of-order user; the third figure is printed for legibility, not to close a hole.
- **Reason:** §10.6.4's phrase has one natural referent and two arguable ones, and the cost of settling it wrongly is a trigger that fires on the wrong denominator. Printing all three denominators' shares makes the choice checkable rather than merely stated, and costs one column.
- **Affects:** `outputs/tables/part2_04_out_of_order.csv`; whether §10.6.4's 1.0% trigger fires and therefore whether a stated interpretation is required; the report's funnel section.
- **Falsifiable by:** The architecture session reading "the step's raw population" as the predecessor's, which would change the denominator and could change whether the trigger fires — and which the printed alternatives make a one-line correction rather than a re-run.

### A-171 — The SQL assertions guard the document's own literals, and a firing guard is an implementation defect
- **Kind:** decision
- **Part:** 2
- **Date:** 2026-09-20
- **Status:** active
- **Decision:** Guard `sql/31_part2_progression_matrix_and_funnel.sql` with an `ERROR()` that refuses to return a row unless the raw per-user step counts equal §10.6.3's stated figures exactly — **15,175 / 10,166 / 8,168 / 5,676** — and guard `sql/30_part2_population_and_vocabulary.sql` the same way on **5,700,000** rows and **15,175** distinct users (A-096, A-097). Record now, before either runs: **if a guard fires, that is a defect in this implementation and it stops the run — it is not evidence against the recon**, and the response is to report it rather than to adjust the assertion. Do **not** guard the duplicate count: A-124's own `Falsifiable by` makes a different figure "a finding about the source table rather than a reason to change the rule", so **207** is printed beside the measured count rather than enforced.
- **Alternatives rejected:** Checking the four figures in Python after the query returns — the bytes are already spent by then, and §10.6.3 gives the counts specifically "so the build session can check its own arithmetic against a known figure", which is a check worth having at the point the arithmetic happens. Leaving them unasserted because the recon already established them — A-079 makes the CSV the source of truth for every number including ones §10.6 quotes, and Part 1 recomputed rather than transcribed its population figures for the same reason (A-145). Asserting the duplicate count at 207 — it would halt the session on a fact about the export that A-124 explicitly classes as a finding. Asserting the deduped *event* counts against §10.6.5's table — they cannot match, by A-166.
- **Reason:** These four counts are invariant under the one transformation Part 2 applies before counting them: §10.7.4 removes exact duplicate rows, and a duplicate row carries the same user and event name as its twin, so distinct-user counts cannot move. That makes the assertion both safe and load-bearing — it can only fail if the query is wrong — and stating the consequence in advance removes the temptation, at the moment a guard fires, to read it as a surprising fact rather than as a bug. Part 1 wrote the same sentence about its eligibility guard in query 12 and did not have to use it.
- **Affects:** `sql/30` and `sql/31`; whether the run proceeds at all; the standing of every count downstream of those four.
- **Falsifiable by:** A guard firing — which is reported with both the expected and the observed figures, and diagnosed as an implementation defect before any other reading is entertained.

### A-172 — The non-quickplay progression track is measured as a labelled diagnostic and is never a funnel step
- **Kind:** decision
- **Part:** 2
- **Date:** 2026-09-20
- **Status:** active
- **Decision:** Carry `level_start` — the non-quickplay progression event, **74,417 events across 4,774 users** — as a fifth boolean flag in query 31's per-user presence matrix, **labelled a diagnostic and never a funnel step**, so that the number of users with no `level_start_quickplay` who nonetheless started a non-quickplay level is measured rather than speculated about. Report it in the "What this does not support" section (§10.7.2) with the two user-property figures that point the same way: `plays_progressive` covers **4,585** users against `plays_quickplay`'s **3,548** (A-109's committed `recon_09_user_properties.csv`), so the mode the funnel does not cover is the **larger** of the two. **§10.6.3's four steps are untouched.** The flag costs **no additional bytes**: it reads `event_name`, which query 31 already scans for S1, S2 and S3.
- **Alternatives rejected:** Adding `level_start`, `level_end`, `level_complete` and `level_fail` as a second funnel or as alternative steps — §10.6.3 fixes the four steps and this session may not change them; A-120 chose the `_quickplay` family and the choice is not reopened here. Substituting `level_start` for S1, or defining S1 as either event — that is redefining a step, which §10.6.3 forbids and which would also break the raw counts §10.6.3 gives this session to check against. Not measuring it, on the grounds that §10.6.3 does not ask — the question "did the 5,009 users without S1 simply play the other mode" is the first one a reader who knows this export asks, the measurement costs nothing, and §10.7.2 requires the negative-results section to state what the figures are not about. Acknowledging the parallel track in prose without measuring it — an acknowledged limitation whose size is unknown is weaker than a measured one, and the measurement was free.
- **Reason:** The funnel's S1 rate of 66.99% invites the reading that a third of the sample never played, and that reading is wrong to the extent that users progressed in the mode the funnel does not cover. The honest response is neither to change the steps nor to hedge the sentence, but to bound it: report exactly how many of the users outside S1 started a non-quickplay level, and let the number carry the caveat. Measuring it beats acknowledging it, and it changes no definition.
- **Affects:** `sql/31_part2_progression_matrix_and_funnel.sql`, whose matrix is over five events rather than four; `outputs/tables/part2_05_progression_matrix.csv`; the report's "What this does not support" section; nothing in any funnel step, rate, denominator or interval.
- **Falsifiable by:** The overlap turning out to be negligible — which would mean the users outside S1 genuinely did not play, strengthen the funnel's reading, and still be worth reporting as the measurement that established it.

### A-173 — The funnel table carries two rates per step, each with its own denominator and interval
- **Kind:** decision
- **Part:** 2
- **Date:** 2026-09-20
- **Status:** active
- **Decision:** Report two rates against every funnel step, each with the denominator printed beside it (§10.7.6) and a 95% Wilson interval (§10.6.4): the **cumulative share of S0**, which is §10.6.3's own "Share of 15,175" column, computed on the strict population; and the **step-to-step conversion** from the previous step's strict population, which is what §10.6.4 requires. S0's step-to-step cell has no predecessor and is printed as an **explicit null**, never as 100%.
- **Alternatives rejected:** Step-to-step conversion alone — §10.6.3's table states shares of 15,175 and a reader will compare the report against it, so omitting the cumulative column would make the two disagree in shape for no reason. Cumulative share alone — §10.6.4 requires step-to-step conversion on the strict population in terms, and it is the quantity that says where users are actually lost. Printing S0's step-to-step as 100.00% — it would be a rate with no denominator and no meaning, and §10.5.5's principle that an unmeasurable cell is printed as an explicit null rather than a plausible number applies to any cell, not only to a window-bounded one. Reporting the cumulative share on the **raw** counts to match §10.6.3 exactly — the funnel is strict by §10.6.4, and a table mixing a strict count with a raw share would invite the reader to divide one by the other and get neither.
- **Reason:** The two rates answer different questions — how much of the sample reaches this step, and how much of the previous step survives it — and a funnel that reports only one of them makes the reader compute the other, which under §7.5 is exactly the arithmetic a report should not push onto its audience. Both are cheap, both come from counts already in the table, and each carries its own denominator so neither can be mistaken for the other.
- **Affects:** `outputs/tables/part2_03_funnel.csv`; `outputs/figures/part2_01_funnel.png`; the funnel section of the report; the verification that every rate has a denominator and every point estimate lies inside its interval.
- **Falsifiable by:** Not applicable — both quantities are defined by §10.6.3 and §10.6.4 respectively, and this entry settles only that both are printed.

### A-174 — The segment floor is evaluated once, on S0
- **Kind:** decision
- **Part:** 2
- **Date:** 2026-09-20
- **Status:** active
- **Decision:** Evaluate §10.7.5's "**≥ 200 users** at S0 (of 15,175)" floor **once**, on each dimension's S0 population, so that segment membership and the single "Other (n segments)" row are identical across S1, S2 and S3 and the columns can be read across; then print each step's own denominator inside each segment, with §10.5.3's n<30 suppression applying cell by cell. Attribute a user's segment from their **earliest event row**, ties broken by lowest `event_timestamp` then alphabetically lowest `event_name` (§10.7.5), after the A-166 de-duplication. Name in the table's own caption what earliest-event attribution measures, as A-154 requires: `app_info.version` means **version at install**, `device.language` means **language at first observed event**.
- **Alternatives rejected:** Re-evaluating the floor at each step — a segment could then be named at S1 and fall into "Other" at S3, so the columns of one table would describe three different partitions and could not be read across, and the "Other" row would change meaning between columns while keeping its name. This is A-140's reasoning for Part 1, and the only thing that differs here is the number. Dropping sub-floor segments instead of pooling them — §10.7.5 forbids it, and it silently changes the denominator so the shares no longer sum. Attributing by the modal value across a user's events — defensible, but it needs a tie rule of its own and diverges from the single deterministic rule §10.7.5 fixes for both parts. Omitting the caption note because §10.7.5's attribution rule is stated in the report's methods — A-154 requires it in the table's **own** caption, because a committed table is read on its own and a figure generated from it is screenshotted on its own.
- **Reason:** A segment table is read across its columns, so the partition has to be stable across them; the floor is about whether a segment is worth printing at all, which is a property of the population rather than of a step. The per-cell suppression floor then does the step-specific work, which is what §10.5.3 is for. §10.7.5's own arithmetic sets the number: S3 retains 37.40%, so 200 at entry leaves about 75 at the last step.
- **Affects:** `sql/33_part2_funnel_by_segment.sql`; `outputs/tables/part2_09_funnel_by_segment.csv`; which segments are named and which fall into "Other"; the verification that segment counts sum to 15,175 at S0 for every dimension.
- **Falsifiable by:** A segment clearing 200 at S0 but falling below 30 at S3, which would print a named row with a suppressed final cell — visible, correct under both rules, and worth reporting if it happens.

---

## Amendment pass — `ARCHITECTURE.md` v1.7 (2026-09-20) — final

Part 2's challenge answered and the README opener settled. IDs allocated by re-reading
this file per A-083: the highest heading present was A-174. §1–§6 untouched; Part 3's
freeze at v1.2 / `c6d72f83` stands; nothing already built is re-specified.

### A-175 — Reading 1 governs the user-level reconciliation, and a firing trigger obliges five statements
- **Kind:** supersedes A-121
- **Part:** 2
- **Date:** 2026-09-20
- **Status:** active
- **Supersedes scope:** the `Decision` field of A-121, in respect of the `level_end` reconciliation only — which user-level figure it means, and what a firing trigger requires. Its strict-funnel rule, its raw-beside-strict requirement and its out-of-order 1.0% trigger stand unchanged. **Answers A-164.**
- **Decision:** Settle the user-level reconciliation as **reading 1**: users holding `level_end_quickplay` and **neither** outcome, over the users with S2 — **202 of 8,168 = 2.47%** on this export — and apply the **1.0%** trigger to that figure and to nothing else. Specify what a firing trigger obliges: the report must state **(1)** the asymmetry and its direction in counts both ways, with the percentage identified as its magnitude rather than the finding; **(2)** the components of all three readings, so any can be rebuilt; **(3)** the candidate explanations the export cannot distinguish between — abandonment mid-attempt, an unnamed outcome type, loss of the outcome event in the sample — and that the report does not choose among them; **(4)** that the step is not redefined and no funnel figure moves; **(5)** that the event-level and user-level shares are two views of one population. It may **not** conclude a cause, a data-quality verdict on the export, an estimate of how many users "really" completed or failed, or any correction to any count. Below the trigger, the reconciliation is printed in full and one sentence discharges it.
- **Alternatives rejected:** **Reading 2**, `(users(complete) + users(fail) − users(end)) / users(end)`, the literal translation of the event-level formula — rejected because it measures how many users hold **both** outcomes rather than how many ends carry none, so its sign is governed by the overlap rather than the gap. With **4,052** both-holders on this export it returns an **excess of 47.15%**, and the defect is structural rather than local: any overlap at all turns the statistic positive, so a shortfall trigger tested against it can never fire for the reason it was written. **Reading 3**, reading 1's numerator over the users with either outcome — rejected on a sharper ground than "a population the event figure never uses": its numerator is the users with **neither** outcome and its denominator the users with **either**, so the two sets are **disjoint** and the ratio is not a share of anything. Reporting all three as co-equal — three reconciliation percentages with no rule for which governs is the structure §1.6 exists to prevent. Leaving "a stated interpretation" unspecified, as v1.5 did — it handed the content of a required finding to the build session, which is the gap §10.7.7 exists to close elsewhere and which reappeared three sections away.
- **Reason:** The event-level figure measures **ends that carry no outcome**, and a user-level figure is a reconciliation *of it* only if it measures the same population at user grain. Reading 1 is that figure; the arithmetic closes against it and not against the alternatives — 7,967 users hold an outcome, exactly **1** of them has no end, and 7,966 + 202 = **8,168**, reading 1's denominator. On the obligations: the asymmetry is what the finding is about. Essentially every user with an outcome records the preceding end while 202 ends carry none, so whatever is happening affects ends and not outcomes — and a report that printed only 2.47% would have reported the magnitude of something without saying what.
- **Affects:** §10.6.5; which figure the trigger tests; what any future firing reconciliation must state. Part 2's report already discharges all five obligations, so this adds nothing to built work — it records the rule the build followed under direction.
- **Falsifiable by:** An export where no user holds both outcomes, which would make readings 1 and 2 coincide and the choice moot — it does not arise here, and the structural objection to reading 2 stands regardless.

### A-176 — The README opener becomes one sentence per analysis, with its population named
- **Kind:** supersedes A-032
- **Part:** project-wide
- **Date:** 2026-09-20
- **Status:** active — `Decision` field superseded by A-180 (closing limitation, cross-part ban) and by A-187 (opener-region contents: one link line)
- **Supersedes scope:** the `Decision` field of A-032 in full. Its reasoning — that a repository should lead with what a reader can act on rather than with "this repository contains" — is the reason this entry exists and is carried forward, not discarded.
- **Decision:** Replace the three-sentence opener with **exactly *n* + 2 sentences for *n* analyses**: a frame naming what the repository holds, **one sentence per analysis in repository order** stating the single most actionable thing that analysis supports **with its population named in the same sentence**, and one closing sentence naming the limitation that bounds every analysis. Constraints: every sentence names its population; **no Part 1 or Part 2 sentence is phrased as a recommendation**; **no cross-part inference** and no sentence whose subject spans two analyses; **quoted figures only, with derived figures barred from the opener entirely**; at most **45 words** per sentence; nothing a part's own negative-results section forbids.
- **Alternatives rejected:** Keeping three sentences and letting them be Part 3's — the repository's front page would then imply that Parts 1 and 2 also recommend something, which §10.5 and §10.6 forbid them from doing, so two thirds of the work would be misrepresented by its own opener. Three sentences averaged across all three analyses — an average of a recommendation and two findings is a sentence with no subject, and a PM could act on none of it. A one-sentence-per-part opener with no frame and no limitation — the frame is what stops a reader treating three separate analyses as one study, and the limitation is the thing a reader would otherwise assume away. Dropping the "actionable" requirement as unachievable across three parts — it is achievable once "actionable" is read correctly: what a reader can act on from Parts 1 and 2 is a figure **plus the population it does and does not describe**, which tells them what they may quote and of whom. An unbounded executive summary — long enough to hedge, and hedging is what it would fill with, which was A-032's original objection and still holds.
- **Reason:** The opener's job changed when the repository stopped holding one analysis. Fixing *n* + 2 keeps each analysis speaking for itself while still forcing each to have reached a single statement, which is what the three-sentence rule was really for. The population requirement is the anti-overclaim device the single-analysis version never needed: "classic D7 is 5.67%" and "classic D7 among users with an observed install event is 5.67%" are different claims, and only the second is true.
- **Affects:** §7.6; `README.md`'s opener, to be written next under this rule; §8's grant (A-177).
- **Falsifiable by:** A fourth analysis whose most actionable statement cannot be made in one sentence, which would need the rule widened for that part rather than abandoned.

### A-177 — The architecture session owns the README opener region
- **Kind:** supersedes A-118
- **Part:** project-wide
- **Date:** 2026-09-20
- **Status:** active
- **Supersedes scope:** the `Decision` field of A-118, now that its condition — all three analyses existing — is met. Its protection of the opener from every build session held throughout and is the reason this decision could be made at all.
- **Decision:** Grant the **architecture session** the `README.md` **opener region** — everything above the first `##` heading — and grant it to no other session; each part's `## Part N` section stays with that part's session. Record that §9's open question 8 is **closed, yes**. The grant is bound by §7.6's **quoted-figures-only** rule, which is what makes it safe for a session that has no renderer to emit derived figures.
- **Alternatives rejected:** Leaving the opener forbidden to everyone, as §8 stood before this pass — the rule that protected it through three builds would then prevent it ever being written. Giving it to a short-lived README session with its own runner — a fourth session and a fourth path list for five sentences, and it would face the same question of which analysis leads. Giving it to the last build session to finish — it makes the repository's most-read text the responsibility of whichever session happened to run last, which is exactly what A-118 was written to prevent. Permitting derived figures in the opener with an audit exemption — an exemption in the one place every reader looks is the worst possible place for one; requiring the part's renderer to emit the cell first costs nothing and keeps §7.5 whole.
- **Reason:** The architecture session is the only party with all three analyses in view, and A-118 reserved the decision for exactly this moment. The quoted-figures-only constraint is what lets the grant be narrow: the session writes prose and quotes cells, and any figure that does not already exist as a cell is a figure some part's renderer must emit first.
- **Affects:** §7.6, §8 and §9 question 8; who writes the opener; nothing in any committed report.
- **Falsifiable by:** Not applicable — the grant is a choice of owner, and the constraint that makes it safe is stated with it.

### A-178 — The architecture series ends at v1.7, and the amendment protocol does not expire
- **Kind:** decision
- **Part:** project-wide
- **Date:** 2026-09-20
- **Status:** active — `Decision` field superseded by A-181
- **Decision:** Record v1.7 as the last planned pass, with all three parts built, committed and pushed, the recon closed, and every challenge either build session raised — A-095, A-134, A-135, A-136, A-164 — answered in the document rather than in a build. Record the two things left open **by design**: §9's open question 7, whether BigQuery-derived outputs come under §7.5's byte-identity rule, which waits on a materialised-extract decision nothing now depends on; and the §7.6 opener itself, specified here and written next. Record that the §11 amendment protocol **does not expire**: a later change enters as a `challenge` or `finding`, the architecture session issues v1.8 in the four-field format, and **§1–§6 stay frozen** — Part 3's report cites `c6d72f83`, so reopening its pre-registration would invalidate a published result rather than improve one. Parts 1 and 2's specifications may be amended for a future part's benefit, but their **committed reports are not reopened to match**, and any such amendment says so explicitly.
- **Alternatives rejected:** Declaring the document closed outright — a closed document with no amendment path is one a future session will either ignore or fork, and the protocol costs nothing to leave standing. Saying nothing and letting the version history imply the end — a reader arriving at v1.7 cannot tell whether the series stopped deliberately or stalled, and the difference matters for whether they trust what is missing. Retroactively applying v1.6's and v1.7's rules to the completed reports — the derived-figure rule would have changed how Part 3 was audited and the opener rule changes prose that predates it, but reopening finished, cited work to match a later document is how a project loses the very traceability these rules exist to create.
- **Reason:** The freeze is the mechanism that made Part 3's pre-registration worth writing, and it only means anything if it survives the temptation to tidy. Stating where the series ends, what remains open on purpose, and how a genuine later change would enter is the last thing this document can do that a reader could not reconstruct from its history.
- **Affects:** §11's closing note; how any future session reads the absence of a v1.8; the standing of the three committed reports.
- **Falsifiable by:** A defect found in a built part that changes a published figure — which enters as a `challenge`, gets a v1.8, and is disclosed in the affected report as a correction rather than a silent edit.

---

## Amendment pass — `ARCHITECTURE.md` v1.8 (2026-09-21) — final

The §7.6 opener written, and the three rule defects that writing it exposed. IDs
allocated by re-reading this file per A-083: the highest heading present was A-178.
§1–§6 untouched; Part 3's freeze at v1.2 / `c6d72f83` stands; no committed report is
edited by this pass.

### A-179 — The README opener as written: figures, limitation, and two claims narrowed
- **Kind:** decision
- **Part:** project-wide
- **Date:** 2026-09-21
- **Status:** active
- **Decision:** Write the `README.md` opener region as five sentences under §7.6 as v1.8 amends it — a frame, one sentence each for Parts 1, 2 and 3 in repository order, and one closing limitation — quoting only committed cells: 4,319 and 15,175 from `part1_01_population_reconciliation.csv`; 5.67%, its 4.99–6.44 Wilson bounds and the 15 cohorts from `part1_04_classic_retention_pooled.csv` at `horizon_days=7`; 10,166 from `part2_03_funnel.csv` at `step=S1`; 80.12% and 69.64% from that file's `step_conversion_pct_display` at `step=S2` and `step=S3`; 1,955 from `part2_10_parallel_track.csv`; 0.82 pp and the 1.34–0.31 bootstrap bounds from `part3_06_primary_inference.csv`; 90,189 from `part3_02_srm.csv`; the recommendation text from `part3_11_decision.csv`; and 50,000 from `part2_report_figures.csv`. Nothing is computed.
- **Alternatives rejected — the limitation:** The **71.54% install-event gap**, which bounds Part 1 alone and is already carried inline as that sentence's population qualifier, where §7.6 wants a per-part caveat. **Part 3's unmeasurable exposure**, which bounds the magnitude but not the direction or the recommendation — dilution pushes the true effect on exposed players further from zero, so it makes the measured harm an understatement and *strengthens* "keep the gate at level 30"; sentence 4's "assigned players" is the ITT marker that guards the figure. The **50,000-row sampling cap** was chosen because it invalidates a whole class of statement — every absolute count in two of three analyses — rather than qualifying one estimate, and absolute counts are the easiest figures to lift from a table and the likeliest to be misread as traffic.
- **Alternatives rejected — the figures:** Part 2's **66.99% of all 15,175 users started a level**, its most quotable figure — rejected because Part 2's own §9.1 rules it out: the funnel covers only the `_quickplay` family, so 66.99% is a floor on "started playing" rather than a measure of it. The step conversions are conditional on already being inside the covered mode, so the coverage gap does not distort them, which is why sentence 3 is built from 80.12% and 69.64% instead. A synthesis sentence across parts — none of the three supports one, and the place it wanted to appear, between progression and gate placement, is exactly where the reach was.
- **Two claims narrowed in review, both worth recording:** **(1)** The frame first claimed that each analysis had "its definitions fixed and committed before its numbers existed". That is false, and Part 1's own section 8.2 records why: A-142 replaced the zone criterion after query 17's figures were visible. It is also false for Parts 1 and 2 more broadly — §10.5 and §10.6 were written by the architecture session holding the recon's counts, and §10.6.3 carries 10,166 / 8,168 / 5,676 as literals, so those parts were specified after a schema survey rather than pre-registered. The frame now claims pre-registration for **Part 3 only**, specification-after-survey for Parts 1 and 2, and recorded change for all three — which is verifiable from git and this file, and is the stronger claim because the rarest one is attached to the only analysis it holds for. "Independent" was also dropped: Parts 1 and 2 share a dataset and a population, and the word invites a reader to think otherwise. **(2)** Sentence 3 first said the quickplay mode was "not the game's larger one", which is wrong — see A-182. **(3)** Sentence 5 first closed with "only the shares within a stated population do", which asserts that shares measure the real player base. Nothing establishes that, and Part 1's report rules it out: its §8.3 records that the sampling fraction may vary by day and could affect rate comparisons, and its §8.4 asks for a sampling manifest because the method is undocumented. **The mechanism is a candidate, not an established fact**, and this entry was corrected in review to say so. Exactly 50,000 rows per shard is consistent with at least two methods the export does not distinguish: **random row sampling**, under which a user generating more events is likelier to appear at all, which would bias user-level shares toward engaged players; and **truncation by timestamp** — the first 50,000 events of each local day — under which users active early in the day are over-represented, with no clear direction for retention. A fixed row count does rule out deterministic **user**-level sampling, which would yield a variable number of rows per day. So a nameable direction exists **only under random row sampling**, and nothing here establishes which method was used. The sentence now states that no count measures the real player base **and** that whether the shares do depends on an undocumented sampling method. "Capped at 50,000" also became "of exactly 50,000": a cap asserts a truncation mechanism, and what the recon observed is a fixed count (A-096).
- **Reason:** The opener is where a reader's whole impression forms in seconds, and both narrowed claims were the kind that a reader checking one report would catch. Neither survived because a rule caught it; both survived to a review round and were caught there, which is the argument for the round.
- **Affects:** `README.md`'s opener region; nothing below its first `##` heading, which stays as each build session wrote it.
- **Falsifiable by:** A figure in the opener failing to match its cell on a re-run, which the §7.5 audit would catch.

### A-180 — §7.6's closing limitation names its scope, and the cross-part ban is scoped
- **Kind:** supersedes A-176
- **Part:** project-wide
- **Date:** 2026-09-21
- **Status:** active
- **Supersedes scope:** the `Decision` field of A-176, in respect of the closing-limitation requirement and the cross-part inference ban only. Its *n* + 2 structure, its population requirement, its no-recommendation rule for Parts 1 and 2, its quoted-figures-only rule and its 45-word cap stand unchanged.
- **Decision:** Require the closing sentence to be **the limitation that most constrains what a reader may quote, naming which analyses it bounds** — not "the limitation that bounds every analysis here". Scope the **cross-part inference ban to the per-analysis sentences**, since the closing sentence spans analyses by construction.
- **Alternatives rejected:** Keeping "every analysis" and choosing a limitation that spans all three — the only candidate is that no part carries monetization data, which is true of all three and invalidates no figure, so the opener would trade the limitation that voids a class of statement for one that merely bounds a class of question. Keeping "every analysis" and letting the drafted sentence quietly not meet it — the defect would then sit in the one artefact every reader reads. Keeping the unscoped cross-part ban and rewriting the closing sentence to avoid naming parts — "no count in this repository measures real traffic" is false for Part 3, which is not sampled.
- **Reason:** Both defects came from writing a rule for a repository that was being described rather than drafted against. The sampling cap bounds Parts 1 and 2 and not Part 3, and a requirement that forces a weaker limitation in order to span every part is optimising the wrong thing; naming the scope costs four words and keeps the strongest limitation. The ban was written for the per-analysis sentences and read as covering all of them, which made the section forbid the sentence it required.
- **Affects:** §7.6; the opener as written (A-179); any future opener under this rule.
- **Falsifiable by:** A repository whose parts share one dataset, where "every analysis" would be satisfiable and the scope clause redundant but harmless.

### A-181 — The correction protocol covers wrong interpretations, and false claims in table notes
- **Kind:** supersedes A-178
- **Part:** project-wide
- **Date:** 2026-09-21
- **Status:** active
- **Supersedes scope:** the `Decision` field of A-178, extending its correction protocol. Its record of where the series ends, its two-things-open note and its freeze on §1–§6 stand unchanged, as does the rule that a committed report is not reopened merely to match a later specification.
- **Decision:** Extend the protocol to cover, alongside a defect that changes a published figure: **a wrong interpretation drawn from correct figures**, and **a false claim in a committed table's note**. In each case the correction is made by **that part's own build session**, **disclosed in the report as a correction**, and **never edited silently**. The distinction §11's closing note now carries: whether the report is *behind* the document, in which case it stands, or *wrong on its own terms*, in which case it is corrected.
- **Alternatives rejected:** Leaving the protocol at figure defects — A-182's case shows the gap: both underlying counts are correct and the inference from them is not, so no figure audit could ever catch it and no rule required its correction. Treating a wrong interpretation as out of scope because no number changes — the interpretation is what a reader carries away, and a false one in a negative-results section is worse than a wrong figure in a table nobody reads. Correcting it from the architecture session — the report is the build session's under §8, and an architecture session editing a build session's prose would break the ownership that makes every other path grant meaningful. Handling it as a `challenge` — a challenge is a build session's instrument against a document it cannot edit, and the architecture session raising one against itself is a category error.
- **Reason:** A figure audit verifies that numbers trace to cells. It cannot verify that the sentence around them is true, and `part2_10_parallel_track.csv` shows a **table note** can carry a false claim that passes every check the project has. Extending the protocol to interpretations closes the widest remaining gap between "checkable" and "correct".
- **Affects:** §11's closing note; A-182's disposition; how any later defect in built work is handled.
- **Falsifiable by:** Not applicable — this widens a protocol rather than asserting a fact.

### A-182 — Part 2's comparative claim about mode size is wrong and is to be corrected
- **Kind:** decision
- **Part:** 2
- **Date:** 2026-09-21
- **Status:** active — the correction it directs was made by the Part 2 build session on 2026-09-22 and is recorded as done by A-184
- **Decision:** Record that Part 2's report §9.1 — "the mode this funnel does not cover is **the larger** of the two" — and the note on the `plays_quickplay` row of `outputs/tables/part2_10_parallel_track.csv` — "the mode the funnel DOES cover is the smaller of the two" — are **both wrong**. They rest on user-property counts of **4,585** `plays_progressive` against **3,548** `plays_quickplay`, but **10,166** users have an observed `level_start_quickplay` against **4,774** with a non-quickplay level start, so by observed play **quickplay is the larger mode** and the property undercounts quickplay participation by nearly threefold while its semantics are undocumented. **Both underlying counts are correct; only the inference drawn from them is wrong.** Under A-181 the correction belongs to the **Part 2 build session**, disclosed in the report as a correction and not edited silently. The claim was **dropped from the README opener** rather than repeated (A-179).
- **Alternatives rejected:** Repeating the claim in the opener because the report asserts it — the opener may not assert what a part's negative-results section rules out, and here the section itself is what is wrong, which is a stronger reason not to repeat it. Correcting the report from this session — it is the build session's path under §8 (A-181). Leaving it unrecorded because the opener no longer repeats it — the report is where a reader checking the opener would land, so silence would leave the opener correct and its source wrong. Treating the user properties as measuring something else that makes the claim true — possible, since their semantics are undocumented, but that is an argument for not drawing a comparative from them at all rather than for keeping this one.
- **Reason, recorded plainly:** the comparative entered Part 2's report and its table note **under the project author's direction**, and was endorsed twice by this session before being caught — once in the opener draft and once in the notes defending it. What caught it was checking the property count against observed level starts, which is the check that should have been run when the comparative was first written. A user property is not a participation measure unless something establishes that it is.
- **Affects:** Part 2's report §9.1 and `part2_10_parallel_track.csv`'s note, pending that session's correction; the opener's sentence 3, already narrowed; nothing in any figure.
- **Falsifiable by:** Documentation of `plays_quickplay`'s semantics showing it measures something the 10,166 figure does not contradict — which would make the comparative defensible on a stated basis rather than on an unexamined one.

### A-183 — Part 2's report claims the funnel's shares are what the sample supports
- **Kind:** decision
- **Part:** 2
- **Date:** 2026-09-22
- **Status:** active — the correction it directs was made by the Part 2 build session on 2026-09-22 and is recorded as done by A-185
- **Decision:** Record that Part 2's report §9.1 states "The funnel's **shares** are what the sample supports", which is a published overclaim: nothing establishes that a share computed on this extract transfers to the property's real population. It is inherited from §10.7.1, which until v1.8 ended a bullet with "rates within a cohort are the only quantities the sample supports" and has now been corrected to say that counts are ruled out and **rates are unestablished** pending the undocumented sampling method. Under A-181 the correction belongs to the **Part 2 build session**, disclosed in the report as a correction and not edited silently. The replacement claim available to it: counts are ruled out outright, and whether the funnel's shares transfer depends on a sampling method the export does not document.
- **Alternatives rejected:** Leaving it because §10.7.1 authorised it — the spec's error does not make the report's sentence true, and the report is the artefact a reader believes. Correcting it from this session — Part 2's report is its build session's path under §8 (A-181). Treating it as covered by A-182 — that entry is the mode-size comparative, a different claim in the same section, and two defects handed over as one invite a partial fix. Weakening it to "the funnel's shares are what the sample best supports" — a comparative hedge that still asserts support.
- **Reason:** A grep of both reports for this phrasing and its paraphrases found exactly one instance: Part 2 line 596. Part 1's report never inherited it — its three uses of "supports" are unrelated and hedged — which is worth recording, because it means the defect is one sentence rather than a pattern across the project. The claim matters more than its size: the funnel's shares are the entirety of what Part 2 reports, so a sentence asserting they are supported is asserting that the part's whole output transfers, which is the single largest unearned claim available to it.
- **Affects:** Part 2's report §9.1, pending that session's correction; nothing in any figure or table; §10.7.1, already corrected in v1.8.
- **Falsifiable by:** Documentation of the sampling method establishing that shares do transfer — which would make the sentence true on a stated basis rather than on an unexamined one.

### A-184 — Finding: A-182's mode-size comparative is corrected in Part 2's report and in both table notes
- **Kind:** finding
- **Part:** 2
- **Date:** 2026-09-22
- **Status:** active
- **Decision:** Record that the correction A-182 directs has been made by the Part 2 build session under A-181's protocol. `reports/part2_progression_funnel.md` §9.1 no longer claims that "the mode this funnel does not cover is the larger of the two"; it now states that the `plays_*` user properties **do not measure mode participation**, that **10,166** users have an observed `level_start_quickplay` against **4,774** with a non-quickplay level start so **by observed play quickplay is the larger mode**, and that the property undercounts observed quickplay participation by **2.9×** — emitted as the register row `quickplay_property_undercount_ratio` so the figure is quoted rather than asserted. The counts **4,585** and **3,548** are unchanged, because they were never wrong. The correction is disclosed **inline in §9.1** as a dated note naming what the passage previously claimed and why it was wrong, not only here.
- **Alternatives rejected:** Not applicable — this is an observation, recording work A-182 directed. Recorded because A-181 requires a correction to be disclosed rather than made silently, and an entry directing a correction is not evidence the correction happened.
- **Two things done beyond what A-182 names, disclosed rather than absorbed:** A-182 names the note on the `plays_quickplay` row of `outputs/tables/part2_10_parallel_track.csv`. The adjacent `plays_progressive` row carried the same inference in different words — "points the same way as the event counts" — so **both notes were corrected**, each carrying its own dated note recording its previous wording. Leaving a demonstrably misleading note in place while fixing its twin would satisfy A-182's letter and defeat A-181's purpose. Separately, the README's `## Part 2` section was searched for the claim and for paraphrases of it — on *larger*, *smaller*, *bigger*, *mode*, *plays_*, *progressive* and *quickplay* — and **carries neither the comparative nor any paraphrase**: its only reference to the parallel track states that 1,955 of 5,009 users started a level in a mode the funnel does not cover, which makes no comparative claim. Nothing in the README needed correcting, and that is recorded because A-182 asked for the answer either way.
- **On method, since this is the second time the same discipline would have caught it:** the note was fixed **in `src/part2_funnel/tables.py`, the renderer that generates it**, and the table regenerated — never by editing the CSV, which the next render would overwrite and which would break §7.5's byte-identity check. After regeneration **20 of the 22** committed Part 2 outputs are byte-identical to their committed versions; the two that changed are `part2_10_parallel_track.csv`, whose `metric`, `users` and `share` columns are themselves unchanged so that only the note text moved, and `part2_report_figures.csv`, which gained exactly one row. No published figure changed anywhere.
- **Reason:** A-182 records that the inference was endorsed twice before being caught, and what caught it was checking a user property against observed event counts. That check is now written into the report's own prose rather than left as something a future reader has to think of.
- **Affects:** `reports/part2_progression_funnel.md` §9.1; `outputs/tables/part2_10_parallel_track.csv`'s two property notes; `src/part2_funnel/tables.py` and `register.py`; A-182, whose Status line records this entry as the correction.
- **Falsifiable by:** Documentation of `plays_quickplay`'s semantics showing it measures something the 10,166 figure does not contradict — which A-182 already names, and which would reopen the comparative on a stated basis rather than restore the old sentence.

### A-185 — Finding: A-183's shares-are-supported overclaim is corrected in Part 2's report
- **Kind:** finding
- **Part:** 2
- **Date:** 2026-09-22
- **Status:** active
- **Decision:** Record that the correction A-183 directs has been made by the Part 2 build session under A-181's protocol. `reports/part2_progression_funnel.md` §9.1's "Real traffic, at any grain" bullet no longer ends "The funnel's **shares** are what the sample supports". It now states that **counts are ruled out outright and shares are not thereby established**, and that whether a share computed on this extract transfers to the property's real population **depends on a sampling method the export does not document** — the replacement claim A-183 makes available, implemented as written. The correction is disclosed **inline in §9.1** as a dated note giving the previous wording, why it was an overclaim, and where it was inherited from, not only here.
- **Alternatives rejected:** Not applicable — this is an observation, recording work A-183 directed.
- **What the inline note says, because the provenance is the point:** that the sentence asserted a transfer nothing establishes; that it was the largest unearned claim this part had available, since the funnel's shares are the entirety of what Part 2 reports, so asserting they are supported asserts that the whole of the part's output carries to the real population; and that the wording was inherited from §10.7.1, which until v1.8 ended a bullet with "rates within a cohort are the only quantities the sample supports". The note states plainly that **the specification's error did not make the report's sentence true** — the report is the artefact a reader believes, and it is corrected on its own terms rather than excused by where the phrasing came from.
- **Also checked, and reported either way:** the README's `## Part 2` section was searched for this claim and its paraphrases, on *support*, *share* and *rate*. Its only use of "support" is "this sample does not support a revenue analysis", which is a negative claim about revenue and is correct and unrelated. **Nothing in the README needed correcting.** No figure, table or cell changed for this correction: it is one bullet of prose, and every other committed Part 2 output is byte-identical after the regeneration A-184 records.
- **Reason:** A-183 records that a grep of both reports found exactly one instance of this phrasing, and that Part 1's report never inherited it. The defect was one sentence rather than a pattern, and one sentence is what was changed.
- **Affects:** `reports/part2_progression_funnel.md` §9.1; nothing in any figure or table; A-183, whose Status line records this entry as the correction.
- **Falsifiable by:** Documentation of the sampling method establishing that shares do transfer, which A-183 already names, and which would make the original sentence true on a stated basis rather than restore it on an unexamined one.

---

## Amendment pass — `ARCHITECTURE.md` v1.9 (2026-09-23)

A new deliverable specified before it is built: an interactive Tableau Public dashboard
over the three parts. IDs allocated by re-reading this file per A-083: the highest
heading present was A-185. §1–§6 untouched; no part, report or committed table reopened.

### A-186 — The dashboard recomputes nothing, reads thirteen named files, and is a snapshot of `5eb02fd`
- **Kind:** decision
- **Part:** project-wide
- **Date:** 2026-09-23
- **Status:** active — `Decision` field superseded by A-188 in respect of the source list and the measured-zero checks
- **Decision:** The Tableau Public dashboard is a presentation layer that **recomputes nothing**: every figure it shows is a committed cell, read from the full-precision column — `*_value` in Parts 1 and 2, `value` in Part 3's quantity tables, `rate_pp` in `part3_05` — and never from a `*_display` column, **except as tooltip text**: a display column may appear in a tooltip and nowhere else — never as a plotted coordinate, never as a mark's position, size or colour, and never inside a calculated field; no calculated field produces a number that is not in a cell, and no null is converted to zero. Its sources are **thirteen files, by name**: `part1_01_population_reconciliation.csv`, `part1_03_classic_retention_weekly.csv`, `part1_04_classic_retention_pooled.csv`, `part2_03_funnel.csv`, `part2_08_segment_constancy.csv`, `part2_09_funnel_by_segment.csv`, `part2_10_parallel_track.csv`, `part2_report_figures.csv`, `part3_02_srm.csv`, `part3_03_power.csv`, `part3_05_retention_rates.csv`, `part3_06_primary_inference.csv`, `part3_11_decision.csv`. **Status filter rule:** any table with a status column is filtered to `reported` before anything plots, on the status value rather than on nullness, with Part 2's two status columns each governing its own measure; ineligible cells never plot, and measured zeros always do — across the thirteen sources at `5eb02fd` there is exactly one, **W01 at D30** in `part1_03` (0 of 176). `part1_07_retention_by_segment.csv` holds three more reported D30 zeros — **Canada** (0 of 104), **Australia** (0 of 84) and **en-ca** (0 of 87) — but it is **not** a source; if it is ever added, each must plot at 0% with its interval whenever its dimension is selected. The workbook is **extracted from `outputs/tables/` at `5eb02fd`**, so it is a **snapshot that goes stale if any of those outputs change**; `dashboard/README.md` records the commit and each source's SHA-256 so staleness is detectable by checksum, and a stale workbook is re-extracted rather than patched. **No file from `data/` enters it.** Two consequences recorded with the decision: the ±1.00 pp band's edges are `part3_03_power.csv` → `action_threshold_pp` and its negation, which is the band's definition under §1.4 and §1.6 and the dashboard's **only** transformation; and Part 2's Wilson intervals appear **as tooltip text**, because its interval bounds exist only as display columns and have no full-precision twin.
- **Alternatives rejected:** Reading the raw query results (`part*_q*.csv`) — they are what the rendered tables were built from and may differ in shape or de-duplication, so the dashboard could disagree with the report while every figure traced to *a* file. Reading display columns for labels — they carry separators, rounding and the literal `NULL` in ineligible cells, so a label read from one can silently show text where a null belongs; formatting the value column in Tableau reproduces the display at no risk. Parsing Part 2's display bounds back to numbers to draw interval bars — it plots rounded strings, which is the one thing the column rule exists to forbid. **Omitting Part 2's intervals entirely**, as this entry's first draft did — it would show Part 1's uncertainty beside a Part 2 that looks exact, a worse misreading than any the tooltip exception risks; a tooltip neither reads a string as a number nor plots a `NULL`, and it shows the committed string exactly as the report printed it. Filtering on nullness rather than status — a null is the symptom and the status the documented reason, and filtering on the symptom would drop a cell for a reason no table states. Packaging the Cookie Cats CSV so the workbook could show Part 3's raw distribution — A-025 keeps that file out of the repository on redistribution grounds, and a `.twbx` published to Tableau Public would redistribute it. A live connection instead of an extract — Tableau Public does not support one to a local repository, and an extract pinned to a commit is what makes "stale" a checkable state rather than a drift nobody sees.
- **Reason:** Every figure in this project traces to a committed cell and every report is checkable against its tables. A dashboard is the one surface where a figure can be recomputed inside a tool, silently rounded by a format, or coerced from null to zero by a default — so its sources, its columns and its one permitted transformation are fixed before it is built, and the snapshot is pinned so its relationship to the tables can be verified rather than assumed.
- **Revised in review, before commit:** this entry's first draft stated one measured zero without scoping it to the thirteen sources, and omitted Part 2's intervals under an exceptionless column rule. Both were corrected in place, since neither draft was ever committed; the review that caught them also proposed that `part1_07` was a source, which it is not, so the three segment zeros are recorded as a conditional requirement rather than a live one.
- **Affects:** `ARCHITECTURE.md` §7.8 in full; `dashboard/README.md`'s required contents; which tables the build may open.
- **Falsifiable by:** Any dashboard figure that does not match its source cell.

### A-187 — The dashboard link lives in the opener region; the README's layout block is left as Part 3 wrote it
- **Kind:** supersedes A-176
- **Part:** project-wide
- **Date:** 2026-09-23
- **Status:** active
- **Supersedes scope:** the `Decision` field of A-176, in respect of the opener region's contents only — adding one permitted link line. The *n* + 2 structure, the population requirement, the no-recommendation rule for Parts 1 and 2, the quoted-figures-only rule and the 45-word cap stand unchanged, as do A-180's closing-limitation and cross-part amendments.
- **Decision:** Permit **exactly one link line** in the README opener region, after the *n* + 2 sentences and before the first `##`, not counted as a sentence and carrying **no figure and no claim about any result** — only what the link is and where `dashboard/README.md` documents its provenance. It is written by the **architecture session once the Tableau Public URL exists**, with no placeholder before then. Grant **`dashboard/` by prefix** to the dashboard build — the project author building by hand, or a session acting on the author's explicit instruction — with nothing outside it, nothing from `data/`, and not the README's link line. **Leave the README's `### Repository layout` block unamended**: it is inside `## Part 3` and is the Part 3 session's, and `dashboard/` is listed instead in `ARCHITECTURE.md` §7.1's canonical tree and reached from the link line.
- **Alternatives rejected:** A `## Dashboard` section immediately above `## Part 1` — it would put a presentation layer ahead of the three analyses in the README's own order and give a single line its own owner and heading. A `## Dashboard` section at the foot of the README — permitted by ownership, but it fails "near the top", which is the whole reason for the link. Counting the link line as a sixth sentence under *n* + 2 — it would have to meet the population rule, and a link has no population; a separate, stricter rule is cleaner. Letting the link line carry a one-clause description of what the dashboard shows — that is a claim, and a claim outside the sentence rules is the gap the no-claim clause closes. Asking the Part 3 session to add `dashboard/` to its layout block — it reopens a completed part's section for a directory that part did not create, and the block already omits `sql/`, which Parts 1 and 2 created, so adding one line would make a stale block look complete. Granting `dashboard/` to a new Claude session — the build is by hand in Tableau, and a grant should name who actually writes the files.
- **Reason:** The link has to be near the top to be useful, and the only thing above `## Part 1` is the opener region, which already has one owner; putting the line there keeps it that way, and the no-figure, no-claim rule keeps it from becoming an ungoverned sixth sentence. On the layout block, the honest statement is that the README's block describes the repository as Part 3 left it, and the canonical layout is the one this document maintains.
- **Affects:** §7.6's opener-region contents; §8's grants; §7.1's tree; what the architecture session writes after publication.
- **Falsifiable by:** A link line that states a figure or a result, or a `dashboard/` file written by anyone outside the grant — either is a defect by this entry's own terms.

---

## Amendment pass — `ARCHITECTURE.md` v1.10 (2026-09-23)

Part 1's segment view restored to the dashboard. IDs allocated by re-reading this file per
A-083: the highest heading present was A-187. §1–§6 untouched; no part, report or
committed table reopened.

### A-188 — Part 1's segment view is restored, and the two segment views share a dimension control and nothing finer
- **Kind:** supersedes A-186
- **Part:** project-wide
- **Date:** 2026-09-23
- **Status:** active
- **Supersedes scope:** the `Decision` field of A-186, in respect of the source list and the measured-zero checks only. Its recompute-nothing rule, its full-precision-column rule and tooltip exception, its status filter, its snapshot at `5eb02fd`, its exclusion of `data/`, and the band negation stand unchanged.
- **Decision:** Add **`part1_07_retention_by_segment.csv`** as the dashboard's **fourteenth** source and restore Part 1's segment view: classic retention only, D1/D7/D30 pooled per segment, Wilson intervals from the `*_value` columns, the status filter kept, discrete points with no connecting lines, "Other" labelled with its pooled count, rolling retention excluded, and `part1_07`'s `caveat` and `note` columns **not surfaced**. The **measured-zero checks become four live requirements**: W01 at D30 in `part1_03` (0 of 176), and Canada (0 of 104), Australia (0 of 84) and en-ca (0 of 87) at D30 in `part1_07`, each at 0% with its interval whenever its dimension is selected. **Part 1 and Part 2 may share one parameter selecting the segmentation dimension, and nothing finer** — no shared segment selection, highlight, filter action or legend — with separate panels, separate axes, a parameter labelled "Segment by" that names no population, and **each view captioning its own population**.
- **Why v1.9 excluded it:** for **scope**, not for any data or method reason. v1.9 kept the dashboard to one primary view per part plus Part 2's segments, and put Part 1's segment table on the out-of-scope list alongside Part 3's guardrail and Part 2's diagnostics. It did not check that list against the brief, which had requested the view. The table was always fit to show: every cell is `reported`, every dimension's denominators sum to the pooled denominator, and the report already carries the reading it needs. The omission surfaced only because the zero check in v1.9's review found three zeros in a table the dashboard did not read.
- **Alternatives rejected — the control:** A **shared segment parameter** driving both views — the tables name different segments, because Part 1 names a segment at ≥ 100 installers and Part 2 at ≥ 200 users at S0, so Germany, Mexico, United Kingdom, app versions 2.59 and 2.6.27, and languages de-de and en are named in Part 2 and pooled into "Other" in Part 1; selecting one would show a mark in one view and nothing in the other, and **"Other" is a different pool in each**, so a shared highlight on it would equate two different sets. **A shared axis or a single combined chart** — Part 1 plots a retention rate and Part 2 a share reaching a funnel step; one axis would present them as one measure. **Separate, unlinked controls** — defensible, but the brief asked for one control, and a dimension parameter is safe because the five dimension names are identical in both tables and mean the same attribution rule; the risk sits at the segment level, and that is where the sharing stops. **Surfacing `part1_07`'s caveat column** — its app-version text says §10.7.5 states no constancy test for that dimension, which was true when Part 1 was built and was superseded by v1.6 (A-154); displaying it would present a superseded statement as current, and editing it would reopen a committed table.
- **Reason:** The brief's request was sound and the table supports it. The design risk was never the view itself but the control: one control over two populations invites a reader to take a segment's two numbers as describing the same people. The tables make the difference concrete rather than hypothetical — the same `app_info.version` dimension is non-constant for **8.76%** of Part 2's 15,175 users and **1.97%** of Part 1's 4,319 installers — so the control is shared only at the one level where both tables genuinely say the same thing, and each view states whose figures it shows.
- **Affects:** `ARCHITECTURE.md` §7.8.1, §7.8.3, §7.8.4, §7.8.5 and §7.8.6; `dashboard/README.md`'s source list and checksums, now fourteen; the build's parameter design.
- **Falsifiable by:** Any dashboard figure that does not match its source cell, or a segment control that links a segment selection across the two views.

