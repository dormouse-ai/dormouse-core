"""Structural rules, enforced as tests instead of review comments.

Two rules that cost us real time when they were broken:

* one module, one concept — a file that exports two unrelated public names is a
  file where one of them will drift out of sync with its docstring;
* a module that grows past a few hundred lines is usually two modules wearing one
  name.

The second is a warning-shaped check: it fails only above a hard ceiling, and
prints the offenders above the soft one. Triton kernels are exempt — a single
kernel can legitimately be long.
"""

from __future__ import annotations

import ast
from pathlib import Path

SRC = Path(__file__).resolve().parents[1] / "src"
SOFT = 250
HARD = 400
EXEMPT = {"counters.py"}  # one concept, but the docstring is the point of the file


def _modules() -> list[Path]:
    return sorted(p for p in SRC.rglob("*.py") if p.name != "__init__.py")


def _public_classes(path: Path) -> list[str]:
    tree = ast.parse(path.read_text())
    return [
        n.name
        for n in tree.body
        if isinstance(n, ast.ClassDef) and not n.name.startswith("_") and not _is_exception(n)
    ]


def _declared_concepts(path: Path) -> set[str]:
    tree = ast.parse(path.read_text())
    for node in tree.body:
        if isinstance(node, ast.Assign) and getattr(node.targets[0], "id", "") == "__concepts__":
            return {elt.value for elt in node.value.elts}  # type: ignore[attr-defined]
    return set()


def test_no_module_is_longer_than_the_hard_ceiling() -> None:
    offenders = {
        str(p.relative_to(SRC)): len(p.read_text().splitlines())
        for p in _modules()
        if p.name not in EXEMPT and len(p.read_text().splitlines()) > HARD
    }
    assert not offenders, f"modules over {HARD} lines: {offenders}"


def test_long_modules_are_named_even_below_the_ceiling(capsys) -> None:
    """Soft ceiling: reported, not failed. A signal for the next edit."""
    long = {
        str(p.relative_to(SRC)): len(p.read_text().splitlines())
        for p in _modules()
        if SOFT < len(p.read_text().splitlines()) <= HARD
    }
    if long:
        print(f"soft ceiling ({SOFT}) exceeded by: {long}")


def _is_exception(node: ast.ClassDef) -> bool:
    """An exception is part of a concept's contract, not a second concept."""
    if node.name.endswith("Error") or node.name.endswith("Exception"):
        return True
    for base in node.bases:
        name = base.id if isinstance(base, ast.Name) else getattr(base, "attr", "")
        if name.endswith("Error") or name.endswith("Exception"):
            return True
    return False


def test_each_module_has_exactly_one_primary_public_class() -> None:
    """One concept per file, where an exception does not count as a second one.

    `component.py` may carry the protocol and its error; what it may not do is
    house two unrelated concepts that will drift apart. The error hierarchy itself
    is one concept and lives in `errors.py`.
    """
    offenders: dict[str, list[str]] = {}
    for path in _modules():
        if path.name == "errors.py":
            continue
        # A module may declare its public concepts explicitly. `Phase` inside
        # `plan.py` is a member of the plan concept, not a rival to it.
        declared = _declared_concepts(path)
        classes = [c for c in _public_classes(path) if c not in declared]
        if len(classes) > 1:
            offenders[str(path.relative_to(SRC))] = classes
        continue
        classes = _public_classes(path)
        if len(classes) > 1:
            offenders[str(path.relative_to(SRC))] = classes
    assert not offenders, f"modules with more than one public class: {offenders}"


def test_every_public_module_has_a_docstring() -> None:
    missing = []
    for path in _modules():
        tree = ast.parse(path.read_text())
        if not ast.get_docstring(tree):
            missing.append(str(path.relative_to(SRC)))
    assert not missing, f"modules without a docstring: {missing}"


def test_no_public_function_is_undocumented() -> None:
    missing = []
    for path in _modules():
        tree = ast.parse(path.read_text())
        for node in tree.body:
            public = isinstance(node, ast.FunctionDef) and not node.name.startswith("_")
            if public and not ast.get_docstring(node):
                missing.append(f"{path.relative_to(SRC)}:{node.name}")
    assert not missing, f"public functions without a docstring: {missing}"


def test_total_source_stays_inside_the_budget() -> None:
    """A budget, not a wish: this package earns its place by staying small.

    The ceiling is deliberately tight. When it is reached the answer is to delete
    or move code, not to raise the number — the whole point of a separate package
    is that it stays readable in one sitting.
    """
    total = sum(len(p.read_text().splitlines()) for p in _modules())
    assert total <= 900, f"core is {total} lines, budget is 900; delete or move, do not raise"
