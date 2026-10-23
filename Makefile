VENV = .venv
PYTHON = $(VENV)/bin/python
PIP = $(VENV)/bin/pip
ARGS ?=
FLAGS = --warn-return-any\
		--warn-unused-ignores\
		--ignore-missing-imports\
		--disallow-untyped-defs\
		--check-untyped-defs

.PHONY: install run debug clean lint lint-strict

install:
	python3 -m venv $(VENV)
	$(PIP) install -r requirements.txt

run:
	$(PYTHON) main.py $(ARGS)

debug:
	$(PYTHON) -m pdb main.py $(ARGS)

clean:
	find . | grep "__pycache__" | xargs rm -rf
	find . | grep ".mypy_cache" | xargs rm -rf
	rm -rf $(VENV)

lint:
	$(PYTHON) -m flake8 --docstring-convention numpy --extend-exclude=$(VENV),anothertest.py .
	$(PYTHON) -m mypy --exclude $(VENV) $(FLAGS) .

lint-strict:
	$(PYTHON) -m flake8 --docstring-convention numpy --extend-exclude=$(VENV),anothertest.py .
	$(PYTHON) -m mypy --exclude $(VENV) --strict .

