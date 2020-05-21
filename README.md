---
page_type: sample
languages:
  - python
description: "ElectionGuard: Support for e2e verified elections."
urlFragment: "https://github.com/microsoft/electionguard-python"
---

# ElectionGuard-Python

<!--
Guidelines on README format: https://review.docs.microsoft.com/help/onboard/admin/samples/concepts/readme-template?branch=master

Guidance on onboarding samples to docs.microsoft.com/samples: https://review.docs.microsoft.com/help/onboard/admin/samples/process/onboarding?branch=master

Taxonomies for products and languages: https://review.docs.microsoft.com/new-hope/information-architecture/metadata/taxonomies?branch=master
-->

This repository is a "reference implementation" of ElectionGuard written in Python3. This includes
both a "verifier" application, useful for validating the results of an ElectionGuard election, as
well as a standalone Python library, suitable for building other applications.

## Contents

Outline the file contents of the repository. It helps users navigate the codebase, build configuration and any related assets.

| File/folder         | Description                              |
| ------------------- | ---------------------------------------- |
| `bench`             | Microbenchmarks based on this codebase   |
| `src/electionguard` | Source code to the ElectionGuard library |
| `stubs`             | Type annotations for external libraries  |
| `tests`             | Unit tests to exercise this codebase     |
| `CONTRIBUTING.md`   | Guidelines for contributing              |
| `README.md`         | This README file                         |
| `LICENSE`           | The license for ElectionGuard-Python.    |

## Prerequisites

### Python 3.8+

This code was developed against Python3.8, and is unlikely to work against earlier versions. [Download Python](https://www.python.org/downloads/).

### make (Recommended)

**make** is used to simplify the commands and GitHub Actions. This approach is recommended to simplify the command line experience. This is built in for MacOS and Linux. For Windows, setup is simpler with [Chocolatey](https://chocolatey.org/install) and installing the provided [make package](https://chocolatey.org/packages/make). The other Windows option is [manually installing make](http://gnuwin32.sourceforge.net/packages/make.htm).

### gmpy2 Requirements

To make the math go faster, we're using [Gmpy2](https://gmpy2.readthedocs.io/en/latest/), which
has its own [installation requirements (native C libraries)](https://gmpy2.readthedocs.io/en/latest/intro.html#installation).

**⚠️ Note:** _This is not required for Windows since the gmpy2 precompiled libraries are provided._

### pipenv

[pipenv](https://github.com/pypa/pipenv) is used to configure the environment. Installation instructions can be found [here](https://github.com/pypa/pipenv#installation).

## Quick Start

Using **make**, the entire Github Action workflow can be run with one command: `make`

## Setup

### 1. Initialize dev environment

```
make environment
```

OR

```
pipenv install --dev
```

### 2. Install `electionguard` module in edit mode

```
make install
```

OR

```
pipenv run python -m pip install -e .
```

**⚠️ Note:** _For Windows without `make`, use supplied precompiled **gmpy2** package with the `--find-links` or `-f` option. The 32 vs 64 bit is based on your installed python version NOT your system._

_**Determine if 64-bit:**_

_This code snippet will read `true` for 64 bit._

`python -c 'from sys import maxsize; print(maxsize > 2**32)`

_**Install module with link**_

- **32-bit:** `pipenv run pip install -f packages/gmpy2-2.0.8-cp38-cp38-win32.whl -e .`
- **64-bit:** `pipenv run pip install -f packages/gmpy2-2.0.8-cp38-cp38-win_amd64 -e .`

### 3. Validate import of module _(Optional)_

```
make validate
```

OR

```
pipenv run python -c 'import electionguard; print(electionguard.__package__ + " successfully imported")'
```

## Running

### Option 1: Code Coverage

```
make coverage
```

OR

```
pipenv run coverage report
```

### Option 2: Run tests in VS Code

Install recommended test explorer extensions and run unit tests through tool.

**⚠️ Note:** For Windows, be sure to select the [virtual environment Python interpreter](https://docs.microsoft.com/en-us/visualstudio/python/installing-python-interpreters).

### Option 3: Run test command

```
make test
```

OR

```
pipenv run python -m pytest /testss
```

## Documentation

- [Design and Architecture](docs/Design_and_Architecture.md)
