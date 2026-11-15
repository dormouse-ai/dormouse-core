"""A plan you can read before spending a GPU-day.

Every long run in this project started with a command whose cost was estimated in
someone's head. This module makes the estimate a value: a list of phases, each
with what it will do and how long it will take, printed before anything is
allocated. `require_approval` is the reason it exists — a plan that predicts more
than the allowed budget must be approved explicitly rather than discovered at
hour six.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from .errors import LoudError

__concepts__ = ("Plan",)


@dataclass(frozen=True)
class Phase:
    """One step of a run, with its honest cost."""

    name: str
    seconds: float
    note: str = ""

    def human(self) -> str:
        """Render the duration the way a person reads it."""
        if self.seconds < 90:
            return f"{self.seconds:.0f}s"
        if self.seconds < 3600:
            return f"{self.seconds / 60:.0f}min"
        return f"{self.seconds / 3600:.1f}h"


@dataclass
class Plan:
    """An ordered set of phases plus the warnings that make it risky."""

    phases: list[Phase] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    def add(self, name: str, seconds: float, note: str = "") -> Plan:
        """Append a phase; returns self so plans read as a chain."""
        self.phases.append(Phase(name=name, seconds=seconds, note=note))
        return self

    def warn(self, text: str) -> Plan:
        """Record a risk that should be visible before the run starts."""
        self.warnings.append(text)
        return self

    @property
    def seconds(self) -> float:
        """Total predicted duration."""
        return sum(p.seconds for p in self.phases)

    def render(self) -> list[str]:
        """Lines to print: phases with durations, then warnings."""
        lines = [f"plan: {len(self.phases)} phase(s), {Phase('', self.seconds).human()} total"]
        for p in self.phases:
            suffix = f"  # {p.note}" if p.note else ""
            lines.append(f"  {p.human():>8}  {p.name}{suffix}")
        lines.extend(f"  warning: {w}" for w in self.warnings)
        return lines

    def require_approval(self, budget_seconds: float) -> None:
        """Refuse a plan longer than the budget unless the caller says otherwise."""
        if self.seconds <= budget_seconds:
            return
        raise LoudError(
            f"plan needs {Phase('', self.seconds).human()}, budget is "
            f"{Phase('', budget_seconds).human()}",
            "re-run with --yes to accept the cost, or shrink the run",
        )
