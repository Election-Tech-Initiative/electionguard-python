from typing import List
import click
from electionguard.guardian import Guardian
from electionguard.utils import get_optional
from electionguard.ballot import SubmittedBallot
from electionguard.manifest import Manifest
from electionguard.tally import CiphertextTally
from electionguard.decryption_mediator import DecryptionMediator
from electionguard.election_polynomial import LagrangeCoefficientsRecord

from ..cli_models import BuildElectionResults, CliDecryptResults
from .cli_step_base import CliStepBase


class DecryptStep(CliStepBase):
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

    def decrypt(
        self,
        ciphertext_tally: CiphertextTally,
        spoiled_ballots: List[SubmittedBallot],
        guardians: List[Guardian],
        build_election_results: BuildElectionResults,
        manifest: Manifest,
    ) -> CliDecryptResults:
        self.print_header("Decrypting tally")

        decryption_mediator = DecryptionMediator(
            "decryption-mediator",
            build_election_results.context,
        )
        context = build_election_results.context

        self.print_value("Cast ballots", ciphertext_tally.cast())
        self.print_value("Spoiled ballots", ciphertext_tally.spoiled())
        self.print_value("Total ballots", len(ciphertext_tally))

        count = 0
        for guardian in guardians:
            guardian_key = guardian.share_key()
            tally_share = get_optional(
                guardian.compute_tally_share(ciphertext_tally, context)
            )
            ballot_shares = guardian.compute_ballot_shares(spoiled_ballots, context)
            decryption_mediator.announce(guardian_key, tally_share, ballot_shares)
            count += 1
            click.echo(f"Guardian Present: {guardian.id}")

        lagrange_coefficients = self._get_lagrange_coefficients(decryption_mediator)

        plaintext_tally = get_optional(
            decryption_mediator.get_plaintext_tally(ciphertext_tally, manifest)
        )

        plaintext_spoiled_ballots = get_optional(
            decryption_mediator.get_plaintext_ballots(spoiled_ballots, manifest)
        )

        return CliDecryptResults(
            plaintext_tally,
            plaintext_spoiled_ballots,
            ciphertext_tally,
            lagrange_coefficients,
        )
