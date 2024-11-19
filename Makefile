format-ruff-check:
	uv run --all-extras ruff format --check .

format-ruff:
	uv run --all-extras ruff format .

check-ruff:
	uv run --all-extras ruff check .

check-ruff-fix:
	uv run --all-extras ruff check --fix .

check-mypy:
	uv run --all-extras mypy pathvein

check: format-ruff-check check-ruff check-mypy

format: format-ruff

fix: check-ruff-fix

install:
	uv sync

build:
	uv build

test:
	uv run --all-extras pytest 

commit:
	uv run cz commit

publish:

