import click
from e2e_steps import ElectionBuilderStep, KeyCeremonyStep, SubmitVotesStep, DecryptStep, PrintResultsStep, InputRetrievalStep

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

    # get user inputs
    (guardians, manifest, ballots) = InputRetrievalStep().get_inputs(guardian_count, quorum)

    # perform election
    joint_key = KeyCeremonyStep().run_key_ceremony(guardians)
    internal_manifest, context = ElectionBuilderStep().build_election(
        joint_key, guardian_count, quorum, manifest
    )
    ballot_store = SubmitVotesStep().submit_votes(ballots, internal_manifest, context)
    (tally, spoiled_ballots) = DecryptStep().decrypt_tally(ballot_store, guardians, internal_manifest, context)

    # print results
    PrintResultsStep().print_election_results(tally, spoiled_ballots)
