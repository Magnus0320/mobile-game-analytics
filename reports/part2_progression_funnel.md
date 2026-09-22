# Part 2 — Progression funnel

How far players get through Cookie Cats' level content, measured per user across the
whole observation window of the GA4 public sample.

This part is specified in `ARCHITECTURE.md` §10.6, written from a dataset recon and
committed before any funnel query ran. The population, the counting unit, the four
steps, the strict-cumulative rule and both reporting triggers were fixed there. This
build implements them and reports what they produce. Where §10.6 admitted more than one
reading, the ambiguity is recorded as a challenge in `assumptions.md` for the
architecture session rather than settled here.

In order: who is in the analysis, what this part cannot be about, what the sample is,
the definitions, the results, and then a section on what none of it supports.

---

## 1. Who is in this analysis

Every user in the sample. Part 2's population is all 15,175<!--fig:pop_users--> distinct
`user_pseudo_id` values with at least one event in the window, and
0<!--fig:pop_excluded--> of them are excluded.

<!--table:population-->
|  | Count | Share |
|---|---:|---:|
| distinct users with at least one event in the window | 15,175 | 100.00% |
| users excluded from the funnel population | 0 | 0.00% |
| of those, users with a first_open event | 4,319 | 28.46% |
| of those, users with no first_open event | 10,856 | 71.54% |
| raw event rows before §10.7.4 de-duplication | 5,700,000 |  |
| event rows after §10.7.4 de-duplication | 5,699,793 |  |
| duplicate rows removed | 207 |  |
<!--/table-->

That is a deliberate contrast with Part 1, and §10.6.2 fixes it. Part 1 built install
cohorts on the `first_open` event and could therefore speak only about the
4,319<!--fig:pop_with_first_open--> users who have one, discarding the
10,856<!--fig:pop_without_first_open--> who do not —
71.54%<!--fig:pop_without_first_open_pct--> of the sample. A funnel step has to be
reachable by everyone in the denominator, and beginning at `first_open` would have done
one of two things: restricted Part 2 to the same slice for no new insight, or produced a
funnel that rises rather than falls, since more users started a level than have an
install event at all.

**A user means a device-install.** `user_id` is null on every row of this export, so
`user_pseudo_id` is the only identifier there is. One person on two devices is two users
here; a reinstall may be a new user. No cross-device claim and no unique-people claim is
available from this data, and the word "users" below never means "people".

**De-duplication, before any count.** §10.7.4 removes exact duplicate rows on
(`user_pseudo_id`, `event_name`, `event_timestamp`) before anything is counted. This
build removed 207<!--fig:dup_rows--> rows from 5,700,000<!--fig:rows_raw-->, leaving
5,699,793<!--fig:rows_deduped--> — 36<!--fig:dup_ppm--> parts per million, spread across
17<!--fig:dup_event_names--> of the 37<!--fig:event_names_total--> event names in the
window. This is the opposite of Part 3's rule, which keeps a suspicious row because
removing it after randomisation would break intention-to-treat. There is no
randomisation here, a duplicated log row is not an observation of anything, and per-user
distinct counts are exactly the quantity exact duplication distorts.

---

## 2. What this part is not: no revenue question is answerable

§10.3 fixed a rule before the recon ran. Part 2 would be a funnel *and monetization*
analysis if the sample carried at least 1,000 revenue-positive purchase events **and**
at least 0.5% of users with one, and a **progression funnel only** otherwise. The rule
selected the second branch, and this is the statement §10.6.1 requires.

**This sample does not support revenue analysis.**

<!--table:rescope-->
|  | Observed |
|---|---:|
| revenue-positive purchase events | 27 |
| distinct users with such an event | 27 |
| payer coverage of the 15,175-user denominator | 0.178% |
| §10.3 event threshold | 1,000 |
| §10.3 coverage threshold | 0.5% |
| events with a positive event_value_in_usd | 24 |
| shards with no event_value_in_usd column | 15 |
| spend_virtual_currency events | 9,363 |
| spend_virtual_currency users | 2,044 |
<!--/table-->

The observed counts are 27<!--fig:rescope_events--> revenue-positive purchase events
from 27<!--fig:rescope_users--> distinct users, which is
0.178%<!--fig:rescope_coverage_pct--> of the 15,175<!--fig:pop_users-->-user
denominator. That misses the event threshold by 37×<!--fig:rescope_event_factor--> and
the coverage threshold by 2.8×<!--fig:rescope_coverage_factor-->.

**27<!--fig:rescope_events--> is a lower bound, not a census.** `event_value_in_usd` does
not exist as a column on 15<!--fig:rescope_shards_without_usd--> of the
114<!--fig:shard_count--> shards, and only 24<!--fig:rescope_usd_events--> of the events
carry a positive value in it, while all of them carry a positive `price` parameter. The
larger carrier is the one counted. Nothing rests on the precision — the count could be
wrong by an order of magnitude and still miss the event threshold by a factor of three —
but a floor presented as a census is the kind of small overclaim a reader who knows this
dataset catches first.

These figures are quoted from the recon's committed result file and were **not**
recounted for this report. §10.3 evaluates its rule once, from that file, and
re-counting after seeing the verdict is precisely what the rule exists to prevent.

**`spend_virtual_currency` is not revenue.** It appears 9,363<!--fig:spend_events-->
times across 2,044<!--fig:spend_users--> users, and it is a soft-currency sink. It may
not be presented as monetization, spend, or purchase behaviour, and it is not.

---

## 3. What this sample is — and what it is not

Every one of the 114<!--fig:shard_count--> daily shards in this export holds exactly
50,000<!--fig:shard_rows--> rows. The minimum equals the maximum, on every single day.
That uniformity is not traffic; it is a sampling cap, and it governs how everything
below may be read.

- **Part 2 describes a 50,000<!--fig:shard_rows-->-events-per-day sample of this
  property, not the game's player base.**
- **No absolute count here measures real traffic** — not users at a step, not events per
  day, not the size of any segment.
