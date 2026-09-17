"""Part 1's figures, generated from the committed tables.

§7.5 and A-043 fix what a figure may claim and how it is produced: every plotted
value is read back from a file under outputs/tables/, so the numbers behind a
figure reproduce byte-identically even where the pixels do not; the backend,
figure size, DPI and font family are fixed; and no timestamp, hostname or random
jitter enters a figure, so a re-run on the same machine with the same lock file
produces byte-identical PNGs.

§10.7.1 governs what may be drawn at all: this is a 50,000-events-per-day sample,
so no absolute count is plotted as traffic and no volume trend is drawn. Install
counts appear only as denominators in labels. Rates within a cohort are the only
quantities the sample supports, and they are what these figures show.

Ineligible cells are gaps, never zeros (§10.5.5).
"""

import csv

import matplotlib
matplotlib.use("Agg")                      # explicit, per §7.5
import matplotlib.pyplot as plt            # noqa: E402

from . import config as C                  # noqa: E402

FIGSIZE = (10.0, 6.0)
DPI = 140
PNG_METADATA = {"Software": "part1_retention", "Date": None}   # no creation date
SERIES_COLOUR = {1: "#1f4e79", 7: "#2e8b57", 30: "#b8860b"}
SERIES_MARKER = {1: "o", 7: "s", 30: "^"}


def _setup():
    plt.rcParams.update({
        "font.family": "sans-serif",
        "font.sans-serif": ["DejaVu Sans", "Helvetica", "Arial", "sans-serif"],
        "axes.grid": True,
        "grid.alpha": 0.25,
        "axes.spines.top": False,
        "axes.spines.right": False,
        "figure.autolayout": True,
    })


def _read(name):
    with open(C.TABLES / name, newline="") as fh:
        return list(csv.DictReader(fh))


def _save(fig, name):
    fig.savefig(C.FIGURES / name, dpi=DPI, format="png", metadata=PNG_METADATA)
    plt.close(fig)
    return name


def weekly_trend(table_name: str, out_name: str, title: str, subtitle: str) -> str:
    rows = _read(table_name)
    cohorts = sorted({r["cohort"] for r in rows})
    x = range(len(cohorts))
    fig, ax = plt.subplots(figsize=FIGSIZE)
    for horizon in C.HORIZONS:
        ys, los, his = [], [], []
        for cohort in cohorts:
            row = next(r for r in rows
                       if r["cohort"] == cohort and int(r["horizon_days"]) == horizon)
            if row["status"] == C.STATUS_REPORTED:
                ys.append(float(row["rate_pct_value"]))
                los.append(float(row["wilson_lo_pct_value"]))
                his.append(float(row["wilson_hi_pct_value"]))
            else:
                ys.append(float("nan")); los.append(float("nan")); his.append(float("nan"))
        ax.plot(x, ys, marker=SERIES_MARKER[horizon], markersize=4.5, linewidth=1.6,
                color=SERIES_COLOUR[horizon], label=f"D{horizon}")
        ax.fill_between(x, los, his, color=SERIES_COLOUR[horizon], alpha=0.13, linewidth=0)
    ax.set_xticks(list(x))
    ax.set_xticklabels(cohorts, rotation=45, ha="right", fontsize=8)
    ax.set_ylabel("retention (%)")
    ax.set_ylim(bottom=0)
    ax.set_title(title, fontsize=12, loc="left", pad=30)
    ax.text(0.0, 1.012, subtitle, transform=ax.transAxes, fontsize=8.5,
            color="#444444", va="bottom")
    ax.legend(frameon=False, fontsize=9, ncol=3, loc="upper right")
    return _save(fig, out_name)


