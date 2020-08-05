.PHONY: all bench environment install install-mac install-linux install-windows lint validate test test-example coverage coverage-html coverage-xml coverage-erase generate-sample-data

CODE_COVERAGE ?= 90
WINDOWS_32BIT_GMPY2 ?= packages/gmpy2-2.0.8-cp38-cp38-win32.whl
WINDOWS_64BIT_GMPY2 ?= packages/gmpy2-2.0.8-cp38-cp38-win_amd64.whl
OS ?= $(shell python -c 'import platform; print(platform.system())')
IS_64_BIT ?= $(shell python -c 'from sys import maxsize; print(maxsize > 2**32)')

all: environment install validate lint coverage

bench:
	@echo 📊 BENCHMARKS
	pipenv run python -s bench/bench_chaum_pedersen.py

environment:
	@echo 🔧 PIPENV SETUP
	pip install pipenv
	pipenv install --dev

install:
	@echo 📦 Install Module
	@echo Operating System identified as $(OS)
ifeq ($(OS), Linux)
	make install-linux
endif
ifeq ($(OS), Darwin)
	make install-mac
endif
ifeq ($(OS), Windows)
	make install-windows
endif
ifeq ($(OS), Windows_NT)
	make install-windows
endif

install-mac:
	@echo 🍎 MACOS INSTALL
# gmpy2 requirements
	brew install gmp || true
# install module
	pipenv run python -m pip install -e .

install-linux:
	@echo 🐧 LINUX INSTALL
# gmpy2 requirements
	sudo apt-get install libgmp-dev
	sudo apt-get install libmpfr-dev
	sudo apt-get install libmpc-dev
# install module
	pipenv run python -m pip install -e .

install-windows:
	@echo 🏁 WINDOWS INSTALL
# install module with local gmpy2 package
ifeq ($(IS_64_BIT), True)
	pipenv run python -m pip install -f $(WINDOWS_64BIT_GMPY2) -e . 
endif
ifeq ($(IS_64_BIT), False)
	pipenv run python -m pip install -f $(WINDOWS_32BIT_GMPY2) -e . 
endif
	

lint:
	@echo 💚 LINT
	@echo 1.Pylint
	pipenv run pylint ./src/**/*.py ./tests/**/*.py ./bench/**/*.py
	@echo 2.Black Formatting
	pipenv run black --check .
	@echo 3.Mypy Static Typing
	pipenv run mypy bench src stubs tests setup.py
	@echo 4.Package Metadata
	pipenv run python setup.py --quiet sdist bdist_wheel
	pipenv run twine check dist/*
	@echo 5.Docstring
	pipenv run pydocstyle
	@echo 6.Documentation
	pipenv run mkdocs build --strict

validate: 
	@echo ✅ VALIDATE
	@pipenv run python -c 'import electionguard; print(electionguard.__package__ + " successfully imported")'

# Test
test: 
	@echo ✅ TEST
	pipenv run pytest . -x

test-example:
	@echo ✅ TEST Example
	pipenv run python -m pytest -s tests/integration/test_end_to_end_election.py

test-integration:
	@echo ✅ INTEGRATION TESTS
	pipenv run pytest tests/integration

# Coverage
coverage:
	@echo ✅ COVERAGE
	pipenv run coverage run -m pytest
	pipenv run coverage report --fail-under=$(CODE_COVERAGE)

coverage-html:
	pipenv run coverage html -d coverage

coverage-xml:
	pipenv run coverage xml

coverage-erase:
	@pipenv run coverage erase

# Documentation
docs-serve:
	pipenv run mkdocs serve

docs-build:
	pipenv run mkdocs build

docs-deploy:
	@echo 🚀 DEPLOY to Github Pages
	pipenv run mkdocs gh-deploy --force

dependency-graph:
	pipenv run pydeps --max-bacon 2 -o dependency-graph.svg src/electionguard

# Sample Data
generate-sample-data:
	pipenv run python src/electionguardtest/sample_generator.py

# Package
package:
	@echo ⬇️ INSTALL WHEEL
	python -m pip install --user --upgrade setuptools wheel
	@echo 📦 PACKAGE
	python setup.py sdist bdist_wheel

package-upload:
	python3 -m pip install --user --upgrade twine
	python -m twine upload dist/*

package-upload-test:
	python3 -m pip install --user --upgrade twine
	python -m twine upload --repository testpypi dist/*

package-validate:	
	@echo ✅ VALIDATE
	python -m pip install --no-deps electionguard
	python -c 'import electionguard'


package-validate-test:	
	@echo ✅ VALIDATE
	python -m pip install --index-url https://test.pypi.org/simple/ --no-deps electionguard
	python -c 'import electionguard'
