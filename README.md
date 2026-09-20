We tested whether moving Cookie Cats' progression gate from level 30 to level 40 changes player retention, across 90,189 players split between the two placements, measured at 1 and 7 days after install. Moving the gate to level 40 lowered 7-day retention by 0.82 percentage points, from 19.02% to 18.20%, with a 95% interval running from 1.34 to 0.31 percentage points of lost retention. Keep the gate at level 30; the one thing that would change this is revenue data, because a gate exists to drive monetization and this experiment contains no monetization fields at all.

---

## Part 1 — Retention and install cohorts

**Among the 4,319 users with an observed install event — not the 15,175 in the
sample — classic retention is 21.74% at day 1, 5.67% at day 7 and 2.09% at day
30.** Full analysis in
[`reports/part1_retention_cohorts.md`](reports/part1_retention_cohorts.md).

| | |
|---|---|
| Population | 4,319 users with an observed `first_open` event, of 15,175 in the sample |
| Excluded | 10,856 users with no install event in the window — **71.54%**, and not a random slice |
| Metric | Classic retention: at least one event on install day + N exactly |
| D1 | **21.74%**, 95% Wilson [20.51, 23.01], n = 4,191 across 16 cohorts |
| D7 | **5.67%**, 95% Wilson [4.99, 6.44], n = 3,913 across 15 cohorts |
| D30 | **2.09%**, 95% Wilson [1.64, 2.67], n = 2,963 across 12 cohorts |
| Cohorts | 16 fixed 7-day blocks from 20180612; the 20181002–03 tail (128 installs) is excluded |
| Sampling | Every shard holds exactly **50,000 rows**, so no install count here is a traffic figure |

Rolling retention is reported in §5 of the report and is deliberately not
summarised here: its weekly series is not a trend and its pooled figures blend
differently-censored cohorts, and a table cell carries neither caveat.

Every figure above comes from a file in [`outputs/`](outputs/); none was typed in
by hand.

### What makes this analysis checkable

The definitions came first. `ARCHITECTURE.md` §10.5 fixes the population, the day
key, both retention definitions, the weekly grain, the eligibility cutoffs and the
n = 30 suppression floor, and it was committed in `5b2c0ba` before any retention
number existed. The judgement calls this build made on top of it were appended to
`assumptions.md` and committed in `6a2fb35` **before the first query ran**.
`git log` is the evidence.

That ordering does real work here too. The observation window leaves 16 cohorts
measurable at D1, 15 at D7 and 12 at D30; the 5 cells it rules out in the weekly
table print an explicit `NULL`, while four cells across the weekly and segment
tables are **measured zeros** — cohorts that were observable at day 30 and had
nobody return. A reader who could not tell those apart would draw a conclusion
the data does not support.

One rule was changed mid-flight. The zone used to date an unverified field was
picked by a criterion that turned out to be unsatisfiable, and the replacement
was written after the figures it affects were visible. §8.2 of the report sets
out that sequence in full, including what argues against it.

## Part 2 — Progression funnel

**Among all 15,175<!--fig:pop_users--> users present in the window — not Part 1's 4,319<!--fig:pop_with_first_open-->-user install cohort — 66.99%<!--fig:s1_share_of_s0--> started a level, 53.67%<!--fig:s2_share_of_s0--> finished an attempt and 37.38%<!--fig:s3_share_of_s0--> completed one.**
Full analysis in
[`reports/part2_progression_funnel.md`](reports/part2_progression_funnel.md).

**This is a progression funnel, and this sample does not support a revenue
analysis.** It carries 27<!--fig:rescope_events--> revenue-positive purchase events from 27<!--fig:rescope_users--> users — 0.178%<!--fig:rescope_coverage_pct--> of users against the 0.5% bar `ARCHITECTURE.md` §10.3 fixed before the data was queried — and that count is a **lower bound, not a census**: the revenue field is absent from 15<!--fig:rescope_shards_without_usd--> of the 114<!--fig:shard_count--> daily shards.

<!--table:readme_summary-->
|  |  |
|---|---|
| Population | 15,175 users with at least one event in the window — everyone in the sample, none excluded |
| Counting unit | Per user, whole-window presence; `first_open` is not a step |
| S0 — present in the window | **15,175** &middot; 100.00%, by construction |
| S1 — started a level | **10,166** &middot; 66.99% of S0, 95% Wilson [66.24, 67.74] |
| S2 — finished an attempt | **8,145** &middot; 53.67% of S0 &middot; 80.12% of S1, 95% Wilson [79.33, 80.88] |
| S3 — completed a level | **5,672** &middot; 37.38% of S0 &middot; 69.64% of S2, 95% Wilson [68.63, 70.63] |
| Revenue | **Not answerable.** 27 revenue-positive purchase events from 27 users — 0.178% of users against a 0.5% bar, and that count is a floor |
| Sampling | Every shard holds exactly **50,000** rows, so no count here is a traffic figure |
<!--/table-->

