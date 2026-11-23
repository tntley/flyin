VENV = .venv
PYTHON = uv run python3
PIP = $(VENV)/bin/pip
ARGS ?=
FLAGS = --warn-return-any\
		--warn-unused-ignores\
		--ignore-missing-imports\
		--disallow-untyped-defs\
		--check-untyped-defs

.PHONY: install run debug clean lint lint-strict

install:
	uv venv -p 3.13.1 --clear
	uv pip install --requirements requirements.txt

run:
	@$(PYTHON) main.py $(ARGS) > log.txt

debug:
	$(PYTHON) -m pdb main.py $(ARGS)

clean:
	find . | grep "__pycache__" | xargs rm -rf
	find . | grep ".mypy_cache" | xargs rm -rf
	rm -rf $(VENV)
	rm -f log.txt

lint:
	$(PYTHON) -m flake8 --docstring-convention numpy --extend-exclude=$(VENV) .
	$(PYTHON) -m mypy --exclude $(VENV) $(FLAGS) .

lint-strict:
	$(PYTHON) -m flake8 --docstring-convention numpy --extend-exclude=$(VENV) .
	$(PYTHON) -m mypy --exclude $(VENV) $(FLAGS) --strict .

