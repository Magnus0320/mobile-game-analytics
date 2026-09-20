"""The declared-cell audit, and the negative self-test that proves it can fail.

§7.5 as amended in v1.6: "The audit checks the declared cell, not the corpus.
Each prose figure is tagged with the table and column it comes from, and the
audit verifies THAT cell. A number that appears somewhere in the tables but not
in its declared cell FAILS."

Part 1's audit verified that every prose figure appeared verbatim SOMEWHERE in a
committed table. A hand-written "20 ineligible cells" passed it against a true
count of 5, because "20" occurred in the tables as an unrelated figure. That is
the failure this module exists to make impossible, and `selftest()` replants it
on every run: an audit that has never been observed to fail is an assertion, not
a check, and Part 1's had never been observed to fail either.
"""

import re

from . import config as C
from . import markdown
from .report_figures import LocatorError, format_value, resolve

FIG_RE = re.compile(r"<!--fig:([A-Za-z0-9_.\-]+)-->")

# --- §7.5's exempt numerals, enumerated so the exemption is checkable ---------
# Anything not matched here and not carrying a <!--fig:--> tag FAILS.
EXEMPT_PATTERNS = [
    (r"`[^`]*`", "identifiers and labels in code spans"),
    (r"\]\([^)]*\)", "markdown link targets"),
    (r"§\d+(?:\.\d+)*", "section numbers"),
    (r"\bA-\d{3}\b", "assumptions.md references"),
    (r"\bv\d+\.\d+\b", "ARCHITECTURE.md version references"),
    (r"\bPart [123]\b", "part names"),
    (r"\b20\d{6}\b", "dates in shard-suffix form"),
    (r"\b\d{4}-\d{2}-\d{2}\b", "ISO dates"),
    (r"\bS[0-3]\b", "funnel step labels"),
    (r"\b(?=[0-9a-f]{7,40}\b)[0-9a-f]*[a-f][0-9a-f]*\b", "commit SHAs"),
    (r"\b(?:item|reading|step|query|section|figure|row)s?\s+\d+\b",
     "references to this document's own numbered items"),
    # thresholds quoted from ARCHITECTURE.md, as literals and nothing wider
    (r"\b1\.0%", "§10.6.4 / §10.6.5 trigger"),
    (r"\b5\.0%", "§10.7.5 caveat trigger"),
    (r"\b25\.0%", "§10.7.5 drop trigger"),
    (r"\b0\.5%", "§10.3 coverage threshold"),
    (r"\b1,000\b", "§10.3 event threshold"),
    (r"\b200\b", "§10.7.5 Part 2 segment floor"),
    (r"\b30\b", "§10.5.3 suppression floor"),
    (r"\b95%", "the interval's confidence level"),
]

# Spelled-out quantities are scanned too -- "twenty" would dodge a digit
# scanner, and a spelled-out wrong count is the same defect in words. Only
# counts of this document's own items are exempt.
EXEMPT_WORDS = {"one", "two", "three", "four", "five", "seven",
                "both", "single", "once", "twice"}
WORD_RE = re.compile(
    r"\b(one|two|three|four|five|six|seven|eight|nine|ten|eleven|twelve|"
    r"thirteen|fourteen|fifteen|sixteen|seventeen|eighteen|nineteen|twenty|"
    r"thirty|forty|fifty|hundred|thousand|million|dozen|both|single|once|twice)\b",
    re.I)
NUMERAL_RE = re.compile(r"\d[\d,]*(?:\.\d+)?%?")
FENCE_RE = re.compile(r"```.*?```", re.S)


def _strip_exempt(text: str) -> str:
    out = FENCE_RE.sub(" ", text)
    for pattern, _ in EXEMPT_PATTERNS:
        out = re.sub(pattern, " ", out)
    return out


def scan_untagged(text: str) -> list[str]:
    """Every numeral and spelled-out quantity left after tags and exemptions."""
    problems = []
    residue = _strip_exempt(text)
    for match in NUMERAL_RE.finditer(residue):
        context = residue[max(0, match.start() - 45):match.end() + 25].strip()
        problems.append(
            f"untagged numeral {match.group(0)!r} — every figure in prose must "
            f"carry <!--fig:id--> naming its declared cell … {context!r}")
    for match in WORD_RE.finditer(residue):
        if match.group(0).lower() in EXEMPT_WORDS:
            continue
        context = residue[max(0, match.start() - 45):match.end() + 25].strip()
        problems.append(
            f"untagged spelled-out quantity {match.group(0)!r} … {context!r}")
    return problems


