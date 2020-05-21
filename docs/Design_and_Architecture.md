# Design & Architecture

This describes the design and architecture of the `electionguard-python` project.

## Design

### ✅ Simplicity

Simplicity is the first and foremost goal of the code. The ideal is to be able to **easily transliterate the code to any other programming language** having nothing more than structures and functions. This simplicity applies all aspects of the code design including the naming.

### ✅ Extendable and Interpretable

The library is meant to be a general-purpose to support different variants of the "end to end" encrypted voting systems. Different projects will wish to use different layers of the library including math primitives, encryption functions, etc.

### ✅ Object Oriented Design (OOD) & Functional Methods

The general goal is to build a familiar object oriented design with an underlying functional style methods. This allows for users to work with simple construction of objects in OOP way or directly call the underlying methods in functional way. This design also facilitates easy testing and composition.

Class methods are being used to simplify, but sophistication, in regards to inheritance, object encapsulation, or design patterns, is being intentionally avoided. These class methods usually rely on the aforementioned functional methods unless the class contains state.

### ✅ Immutable

The library prefers immutable objects where possible to encourage simple data structures.

#### dataclass

`dataclass`'s use the `object.__setattr__` pattern in `_postinit__` functions to support freezing data classes where possible.

#### NamedTuple

[NamedTuple](https://docs.python.org/3/library/typing.html#typing.NamedTuple) is being used frequently for the libraries data structures. They are immutable after creation and have a `_replace()` method that makes it easy to make a copy replacing only one field.

### ✅ Concurrency

While this library is not explicitly engineered to _use_ concurrency, it's definitely meant to work properly when the caller wants to run more than one thing at a time. This means that there is no global, mutable state in the library with the exception of a discrete-log function doing internal memoization, which is explicitly written to be thread-safe.

### ✅ Union Classes

For both naming purposes and usability, union classes are preferred in many cases. This can alleviate issues with [multiple inheritance](#multiple-inheritance)

### 🚫 Exceptions

To allow for easier transliteration, the library will not raise exception across the API boundary since this is not available in all languages. Instead, the library will have a variety of functions that indicate failures by returning `None`, and the caller is expected to check if the result is `None` before any further processing. Python3 `typing` calls this sort of result `Optional`.This tactic also indicates all exceptions raised are expected to be from bugs.

### 🚫 Multiple Inheritance

Although a handy python feature, in alignment with simplicity goals, this feature is not used and should be avoided.

## Architecture

### 🤝 Approachable

The python setup is designed to be as approachable as possible from the environment to the continuous integration.

#### Setup

The library contains a `Pipfile` that can be used with `pipenv` to ensure the correct dependencies as well as a `setup.py` to install the package. There is also a `Makefile` which allows for simple `make` commands to ease new developers into the build process. If one is a new developer, the recommendation is starting with [Visual Studio Code](https://code.visualstudio.com/) since there are many default settings and recommended extensions in the repository.

#### Folder Structure

The folder structure is kept to a bare minimum. The ElectionGuard library is located in `src/electionguard` and the tests are in `tests`. Standalone applications or other pieces should be in seperate subdirectories. For example, the `bench` directory which has a simple Chaum-Pedersen proof computation benchmark.

#### Commands

To simplify the command structure, [make](https://www.gnu.org/software/make/manual/make.html) is used. A `Makefile` sits in the root and holds useful commands that can be used to run setup. These are shown in use in the [continuous integration](#continuous-integration).

### 🧹 Clean Code

The library uses several tools to assist developer in maintaining clean code. The recommendation is to use Visual Studio Code for easier setup.

#### Typing

The library uses Python3's **type hints** throughout and ensures return types are defined. The tool **[Mypy](https://mypy.readthedocs.io/en/stable/)** is used to statically check the typing.

#### Linting

[Pylint]() is the chosen tool for typing. Settings are in the `.pylinrc` file.

#### Formatting

[Black]() is used for auto formatting and checking the formatting of the python code. Settings are in the `pyproject.toml` file.

### 🧪 Testing

The goal of the project is 100% code coverage with an understanding that there is some limitations.

#### Property Based

Property testing is helpful for testing certain [properties](https://fsharpforfunandprofit.com/posts/property-based-testing-2/). [Hypothesis](https://hypothesis.readthedocs.io/en/stable/) property-based testing to vigorously exercise our library. The library includes generator functions for all the core datatypes, making them easy to randomly generate.

### 🚀 Continous Integration

GitHub Actions are being used for continuous integration. Cross-platform is a primary goal and the workflows provided demonstrate how a developer can build in Linux, MacOS, and Windows.

The run workflows can be seen on the GitHub repo page or a user can navigate to `.github/workflows` to inspect them.

### 📦 Math Library

[gmpy2](https://gmpy2.readthedocs.io/en/latest/index.html) is a multiprecision numeric library that was chosen over Python's built-ins `int` type for its speed necessary for encryption performance. The current version used is `2.0.8` which is the most stable version. This is necessary for cross-platform since the library uses precompiled libraries for Windows due to reliance on `gmp`. The gmpy2 options are chosen over the native Python equivalents as shown below.

- **Integers:** `int` -> [`mpz`](https://gmpy2.readthedocs.io/en/latest/mpz.html)
- **Exponents:** `pow` -> `powmod`

With the use of **mypy** for typing and the lack of type presence in [Typeshed](https://github.com/python/typeshed) for gmpy2, the library provides a stub in `stubs/gmpy2.pyi` to ensure the code compiles without warnings.
