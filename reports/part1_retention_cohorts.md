# Part 1 — Retention and install cohorts

**Dataset.** The GA4 public sample for the mobile game Flood-It,
`firebase-public-project.analytics_153293282.events_*`: 114 daily shards covering
**20180612 to 20181003**, 5,700,000 event rows, 15,175 device-installs.

**Specification.** `ARCHITECTURE.md` §10.5 and §10.7, at v1.5, commit `5b2c0ba`. Every
definition this report rests on — the population, the day key, the two retention
definitions, the weekly grain, the eligibility cutoffs, the n = 30 suppression floor and
the interval method — was fixed in that document **before any retention number existed**,
for the same reason §1 fixed Part 3's decision rule before its data was loaded.

**Judgement log.** The implementation calls this build had to make were appended to
`assumptions.md` as **A-131 through A-141** and committed at `6a2fb35` **before the first
query ran**, so that each call which shapes a number demonstrably predates the number.
Three of those eleven are `challenge` entries rather than decisions, because they record
ambiguities in the specification that this build was directed through rather than
resolving on its own authority. **A-142 through A-151** were appended as the work
proceeded. A-142 is a mid-flight supersede of one of this session's **own** rules, and it
changed an outcome; it is set out in full in §8.2 rather than left in the log.

**Traceability.** Every figure below comes from a committed table under
`outputs/tables/`, named beside the block that uses it. No number in this report was
typed from memory or from the specification — the population figures in particular were
**recomputed** rather than transcribed, because `ARCHITECTURE.md` §10.1 makes the CSV the
source of truth for every number, including numbers it quotes itself.

---

## 1. Who is in this analysis, and who is not

| | Users |
|---|---:|
| Distinct device-installs with any event in the window | **15,175** |
| **With a `first_open` event — this analysis's population** | **4,319** |
| Without a `first_open` event — excluded | **10,856** |
| Share of the sample excluded | **71.54%** |

Source: `part1_01_population_reconciliation.csv`. Also there: 4,322 `first_open` events
across those 4,319 users, 3 of whom have two (never more).

Cohorts are built on the **`first_open` event**, so Part 1 describes the 4,319 users who
have one and discards **71.54%** of the sample. §10.5.1 chose that deliberately over the
`first_open_time` user property, which covers all 15,175: the property's semantics are
unverified — nothing establishes whether it is a true install timestamp or a value
assigned when GA4 first saw the user, and those differ exactly for the users whose
install predates the window. A smaller defensible claim beats a larger unverifiable one,
and the cost of the smaller claim is disclosable, which is what this table does. §8.2
reports the one check available on that trade.

**The exclusion is not random, and its direction is knowable.** A user with events but no
`first_open` in the window either installed before 20180612 or lost the event to the
sampling. Either way the 4,319 are systematically **newer** than the 10,856, so Part 1's
cohorts are a recent-installer slice rather than a random sample of players. Retention of
new installs is typically lower than that of an established base, so the direction the
exclusion pushes these figures is knowable. **Its size is not, and this report does not
estimate it.**

**What these figures are and are not about.** They describe users with an observed
`first_open` event inside a 114-day window of a sampled export. They are not about the
sample's users generally — 71.54% of them are absent. They are not about the game's
player base (§2). And they are not comparable with a published retention figure for this
title unless that figure uses the same population, which cannot be checked.

---

## 2. What this sample is — and what it is not

**Every one of the 114 shards holds exactly 50,000 rows.** That uniformity is not
traffic; it is a sampling cap, and it governs how everything below may be read.

- Part 1 describes a **50,000-events-per-day sample** of this property, not the game's
  player base.
- **No absolute count here measures real traffic** — not installs per week, not users,
  not events per day. The install counts in §3.2 are counts of sampled installs.
- **No growth or trend claim may rest on volume.** Weekly install counts range from
  **95** (W03) to **415** (W08), more than four-fold between the smallest and the
  largest. That is a change in what the sample captured, not in acquisition, and the
  report draws no acquisition conclusion from it anywhere.
- **The per-day sampling fraction is unknown and may not be uniform**, so even
  comparisons of *rates* across weeks could be affected if the sample was drawn
  differently on different days. That is unresolvable from the data and is carried in
  §8.3 rather than attached as a hedge to one chart.

Source for the shard uniformity: `outputs/tables/recon_00_shard_inventory.csv` (A-096).
Install counts: `part1_02_cohort_inventory.csv`.

---

## 3. The definitions these numbers rest on

### 3.1 A day means `event_date`, and the day is not UTC

The day key is the export's own **`event_date`** field. §10.5.2 fixed that over two
alternatives: a UTC date recomputed from `event_timestamp`, which would split one local
day across two keys for a third of all rows and forfeit shard pruning; and a device-local
date, which would give every user a private day boundary so that "day 7" would stop being
one quantity.

§10.5.2 required this build to **report the offset it observes** rather than assume the
recon's reading. Observed, from `part1_09_day_key_offset.csv`:

| | |
|---|---|
| Rows whose `event_date` disagrees with the shard holding it | **0** of 5,700,000 |
| Rows where `event_date` is one day **behind** the UTC date | 1,935,518 (**33.96%**) |
| Rows where `event_date` is **ahead** of the UTC date | **0** |
| Best whole-hour offset | **UTC−07:00**, dating **5,698,777 rows (99.9785%)** |
| Next-best whole-hour offset | 97.3586% |
| Whole-hour offsets that date **every** row | **0** |

