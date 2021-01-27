![Microsoft Defending Democracy Program: ElectionGuard Python][Banner Image]

# 🗳 ElectionGuard Python

![Github Package Action](https://github.com/microsoft/electionguard-python/workflows/Release%20Build/badge.svg) [![](https://img.shields.io/pypi/v/electionguard)](https://pypi.org/project/electionguard/) [![](https://img.shields.io/pypi/dm/electionguard)](https://pypi.org/project/electionguard/) [![Language grade: Python](https://img.shields.io/lgtm/grade/python/g/microsoft/electionguard-python.svg?logo=lgtm&logoWidth=18)](https://lgtm.com/projects/g/microsoft/electionguard-python/context:python) [![Total alerts](https://img.shields.io/lgtm/alerts/g/microsoft/electionguard-python.svg?logo=lgtm&logoWidth=18)](https://lgtm.com/projects/g/microsoft/electionguard-python/alerts/) [![Documentation Status](https://readthedocs.org/projects/electionguard-python/badge/?version=latest)](https://electionguard-python.readthedocs.io) [![license](https://img.shields.io/github/license/microsoft/electionguard)](https://github.com/microsoft/electionguard-python/blob/main/LICENSE)

This repository is a "reference implementation" of ElectionGuard written in Python 3. This implementation can be used to conduct End-to-End Verifiable Elections as well as privacy-enhanced risk-limiting audits.  Components of this library can also be used to construct "Verifiers" to validate the results of an ElectionGuard election.

## 📁 In This Repository

| File/folder             | Description                              |
| ----------------------- | ---------------------------------------- |
| `docs`                  | Documentation for using the library      |
| `src/electionguard`     | Source code to the ElectionGuard library |
| `src/electionguardtest` | sample data and generators for testing   |
| `stubs`                 | Type annotations for external libraries  |
| `tests`                 | Tests to exercise this codebase     |
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

Using [**make**](https://www.gnu.org/software/make/manual/make.html), the entire [GitHub Action workflow][Pull Request Workflow] can be run with one command: 

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

For more detailed build and run options, see the [documentation][Build and Run].

## 📄 Documentation

Overviews:

- [GitHub Pages](https://microsoft.github.io/electionguard-python/)
- [Read the Docs](https://electionguard-python.readthedocs.io/)

Sections:

- [Design and Architecture]
- [Build and Run]
- [Project Workflow]
- [Election Manifest]

Step-by-Step Process:

0. [Configure Election]
1. [Key Ceremony]
2. [Encrypt Ballots]
3. [Cast and Spoil]
4. [Decrypt Tally]
5. [Publish and Verify]

## Contributing

This project encourages community contributions for development, testing, documentation, code review, and performance analysis, etc.  For more information on how to contribute, see [the contribution guidelines][Contributing]

### Code of Conduct

This project has adopted the [Microsoft Open Source Code of Conduct](https://opensource.microsoft.com/codeofconduct/). For more information see the [Code of Conduct FAQ](https://opensource.microsoft.com/codeofconduct/faq/) or contact [opencode@microsoft.com](mailto:opencode@microsoft.com) with any additional questions or comments.

### Reporting Issues

Please report any bugs, feature requests, or enhancements using the [GitHub Issue Tracker](https://github.com/microsoft/electionguard-python/issues).  Please do not report any security vulnerabilities using the Issue Tracker.  Instead, please report them to the Microsoft Security Response Center (MSRC) at [https://msrc.microsoft.com/create-report](https://msrc.microsoft.com/create-report).  See the [Security Documentation][Security] for more information.

### Have Questions?

Electionguard would love for you to ask questions out in the open using GitHub Issues. If you really want to email the ElectionGuard team, reach out at electionguard@microsoft.com.

## License
This repository is licensed under the [MIT License]

## Thanks! 🎉
A huge thank you to those who helped to contribute to this project so far, including:

**[Josh Benaloh _(Microsoft)_](https://www.microsoft.com/en-us/research/people/benaloh/)**

<a href="https://www.microsoft.com/en-us/research/people/benaloh/"><img src="https://www.microsoft.com/en-us/research/wp-content/uploads/2016/09/avatar_user__1473484671-180x180.jpg" title="Josh Benaloh" width="80" height="80"></a> 

**[Keith Fung](https://github.com/keithrfung) [_(InfernoRed Technology)_](https://infernored.com/)**

<a href="https://github.com/keithrfung"><img src="https://avatars2.githubusercontent.com/u/10125297?v=4" title="keithrfung" width="80" height="80"></a>

**[Matt Wilhelm](https://github.com/AddressXception) [_(InfernoRed Technology)_](https://infernored.com/)**

<a href="https://github.com/AddressXception"><img src="https://avatars0.githubusercontent.com/u/6232853?s=460&u=8fec95386acad6109ad71a2aad2d097b607ebd6a&v=4" title="AddressXception" width="80" height="80"></a>

**[Dan S. Wallach](https://www.cs.rice.edu/~dwallach/) [_(Rice University)_](https://www.rice.edu/)**

<a href="https://www.cs.rice.edu/~dwallach/"><img src="https://avatars2.githubusercontent.com/u/743029?v=4" title="danwallach" width="80" height="80"></a>


<!-- Links -->
[Banner Image]: https://raw.githubusercontent.com/microsoft/electionguard-python/main/images/electionguard-banner.svg

[Pull Request Workflow]: https://github.com/microsoft/electionguard-python/blob/main/.github/workflows/pull_request.yml

[Contributing]: https://github.com/microsoft/electionguard-python/blob/main/CONTRIBUTING.md

[Security]:https://github.com/microsoft/electionguard-python/blob/main/SECURITY.md

[Design and Architecture]: https://github.com/microsoft/electionguard-python/blob/main/docs/Design_and_Architecture.md]

[Build and Run]: https://github.com/microsoft/electionguard-python/blob/main/docs/Build_and_Run.md

[Project Workflow]: https://github.com/microsoft/electionguard-python/blob/main/docs/Project_Workflow.md

[Election Manifest]: https://github.com/microsoft/electionguard-python/blob/main/docs/Election_Manifest.md

[Configure Election]: https://github.com/microsoft/electionguard-python/blob/main/docs/0_Configure_Election.md

[Key Ceremony]: https://github.com/microsoft/electionguard-python/blob/main/docs/1_Key_Ceremony.md

[Encrypt Ballots]: https://github.com/microsoft/electionguard-python/blob/main/docs/2_Encrypt_Ballots.md

[Cast and Spoil]: https://github.com/microsoft/electionguard-python/blob/main/docs/3_Cast_and_Spoil.md

[Decrypt Tally]: https://github.com/microsoft/electionguard-python/blob/main/docs/4_Decrypt_Tally.md

[Publish and Verify]: https://github.com/microsoft/electionguard-python/blob/main/docs/5_Publish_and_Verify.md)

[MIT License]: https://github.com/microsoft/electionguard-python/blob/main/LICENSE
