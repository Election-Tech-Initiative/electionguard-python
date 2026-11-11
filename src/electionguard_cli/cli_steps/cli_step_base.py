from typing import Any
import click

from electionguard.guardian import Guardian
from electionguard.key_ceremony import ElectionPublicKey
from electionguard.type import GuardianId


class CliStepBase:
    """
    Responsible for providing common functionality to the individual steps within an end-to-end election command
    from the CLI.
    """

    header_color = "green"
    value_color = "yellow"
    warning_color = "bright_red"
    section_color = "bright_white"
    VERIFICATION_URL_NAME = "verification_url"

    def print_header(self, s: str) -> None:
        click.echo("")
        click.secho(f"{'-'*40}", fg=self.header_color)
        click.secho(s, fg=self.header_color)
        click.secho(f"{'-'*40}", fg=self.header_color)

    def print_section(self, s: str | None) -> None:
        click.echo("")
        click.secho(s, fg=self.section_color, bold=True)

    def print_value(self, name: str, value: Any) -> None:
        click.echo(click.style(name + ": ") + click.style(value, fg=self.value_color))

    def print_warning(self, s: str) -> None:
        click.secho(f"WARNING: {s}", fg=self.warning_color)

    @staticmethod
    def _get_all_guardian_keys(
        guardians: list[Guardian],
    ) -> dict[GuardianId, ElectionPublicKey]:
        """
        Every guardian's public key, including guardians that are not present,
        as exchanged with the present guardians during the key ceremony.
        """
        keys: dict[GuardianId, ElectionPublicKey] = {}
        for guardian in guardians:
            keys.update(guardian.export_private_data().guardian_election_public_keys)
            keys[guardian.id] = guardian.share_key()
        return dict(sorted(keys.items(), key=lambda item: item[1].sequence_order))