So the day key is consistent — perfectly consistent with the shard it is stored in — but
it is **not** a function of `event_timestamp` under any constant offset. The feasible
interval for such an offset is **empty by 93 seconds**, and a fixed UTC−07:00 zone would
misplace **1,223 rows (0.0215%)**, all of them within a minute and a half of a local
midnight. The honest description is that `event_date` is **the export's own day stamp**,
which agrees with a UTC−07:00 local date on all but 0.02% of rows.

**The cost, stated:** day *N* in this report is a property-local day. It is not a UTC day
and it is not the user's own local day. No metric here depends on the zone's identity;
every metric depends on the key being consistent, and it is.

### 3.2 Install day, and the sixteen weekly cohorts

**Install day** is the `event_date` of the user's **earliest** `first_open` event, and it
is **day 0** — never counted as a retention day. For the 3 users with two `first_open`
events the earliest is taken, which makes them deterministic rather than arbitrary; the
build asserted that this reading agrees with taking the minimum `event_date`, and it does
for **all** 4,319 users (`part1_08_data_handling.csv`).

Cohorts are **weekly**, in 16 fixed 7-day blocks anchored at the first shard rather than
ISO weeks — 20180612 is a Tuesday, so ISO weeks would have made W01 a 4-day cohort whose
denominator is incomparable with every other. Daily cohorts were rejected on measurement
grounds before the fact: `first_open` volume per shard has a median of 38 (A-100), and at
that size most cells would fall under the suppression floor.

114 days is 16 whole weeks plus 2 days. **The 20181002–20181003 tail is excluded from
every cohort table** and its install count reported instead; folding it into W16 would
have made W16 a 9-day cohort with a denominator about 29% larger than its neighbours and
distorted the very trend the weekly grain exists to show.


| Cohort | Install days | Installs | D1 | D7 | D30 |
|---|---|---:|:-:|:-:|:-:|
| W01 | 20180612–20180618 | 176 | yes | yes | yes |
| W02 | 20180619–20180625 | 181 | yes | yes | yes |
| W03 | 20180626–20180702 | 95 | yes | yes | yes |
| W04 | 20180703–20180709 | 212 | yes | yes | yes |
| W05 | 20180710–20180716 | 271 | yes | yes | yes |
| W06 | 20180717–20180723 | 245 | yes | yes | yes |
| W07 | 20180724–20180730 | 267 | yes | yes | yes |
| W08 | 20180731–20180806 | 415 | yes | yes | yes |
| W09 | 20180807–20180813 | 305 | yes | yes | yes |
| W10 | 20180814–20180820 | 241 | yes | yes | yes |
| W11 | 20180821–20180827 | 250 | yes | yes | yes |
| W12 | 20180828–20180903 | 305 | yes | yes | yes |
| W13 | 20180904–20180910 | 384 | yes | yes | — |
| W14 | 20180911–20180917 | 300 | yes | yes | — |
| W15 | 20180918–20180924 | 266 | yes | yes | — |
| W16 | 20180925–20181001 | 278 | yes | — | — |
| *tail, excluded* | 20181002–20181003 | *128* | — | — | — |
| *of which W16 installs on 20180925–26* | — | *85* | | | |
| **All 16 weeks** | 20180612–20181001 | **4,191** | | | |

Source: `part1_02_cohort_inventory.csv`. Read the install counts under §2: they are
sampled installs, and the spread between W03's 95 and W08's 415 is a property of the
sample rather than of acquisition.

### 3.3 Which cohorts can be measured, and how an unmeasurable cell is printed

A cohort can be measured at day *N* only if its **last** install day plus *N* falls inside
the window ending 20181003. That gives cutoffs of install day ≤ **20181002** for D1,
≤ **20180926** for D7 and ≤ **20180903** for D30, and therefore **16 cohorts at D1, 15 at
D7 and 12 at D30**. The block boundaries, the three cutoff dates and the 16 / 15 / 12
counts are each asserted twice — by `ERROR()` guards inside `sql/12`, `sql/13` and
`sql/14`, which would have failed the queries rather than returned a table meaning
something else, and again in `src/part1_retention/verify.py` against the written files.

**An ineligible cell is printed as explicitly null — not zero, not blank, not omitted.**
A cohort that cannot be observed for 30 days still appears in the D30 table with its
install count shown and its rate `NULL`. Omitting the row would let a reader infer that
only 12 cohorts exist; printing zero would be a false retention figure of the worst kind.

That distinction is load-bearing here rather than decorative, because **four cells in
this report are measured zeros**:

| Cell | Table | Count | 95% Wilson upper bound |
|---|---|---:|---:|
| W01 at D30, classic | `part1_03_classic_retention_weekly.csv` | 0 / 176 | 2.14% |
| Canada at D30 | `part1_07_retention_by_segment.csv` | 0 / 104 | 3.56% |
| Australia at D30 | `part1_07_retention_by_segment.csv` | 0 / 84 | 4.37% |
| en-ca at D30 | `part1_07_retention_by_segment.csv` | 0 / 87 | 4.23% |

Each of those is a real measurement: the cohort was observable at day 30 and nobody
returned on it. Each carries an interval, because a zero out of 176 and a zero out of 84
are different statements. A reader who could not tell these apart from the 20 ineligible
cells in the same tables would draw a conclusion the data does not support, which is the
whole reason the two are printed differently.

### 3.4 Two retention definitions, both reported, neither unlabelled

- **Classic retention — the primary metric.** Retained at day *N* if the user has at
  least one event whose `event_date` equals install day + *N* **exactly**.
- **Rolling retention — the secondary metric**, in its own labelled table. Retained at
  day *N* if the user has at least one event with `event_date` **≥** install day + *N*.

