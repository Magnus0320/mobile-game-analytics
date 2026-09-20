"""The derived-figure register (§7.5 as amended in v1.6, A-158, A-165).

Two classes of figure, and after this module there is only one:

  - a QUOTED figure appears verbatim as a cell of a committed table. Its register
    row is built by READING that cell, never by retyping it, so the row is a
    verified copy rather than a second assertion.
  - a DERIVED figure -- a count of rows meeting a condition, a sum, a difference,
    a ratio, a cross-table percentage, an extremum, any "N of M" -- is computed
    here from declared cells and emitted as its own cell in
    outputs/tables/part2_report_figures.csv. The prose then quotes that cell, so
    the derived figure has become a quoted one.

A cell locator is "file.csv:column:key=value&key2=value2". The key/value pairs
identify the row; the column names the cell. audit.py resolves the same locators,
so the declared cell is declared exactly once.
"""

import csv

from . import config as C

FIELDS = ["figure_id", "kind", "value_display", "value_num", "unit",
          "definition", "source_tables", "source_cells"]

_FORMATTERS = {
    "count": lambda v: f"{int(round(v)):,}",
    "pct": lambda v: f"{v:.2f}%",
    "pp": lambda v: f"{v:.2f} pp",
    "ratio": lambda v: f"{v:.1f}x",
    "bytes": lambda v: f"{int(round(v)):,}",
    "gib": lambda v: f"{v:.2f} GiB",
    "mib": lambda v: f"{v:.0f} MiB",
    "text": lambda v: str(v),
}


class LocatorError(LookupError):
    pass


_AGGS = {"min": min, "max": max, "sum": sum, "count": len}


def resolve(locator: str) -> str:
    """Return the raw text of the cell a locator names.

    "file.csv:column:key=value" names exactly one cell and is the normal form.
    "file.csv:column:key=value|min" applies an aggregate across every matching
    row, for the few figures whose declared source is a column rather than a
    cell -- "the row count of every shard", where the claim IS that min equals
    max. Aggregated locators are only accepted for derived figures.
    """
    agg = None
    if "|" in locator:
        locator, _, agg = locator.partition("|")
        if agg not in _AGGS:
            raise LocatorError(f"unknown aggregate {agg!r}")
    try:
        file_name, column, rowkey = locator.split(":", 2)
    except ValueError as exc:
        raise LocatorError(f"malformed locator {locator!r}") from exc
    path = C.TABLES / file_name
    if not path.exists():
        raise LocatorError(f"{locator}: no such table {file_name}")
    predicates = []
    if rowkey:
        for clause in rowkey.split("&"):
            key, _, value = clause.partition("=")
            predicates.append((key, value))
    with open(path, newline="") as fh:
        matches = [r for r in csv.DictReader(fh)
                   if all(r.get(k) == v for k, v in predicates)]
    if not matches:
        raise LocatorError(f"{locator}: matched no rows")
    if column not in matches[0]:
        raise LocatorError(f"{locator}: no column {column!r} in {file_name}")
    if agg is None:
        if len(matches) != 1:
            raise LocatorError(
                f"{locator}: matched {len(matches)} rows, expected exactly 1")
        return matches[0][column]
    values = [float(r[column].replace(",", "")) for r in matches if r[column] != ""]
    result = _AGGS[agg](values) if agg != "count" else len(values)
    return f"{result:.10f}".rstrip("0").rstrip(".")


def format_value(value, unit: str) -> str:
    if unit not in _FORMATTERS:
        raise ValueError(f"unknown unit {unit!r}")
    return _FORMATTERS[unit](value)


class Register:
    """Collects every figure the report is allowed to quote."""

    def __init__(self):
        self._rows: dict[str, dict] = {}

    def _add(self, figure_id, kind, value_display, value_num, unit,
             definition, cells):
        if figure_id in self._rows:
            raise ValueError(f"duplicate figure_id {figure_id!r}")
        tables = sorted({c.split(":", 1)[0] for c in cells})
        self._rows[figure_id] = {
            "figure_id": figure_id,
            "kind": kind,
            "value_display": value_display,
            "value_num": "" if value_num is None else f"{value_num:.10f}".rstrip("0").rstrip("."),
            "unit": unit,
            "definition": definition,
            "source_tables": ";".join(tables),
            "source_cells": ";".join(cells),
        }
        return value_display

    def quoted(self, figure_id, locator, unit, definition):
        """A figure that IS a committed cell. Read it; never retype it."""
        raw = resolve(locator)
        if unit == "text":
            display, number = raw, None
        else:
            number = float(raw.replace(",", ""))
            display = format_value(number, unit)
        return self._add(figure_id, "quoted", display, number, unit,
                         definition, [locator])

    def derived(self, figure_id, value, unit, definition, cells):
        """A figure COMPUTED from committed cells, emitted as its own cell."""
        if not cells:
            raise ValueError(f"{figure_id}: a derived figure must declare its sources")
        for locator in cells:
            resolve(locator)            # fail now if a declared source is wrong
        display = format_value(value, unit)
        return self._add(figure_id, "derived", display, None if unit == "text" else float(value),
                         unit, definition, list(cells))

    def value(self, figure_id) -> str:
        return self._rows[figure_id]["value_display"]

    def rows(self) -> list[dict]:
        return [self._rows[k] for k in sorted(self._rows)]

    def write(self, name="part2_report_figures.csv") -> str:
        path = C.TABLES / name
        with open(path, "w", newline="") as fh:
            writer = csv.DictWriter(fh, fieldnames=FIELDS, lineterminator="\n")
            writer.writeheader()
            for row in self.rows():
                writer.writerow(row)
        return name


def read_register(name="part2_report_figures.csv") -> list[dict]:
    with open(C.TABLES / name, newline="") as fh:
        return list(csv.DictReader(fh))
