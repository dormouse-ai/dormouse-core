"""Ordering components so every requirement is provided before it is used.

A cycle raises instead of producing an arbitrary order: an arbitrary order is how
a model ends up with attention built before the positional scheme that attention
depends on.
"""

from __future__ import annotations

from collections.abc import Iterable

from .component import Component, ComponentError


def topo_order(comps: Iterable[Component]) -> list[Component]:
    """Order providers before consumers, and raise when one is missing."""
    remaining = list(comps)
    ordered: list[Component] = []
    ctx: dict[str, str] = {}
    while remaining:
        progressed = False
        for comp in list(remaining):
            if not comp.coeffects().unsatisfied(ctx):
                ordered.append(comp)
                ctx.update(comp.coeffects().provides)
                remaining.remove(comp)
                progressed = True
        if not progressed:
            names = ", ".join(c.name for c in remaining)
            first = remaining[0]
            gap = first.coeffects().unsatisfied(ctx)
            raise ComponentError(
                f"cannot order {names}: {first.name!r} {gap}",
                "add a component that provides that key, or remove the requirement",
            )
    return ordered
