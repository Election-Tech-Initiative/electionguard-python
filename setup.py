#!/usr/bin/env python
# -*- encoding: utf-8 -*-
from __future__ import absolute_import
from __future__ import print_function

from glob import glob
from os.path import basename, splitext, abspath, dirname, join

from setuptools import find_packages
from setuptools import setup

current_directory = abspath(dirname(__file__))
with open(join(current_directory, "README.md"), encoding="utf-8") as readme_file:
    LONG_DESCRIPTION = readme_file.read()

NAME = "electionguard"
VERSION = "1.1.2"
LICENSE = "MIT"
DESCRIPTION = "ElectionGuard: Support for e2e verified elections."
LONG_DESCRIPTION_CONTENT_TYPE = "text/markdown"
AUTHOR = "Microsoft Corporation"
AUTHOR_EMAIL = "electionguard@microsoft.com"
URL = "https://github.com/microsoft/electionguard-python"
PROJECT_URLS = {
    "Documentation": "https://microsoft.github.io/electionguard-python",
    "Read the Docs": "https://electionguard-python.readthedocs.io",
    "Releases": "https://github.com/microsoft/electionguard-python/releases",
    "Milestones": "https://github.com/microsoft/electionguard-python/milestones",
    "Issue Tracker": "https://github.com/microsoft/electionguard-python/issues",
}
CLASSIFIERS = [
    # http://pypi.python.org/pypi?%3Aaction=list_classifiers
    "Development Status :: 5 - Production/Stable",
    "Intended Audience :: Developers",
    "License :: OSI Approved :: MIT License",
    "Operating System :: Unix",
    "Operating System :: POSIX",
    "Operating System :: MacOS",
    "Operating System :: Microsoft :: Windows",
    "Programming Language :: Python",
    "Programming Language :: Python :: 3.8",
    "Programming Language :: Python :: Implementation :: CPython",
    "Topic :: Utilities",
]


setup(
    name=NAME,
    version=VERSION,
    license=LICENSE,
    description=DESCRIPTION,
    long_description=LONG_DESCRIPTION,
    long_description_content_type=LONG_DESCRIPTION_CONTENT_TYPE,
    author=AUTHOR,
    author_email=AUTHOR_EMAIL,
    url=URL,
    packages=find_packages("src"),
    package_dir={"": "src"},
    py_modules=[splitext(basename(path))[0] for path in glob("src/*.py")],
    include_package_data=True,
    zip_safe=False,
    classifiers=CLASSIFIERS,
    project_urls=PROJECT_URLS,
    python_requires="~=3.8",
    install_requires=[
        "gmpy2>=2.0.8",
        "numpy>=1.18.2",
        "jsons>=1.1.2",
        "cryptography",
        "psutil>=5.7.2",
    ],
)
