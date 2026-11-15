# `make check` is exactly what the CI test job runs. Needs `make install` first.
.PHONY: install check build

install:
	uv sync --frozen --extra dev

check:
	uv run --no-sync ruff check .
	uv run --no-sync ruff format --check .
	uv run --no-sync mypy src
	uv run --no-sync python -m pytest --cov --cov-report=term-missing

build:
	uv run --no-sync python -m build
