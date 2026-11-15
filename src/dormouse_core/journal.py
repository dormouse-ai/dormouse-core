"""The run journal: one append-only record per run, readable by a human and a tool.

Why a journal and not log files: three times a run reported a number that could
not be reconstructed afterwards, because the config lived in a shell history, the
seed lived in a script, and the loss lived in a `grep` over stdout. A journal
makes the run itself the artifact — every number, every config change, every
segment boundary is one JSON object per line, and `status` reads only this.

Append-only matters for a second reason: a hot swap (a component replaced, a
kernel upgraded) must appear as an event *with a step number*, not as a silent
change between two log files. That is what keeps a swapped run reproducible.
"""

from __future__ import annotations

import json
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from .errors import LoudError

#: The events a run may write. A closed set, because an event nobody reads is a
#: field nobody validates.
KINDS = frozenset({"start", "step", "eval", "swap", "end"})


@dataclass
class Journal:
    """Append-only JSONL of a single run."""

    path: Path
    records: list[dict[str, Any]] = field(default_factory=list)

    @classmethod
    def open(cls, path: str | Path) -> Journal:
        """Open (or create) a journal, loading whatever is already there."""
        p = Path(path)
        p.parent.mkdir(parents=True, exist_ok=True)
        journal = cls(path=p)
        if p.exists():
            journal.records = _load(p)
        return journal

    def write(self, kind: str, **fields: Any) -> dict[str, Any]:
        """Append one event; `kind` must be one the project knows how to read."""
        if kind not in KINDS:
            raise LoudError(
                f"unknown journal event {kind!r}",
                f"use one of: {', '.join(sorted(KINDS))}",
            )
        if "step" in fields and not isinstance(fields["step"], int):
            raise LoudError("journal 'step' must be an int", "pass the optimizer step as an int")
        record = {"kind": kind, "t": round(time.time(), 3), **fields}
        with self.path.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(record, sort_keys=True) + "\n")
        self.records.append(record)
        return record

    def last(self, kind: str) -> dict[str, Any] | None:
        """Return the most recent event of a kind, or None."""
        for record in reversed(self.records):
            if record.get("kind") == kind:
                return dict(record)
        return None

    def segments(self) -> list[dict[str, Any]]:
        """Return the swap events: every point where the run changed shape."""
        return [r for r in self.records if r.get("kind") == "swap"]

    def summary(self) -> str:
        """One line a human can read: phase, step, last metric."""
        start = self.last("start") or {}
        step = self.last("step") or {}
        tail = self.last("end") or {}
        phase = "ended" if tail else ("running" if step else "not started")
        return (
            f"{phase} step={step.get('step', 0)} "
            f"config={start.get('config', '?')} segments={len(self.segments())}"
        )


def _load(path: Path) -> list[dict[str, Any]]:
    """Read a journal, refusing a corrupted line instead of skipping it."""
    out: list[dict[str, Any]] = []
    for lineno, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip():
            continue
        try:
            out.append(json.loads(line))
        except json.JSONDecodeError as exc:
            raise LoudError(
                f"{path}: line {lineno}: corrupted journal ({exc.msg})",
                "a journal is append-only; restore the line or start a new run",
            ) from None
    return out
