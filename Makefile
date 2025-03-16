.PHONY: install run test build

install:
    poetry install

run:
    poetry run python src/main.py

test:
    poetry run pytest

build:
    poetry build