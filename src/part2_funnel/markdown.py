"""Markdown tables GENERATED from committed CSVs, and regenerated to verify them.

§7.5 as amended in v1.6 requires each prose figure to be checked against its
DECLARED cell rather than against the corpus. A funnel report's tables carry
hundreds of cells, and tagging each one would swamp the source. A-165 takes the
stronger route instead: a report table is not written, it is generated here from
its committed CSV and embedded between markers, and audit.py regenerates it and
asserts byte-equality. No cell in a report table can be wrong, because no cell in
a report table is typed.
"""

import re

BLOCK_RE = re.compile(
    r"<!--table:(?P<view>[A-Za-z0-9_.\-]+)-->\n(?P<body>.*?)\n<!--/table-->",
    re.S,
)


def table(headers: list[str], aligns: list[str], rows: list[list[str]]) -> str:
    """A GitHub-flavoured markdown table. `aligns` are 'l', 'r' or 'c'."""
    if len(headers) != len(aligns):
        raise ValueError("headers and aligns must be the same length")
    rule = {"l": "---", "r": "---:", "c": ":---:"}
    out = ["| " + " | ".join(headers) + " |",
           "|" + "|".join(rule[a] for a in aligns) + "|"]
    for row in rows:
        if len(row) != len(headers):
            raise ValueError(f"row has {len(row)} cells, header has {len(headers)}")
        out.append("| " + " | ".join(str(c) for c in row) + " |")
    return "\n".join(out)


def block(view_id: str, body: str) -> str:
    """Wrap a generated body in the markers the audit looks for."""
    return f"<!--table:{view_id}-->\n{body}\n<!--/table-->"


def find_blocks(text: str) -> list[tuple[str, str]]:
    return [(m.group("view"), m.group("body")) for m in BLOCK_RE.finditer(text)]


def strip_blocks(text: str) -> str:
    """Remove generated table blocks; they are verified by regeneration, not by
    the prose scanner."""
    return BLOCK_RE.sub("\n", text)
