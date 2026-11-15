# `make check` is exactly what the CI test job runs. Needs `make install` first.
.PHONY: install check build

install:
	pip install -e '.[dev]'

check:
	ruff check .
	ruff format --check .
	mypy src
	python -m pytest --cov --cov-report=term-missing

build:
	python -m build
