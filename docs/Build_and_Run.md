# Build and Run

These instructions can be used to build and run the project.

## Setup

### 1. Initialize dev environment

```
make environment
```

OR

```
poetry install --dev
```

### 2. Install the `electionguard` module in edit mode

```
make install
```

OR

```
poetry run python -m pip install -e .
```

!!! warning "Note: gmpy2 Windows Installation"

    **Recommended: Use Windows Subsystem for Linux (WSL)**

    _WSL supports the generic workflow for installtion._

    1. Install [WSL](https://docs.microsoft.com/en-us/windows/wsl/install). 
    2. Return to **1. Initialize dev environment**

    **Alternative: Install pre-compiled binary**

    _Poetry does not support `pip install --find-links`, so the `pyproject.toml` must be edited and utilize a local pre-compiled binary of the gmpy2 package._

    1. Determine if 64-bit:
        _The 32 vs 64 bit is based on your installed python version NOT your system._
        This code snippet will read true for 64 bit.
    ```py
    python -c 'from sys import maxsize; print(maxsize > 2**32)'
    ```
    2. Download [pre-compiled binary](https://www.lfd.uci.edu/~gohlke/pythonlibs/#gmpy) into project folder
    3. Within `pyproject.toml`, replace `gmpy2` reference with direct path to downloaded file.
    ```py
    gmpy2 = { path = "./packages/gmpy2-2.0.8-cp39-cp39-win_amd64.whl" }
    ```
    3. Run `make install`


### 3. Validate import of module _(Optional)_

```
make validate
```

OR

```
poetry run python -c 'import electionguard; print(electionguard.__package__ + " successfully imported")'
```

## Running

### Option 1: Code Coverage

```
make coverage
```

OR

```
poetry run coverage report
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
poetry run python -m pytest /tests
```
