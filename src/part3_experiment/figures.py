"""§7.7 step 19 (figures). Every figure is generated FROM a committed table.

§7.5 states the reproducibility guarantee at two strengths, and this module
implements the weaker one honestly: tables and JSON are byte-identical anywhere,
figures are byte-identical only on the same machine with the same lock file.
Matplotlib does not produce byte-identical PNGs across versions, platforms or
font configurations, so a cross-machine pixel claim would be falsified by the
first re-run elsewhere (A-043).

What holds regardless: every plotted value is read back out of a file in
outputs/tables/, so no figure is ever the sole record of a value.
"""

from __future__ import annotations

import csv
from pathlib import Path

import matplotlib

from . import config

# Idempotent: step 1 already set this via manifest.resolve_environment(). Kept so
# that importing this module in isolation cannot pick up an interactive backend.
matplotlib.use(config.FIG_BACKEND)

import matplotlib.pyplot as plt  # noqa: E402

PNG_METADATA = {"Software": None}  # suppress matplotlib's version/date tag


def _apply_style() -> None:
    plt.rcParams.update({
        "figure.figsize": config.FIG_SIZE,
        "figure.dpi": config.FIG_DPI,
        "savefig.dpi": config.FIG_DPI,
        "font.family": config.FIG_FONT_FAMILY,
        "font.sans-serif": config.FIG_FONT_FALLBACK,
        "axes.grid": True,
        "grid.alpha": 0.3,
        "axes.spines.top": False,
        "axes.spines.right": False,
        "svg.hashsalt": "part3",
    })


