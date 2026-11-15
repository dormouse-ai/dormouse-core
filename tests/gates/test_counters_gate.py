"""The counter invariant, run as its own CI job so a silent mechanism is red.

The two shapes that cost this project: a flag that was on while the code behind it
never ran, and a mechanism that ran forward-only. Both are one line here and both
are a hard error in `Counters.check()`, not a warning in a log.
"""

from __future__ import annotations

import pytest

from dormouse_core.counters import Counters, MissingReport


def test_an_enabled_mechanism_that_never_runs_is_an_error() -> None:
    """`use_kda=false` meant "no attention at all": the flag was on, nothing ran."""
    counters = Counters()
    counters.enable("kda", why="the config asked for the chunked kernel")
    with pytest.raises(MissingReport) as e:
        counters.check()
    assert "kda" in str(e.value)
    assert "did not reach the code" in str(e.value)


def test_a_forward_only_mechanism_is_an_error() -> None:
    """3126 forwards and zero backwards: half a mechanism is not a mechanism."""
    counters = Counters()
    counters.enable("kda", counter="kda_bwd")
    counters.count("kda_fwd", 3126)
    with pytest.raises(MissingReport):
        counters.check()
    counters.count("kda_bwd")
    counters.check()  # now it may pass
