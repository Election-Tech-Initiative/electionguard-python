import click
from ..e2e_steps import (
    ElectionBuilderStep,
    KeyCeremonyStep,
    SubmitVotesStep,
    DecryptStep,
    PrintResultsStep,
    InputRetrievalStep,
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

    # get user inputs
    election_inputs = InputRetrievalStep().get_inputs(guardian_count, quorum)

    # perform election
    joint_key = KeyCeremonyStep().run_key_ceremony(election_inputs)
    build_election_results = ElectionBuilderStep().build_election(
        election_inputs, joint_key
    )
    ballot_store = SubmitVotesStep().submit_votes(
        election_inputs, build_election_results
    )
    decrypt_results = DecryptStep().decrypt_tally(
        ballot_store, election_inputs.guardians, build_election_results
    )

    # print results
    PrintResultsStep().print_election_results(decrypt_results)
