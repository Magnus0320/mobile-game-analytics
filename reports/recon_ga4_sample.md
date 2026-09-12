# GA4 public sample — dataset recon for Parts 1 and 2

**What this is.** The thirteen-item recon checklist of `ARCHITECTURE.md` §10.2,
executed under §10.1's protocol against
`firebase-public-project.analytics_153293282.events_*`. It establishes facts and
stops. It contains **no metric definition, cohort definition, funnel step, day
boundary or retention window**, and may not be read as proposing one — that is the
architecture session's work under §10.4.

**What this is not.** An authority for any number. Per §10.1 and A-079 the
committed CSVs in `outputs/tables/recon_*.csv` are the source of truth for every
figure, the `assumptions.md` `finding` entries are the source of truth for what a
figure means, and this document is a rendering of both. **Where this document and
a CSV disagree, the CSV wins and the discrepancy is a defect.**

Run date 2026-09-12. Shard range covered: **20180612–20181003**, 114 contiguous
shards. Every result file has a `recon_NN_<name>.meta.json` sidecar carrying its
provenance (A-086, A-093).

---

## Verdicts at a glance

| # | Item | Verdict | Headline artefact |
|---|---|---|---|
| 1 | Shard range | **problematic** | 114 contiguous shards, 20180612–20181003, no gaps — but 114 days is 16 weeks **+ 2 days** |
| 2 | `first_open` coverage | **problematic** | **71.54%** of users have events but no `first_open` (threshold: 5%) |
| 3 | Timestamp / timezone | answered | microseconds; `event_date` never ahead of UTC, 33.96% one day behind; 0.28% of users' first-touch gap exceeds a day |
| 4 | Identifier | **problematic** | `user_id` **null on all 5,700,000 rows**; `user_pseudo_id` only |
| 5 | Cohort granularity | **problematic** | median **38** `first_open` per shard (threshold: 100) |
| 6 | Session semantics | **problematic** | **no session identifier exists** in `event_params` or `user_properties` |
| 7 | Platform mix | answered | ANDROID + IOS only, mobile + tablet only, **no web on any row** |
| 8 | Duplicate events | answered | 207 duplicates = **36 ppm** (threshold: 1,000 ppm) |
| 9 | Revenue population | **problematic** | **27** revenue-positive purchase events, **0.178%** payer coverage — both §10.3 thresholds missed |
| 10 | Event vocabulary | answered | **37** event names; `in_app_purchase` **present**; **no tutorial event** |
| 11 | Funnel counting unit | **unanswered** | per-user measured for all 37 events; **per-session not computable** — no session id |
| 12 | Byte cost | answered | **4.90 GiB** billed total = 2.45% of the 200 GiB ceiling; no extract needed |
| 13 | Obfuscation / segmentability | **problematic** | `geo.region` **88.57% null** → dropped; **`geo.country` survives** |

Seven problematic, five answered, one unanswered. The three items that gate the
most downstream work — 2, 6 and 9 — are all problematic, and item 9's consequence
is fixed in advance by §10.3.

### How a verdict was assigned

- **answered** — the query ran, the artefact is complete in its CSV, and the
  observed value does not meet §10.2's stated problematic condition.
- **problematic** — artefact complete, value meets the stated condition.
- **unanswered** — the artefact could not be produced, or does not in fact answer
  the question. Per A-082 a near miss is unanswered with a reason, never answered.

