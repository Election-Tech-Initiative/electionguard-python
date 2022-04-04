from typing import Dict, List, Any, Optional
import click
from e2e_steps import ElectionBuilderStep, KeyCeremonyStep, SubmitVotesStep, DecryptStep
from electionguard.ballot import PlaintextBallot

from electionguard.type import BallotId
from electionguard.guardian import Guardian
from electionguard.manifest import InternationalizedText, Manifest
from electionguard.tally import (
    PlaintextTally,
)
from electionguard_tools.factories.ballot_factory import BallotFactory
from electionguard_tools.factories.election_factory import (
    ElectionFactory,
)


@click.command()
@click.option(
    "--guardian-count",
    prompt="Number of guardians",
    help="The number of guardians that will participate in the key ceremony and tally.",
    type=click.INT,
)
@click.option(
    "--quorum",
    prompt="Quorum",
    help="The minimum number of guardians required to show up to the tally.",
    type=click.INT,
)
def e2e(guardian_count: int, quorum: int) -> None:
    """Runs through an end-to-end election."""

    def print_header(s: str) -> None:
        click.secho(f"{'-'*40}", fg="green")
        click.secho(s, fg="green")
        click.secho(f"{'-'*40}", fg="green")

    def print_value(name: str, value: Any) -> None:
        click.echo(click.style(name + ": ") + click.style(value, fg="yellow"))

    def get_ballots() -> List[PlaintextBallot]:
        # todo: parameterize the plaintext ballot file
        return BallotFactory().get_simple_ballots_from_file()

    def print_manifest(manifest: Manifest) -> None:
        def get_first_value(text: Optional[InternationalizedText]) -> str:
            return "" if text is None else text.text[0].value

        manifest_name = get_first_value(manifest.name)
        print_value("Name", manifest_name)
        print_value("Scope", manifest.election_scope_id)
        print_value("Geopolitical Units", len(manifest.geopolitical_units))
        print_value("Parties", len(manifest.parties))
        print_value("Candidates", len(manifest.candidates))
        print_value("Contests", len(manifest.contests))
        print_value("Ballot Styles", len(manifest.ballot_styles))
        print_value("Guardians", guardian_count)
        print_value("Quorum", quorum)

    def get_manifest() -> Manifest:
        # todo: get manifest from params
        print_header("Retrieving manifest")
        manifest: Manifest = ElectionFactory().get_simple_manifest_from_file()
        if not manifest.is_valid():
            raise ValueError("manifest file is invalid")
        print_manifest(manifest)
        return manifest

    def get_guardians(number_of_guardians: int) -> List[Guardian]:
        guardians: List[Guardian] = []
        for i in range(number_of_guardians):
            guardians.append(
                Guardian(
                    str(i + 1),
                    i + 1,
                    number_of_guardians,
                    quorum,
                )
            )
        return guardians



    def print_tally(plaintext_tally: PlaintextTally) -> None:
        print_header("Decrypted tally")
        for contest in plaintext_tally.contests.values():
            click.echo(f"Contest: {contest.object_id}")
            for selection in contest.selections.values():
                click.echo(
                    f"  Selection '{selection.object_id}' received: {selection.tally} votes"
                )

    def print_spoiled_ballot(
        plaintext_spoiled_ballots: Dict[BallotId, PlaintextTally]
    ) -> None:
        ballot_id = list(plaintext_spoiled_ballots)[0]
        print_header(f"Spoiled ballot '{ballot_id}'")
        spoiled_ballot = plaintext_spoiled_ballots[ballot_id]
        for contest in spoiled_ballot.contests.values():
            click.echo(f"Contest: {contest.object_id}")
            for selection in contest.selections.values():
                click.echo(
                    f"  Selection '{selection.object_id}' received {selection.tally} vote"
                )


    # get user inputs
    guardians = get_guardians(guardian_count)
    manifest: Manifest = get_manifest()
    ballots = get_ballots()

    # perform election
    joint_key = KeyCeremonyStep().run_key_ceremony(guardians)
    internal_manifest, context = ElectionBuilderStep().build_election(
        joint_key, guardian_count, quorum, manifest
    )
    ballot_store = SubmitVotesStep().submit_votes(ballots, internal_manifest, context)
    (tally, spoiled_ballots) = DecryptStep().decrypt_tally(ballot_store, guardians, internal_manifest, context)

    # print results
    print_tally(tally)
    print_spoiled_ballot(spoiled_ballots)
