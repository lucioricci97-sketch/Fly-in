PYTHON ?= python3
MAP    ?= maps/easy/01_linear_path.txt
VENV   = .venv
VENV_BIN = $(VENV)/bin

.PHONY: install run debug clean lint lint-strict

# This creates the venv AND installs requirements inside it
install:
	$(PYTHON) -m venv $(VENV)
	$(VENV_BIN)/pip install -r requirements.txt

# Use the venv's python to run the project
run:
	$(VENV_BIN)/python -m src $(MAP)

debug:
	$(VENV_BIN)/python -m pdb -m src $(MAP) --no-visual

clean:
	rm -rf __pycache__ src/__pycache__ .mypy_cache .pytest_cache
	rm -rf $(VENV)

lint:
	$(VENV_BIN)/flake8 src --max-line-length=120
	$(VENV_BIN)/mypy src --warn-return-any --warn-unused-ignores \
		--ignore-missing-imports --disallow-untyped-defs --check-untyped-defs

lint-strict:
	$(VENV_BIN)/flake8 src --max-line-length=120
	$(VENV_BIN)/mypy src --strict