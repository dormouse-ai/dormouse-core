"""The plan is the thing that stops a run from being a surprise.

The tests are about the two failures a plan can have: it can under-predict (then
the budget guard never fires) and it can hide a warning (then the reader accepts a
run they would have refused).
"""

from __future__ import annotations

import pytest

from dormouse_core.errors import LoudError
from dormouse_core.plan import Phase, Plan


def test_phases_sum_and_render() -> None:
    plan = Plan().add("pretrain", 3600, "13 GB").add("sft", 600)
    assert plan.seconds == 4200
    lines = plan.render()
    assert lines[0].startswith("plan: 2 phase(s)")
    assert "1.2h" in lines[0]
    assert "pretrain" in lines[1]


def test_warnings_are_printed_not_stored_silently() -> None:
    plan = Plan().add("train", 60).warn("batch 24 is 0.2 GiB from OOM")
    assert "warning: batch 24" in "\n".join(plan.render())


def test_a_plan_over_budget_is_refused_with_the_escape() -> None:
    plan = Plan().add("train", 7200)
    with pytest.raises(LoudError) as e:
        plan.require_approval(budget_seconds=3600)
    assert "--yes" in str(e.value)


def test_a_plan_under_budget_passes() -> None:
    Plan().add("train", 60).require_approval(budget_seconds=3600)


def test_human_durations_switch_units() -> None:
    assert Phase("a", 30).human() == "30s"
    assert Phase("a", 600).human() == "10min"
    assert Phase("a", 7200).human() == "2.0h"