def audit_prose(text: str, register_rows: list[dict]) -> list[str]:
    """Check every tagged figure against its declared cell, then scan the rest."""
    problems = []
    body = markdown.strip_blocks(text)
    known = {r["figure_id"]: r["value_display"] for r in register_rows}
    used, kept, cursor = set(), [], 0

    for match in FIG_RE.finditer(body):
        figure_id = match.group(1)
        before = body[cursor:match.start()]
        cursor = match.end()
        if figure_id not in known:
            problems.append(
                f"tag <!--fig:{figure_id}--> names no row of "
                f"part2_report_figures.csv")
            kept.append(before)
            continue
        expected = known[figure_id]
        if before.endswith(expected):
            kept.append(before[:-len(expected)])     # the figure is accounted for
            used.add(figure_id)
        else:
            problems.append(
                f"tag <!--fig:{figure_id}--> declares {expected!r} but the prose "
                f"before it ends {before[-40:]!r}")
            kept.append(before)
    kept.append(body[cursor:])

    for figure_id in sorted(known):
        if figure_id not in used:
            problems.append(
                f"register row {figure_id!r} is never quoted — a dead row is a "
                f"figure nobody can check against prose")
    return problems + scan_untagged("".join(kept))


def audit_tables(text: str, views: dict) -> list[str]:
    """Regenerate every embedded table from its committed CSV and compare."""
    problems = []
    seen = set()
    for view_id, body in markdown.find_blocks(text):
        seen.add(view_id)
        if view_id not in views:
            problems.append(f"table block {view_id!r} has no generator")
            continue
        regenerated = views[view_id]()
        if regenerated != body:
            problems.append(
                f"table block {view_id!r} does not match its committed CSV; "
                f"regenerate it rather than editing the report")
    return problems


def check_register(register_rows: list[dict]) -> list[str]:
    """Register integrity. Runs before any prose exists."""
    problems = []
    seen = set()
    for row in register_rows:
        figure_id = row["figure_id"]
        if figure_id in seen:
            problems.append(f"duplicate figure_id {figure_id!r}")
        seen.add(figure_id)
        locators = [c for c in row["source_cells"].split(";") if c]
        if not locators:
            problems.append(f"{figure_id}: declares no source cell")
        for locator in locators:
            try:
                raw = resolve(locator)
            except LocatorError as exc:
                problems.append(f"{figure_id}: {exc}")
                continue
            if row["kind"] == "quoted":
                unit = row["unit"]
                expected = (raw if unit == "text"
                            else format_value(float(raw.replace(",", "")), unit))
                if expected != row["value_display"]:
                    problems.append(
                        f"{figure_id}: declared cell holds {expected!r}, register "
                        f"row says {row['value_display']!r}")
    return problems


# --- the negative self-test --------------------------------------------------

_FIXTURE_REGISTER = [
    {"figure_id": "ineligible_cells", "kind": "derived", "value_display": "5",
     "unit": "count", "source_cells": "", "definition": "fixture"},
]


def selftest() -> list[str]:
    """Assert the audit REJECTS four fixtures and ACCEPTS one.

    The rejections alone would be satisfied by an audit that rejected
    everything, so the acceptance case is part of the test rather than a
    courtesy.
    """
    cases = [
        ("part 1's failure replanted: a wrong derived count whose digits occur "
         "in the tables as an unrelated figure",
         "Beside the 20<!--fig:ineligible_cells--> ineligible cells.", True),
        ("an untagged numeral",
         "There were 1,234 users at that step.", True),
        ("a spelled-out quantity",
         "Beside the twenty ineligible cells.", True),
        ("a tag naming no register row",
         "Beside the 5<!--fig:no_such_figure--> cells.", True),
        ("a correct fixture, which must be ACCEPTED",
         "Beside the 5<!--fig:ineligible_cells--> ineligible cells, per §10.5.5 "
         "and A-142, against the 1.0% trigger.", False),
    ]
    notes = []
    for label, prose, must_fail in cases:
        problems = audit_prose(prose, _FIXTURE_REGISTER)
        if must_fail and not problems:
            raise AssertionError(
                f"audit self-test: the audit ACCEPTED {label!r}. The audit cannot "
                f"detect the error class it exists for; no figure in this report "
                f"is checked.")
        if not must_fail and problems:
            raise AssertionError(
                f"audit self-test: the audit REJECTED {label!r} — {problems}. An "
                f"audit that rejects everything checks nothing.")
        notes.append(("rejected" if must_fail else "accepted") + ": " + label)
    return notes
