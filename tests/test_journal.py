"""The journal is the run's only source of truth, so it has to survive three things:
a restart, a swap in the middle, and a corrupted line.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from dormouse_core.errors import LoudError
from dormouse_core.journal import Journal


def test_events_are_appended_and_read_back(tmp_path: Path) -> None:
    path = tmp_path / "run.jsonl"
    j = Journal.open(path)
    j.write("start", config="chat275.toml", seed=1)
    j.write("step", step=100, loss=1.9)
    j.write("step", step=200, loss=1.8)
    again = Journal.open(path)
    assert len(again.records) == 3
    last = again.last("step")
    assert last is not None and last["step"] == 200 and last["loss"] == 1.8


def test_unknown_event_is_refused_with_the_known_set() -> None:
    import tempfile

    j = Journal(path=Path(tempfile.mkdtemp()) / "j.jsonl")
    with pytest.raises(LoudError) as e:
        j.write("progress", step=1)
    assert "eval" in str(e.value)


def test_step_must_be_an_integer() -> None:
    import tempfile

    j = Journal(path=Path(tempfile.mkdtemp()) / "j.jsonl")
    with pytest.raises(LoudError):
        j.write("step", step=1.5)


def test_a_swap_is_a_segment_with_a_step(tmp_path: Path) -> None:
    """Hot swap must be recorded where it happened, not between two log files."""
    j = Journal.open(tmp_path / "run.jsonl")
    j.write("start", config="a.toml")
    j.write("step", step=500)
    j.write("swap", step=500, component="attn", took="kda", gave="sdpa")
    assert len(j.segments()) == 1
    assert j.segments()[0]["took"] == "kda"


def test_a_corrupted_line_is_named_not_skipped(tmp_path: Path) -> None:
    path = tmp_path / "run.jsonl"
    path.write_text('{"kind": "start"}\n{not json}\n')
    with pytest.raises(LoudError) as e:
        Journal.open(path)
    assert "line 2" in str(e.value)


def test_summary_reports_the_state(tmp_path: Path) -> None:
    j = Journal.open(tmp_path / "run.jsonl")
    j.write("start", config="c.toml")
    j.write("step", step=42)
    assert j.summary() == "running step=42 config=c.toml segments=0"
    j.write("end", step=42, reason="done")
    assert j.summary().startswith("ended")
