"""Counters: a mechanism that did not report itself is a mechanism that did not run.

This module exists because of one measured failure class. In this project a flag
was set, the config validated, the run trained and reported a loss — and the
mechanism behind the flag never executed. Twice: the KDA arm ran 3126 forwards
and zero backwards, and `use_kda=false` turned out to mean "no attention at
all". Neither was visible in the logs, and neither was caught by ~3000 tests,
because those tests compared the code to itself.

The rule this module enforces, in code rather than in prose:

    If a mechanism is enabled, it must increment a counter that is read at the
    end of a step. Enabling a mechanism and leaving its counter at zero is a
    hard error, not a warning.

Usage:

    c = Counters()
    c.enable("kda")
    c.count("kda_fwd")
    ...
    c.check()          # raises MissingReport if an enabled mechanism never ran

The check is deliberately about *reporting*, not about correctness: it cannot
tell you that the kernel is right, only that it is not silently absent. That is
the defect class it exists for.
"""

from __future__ import annotations

from collections import Counter, defaultdict
from dataclasses import dataclass, field

from .errors import MissingReport

__all__ = ["Counters", "MissingReport"]


@dataclass
class Counters:
    """Per-step counters with an enable/require discipline.

    `enable(name)` declares that a mechanism is on for this run. `require(name,
    counter)` binds it to the counter that proves it ran. `check()` fails if any
    enabled mechanism's counter stayed at zero.
    """

    counts: Counter[str] = field(default_factory=Counter)
    enabled: set[str] = field(default_factory=set)
    required: dict[str, str] = field(default_factory=dict)
    _why: dict[str, str] = field(default_factory=lambda: defaultdict(str))

    # ---------------------------------------------------------------- writing
    def count(self, key: str, n: int = 1) -> None:
        """Add `n` to `key`; negative counts are refused as a programming error."""
        if n < 0:
            raise ValueError(f"count({key!r}, {n}): counters are non-negative")
        self.counts[key] += n

    def enable(self, mechanism: str, *, counter: str | None = None, why: str = "") -> None:
        """Mark a mechanism as on; `counter` is the proof that it ran."""
        self.enabled.add(mechanism)
        self.required[mechanism] = counter or mechanism
        if why:
            self._why[mechanism] = why

    # ----------------------------------------------------------------- checks
    def silent(self) -> list[str]:
        """Return the enabled mechanisms whose counter is still zero."""
        return sorted(m for m in self.enabled if self.counts.get(self.required[m], 0) == 0)

    def check(self) -> None:
        """Raise `MissingReport` listing every enabled mechanism that never ran."""
        missing = self.silent()
        if missing:
            raise MissingReport(missing)

    # ---------------------------------------------------------------- reading
    def line(self) -> str:
        """One log line: every non-zero counter, sorted, `k=v` separated."""
        return " ".join(f"{k}={v}" for k, v in sorted(self.counts.items()) if v)

    def reasons(self) -> dict[str, str]:
        """Return why each mechanism was enabled — printed next to the counters."""
        return {k: v for k, v in self._why.items() if v}

    def reset(self) -> None:
        """Clear the counts, keeping what is enabled and required."""
        self.counts.clear()

    def snapshot(self) -> dict[str, int]:
        """Return a plain copy of the counts, safe to log or compare."""
        return dict(self.counts)