Items 3, 7 and 11 state a problematic condition with **no number** ("non-trivial
share", "material web share", "repeat heavily"), and so does one of item 13's three
tests ("dominated by one placeholder"). This session reports the measured value
and adjudicates nothing, because a threshold fixed by the session reading the
numbers is the failure §10.3 opens by saying it exists to prevent. Raised as a
challenge in **A-095**.

---

## The three pre-session facts, re-established under protocol

Three facts reached this session from two manual console queries that were never
dry-run and were recorded in no file. §10.2 item 10's discipline was applied to all
three: treat them as inputs to verify, not as assumptions to build on.

| Claimed before this session | Established here | Agrees? |
|---|---|---|
| Shard range 20180612–20181003, 114 shards, no gaps | Identical, from table metadata at **0 bytes** | **yes** |
| 31 event names on shard 20180612; **no `in_app_purchase`**, no tutorial event | **37** names over the full range; **`in_app_purchase` exists** (27 events / 27 users); no tutorial event confirmed | **no — see below** |
| 25 `first_open` on shard 20180612 against 21,281 `screen_view` | 4,322 `first_open` over 114 shards, median 38/shard; 4,319 distinct users | consistent |

**The divergence is the finding.** The single-shard observation was not wrong about
its shard — it was extrapolated from one day to 114. A purchase event occurring 27
times across a 114-day window is absent from almost any single day one picks. Had
it been carried forward, this report would have stated that the sample contains no
purchase event at all, which is false, and would have reached the correct Part 2
scope decision for the wrong reason. This is precisely what §10.2 item 10 requires
the full range for. Recorded in **A-105**.

---

## Item 9 and the §10.3 scope rule, evaluated once

§10.3 fixes this rule before the query runs, and requires the observed counts and
both thresholds to be printed whichever side fires.

**Denominator, per §10.3 and A-084, named literally and not re-selected:** distinct
`user_pseudo_id` values with at least one event of any kind over the full shard
range, users with no `first_open` **included**, no trailing-window exclusion.

> **15,175 distinct users**

**Purchase event set:** `in_app_purchase`, the only purchase-shaped event in the
37-name vocabulary. `spend_virtual_currency` (9,363 events / 2,044 users) is
**excluded** per §10.2 item 9 — it is a soft-currency sink, and counting it is how
an unmonetized sample comes to look monetized.

| | Threshold | Observed | Result |
|---|---|---|---|
| Event volume | ≥ **1,000** revenue-positive purchase events | **27** | **MISSED** by 37× |
| User coverage | ≥ **0.5%** of 15,175 = **75.9** users | **27 users = 0.178%** | **MISSED** by 2.8× |

Both are required (A-081, unchanged by A-084). Either missed triggers the re-scope
branch.

> ### → §10.3 selects: **Part 2 is re-scoped to a progression funnel only.**
>
> It may not be titled, introduced or summarised as monetization anywhere,
> the README included, and must state that this sample does not support revenue
> analysis with the observed counts given.

**The outcome does not depend on which revenue carrier is chosen.** Three candidates
exist and the most generous still misses both bars: the `price` event parameter
gives 27, `event_value_in_usd` gives 24, and raw `in_app_purchase` event count
gives 27. A caveat that cuts the same way — `event_value_in_usd` does not exist as
a column on 15 of the 114 shards, so its figure is a lower bound; the `price`
parameter is present on all shards and is the larger number.

**One number deliberately not reached for.** `user_ltv.revenue` is strictly
positive for **146** users — 0.96% of the denominator, which would clear the
coverage threshold. It is not a purchase event: it is a running per-user lifetime
value carried on every row, accumulated over a history this window does not bound,
and 146 users carry it while only 27 purchased inside the range. Substituting it is
exactly the manipulation §10.3 names as invalidating the rule. It is recorded here
as declined rather than unnoticed (**A-104**).

---

## Item-by-item detail

Estimate and billed figures are per query file. Where one query answers several
items its cost appears against each; the ledger counts it once.

### Item 1 — Shard range · **problematic** · `sql/00_recon_shard_inventory.sql` · est 0 B / billed 0 B

Min suffix `20180612` (Tuesday), max `20181003` (Wednesday). **114** tables matching
`events_YYYYMMDD`, **zero** missing dates across the 114-day inclusive span, and no
`events_intraday_*` or other table. Total 5,700,000 rows, 4,151,085,667 logical
bytes. **Every shard holds exactly 50,000 rows.**

Taken from `__TABLES__` metadata; dry run and execution both billed **0 bytes**, as
§10.1 requires for this item.

Two conditions clear — no gaps, and 114 ≫ 30 shards. The third fires: **114 mod 7 =
2**, so the window is sixteen whole weeks plus two days and does not cover whole
weeks. Artefact: `recon_00_shard_inventory.csv`. Finding: **A-096**.

### Item 2 — `first_open` coverage · **problematic** · `sql/03_recon_event_vocabulary.sql` · est 273.60 MiB / billed 274.00 MiB

15,175 distinct users with any event; **4,319** with at least one `first_open`;
gap **10,856 users = 71.54%**, against a 5% threshold — more than fourteen times
over.

A plausible mechanism (these users installed before the window opens) is **not**
established by this pass and must not be assumed. Artefact:
`recon_03_event_vocabulary.csv`. Finding: **A-097**. See also item 6's companion
finding **A-109**, which records that the `first_open_time` *user property* is
populated for **all 15,175** users — a fact, not a proposal.

### Item 3 — Timestamp and timezone semantics · **answered** · `sql/06_recon_identity_time_duplicates.sql` · est 458.42 MiB / billed 459.00 MiB

`event_timestamp` is **microseconds**: its minimum, 1528786810908005, is
2018-06-12 07:00:10.908005 UTC and its maximum is 2018-10-04 07:01:23.482 UTC.

`event_date` equals its own shard suffix on **all 5,700,000 rows**. It differs from
the UTC date implied by the timestamp on **1,935,518 rows (33.96%)**, and the
difference is **strictly one-sided** — 1,935,518 rows exactly one day *behind* UTC,
**zero** ahead. `device.time_zone_offset_seconds` is non-null on every row with
**31** distinct values.

First-touch versus `first_open` gap: median **0 s**, p99 **81 s**, min −94 s, max
68,758,101 s (~795 days). **13 rows / 12 users exceed one day = 0.28%** of the 4,319
users with a `first_open`.

A property-local boundary and a device-local boundary are **both** available and are
**different**, so the choice between them is real. This session makes none.
Artefact: `recon_06_identity_time_duplicates.csv`. Finding: **A-098**.

### Item 4 — Identifier · **problematic** · `sql/06_recon_identity_time_duplicates.sql` · est 458.42 MiB / billed 459.00 MiB

`user_id` is **NULL on all 5,700,000 rows** — null rate exactly 1,000,000 ppm — so
distinct non-null `user_id` is **zero**. `user_pseudo_id` carries **15,175** values.
Query 01 confirmed `user_id` exists as a column on all 114 shards, so this is an
absent value throughout, not an absent column.

Item 4's problematic condition in its strongest form. "A player" means a
device-install; cross-device deduplication is impossible; the limitation must be
stated plainly in both parts. Finding: **A-099**.

### Item 5 — Cohort granularity · **problematic** · `sql/03_recon_event_vocabulary.sql` · est 273.60 MiB / billed 274.00 MiB

`first_open` per shard: median **38**, mean 39.7, min 1, max 71, across the **109**
of 114 shards that carry the event — five shards have none. Range total 4,322.

Against a threshold of a median below 100. Reported **per shard suffix**, the
export's own shard key, and explicitly not per any defined day (A-091); as it
happens `event_date` equals the shard suffix on every row, but that agreement is a
finding rather than a choice made here.

This interacts with item 1: the grain must coarsen because daily volume is thin,
yet the window is 16 weeks + 2 days, so a weekly grain does not divide it evenly
either. Finding: **A-100**.

### Item 6 — Session semantics · **problematic** · `sql/04_recon_event_parameters.sql` + `sql/09_recon_user_properties.sql` · est 1034.93 + 1003.45 MiB / billed 1035.00 + 1004.00 MiB

**No session identifier exists anywhere in this export.** `event_params` carries
**52** distinct keys and `user_properties` carries **25**; neither key space
contains `ga_session_id`, `ga_session_number`, or any other session id. Both lists
are complete — no key was filtered on a judgement about meaning (A-090).

A `session_start` event does exist — 74,353 events across 12,261 users — but carries
no id, so sessions can be counted as events and cannot be identified, grouped or
joined.

§10.2 fixes the consequence: a return must then be defined on **event presence**
rather than on sessions, which is a different definition and has to be stated as
one. This session states the fact and defines nothing. Artefacts:
`recon_04_event_parameters.csv`, `recon_09_user_properties.csv`. Findings:
**A-101**, completed by **A-109**.

### Item 7 — Platform mix · **answered** · `sql/07_recon_field_profiles.sql` · est 599.99 MiB / billed 600.00 MiB

`platform`: **ANDROID** 3,031,782 events / 7,410 users (53.19%), **IOS** 2,668,218 /
7,765 (46.81%), zero nulls. `device.category`: **mobile** 4,167,158 / 11,774
(73.11%), **tablet** 1,532,842 / 3,401 (26.89%), zero nulls.

**No web platform and no desktop category on any row.** The mobile-game framing
holds for all 5,700,000 rows, so no population filter is needed to establish it —
and Parts 1 and 2 should not carry one for appearance's sake, since it would remove
nothing. Item 13 confirms `platform` is not obfuscated. Finding: **A-102**.

### Item 8 — Duplicate events · **answered** · `sql/06_recon_identity_time_duplicates.sql` · est 458.42 MiB / billed 459.00 MiB

5,700,000 rows against 5,699,793 distinct values of
(`user_pseudo_id`, `event_name`, `event_timestamp`) — **207 duplicates = 36 ppm =
0.0036%**, against a 0.1% (1,000 ppm) threshold, roughly one twenty-eighth of it.

No downstream count needs a stated de-duplication step. The 207 rows are real and
disclosed; they are far too few to move any reported count. Finding: **A-103**.

### Item 9 — Revenue population · **problematic** · `sql/05_recon_revenue_population.sql` · est 853.91 MiB / billed 854.00 MiB

See the dedicated section above. Computed for **every** event name rather than a
candidate set (A-090), so the purchase set is a visible selection from a complete
committed table. Artefact: `recon_05_revenue_population.csv`. Finding: **A-104**.

### Item 10 — Event vocabulary · **answered** · `sql/03_recon_event_vocabulary.sql` · est 273.60 MiB / billed 274.00 MiB

**37** distinct event names over the full range. Largest: `screen_view` 2,247,623 /
14,077 users, `user_engagement` 1,358,958 / 13,588, `level_start_quickplay` 523,430
/ 10,166, `level_end_quickplay` 349,729 / 8,168, `post_score` 242,051 / 8,580.
Smallest include `in_app_purchase` 27 / 27 and `notification_foreground` 1 / 1.

Of the names §10.2 reports and requires verifying: `level_start_quickplay`,
`level_complete_quickplay` (191,088 / 5,676), `spend_virtual_currency` (9,363 /
2,044) and `in_app_purchase` are **all present**. There is **no tutorial event** —
no name over the full range contains "tutorial".

§10.2 fixes the consequence: the funnel sketched as first_open → tutorial → first
purchase has no referent for its middle step and is **abandoned rather than
approximated**. No replacement funnel is written here. §10.2 says this item cannot
fail and can only surprise; it surprised — see the divergence section above.
Finding: **A-105**.

### Item 11 — Funnel counting unit · **unanswered** · `sql/08_recon_event_repetition.sql` · est 273.60 MiB / billed 274.00 MiB

Events-per-user computed for **every** event name (A-090). Progression events repeat
heavily: `level_start_quickplay` median 5 per user, p90 54, max 24,641, with
**81.9%** of its users above one. `first_open` is near-unique (median 1, p90 1, max
2, 0.07% repeating) and `in_app_purchase` is exactly one per user. Repetition stays
heavy within a single shard too — `level_start_quickplay` median 3, p90 25, 76.4% of
user-shard pairs above one.

**Events per session, and within-session repetition, could not be computed at all**
— item 6 established that no session identifier exists. Two of the artefact's three
components are therefore unavailable, and per A-082 that is *unanswered* with a
reason, not *answered* on a near miss. The per-shard grain is reported as a bounded
fact about the export's own dating; it is **not** a session and **not** a day
boundary, and substituting it would be defining a session. Finding: **A-106**.

### Item 12 — Byte cost · **answered** · `sql/02_recon_shard_scan_cost.sql` + the full ledger · est 36.37 MiB / billed 37.00 MiB

See the budget section below. Finding: **A-107**.

### Item 13 — Obfuscation, placeholders and segmentability · **problematic** · `sql/07_recon_field_profiles.sql` · est 599.99 MiB / billed 600.00 MiB

| Field | Distinct | Null % | Top value | Share | Assessment |
|---|---|---|---|---|---|
| `geo.country` | 155 | 0.00% | United States | 61.54% | **passes all three tests** |
| `geo.region` | 50 | **88.57%** | — | — | **FAILS — null > 50%** |
| `platform` | 2 | 0.00% | ANDROID | 53.19% | passes |
| `device.category` | 2 | 0.00% | mobile | 73.11% | passes |
| `device.operating_system` | 2 | 5.92% | ANDROID | 51.28% | passes |
| `device.language` | 229 | 0.00% | en-us | 65.36% | passes |
| `app_info.version` | 34 | 0.00% | 2.62 | 48.32% | passes |
| `traffic_source.name` | 8 | 24.66% | (direct) | 75.25% | see below |
| `traffic_source.medium` | 8 | 0.07% | (none) | 75.25% | see below |
| `traffic_source.source` | 9 | 0.07% | (direct) | 75.25% | see below |

Query 01 established all ten paths exist on all 114 shards, so no null count here
is an absent column.

**`geo.region` is dropped, not reported** — §10.2 item 13 fixes that consequence in
advance. No Part 1 or Part 2 section may promise a region segmentation.

**Segment-by-country survives.** §10.2 names it specifically as contingent on this
item and this session's brief anticipated it might not survive. `geo.country` is the
best-populated segmentation dimension in the dataset: zero nulls, 155 distinct
values, no placeholder domination. Together with platform, device category, device
language and app version, segmentation is available on **five** dimensions rather
than none.

**The traffic-source fields are left undecided on purpose.** They pass every test
§10.2 quantifies and fail the one it does not: `traffic_source.name` is 75.25%
`(direct)` plus 24.66% null, so **99.91%** of rows sit in two buckets, one a
placeholder token; `medium` and `source` are 99.79% and 99.39% two-valued. Whether
that is "dominated by one placeholder" decides whether any traffic-source
segmentation is permitted, and fixing that threshold while holding the numbers is
what **A-095** challenges. Artefact: `recon_07_field_profiles.csv`. Finding:
**A-108**.

---

## Budget

Tracked in **actual bytes billed** read from job statistics after each query, never
in estimates (§10.1, A-085). Ledger: `outputs/tables/recon_budget_ledger.csv`.

| | |
|---|---|
| Query jobs | **13** — 11 under protocol, plus 2 pre-session console queries seeded from job history (A-094) |
| **Total billed** | **5,259,657,216 bytes = 4.90 GiB** |
| Against the 200 GiB total ceiling | **2.45% used**, 195.10 GiB remaining |
| Against the 50 GiB per-query ceiling | largest single query **1.01 GiB** — 2.0% of it |
| Against the 1 TiB monthly free tier | **0.48%** |
| Halt rule | never approached in either condition |

**The two prior console queries.** Their *actual* billed bytes were recovered from
`bq ls -j` rather than approximated: one billed **0** (a metadata query) and one
billed **10,485,760** — 10 MiB exactly, the per-query minimum, on 812,405 bytes
processed. Total prior consumption was **10 MiB**, not the ~20 MB carried in this
session's brief. Their estimate and divergence fields read `not_taken`, because no
dry run was ever performed on them and inventing one would put a fabricated number
in the column that records what authorised a query.

**`sql/06` appears twice in the ledger.** It was amended mid-pass to measure item 3's
over-one-day share exactly rather than leave it bounded between 0% and 1%, and
re-run. Both executions are recorded because both spent bytes.

### The cost model, built on actuals

Billed bytes follow an exact rule, which holds **without exception on all 13 ledger
rows**:

> **billed = max(10 MiB, ceil(processed → whole MiB))**

and on every protocol query the **dry-run estimate equalled bytes processed
exactly**. Observed ratios run from 1.0000 to 1.0174, the largest belonging to the
smallest real scan.

**Per-day unit cost.** A full-column scan of shard `events_20181003` billed
**38,797,312 bytes** against that shard's **38,133,989** bytes of table metadata, so
metadata `size_bytes` predicts billed bytes to within the MiB rounding. The
full-range, full-column cost therefore projects to **4,151,085,667 bytes ≈ 3.87
GiB** from free metadata alone — that is the ceiling on any conceivable single query
against this table.

**No materialised extract is required.** Item 12's problematic condition would need
Parts 1 and 2 plus a full re-run to exceed ~1,014 GiB of remaining monthly
allowance; this entire pass cost 4.90 GiB, and the most expensive possible query is
3.87 GiB. §7.5's zero-cost re-runnability holds comfortably.

### Two respects in which the actuals contradict §10.1's expectations

Both make Parts 1 and 2 **cheaper and more predictable** than the budget rule
assumed, and both are reported because §10.1 requires every divergence to be a
finding in both directions.

1. **The per-shard minimum does not multiply.** §10.1 and A-085 warn that BigQuery
   "bills a minimum per table referenced regardless of the estimate, which for a
   wildcard query touching many shards can dominate a cheap query's cost outright."
   It did not. A 114-shard wildcard scanning two columns billed **274 MiB**, not
   114 × 10 MiB = 1.14 GiB. The 10 MiB minimum applies **per query, not per shard
   referenced**.
2. **Estimates are precise, not merely indicative.** A-085 was written on the
   expectation that dry-run and billed figures would diverge unpredictably for
   `_TABLE_SUFFIX`-filtered wildcards. They did not diverge at all in the processed
   figure, and diverged from billed only by the documented rounding. An
   estimate-based projection for Parts 1 and 2 would have been very nearly right.

**On item 12's second problematic condition, reported rather than adjudicated.**
§10.2 names "a systematic divergence between estimated and billed bytes" as
problematic in its own right. A divergence *is* systematic here — billed exceeds
processed on every query that scans anything, always in the same direction. But it
is exactly characterised and bounded at sub-MiB plus a 10 MiB floor. This session
judges that a fully explained rounding rule is not the unpredictable planner
behaviour the clause exists to catch, and resolves the item **answered**. A reader
may disagree; the numbers are above and in the ledger.

---

## What this pass could not do, and what it declined to do

**Could not.** Item 11's per-session half, because no session identifier exists in
either key space. Recorded *unanswered* and escalated rather than approximated.

**Declined, because §8's content gate and §10.4 forbid it.** Choosing which events
are "progression events" for item 11 or "candidate purchase events" for item 9 —
both were computed over the whole 37-name vocabulary instead (A-090). Calling item
5's shard grouping a "calendar day" (A-091). Selecting a day boundary from item 3's
facts, when two defensible ones are available and differ. Reconciling item 2's
71.54% gap against the `first_open_time` user property that covers all 15,175 users
— the fact is recorded in **A-109**; what to do about it is a population definition.

**Declined, because it would fix a threshold while holding the numbers.**
Adjudicating "non-trivial share" (item 3), "material web share" (item 7), "repeat
heavily" (item 11) and "dominated by one placeholder" (item 13). Challenged in
**A-095**.

**Declined, because §10.3 names it as invalidating.** Substituting
`user_ltv.revenue`'s 146 users for `in_app_purchase`'s 27 to clear the coverage
threshold (**A-104**).

---

## Handover

Per §10.4 the next step is the architecture session's, not a build session's. The
three artifacts are complete: ten committed queries in `sql/00`–`sql/09`, eleven
result files with provenance sidecars in `outputs/tables/recon_*.csv`, and
`assumptions.md` entries **A-087 through A-111** — nine decisions, one challenge
(**A-095**), one finding per checklist item plus **A-109** completing item 6, and
**A-110** partially superseding A-088 in respect of the authentication sequence.
A-088's Status line is annotated accordingly, which A-047(i) permits and which is
the only edit made to any pre-existing entry.

Every one of the thirteen items carries a verdict. No Part 1 or Part 2 metric,
cohort, funnel step, day boundary or retention window has been written.
