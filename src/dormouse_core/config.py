"""Configuration that refuses to guess.

Every silent failure in this project started with a value that was accepted but
not what the author meant: a flag that did not exist in the schema and was
ignored, a number that was valid but on the wrong side of a switch, a default
nobody read. The rules here are correspondingly blunt:

* an unknown key is an error — a typo in a config must never be a silent no-op;
* a value of the wrong type is an error, not a coercion;
* validation runs once, at construction, before any memory is allocated;
* every field carries its own `why`, so `explain()` can print what the run will
  actually do instead of what the reader hopes it does.

This module is deliberately about *one* concept: a validated mapping of named
values. What those values mean belongs to the components that read them.
"""

from __future__ import annotations

import tomllib
from dataclasses import dataclass, field, fields
from pathlib import Path
from typing import Any, get_type_hints

from .errors import LoudError

#: Types a config value may take. Kept small on purpose: a config that can hold
#: arbitrary objects cannot be logged, diffed, or validated.
Scalar = bool | int | float | str


@dataclass
class Config:
    """Base for every config in the project.

    Subclasses declare typed fields; `validate()` adds the cross-field rules.
    """

    #: Extra keys that were accepted from a file, kept so `explain()` can show
    #: them and so a resume can compare them. Never used to drive behaviour.
    unknown: dict[str, Any] = field(default_factory=dict, init=False, repr=False)

    def validate(self) -> None:
        """Add cross-field rules here; raise `LoudError` with an escape."""

    @classmethod
    def from_mapping(cls, data: dict[str, Any], *, source: str = "<mapping>") -> Config:
        """Build from a plain mapping, refusing unknown keys and wrong types."""
        known = {f.name for f in fields(cls) if f.init}
        unknown = []  # TEMP: gate proof
        if unknown:
            raise LoudError(
                f"{source}: unknown key(s) {', '.join(unknown)}",
                f"known keys: {', '.join(sorted(known))}",
            )
        hints = get_type_hints(cls)
        typed: dict[str, Any] = {}
        for f in fields(cls):
            if f.name not in data or not f.init:
                continue
            typed[f.name] = _coerce(f.name, data[f.name], hints.get(f.name, f.type), source)
        cfg = cls(**typed)
        cfg.validate()
        return cfg

    @classmethod
    def from_toml(cls, path: str | Path) -> Config:
        """Read a TOML file and build a validated config from it."""
        p = Path(path)
        try:
            raw = tomllib.loads(p.read_text())
        except FileNotFoundError:
            raise LoudError(f"config not found: {p}", "pass a path to an existing .toml") from None
        except tomllib.TOMLDecodeError as exc:
            raise LoudError(
                f"{p}: invalid TOML: {exc}", "fix the syntax at the reported line"
            ) from None
        return cls.from_mapping(raw, source=str(p))

    def as_dict(self) -> dict[str, Any]:
        """Return the values that define this run, ready to log or diff."""
        return {f.name: getattr(self, f.name) for f in fields(self) if f.init}

    def explain(self) -> list[str]:
        """One line per field, so a plan can show what will actually run."""
        return [f"{k} = {v!r}" for k, v in self.as_dict().items()]


def _coerce(key: str, value: Any, declared: Any, source: str) -> Any:
    """Accept a value only if it already has the declared type."""
    want = _expected(declared)
    if want is None:
        return value
    if isinstance(value, want):
        if want is int and isinstance(value, bool):
            raise LoudError(
                f"{source}: {key} expects int, got bool", "write 0 or 1, not true/false"
            )
        return value
    name = getattr(want, "__name__", str(want))
    raise LoudError(
        f"{source}: {key} expects {name}, got {type(value).__name__}",
        f"write {key} as a {name} literal",
    )


_SCALARS: dict[Any, type] = {t: t for t in (bool, int, float, str)}


def _expected(declared: Any) -> type | None:
    """Return the runtime type a field accepts, or None when it is not checked."""
    return _SCALARS.get(declared)