Two results are left out of the table, because a cell carries neither asymmetry. 202<!--fig:le_users_shortfall--> users record the end of a level attempt with neither outcome event, while exactly 1<!--fig:le_outcome_without_end--> records an outcome with no end (§6). And 1,955<!--fig:track_without_s1_with_np--> of the 5,009<!--fig:track_without_s1--> users this funnel counts as never starting a level did start one in a parallel mode the funnel does not cover (§9.1).

Every figure above comes from a file in [`outputs/`](outputs/); none was typed in
by hand.

### What makes this analysis checkable

The definitions came first. `ARCHITECTURE.md` §10.6 fixes the population, the
counting unit, the four steps, the strict-cumulative rule and both reporting
triggers, and it was committed before any funnel query ran. The judgement calls
this build made on top of it were appended to `assumptions.md` and committed
**before the first query ran**. `git log` is the evidence.

Every number in the report is checked against the **specific table cell it claims
to come from**, not against the outputs as a whole. Tables are generated from
their CSVs and verified by regenerating them; each prose figure names its own
cell; and the check is tested on every run against planted failures, including
the one that got past Part 1's audit, where a wrong count survived because its
digits appeared elsewhere in the outputs.

One rule could not be applied as written. §10.6.5 requires a reconciliation "at
both event and user level" but fixes only the event-level arithmetic, which does
not translate to users. §6.3 of the report names all three readings, records
which was directed, and leaves the choice to the architecture session.

## Part 3 — A/B test: gate placement and retention

**Recommendation: keep the gate at level 30.** Full analysis in
[`reports/part3_cookie_cats_experiment.md`](reports/part3_cookie_cats_experiment.md).

| | |
|---|---|
| Design | Two arms, `gate_30` (control) vs `gate_40` (variant), 90,189 players |
| Primary metric | 7-day retention, pre-registered as the sole decision-eligible test |
| Effect on D7 | −0.82 pp (19.02% → 18.20%), 95% interval [−1.34, −0.31] pp |
| p-value | 0.00155, two-sided, alpha 0.05 |
| Guardrail (D1) | −0.59 pp, 95% interval [−1.25, 0.05] pp — contains zero, no test |
| Sample ratio mismatch | exact binomial p = 0.00869, above the 0.001 failure threshold |
| Decision path | Stage 1 clean → Stage 2 **R3** → Stage 3 **R10** |

Every figure above comes from a file in [`outputs/`](outputs/); none was typed in
by hand.

### What makes this analysis checkable

The decision rule was fixed **before the data was loaded**. `ARCHITECTURE.md`
specifies the primary metric, alpha, the 1.00 pp action threshold, the SRM
protocol, the data-handling policy, and a three-stage rule that maps any possible
result onto a recommendation. It was committed in
`c6d72f834359fba8b8748a0d7251592a8cab80c5`, which contains that file,
`assumptions.md` and `.gitignore` and nothing else, four commits before the
dataset's checksum was recorded. `git log` is the evidence.

That ordering does real work here. The SRM p-value is 0.00869 — significant at
the conventional 0.05, and not at the 0.001 threshold the pre-registration fixed
sight-unseen. The report explains why 0.001 was chosen and what the check does
and does not establish.

`assumptions.md` is an append-only log of every judgement call, with the
alternatives considered and why each lost. It is never edited, only added to.

### Setup and reproduction

From a clean checkout, this sequence reproduces every number, table and figure:

```bash
# Any source of a CPython 3.12 interpreter works — pyenv, python.org, a distro
# package. Homebrew is what this project was built with:
brew install python@3.12

python3.12 -m venv .venv    # or "$(brew --prefix python@3.12)/bin/python3.12"
./.venv/bin/python -m pip install -r requirements.lock.txt
./.venv/bin/python --version   # expect 3.12.x
```

If `python3.12` is not on your `PATH` after installing, invoke it by full path.
On Apple Silicon that is `/opt/homebrew/bin/python3.12`; on Intel macOS it is
`/usr/local/bin/python3.12`. The minor version is what matters — the run stops if
it is not 3.12 — and the exact patch version used to produce these outputs is
recorded in `assumptions.md` A-054.

Fetch the dataset into `data/raw/`. It is not committed — redistributing a Kaggle
dataset is not ours to grant — so `data/raw/` is git-ignored and the file's
SHA-256 is recorded in `assumptions.md` A-072 instead:

```bash
kaggle datasets download -d mursideyarkin/mobile-games-ab-testing-cookie-cats -p data/raw --unzip
shasum -a 256 data/raw/cookie_cats.csv
# expect 5ab54d761fbddcd50de7b88e4eaf7837cba4569474f50c043a4d17ee342c46bd
```

The Kaggle CLI is deliberately not in `requirements.txt`: it is a fetch tool, not
part of the analysis environment the lock file certifies. Install it however you
like, outside this project's virtual environment.

Then run the whole part with one command:

