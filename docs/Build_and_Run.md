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

⚠️ Note: For Windows, use supplied precompiled gmpy2 package. Poetry does not support `pip install --find-links`, so the `pyproject.toml` must be edited.

**Install gmpy2 for Windows**
1. Determine if 64-bit:
    _The 32 vs 64 bit is based on your installed python version NOT your system._
    This code snippet will read true for 64 bit.
     `python -c 'from sys import maxsize; print(maxsize > 2**32)'`
2. Within `pyproject.toml`,
    - Comment the original `gmpy2` line
    - Uncomment the corresponding windows `gmpy2` line


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
