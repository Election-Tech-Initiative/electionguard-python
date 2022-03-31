# Setup

The ElectionGuard CLI can be installed via [setuptools](https://click.palletsprojects.com/en/8.1.x/setuptools/#setuptools-integration)

1. `poetry install`
2. `poetry shell`
3. `pip install --editable ./src/electionguard_cli/`

# Run the CLI

Now the end-to-end command is available to run from anywhere in the virual environment with the `eg` command.  Common commands:

- Get help, prints available commands: `eg --help`
- Print verison: `eg --version`
- Get help about how to run an end to end election test: `eg e2e --help`
- Run end-to-end election test: `eg e2e`
