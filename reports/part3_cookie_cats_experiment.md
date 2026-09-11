# Part 3 — Should the Cookie Cats progression gate move from level 30 to level 40?

**Answer: no. Keep the gate at level 30.** Moving it to level 40 costs 7-day
retention. The estimated cost is 0.82 percentage points (95% bootstrap interval
1.34 pp to 0.31 pp of lost retention), detected at p = 0.00155. The backlog item
closes on retention grounds.

This report is generated from the files in `outputs/`. Every figure quoted below
exists in one of them; none was typed in by hand.

---

## 1. What was pre-registered, and how to check that it was

The analysis design — primary metric, alpha, action threshold, SRM protocol,
data-handling policy, and the decision rule that turns a result into a
recommendation — was fixed in `ARCHITECTURE.md` **before any data was loaded and
before any statistic was computed**. That document was read-only to the session
that produced these numbers.

| Artefact | Value |
|---|---|
| Pre-registration commit | `c6d72f834359fba8b8748a0d7251592a8cab80c5` |
| `ARCHITECTURE.md` blob at that commit | `29b4f465421b18e8cd9dcbd2b7380e5962fd1305` |
| `ARCHITECTURE.md` version | v1.2 |
| Commit at which the dataset entered the repository | `20b946ede7905ef4e4d792db9c21fe0f2bc88301` |
| Commit containing the first line of `src/` | `1cb052feda8bb8fce69850fe76d073849aa999c6` |

The pre-registration commit contains exactly three files — `ARCHITECTURE.md`,
`assumptions.md` and `.gitignore` — and nothing else. It precedes the first
commit that touches `src/`, as `ARCHITECTURE.md` §1.7 requires. **The ordering is
checkable rather than asserted:** `git log` shows the design fixed at
`c6d72f83`, four commits before the CSV's checksum was recorded at `20b946ed`.
That ordering matters most in §3 below, and it is the reason this report can make
the claim it makes there.

Every judgement call is logged in `assumptions.md`, which is append-only:
entries A-001 to A-053 predate the repository, A-054 to A-071 were committed
before the dataset arrived, A-072 records the dataset's provenance, and A-073 to
A-075 record findings from the completed run.

### 1.1 The design, in brief

- **Primary metric:** 7-day retention (`retention_7`), and only that (§1.1).
  A gate has to be reached before it can be experienced; D7 gives the population
  a week to get there, so more of the treatment has actually been delivered than
  at D1.
- **Alpha:** 0.05, two-sided, all of it on the primary (§1.3).
- **Action threshold:** 1.00 percentage point absolute (§1.4). Below roughly a
  point, an effect is smaller than the week-to-week noise a live title sees from
  acquisition mix and seasonality.
- **Guardrail:** 1-day retention (`retention_1`), with no alpha, no significance
  claim, and no power to produce a ship recommendation — only to hold one (§1.2).
- **Estimand:** the intention-to-treat effect on assigned players (§4.1). This
  matters more here than usual; see §7.1.

---

## 2. The data

| | |
|---|---|
| Source | Kaggle `mursideyarkin/mobile-games-ab-testing-cookie-cats` |
| File | `cookie_cats.csv`, 2,707,297 bytes |
| SHA-256 | `5ab54d761fbddcd50de7b88e4eaf7837cba4569474f50c043a4d17ee342c46bd` |
| Rows | 90,189 data rows, excluding the header |
| Columns | `userid`, `version`, `sum_gamerounds`, `retention_1`, `retention_7` |

The CSV is not committed — redistributing someone else's dataset is not ours to
grant — so `data/raw/` is git-ignored and provenance is recorded in
`assumptions.md` A-072 instead. The entrypoint verifies that SHA-256 before
anything runs, reading the expected value out of `assumptions.md` rather than
from a constant in code, so the record a reader checks is the record the code
checks.

The row count is stated as **data rows excluding the header**, which is the same
quantity the loader records, and the two are asserted equal at the end of the
run. Note that `wc -l` reports 90,190 for this file, one greater, because it
counts newline bytes across a header line and a trailing newline.

The observed row count matches the documented size of the dataset exactly.

### 2.1 Structural validation

Every value in `version`, `retention_1`, `retention_7` and `sum_gamerounds` was
checked against an enumerated token set before any statistic was computed. All
values fell inside their sets, so the file is the file `ARCHITECTURE.md`
describes.

