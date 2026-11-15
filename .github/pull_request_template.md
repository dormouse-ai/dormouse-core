## What and why

One paragraph: what changes and which defect or measurement motivates it.

## Evidence

- [ ] tests cover the claim (name the test)
- [ ] a number is quoted, or this change is a refactor with no behaviour change
- [ ] `ruff check . && ruff format --check . && mypy src` clean
- [ ] no golden hash captured from our own run was added

## Risk

What could break, and how a reader would notice.
