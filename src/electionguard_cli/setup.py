from setuptools import setup

setup(
    name='electionguard_cli',
    version='0.1.0',
    py_modules=['start'],
    install_requires=[
        'Click',
    ],
    entry_points={
        'console_scripts': [
            'eg = electionguard_cli:cli',
        ],
    },
)