This check exists because casting the string `"False"` to a boolean in Python
yields `True`, which produces a wrong retention rate that looks entirely
plausible and survives every eyeball check. Retention values were mapped from an
explicit token set — `True`/`False` and `1`/`0` — never by truthiness. After
coercion, the count of each value was verified to equal the count of its source
token before coercion.

---

## 3. Assignment integrity — the SRM check, and the number to look at

*Source: `outputs/tables/part3_02_srm.csv`; recorded as finding A-075.*

| Quantity | Value |
|---|---|
| Assignment population | 90,189 |
| `gate_30` (control) | 44,700 |
| `gate_40` (variant) | 45,489 |
| Expected under 1:1 | 45,094.5 per arm |
| Excess in the variant arm | 789 rows |
| Observed control share | 0.495626 |
| **Two-sided exact binomial p** | **0.00869** |
| Chi-square goodness-of-fit (1 df) | 6.9024, p = 0.00861 |
| Pre-registered failure threshold | 0.001 |
| **Result** | **Does not trip. No integrity downgrade.** |

**This p-value deserves to be looked at directly rather than filed under
diagnostics.** At the conventional 0.05 it would be called significant. At 0.01
it would still trip. It does not trip here because `ARCHITECTURE.md` §2.3 set the
SRM failure threshold at **0.001**, and it set it before any data was accessed.

The reasoning §2.3 gives for 0.001 was written without knowledge of this result:
SRM is a data-quality alarm on a nuisance parameter rather than a hypothesis of
interest, so it is tuned for specificity, not for the conventional 5%. At 0.05,
about one clean experiment in twenty would trip an alarm whose consequence is
withholding the headline. The failure modes SRM exists to catch — a broken
assignment service, a logging filter applied to one arm, a bot-traffic asymmetry
— produce *gross* imbalance, not marginal imbalance, and at n ≈ 90,000 the test
has overwhelming power against those. An observed split of 49.56 / 50.44 is
marginal by that standard.

A reader who suspects the threshold was chosen to accommodate the result can
settle it without taking anyone's word: the threshold is in commit
`c6d72f834359fba8b8748a0d7251592a8cab80c5` and the dataset's checksum first
appears four commits later in `20b946ede7905ef4e4d792db9c21fe0f2bc88301`. This
is the single most checkable claim in this deliverable, and it is the reason the
pre-registration was written the way it was.

**The conditional this test rests on.** No public documentation states the
experiment's intended allocation. The 1:1 split tested above is an assumption
(A-008), recorded as a permanent unknown. **If the original design was weighted
rather than 1:1, the SRM p-value as computed here is uninterpretable, and with it
the integrity claim that rests on it.** That sentence holds whether or not the
test trips, because its truth does not depend on the outcome.

What the check does **not** establish is that assignment was balanced. It
establishes only that the observed imbalance is not extreme enough to trip an
alarm calibrated for gross failures. The 789-row excess is carried forward to
§7.3 as an unverifiable property, because this dataset contains no
pre-treatment covariates and no further diagnosis of it is possible.

---

## 4. Data quality

*Source: `outputs/tables/part3_01_data_quality.csv`; findings A-073 and A-074.*

The file is unusually clean, and each of the following was asserted rather than
assumed:

| Check | Result |
|---|---|
| Unassignable rows (missing `version`) | **0** |
| Duplicate `userid` values | **0** — all 90,189 distinct |
| Missing `retention_7`, either arm | **0** |
| Missing `retention_1`, either arm | **0** |
| Missing `sum_gamerounds` | **0** |
| Differential missingness between arms | 0.00 pp on both metrics |

Because nothing was excluded, **every analysis denominator equals its arm's
assignment count**: 44,700 for `gate_30` and 45,489 for `gate_40`, on both
metrics. The descriptive differential-exclusion check is therefore exactly even,
there being no exclusions to distribute.

Three policies that `ARCHITECTURE.md` specifies in detail — duplicate handling
by case, per-metric exclusion of nulls, and their respective integrity
thresholds — were consequently never exercised. They are implemented and tested,
and they are recorded here as unused rather than quietly dropped.

The SRM denominator was fixed before any of these checks ran, so no cleaning
judgement could have moved it. That ordering is enforced by the code, not by
convention.

---

