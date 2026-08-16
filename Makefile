.PHONY: check test lint type ingest

# The only verification command. Bounded output, one summary line per gate.
check: lint type test

lint:
	ruff check src/ tests/ --quiet

type:
	mypy src/kinetiek --no-error-summary

test:
	python -m pytest tests/ urban/tests/ -q --tb=line

ingest:
	@echo "Run ingest modules individually: python -m kinetiek.ingest.<name>"
