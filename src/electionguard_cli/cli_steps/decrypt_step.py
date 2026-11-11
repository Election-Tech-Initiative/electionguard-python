import click
from electionguard.guardian import Guardian
from electionguard.utils import get_optional
from electionguard.ballot import SubmittedBallot
from electionguard.manifest import Manifest
from electionguard.tally import CiphertextTally
from electionguard.decryption_mediator import DecryptionMediator
from electionguard.election_polynomial import LagrangeCoefficientsRecord
from electionguard_tools.helpers.tally_ceremony_orchestrator import (
    TallyCeremonyOrchestrator,
)

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
        spoiled_ballots: list[SubmittedBallot],
        guardians: list[Guardian],
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

        if len(guardians) < context.quorum:
            raise click.ClickException(
                f"{len(guardians)} guardian(s) present, "
                f"but a quorum of {context.quorum} is required to decrypt"
            )

        all_guardian_keys = self._get_all_guardian_keys(guardians)
        present_ids = {guardian.id for guardian in guardians}
        for guardian in guardians:
            click.echo(f"Guardian Present: {guardian.id}")
        for guardian_id in all_guardian_keys:
            if guardian_id not in present_ids:
                click.echo(f"Guardian Missing: {guardian_id}")

        # announces the present guardians, and when some are missing has the present
        # guardians compensate for them so a quorum can still decrypt
        TallyCeremonyOrchestrator.perform_compensated_decryption_setup(
            guardians,
            list(all_guardian_keys.values()),
            decryption_mediator,
            context,
            ciphertext_tally,
            spoiled_ballots,
        )

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
