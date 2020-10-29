# Build and Run

These instructions can be used to build and run the project.

## Setup

### 1. Initialize dev environment

```
make environment
```

OR

```
pipenv install --dev
```

### 2. Install the `electionguard` module in edit mode

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

`python -c 'from sys import maxsize; print(maxsize > 2**32)'`

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
