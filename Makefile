VENV = .venv
PYTHON = $(VENV)/bin/python
PIP = $(VENV)/bin/pip
ARGS ?=

.PHONY: install run

install:
	python3 -m venv $(VENV)
	$(PIP) install -r requirements.txt

run:
	$(PYTHON) main.py $(ARGS)

