.PHONY: install test lint format simulate clean

install:
	pip install -e '.[dev]'

test:
	pytest

lint:
	ruff check src tests

format:
	ruff format src tests

simulate:
	quotalane simulate examples/paragraph_summary_large_job.yaml --reset

clean:
	rm -rf .pytest_cache .ruff_cache build dist *.egg-info .quotalane
