"""The config invariants: an unknown key and a wrong type are errors, not no-ops.

Every silent failure here started with a value that was accepted but not what the
author meant. These two tests are the floor under that: a typo must be named, and
`"832"` must not become `832`.
"""

from __future__ import annotations

from dataclasses import dataclass

import pytest

from dormouse_core.config import Config
from dormouse_core.errors import LoudError


@dataclass
class _Arm(Config):
    """The smallest config that can lie: one integer and one flag."""

    width: int = 8
    use_kda: bool = False


def test_an_unknown_key_is_an_error_not_a_no_op() -> None:
    with pytest.raises(LoudError) as e:
        _Arm.from_mapping({"width": 832, "use_kdaa": True})
    assert "use_kdaa" in str(e.value)
    assert "known keys" in str(e.value)


def test_a_wrong_type_is_refused_not_coerced() -> None:
    with pytest.raises(LoudError) as e:
        _Arm.from_mapping({"width": "832"})
    assert "expects int" in str(e.value)


def test_a_bool_is_not_an_int() -> None:
    """`width=true` passes an isinstance check on int without this guard."""
    with pytest.raises(LoudError) as e:
        _Arm.from_mapping({"width": True})
    assert "expects int, got bool" in str(e.value)
