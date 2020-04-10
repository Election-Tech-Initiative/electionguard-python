# Engineering Notes for ElectionGuard-Python

This file tries to describe how we built ElectionGuard-Python and why it's built the way it is.
You'll find this useful when adding features and if you're trying to port it to a different
programming language or environment.

Table of contents:
- [General software engineering](#general-software-engineering)
- [Python-specific engineering](#python-specific-engineering)
- [Build engineering](#build-engineering)
- [GMPY2: Faster math](#gmpy2-faster-math)

## General software engineering
For starters, ElectionGuard-Python is meant to be a general-purpose library to support all
sorts of "end to end" encrypted voting systems. Different projects will wish to use different
layers of the library. This means that we're trying to expose useful math primitives, useful
encryption primitives, and so forth.

**Simplicity: an important engineering goal**: You should be able to transliterate the code here from Python
to any other programming language having nothing more than structures and functions.
To that end, ElectionGuard-Python has what we need, and not much more. For example,
the core math library (`group.py`) is built around two types, `ElementModP` and
`ElementModQ` and has the necessary operations to do additions on Q's and 
multiplications with P's. It's not trying to behave like a regular Python number with infix
math operations since that's extra code we don't really need.

You'll see that we're sometimes implementing methods on Python classes and other times we're
building old-fashioned functions. The goal is to be sensible. If it makes sense to have a
method on an object, like checking if a proof is valid, then `proof.is_valid()` is a bit easier
to read than `disjoint_chaum_pedersen_proof_is_valid(proof)`. As such, we're using class methods 
to simplify our code, where it's appropriate, but we're not really doing anything sophisticated with inheritance,
object encapsulation, or design patterns.

For the most part, the code here is written in a functional style. That doesn't mean we're
opposed to object-oriented programming or to mutating state. This particular style does,
however, lend itself to being easy to test and compose.

**Testing**: We're testing this code using property-based testing. If you're unfamiliar with
the concept, here are some good resources:

- [What is property-based testing?](https://hypothesis.works/articles/what-is-property-based-testing/): A quick read.
- [Choosing properties for property-based testing](https://fsharpforfunandprofit.com/posts/property-based-testing-2/): The examples here are in F#, but the engineering concepts are easily generalized.

Right now, using this style of testing, we're able to hit 100% code coverage, so straightforward bugs tend
to be easy to find and isolate. We even found a bug in one of the equations in the ElectionGuard
specification! Of course, this sort of testing is certainly not comprehensive, nor is it
likely to find subtle cryptographic flaws. 

The need to do testing has interesting ramifications for the design of the libraries. For example,
in standard object-oriented programming, you want to have constructors that enforce properties of
data structures, while hiding the implementation details from external clients of those interfaces. 
That's great, but what if you want to have validator functions that return true or false based on
whether a data structure is well-formed? Life is much simpler if you can use the same data structures,
even if you're loading them with bad data.

**Concurrency**: While this library is not explicitly engineered to *use* concurrency, it's 
definitely meant to work properly when the caller wants to run more than one thing at a time.
This means that there is no global, mutable state, anywhere in ElectionGuard-Python.
(Exception: our discrete-log function does internal memoization, so it's explicitly
written to be thread-safe.)

## Python-specific engineering

ElectionGuard-Python tries to use Python3's *type hints* throughout,
allowing for tools like [Mypy](https://mypy.readthedocs.io/en/stable/) to statically check the code for bugs.
    Also, our unit tests leverage
[Hypothesis](https://hypothesis.readthedocs.io/en/stable/) property-based testing to
vigorously exercise our library. In particular, we've written generator functions for
all the core datatypes, making it easy to randomly generate 

Also, ElectionGuard-Python requires a common Python indentation and variable-naming strategy. We use
[Black](https://black.readthedocs.io/en/stable/) to autoformat our code. Our CI testing requires the code
pass all the unit tests, plus Mypy, Black, and [Pylint](https://www.pylint.org/).

Generally speaking, we're using Python3's [NamedTuple](https://docs.python.org/3/library/typing.html#typing.NamedTuple)
for all our data structures. What's useful about these is that they're immutable after creation,
but they have a nice `_replace()` method that makes it easy to make a copy where you change
only one field.

Another Python-specific engineering goal is that *ElectionGuard-Python will never raise an
Exception unless there's a bug*. Instead, we have a variety of functions that indicate failures
by returning `None`, and the caller is expected to check if the result is `None` before any
further processing. Python3 calls this sort of result `Optional`. If you've heard of monads,
then Python's `Optional` is *not* the maybe monad. Nonetheless, we provide some helper functions at the bottom 
of `group.py` for working with these things with `flatmap` and other such helpers.

## Build engineering

ElectionGuard-Python uses a variety of tools to help with its build process. To run our
unit tests on GitHub, we're using [Tox](https://tox.readthedocs.io/en/latest/). We also
have various standard files like `Pipfile` or `setup.py`, which are recognized by common IDEs like
PyCharm or VSCode. 

Generally speaking, anything that belongs inside the ElectionGuard library should be
inside `src/electionguard`, and the tests are in `tests`. If we create standalone applications
that build on the library, they'll probably be in a separate subdirectory. See, for example,
the `bench` directory which has a simple Chaum-Pedersen proof computation benchmark.

## GMPY2: Faster math

We're using the GMPY2 multiprecision numeric library to go faster than Python's builtin int type, even 
though Python natively supports modular exponentiation. GMPY2 is *much* faster.

**Useful hyperlinks**:
- [Top-level documentation](https://gmpy2.readthedocs.io/en/latest/index.html)
- [Documentation on the `mpz` (multi-precision integer) type](https://gmpy2.readthedocs.io/en/latest/mpz.html)

**General usage:**
There's a constructor, `mpz()`, to go from a regular integer or string to an `mpz` integer. After
that, you can use `mpz` integers and regular Python `int` integers interchangeably. Equality and
everything appears to just work. GMPY2 defines a `powmod` function that looks to be equivalent
to Python's three-argument `pow` function, so we'll use `powmod` in case it's faster.

**Multithreading:**
GMPY2.0.8 is the most recent "stable" version.
GMPY2.1b4 is the most recent "beta" 
([release notes](https://gmpy2.readthedocs.io/en/latest/intro.html#enhancements-in-gmpy2-2-1),
[GitHub release tag](https://github.com/aleaxit/gmpy/releases/tag/gmpy2-2.1.0b4))
claims to have "thread-safe contexts", which seems important.
So far, all our tests with seem to pass with 2.1b4, but we can downgrade to 2.0.8 if necessary.

We have a very simplistic parallel test in `test_elgamal.py` (`test_gmpy2_parallelism_is_safe`) to exercise this.
Similarly, `bench/bench_chaum_pedersen.py` runs in parallel. Either of these will detect
any computational errors, if they were to occur when running in parallel.
Whether these tests reflect the stresses of a real-world deployment is TBD.

**Python type hints:**
GMPY2 has no type hints, nor are any present in [Typeshed](https://github.com/python/typeshed).
This makes `mypy` unhappy with our code in `group.py`. If you look in `stubs/gmpy2.pyi`, you'll see
just enough stubs to get `group.py` to compile without warnings.