Both are reported because the literature quotes them interchangeably and a reader who
knows the space will ask which this is. Classic is primary because D1/D7/D30 are
conventionally classic, and because rolling is bounded by the observation window in a way
classic is not — §5 shows exactly how much that matters here.

### 3.5 Intervals, and the floor below which no rate is printed

Every rate carries a **95% Wilson score interval** and its denominator. Wilson rather than
Wald because cohort denominators run from tens to thousands and Wald misbehaves at small
*n* and near 0 or 1; a closed form rather than a bootstrap because a single proportion
needs no seed and no resample count. The constant is derived from the standard library
rather than typed, so the intervals do not rest on a rounded 1.96.

**Any cell whose denominator is below 30 is reported as a count only** — no rate, no
interval. That rule was checked on all 96 weekly cells and **never fired**: the smallest
cohort is 95, more than three times the floor. It is reported as checked-and-quiet rather
than left as a silence, on the same principle that makes an unconditional SRM report
worth more than one that appears only when it fails.

---

## 4. Classic retention — the primary figures

### 4.1 Pooled

| Horizon | Cohorts pooled | Install days covered | Retained | Denominator | Rate % | 95% Wilson |
|---|:-:|---|---:|---:|---:|---|
| **D1** | 16 | 20180612–20181001 | 911 | 4,191 | **21.74** | [20.51, 23.01] |
| **D7** | 15 | 20180612–20180924 | 222 | 3,913 | **5.67** | [4.99, 6.44] |
| **D30** | 12 | 20180612–20180903 | 62 | 2,963 | **2.09** | [1.64, 2.67] |

Source: `part1_04_classic_retention_pooled.csv`. Each horizon pools **only** the cohorts
eligible at it, so the three rows have three different denominators, each printed. Every
pooled denominator and numerator is the exact sum of its eligible weekly cells — an
identity `verify.py` asserts rather than eyeballs. Pooling D30 over installs that could
not be observed for 30 days would be the same error as printing zero, with the arithmetic
hidden inside a single number.

The pooled figures are the **level**; the weekly cohorts below are the **trend**. Both
appear, and neither replaces the other.

### 4.2 By weekly cohort

| Cohort | n | D1 retained | D1 % [95% Wilson] | D7 retained | D7 % [95% Wilson] | D30 retained | D30 % [95% Wilson] |
|---|---:|---:|---|---:|---|---:|---|
| W01 | 176 | 56 | 31.82 [25.39, 39.02] | 5 | 2.84 [1.22, 6.48] | 0 | 0.00 [0.00, 2.14] |
| W02 | 181 | 51 | 28.18 [22.13, 35.13] | 11 | 6.08 [3.43, 10.55] | 6 | 3.31 [1.53, 7.04] |
| W03 | 95 | 31 | 32.63 [24.04, 42.57] | 7 | 7.37 [3.61, 14.44] | 3 | 3.16 [1.08, 8.88] |
| W04 | 212 | 59 | 27.83 [22.23, 34.22] | 16 | 7.55 [4.70, 11.91] | 6 | 2.83 [1.30, 6.04] |
| W05 | 271 | 61 | 22.51 [17.94, 27.85] | 21 | 7.75 [5.12, 11.56] | 6 | 2.21 [1.02, 4.75] |
| W06 | 245 | 68 | 27.76 [22.52, 33.67] | 21 | 8.57 [5.67, 12.75] | 7 | 2.86 [1.39, 5.78] |
| W07 | 267 | 75 | 28.09 [23.04, 33.76] | 19 | 7.12 [4.60, 10.85] | 5 | 1.87 [0.80, 4.31] |
| W08 | 415 | 90 | 21.69 [17.99, 25.90] | 24 | 5.78 [3.92, 8.46] | 9 | 2.17 [1.15, 4.07] |
| W09 | 305 | 78 | 25.57 [21.00, 30.75] | 18 | 5.90 [3.77, 9.13] | 3 | 0.98 [0.34, 2.85] |
| W10 | 241 | 53 | 21.99 [17.22, 27.64] | 23 | 9.54 [6.44, 13.91] | 6 | 2.49 [1.15, 5.32] |
| W11 | 250 | 51 | 20.40 [15.87, 25.83] | 11 | 4.40 [2.47, 7.71] | 3 | 1.20 [0.41, 3.47] |
| W12 | 305 | 49 | 16.07 [12.37, 20.60] | 7 | 2.30 [1.12, 4.66] | 8 | 2.62 [1.33, 5.09] |
| W13 | 384 | 51 | 13.28 [10.25, 17.04] | 16 | 4.17 [2.58, 6.66] | — | NULL |
| W14 | 300 | 40 | 13.33 [9.95, 17.65] | 16 | 5.33 [3.31, 8.49] | — | NULL |
| W15 | 266 | 49 | 18.42 [14.22, 23.52] | 7 | 2.63 [1.28, 5.33] | — | NULL |
| W16 | 278 | 49 | 17.63 [13.60, 22.54] | — | NULL | — | NULL |

Source: `part1_03_classic_retention_weekly.csv`; figure
`outputs/figures/part1_01_classic_retention_weekly.png`, drawn from that table, with
ineligible cohorts as gaps rather than zeros.

**On the pattern in D1.** The three highest D1 cohorts are the three earliest, and the
series is lower in the second half of the window than the first. This report does not
read that as a decline in retention. §2 records that the per-day sampling fraction is
unknown and may not be uniform, so a change in a rate across weeks cannot be separated
from a change in what the sample captured; and the intervals on adjacent cohorts overlap
heavily throughout. The pattern is stated because it is visible in the committed table
and a reader will see it; no cause is offered for it.

---

