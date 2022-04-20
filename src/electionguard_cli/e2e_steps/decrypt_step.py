from typing import List
import click
from electionguard_cli.cli_models import BuildElectionResults, E2eDecryptResults
from electionguard.decryption_share import DecryptionShare
from electionguard.election import CiphertextElectionContext
from electionguard.data_store import DataStore
from electionguard.ballot_box import get_ballots
from electionguard.guardian import Guardian
from electionguard.utils import get_optional
from electionguard.ballot import BallotBoxState, SubmittedBallot
from electionguard.tally import CiphertextTally, tally_ballots
from electionguard.decryption_mediator import DecryptionMediator
from electionguard.election_polynomial import LagrangeCoefficientsRecord
from .e2e_step_base import E2eStepBase


class DecryptStep(E2eStepBase):
    """Responsible for decrypting a tally and/or cast ballots"""

    def _get_lagrange_coefficients(
        self, decryption_mediator: DecryptionMediator
    ) -> LagrangeCoefficientsRecord:
        lagrange_coefficients = LagrangeCoefficientsRecord(
            decryption_mediator.get_lagrange_coefficients()
        )
        coefficient_count = len(lagrange_coefficients.coefficients)
        self.print_value("Lagrange coefficients retrieved", coefficient_count)
        return lagrange_coefficients

    def decrypt_ballot_store(
        self,
        ballot_store: DataStore,
        guardians: List[Guardian],
        build_election_results: BuildElectionResults,
    ) -> E2eDecryptResults:
        ciphertext_tally = DecryptStep._get_tally(ballot_store, build_election_results)
        spoiled_ballots = DecryptStep._get_spoiled_ballots(ballot_store)
        return self.decrypt_tally(
            ciphertext_tally, spoiled_ballots, guardians, build_election_results
        )

    def decrypt_tally(
        self,
        ciphertext_tally: CiphertextTally,
        spoiled_ballots: List[SubmittedBallot],
        guardians: List[Guardian],
        build_election_results: BuildElectionResults,
    ) -> E2eDecryptResults:
        self.print_header("Decrypting tally")

        decryption_mediator = DecryptStep._get_decryption_mediator(
            build_election_results
        )
        context = build_election_results.context

        self.print_value("Cast ballots", ciphertext_tally.cast())
        self.print_value("Spoiled ballots", ciphertext_tally.spoiled())
        self.print_value("Total ballots", len(ciphertext_tally))

        count = 0
        for guardian in guardians:
            guardian_key = guardian.share_key()
            tally_share = DecryptStep._compute_tally_share(
                guardian, ciphertext_tally, context
            )
            ballot_shares = guardian.compute_ballot_shares(spoiled_ballots, context)
            decryption_mediator.announce(guardian_key, tally_share, ballot_shares)
            count += 1
            click.echo(f"Guardian Present: {guardian.id}")

        click.echo("Retrieving lagrange_coefficients")
        lagrange_coefficients = self._get_lagrange_coefficients(decryption_mediator)

        plaintext_tally = get_optional(
            decryption_mediator.get_plaintext_tally(ciphertext_tally)
        )

        plaintext_spoiled_ballots = get_optional(
            decryption_mediator.get_plaintext_ballots(spoiled_ballots)
        )

        return E2eDecryptResults(
            plaintext_tally,
            plaintext_spoiled_ballots,
            ciphertext_tally,
            lagrange_coefficients,
        )

    @staticmethod
    def _compute_tally_share(
        guardian: Guardian,
        tally: CiphertextTally,
        context: CiphertextElectionContext,
    ) -> DecryptionShare:
        shares = guardian.compute_tally_share(tally, context)
        return get_optional(shares)

    @staticmethod
    def _get_spoiled_ballots(ballot_store: DataStore) -> List[SubmittedBallot]:
        submitted_ballots = get_ballots(ballot_store, BallotBoxState.SPOILED)
        spoiled_ballots_list = list(submitted_ballots.values())
        return spoiled_ballots_list

    @staticmethod
    def _get_tally(
        ballot_store: DataStore, build_election_results: BuildElectionResults
    ) -> CiphertextTally:
        # instead create a CiphertextTally and add all the ballots and remove the ballot_store and ballot_box
        tally = tally_ballots(
            ballot_store,
            build_election_results.internal_manifest,
            build_election_results.context,
        )
        return get_optional(tally)

    @staticmethod
    def _get_decryption_mediator(
        build_election_results: BuildElectionResults,
    ) -> DecryptionMediator:
        decryption_mediator = DecryptionMediator(
            "decryption-mediator",
            build_election_results.context,
        )
        return decryption_mediator