## 5. What this sample could have seen

*Source: `outputs/tables/part3_03_power.csv`, `outputs/figures/part3_03_power_curve.png`.*

This section appears **before** the results deliberately: it is a property of the
design, not an account of the outcome.

| Quantity | Value |
|---|---|
| Baseline (observed `gate_30` D7 rate) | 19.02% |
| Arm sizes (observed, not nominal) | 44,700 / 45,489 |
| Power to detect a 1.00 pp absolute difference | **0.9663** |
| Smallest absolute difference detectable at 80% power | **0.74 pp** |
| Smallest absolute difference detectable at 95% power | **0.95 pp** |

**Required comparison (§3):** the smallest effect detectable at 80% power is
0.74 pp, which is **smaller than** the 1.00 pp action threshold. This sample can
detect effects smaller than the one we would act on.

### 5.1 Which standard error enters which quantity

All three figures come from the same expression, so that a reader can reproduce
them from the stated method. With `p_c` the observed control rate, `δ` the
absolute difference, and `n_c`, `n_v` the observed arm sizes:

```
power(δ) = Φ( ( δ − z₁₋α/₂ · SE_null(δ)) / SE_alt(δ) )
         + Φ( (−δ − z₁₋α/₂ · SE_null(δ)) / SE_alt(δ) )

SE_null(δ) = √( p̄(1−p̄) · (1/n_c + 1/n_v) ),  p̄ = (n_c·p_c + n_v·(p_c+δ)) / (n_c+n_v)
SE_alt(δ)  = √( p_c(1−p_c)/n_c + (p_c+δ)(1−p_c−δ)/n_v )
```

- The **pooled null standard error** scales the critical value. This is the
  "pooled variance under the null" §3 specifies.
- The **unpooled alternative standard error** scales the distance from the
  alternative to that critical value, mirroring the pooled-test / unpooled-interval
  asymmetry used for the estimate itself (§4.1).
- The two inverse-solved rows are the same expression solved numerically for `δ`
  at power 0.80 and 0.95.

At δ = 1.00 pp these are `SE_null` = 0.002640 and `SE_alt` = 0.002639.