## 5. Rolling retention — the secondary figures, and what bounds them

### 5.1 The limitation belongs to the table, so it is printed in the table

Rolling retention counts any event **on or after** install day + *N*, so its value depends
on how much window remains after that day. The eligibility rule in §3.3 removes the cells
with **no** observable window; it does not make the surviving cells comparable with one
another. Both rolling tables therefore carry the remaining observation window beside every
cell — the days left after day *N* for the cohort's **last** installer and for its
**first**.

That column also makes the eligibility rule visible arithmetic: **a cell is `NULL`
exactly when its minimum falls below 1.** W16 at D7 shows −4; W13 at D30 shows −6. And
W12 at D30 shows **1**, which is why it qualifies at all.

**The distinction worth carrying away, because it generalises beyond this dataset:
binding an eligibility rule to a window-bounded metric fixes measurability, not
comparability.** A cohort that cannot be observed to install + *N* should not be measured
at *N*, and the rule correctly removes it. But among the cohorts that survive, the metric
still means something different for each, and no eligibility rule of that shape can
repair it. Classic retention is immune, because it needs the single day install + *N* and
nothing after it — which is why §10.5.3 made classic primary.

### 5.2 Pooled

| Horizon | Cohorts pooled | Retained | Denominator | Rate % | 95% Wilson | Observation days left after day N |
|---|:-:|---:|---:|---:|---|---|
| **D1** | 16 | 1,970 | 4,191 | **47.01** | [45.50, 48.52] | 2 to 113 |
| **D7** | 15 | 1,136 | 3,913 | **29.03** | [27.63, 30.47] | 3 to 107 |
| **D30** | 12 | 449 | 2,963 | **15.15** | [13.91, 16.49] | 1 to 84 |

Source: `part1_06_rolling_retention_pooled.csv`. **These pooled figures blend cohorts with
very different observation windows** — at D7, from 3 days of opportunity to 107 — so each
is a weighted average over unlike quantities rather than an estimate of one quantity.
They are reported because §10.5.3 requires both definitions, and they should be read as
the upper of two bounds on the same population, never as a headline.

### 5.3 By weekly cohort

**D1**

| Cohort | n | Retained | Rate % [95% Wilson] | Observation days left after day 1 (last installer → first) |
|---|---:|---:|---|---|
| W01 | 176 | 102 | 57.95 [50.57, 65.00] | 107 → 113 |
| W02 | 181 | 96 | 53.04 [45.78, 60.17] | 100 → 106 |
| W03 | 95 | 56 | 58.95 [48.90, 68.30] | 93 → 99 |
| W04 | 212 | 126 | 59.43 [52.71, 65.82] | 86 → 92 |
| W05 | 271 | 149 | 54.98 [49.03, 60.79] | 79 → 85 |
| W06 | 245 | 132 | 53.88 [47.62, 60.01] | 72 → 78 |
| W07 | 267 | 147 | 55.06 [49.06, 60.91] | 65 → 71 |
| W08 | 415 | 214 | 51.57 [46.77, 56.34] | 58 → 64 |
| W09 | 305 | 160 | 52.46 [46.86, 58.00] | 51 → 57 |
| W10 | 241 | 136 | 56.43 [50.12, 62.54] | 44 → 50 |
| W11 | 250 | 115 | 46.00 [39.93, 52.19] | 37 → 43 |
| W12 | 305 | 114 | 37.38 [32.14, 42.93] | 30 → 36 |
| W13 | 384 | 141 | 36.72 [32.05, 41.65] | 23 → 29 |
| W14 | 300 | 102 | 34.00 [28.87, 39.53] | 16 → 22 |
| W15 | 266 | 97 | 36.47 [30.91, 42.41] | 9 → 15 |
| W16 | 278 | 83 | 29.86 [24.78, 35.48] | 2 → 8 |

**D7**

| Cohort | n | Retained | Rate % [95% Wilson] | Observation days left after day 7 (last installer → first) |
|---|---:|---:|---|---|
| W01 | 176 | 54 | 30.68 [24.34, 37.85] | 101 → 107 |
| W02 | 181 | 57 | 31.49 [25.17, 38.58] | 94 → 100 |
| W03 | 95 | 39 | 41.05 [31.70, 51.10] | 87 → 93 |
| W04 | 212 | 89 | 41.98 [35.54, 48.71] | 80 → 86 |
| W05 | 271 | 104 | 38.38 [32.79, 44.29] | 73 → 79 |
| W06 | 245 | 90 | 36.73 [30.95, 42.93] | 66 → 72 |
| W07 | 267 | 100 | 37.45 [31.86, 43.40] | 59 → 65 |
| W08 | 415 | 128 | 30.84 [26.59, 35.45] | 52 → 58 |
| W09 | 305 | 100 | 32.79 [27.76, 38.24] | 45 → 51 |
| W10 | 241 | 83 | 34.44 [28.73, 40.64] | 38 → 44 |
| W11 | 250 | 61 | 24.40 [19.49, 30.09] | 31 → 37 |
| W12 | 305 | 69 | 22.62 [18.28, 27.64] | 24 → 30 |
| W13 | 384 | 81 | 21.09 [17.31, 25.45] | 17 → 23 |
| W14 | 300 | 56 | 18.67 [14.66, 23.46] | 10 → 16 |
| W15 | 266 | 25 | 9.40 [6.45, 13.51] | 3 → 9 |
| W16 | 278 | — | NULL | -4 → 2 |

**D30**

