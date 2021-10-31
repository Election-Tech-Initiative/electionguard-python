.PHONY: all openssl-fix install install-gmp install-gmp-mac install-gmp-linux install-gmp-windows install-mkdocs auto-lint validate test test-example bench coverage coverage-html coverage-xml coverage-erase generate-sample-data

CODE_COVERAGE ?= 90
OS ?= $(shell python -c 'import platform; print(platform.system())')
ifeq ($(OS), Linux)
PKG_MGR ?= $(shell python -c 'import subprocess as sub; print(next(filter(None, (sub.getstatusoutput(f"command -v {pm}")[0] == 0 and pm for pm in ["apt-get", "pacman"])), "undefined"))')
endif
IS_64_BIT ?= $(shell python -c 'from sys import maxsize; print(maxsize > 2**32)')
SAMPLE_BALLOT_COUNT ?= 5
SAMPLE_BALLOT_SPOIL_RATE ?= 50

all: environment install build validate auto-lint coverage

environment:
	@echo 🔧 ENVIRONMENT SETUP
	make install-gmp
	python -m pip install -U pip
	pip3 install 'poetry==1.1.10'
	poetry config virtualenvs.in-project true 
	poetry install
	@echo 🚨 Be sure to add poetry to PATH

install:
	@echo 🔧 INSTALL
	poetry install

build:
	@echo 🔨 BUILD
	poetry build
	poetry install 

openssl-fix:
	export LDFLAGS=-L/usr/local/opt/openssl/lib
	export CPPFLAGS=-I/usr/local/opt/openssl/include 

install-gmp:
	@echo 📦 Install gmp
	@echo Operating System identified as $(OS)
ifeq ($(OS), Linux)
	make install-gmp-linux
endif
ifeq ($(OS), Darwin)
	make install-gmp-mac
endif
ifeq ($(OS), Windows)
	make install-gmp-windows
endif
ifeq ($(OS), Windows_NT)
	make install-gmp-windows
endif

install-gmp-mac:
	@echo 🍎 MACOS INSTALL
	brew install gmp || true
	brew install mpfr || true
	brew install libmpc || true

install-gmp-linux:
	@echo 🐧 LINUX INSTALL
ifeq ($(PKG_MGR), apt-get)
	sudo apt-get install libgmp-dev
	sudo apt-get install libmpfr-dev
	sudo apt-get install libmpc-dev
else ifeq ($(PKG_MGR), pacman)
	sudo pacman -S gmp
else ifeq ($(PKG_MGR), undefined)
	@echo "We could not install GMP automatically for your Linux distribution. Please, install GMP manually."
endif

install-gmp-windows:
	@echo 🏁 WINDOWS INSTALL
	@echo 🚨 Ensure pyproject.toml has been modified to include appropriate local gmpy2 package 🚨 
# install module with local gmpy2 package
ifeq ($(IS_64_BIT), True)
	@echo 64 bit system detected
endif
ifeq ($(IS_64_BIT), False)
	@echo 32 bit system detected
endif

