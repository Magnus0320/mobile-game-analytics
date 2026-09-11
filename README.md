We tested whether moving Cookie Cats' progression gate from level 30 to level 40 changes player retention, across 90,189 players split between the two placements, measured at 1 and 7 days after install. Moving the gate to level 40 lowered 7-day retention by 0.82 percentage points, from 19.02% to 18.20%, with a 95% interval running from 1.34 to 0.31 percentage points of lost retention. Keep the gate at level 30; the one thing that would change this is revenue data, because a gate exists to drive monetization and this experiment contains no monetization fields at all.

---

## Part 1

## Part 2

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
brew install python@3.12                    # any source of a 3.12 interpreter works
/opt/homebrew/bin/python3.12 -m venv .venv
./.venv/bin/python -m pip install -r requirements.lock.txt
```

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

Tables and the run manifest reproduce byte-for-byte on any machine. Figures do
not — matplotlib does not produce identical PNGs across platforms and font
configurations — but every figure is generated from a committed table, so the
numbers behind it reproduce exactly even when the pixels do not.

### Repository layout

```
ARCHITECTURE.md   the pre-registration; read-only to analysis sessions
assumptions.md    append-only log of every judgement call
reports/          one write-up per part
outputs/tables/   every number in the reports, as CSV
outputs/figures/  every figure, generated from those tables
src/              analysis code; run_part3.py holds the execution order
```