| Cohort | n | Retained | Rate % [95% Wilson] | Observation days left after day 30 (last installer → first) |
|---|---:|---:|---|---|
| W01 | 176 | 27 | 15.34 [10.76, 21.40] | 78 → 84 |
| W02 | 181 | 42 | 23.20 [17.65, 29.87] | 71 → 77 |
| W03 | 95 | 19 | 20.00 [13.19, 29.14] | 64 → 70 |
| W04 | 212 | 51 | 24.06 [18.80, 30.24] | 57 → 63 |
| W05 | 271 | 55 | 20.30 [15.94, 25.48] | 50 → 56 |
| W06 | 245 | 51 | 20.82 [16.20, 26.33] | 43 → 49 |
| W07 | 267 | 48 | 17.98 [13.84, 23.03] | 36 → 42 |
| W08 | 415 | 53 | 12.77 [9.90, 16.33] | 29 → 35 |
| W09 | 305 | 43 | 14.10 [10.64, 18.45] | 22 → 28 |
| W10 | 241 | 27 | 11.20 [7.81, 15.81] | 15 → 21 |
| W11 | 250 | 15 | 6.00 [3.67, 9.66] | 8 → 14 |
| W12 | 305 | 18 | 5.90 [3.77, 9.13] | 1 → 7 |
| W13 | 384 | — | NULL | -6 → 0 |
| W14 | 300 | — | NULL | -13 → -7 |
| W15 | 266 | — | NULL | -20 → -14 |
| W16 | 278 | — | NULL | -27 → -21 |

Source: `part1_05_rolling_retention_weekly.csv`; figure
`outputs/figures/part1_02_rolling_retention_weekly.png`.

**This series cannot be read as a trend.** Rolling D7 falls from 30.68% at W01 to 9.40%
at W15 while the window left to the last installer falls from 101 days to 3. The decline
is what a shrinking observation window produces mechanically. No behavioural reading of
it is available from this data, and the report offers none.

---

## 6. Retention by segment

Segmentation is applied to **pooled cohorts only** and is never crossed with the weekly
cohorts: 4,191 installs over 16 weeks and 5 countries is about 54 users per cell, below
the suppression floor for most cells. It covers the **classic** metric, the primary one.

Five dimensions are permitted and all five survived: `geo.country`, `platform`,
`device.category`, `device.language`, `app_info.version`. Two families were dropped before
this build began, on the recon's field profiles
(`outputs/tables/recon_07_field_profiles.csv`):

- **`geo.region` is dropped** at **88.57%** null.
- **`traffic_source.name`, `.medium` and `.source` are dropped**, and this is the single
  descriptive line that documents why: each is essentially one bucket plus a placeholder —
  `(direct)` at 75.25% of events with a further 24.66% null on `.name`; `(none)` at 75.25%
  with `organic` at 24.54% on `.medium`; `(direct)` at 75.25% with `google-play` at 24.14%
  on `.source`. A dimension with one real bucket cannot distinguish cohorts, so **no metric
  in this report is segmented by traffic source.**

A segment is named individually only at **≥ 100 users** in the pooled install population.
Everything below that floor is pooled into a single **"Other"** row with its own count and
the number of segments it holds — never dropped, because a dropped row silently changes
the denominator. The floor was applied **once**, on the pooled install population, so the
three horizon columns describe the same partition and can be read across. Within each
segment the per-horizon denominators still differ, and each is printed.

**`geo.country`**

| Segment | Users | D1 | D1 % [95% Wilson] | D7 | D7 % [95% Wilson] | D30 | D30 % [95% Wilson] |
|---|---:|---:|---|---:|---|---:|---|
| United States | 1,495 | 349/1495 | 23.34 [21.27, 25.56] | 98/1394 | 7.03 [5.80, 8.49] | 33/1128 | 2.93 [2.09, 4.08] |
| India | 755 | 162/755 | 21.46 [18.68, 24.53] | 28/713 | 3.93 [2.73, 5.62] | 9/539 | 1.67 [0.88, 3.14] |
| Japan | 201 | 53/201 | 26.37 [20.76, 32.86] | 17/184 | 9.24 [5.85, 14.30] | 3/116 | 2.59 [0.88, 7.33] |
| Canada | 149 | 28/149 | 18.79 [13.33, 25.82] | 10/138 | 7.25 [3.98, 12.83] | 0/104 | 0.00 [0.00, 3.56] |
| Australia | 145 | 32/145 | 22.07 [16.09, 29.49] | 11/138 | 7.97 [4.51, 13.71] | 0/84 | 0.00 [0.00, 4.37] |
| Other (110 segments pooled) | 1,446 | 287/1446 | 19.85 [17.87, 21.98] | 58/1346 | 4.31 [3.35, 5.53] | 17/992 | 1.71 [1.07, 2.73] |

**`platform`**

| Segment | Users | D1 | D1 % [95% Wilson] | D7 | D7 % [95% Wilson] | D30 | D30 % [95% Wilson] |
|---|---:|---:|---|---:|---|---:|---|
| ANDROID | 2,799 | 643/2799 | 22.97 [21.45, 24.57] | 154/2629 | 5.86 [5.02, 6.82] | 44/2160 | 2.04 [1.52, 2.72] |
| IOS | 1,392 | 268/1392 | 19.25 [17.27, 21.41] | 68/1284 | 5.30 [4.20, 6.66] | 18/803 | 2.24 [1.42, 3.52] |

**`device.category`**

| Segment | Users | D1 | D1 % [95% Wilson] | D7 | D7 % [95% Wilson] | D30 | D30 % [95% Wilson] |
|---|---:|---:|---|---:|---|---:|---|
| mobile | 3,238 | 731/3238 | 22.58 [21.17, 24.05] | 165/3016 | 5.47 [4.71, 6.34] | 47/2239 | 2.10 [1.58, 2.78] |
| tablet | 953 | 180/953 | 18.89 [16.53, 21.50] | 57/897 | 6.35 [4.94, 8.14] | 15/724 | 2.07 [1.26, 3.39] |