- **No growth or trend claim may be made from volume.** Nothing in this report is a time
  series, and that is partly why.
- **The sampling fraction per day is unknown and may not be uniform**, so even
  comparisons of rates between groups could be affected if the sample was drawn
  differently on different days. That is unresolvable from the data, and it is in §9
  rather than hedged onto one table.

---

## 4. The definitions these numbers rest on

### 4.1 Population and counting unit

All 15,175<!--fig:pop_users--> users, counted **per user**. Per-event counting is
rejected outright: the recon measured heavy per-user repetition on the progression
events, so a per-event funnel would count one heavy player many times over and call it
conversion. Per-session counting is not available at all — no session identifier exists
anywhere in this export, in either the event-parameter or the user-property key space —
so there is nothing to count sessions with.

`first_open` is **not** a funnel step. The funnel begins at "present in the window".

### 4.2 The four steps

Fixed in §10.6.3 from the 37<!--fig:event_names_total--> event names the recon
established, and untouched by this build:

| Step | Definition |
|---|---|
| **S0** | Present in the window — at least one event of any kind |
| **S1** | Started a level — at least one `level_start_quickplay` |
| **S2** | Finished a level attempt — at least one `level_end_quickplay` |
| **S3** | Completed a level — at least one `level_complete_quickplay` |

The funnel sketched before the schema was known — install, then tutorial, then first
purchase — was **abandoned, not approximated**. There is no tutorial event of any kind
among the event names, `first_open` covers a minority of users, and
27<!--fig:diag_in_app_purchase_users--> purchase users cannot carry a funnel step.
Nothing was substituted for the missing middle step, because a substitution would
preserve a shape chosen before anyone had looked at the data.

### 4.3 Strict, and why both counts are printed

The funnel is **strict**: step *k*'s population is users who hold **all** of S0 through
S*k*, not users who hold S*k*. Monotonicity then holds by construction rather than by
luck. The **raw** per-step count is printed beside it in the same table, because the gap
between the two is the size of the out-of-order population, and that is information
about the export a reader should see rather than a discrepancy to smooth away.

### 4.4 Intervals, and the floor below which no rate is printed

Every rate carries its denominator and a 95% Wilson score interval. Wilson rather than
Wald, because segment denominators run from hundreds to thousands and Wald misbehaves at
small *n* and near the ends of the scale; and rather than a bootstrap, because a closed
form on a single proportion needs no seed and no resample count. Any cell whose
denominator falls below 30 is reported as a count only — no rate, no interval. On this
data that floor was checked on every cell and never bit.

---

## 5. The funnel

<!--table:funnel-->
| Step | What it means | Event | Strict | Raw | Share of S0 % [95% Wilson] | Step-to-step % [95% Wilson] |
|---|---|---|---:|---:|---:|---:|
| **S0** | Present in the window | `(any event)` | 15,175 | 15,175 | 100.00 [99.97, 100.00] | NULL |
| **S1** | Started a level | `level_start_quickplay` | 10,166 | 10,166 | 66.99 [66.24, 67.74] | 66.99 [66.24, 67.74] |
| **S2** | Finished a level attempt | `level_end_quickplay` | 8,145 | 8,168 | 53.67 [52.88, 54.47] | 80.12 [79.33, 80.88] |
| **S3** | Completed a level | `level_complete_quickplay` | 5,672 | 5,676 | 37.38 [36.61, 38.15] | 69.64 [68.63, 70.63] |
<!--/table-->

The same four steps are drawn in `outputs/figures/part2_01_funnel.png`, generated from
the table above: strict and raw shares side by side, with 95% Wilson intervals on the
strict share and the sampling cap named in the subtitle.

### 5.1 Where users are lost

S0 is the whole population by construction, so its share is
100.00%<!--fig:s0_share_of_s0--> of 15,175<!--fig:s0_strict--> and its step-to-step cell
is an explicit null rather than a meaningless figure.

Of those users, **10,166<!--fig:s1_strict--> started a level** —
66.99%<!--fig:s1_share_of_s0-->, 95% Wilson [66.24%<!--fig:s1_share_lo-->,
67.74%<!--fig:s1_share_hi-->]. That is the largest single loss in the funnel:
5,009<!--fig:drop_s0_s1_users--> users, 33.01 pp<!--fig:drop_s0_s1_pp-->, between being
present and starting a level. §9 has a good deal to say about what that number does and
does not mean.

Of those who started, **8,145<!--fig:s2_strict--> finished an attempt** —
80.12%<!--fig:s2_conversion--> of the previous step, [79.33%<!--fig:s2_conversion_lo-->,
80.88%<!--fig:s2_conversion_hi-->] — losing 2,021<!--fig:drop_s1_s2_users--> users, or
19.88 pp<!--fig:drop_s1_s2_pp-->. That is 53.67%<!--fig:s2_share_of_s0--> of the
population, [52.88%<!--fig:s2_share_lo-->, 54.47%<!--fig:s2_share_hi-->]. This is the tightest step in the funnel: a player who
starts a level nearly always reaches an end of it.

Of those, **5,672<!--fig:s3_strict--> completed a level** —
69.64%<!--fig:s3_conversion-->, [68.63%<!--fig:s3_conversion_lo-->,
70.63%<!--fig:s3_conversion_hi-->] — losing 2,473<!--fig:drop_s2_s3_users-->, or
30.36 pp<!--fig:drop_s2_s3_pp-->. End to end, 37.38%<!--fig:s3_share_of_s0--> of the
population completed a level, [36.61%<!--fig:s3_share_lo-->,
38.15%<!--fig:s3_share_hi-->], with 9,503<!--fig:drop_s0_s3_users--> users never getting
there.

