![Microsoft Defending Democracy Program: ElectionGuard Python](https://github.com/microsoft/electionguard-python/blob/main/images/electionguard-banner.svg?raw=true)

# 🗳 ElectionGuard Python

[![ElectionGuard Specification 0.95.0](https://img.shields.io/badge/🗳%20ElectionGuard%20Specification-0.95.0-green)](https://www.electionguard.vote) ![Github Package Action](https://github.com/microsoft/electionguard-python/workflows/Release%20Build/badge.svg) [![](https://img.shields.io/pypi/v/electionguard)](https://pypi.org/project/electionguard/) [![](https://img.shields.io/pypi/dm/electionguard)](https://pypi.org/project/electionguard/) [![Language grade: Python](https://img.shields.io/lgtm/grade/python/g/microsoft/electionguard-python.svg?logo=lgtm&logoWidth=18)](https://lgtm.com/projects/g/microsoft/electionguard-python/context:python) [![Total alerts](https://img.shields.io/lgtm/alerts/g/microsoft/electionguard-python.svg?logo=lgtm&logoWidth=18)](https://lgtm.com/projects/g/microsoft/electionguard-python/alerts/) [![Documentation Status](https://readthedocs.org/projects/electionguard-python/badge/?version=latest)](https://electionguard-python.readthedocs.io) [![license](https://img.shields.io/github/license/microsoft/electionguard)](https://github.com/microsoft/electionguard-python/blob/main/LICENSE)

This repository is a "reference implementation" of ElectionGuard written in Python 3. This implementation can be used to conduct End-to-End Verifiable Elections as well as privacy-enhanced risk-limiting audits. Components of this library can also be used to construct "Verifiers" to validate the results of an ElectionGuard election.

## 📁 In This Repository

| File/folder               | Description                              |
| ------------------------- | ---------------------------------------- |
| `docs`                    | Documentation for using the library      |
| `src/electionguard`       | Source code to the ElectionGuard library |
| `src/electionguard_tools` | sample data and generators for testing   |
| `stubs`                   | Type annotations for external libraries  |
| `tests`                   | Tests to exercise this codebase          |
| `CONTRIBUTING.md`         | Guidelines for contributing              |
| `README.md`               | This README file                         |
| `LICENSE`                 | The license for ElectionGuard-Python.    |

<br/>

## ❓ What Is ElectionGuard?

ElectionGuard is an open source software development kit (SDK) that makes voting more secure, transparent and accessible. The ElectionGuard SDK leverages homomorphic encryption to ensure that votes recorded by electronic systems of any type remain encrypted, secure, and secret. Meanwhile, ElectionGuard also allows verifiable and accurate tallying of ballots by any 3rd party organization without compromising secrecy or security.

Learn More in the [ElectionGuard Repository](https://github.com/microsoft/electionguard)

## 🦸 How Can I use ElectionGuard?

ElectionGuard supports a variety of use cases. The Primary use case is to generate verifiable end-to-end (E2E) encrypted elections. The Electionguard process can also be used for other use cases such as privacy enhanced risk-limiting audits (RLAs).

## 💻 Requirements

- [Python 3.9.5](https://www.python.org/downloads/) is <ins>**required**</ins> to develop this SDK. If developer uses multiple versions of python, [pyenv](https://github.com/pyenv/pyenv) is suggested to assist version management.
- [GNU Make](https://www.gnu.org/software/make/manual/make.html) is used to simplify the commands and GitHub Actions. This approach is recommended to simplify the command line experience. This is built in for MacOS and Linux. For Windows, setup is simpler with [Chocolatey](https://chocolatey.org/install) and installing the provided [make package](https://chocolatey.org/packages/make). The other Windows option is [manually installing make](http://gnuwin32.sourceforge.net/packages/make.htm).
- [Gmpy2](https://gmpy2.readthedocs.io/en/latest/) is used for [Arbitrary-precision arithmetic](https://en.wikipedia.org/wiki/Arbitrary-precision_arithmetic) which
  has its own [installation requirements (native C libraries)](https://gmpy2.readthedocs.io/en/latest/intro.html#installation) on Linux and MacOS. **⚠️ Note:** _This is not required for Windows since the gmpy2 precompiled libraries are provided._
- [poetry 1.1.10](https://python-poetry.org/) is used to configure the python environment. Installation instructions can be found [here](https://python-poetry.org/docs/#installation).

## 🚀 Quick Start

Using [**make**](https://www.gnu.org/software/make/manual/make.html), the entire [GitHub Action workflow](https://github.com/microsoft/electionguard-python/blob/main/.github/workflows/pull_request.yml) can be run with one command:

```
make
```

The unit and integration tests can also be run with make:

```
make test
```

A complete end-to-end election example can be run independently by executing:

```
make test-example
```

For more detailed build and run options, see the [documentation](Build_and_Run.md).

## 📄 Documentation

Sections:

- [Design and Architecture](Design_and_Architecture.md)
- [Build and Run](Build_and_Run.md)
- [Project Workflow](Project_Workflow.md)
- [Election Manifest](Election_Manifest.md)

Step-by-Step Process:

0. [Configure Election](0_Configure_Election.ipynb)
1. [Key Ceremony](1_Key_Ceremony.md)
2. [Encrypt Ballots](2_Encrypt_Ballots.md)
3. [Cast and Spoil](3_Cast_and_Spoil.md)
4. [Decrypt Tally](4_Decrypt_Tally.md)
5. [Publish and Verify](5_Publish_and_Verify.md)

## ❓Questions

Electionguard would love for you to ask questions out in the open using GitHub Issues. If you really want to email the ElectionGuard team, reach out at electionguard@microsoft.com.
