INPUT_FILE=
	
.PHONY: all process

#all: poetry install-dev fmt lint run

all: examples

process:
	@basename="$(shell basename "$(INPUT_FILE)" .json)" && \
	poetry run python3 -m botcpdf.main "$(INPUT_FILE)"

clean:
	@find . -type f \( -iname "*.pdf" -o -iname "*.html" \) -exec rm -vf {} \;

POETRY=poetry
POETRY_OK:=$(shell command -v $(POETRY) 2> /dev/null)
PYSRC=botcpdf

poetry:
ifndef POETRY_OK
	python3 -m pip install poetry
endif

install-dev: poetry
	$(POETRY) config virtualenvs.in-project true
	$(POETRY) install

fmt: install-dev
	$(POETRY) run black -t py311 $(PYSRC)

lint: install-dev
	$(POETRY) run pylint $(PYSRC)

run: poetry 
	@$(MAKE) process INPUT_FILE="scripts/Trouble Brewing.json"

examples: install-dev
	@find scripts -type f -exec $(MAKE) process INPUT_FILE="{}" \;

optimise-pdf: install-dev
	@find pdfs -type f -not -name "*.opt.pdf" -exec $(POETRY) run python3 -m botcpdf.optimise_pdf "{}" \;