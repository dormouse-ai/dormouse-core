# dormouse-core

The discipline layer: counters that make a silent mechanism a hard error,
coeffects that refuse an incompatible component before it allocates, reversible
effects that restore the context bit-for-bit, and errors that always name the way
out. No dependencies beyond the standard library.

## Why this package exists

Nine times in this project a mechanism was enabled, the run trained, and the
mechanism never executed — a KDA arm with 3126 forwards and zero backwards, a
config where `use_kda=false` meant "no attention at all", an initialisation at
the wrong corner of the simplex. None was visible in the logs and none was caught
by the ~3000 tests we had, because those tests compared the code with itself.

This package makes that class of failure impossible by construction:

* `Counters.enable(name, counter=...)` binds a mechanism to the counter that
  proves it ran; `check()` raises `MissingReport` listing every silent one.
* `Coeffects` declares what a component needs and provides; the slot refuses an
  incompatible component before it mutates anything.
* `Effect` carries its own inverse; `Slot.deactivate` reverses them in order, and
  a property test asserts the context is restored exactly.

## Tests

```bash
python -m venv .venv && .venv/bin/pip install -e '.[dev]'
.venv/bin/python -m pytest
.venv/bin/ruff check . && .venv/bin/mypy src
```

The tests are properties and invariants, not recorded outputs: no golden hashes
captured from our own runs — those prove the code equals itself.
