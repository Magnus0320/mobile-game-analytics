"""Part 2's figures, generated from the committed tables.

§7.5 and A-043 fix what a figure may claim and how it is produced: every plotted
value is read back from a file under outputs/tables/, so the numbers behind a
figure reproduce byte-identically even where the pixels do not; the backend,
figure size, DPI and font family are fixed; and no timestamp, hostname or random
jitter enters a figure, so a re-run on the same machine with the same lock file
produces byte-identical PNGs.

§10.7.1 governs what may be drawn at all: this is a 50,000-events-per-day sample,
so no absolute count is plotted as traffic. Counts appear only as denominators in
labels; the plotted quantities are shares within the population, which is what
the sample supports.

A-154 requires a segmented figure to name what earliest-event attribution
measures, so the country figure says so in its subtitle.
"""

import matplotlib
matplotlib.use("Agg")                      # explicit, per §7.5
import matplotlib.pyplot as plt            # noqa: E402

from . import config as C                  # noqa: E402
from .tables import read_rows              # noqa: E402

FIGSIZE = (10.0, 6.0)
DPI = 140
PNG_METADATA = {"Software": "part2_funnel", "Date": None}   # no creation date
STEP_COLOUR = "#1f4e79"
RAW_COLOUR = "#9ab8d6"


def _setup():
    plt.rcParams.update({
        "font.family": "sans-serif",
        "font.sans-serif": ["DejaVu Sans", "Helvetica", "Arial", "sans-serif"],
        "axes.grid": True,
        "grid.alpha": 0.25,
        "axes.spines.top": False,
        "axes.spines.right": False,
        "figure.dpi": DPI,
    })


def _save(fig, name):
    path = C.FIGURES / name
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path, dpi=DPI, bbox_inches="tight", metadata=PNG_METADATA)
    plt.close(fig)
    return name


def funnel_figure():
    rows = {r["step"]: r for r in read_rows("part2_03_funnel.csv")}
    steps = list(C.STEPS)
    strict = [float(rows[s]["share_of_s0_pct_display"]) for s in steps]
    raw = [100.0 * int(rows[s]["users_raw"]) / C.POPULATION for s in steps]
    lo = [float(rows[s]["share_of_s0_lo_display"]) for s in steps]
    hi = [float(rows[s]["share_of_s0_hi_display"]) for s in steps]

    _setup()
    fig, ax = plt.subplots(figsize=FIGSIZE)
    positions = range(len(steps))
    ax.bar([p - 0.19 for p in positions], strict, width=0.38, color=STEP_COLOUR,
           label="strict cumulative — holds every earlier step")
    ax.bar([p + 0.19 for p in positions], raw, width=0.38, color=RAW_COLOUR,
           label="raw — holds this step, whatever came before")
    ax.errorbar([p - 0.19 for p in positions], strict,
                yerr=[[s - l for s, l in zip(strict, lo)], [h - s for s, h in zip(strict, hi)]],
                fmt="none", ecolor="#333333", capsize=4, linewidth=1.2)
    for position, step in zip(positions, steps):
        ax.text(position - 0.19, strict[position] + 2.2,
                f"{int(rows[step]['users_strict']):,}\n{strict[position]:.2f}%",
                ha="center", va="bottom", fontsize=8.5)

    ax.set_xticks(list(positions))
    ax.set_xticklabels([f"{s}\n{C.STEP_LABEL[s]}" for s in steps], fontsize=9)
    ax.set_ylabel("share of the 15,175-user population (%)")
    ax.set_ylim(0, 118)
    ax.set_yticks([0, 20, 40, 60, 80, 100])
    ax.set_title("Progression funnel — strict cumulative against raw per-step, per user",
                 fontsize=13, pad=30, loc="left")
    ax.text(0, 1.015,
            "Whole-window presence: a user either has the event somewhere in 20180612–20181003 or does not.\n"
            "Every shard holds exactly 50,000 rows, so no count here is a measure of real traffic.\n"
            "Bars carry 95% Wilson intervals on the strict share.",
            transform=ax.transAxes, fontsize=8.5, va="bottom", color="#444444")
    ax.legend(loc="upper right", fontsize=8.5, framealpha=0.9)
    return _save(fig, "part2_01_funnel.png")


def segment_figure(dimension="geo.country"):
    rows = [r for r in read_rows("part2_09_funnel_by_segment.csv")
            if r["dimension"] == dimension]
    if not rows:
        return None
    by_segment = {}
    for row in rows:
        by_segment.setdefault(row["segment"], {})[row["step"]] = row
    ordered = sorted(by_segment.items(),
                     key=lambda kv: (kv[0] == C.OTHER_LABEL, -int(kv[1]["S0"]["users_s0"])))

    _setup()
    fig, ax = plt.subplots(figsize=FIGSIZE)
    transitions = [("S1", "S0→S1"), ("S2", "S1→S2"), ("S3", "S2→S3")]
    width = 0.8 / len(ordered)
    palette = ["#1f4e79", "#2e8b57", "#b8860b", "#8b3a3a", "#5b4b8a",
               "#3d7ea6", "#7a7a7a", "#c26a3d", "#4f7942"]
    for index, (segment, steps) in enumerate(ordered):
        values, errs_lo, errs_hi = [], [], []
        for step, _ in transitions:
            cell = steps[step]
            if cell["step_conversion_status"] != C.STATUS_REPORTED:
                values.append(0.0); errs_lo.append(0.0); errs_hi.append(0.0)
                continue
            value = float(cell["step_conversion_pct_display"])
            values.append(value)
            errs_lo.append(value - float(cell["step_conversion_lo_display"]))
            errs_hi.append(float(cell["step_conversion_hi_display"]) - value)
        offsets = [i + (index - (len(ordered) - 1) / 2) * width
                   for i in range(len(transitions))]
        label = segment
        if segment == C.OTHER_LABEL:
            pooled = steps["S0"]["segments_pooled"]
            label = f"Other ({int(pooled)} segments)" if pooled else "Other"
        ax.bar(offsets, values, width=width * 0.92, color=palette[index % len(palette)],
               label=f"{label} (n = {int(steps['S0']['users_s0']):,})")
        ax.errorbar(offsets, values, yerr=[errs_lo, errs_hi], fmt="none",
                    ecolor="#333333", capsize=2, linewidth=0.8)

    ax.set_xticks(range(len(transitions)))
    ax.set_xticklabels([label for _, label in transitions], fontsize=10)
    ax.set_ylabel("step-to-step conversion on the strict population (%)")
    ax.set_ylim(0, 100)
    ax.set_title(f"Step-to-step conversion by {dimension}", fontsize=13, pad=34, loc="left")
    ax.text(0, 1.015,
            f"Segments are attributed from the user's earliest event row, so this is "
            f"{C.ATTRIBUTION_MEANING[dimension]}.\n"
            f"A segment is named individually only at {C.SEGMENT_FLOOR} users at S0; everything below "
            f"that floor is pooled into one Other row.\nBars carry 95% Wilson intervals.",
            transform=ax.transAxes, fontsize=8.5, va="bottom", color="#444444")
    fig.legend(loc="upper left", bbox_to_anchor=(1.0, 0.94), fontsize=8.5, framealpha=0.9)
    return _save(fig, "part2_02_step_conversion_by_country.png")


def build_all() -> list[str]:
    return [name for name in (funnel_figure(), segment_figure()) if name]
