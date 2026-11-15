"""Tests for the counter discipline.

The point of these tests is not that `Counters` works — it is that a mechanism
whose counter never moves is a *failure*, demonstrated on the two shapes that
actually bit us: a flag that never reached the code, and a mechanism that ran
forward-only.
"""

from __future__ import annotations

import pytest

from dormouse_core.counters import Counters, MissingReport


def test_a_counter_records_and_reports() -> None:
    c = Counters()
    c.count("fwd")
    c.count("fwd")
    c.count("bwd", 3)
    assert c.snapshot() == {"fwd": 2, "bwd": 3}
    assert c.line() == "bwd=3 fwd=2"


def test_two_silent_mechanisms_are_both_named() -> None:
    c = Counters()
    c.enable("engram")
    c.enable("mhc")
    with pytest.raises(MissingReport) as e:
        c.check()
    assert "engram" in str(e.value) and "mhc" in str(e.value)


def test_reset_keeps_the_discipline() -> None:
    c = Counters()
    c.enable("lfb")
    c.count("lfb")
    c.check()
    c.reset()
    assert c.snapshot() == {}
    with pytest.raises(MissingReport):
        c.check()


def test_reasons_are_carried_for_the_log() -> None:
    c = Counters()
    c.enable("engram", why="402M host tables")
    assert c.reasons() == {"engram": "402M host tables"}


def test_negative_counts_are_refused() -> None:
    c = Counters()
    with pytest.raises(ValueError):
        c.count("x", -1)


def test_zero_counts_are_not_printed() -> None:
    """A zero in the log reads as 'ran and did nothing' — do not print it."""
    c = Counters()
    c.count("a")
    assert c.line() == "a=1"
