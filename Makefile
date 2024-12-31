PJNAME := sms-aichat
PJVER := test

Objects = *.py

all: clean expt build

init:
	uv sync

expt:
	@echo "Export requirements.txt from uv.lock"
	uv export --frozen --no-install-project --no-dev --format requirements-txt > requirements.txt

lint:
	uvx ruff format $(Objects)
	uvx ruff check $(Objects)
	uvx mypy --python-executable ./.venv/bin/python $(Objects)

fix:
	uvx ruff check --fix

build: expt clean
	docker build --platform linux/amd64 -t $(PJNAME):$(PJVER) .

run:
	docker run --rm --platform linux/amd64 -p 9000:8080 $(PJNAME):$(PJVER)

clean:
	docker rmi $(PJNAME):$(PJVER)
	@echo "Clean completed."

test:
	@echo "Running local tests..."
	curl "http://localhost:9000/2015-03-31/functions/function/invocations" -d '{}' --request 'POST'

.PHONY: all init expt lint fix build run clean test
