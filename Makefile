#!make
PJNAME := sms-aichat
PJVER := test
SRC_DIR := $(CURDIR)/src
UNITTEST_DIR := $(CURDIR)/tests/unit/src

ifneq (,$(wildcard .env))
	include .env
    ENV_VARS := $(shell awk 'NF {print}' .env | xargs)
endif

all: clean expt build

init:
	uv sync

expt:
	@echo "Export requirements.txt from uv.lock"
	uv export --frozen --no-install-project --no-dev --format requirements-txt > requirements.txt

lint:
	uvx ruff check 
	uv run mypy $(SRC_DIR) $(UNITTEST_DIR)
	uvx ruff format

fix:
	uvx ruff check --fix

build: expt clean
	docker build --platform linux/amd64 -t $(PJNAME):$(PJVER) .

run:
	docker run --rm --platform linux/amd64 -p 9000:8080 --env-file ./.env $(PJNAME):$(PJVER)

invoke:
	curl "http://localhost:9000/2015-03-31/functions/function/invocations" -d '{"prompt":$(PROMPT)}' --request 'POST'

clean:
	docker rmi $(PJNAME):$(PJVER) || true
	@echo "Clean completed."

test:
	@echo "Running local tests..."
	uv run pytest -o log_cli=true -vv

.PHONY: all init expt lint fix build run invoke clean test