def _read(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as fh:
        return list(csv.DictReader(fh))


def _kv(path: Path) -> dict[str, str]:
    return {r["quantity"]: r["value"] for r in _read(path)}


def _save(fig, name: str) -> Path:
    config.FIGURES_DIR.mkdir(parents=True, exist_ok=True)
    out = config.FIGURES_DIR / name
    fig.savefig(out, format="png", metadata=PNG_METADATA, bbox_inches="tight")
    plt.close(fig)
    return out


def write_all() -> list[Path]:
    _apply_style()
    tables = config.TABLES_DIR
    written: list[Path] = []

    # 01 — retention rates by arm (from part3_05) ---------------------------
    rates = _read(tables / "part3_05_retention_rates.csv")
    fig, axes = plt.subplots(1, 2, figsize=(9.0, 4.5))
    for ax, metric, title in (
        (axes[0], "retention_7", "7-day retention (primary)"),
        (axes[1], "retention_1", "1-day retention (guardrail)"),
    ):
        sel = [r for r in rates if r["metric"] == metric]
        labels = [r["arm"] for r in sel]
        values = [float(r["rate_pp"]) for r in sel]
        bars = ax.bar(labels, values, color=["#4C72B0", "#DD8452"], width=0.55)
        for bar, value in zip(bars, values):
            ax.annotate(f"{value:.2f}%", (bar.get_x() + bar.get_width() / 2, value),
                        ha="center", va="bottom", fontsize=9)
        ax.set_title(title, fontsize=11)
        ax.set_ylabel("retained (%)")
        ax.set_ylim(0, max(values) * 1.25)
    fig.suptitle("Retention by arm — intention-to-treat over all assigned players",
                 fontsize=12)
    written.append(_save(fig, "part3_01_retention_rates.png"))

    # 02 — effects against the action threshold (from part3_06 / part3_07) ---
    primary = _kv(tables / "part3_06_primary_inference.csv")
    guard = _kv(tables / "part3_07_guardrail_inference.csv")
    fig, ax = plt.subplots(figsize=(9.0, 4.2))
    rows = [
        ("D7 (primary)\nbootstrap", float(primary["delta_7_pp"]),
         float(primary["bootstrap_ci_low_pp"]), float(primary["bootstrap_ci_high_pp"]),
         "#4C72B0"),
        ("D7 (primary)\nanalytic", float(primary["delta_7_pp"]),
         float(primary["analytic_ci_low_pp"]), float(primary["analytic_ci_high_pp"]),
         "#7FA3D1"),
        ("D1 (guardrail)\nbootstrap", float(guard["delta_1_pp"]),
         float(guard["bootstrap_ci_low_pp"]), float(guard["bootstrap_ci_high_pp"]),
         "#DD8452"),
    ]
    mde = config.MDE_PP
    ax.axvspan(-mde, mde, color="#999999", alpha=0.15,
               label=f"within the {mde:.2f} pp action threshold")
    ax.axvline(0.0, color="#333333", lw=1.0)
    for i, (label, point, lo, hi, colour) in enumerate(rows):
        y = len(rows) - 1 - i
        ax.plot([lo, hi], [y, y], color=colour, lw=3, solid_capstyle="round")
        ax.plot([point], [y], "o", color=colour, markersize=8, zorder=3)
    ax.set_yticks(range(len(rows)))
    ax.set_yticklabels([r[0] for r in reversed(rows)], fontsize=9)
    ax.set_xlabel("effect on retention, variant minus control (percentage points)")
    ax.set_title("Estimated effects with 95% intervals, against the action threshold",
                 fontsize=12)
    ax.legend(loc="lower right", fontsize=9, framealpha=0.9)
    written.append(_save(fig, "part3_02_effect_intervals.png"))

    # 03 — power curve (from part3_04) ---------------------------------------
    curve = _read(tables / "part3_04_power_curve.csv")
    power_kv = _kv(tables / "part3_03_power.csv")
    fig, ax = plt.subplots()
    ax.plot([float(r["effect_pp"]) for r in curve],
            [float(r["power"]) for r in curve], color="#4C72B0", lw=2)
    ax.axvline(config.MDE_PP, color="#C44E52", ls="--", lw=1.2,
               label=f"action threshold {config.MDE_PP:.2f} pp")
    ax.axhline(0.80, color="#999999", ls=":", lw=1.0, label="80% power")
    d80 = float(power_kv["detectable_at_80_power_pp"])
    ax.plot([d80], [0.80], "o", color="#55A868", markersize=7,
            label=f"detectable at 80% power = {d80:.2f} pp")
    ax.set_xlabel("absolute effect on 7-day retention (percentage points)")
    ax.set_ylabel("power")
    ax.set_ylim(0, 1.02)
    ax.set_title("Sensitivity of this fixed sample — what it could have seen",
                 fontsize=12)
    ax.legend(loc="lower right", fontsize=9)
    written.append(_save(fig, "part3_03_power_curve.png"))

    # 04 — engagement distribution (from part3_09) ---------------------------
    bins = _read(tables / "part3_09_engagement_distribution.csv")
    fig, ax = plt.subplots()
    labels, width, offset = [], 0.4, {config.ARM_CONTROL: -0.2, config.ARM_VARIANT: 0.2}
    edges = sorted({int(b["bin_low"]) for b in bins})
    for b in bins:
        low, high = int(b["bin_low"]), int(b["bin_high"])
        x = edges.index(low) + offset[b["arm"]]
        ax.bar(x, int(b["count"]), width=width,
               color="#4C72B0" if b["arm"] == config.ARM_CONTROL else "#DD8452",
               label=b["arm"] if x < 1 else None)
    for low in edges:
        matching = [b for b in bins if int(b["bin_low"]) == low]
        high = int(matching[0]["bin_high"])
        labels.append(f"{low}+" if high < 0 else f"{low}-{high - 1}")
    ax.set_xticks(range(len(edges)))
    ax.set_xticklabels(labels, rotation=45, ha="right", fontsize=8)
    ax.set_xlabel("rounds played in the first 14 days")
    ax.set_ylabel("players")
    ax.set_title("Engagement distribution by arm", fontsize=12)
    handles, names = ax.get_legend_handles_labels()
    if handles:
        ax.legend(handles[:2], names[:2], fontsize=9)
    written.append(_save(fig, "part3_04_engagement_distribution.png"))

    return written
