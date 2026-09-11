"""The three failure classes of ARCHITECTURE.md §7.7, represented in code.

  hard stop  — raise. `StructuralFault` for a data fault at the §7.7 step 5
               gate; `SelfVerificationFailure` for step 20. Both propagate out
               of the entrypoint uncaught, so the process exits non-zero.
  downgrade  — `RunState.downgrade(...)`. Appends a reason and returns. It
               never raises, and no code path lets a downgrade skip a later
               step: the run continues to completion with the full analysis
               computed and reported, and only the recommendation is withheld
               (§2.4, rule R0).
  finding    — `RunState.finding(...)`. Recorded in the outputs; run continues.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


class StructuralFault(RuntimeError):
    """The file is not the file ARCHITECTURE.md describes (§5 preamble).

    Raised only at §7.7 step 5's single structural gate and by the step 9
    assertion group. Past step 5, no token value can stop the run.
    """


class SelfVerificationFailure(RuntimeError):
    """A §7.7 step 20 self-verification assertion failed.

    Unlike every other hard stop, this one occurs after step 19 has written
    outputs, so the files on disk are the product of a failed run. They must not
    be committed. See A-070 for why the failure-class label is imprecise here and
    what carries the consequence instead.
    """


@dataclass(frozen=True)
class Finding:
    step: int
    finding_id: str
    description: str
    values: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class Downgrade:
    step: int
    source: str
    detail: str
    values: dict[str, Any] = field(default_factory=dict)


@dataclass
class RunState:
    """Accumulates findings, downgrade reasons and denominators across the run."""

    findings: list[Finding] = field(default_factory=list)
    downgrades: list[Downgrade] = field(default_factory=list)
    denominators: dict[str, int] = field(default_factory=dict)

    # --- finding ------------------------------------------------------------
    def finding(
        self,
        step: int,
        finding_id: str,
        description: str,
        values: dict[str, Any] | None = None,
    ) -> None:
        self.findings.append(
            Finding(step=step, finding_id=finding_id, description=description,
                    values=dict(values or {}))
        )

    # --- downgrade ----------------------------------------------------------
    def downgrade(
        self,
        step: int,
        source: str,
        detail: str,
        values: dict[str, Any] | None = None,
    ) -> None:
        """Set the R0 integrity flag and CONTINUE. Never raises (§7.7, §2.4)."""
        self.downgrades.append(
            Downgrade(step=step, source=source, detail=detail,
                      values=dict(values or {}))
        )
        self.finding(
            step=step,
            finding_id=f"downgrade:{source}",
            description=f"Integrity downgrade triggered (rule R0): {detail}",
            values=values,
        )

    @property
    def is_downgraded(self) -> bool:
        return len(self.downgrades) > 0

    # --- denominators -------------------------------------------------------
    def record_denominator(self, key: str, n: int) -> None:
        """Record a denominator so §7.7 step 20 can re-check what was reported."""
        if key in self.denominators and self.denominators[key] != n:
            raise SelfVerificationFailure(
                f"Denominator {key!r} recorded twice with different values: "
                f"{self.denominators[key]} then {n}."
            )
        self.denominators[key] = int(n)
