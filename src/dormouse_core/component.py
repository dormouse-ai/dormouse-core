"""The protocol every swappable piece of the system implements.

Kept to one concern: what a component *is*. Ordering lives in `order.py`,
occupancy and swapping in `slot.py`.
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from .coeffects import Coeffects
from .effect import Effect
from .errors import LoudError


class ComponentError(LoudError):
    """A component could not be activated, or refused to be deactivated."""


@runtime_checkable
class Component(Protocol):
    """A piece of the system that declares its needs and can undo its effects.

    `slot` is the position it occupies ("attn", "ffn", "objective"). Swapping is
    defined per slot, so two attention implementations can never both be active
    while an attention and an FFN coexist happily.
    """

    name: str
    slot: str

    def coeffects(self) -> Coeffects:
        """Declare what this component needs and provides."""
        ...

    def activate(self, ctx: dict[str, str]) -> list[Effect]:
        """Take the context, return the effects that undo this activation."""
        ...

    def deactivate(self) -> None:
        """Release anything held outside the context; effects were already reverted."""
        ...
