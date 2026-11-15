"""The two properties that make a component replaceable, tested as properties.

Not "does activate() run" — that is a unit test of nothing. What matters:

* a component whose coeffects do not match is refused **before** it mutates
  anything (spatial composability);
* activating then deactivating restores the context **exactly** (temporal
  composability) — this is the property that would have caught every "we turned
  the flag off and the run still behaved as if it were on" defect.
"""

from __future__ import annotations

import pytest

from dormouse_core.component import Coeffects, ComponentError
from dormouse_core.effect import Effect
from dormouse_core.errors import LoudError
from dormouse_core.order import topo_order
from dormouse_core.slot import Slot


class Writer:
    """A component that writes N keys into the context and can undo them."""

    name = "writer"
    slot = "content"

    def __init__(self, keys: list[str], value: str = "on") -> None:
        self.keys = keys
        self.value = value
        self.active = False

    def coeffects(self) -> Coeffects:
        return Coeffects(provides=dict.fromkeys(self.keys, self.value))

    def activate(self, ctx: dict[str, str]) -> list[Effect]:
        self.active = True
        effects = []
        for key in self.keys:
            previous = ctx.get(key)
            ctx[key] = self.value

            def undo(k: str = key, prev: str | None = previous) -> None:
                if prev is None:
                    ctx.pop(k, None)
                else:
                    ctx[k] = prev

            effects.append(Effect(what=f"set {key}", undo=undo))
        return effects

    def deactivate(self) -> None:
        self.active = False


class Needs:
    """A component that requires a key before it may run."""

    name = "needs"
    slot = "consumer"

    def __init__(self, key: str, want: str) -> None:
        self.key = key
        self.want = want
        self.touched = False

    def coeffects(self) -> Coeffects:
        return Coeffects(requires={self.key: self.want})

    def activate(self, ctx: dict[str, str]) -> list[Effect]:
        self.touched = True
        return []

    def deactivate(self) -> None:
        return None


def test_a_component_is_refused_before_it_touches_anything() -> None:
    ctx: dict[str, str] = {}
    slot = Slot(ctx=ctx)
    comp = Needs("dtype", "bf16")
    with pytest.raises(ComponentError) as e:
        slot.activate(comp)
    assert "dtype" in str(e.value)
    assert "Escape" in str(e.value)
    assert comp.touched is False, "refusal must happen before activation runs"
    assert ctx == {}


def test_the_right_context_lets_it_through() -> None:
    slot = Slot(ctx={"dtype": "bf16"})
    comp = Needs("dtype", "bf16")
    slot.activate(comp)
    assert comp.touched is True


def test_swap_reverts_the_previous_occupant() -> None:
    ctx: dict[str, str] = {}
    slot = Slot(ctx=ctx)
    first = Writer(["x"], "one")
    slot.activate(first)
    second = Writer(["y"], "two")
    second.name = "writer2"
    slot.swap(second)  # same slot, so the first must be reverted
    assert ctx == {"y": "two"}


def test_double_activation_is_refused_with_an_escape() -> None:
    slot = Slot()
    slot.activate(Writer(["a"]))
    with pytest.raises(ComponentError) as e:
        slot.activate(Writer(["b"]))
    assert "swap(" in str(e.value)


def test_topological_order_puts_providers_first() -> None:
    provider = Writer(["pos"])
    provider.name = "rope"
    consumer = Needs("pos", "on")
    ordered = topo_order([consumer, provider])
    assert [c.name for c in ordered] == ["rope", "needs"]


def test_a_missing_provider_is_named_not_guessed() -> None:
    consumer = Needs("attn.kind", "kda")
    with pytest.raises(ComponentError) as e:
        topo_order([consumer])
    assert "attn.kind" in str(e.value)


def test_errors_carry_an_escape() -> None:
    err = LoudError("bad config", "set dtype=bf16")
    assert "Escape: set dtype=bf16" in str(err)
