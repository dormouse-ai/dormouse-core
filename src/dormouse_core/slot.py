"""Occupancy: at most one active component per slot, and swapping that reverts.

The invariant this file exists for: after `deactivate`, the context is what it
was before `activate`, bit for bit.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from .component import Component, ComponentError
from .effect import Effect


@dataclass
class Slot:
    """Holds active components and the effects that must be undone to remove them."""

    ctx: dict[str, str] = field(default_factory=dict)
    active: dict[str, Component] = field(default_factory=dict)  # by slot
    effects: dict[str, list[Effect]] = field(default_factory=dict)

    def occupant(self, slot: str) -> Component | None:
        """Return the component in `slot`, or None when it is empty."""
        return self.active.get(slot)

    def activate(self, comp: Component) -> None:
        """Activate a component, or refuse with a named reason before it mutates."""
        if comp.slot in self.active:
            raise ComponentError(
                f"slot {comp.slot!r} already holds {self.active[comp.slot].name!r}",
                f"deactivate it first, or use swap({comp.name!r})",
            )
        gap = comp.coeffects().unsatisfied(self.ctx)
        if gap:
            raise ComponentError(
                f"{comp.name!r} cannot activate: it {gap}",
                "change the context or pick a component whose coeffects match",
            )
        produced = comp.activate(self.ctx)
        self.active[comp.slot] = comp
        self.effects[comp.slot] = list(produced)

    def deactivate(self, slot: str) -> None:
        """Revert the slot's effects in reverse order, then release the component."""
        comp = self.active.get(slot)
        if comp is None:
            raise ComponentError(f"slot {slot!r} is empty", "nothing to deactivate")
        for effect in reversed(self.effects[slot]):
            effect.revert()
        comp.deactivate()
        del self.active[slot]
        del self.effects[slot]

    def swap(self, comp: Component) -> None:
        """Replace whatever occupies the same slot, reverting it first."""
        if comp.slot in self.active:
            self.deactivate(comp.slot)
        self.activate(comp)
