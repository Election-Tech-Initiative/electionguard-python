---
page_type: sample
languages:
- csharp
products:
- dotnet
description: "Add 150 character max description"
urlFragment: "update-this-to-unique-url-stub"
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

| File/folder       | Description                                |
|-------------------|--------------------------------------------|
| `bench`           | Microbenchmarks based on this codebase     |
| `src/electionguard` | Source code to the ElectionGuard library |
| `stubs`           | Type annotations for external libraries    |
| `tests`           | Unit tests to exercise this codebase       |
| `CONTRIBUTING.md` | Guidelines for contributing                |
| `README.md`       | This README file                           |
| `LICENSE`         | The license for ElectionGuard-Python.      |

## Prerequisites

This code was developed against Python3.8, and is unlikely to work against earlier versions.
To make the math go faster, we're using [Gmpy2](https://gmpy2.readthedocs.io/en/latest/), which
has its own installation requirements (native C libraries).

## Setup

(Say something about `pip` installation commands.)

## Running

This project is configured to use [tox](https://tox.readthedocs.io/en/latest/) to run its
unit tests.

(More here later for any standalone utilities that will appear in this repository.)

## Key concepts

TBD

## Contributing

This project welcomes contributions and suggestions.  

ElectionGuard-Python tries to use Python3's *type hints* throughout,
allowing for tools like [mypy](https://mypy.readthedocs.io/en/stable/) to statically check the code for bugs.
Please do your best to ensure that `mypy` has zero issues with the code. Also, our unit tests leverage
[hypothesis](https://hypothesis.readthedocs.io/en/stable/) property-based testing to
vigorously exercise our library. Please write lots of good tests with your PRs.

Most contributions require you to agree to a
Contributor License Agreement (CLA) declaring that you have the right to, and actually do, grant us
the rights to use your contribution. For details, visit https://cla.opensource.microsoft.com.

When you submit a pull request, a CLA bot will automatically determine whether you need to provide
a CLA and decorate the PR appropriately (e.g., status check, comment). Simply follow the instructions
provided by the bot. You will only need to do this once across all repos using our CLA.

This project has adopted the [Microsoft Open Source Code of Conduct](https://opensource.microsoft.com/codeofconduct/).
For more information see the [Code of Conduct FAQ](https://opensource.microsoft.com/codeofconduct/faq/) or
contact [opencode@microsoft.com](mailto:opencode@microsoft.com) with any additional questions or comments.