**`device.language`**

| Segment | Users | D1 | D1 % [95% Wilson] | D7 | D7 % [95% Wilson] | D30 | D30 % [95% Wilson] |
|---|---:|---:|---|---:|---|---:|---|
| en-us | 2,045 | 476/2045 | 23.28 [21.50, 25.16] | 121/1902 | 6.36 [5.35, 7.55] | 35/1497 | 2.34 [1.69, 3.23] |
| en-gb | 576 | 113/576 | 19.62 [16.58, 23.06] | 26/546 | 4.76 [3.27, 6.89] | 10/446 | 2.24 [1.22, 4.08] |
| ja-jp | 192 | 52/192 | 27.08 [21.29, 33.77] | 16/178 | 8.99 [5.61, 14.10] | 3/112 | 2.68 [0.92, 7.58] |
| en-in | 171 | 39/171 | 22.81 [17.16, 29.65] | 10/164 | 6.10 [3.35, 10.86] | 2/117 | 1.71 [0.47, 6.02] |
| en-au | 143 | 35/143 | 24.48 [18.16, 32.13] | 8/134 | 5.97 [3.06, 11.34] | 1/81 | 1.23 [0.22, 6.67] |
| en-ca | 124 | 25/124 | 20.16 [14.05, 28.07] | 11/117 | 9.40 [5.33, 16.05] | 0/87 | 0.00 [0.00, 4.23] |
| Other (124 segments pooled) | 940 | 171/940 | 18.19 [15.86, 20.79] | 30/872 | 3.44 [2.42, 4.87] | 11/623 | 1.77 [0.99, 3.13] |

**`app_info.version`**

| Segment | Users | D1 | D1 % [95% Wilson] | D7 | D7 % [95% Wilson] | D30 | D30 % [95% Wilson] |
|---|---:|---:|---|---:|---|---:|---|
| 2.62 | 2,775 | 642/2775 | 23.14 [21.60, 24.74] | 154/2614 | 5.89 [5.05, 6.86] | 44/2146 | 2.05 [1.53, 2.74] |
| 2.6.31 | 985 | 171/985 | 17.36 [15.12, 19.85] | 52/880 | 5.91 [4.53, 7.67] | 11/434 | 2.53 [1.42, 4.48] |
| 2.6.30 | 315 | 91/315 | 28.89 [24.16, 34.12] | 12/314 | 3.82 [2.20, 6.56] | 6/306 | 1.96 [0.90, 4.21] |
| Other (22 segments pooled) | 116 | 7/116 | 6.03 [2.95, 11.93] | 4/105 | 3.81 [1.49, 9.39] | 1/77 | 1.30 [0.23, 7.00] |

Source: `part1_07_retention_by_segment.csv`; figure
`outputs/figures/part1_04_retention_by_segment.png`. Every dimension's denominators sum
exactly to the pooled denominator at all three horizons — which is what pooling sub-floor
segments rather than dropping them is for, and what `verify.py` asserts.

**How to read these.** The intervals overlap heavily almost everywhere. The widest
separations are at D1 — ANDROID 22.97% against IOS 19.25%, mobile 22.58% against tablet
18.89% — and even there the intervals nearly touch. Nothing in this table supports a
claim that one segment retains better than another in a way a product decision could rest
on; what it supports is the observation that no segment behaves wildly unlike the pooled
figure, which is a weaker and more defensible statement.

**Attribution is by the user's earliest event row**, ties broken by lowest
`event_timestamp` then alphabetically lowest `event_name` — one deterministic rule.
For `app_info.version` that means **version at install**, and §8.3 records what follows
from it.

---

## 7. Data handling

| | |
|---|---|
| Raw event rows | 5,700,000 |
| Duplicate rows removed | **207** (**36 ppm**) |
| Duplicate groups straddling two dates | **0** |
| Users where the two readings of install day disagree | **0** |
| Cells suppressed by the n = 30 floor | **0** of 96 |

Source: `part1_08_data_handling.csv`.

**Duplicates are removed here, and kept in Part 3 — deliberately.** Part 1 de-duplicates
on (`user_pseudo_id`, `event_name`, `event_timestamp`) before any count. Part 3's §5.1
keeps its suspicious row, because removing a row from a randomised experiment after
assignment breaks intention-to-treat. There is no randomisation and no ITT here: a
duplicated log row is not an observation of anything, and while 36 ppm cannot move a
rate, distinct-user counts and per-user event counts are both sensitive to exact
duplication. The two rules differ because the reason for Part 3's rule is absent here,
not because one of them is a mistake.

**"A user" means a device-install.** `user_id` is NULL on all 5,700,000 rows, so
`user_pseudo_id` is the only identifier available. One person on two devices is two users
here; a reinstall may be a new user. **No cross-device claim, no unique-people claim and
no deduplication of people is possible in this report**, and the word "users" above should
be read in those terms throughout.

**No session-level metric is reported.** No session identifier exists anywhere in this
export — not among the 52 `event_params` keys, not among the 25 `user_properties` keys. A
`session_start` event exists but carries no id, and its own volume argues against trusting
it as a boundary: 74,353 events across 12,261 users, a median of 2 per user, against
5,700,000 total events. Defining a session from an inactivity threshold was considered and
rejected: it would produce a session count that is an artefact of the threshold, sitting
among numbers that are measurements. The question of what a session is on this export is
**permanently unanswerable**, and this report says so rather than leaving the absence to
be noticed.


