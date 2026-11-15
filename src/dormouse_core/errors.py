"""Errors that name the way out.

Every refusal in this project has one job: tell the reader what to do instead.
A message like "invalid configuration" costs an hour of guessing; a message like
"kda requires pos='none', got 'rope': set pos='none' or pick attn='sdpa'" costs
nothing. Because the same nine silent failures kept coming back, the *shape* of
an error is enforced here rather than left to each caller: an error either
carries an escape or it is a bug.
"""

from __future__ import annotations

from dataclasses import dataclass


class DormouseError(Exception):
    """Base class. Every project error has a `what` and, usually, an `escape`."""

    def __init__(self, what: str, escape: str | None = None) -> None:
        """Keep the two parts separate so callers can render them differently."""
        self.what = what
        self.escape = escape
        super().__init__(self.message())

    def message(self) -> str:
        """Render `what` and, when present, the escape."""
        if self.escape:
            return f"{self.what}. Escape: {self.escape}"
        return self.what


class LoudError(DormouseError):
    """A refused configuration or an impossible state — the run must not start."""


class MissingReport(DormouseError):
    """An enabled mechanism never proved it ran."""

    def __init__(self, names: list[str]) -> None:
        """Name every silent mechanism at once, not the first one found."""
        listed = ", ".join(sorted(names))
        super().__init__(
            f"enabled but never reported: {listed}",
            "either the flag did not reach the code (fix the wiring) or the "
            "mechanism genuinely did not run (do not enable it)",
        )


@dataclass(frozen=True)
class Message:
    """A rendered diagnostic: what happened, what to do, and how bad it is."""

    what: str
    escape: str | None = None
    fatal: bool = True

    def line(self) -> str:
        """Render one log line for this message."""
        if self.escape:
            return f"{self.what}. Escape: {self.escape}"
        return self.what
