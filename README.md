![Microsoft Defending Democracy Program: ElectionGuard Python](images/electionguard-banner.svg)

# 🗳 ElectionGuard Python

![Github Package Action](https://github.com/microsoft/electionguard-python/workflows/Release%20Build/badge.svg) [![](https://img.shields.io/pypi/v/electionguard)](https://pypi.org/project/electionguard/) [![](https://img.shields.io/pypi/dm/electionguard)](https://pypi.org/project/electionguard/) [![Documentation Status](https://readthedocs.org/projects/electionguard-python/badge/?version=latest)](https://electionguard-python.readthedocs.io) [![license](https://img.shields.io/github/license/microsoft/electionguard)](https://github.com/microsoft/electionguard-python/blob/main/LICENSE)

This repository is a "reference implementation" of ElectionGuard written in Python3. This implementation can be used to conduct End-to-End Verifiable Elections as well as privacy-enhanced risk-limiting audits.  Components of this library can also be used to construct "Verifiers" to validate the results of an ElectionGuard election.

## 📁 In This Repository

| File/folder             | Description                              |
| ----------------------- | ---------------------------------------- |
| `bench`                 | Microbenchmarks based on this codebase   |
| `docs`                  | Documentation for using the library      |
| `src/electionguard`     | Source code to the ElectionGuard library |
| `src/electionguardtest` | sample data and generators for testing   |
| `stubs`                 | Type annotations for external libraries  |
| `tests`                 | Unit tests to exercise this codebase     |
| `CONTRIBUTING.md`       | Guidelines for contributing              |
| `README.md`             | This README file                         |
| `LICENSE`               | The license for ElectionGuard-Python.    |

## ❓ What Is ElectionGuard?

ElectionGuard is an open source software development kit (SDK) that makes voting more secure, transparent and accessible. The ElectionGuard SDK leverages homomorphic encryption to ensure that votes recorded by electronic systems of any type remain encrypted, secure, and secret. Meanwhile, ElectionGuard also allows verifiable and accurate tallying of ballots by any 3rd party organization without compromising secrecy or security.

Learn More in the [ElectionGuard Repository](https://github.com/microsoft/electionguard)

## 🦸 How Can I use ElectionGuard?

ElectionGuard supports a variety of use cases.  The Primary use case is to generate verifiable end-to-end (E2E) encrypted elections.  The Electionguard process can also be used for other use cases such as privacy enhanced risk-limiting audits (RLAs).

## 💻 Requirements

- [Python 3.8](https://www.python.org/downloads/) is <ins>**required**</ins> to develop this SDK. If developer uses multiple versions of python, [pyenv](https://github.com/pyenv/pyenv) is suggested to assist version management.
- [GNU Make](https://www.gnu.org/software/make/manual/make.html) is used to simplify the commands and GitHub Actions. This approach is recommended to simplify the command line experience. This is built in for MacOS and Linux. For Windows, setup is simpler with [Chocolatey](https://chocolatey.org/install) and installing the provided [make package](https://chocolatey.org/packages/make). The other Windows option is [manually installing make](http://gnuwin32.sourceforge.net/packages/make.htm).
- [Gmpy2](https://gmpy2.readthedocs.io/en/latest/) is used for [Arbitrary-precision arithmetic](https://en.wikipedia.org/wiki/Arbitrary-precision_arithmetic) which
has its own [installation requirements (native C libraries)](https://gmpy2.readthedocs.io/en/latest/intro.html#installation) on Linux and MacOS.  **⚠️ Note:** _This is not required for Windows since the gmpy2 precompiled libraries are provided._
- [pipenv](https://github.com/pypa/pipenv) is used to configure the python environment. Installation instructions can be found [here](https://github.com/pypa/pipenv#installation).

## 🚀 Quick Start

Using [**make**](https://www.gnu.org/software/make/manual/make.html), the entire [Github Action workflow](.github/workflows/pull_request.yml) can be run with one command: 

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

For more detailed build and run options, see the [documentation](docs/Build_and_Run.md).

## 📄 Documentation

Overviews:

- [Github Pages](https://microsoft.github.io/electionguard-python/)
- [Read the Docs](https://electionguard-python.readthedocs.io/)

Sections:

- [Design and Architecture](docs/Design_and_Architecture.md)
- [Build and Run](docs/Build_and_Run.md)

Step-by-Step Process:

0. [Configure Election](docs/0_Configure_Election.md)
1. [Key Ceremony](docs/1_Key_Ceremony.md)
2. [Encrypt Ballots](docs/2_Encrypt_Ballots.md)
3. [Cast and Spoil](docs/3_Cast_and_Spoil.md)
4. [Decrypt Tally](docs/4_Decrypt_Tally.md)

## Contributing

This project encourages community contributions for development, testing, documentation, code review, and performance analysis, etc.  For more information on how to contribute, see [the contribution guidelines](CONTRIBUTING.md)

### Code of Conduct

This project has adopted the [Microsoft Open Source Code of Conduct](https://opensource.microsoft.com/codeofconduct/). For more information see the [Code of Conduct FAQ](https://opensource.microsoft.com/codeofconduct/faq/) or contact [opencode@microsoft.com](mailto:opencode@microsoft.com) with any additional questions or comments.

### Reporting Issues

Please report any bugs, feature requests, or enhancements using the [Github Issue Tracker](https://github.com/microsoft/electionguard-python/issues).  Please do not report any secirity vulnerabilities using the Issue Tracker.  Instead, please report them to the Microsoft Security Response Center (MSRC) at [https://msrc.microsoft.com/create-report](https://msrc.microsoft.com/create-report).  See the [Security Documentation](SECURITY.md) for more information.

### Have Questions?

Electionguard would love for you to ask questions out in the open using Github Issues. If you really want to email the ElectionGuard team, reach out at electionguard@microsoft.com.

## License

This repository is licensed under the [MIT License](LICENSE)
