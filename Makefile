# Notes:
#  - Linux/macOS/Git Bash/WSL: works as-is (needs `make`).
#  - Windows PowerShell without make: run the commands shown in each target by hand,
#    e.g. `python -m venv .venv; .venv\Scripts\pip install -r requirements.txt`.
#  - Targets use the venv's executables directly, so activation is not required.

ifeq ($(OS),Windows_NT)
  BIN := .venv/Scripts
else
  BIN := .venv/bin
endif

.PHONY: venv install test mock lint

venv:
	python -m venv .venv

install: venv
	$(BIN)/python -m pip install -r requirements.txt

test:
	$(BIN)/python -m pytest -q

mock:
	$(BIN)/python run.py --mock

# Lint: byte-compile check only (no extra dependency). Swap in ruff/flake8 if the team adopts one.
lint:
	$(BIN)/python -m compileall -q src run.py tests
