from typing import List
import click
from electionguard_cli.cli_models import BuildElectionResults, E2eDecryptResults
from electionguard.decryption_share import DecryptionShare
from electionguard.election import CiphertextElectionContext
from electionguard.data_store import DataStore
from electionguard.ballot_box import get_ballots
from electionguard.guardian import Guardian
from electionguard.utils import get_optional
from electionguard.ballot import BallotBoxState
from electionguard.tally import CiphertextTally, tally_ballots
from electionguard.decryption_mediator import DecryptionMediator
from electionguard.election_polynomial import LagrangeCoefficientsRecord

from .e2e_step_base import E2eStepBase


class DecryptStep(E2eStepBase):
    """Responsible for decrypting a tally and/or cast ballots"""

    def __get_spoiled_ballots(self, ballot_store: DataStore):
        submitted_ballots = get_ballots(ballot_store, BallotBoxState.SPOILED)
        spoiled_ballots_list = list(submitted_ballots.values())
        return spoiled_ballots_list

    def __get_tally(
        self, ballot_store: DataStore, build_election_results: BuildElectionResults
    ) -> CiphertextTally:
        tally = tally_ballots(
            ballot_store,
            build_election_results.internal_manifest,
            build_election_results.context,
        )
        return get_optional(tally)

    def __get_decryption_mediator(
        self, build_election_results: BuildElectionResults
    ) -> DecryptionMediator:
        decryption_mediator = DecryptionMediator(
            "decryption-mediator",
            build_election_results.context,
        )
        return decryption_mediator

    def __print_lagrange_coefficients(
        self, decryption_mediator: DecryptionMediator
    ) -> None:
        lagrange_coefficients = LagrangeCoefficientsRecord(
            decryption_mediator.get_lagrange_coefficients()
        )
        coefficient_count = len(lagrange_coefficients.coefficients)
        self.print_value("Lagrange coefficients retrieved", coefficient_count)

    def __compute_tally_share(
        self,
        guardian: Guardian,
        tally: CiphertextTally,
        context: CiphertextElectionContext,
    ) -> DecryptionShare:
        shares = guardian.compute_tally_share(tally, context)
        return get_optional(shares)

    def decrypt_tally(
        self,
        ballot_store: DataStore,
        guardians: List[Guardian],
        build_election_results: BuildElectionResults,
    ) -> E2eDecryptResults:
        self.print_header("Decrypting tally")

        tally = self.__get_tally(ballot_store, build_election_results)
        spoiled_ballots = self.__get_spoiled_ballots(ballot_store)
        decryption_mediator = self.__get_decryption_mediator(build_election_results)
        context = build_election_results.context

        self.print_value("Cast ballots", tally.cast())
        self.print_value("Spoiled ballots", tally.spoiled())
        self.print_value("Total ballots", len(tally))

        count = 0
        for guardian in guardians:
            guardian_key = guardian.share_key()
            tally_share = self.__compute_tally_share(guardian, tally, context)
            ballot_shares = guardian.compute_ballot_shares(spoiled_ballots, context)
            decryption_mediator.announce(guardian_key, tally_share, ballot_shares)
            count += 1
            click.echo(f"Guardian Present: {guardian.id}")

        self.__print_lagrange_coefficients(decryption_mediator)

        plaintext_tally = get_optional(decryption_mediator.get_plaintext_tally(tally))

        plaintext_spoiled_ballots = get_optional(
            decryption_mediator.get_plaintext_ballots(spoiled_ballots)
        )

        return E2eDecryptResults(plaintext_tally, plaintext_spoiled_ballots)