One convention note, because it accounts for a reproducible difference of a few
hundredths of a point. Evaluating the variance at the **baseline rate alone**,
rather than at the alternative, yields 0.9690 power and detectable effects of
0.73 pp and 0.94 pp — slightly less conservative, because `p(1−p)` is smaller at
0.1902 than at 0.2002. The convention used here is the more conservative one and
is the one §3 describes. As a cross-check, the arcsine (Cohen's *h*) formulation
gives 0.9663 at 1.00 pp, agreeing with the figure reported above to four decimal
places.

**This is a fixed-n dataset.** The CSV has the rows it has; the experiment cannot
be extended. The calculation above is descriptive of the sensitivity this sample
happens to have, and is not a sample-size calculation. Power is never evaluated
at the observed effect size, which would be a monotone re-expression of the
p-value and would carry no information the p-value does not.

---

## 6. Results

### 6.1 Retention rates

*Source: `outputs/tables/part3_05_retention_rates.csv`, `outputs/figures/part3_01_retention_rates.png`.*

| Metric | Arm | Retained | Denominator | Rate |
|---|---|---|---|---|
| `retention_7` (primary) | `gate_30` | 8,502 | 44,700 | **19.02%** |
| `retention_7` (primary) | `gate_40` | 8,279 | 45,489 | **18.20%** |
| `retention_1` (guardrail) | `gate_30` | 20,034 | 44,700 | 44.82% |
| `retention_1` (guardrail) | `gate_40` | 20,119 | 45,489 | 44.23% |

### 6.2 Primary — 7-day retention

*Source: `outputs/tables/part3_06_primary_inference.csv`, `outputs/figures/part3_02_effect_intervals.png`.*

| Quantity | Value |
|---|---|
| **Δ₇ (variant − control)** | **−0.82 pp** |
| z statistic (pooled variance) | −3.1644 |
| **p₇ (two-sided)** | **0.00155** |
| 95% analytic interval (unpooled Wald) | **[−1.33, −0.31] pp** |
| 95% bootstrap percentile interval | **[−1.34, −0.31] pp** |
| Monte Carlo standard error | 0.2610 pp |
| Resamples | 10,000, stratified by arm, seed 20260910 |

**Moving the gate from level 30 to level 40 costs 7-day retention.** The effect
is negative and it is detected: p = 0.00155 against a pre-registered alpha of
0.05. Both interval methods exclude zero and agree to within a hundredth of a
point.

**On magnitude, stated carefully.** The estimate is 0.82 pp, which is *below* the
1.00 pp action threshold, and the interval spans values on both sides of that
threshold in magnitude. This experiment therefore establishes that the move
causes a loss, but it does **not** establish that the loss clears the bar the
threshold defines. Those are different claims and only the first is supported.

This distinction costs the decision nothing: rule R3 fires on significance and
sign alone and does not consult the action threshold, and a harm that fails to
clear the threshold is no reason to make the change either. The threshold test
and the rule that actually fired agree on "keep", so the recommendation does not
depend on which of the two a reader consults.

**Two standard errors, deliberately.** The p-value uses the pooled
(common-proportion) standard error, 0.2592 pp, because under the null the two
arms share a single proportion and that is the correct null variance. The
interval uses the unpooled (Wald) standard error, 0.2592 pp, because estimating
the size of a difference is a different problem from testing whether it is zero,
and under the alternative the arms do not share a proportion. The two agree to
four decimal places here by arithmetic accident — they are 0.259177 and 0.259201
— not because one was reused for both. No continuity correction is applied.

### 6.3 The two instruments agree

The z-test is the confirmatory instrument: alpha was pre-registered against it,
so it and it alone decides significance. The bootstrap is the estimation
instrument: it decides the comparison against the action threshold. They can
disagree in exactly two ways, and neither occurred here — p₇ is below 0.05 and
the bootstrap interval excludes zero. The conflict precondition did not fire.

### 6.4 Guardrail — 1-day retention

*Source: `outputs/tables/part3_07_guardrail_inference.csv`.*

| Quantity | Value |
|---|---|
| Δ₁ (variant − control) | **−0.59 pp** |
| 95% bootstrap percentile interval | **[−1.25, 0.05] pp** |
| 95% analytic interval | [−1.24, 0.06] pp |
| Monte Carlo standard error | 0.3316 pp |
| Test performed | **None** |

The guardrail interval **contains zero**, so the guardrail is quiet. No
significance claim is made or available: `retention_1` carries no alpha and no
p-value was computed for it at all.

D1 moves in the same direction as D7 and by a similar amount, and the interval's
upper bound sits at +0.05 pp — close enough to zero that a modestly different
resample would place it on either side. That proximity changes nothing: had the
interval excluded zero, the applicable modifier would have been R9, whose effect
on an already-conservative recommendation is "unchanged". The recommendation is
robust to this boundary.

### 6.5 Engagement

*Source: `outputs/tables/part3_08_engagement.csv`, `outputs/tables/part3_09_engagement_disclosure.csv`, `outputs/figures/part3_04_engagement_distribution.png`.*

`sum_gamerounds` counts rounds played in the first 14 days. It is reported
descriptively and was never tested for the headline claim: it is heavily skewed,
it is not a decision variable, and its 14-day window does not align with either
retention flag.

**The extreme observation is disclosed and kept.** One player in `gate_30`
records **49,854 rounds** in 14 days — roughly 150 rounds an hour, continuously,
for two weeks. No other row comes close; the next highest is 2,961. The value is
implausible as human play and is more likely a logging artefact or an automated
client, but this dataset contains nothing that can distinguish those, and the
honest statement is that it cannot be adjudicated.

It is kept in the primary analysis. Removing rows from a randomised experiment
after assignment, on the basis of an outcome variable, is a selection process
applied post-randomisation — the exact thing randomisation exists to prevent —
and it would also perturb the arm count the integrity check depends on. It
cannot meaningfully affect the retention result in any case: `retention_7` is a
boolean, so one player moves an arm's proportion by at most 1/n, about 0.002 pp
against a 1.00 pp threshold.

| Arm | | n | Mean | Median | Max | Winsorised mean |
|---|---|---|---|---|---|---|
| `gate_30` | with extreme | 44,700 | 52.46 | 17.0 | 49,854 | 49.14 |
| `gate_30` | without | 44,699 | 51.34 | 17.0 | 2,961 | 49.13 |
| `gate_40` | with extreme | 45,489 | 51.30 | 16.0 | 2,640 | 48.85 |
| `gate_40` | without | 45,489 | 51.30 | 16.0 | 2,640 | 48.85 |

Winsorisation is at the pooled 99th percentile, a cap of 493 rounds, applied
identically to both arms. The single row moves the `gate_30` mean by 1.12
rounds and the median not at all.

---

## 7. What this experiment does not support

This section sits before the recommendation on purpose: the boundaries of the
claim should be read before the claim.

### 7.1 Not answerable from this data at all

- **Revenue and lifetime value.** There are no monetization fields. A gate is
  fundamentally a monetization instrument — it stops the player and asks them to
  wait, ask friends, or pay — so this experiment cannot speak to the variable the
  gate is actually tuning. A retention-negative gate move could still be
  revenue-positive, and nothing here would show it.
- **The effect on players who actually met the gate.** This is the central
  limitation. No field records whether any player ever reached level 30, let
  alone level 40. Every player assigned to `gate_40` who quit at level 6
  experienced exactly the same game as their `gate_30` counterpart, and both are
  in the denominator. The estimate is an intention-to-treat effect over all
  assigned players, an unknown and probably large share of whom were never
  exposed to either gate, and those players dilute the true effect on exposed
  players toward zero by an unknown factor. **Therefore a null or negative ITT
  result here is not evidence about what gate placement does to players who
  actually reach it** — the −0.82 pp measured across everyone is a diluted
  reflection of an effect on an unknown and unmeasurable subset, and the
  undiluted effect on that subset could be substantially larger.
- **Anything past day 7.** The retention flags stop at D7, and `sum_gamerounds`
  covers 14 days, so the two windows do not even align. D14, D30 and long-run
  churn are out of reach — and a pacing change is precisely the kind of
  intervention whose effect can appear or reverse after the first week.
- **Cannibalisation and mechanism.** Whether the retention loss comes from
  altered pacing, changed session length, shifted difficulty, or something else
  is not distinguishable from two boolean flags and a round count.

### 7.2 Answered only under stated assumptions

- **Which arm is the incumbent** (A-001, confirmed as A-036). `gate_30` is
  treated as the shipped baseline and `gate_40` as the proposed change, on the
  basis of the dataset card. Every effect is variant minus control, so this fixes
  the sign of every number above.
- **The intended 1:1 allocation** (A-008). The SRM test in §3 is run against a
  hypothesised even split that no documentation confirms. This is a permanent
  unknown, and §3 states the consequence.
- **The treatment of the extreme observation** (A-021). It is kept, and reported
  both ways in §6.5. It cannot affect the retention conclusion.

### 7.3 Confounds and unverifiable properties that remain

- **The 789-row arm imbalance is not explained, only tolerated.** The SRM check
  did not trip, and that is not the same as establishing that assignment was
  balanced. The observed split is 49.56 / 50.44 against an assumed 50 / 50, and
  whether that excess is chance or a mechanism cannot be determined here.
- **No pre-treatment covariates exist**, so no randomisation or balance check is
  possible beyond the arm counts themselves. `sum_gamerounds` and both retention
  flags are all post-assignment outcomes. No covariate-balance table can be
  built, and the imbalance above cannot be diagnosed further from this data.
  Acquisition-channel mix, geography, device tier and platform could differ
  between the arms and it would be undetectable.
- **Unknown randomisation unit** — user, device, or install. If it is device or
  install, one person can appear in both arms and intention-to-treat is
  contaminated in a way the duplicate check cannot see. That check found no
  repeated `userid`, which rules out repetition of that identifier and nothing
  more.
- **Unknown assignment timing** relative to install, so it cannot be confirmed
  that assignment preceded any measured behaviour.
- **Unknown calendar window.** Day-of-week effects, a live-ops event, a store
  feature or a marketing burst overlapping one arm's install cohort cannot be
  ruled out.
- **Reinstall and reassignment behaviour** is unspecified, so a churned player
  who returned under the other arm's configuration is invisible.
- **Novelty and learning effects** cannot be separated from steady-state effects
  in a single fixed window.
- **Unknown game version and level-difficulty tuning** at the time of the test.
  The treatment is defined by a level number, and a level number is not a fixed
  quantity of difficulty across versions — how hard level 30 actually was is not
  recoverable.

### 7.4 What would be required to answer the business question properly

- **Exposure instrumentation:** an event recording whether and when each player
  reached the gate. This converts the ITT estimate into an effect on the exposed
  population and makes the dilution in §7.1 measurable rather than unknown. This
  is the single highest-value addition.
- **Revenue per user over a longer horizon**, so the experiment is powered on the
  metric the gate exists to move rather than on a proxy for it.
- **Retention at D14 and D30**, to see whether a first-week loss persists,
  deepens, or reverses.
- **Level-progression telemetry** — the distribution of highest level reached —
  to establish where players actually stall, which is what determines whether 30
  and 40 are even the right pair of candidates to compare.
- **A multi-arm test** with at least one further placement, for example a third
  arm well beyond 40. A two-arm test cannot detect a non-monotone response, and
  "40 is worse than 30" does not imply "earlier is always better".
- **A named follow-up hypothesis for the guardrail:** *moving the gate to level 40
  reduces 1-day retention.* The interval here is [−1.25, 0.05] pp and includes
  zero, so this run does not establish it; it is written as a testable statement
  for a future experiment rather than reported as an observation.

---

## 8. Recommendation

The recommendation is derived mechanically from the decision rule fixed in
`ARCHITECTURE.md` §1.6 before the result was known. The full path is quoted by
rule name, as that section requires.

*Source: `outputs/tables/part3_11_decision.csv`.*

| Stage | Outcome |
|---|---|
| **Stage 1 — preconditions** | **Clean.** R0 did not fire: no integrity downgrade was triggered by any of its four sources. R6 did not fire: the z-test and the bootstrap agree. |
| **Stage 2 — outcome branch** | **R3** — `p₇ < 0.05` and `Δ₇ < 0`. Exactly one of R1–R5 fired; the other four conditions are recorded false. |
| **Stage 3 — modifier** | **R10** — `CI₁` contains zero. The guardrail was checked and was quiet. |

> ## Keep the gate at level 30.
>
> Moving it to level 40 is estimated to cost **0.82 pp of 7-day retention**
> (95% interval **1.34 pp to 0.31 pp** of loss), and the effect is detected at
> **p = 0.00155**. The backlog item closes on retention grounds.

**The one thing that would change this:** evidence on revenue. The gate is a
monetization instrument and this experiment contains no monetization data at all,
so a later gate could still be revenue-positive despite costing retention. That
question is not answerable here and would need the instrumentation listed in
§7.4.

What this recommendation does **not** rest on: the size of the loss relative to
the 1.00 pp action threshold, which this experiment does not establish (§6.2);
the guardrail, which is quiet and which by design can never create a
recommendation; or `sum_gamerounds`, which was never tested.

---

## 9. Reproducing this

From a clean checkout, this sequence and nothing else reproduces every number,
table and figure above:

```bash
brew install python@3.12                    # any source of a 3.12 interpreter works
/opt/homebrew/bin/python3.12 -m venv .venv
./.venv/bin/python -m pip install -r requirements.lock.txt
# fetch cookie_cats.csv into data/raw/ — see the README
./run_part3.sh
```

The run verifies the input checksum before computing anything and ends by
re-reading its own outputs and asserting that the data-handling assertions held,
that every reported denominator equals the row count recorded for it, that
exactly one Stage 2 branch fired, and that the recorded recommendation is the one
the decision pipeline produces from the same inputs.

**Reproducibility guarantee, stated at the strength it actually holds.** Every
file in `outputs/tables/` and `outputs/run_manifest.json` reproduces
byte-for-byte on any machine, the manifest's run timestamp excepted. Figures are
**not** byte-identical across machines — matplotlib does not produce identical
PNGs across versions, platforms and font configurations, and claiming otherwise
would be falsified by the first re-run elsewhere. What holds for figures is that
each is generated from a committed table, so the numbers and labels behind it
reproduce exactly even when the pixels do not, and that a re-run on the same
machine with the same lock file is byte-identical.

Environment recorded in `outputs/run_manifest.json`: CPython 3.12.14, numpy
2.5.3, scipy 1.18.1, pandas 3.0.5, statsmodels 0.15.0, matplotlib 3.11.1 on the
`Agg` backend. The bootstrap seed is 20260910, defined once and imported
everywhere; the two metrics' resampling streams are derived from it by spawning.
Same seed, same resample count, same numpy version gives bit-identical interval
endpoints.