def pooled_comparison(classic_rows, rolling_rows, out_name: str) -> str:
    fig, ax = plt.subplots(figsize=(8.0, 5.0))
    width = 0.34
    labels = [f"D{h}" for h in C.HORIZONS]
    for offset, (rows, label, colour) in enumerate(
            ((classic_rows, "classic (primary)", "#1f4e79"),
             (rolling_rows, "rolling (secondary)", "#2e8b57"))):
        xs, ys, errs = [], [], []
        for i, horizon in enumerate(C.HORIZONS):
            row = next(r for r in rows if int(r["horizon_days"]) == horizon)
            if row["status"] != C.STATUS_REPORTED:
                continue
            rate = float(row["rate_pct_value"])
            xs.append(i + (offset - 0.5) * width)
            ys.append(rate)
            errs.append([rate - float(row["wilson_lo_pct_value"]),
                         float(row["wilson_hi_pct_value"]) - rate])
        err = [[e[0] for e in errs], [e[1] for e in errs]]
        ax.bar(xs, ys, width=width, color=colour, label=label)
        ax.errorbar(xs, ys, yerr=err, fmt="none", ecolor="#222222", capsize=4, linewidth=1.1)
    ax.set_xticks(range(len(labels)))
    ax.set_xticklabels(labels)
    ax.set_ylabel("retention (%)")
    ax.set_title("Pooled retention, both definitions", fontsize=12, loc="left", pad=30)
    ax.text(0.0, 1.012,
            "95% Wilson intervals. Each horizon pools only the cohorts eligible at it "
            "(16 / 15 / 12 at D1 / D7 / D30).",
            transform=ax.transAxes, fontsize=8.5, color="#444444", va="bottom")
    ax.legend(frameon=False, fontsize=9)
    return _save(fig, out_name)


def by_segment(rows, out_name: str) -> str | None:
    dimensions = [d for d in C.PERMITTED_DIMENSIONS
                  if any(r["dimension"] == d for r in rows)]
    if not dimensions:
        return None
    fig, axes = plt.subplots(len(dimensions), 1,
                             figsize=(10.0, 2.6 * len(dimensions) + 1.2), squeeze=False)
    for ax, dimension in zip((a[0] for a in axes), dimensions):
        segs = []
        for r in rows:
            if r["dimension"] == dimension and r["segment"] not in segs:
                segs.append(r["segment"])
        x = range(len(segs))
        for horizon in C.HORIZONS:
            ys, errs, xs = [], [], []
            for i, seg in enumerate(segs):
                row = next((r for r in rows if r["dimension"] == dimension
                            and r["segment"] == seg and int(r["horizon_days"]) == horizon), None)
                if row is None or row["status"] != C.STATUS_REPORTED:
                    continue
                rate = float(row["rate_pct_value"])
                xs.append(i)
                ys.append(rate)
                errs.append((rate - float(row["wilson_lo_pct_value"]),
                             float(row["wilson_hi_pct_value"]) - rate))
            if not xs:
                continue
            ax.errorbar(xs, ys,
                        yerr=[[e[0] for e in errs], [e[1] for e in errs]],
                        fmt=SERIES_MARKER[horizon], markersize=5, capsize=3, linewidth=1.1,
                        color=SERIES_COLOUR[horizon], label=f"D{horizon}")
        ax.set_xticks(list(x))
        ax.set_xticklabels(segs, fontsize=8, rotation=20, ha="right")
        ax.set_ylabel("%")
        ax.set_ylim(bottom=0)
        ax.set_title(dimension, fontsize=10, loc="left")
    handles, labels = axes[0][0].get_legend_handles_labels()
    fig.legend(handles, labels, frameon=False, fontsize=9, ncol=3,
               loc="upper right", bbox_to_anchor=(0.995, 1.0))
    fig.suptitle("Pooled classic retention by segment, 95% Wilson intervals",
                 fontsize=12, x=0.01, ha="left", y=0.995)
    return _save(fig, out_name)


def build_all(classic_pooled, rolling_pooled, segment_rows) -> list[str]:
    _setup()
    C.FIGURES.mkdir(parents=True, exist_ok=True)
    written = [
        weekly_trend("part1_03_classic_retention_weekly.csv",
                     "part1_01_classic_retention_weekly.png",
                     "Classic retention by weekly install cohort",
                     "95% Wilson intervals. Gaps are cohorts the observation window cannot "
                     "measure at that horizon (§10.5.5) — never zeros."),
        weekly_trend("part1_05_rolling_retention_weekly.csv",
                     "part1_02_rolling_retention_weekly.png",
                     "Rolling retention by weekly install cohort (secondary definition)",
                     "Any event on or after install + N. NOT A TREND: the window left after day N "
                     "falls from 101 days (W01) to 3 (W15) at D7, so the decline is largely "
                     "right-censoring (A-150). Gaps are unmeasurable cohorts."),
        pooled_comparison(classic_pooled, rolling_pooled, "part1_03_pooled_retention.png"),
    ]
    segment_figure = by_segment(segment_rows, "part1_04_retention_by_segment.png")
    if segment_figure:
        written.append(segment_figure)
    return written