Strict and raw agree exactly at S0 and at S1, because S0 is universal — both are
15,175<!--fig:s0_raw--> and 10,166<!--fig:s1_raw--> respectively. They diverge below:
the raw S2 count is 8,168<!--fig:s2_raw--> against a strict
8,145<!--fig:s2_strict-->, a gap of 23<!--fig:strict_raw_gap_s2-->, and the raw S3 count
is 5,676<!--fig:s3_raw--> against a strict 5,672<!--fig:s3_strict-->, a gap of
4<!--fig:strict_raw_gap_s3-->. Those gaps are the out-of-order population, and they are
the subject of the next section.

### 5.2 Out-of-order users — the trigger does not fire

§10.6.4 requires users who hold a later step without an earlier one to be counted and
reported, and makes a share above 1.0% of the step's raw population a finding with a
stated interpretation.

<!--table:out_of_order-->
| Step | Violation | Users | Raw population | Share of step | Share of all users | 1.0% trigger |
|---|---|---:|---:|---:|---:|---|
| S2 | has S2 but not S1 | 23 | 8,168 | 0.28% | 0.15% | not fired |
| S3 | has S3 but not S2 | 0 | 5,676 | 0.00% | 0.00% | not fired |
| S3 | has S3 but not S1 | 4 | 5,676 | 0.07% | 0.03% | not applied |
<!--/table-->

Neither named case comes close. 23<!--fig:ooo_s2_without_s1--> users hold S2 without S1 —
0.28%<!--fig:ooo_s2_without_s1_pct--> of the raw S2 population — and
0<!--fig:ooo_s3_without_s2--> users hold S3 without S2, which is
0.00%<!--fig:ooo_s3_without_s2_pct-->. The trigger does not fire and no interpretation is
owed. The counts are reported anyway, because a check that is only mentioned when it
fails is not a check.

One further figure is printed for legibility rather than because §10.6.4 names it:
4<!--fig:ooo_s3_without_s1--> users hold S3 without S1, which is
0.07%<!--fig:ooo_s3_without_s1_pct-->. They already sit inside the
23<!--fig:ooo_s2_without_s1--> above, since a user with S3 and S2 but no S1 is counted
there. The two named cases between them detect every out-of-order user in the sample.

### 5.3 The whole funnel, in one table

Every count above is a marginal of a single table. The funnel query returns a per-user
presence matrix over five events — the three step events, `level_fail_quickplay` for the
reconciliation in §6, and the non-quickplay `level_start` that §9 discusses — and
19<!--fig:matrix_patterns--> distinct patterns actually occur.

<!--table:matrix-->
| S1 start | S2 end | S3 complete | fail | non-quickplay start | Users | Share |
|:---:|:---:|:---:|:---:|:---:|---:|---:|
| yes | yes | yes | yes | no | 3,051 | 20.11% |
| no | no | no | no | no | 3,038 | 20.02% |
| no | no | no | no | yes | 1,947 | 12.83% |
| yes | yes | no | yes | no | 1,547 | 10.19% |
| yes | no | no | no | no | 1,322 | 8.71% |
| yes | yes | yes | no | no | 1,281 | 8.44% |
| yes | yes | yes | yes | yes | 1,001 | 6.60% |
| yes | yes | no | yes | yes | 726 | 4.78% |
| yes | no | no | no | yes | 699 | 4.61% |
| yes | yes | yes | no | yes | 339 | 2.23% |
| yes | yes | no | no | no | 146 | 0.96% |
| yes | yes | no | no | yes | 54 | 0.36% |
| no | yes | no | yes | no | 11 | 0.07% |
| no | yes | no | yes | yes | 6 | 0.04% |
| no | yes | yes | no | no | 3 | 0.02% |
| no | no | no | yes | no | 1 | 0.01% |
| no | yes | no | no | no | 1 | 0.01% |
| no | yes | no | no | yes | 1 | 0.01% |
| no | yes | yes | no | yes | 1 | 0.01% |
<!--/table-->

The rows sum to 15,175<!--fig:pop_users-->, and every strict count, raw count and
out-of-order count in this report can be re-added from them by hand. The same query also
computes those marginals directly in SQL, and the run asserts that the two derivations
agree — two independent routes to the same numbers inside one query.

---

## 6. Ends without outcomes

§10.6.5 requires one reconciliation, at both event and user level. It is the only place
in this report where the export does not add up.

### 6.1 The asymmetry, which is the finding

**202<!--fig:le_users_shortfall--> users have a `level_end_quickplay` and neither a
`level_complete_quickplay` nor a `level_fail_quickplay`. Exactly
1<!--fig:le_outcome_without_end--> user has an outcome with no end.**

The containment is near-perfect in one direction and not in the other. Essentially every
user who records an outcome also records the end that should precede it, which is what a
well-formed log would look like. The reverse does not hold. **That asymmetry is the
finding**, and it says more than the share it works out to: whatever is happening here
affects ends, not outcomes.

**The export does not record why an end carries no outcome.** A player may have abandoned
a level mid-attempt. There may be a third outcome type the event vocabulary does not
name. The outcome event may have been emitted and lost before it reached this sample.
Nothing in this data distinguishes those possibilities, and this report does not choose
between them.

**S2 is not redefined.** §10.6.5 forbids using this shortfall to redefine the step, and
S2 stands as `level_end_quickplay` presence. The step is presence-based — a user is in
it if they have the event at all — so nothing in §5 moves: the
8,168<!--fig:le_users_end--> raw and 8,145<!--fig:s2_strict--> strict figures are what
they were.

### 6.2 The same population, seen two ways

<!--table:level_end_event-->
|  | Count | Denominator | Share |
|---|---:|---:|---:|
| level_end_quickplay events | 349,715 |  |  |
| level_complete_quickplay events | 191,078 |  |  |
| level_fail_quickplay events | 137,032 |  |  |
| complete + fail | 328,110 |  |  |
| shortfall: ends carrying no outcome | 21,605 | 349,715 | 6.18% |
<!--/table-->

At event level, 349,715<!--fig:le_events_end--> ends against
328,110<!--fig:le_events_outcomes--> outcomes leaves
21,605<!--fig:le_events_shortfall--> ends carrying none, which is
6.18%<!--fig:le_events_shortfall_pct-->.

