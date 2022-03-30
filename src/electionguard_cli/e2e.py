import click
from electionguard import guardian
from electionguard.manifest import Manifest
from electionguard_tools.factories.election_factory import (
    ElectionFactory,
)

@click.command()
@click.option('--guardian-count', prompt='Number of guardians', help='The number of guardians that will participate in the key ceremony and tally.')
@click.option('--quorum', prompt='Quorum', help='The minimum number of guardians required to show up to the tally.')
def start(guardian_count, quorum):
    """Runs through an end-to-end election."""

    manifest: Manifest = ElectionFactory().get_simple_manifest_from_file()
    click.echo(f"{'-'*40}")
    click.echo("Election Summary:")
    manifest_name = manifest.name.text[0].value
    click.echo(f"Name: {manifest_name}")
    click.echo(f"Scope: {manifest.election_scope_id}")
    click.echo(f"Geopolitical Units: {len(manifest.geopolitical_units)}")
    click.echo(f"Parties: {len(manifest.parties)}")
    click.echo(f"Candidates: {len(manifest.candidates)}")
    click.echo(f"Contests: {len(manifest.contests)}")
    click.echo(f"Ballot Styles: {len(manifest.ballot_styles)}")
    click.echo(f"Guardians: {guardian_count}")
    click.echo(f"Quorum: {quorum}")
    click.echo(f"{'-'*40}\n")

    if (not manifest.is_valid()):
        click.echo('bad bad bad')
        return

def cli():
    start()