---

## 8. What this does not support

This section is placed after the results and before anything a reader might act on,
deliberately: the boundaries of the claim should be known before the claim.

### 8.1 Not answerable from this data at all

- **Real traffic, at any grain.** Every shard holds exactly 50,000 rows, so installs per
  week, users per week and events per day are properties of the sample. Nothing here
  measures how many people installed or played this game on any day.
- **Acquisition, growth or decline.** Because volume is capped, the four-fold spread in
  weekly install counts carries no information about acquisition. A reader who takes W08's
  415 installs as a good week and W03's 95 as a bad one has been misled by the sample.
- **The 71.54% of the sample without a `first_open` event.** They are excluded by
  construction and no retention figure here describes them. The exclusion is not random,
  and its direction can be stated: a user with events but no `first_open` in the window
  either installed before 20180612 or lost the event to the sampling, and either way the
  4,319 measured here are systematically newer than the 10,856, who are to that extent an
  established base. An established base retains better than new installs. **Therefore the
  retention figures in this report sit below what a whole-population view would show —
  they understate it.** By how much is unknown, and this report does not estimate it;
  §8.2 reports the one probe available.
- **Anything about people.** `user_id` is NULL on every row, so every count is of
  device-installs. Two devices belonging to one person are two users here, and a reinstall
  may be a new user. No unique-people figure can be produced from this export at all.
- **Anything about sessions.** No session identifier exists in either key space, so
  sessions per user, session length and session-gap analysis are not available, and no
  amount of care recovers them — they would have to be invented from an inactivity
  threshold, which would be a number about the threshold rather than about the game.
- **Anything past day 30, or past 20181003.** The window ends, and four cohorts cannot be
  observed even to day 30. D60, D90 and long-run churn are out of reach.
- **Why retention is what it is.** This report has an install event, an activity date and
  five attribution fields. It has no content, no difficulty, no progression state and no
  price. It can say that D7 classic retention is 5.67%; it cannot say what would move it.

### 8.2 Answered only under stated assumptions

**The `first_open_time` sensitivity check, and the full history of the rule that let it
run.** §10.7.3 requires one check on what the 71.54% exclusion costs: derive install day
from the `first_open_time` user property for all 15,175 users, recompute pooled D7, and
run it only if that derived date agrees with the `first_open` event's `event_date` for at
least **99.0%** of the 4,319 users who have both. The result, from
`part1_08_data_handling.csv`:

| | |
|---|---|
| Agreement on users who have both | **4,306 of 4,319 = 99.70%** (gate: 99.0%) |
| Derived install day before the window | 9,106 users |
| Derived install day inside the window | 5,938 users |
| **Pooled D7 over the property population** | **6.13%** [5.53, 6.79] on 5,611 |
| Primary pooled D7, for comparison | 5.67% [4.99, 6.44] on 3,913 |

**This figure was obtained under a rule this session changed after seeing data, and the
disclosure is therefore maximal rather than minimal — because the result is
reassuring, and a reassuring number obtained under a post-hoc rule is exactly the
combination that deserves the most scrutiny.** What happened, in order:

1. Before any query ran, A-141 fixed how the property's timestamp would be dated: in the
   whole-hour UTC offset shown to be **consistent with `event_date` on all 5,700,000
   rows**. Its stated principle was conservatism — where several offsets qualified, the
   **minimum** agreement across them would be taken, **so that the check could not run on
   a favourable choice of zone**.
2. The day-key query then established that **no constant offset fits at all**: the
   feasible interval is **empty by 93 seconds** (§3.1). A-141's criterion therefore
   selected **no zone**, and on the first rendering pass the check was **omitted** and the
   agreement share reported in its place.
3. That outcome would have voided a check §10.7.3 requires Part 1 to attempt and report
   **either way**, for a reason that has nothing to do with `first_open_time` and
   everything to do with a rule this session wrote. A-142 therefore replaced the criterion
   with **highest row-level agreement**, which selects **UTC−07:00**.
4. **A-142 was written with the agreement figures at the head of this section — the
   99.70% and the 6.13% — already visible.** Under the original rule the check was
   omitted; under the replacement it runs.
5. **The replacement inverts the principle of the rule it supersedes.** A-141 chose the
   *minimum* agreement among qualifying zones precisely so a favourable zone could not
   enable the check; A-142 selects the zone with the *highest* agreement. That inversion
   is real and is not explained away here.
6. What limits the damage, and a reader should weigh it themselves: the zone rests on the
   **day-key query alone**, which measures `event_date` against `event_timestamp` and
   knows nothing about `first_open_time`. On that query UTC−07:00 leads the next-best
   offset by **149,335 rows** — 99.9785% against 97.3586% — and that margin was measured
   **before** the agreement figures existed. A-141's tie-break survives in the
   replacement, and would still take the lower share if two zones ever tied.
7. One claim this report does **not** make: that the runner-up zone would have failed the
   99.0% gate. That is an **inference** from its row-level agreement, not a measurement —
   the agreement figure at UTC−06:00 was never run against the gate, and re-running to
   settle it was judged not worth the bytes for a zone that dates 97.3586% of rows where
   the selected one dates 99.9785%.

**What the check therefore supports, and what it does not.** It suggests that extending to
the property population moves pooled D7 by about half a percentage point **upward**, not
by a factor, so the event-based restriction does not look like it is concealing a wildly
different population at this horizon. It cannot establish that, for two reasons that hold
whatever the zone: the 99.70% agreement is measured only on users who have **both**, and
those are by definition the users whose install the window observed — the agreement says
nothing about the 10,856 it is being extended to; and the property's semantics remain
undocumented. The figure stays in this section and appears in no results table.

