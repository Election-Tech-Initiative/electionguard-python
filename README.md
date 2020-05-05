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

### gmpy2 Requirements

To make the math go faster, we're using [Gmpy2](https://gmpy2.readthedocs.io/en/latest/), which
has its own [installation requirements (native C libraries)](https://gmpy2.readthedocs.io/en/latest/intro.html#installation).

### pipenv

[pipenv](https://github.com/pypa/pipenv) is used to configure the environment. Installation instructions can be found [here](https://github.com/pypa/pipenv#installation).

## Setup

**1. Initialize dev environment**

```
pipenv install --dev
```

**2. Install `electionguard` module in edit mode**

```
pipenv run python -m pip install -e .
```

### Windows

Use supplied precompiled **gmpy2** package with the `--find-links` or `-f` option. 

**32-bit:** 
```
pipenv run pip install -f packages/gmpy2-2.0.8-cp38-cp38-win32.whl -e .
```

**64-bit:** 
```
pipenv run pip install -f packages/gmpy2-2.0.8-cp38-cp38-win_amd64 -e .
```

## Running

### Option 1: Run test command

```
pipenv run python -m pytest /tests
```

### Option 2: Run tests in VS Code

Install recommended test explorer extensions and run unit tests through tool.

**Windows:** Be sure to select the [virtual environment Python interpreter](https://docs.microsoft.com/en-us/visualstudio/python/installing-python-interpreters). 

### Option 3: Run tox

This project is configured to use [tox](https://tox.readthedocs.io/en/latest/) to run its unit tests.


## Key concepts

🚧Under Construction
