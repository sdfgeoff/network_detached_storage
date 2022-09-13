all: test fmt

test:
	mypy nds_core
	pytest -v

fmt:
	black nds_core

serve:
	python3 -m nds_core.serve
