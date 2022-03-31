import click
from electionguard.manifest import Manifest
from electionguard_cli.hello import hello
from electionguard_tools.factories.election_factory import (
    ElectionFactory,
)

@click.command()
@click.option('--guardian-count', prompt='Number of guardians', help='The number of guardians that will participate in the key ceremony and tally.', type=click.INT)
@click.option('--quorum', prompt='Quorum', help='The minimum number of guardians required to show up to the tally.', type=click.INT)
def e2e(guardian_count, quorum):
    """Runs through an end-to-end election."""

    def print_header(s: str):
        click.secho(f"{'-'*40}", fg='green')
        click.secho(s, fg='green')
        click.secho(f"{'-'*40}", fg='green')

    def print_value(name: str, value: any):
        click.echo(click.style(name + ": ") + click.style(value, fg='yellow'))

    manifest: Manifest = ElectionFactory().get_simple_manifest_from_file()
    
    manifest_name = manifest.name.text[0].value
    print_header('Election Summary')
    print_value("Name", manifest_name)
    print_value("Scope", manifest.election_scope_id)
    print_value("Geopolitical Units", len(manifest.geopolitical_units))
    print_value("Parties", len(manifest.parties))
    print_value("Candidates", len(manifest.candidates))
    print_value("Contests", len(manifest.contests))
    print_value("Ballot Styles", len(manifest.ballot_styles))
    print_value("Guardians", guardian_count)
    print_value("Quorum", quorum)

    if (not manifest.is_valid()):
        click.echo('manifest file is invalid')
        return
