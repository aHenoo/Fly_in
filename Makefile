PYTHON := python3
VENV := .venv
VENV_PYTHON := $(VENV)/bin/python
FLAKE8 := $(VENV)/bin/flake8
MYPY := $(VENV)/bin/mypy
MAP := maps/easy/01_linear_path.txt
VISUAL :=

.PHONY: install run debug clean lint lint-strict fclean

install:
	$(PYTHON) -m venv $(VENV)
	$(VENV_PYTHON) -m pip install --upgrade pip
	$(VENV_PYTHON) -m pip install -e ".[dev]"

run:
	$(PYTHON) main.py $(MAP) $(VISUAL)

debug:
	$(PYTHON) -m pdb main.py $(MAP) $(VISUAL)

clean:
	find . -type d -name "__pycache__" -prune -exec rm -rf {} +
	find . -type d -name ".mypy_cache" -prune -exec rm -rf {} +
	find . -type d -name ".pytest_cache" -prune -exec rm -rf {} +
	find . -type d -name "*.egg-info" -prune -exec rm -rf {} +
	find . -type f -name "uv.lock" -delete

fclean:
	find . -type d -name "__pycache__" -prune -exec rm -rf {} +
	find . -type d -name ".mypy_cache" -prune -exec rm -rf {} +
	find . -type d -name ".pytest_cache" -prune -exec rm -rf {} +
	find . -type d -name "*.egg-info" -prune -exec rm -rf {} +
	rm -rf .venv venv
	find . -type f -name "uv.lock" -delete

lint:
	$(FLAKE8) .
	$(MYPY) . --warn-return-any --warn-unused-ignores --ignore-missing-imports --disallow-untyped-defs --check-untyped-defs

lint-strict:
	$(FLAKE8) .
	$(MYPY) . --strict
