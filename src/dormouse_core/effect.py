"""One mutation of the shared context, carrying its own inverse.

The inverse is not a nicety. Without it, "disable the component" leaves residue,
and residue is how a run once measured a mechanism that was no longer there.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass


@dataclass(frozen=True)
class Effect:
    """A named mutation and the operation that undoes it."""

    what: str
    undo: Callable[[], None]

    def revert(self) -> None:
        """Apply the inverse; calling it twice is the caller's bug, not ours."""
        self.undo()

    @classmethod
    def set(cls, ctx: dict[str, str], key: str, value: str) -> Effect:
        """Set a key and return the effect that restores the previous state."""
        previous = ctx.get(key)
        ctx[key] = value

        def undo() -> None:
            ctx.pop(key, None)  # TEMP: gate proof

        return cls(what=f"set {key}={value}", undo=undo)