```bash
./run_part3.sh
```

The run verifies the input checksum before computing anything, and finishes by
re-reading its own outputs to assert that the data-handling assertions held, that
every reported denominator equals the row count recorded for it, that exactly one
decision branch fired, and that the recorded recommendation is the one the rule
produces from the same inputs.

On reproducibility, separating what was built for from what has been checked.
The tables and the run manifest are **built for** cross-machine byte-identity:
fixed column order, explicit float formatting, `\n` line terminators, sorted JSON
keys, and no locale, path or timestamp leakage, the manifest's run timestamp
excepted. What has actually been **verified** is narrower — re-running on this
machine with this lock file reproduces every table and every PNG byte-identically.
Whether the tables are byte-identical on a different machine is a reasonable
expectation from the way they are written, not a result anyone has confirmed, and
it is stated here as the former.

Figures are a separate case and a weaker guarantee on purpose: matplotlib does not
produce identical PNGs across versions, platforms and font configurations, so
cross-machine pixel identity is not claimed at all. What holds instead is that
every figure is generated from a committed table, so the numbers and labels behind
it reproduce exactly even where the pixels do not, and no figure is ever the sole
record of a value.

### Repository layout

```
ARCHITECTURE.md   the pre-registration; read-only to analysis sessions
assumptions.md    append-only log of every judgement call
reports/          one write-up per part
outputs/tables/   every number in the reports, as CSV
outputs/figures/  every figure, generated from those tables
src/              analysis code; run_part3.py holds the execution order
```

---

## Dataset recon

Parts 1 and 2 run on the GA4 public sample
(`firebase-public-project.analytics_153293282.events_*`), which
`ARCHITECTURE.md` §10 deliberately leaves unspecified until the table has been
looked at. A dedicated recon pass established the facts first and stopped there;
its findings are in
[`reports/recon_ga4_sample.md`](reports/recon_ga4_sample.md).

**Headline results.** 114 contiguous daily shards, 20180612–20181003, 5,700,000
events, 15,175 distinct users. Seven of the thirteen checklist items came back
problematic:

| Finding | Consequence |
|---|---|
| `user_id` is null on every row | a "player" is a device-install; no cross-device deduplication |
| No session identifier exists at all | a return visit cannot be defined on sessions |
| 71.54% of users have events but no `first_open` | install cohorts need a stated treatment for them |
| 27 revenue-positive purchase events, 0.178% payer coverage | **Part 2 is a progression funnel, not monetization** |
| No tutorial event exists | the originally sketched funnel has no middle step |
| `geo.region` is 88.57% null | region segmentation is dropped; **country survives** |

The Part 2 scope outcome was decided by a rule fixed in `ARCHITECTURE.md` §10.3
**before the query ran**, with both thresholds and the observed counts printed
either way.

**Reproducing the pass.** It needs the Google Cloud SDK and a BigQuery-enabled
project; queries run against a public dataset and are billed to your own project
under the sandbox's free monthly tier.

```bash
brew install --cask gcloud-cli
gcloud auth login
gcloud auth application-default login
```

`bq` authenticates against the gcloud CLI account rather than against
application-default credentials, so the first command is what makes queries run;
the second satisfies §8's requirement and is what any later client would use.
Both store user credentials in `~/.config/gcloud`. **No credential file is ever
written into this repository**, and the destination project id lives only in an
environment variable:

```bash
export GOOGLE_CLOUD_PROJECT=your-project-id
```

Then run the queries in numeric order — the `NN` prefix is execution order:

```bash
bash src/recon/budget.sh seed
for q in sql/0*_recon_*.sql; do
  name="recon_$(basename "$q" .sql | sed 's/^\([0-9]*\)_recon_/\1_/')"
  bash src/recon/run_recon_query.sh "$q" "$name" "20180612-20181003 (114 shards)"
done
```

Each query is dry-run first and executed only if the estimate is within both
ceilings; actual bytes billed are then read from job statistics and accumulated.
The recon pass uses no Python and does not touch `.venv/`, `requirements.txt` or
`requirements.lock.txt` — those describe the environment Part 3's lock file
certifies, and a completed part must keep reproducing from its own recorded
environment.

**Cost.** The whole pass billed **4.90 GiB** — 2.45% of the 200 GiB budget
`ARCHITECTURE.md` §10.1 sets, and 0.48% of the sandbox's 1 TiB monthly free tier.
Billed bytes follow `max(10 MiB, ceil(processed → MiB))` exactly on every query,
and dry-run estimates matched bytes processed precisely, so no materialised
extract is needed to keep re-runs free.

**On output reproducibility.** Recon results come from an external table that no
checksum covers, so they are exempt from the byte-identity rule that governs Part
3's outputs (§9 open question 7, A-080/A-086). Each result file instead carries a
`recon_NN_<name>.meta.json` sidecar recording the shard range covered, the query
job date, the dry-run estimate, the actual bytes billed and the row count.