<!--table:level_end_user-->
|  | Count | Denominator | Share |
|---|---:|---:|---:|
| users with level_end_quickplay (S2) | 8,168 |  |  |
| users with level_complete_quickplay | 5,676 |  |  |
| users with level_fail_quickplay | 6,343 |  |  |
| users with either outcome (union) | 7,967 |  |  |
| users with BOTH outcomes | 4,052 |  |  |
| users with an outcome but no level_end_quickplay | 1 |  |  |
| shortfall: users with S2 and neither outcome — reading 1 (DIRECTED) | 202 | 8,168 | 2.47% |
| arithmetic parallel: (complete + fail - end) / end — reading 2 | 3,851 | 8,168 | 47.15% |
| shortfall over the outcome union — reading 3 | 202 | 7,967 | 2.54% |
<!--/table-->

At user level the same population is 202<!--fig:le_users_shortfall--> users —
2.47%<!--fig:le_reading1_pct--> of the 8,168<!--fig:le_users_end--> who have an end. The
6.18%<!--fig:le_events_shortfall_pct--> and the 2.47%<!--fig:le_reading1_pct--> are two
views of one unexplained population, not two findings. The user-level share is above
§10.6.5's 1.0% trigger, which is why the paragraphs above exist.

A note on the event figures. This report de-duplicates before counting (§10.7.4), so its
event counts sit marginally below the raw figures §10.6.5 quotes. The entire difference
is the duplicate rows removed from the three events, and
`outputs/tables/part2_07_level_end_reconciliation.csv` carries both bases so the
comparison can be made directly.

### 6.3 Which user-level figure this is, and why

§10.6.5 fixes the event-level arithmetic and requires the reconciliation "at both event
and user level", but that formula does not translate. At user level,
`users(complete) + users(fail)` double-counts anyone holding both, and this export has
exactly 4,052<!--fig:le_users_both--> such users, against
5,676<!--fig:le_users_complete--> with a complete and
6,343<!--fig:le_users_fail--> with a fail. Three readings are available:

**Reading 1, directed and used here** — users with S2 and neither outcome, over the
8,168<!--fig:le_users_end--> users with S2: 2.47%<!--fig:le_reading1_pct-->. It is the
user-level statement of what the event-level figure measures, ends that carry no
outcome, and it is the only one of the three that can be read as a shortfall at all.

**Reading 2, the arithmetic parallel** — `(complete + fail − end) / end`, the direct
translation of the event-level formula. It returns 47.15%<!--fig:le_reading2_pct-->, an
*excess* rather than a shortfall, and it is an excess entirely because those
4,052<!--fig:le_users_both--> users are counted twice. A shortfall trigger tested against
it could never fire for the reason it was written.

**Reading 3, over the outcome union** — reading 1's numerator over the
7,967<!--fig:le_users_union--> users with either outcome: 2.54%<!--fig:le_reading3_pct-->.
It has the right numerator and divides by a population the event-level figure never uses.

§10.6.5 does not say which of the three it means, and it does not say which its 1.0%
trigger applies to. This build did not settle that. The ambiguity is recorded as a
challenge in `assumptions.md` (A-164) for the architecture session, reading 1 was
directed by the project author, and the components of all three are printed in the table
above so a reader can rebuild any of them.

---

## 7. Diagnostic events — reported, never steps

Seven events are reported once here and are explicitly not funnel steps, because none of
them is a progression stage.

<!--table:diagnostics-->
| Event | Events | Users | Share of users | Why not a step |
|---|---:|---:|---:|---|
| `screen_view` | 2,247,537 | 14,077 | 92.76% | UI navigation, not progression |
| `user_engagement` | 1,358,913 | 13,588 | 89.54% | a heartbeat, not an action |
| `session_start` | 74,353 | 12,261 | 80.80% | app-open, and unreliable: median 2 per user against 5.7M events (§10.5.6) |
| `post_score` | 242,039 | 8,580 | 56.54% | score submission, parallel to progression |
| `level_fail_quickplay` | 137,032 | 6,343 | 41.80% | the failure branch of an attempt, not a stage beyond it |
| `spend_virtual_currency` | 9,362 | 2,044 | 13.47% | economy action, and explicitly not revenue (§10.6.1) |
| `in_app_purchase` | 27 | 27 | 0.18% | coverage 0.178%; see §10.6.1 |
<!--/table-->

Two are worth a sentence. `session_start` reaches
12,261<!--fig:diag_session_start_users--> users, which would make an attractive S1, and it
is not one: it carries no session identifier, and
74,353<!--fig:diag_session_start_events--> events across those users cannot describe the
session structure of a user with hundreds of events, so even the export's own marker is
unreliable as a boundary. And `in_app_purchase` reaches
27<!--fig:diag_in_app_purchase_users--> users, which is why §2 says what it says.

---

## 8. The funnel by segment

Segmentation is applied to the pooled population only. A user's segment is attributed
from their **earliest event row**, ties broken by lowest `event_timestamp` and then by
alphabetically lowest `event_name` — one deterministic rule, used in both parts.

### 8.1 Which dimensions survive, and what the attribution actually measures

§10.7.5 permits five dimensions and requires the share of users whose value is not
constant across their own events to be reported for **every** one of them, with a caveat
above 5.0% and a drop above 25.0%.

<!--table:constancy-->
| Dimension | Non-constant users | Share | Max values per user | Earliest-event value means | Outcome |
|---|---:|---:|---:|---|---|
| `app_info.version` | 1,330 | 8.76% | 3 | version at install | caveated |
| `geo.country` | 383 | 2.52% | 7 | country at first observed event | reported |
| `device.language` | 33 | 0.22% | 3 | language at first observed event | reported |
| `device.category` | 0 | 0.00% | 1 | device category at first observed event | reported |
| `platform` | 0 | 0.00% | 1 | platform at first observed event | reported |
<!--/table-->

