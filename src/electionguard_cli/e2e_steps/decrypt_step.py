from typing import Dict, List, Tuple
from cli_models.build_election_results import BuildElectionResults
import click
from e2e_steps.e2e_step_base import E2eStepBase

from electionguard.data_store import DataStore
from electionguard.ballot_box import get_ballots
from electionguard.election import CiphertextElectionContext
from electionguard.type import BallotId
from electionguard.guardian import Guardian
from electionguard.manifest import InternalManifest
from electionguard.utils import get_optional
from electionguard.ballot import (
    BallotBoxState,
)
from electionguard.tally import (
    tally_ballots,
    PlaintextTally,
)
from electionguard.decryption_mediator import DecryptionMediator
from electionguard.election_polynomial import LagrangeCoefficientsRecord


class DecryptStep(E2eStepBase):
    """Responsible for decrypting a tally and/or cast ballots"""

    def decrypt_tally(
        self,
        ballot_store: DataStore,
        guardians: List[Guardian],
        build_election_results: BuildElectionResults,
    ) -> Tuple[PlaintextTally, Dict[BallotId, PlaintextTally]]:
        self.print_header("Decrypting tally")
        internal_manifest = build_election_results.internal_manifest
        context = build_election_results.context
        ciphertext_tally = get_optional(
            tally_ballots(ballot_store, internal_manifest, context)
        )
        submitted_ballots = get_ballots(ballot_store, BallotBoxState.SPOILED)
        click.echo("Decrypting tally")
        self.print_value("Cast ballots", ciphertext_tally.cast())
        self.print_value("Spoiled ballots", ciphertext_tally.cast())
        self.print_value("Total ballots", len(ciphertext_tally))

        # Configure the Decryption
        submitted_ballots_list = list(submitted_ballots.values())
        decryption_mediator = DecryptionMediator(
            "decryption-mediator",
            context,
        )

        # Announce each guardian as present
        count = 0
        for guardian in guardians:
            guardian_key = guardian.share_key()
            tally_share = guardian.compute_tally_share(ciphertext_tally, context)
            ballot_shares = guardian.compute_ballot_shares(
                submitted_ballots_list, context
            )
            decryption_mediator.announce(
                guardian_key, get_optional(tally_share), ballot_shares
            )
            count += 1
            click.echo(f"Guardian Present: {guardian.id}")

        lagrange_coefficients = LagrangeCoefficientsRecord(
            decryption_mediator.get_lagrange_coefficients()
        )
        click.echo(
            f"retrieved {len(lagrange_coefficients.coefficients)} lagrange coefficients"
        )

        # Get the plaintext Tally
        plaintext_tally = get_optional(
            decryption_mediator.get_plaintext_tally(ciphertext_tally)
        )

        # Get the plaintext Spoiled Ballots
        plaintext_spoiled_ballots = get_optional(
            decryption_mediator.get_plaintext_ballots(submitted_ballots_list)
        )

        return (plaintext_tally, plaintext_spoiled_ballots)
