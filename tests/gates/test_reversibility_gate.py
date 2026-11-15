"""Deactivate restores the context exactly — the reversibility gate, as a property.

This is the invariant that would have caught every "we turned the flag off and the
run still behaved as if it were on" defect. It is a property, not an example: any
set of keys a component writes must be gone after `deactivate`, whatever the
context looked like before — including a key that already had a value, which must
come back with that value and not merely "not gone".
"""

from __future__ import annotations

from collections.abc import Iterable

from hypothesis import given, settings
from hypothesis import strategies as st

from dormouse_core.coeffects import Coeffects
from dormouse_core.effect import Effect
from dormouse_core.slot import Slot

#: The keys a property run may start with and over-write.
KEYS = ["a", "b", "c", "d"]


class _Writes:
    """A component that writes its keys into the context and returns their undo."""

    name = "writes"
    slot = "content"

    def __init__(self, keys: Iterable[str]) -> None:
        """Remember what to write."""
        self.keys = tuple(keys)

    def coeffects(self) -> Coeffects:
        """Declare nothing: it only takes keys it is given."""
        return Coeffects()

    def activate(self, ctx: dict[str, str]) -> list[Effect]:
        """Set every key, returning the effect that restores the previous value."""
        return [Effect.set(ctx, key, "on") for key in self.keys]

    def deactivate(self) -> None:
        """Nothing is held outside the context."""


def test_activate_then_deactivate_is_the_identity() -> None:
    """Both branches of the undo: a new key is removed, an old one gets its value back."""
    ctx = {"keep": "me", "a": "old"}
    slot = Slot(ctx=ctx)
    slot.activate(_Writes(["a", "b"]))
    assert ctx == {"keep": "me", "a": "on", "b": "on"}
    slot.deactivate("content")
    assert ctx == {"keep": "me", "a": "old"}


@settings(max_examples=50)
@given(
    before=st.dictionaries(st.sampled_from(KEYS), st.sampled_from(["old", "1"]), max_size=4),
    keys=st.lists(st.sampled_from(KEYS), unique=True, min_size=1, max_size=4),
)
def test_any_key_set_is_reverted_exactly(before: dict[str, str], keys: list[str]) -> None:
    ctx = dict(before)
    slot = Slot(ctx=ctx)
    slot.activate(_Writes(keys))
    slot.deactivate("content")
    assert ctx == before