`app_info.version` is **caveated**: 8.76%<!--fig:constancy_app_info_version--> of users,
1,330<!--fig:constancy_app_info_version_users--> of them, carry more than one version
across their own events. That is above the 5.0% trigger and below the 25.0% one, so the
dimension is reported with its share named and is not dropped.

**The comparison is the interesting part.** Part 1 measured the same share at
1.97%<!--fig:part1_app_version_constancy--> on its
4,319<!--fig:pop_with_first_open--> installers. On the full population it is
4.5×<!--fig:app_version_constancy_ratio--> that. A plausible mechanism, offered as an
explanation rather than a measurement: Part 1's population is observed from a fixed start
— each user's own install day — so their exposure to app releases is bounded by how long
they stayed. Part 2's population spans all 114<!--fig:shard_count--> days, and a user
present at both ends of the window has had every release in between to move through.
Nothing here measures that; it is the reading the two figures suggest.

`geo.country` sits at 2.52%<!--fig:constancy_geo_country--> —
383<!--fig:constancy_geo_country_users--> users — and is reported without a caveat.
`device.language` is 0.22%<!--fig:constancy_device_language-->, or
33<!--fig:constancy_device_language_users--> users. `platform` and `device.category` are
both 0.00%<!--fig:constancy_platform-->, at 0<!--fig:constancy_platform_users--> and
0<!--fig:constancy_device_category_users--> users: nobody in this sample changes either.

**What earliest-event attribution means** has to be said rather than assumed. Segmenting
by `app_info.version` means **version at install**, not "the user's version". Segmenting
by `device.language` means **language at first observed event**. Both are defensible
quantities; neither is quite the one the phrase suggests.

**Traffic source is not a segment.** `traffic_source.name`, `.medium` and `.source`
concentrate 99.91%<!--fig:traffic_name_pct-->, 99.78%<!--fig:traffic_medium_pct--> and
99.39%<!--fig:traffic_source_pct--> of events into two buckets, one of which is a
placeholder in each case. A dimension with one real bucket cannot distinguish groups, so
**no metric in this report is segmented by traffic source.** This is the single
descriptive line §10.7.5 requires to document that.

### 8.2 By country

A segment is named individually only at 200 users at S0. Everything below that floor is
pooled into one **Other** row carrying its own count and the number of segments it
holds, never dropped, because a dropped row silently changes the denominator. The floor
is applied once, on S0, so the columns describe the same partition and can be read
across.

<!--table:segment_geo_country-->
| Segment | S0 | S1 | S0→S1 % [95% Wilson] | S2 | S1→S2 % | S3 | S2→S3 % |
|---|---:|---:|---:|---:|---:|---:|---:|
| United States | 8,084 | 5,553 | 68.69 [67.67, 69.69] | 4,720 | 85.00 [84.04, 85.91] | 3,385 | 71.72 [70.41, 72.98] |
| India | 1,067 | 598 | 56.04 [53.05, 59.00] | 313 | 52.34 [48.34, 56.32] | 138 | 44.09 [38.69, 49.63] |
| Japan | 798 | 593 | 74.31 [71.17, 77.22] | 489 | 82.46 [79.20, 85.31] | 378 | 77.30 [73.38, 80.79] |
| Canada | 682 | 475 | 69.65 [66.10, 72.98] | 395 | 83.16 [79.53, 86.25] | 267 | 67.59 [62.83, 72.02] |
| United Kingdom | 564 | 391 | 69.33 [65.40, 72.99] | 348 | 89.00 [85.51, 91.73] | 258 | 74.14 [69.29, 78.46] |
| Australia | 562 | 428 | 76.16 [72.46, 79.49] | 354 | 82.71 [78.84, 86.00] | 236 | 66.67 [61.60, 71.38] |
| Germany | 291 | 198 | 68.04 [62.48, 73.13] | 166 | 83.84 [78.08, 88.31] | 145 | 87.35 [81.43, 91.57] |
| Mexico | 208 | 124 | 59.62 [52.83, 66.05] | 97 | 78.23 [70.17, 84.58] | 60 | 61.86 [51.91, 70.90] |
| Other (142 segments) | 2,919 | 1,806 | 61.87 [60.09, 63.62] | 1,263 | 69.93 [67.78, 72.00] | 805 | 63.74 [61.05, 66.34] |
<!--/table-->

`outputs/figures/part2_02_step_conversion_by_country.png` draws the three transitions
for each named country, generated from the table above, with 95% Wilson intervals and the
pooled Other row included. Its subtitle names what earliest-event attribution measures.

8<!--fig:seg_geo_country_named--> countries clear the floor, and
142<!--fig:seg_geo_country_pooled--> fall below it and are pooled into an Other row
holding 2,919<!--fig:seg_geo_country_other_users--> users.

### 8.3 By platform and device category

Both dimensions are perfectly constant within users, and both of their values clear the
floor, so neither has an Other row —
2<!--fig:seg_platform_named--> named segments each for `platform` and
2<!--fig:seg_device_category_named--> for `device.category`.

<!--table:segment_platform-->
| Segment | S0 | S1 | S0→S1 % [95% Wilson] | S2 | S1→S2 % | S3 | S2→S3 % |
|---|---:|---:|---:|---:|---:|---:|---:|
| IOS | 7,765 | 6,113 | 78.73 [77.80, 79.62] | 5,120 | 83.76 [82.81, 84.66] | 3,511 | 68.57 [67.29, 69.83] |
| ANDROID | 7,410 | 4,053 | 54.70 [53.56, 55.83] | 3,025 | 74.64 [73.27, 75.95] | 2,161 | 71.44 [69.80, 73.02] |
<!--/table-->

