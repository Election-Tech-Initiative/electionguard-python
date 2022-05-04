from typing import List, Tuple
import click

from electionguard.data_store import DataStore
from electionguard.ballot_box import BallotBox
from electionguard.encrypt import EncryptionDevice, EncryptionMediator
from electionguard.election import CiphertextElectionContext
from electionguard.manifest import InternalManifest
from electionguard.utils import get_optional
from electionguard.ballot import (
    CiphertextBallot,
    PlaintextBallot,
)
from electionguard_tools.factories import (
    ElectionFactory,
)

from ..cli_models import (
    BuildElectionResults,
)
from ..cli_steps import CliStepBase
from .e2e_inputs import E2eInputs
from .e2e_encrypt_results import E2eEncryptResults


class EncryptVotesStep(CliStepBase):
    """Responsible for encrypting votes and storing them in a ballot store."""

    def encrypt(
        self, e2e_inputs: E2eInputs, build_election_results: BuildElectionResults
    ) -> E2eEncryptResults:
        self.print_header("Encrypting Ballots")
        internal_manifest = build_election_results.internal_manifest
        context = build_election_results.context
        (ciphertext_ballots, device) = self._encrypt_votes(
            e2e_inputs.ballots, internal_manifest, context
        )
        return E2eEncryptResults(device, ciphertext_ballots)

    def _get_encrypter(
        self,
        internal_manifest: InternalManifest,
        context: CiphertextElectionContext,
    ) -> Tuple[EncryptionMediator, EncryptionDevice]:
        device = ElectionFactory.get_encryption_device()
        self.print_value("Device location", device.location)
        encrypter = EncryptionMediator(internal_manifest, context, device)
        return (encrypter, device)

    def _encrypt_votes(
        self,
        plaintext_ballots: List[PlaintextBallot],
        internal_manifest: InternalManifest,
        context: CiphertextElectionContext,
    ) -> Tuple[List[CiphertextBallot], EncryptionDevice]:
        self.print_value("Ballots to encrypt", len(plaintext_ballots))
        (encrypter, device) = self._get_encrypter(internal_manifest, context)
        encrypted_ballots = EncryptVotesStep._encrypt_ballots(
            plaintext_ballots, encrypter
        )
        return (encrypted_ballots, device)

    @staticmethod
    def _encrypt_ballots(
        plaintext_ballots: List[PlaintextBallot], encrypter: EncryptionMediator
    ) -> List[CiphertextBallot]:
        ciphertext_ballots: List[CiphertextBallot] = []
        for plaintext_ballot in plaintext_ballots:
            click.echo(f"Encrypting ballot: {plaintext_ballot.object_id}")
            encrypted_ballot = encrypter.encrypt(plaintext_ballot)
            ciphertext_ballots.append(get_optional(encrypted_ballot))
        return ciphertext_ballots
