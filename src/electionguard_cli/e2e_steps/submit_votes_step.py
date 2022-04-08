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
from electionguard_tools.factories.election_factory import (
    ElectionFactory,
)

from ..cli_models import E2eInputs, BuildElectionResults, E2eSubmitResults
from .e2e_step_base import E2eStepBase


class SubmitVotesStep(E2eStepBase):
    """Responsible for encrypting votes and storing them in a ballot store."""

    def submit_votes(
        self, e2e_inputs: E2eInputs, build_election_results: BuildElectionResults
    ) -> E2eSubmitResults:
        ballots = e2e_inputs.ballots
        internal_manifest = build_election_results.internal_manifest
        context = build_election_results.context
        ballot_store: DataStore = DataStore()
        (ciphertext_ballots, device) = self._encrypt_votes(
            ballots, internal_manifest, context
        )
        SubmitVotesStep._cast_and_spoil(
            ballot_store, internal_manifest, context, ciphertext_ballots, e2e_inputs
        )
        return E2eSubmitResults(ballot_store, device)

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
        encrypted_ballots = SubmitVotesStep._encrypt_ballots(
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

    @staticmethod
    def _cast_and_spoil(
        ballot_store: DataStore,
        internal_manifest: InternalManifest,
        context: CiphertextElectionContext,
        ciphertext_ballots: List[CiphertextBallot],
        e2e_inputs: E2eInputs,
    ) -> None:
        ballot_box = BallotBox(internal_manifest, context, ballot_store)

        for ballot in ciphertext_ballots:
            spoil = ballot.object_id == e2e_inputs.spoil_id
            if spoil:
                submitted_ballot = ballot_box.spoil(ballot)
            else:
                submitted_ballot = ballot_box.cast(ballot)

            click.echo(
                f"Submitted Ballot Id: {ballot.object_id} state: {get_optional(submitted_ballot).state}"
            )