<!--table:segment_device_category-->
| Segment | S0 | S1 | S0→S1 % [95% Wilson] | S2 | S1→S2 % | S3 | S2→S3 % |
|---|---:|---:|---:|---:|---:|---:|---:|
| mobile | 11,774 | 7,404 | 62.88 [62.01, 63.75] | 5,875 | 79.35 [78.41, 80.26] | 4,029 | 68.58 [67.38, 69.75] |
| tablet | 3,401 | 2,762 | 81.21 [79.86, 82.49] | 2,270 | 82.19 [80.72, 83.57] | 1,643 | 72.38 [70.50, 74.18] |
<!--/table-->

### 8.4 By language and app version

<!--table:segment_device_language-->
| Segment | S0 | S1 | S0→S1 % [95% Wilson] | S2 | S1→S2 % | S3 | S2→S3 % |
|---|---:|---:|---:|---:|---:|---:|---:|
| en-us | 8,936 | 6,000 | 67.14 [66.16, 68.11] | 4,965 | 82.75 [81.77, 83.68] | 3,523 | 70.96 [69.68, 72.20] |
| en-gb | 1,353 | 834 | 61.64 [59.02, 64.20] | 601 | 72.06 [68.92, 75.00] | 396 | 65.89 [62.01, 69.57] |
| ja-jp | 743 | 553 | 74.43 [71.17, 77.43] | 462 | 83.54 [80.22, 86.40] | 359 | 77.71 [73.69, 81.26] |
| en-ca | 561 | 387 | 68.98 [65.04, 72.67] | 323 | 83.46 [79.44, 86.83] | 215 | 66.56 [61.25, 71.49] |
| en-au | 536 | 406 | 75.75 [71.94, 79.18] | 327 | 80.54 [76.41, 84.10] | 213 | 65.14 [59.82, 70.10] |
| de-de | 283 | 197 | 69.61 [64.02, 74.68] | 166 | 84.26 [78.53, 88.69] | 149 | 89.76 [84.21, 93.51] |
| en-in | 264 | 154 | 58.33 [52.31, 64.12] | 93 | 60.39 [52.50, 67.77] | 46 | 49.46 [39.53, 59.44] |
| en | 255 | 203 | 79.61 [74.24, 84.10] | 167 | 82.27 [76.43, 86.91] | 107 | 64.07 [56.55, 70.96] |
| Other (220 segments) | 2,244 | 1,432 | 63.81 [61.80, 65.78] | 1,041 | 72.70 [70.33, 74.94] | 664 | 63.78 [60.82, 66.65] |
<!--/table-->

8<!--fig:seg_device_language_named--> languages clear the floor and
220<!--fig:seg_device_language_pooled--> are pooled, into an Other row of
2,244<!--fig:seg_device_language_other_users--> users.

The table below carries §10.7.5's caveat, for the share given in §8.1, and the reminder
that under earliest-event attribution this is **version at install** rather than the
version a user ended on. 5<!--fig:seg_app_info_version_named--> versions clear the floor
and 29<!--fig:seg_app_info_version_pooled--> are pooled, into an Other row of
1,235<!--fig:seg_app_info_version_other_users--> users.

<!--table:segment_app_info_version-->
| Segment | S0 | S1 | S0→S1 % [95% Wilson] | S2 | S1→S2 % | S3 | S2→S3 % |
|---|---:|---:|---:|---:|---:|---:|---:|
| 2.62 | 6,531 | 3,798 | 58.15 [56.95, 59.34] | 2,834 | 74.62 [73.21, 75.98] | 2,012 | 71.00 [69.30, 72.64] |
| 2.6.30 | 3,515 | 2,609 | 74.22 [72.75, 75.64] | 2,286 | 87.62 [86.30, 88.83] | 1,481 | 64.79 [62.80, 66.72] |
| 2.6.31 | 2,680 | 2,248 | 83.88 [82.44, 85.22] | 1,784 | 79.36 [77.64, 80.98] | 1,263 | 70.80 [68.64, 72.86] |
| 2.6.27 | 802 | 632 | 78.80 [75.84, 81.49] | 546 | 86.39 [83.50, 88.85] | 403 | 73.81 [69.96, 77.32] |
| 2.59 | 412 | 80 | 19.42 [15.89, 23.51] | 64 | 80.00 [69.95, 87.30] | 54 | 84.38 [73.57, 91.29] |
| Other (29 segments) | 1,235 | 799 | 64.70 [61.99, 67.31] | 631 | 78.97 [76.01, 81.66] | 459 | 72.74 [69.14, 76.07] |
<!--/table-->

---

## 9. What this does not support

### 9.1 Not answerable from this data at all

- **Revenue, and everything that depends on it.** §2 gives the counts. A progression
  funnel cannot say whether reaching level content converts to spending, because this
  sample carries 27<!--fig:rescope_events--> purchase events from
  27<!--fig:rescope_users--> users. There is no ARPPU here, no revenue per install, no
  conversion-to-payer by segment, and no version of this report that could produce one.

- **Anything about sessions.** No session identifier exists in either key space, so
  sessions per user, session length and within-session repetition are all unavailable.
  The recon recorded that half of its own checklist item as permanently unanswered for
  this dataset, and Part 2 inherits it. `session_start` is an event, not a session.

- **Anything about people.** `user_id` is null on every row, so every count in this
  report is a count of device-installs. One person on several devices appears several
  times; a reinstall may appear as a new user. No deduplication of people is possible.

- **Real traffic, at any grain.** Every shard holds exactly
  50,000<!--fig:shard_rows--> rows, so no count in this report measures how many people
  played this game. **Counts are ruled out outright, and shares are not thereby
  established:** whether a share computed on this extract transfers to the property's
  real population depends on the sampling method, and the export does not document one.

  *Corrected 2026-09-22 (A-183).* This bullet previously ended "The funnel's *shares* are
  what the sample supports". That asserts a transfer nothing here establishes, and it is
  the largest unearned claim this part had available: the funnel's shares are the entirety
  of what Part 2 reports, so a sentence saying they are supported says the whole of this
  part's output carries to the real population. The wording was inherited from §10.7.1,
  which until v1.8 ended a bullet with "rates within a cohort are the only quantities the
  sample supports" and now says counts are ruled out and rates unestablished. The
  specification's error did not make this report's sentence true.

