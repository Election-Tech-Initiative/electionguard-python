# Note on the use of GMPY2

We're using the GMPY2 multiprecision numeric library to go faster than Python's builtin int type, even 
though Python natively supports modular exponentiation. GMPY2 is *much* faster.

## Useful hyperlinks:
- [Top-level documentation](https://gmpy2.readthedocs.io/en/latest/index.html)
- [Documentation on the `mpz` (multi-precision integer) type](https://gmpy2.readthedocs.io/en/latest/mpz.html)

## General usage
There's a constructor, `mpz()`, to go from a regular integer or string to an mpz. After
that, you can use mpz's and regular Python int's interchangeably. Equality and
everything appears to just work. GMPY2 defines a `powmod` function that looks to be equivalent
to Python's three-argument `pow` function, so we'll use `powmod` in case it's faster.

## Multithreading
GMPY2.0.8 is the most recent "stable" version.
GMPY2.1b4 is the most recent "beta" 
([release notes](https://gmpy2.readthedocs.io/en/latest/intro.html#enhancements-in-gmpy2-2-1),
[GitHub release tag](https://github.com/aleaxit/gmpy/releases/tag/gmpy2-2.1.0b4))
claims to have "thread-safe contexts", implying the absence of this from earlier releases.
So far, all our tests with seem to pass with 2.1b4, but we can downgrade to 2.0.8 if necessary.

Why go bleeding edge? Multithreading support seems important if/when we want to run EG in parallel,
which will probably be necessary and useful when computing with large ballot manifests.

## Python type hints
GMPY2 has no type hints, nor are any present in [Typeshed](https://github.com/python/typeshed).
This makes `mypy` unhappy with our code in `group.py`. If you look in `stubs/gmpy2.pyi`, you'll see
just enough stubs to get `group.py` to compile without warnings.
