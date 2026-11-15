"""Print the public surface, one name per line, for the api-frozen CI gate.

Deterministic on purpose: the gate compares this output with `api.txt`, so a
public rename or a removed symbol is a red build rather than a silent break for
anyone importing the package.
"""

from __future__ import annotations

import inspect
import pkgutil

import dormouse_core


def main() -> None:
    """Print every public name this package exports, sorted."""
    for info in sorted(pkgutil.iter_modules(dormouse_core.__path__), key=lambda x: x.name):
        module = __import__(f"dormouse_core.{info.name}", fromlist=["*"])
        for name, obj in sorted(vars(module).items()):
            if name.startswith("_") or inspect.getmodule(obj) is not module:
                continue
            print(f"{info.name}.{name}")


if __name__ == "__main__":
    main()