- **Why an end carries no outcome.** §6 gives the size of the population and says plainly
  that the export does not record the reason.

- **Progression in the mode this funnel does not cover — though its size is now known.**
  §10.6.3's steps are the `_quickplay` events, and this export carries a second, parallel
  progression family that the funnel does not measure. Of the
  5,009<!--fig:track_without_s1--> users the funnel counts as never starting a level,
  1,955<!--fig:track_without_s1_with_np--> started a non-quickplay one:
  39.03%<!--fig:track_share_of_outside_s1--> of them. Counting both modes,
  12,121<!--fig:track_either_mode--> users — 79.87%<!--fig:track_either_mode_pct--> of
  the population — started a level somewhere, and only
  3,054<!--fig:track_neither--> started neither.

  <!--table:parallel_track-->
|  | Users | Share of 15,175 |
|---|---:|---:|
| users with no level_start_quickplay (outside S1) | 5,009 | 33.01% |
| of those, users who started a NON-quickplay level | 1,955 | 12.88% |
| users who started a level in EITHER mode | 12,121 | 79.87% |
| users who started a level in NEITHER mode | 3,054 | 20.13% |
| users with a non-quickplay level_start, all | 4,774 | 31.46% |
| users active in BOTH modes | 2,819 | 18.58% |
| users with the plays_progressive user property | 4,585 |  |
| users with the plays_quickplay user property | 3,548 |  |
<!--/table-->

  **The `plays_*` user properties do not measure mode participation, and no comparative
  between the modes rests on them here.** `plays_progressive` covers
  4,585<!--fig:track_plays_progressive--> users against `plays_quickplay`'s
  3,548<!--fig:track_plays_quickplay-->, but 10,166<!--fig:s1_strict--> users have an
  observed `level_start_quickplay` against 4,774<!--fig:track_np_users--> with a
  non-quickplay level start. **By observed play, quickplay is the larger mode**, and the
  property undercounts observed quickplay participation by
  2.9×<!--fig:quickplay_property_undercount_ratio-->. Its semantics are undocumented.

  *Corrected 2026-09-22 (A-182).* This passage previously read "the mode this funnel does
  not cover is **the larger** of the two", drawn from the two property counts alone. Both
  counts are correct and the inference was not: a user property is not a participation
  measure unless something establishes that it is, and checking it against observed level
  starts — the check that should have been run when the comparative was first written —
  reverses the direction. The same inference was published in the note on the
  `plays_quickplay` row of `outputs/tables/part2_10_parallel_track.csv`, and in different
  words on the `plays_progressive` row; both notes are corrected at their source in the
  renderer and regenerated, never edited in the file.

  **What this bullet is for does not depend on which mode is larger.** S1's
  66.99%<!--fig:s1_share_of_s0--> is a floor on "started playing" rather than a measure of
  it, because 1,955<!--fig:track_without_s1_with_np--> users outside S1 started a level in
  a mode this funnel does not count; and the 33.01 pp<!--fig:drop_s0_s1_pp--> loss at the
  first step is therefore not 33.01 pp<!--fig:drop_s0_s1_pp--> of players who never
  engaged with the game.

  §10.6.3 fixes the four steps and this build does not change them.
  4,774<!--fig:track_np_users--> users have a non-quickplay level start in total, of whom
  2,819<!--fig:track_both_modes--> are active in both modes and are already counted inside
  S1. The non-quickplay event rides along in the progression matrix as a labelled
  diagnostic flag and is never a step. It cost no additional bytes, because the query that
  counts the steps already reads the event name.

### 9.2 Answered only under stated assumptions

- **The user-level reconciliation figure** rests on reading 1 of three, directed by the
  project author and recorded as a challenge (A-164) rather than as a decision of this
  build. Under reading 2 the same data returns 47.15%<!--fig:le_reading2_pct--> and means
  something else.

- **Every segment figure** rests on earliest-event attribution (§10.7.5), so it describes
  a user's value at their first observed event rather than across their life. For
  `app_info.version` that assumption is measurably imperfect for
  8.76%<!--fig:constancy_app_info_version--> of users.

- **Every count** rests on de-duplication removing exactly the rows it should
  (§10.7.4). The run asserts that distinct-user counts are unchanged by it — they must
  be, since a duplicate row carries the same user and event name as its twin — and that
  the per-event differences sum to the 207<!--fig:dup_rows--> rows reported.

- **The explanation offered in §8.1** for why app-version instability is
  4.5×<!--fig:app_version_constancy_ratio--> Part 1's is a plausible mechanism, not a
  measured one. Nothing in this build tests it.

### 9.3 Confounds and unverifiable properties that remain

- **The sampling mechanism is unknown, and the direction of its effect on this funnel
  depends on which mechanism it is.** A stated bias must name its direction or say why it
  cannot, so: if the cap thins *events* within a user, a user with few events can lose the
  single `level_complete_quickplay` that would have placed them at S3, every step is
  understated, and the later and rarer steps are understated more than the earlier ones —
  the funnel would look steeper than it is. If instead the cap samples *users* and keeps
  all of their events, the funnel is unbiased for the users it kept. That every shard
  holds exactly 50,000<!--fig:shard_rows--> rows, minimum equal to maximum on every day,
  is evidence for an event-level cap, because a user-level sample would not land on a
  round number daily. It does not say *which* event-level rule, and random thinning and a
  truncation at a daily limit do not have the same effect. **So the direction is
  determinable only conditional on a mechanism this data does not record**, and that is
  the honest statement rather than a direction asserted without one.

  One measurable thing bears on it, weakly. §10.6.4's own reading of out-of-order users is
  that they usually mean an event was dropped by sampling, and this sample has very few:
  23<!--fig:ooo_s2_without_s1--> and 0<!--fig:ooo_s3_without_s2-->. That is consistent
  with thinning being light. It is not proof, because a user whose events were thinned
  away entirely leaves no trace to count.

