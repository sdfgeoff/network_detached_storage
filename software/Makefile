all: test fmt lint

test:
	mypy nds_core
	pytest -v

fmt:
	black nds_core

lint:
	flake8

serve:
	python3 -m nds_core.serve