**The 9,106 derived pre-window installs are consistent with §1's stated mechanism, not
evidence for it.** They are the same unverified field making the claim.

**Two readings of the specification were directed rather than derived**, and both change
numbers in this report:

- **Pooled denominators are the union of the cohorts eligible at each horizon**, not every
  individually observable install. §10.5.5 admits both readings without adjudicating.
  Under the reading used, pooled D7 is W01–W15 exactly and the **85** W16 installs of
  20180925–26, which are individually observable at D7, are excluded with their cohort and
  reported in the inventory. The gain is that every pooled figure is the plain sum of its
  weekly cells; the cost is those 85 installs. D1 and D30 are identical under both
  readings.
- **Eligibility binds the rolling table identically to classic**, at 16 / 15 / 12.
  §10.5.3 and §10.5.5 do not say whether it governs the secondary metric. Under the other
  reading the rolling table would carry all 16 cohorts at every horizon, with the shortest
  windows producing the most truncated figures. §5.1 is the consequence of the reading
  used.

Both are recorded as `challenge` entries — A-134 and A-135 — because an ambiguity in the
specification is not a build session's to settle.

### 8.3 Confounds and unverifiable properties that remain

- **The sampling fraction may vary by day.** If it does, even rate comparisons across
  weeks are affected, and §4.2's pattern in D1 could be an artefact of it. Unresolvable
  from the data.
- **How `event_date` is assigned is undocumented.** It is perfectly consistent with its
  shard, but 1,223 rows sit where no constant UTC offset would put them. Whatever rule
  produced them is unknown, and a user whose activity straddles a local midnight could in
  principle be attributed to a neighbouring day.
- **`app_info.version` is version at install.** §10.7.5 permits it as a segment dimension
  and requires a constancy check for `geo.country` only. Measured here:
  **1.97%** of the install population has a non-constant `app_info.version`, against
  **1.62%** for `geo.country`. The dimension without a constancy test varies more than the
  one with it — and at 1.97% the gap costs this dataset essentially nothing. It is
  recorded as a challenge about method (A-136), not as a result.
- **Rolling retention stays window-bounded** after eligibility, per §5.1. Its weekly
  series is not a trend and its pooled figures blend unlike quantities.
- **Cohort composition may shift across the window.** The country, language and device mix
  of W01's installs need not match W16's, and this report does not hold them constant.
  A segment table crossed with the weekly cohorts would be the way to check, and §10.7.5
  forbids it at about 54 users per cell.
- **The window is a 114-day slice of the title's life.** Any live-ops event, store feature
  or release inside it is invisible here and could move a cohort's retention on its own.
- **Device-install identity** (§7) contaminates every count in a direction that cannot be
  measured: a person who reinstalls appears as a new install with a fresh `first_open`,
  and would be counted as a new cohort member.

### 8.4 What would be required to answer these questions properly

Each item names a measurement, not an aspiration.

- **A sampling manifest from the export's producer** stating the per-day fraction and the
  method. That single document would turn every install count in §3.2 into a traffic
  figure and would settle whether cross-week rate comparison is safe.
- **An install event emitted for every user, or a server-side install log keyed to
  `user_pseudo_id`.** This is what removes the 71.54% exclusion, and it is the single
  highest-value addition available — it converts Part 1 from a recent-installer slice into
  a population analysis.
- **Documentation of what `first_open_time` records and when it is written.** That turns
  §8.2's probe into an answer and would let the property carry the cohort definition it
  cannot carry now.
- **A `ga_session_id` parameter on every event.** Sessions per user, session length and
  session-gap analysis all become available the moment it exists, and none of them is
  available without it.
- **Thirty further days of shards beyond the last install day** — W16's last install day
  is 20181001, so shards through 20181031. That makes D30 measurable for all 16 cohorts
  and collapses the rolling censoring gradient in §5.
- **A stable `user_id` across devices**, which is what converts every count in this report
  from device-installs into people.
- **A documented rule for how `event_date` is assigned to an event**, which would explain
  the 1,223 rows and let a reader decide whether day-boundary attribution needs care.

---

## 9. Reproducing this

```bash
# authenticate as a user, never a service account; no credential file enters this repo
gcloud auth login
gcloud auth application-default login

# the project id lives in the environment and in no committed file
GOOGLE_CLOUD_PROJECT=<your sandbox project> ./run_part1.sh
```

`run_part1.sh` dry-runs every query, gates it against the byte ceilings, executes it,
reads the **actual** bytes billed from job statistics, writes each result with a
`.meta.json` provenance sidecar, appends a ledger row, and then renders the tables,
figures and self-verification.

**What this cost.** Nine queries, no re-runs: **4,604,297,216 bytes billed = 4.288 GiB**,
against a 20 GiB per-session ceiling (21.4%) and a 40 GiB ceiling for both build sessions
(10.7%). The largest single query billed 0.869 GiB against a 4 GiB per-query ceiling. The
predicted cost, `max(10 MiB, ceil(estimate → MiB))`, matched the actual billed bytes with
a difference of **exactly 0 on 9 of 9**. Full ledger: `part1_budget_ledger.csv`.

**Reproducibility, at the strength it can honestly be claimed.** These outputs come from
an external table that no checksum covers, so they are exempt from the byte-identity rule
that governs Part 3 and carry provenance instead: each result file's sidecar records the
shard range, the job date, the dry-run estimate, the actual bytes billed and the row
count. Figures are generated from the committed tables, never from a recomputation, so
their numbers reproduce even where their pixels do not.