- **The constancy test found what generalising it was meant to find.** Under
  `ARCHITECTURE.md` v1.5 the non-constancy test was attached to `geo.country` alone, and
  v1.6 extended it to every permitted dimension after Part 1 raised that the dimension
  most likely to vary had no test at all. On this population `geo.country` sits at
  2.52%<!--fig:constancy_geo_country--> and passes, while `app_info.version` at
  8.76%<!--fig:constancy_app_info_version--> trips the caveat trigger. **Under the
  earlier rule there would have been no trigger on the dimension that tripped**, and the
  caveat in §8.1 would not exist.

- **No cross-device identity**, so a single person's progression can be split across
  several rows of every table in this report, and the funnel's denominators count devices.

- **Unknown calendar context.** The window is a fixed 114<!--fig:shard_count--> days of
  one property. A live-ops event, a store feature, a difficulty retune or a release that
  changed the early levels would all be invisible here and could move every step.

- **Unknown level difficulty behind the events.** S1 to S3 measure that a level was
  started, ended and completed; nothing records *which* level, so a user completing the
  first level and a user completing the fiftieth are the same row.

### 9.4 What would be required to answer the question properly

- **Level-progression telemetry**: the level number on every start, end and complete
  event, and the highest level reached per user. That converts this funnel from "did they
  complete a level" into a distribution of where players actually stall, which is the
  question a design team would ask.

- **An outcome on every `level_end_quickplay`**, or an explicit abandonment event. That
  would resolve the 202<!--fig:le_users_shortfall--> users in §6 into a cause rather than
  a count.

- **A mode field on the progression events**, or a single event family covering both
  modes. That would remove the boundary §9.1 describes and let one funnel cover the
  12,121<!--fig:track_either_mode--> users who started a level in either mode.

- **A session identifier**, which would make sessions per user, session length and
  within-session repetition computable and would let the funnel be expressed per session
  as well as per user.

- **A stable cross-device user identifier**, which would turn every count in this report
  from device-installs into people.

- **The sampling manifest** — the rule that produced exactly
  50,000<!--fig:shard_rows--> rows per day, and the fraction it represents. That alone
  would settle the direction question in §9.3 and turn every share in this report from a
  sample statistic into an estimate with a known relationship to the population.

- **Revenue events at usable volume**, without which no version of this analysis can
  speak to the question a progression gate exists to serve.

---

## 10. Reproducing this

Part 2 needs the Google Cloud SDK and a BigQuery-enabled project. Queries run against a
public dataset and are billed to your own project under the sandbox's free monthly tier.
The project id lives in an environment variable and appears in no committed file.

```bash
export GOOGLE_CLOUD_PROJECT=your-project-id
./run_part2.sh
```

The wrapper dry-runs every query before executing it, refuses to run one whose estimate
breaches a ceiling, reads the actual bytes billed from job statistics afterwards, and
appends a row to a committed ledger for every execution, re-runs included.

<!--table:ledger-->
| Query | Dry-run estimate | Billed | Predicted | Delta |
|---|---:|---:|---:|---:|
| `30_part2_population_and_vocabulary.sql` | 332,489,198 | 333,447,168 | 333,447,168 | 0 |
| `31_part2_progression_matrix_and_funnel.sql` | 332,489,198 | 333,447,168 | 333,447,168 | 0 |
| `32_part2_segment_constancy.sql` | 571,173,619 | 571,473,920 | 571,473,920 | 0 |
| `33_part2_funnel_by_segment.sql` | 571,173,619 | 571,473,920 | 571,473,920 | 0 |
<!--/table-->

The whole part cost 1.69 GiB<!--fig:ledger_total_gib--> across
4<!--fig:ledger_queries--> queries with no re-runs —
8.43%<!--fig:ledger_share_of_session--> of the 20 GiB §10.1 allows a build session, with
the largest single query at 0.53 GiB<!--fig:ledger_largest_gib--> against a 4 GiB
per-query ceiling. Both build sessions together have now spent
5.97 GiB<!--fig:ledger_pair_gib--> of 40 GiB, and Part 1's figure is read from its
committed ledger rather than assumed. Every query's billed bytes matched the prediction
`max(10 MiB, ceil(estimate → MiB))` exactly: the largest miss across the part was
0<!--fig:ledger_max_delta--> bytes, against a 1 MiB halt band that would have stopped the
session.

### What makes the figures in this report checkable

Every number above is either a cell of a committed table or a row of
`outputs/tables/part2_report_figures.csv`, and the run refuses to finish unless each one
matches the cell it declares. There are three mechanisms, and the third is the one that
matters.

**Tables are generated, not written.** Every table in this report is produced from its
committed CSV and embedded between markers. The audit regenerates each block and asserts
it is byte-identical to what is in the file, so no cell in a report table is ever typed
by hand.

**Prose figures name their cell.** Each figure in the prose carries an invisible tag
naming its row of the register, and the audit checks *that cell* — not whether the number
appears somewhere in the outputs. A figure computed across tables is emitted as its own
row of the register first, so there is no second class of figure for an audit to miss.
Everything else in the prose must match an enumerated exemption list — dates, section
numbers, `assumptions.md` references, step labels, and the thresholds quoted from
`ARCHITECTURE.md` — and the scanner reads spelled-out quantities as well as digits.

**The audit is tested against its own failure.** Part 1's audit verified that every prose
figure appeared verbatim *somewhere* in a committed table, and a hand-written count
passed it while being wrong, because the digits occurred elsewhere as an unrelated
figure. That exact case is replanted as a fixture here, along with an untagged number, a
spelled-out quantity and a tag naming no register row, and the run fails unless the audit
rejects all of them — and accepts a correct fixture, because an audit that rejected
everything would satisfy the rejections on its own.

`assumptions.md` A-160 through A-174 record every judgement this build made, committed
before the first query ran. A-164 is a challenge rather than a decision: §10.6.5's
user-level reconciliation admits three readings and the document adjudicates none of
them.