lint:
	@echo 💚 LINT
	@echo 1.Pylint
	poetry run pylint ./src/**/*.py ./tests/**/*.py
	@echo 2.Black Formatting
	poetry run black --check .
	@echo 3.Mypy Static Typing
	poetry run mypy src/electionguard stubs
	@echo 4.Package Metadata
	poetry build
	poetry run twine check dist/*
	@echo 5.Documentation
	poetry run mkdocs build --strict

auto-lint:
	@echo 💚 AUTO LINT
	@echo Auto-generating __init__
	poetry run mkinit src/electionguard --write --black
	poetry run mkinit src/electionguard_tools --write --recursive --black
	poetry run mkinit src/electionguard_verify --write --black
	@echo Reformatting using Black
	poetry run black .
	make lint
	
validate: 
	@echo ✅ VALIDATE
	@poetry run python -c 'import electionguard; print(electionguard.__package__ + " successfully imported")'

# Test
unit-tests:
	@echo ✅ UNIT TESTS
	poetry run pytest tests/unit

property-tests:
	@echo ✅ PROPERTY TESTS
	poetry run pytest tests/property

integration-tests:
	@echo ✅ INTEGRATION TESTS
	poetry run pytest tests/integration

test: 
	@echo ✅ ALL TESTS
	make unit-tests
	make property-tests
	make integration-tests

test-example:
	@echo ✅ TEST Example
	poetry run python3 -m pytest -s tests/integration/test_end_to_end_election.py

test-integration:
	@echo ✅ INTEGRATION TESTS
	poetry run pytest tests/integration

# Coverage
coverage:
	@echo ✅ COVERAGE
	poetry run coverage run -m pytest
	poetry run coverage report --fail-under=$(CODE_COVERAGE)

coverage-html:
	poetry run coverage html -d coverage

coverage-xml:
	poetry run coverage xml

coverage-erase:
	@poetry run coverage erase

# Benchmark
bench:
	@echo 📊 BENCHMARKS
	poetry run python3 -s tests/bench/bench_chaum_pedersen.py

# Documentation
install-mkdocs:
	pip install mkdocs
	pip install mkdocs-jupyter

docs-serve:
	poetry run mkdocs serve

docs-build:
	poetry run mkdocs build

docs-deploy:
	@echo 🚀 DEPLOY to Github Pages
	poetry run mkdocs gh-deploy --force

docs-deploy-ci:
	@echo 🚀 DEPLOY to Github Pages
	poetry run mkdocs gh-deploy --force

dependency-graph:
	poetry run pydeps --noshow --max-bacon 2 -o dependency-graph.svg src/electionguard

dependency-graph-ci:
	sudo apt install graphviz
	poetry run pydeps --noshow --max-bacon 2 -o dependency-graph.svg src/electionguard

# Sample Data
generate-sample-data:
	poetry run python3 src/electionguard_tools/scripts/sample_generator.py -n $(SAMPLE_BALLOT_COUNT) -s $(SAMPLE_BALLOT_SPOIL_RATE)

# Publish
publish:
	poetry publish

publish-ci:
	@echo 🚀 PUBLISH
	poetry publish --username __token__ --password $(PYPI_TOKEN)

publish-test:
	poetry publish --repository testpypi

publish-test-ci:
	@echo 🚀 PUBLISH TEST
	poetry publish --repository testpypi --username __token__ --password $(TEST_PYPI_TOKEN)

publish-validate:	
	@echo ✅ VALIDATE
	python3 -m pip install --no-deps electionguard
	python3 -c 'import electionguard'

publish-validate-test:	
	@echo ✅ VALIDATE
	python3 -m pip install --index-url https://test.pypi.org/simple/ --no-deps electionguard
	python3 -c 'import electionguard'

# Release
release-zip-ci:
	@echo 📁 ZIP RELEASE ARTIFACTS
	mv dist electionguard
	mv dependency-graph.svg electionguard
	zip -r electionguard.zip electionguard

release-notes:
	@echo 📝 GENERATE RELEASE NOTES
	export MILESTONE_NUM=$(cat $GITHUB_EVENT_PATH | jq '.milestone.number')
	export MILESTONE_URL=$(cat $GITHUB_EVENT_PATH | jq '.milestone.url')
	export MILESTONE_TITLE=$(cat $GITHUB_EVENT_PATH | jq '.milestone.title')
	export MILESTONE_DESCRIPTION=$(cat $GITHUB_EVENT_PATH | jq '.milestone.description')
	touch release_notes.md
	echo "# $MILESTONE_TITLE" >> release_notes.md
	echo "$MILESTONE_DESCRIPTION" >> release_notes.md
	echo -en "\n" >> release_notes.md
	echo "## Issues" >> release_notes.md
	curl "${GITHUB_API_URL}/${GITHUB_REPOSITORY}/issues?milestone=${MILESTONE_NUM}&state=all" | jq '.[].title' | while read i; do echo "[$i]($MILESTONE_URL)" >> release_notes.md; done
