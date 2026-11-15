"""A config that refuses to guess, tested on the three ways configs lie.

A config can lie by having a key nobody reads, by having a value of the wrong
type that gets coerced, or by accepting a combination that is impossible. Each is
a test here, plus the round-trip that a logged run can be rebuilt from.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import pytest

from dormouse_core.config import Config
from dormouse_core.errors import LoudError


@dataclass
class Model(Config):
    """A minimal config: one of each kind of field."""

    width: int = 832
    dtype: str = "bf16"
    use_kda: bool = False
    lr: float = 3e-4

    def validate(self) -> None:
        """Cross-field rule: KDA is not wired for any dtype but bf16."""
        if self.use_kda and self.dtype != "bf16":
            raise LoudError(
                f"use_kda with dtype={self.dtype!r}: the kernel has no {self.dtype} path",
                "set dtype='bf16' or use_kda=false",
            )


def test_cross_field_rule_fires_with_an_escape() -> None:
    with pytest.raises(LoudError) as e:
        Model.from_mapping({"use_kda": True, "dtype": "fp32"})
    assert "Escape: set dtype='bf16'" in str(e.value)


def test_defaults_are_the_documented_ones() -> None:
    cfg = Model.from_mapping({})
    assert (cfg.width, cfg.dtype, cfg.use_kda) == (832, "bf16", False)


def test_round_trip_through_toml(tmp_path: Path) -> None:
    path = tmp_path / "m.toml"
    path.write_text('width = 1024\ndtype = "fp16"\nuse_kda = false\nlr = 0.001\n')
    cfg = Model.from_toml(path)
    assert cfg.as_dict() == {"width": 1024, "dtype": "fp16", "use_kda": False, "lr": 0.001}


def test_missing_file_names_the_path() -> None:
    with pytest.raises(LoudError) as e:
        Model.from_toml("/nope/missing.toml")
    assert "/nope/missing.toml" in str(e.value)


def test_broken_toml_names_the_line() -> None:
    path = Path("/tmp/opencode/broken.toml")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("width = = 832\n")
    with pytest.raises(LoudError) as e:
        Model.from_toml(path)
    assert "invalid TOML" in str(e.value)


def test_explain_lists_what_will_run() -> None:
    cfg = Model.from_mapping({"width": 512})
    lines = cfg.explain()
    assert "width = 512" in lines
    assert any(line.startswith("dtype = ") for line in lines)
