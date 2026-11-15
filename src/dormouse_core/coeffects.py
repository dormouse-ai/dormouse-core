"""What a component needs, and what it takes out of the shared context.

A coeffect is the declaration half of replaceability: before a component is
allowed to run, the loader compares this declaration with the context and refuses
with a named reason. That refusal happens before any allocation or mutation, which
is why an incompatible component cannot half-initialise.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class Coeffects:
    """Requirements, provisions, and the names this component claims exclusively."""

    requires: dict[str, str] = field(default_factory=dict)
    provides: dict[str, str] = field(default_factory=dict)
    exclusive: tuple[str, ...] = ()

    def unsatisfied(self, ctx: dict[str, str]) -> str:
        """Return the first gap as a sentence, or an empty string when it fits."""
        for key, want in self.requires.items():
            have = ctx.get(key)
            if have is None:
                return f"needs {key}={want!r}, the context has no {key!r}"
            if have != want:
                return f"needs {key}={want!r}, the context has {have!r}"
        return ""

    def satisfied_by(self, ctx: dict[str, str]) -> tuple[bool, str]:
        """Return whether the context fits, and the reason when it does not."""
        gap = self.unsatisfied(ctx)
        return (not gap), gap
