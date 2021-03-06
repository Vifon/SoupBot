PY_SOURCES = $(wildcard irc/*.py irc/plugins/*.py)
PY_TEST_SOURCES = test_server.py $(wildcard lib/*.py lib/test/*.py)

.PHONY: all
all: test

.PHONY: help
help:
	@ echo "  Available targets:"
	@ echo "    make test"
	@ echo "    make coverage"
	@ echo "    make coverage-html"

.PHONY: test
test: pylint flake8 typing
	./test.sh

.PHONY: test-verbose
test-verbose: pylint flake8 typing
	./test.sh -v

.PHONY: clean
clean:
	rm -f .coverage
	rm -rf htmlcov .mypy_cache mypy-coverage
	find */ -name __pycache__ -exec rm -rf '{}' +


# Yet to be enabled.
.PHONY: pylint
pylint:

.PHONY: flake8
flake8:
	flake8 irc

.PHONY: typing
typing:
	mypy --pretty -p irc

.PHONY: coverage-typing
coverage-typing: mypy-coverage/index.html
	xdg-open file://$(PWD)/$< || true

mypy-coverage/index.html: $(PY_SOURCES)
	mypy --pretty -p irc --html-report mypy-coverage


.PHONY: coverage
coverage: .coverage
	coverage report

.coverage: $(PY_SOURCES) $(PY_TEST_SOURCES)
	./test.sh -c

.PHONY: coverage-html
coverage-html: htmlcov/index.html
	xdg-open file://$(PWD)/$< || true

htmlcov/index.html: .coverage
	coverage html
