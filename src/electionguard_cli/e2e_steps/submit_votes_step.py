from typing import List
import click
from e2e_steps.e2e_step_base import E2eStepBase
from electionguard_cli.cli_models import E2eInputs, BuildElectionResults
from electionguard.data_store import DataStore
from electionguard.ballot_box import BallotBox
from electionguard.encrypt import EncryptionMediator
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


class SubmitVotesStep(E2eStepBase):
    """Responsible for encrypting votes and storing them in a ballot store."""

    def __encrypt_ballots(
        self, plaintext_ballots: List[PlaintextBallot], encrypter: EncryptionMediator
    ) -> List[CiphertextBallot]:
        ciphertext_ballots: List[CiphertextBallot] = []
        for plaintext_ballot in plaintext_ballots:
            click.echo(f"Encrypting ballot: {plaintext_ballot.object_id}")
            encrypted_ballot = encrypter.encrypt(plaintext_ballot)
            ciphertext_ballots.append(get_optional(encrypted_ballot))
        return ciphertext_ballots

    def __get_encrypter(
        self,
        internal_manifest: InternalManifest,
        context: CiphertextElectionContext,
    ) -> EncryptionMediator:
        device = ElectionFactory.get_encryption_device()
        self.print_value("Device location", device.location)
        encrypter = EncryptionMediator(internal_manifest, context, device)
        return encrypter

    def __encrypt_votes(
        self,
        plaintext_ballots: List[PlaintextBallot],
        internal_manifest: InternalManifest,
        context: CiphertextElectionContext,
    ) -> List[CiphertextBallot]:
        self.print_value("Ballots to encrypt", len(plaintext_ballots))
        encrypter = self.__get_encrypter(internal_manifest, context)
        encrypted_ballots = self.__encrypt_ballots(plaintext_ballots, encrypter)
        return encrypted_ballots

    def __cast_and_spoil(
        self,
        ballot_store: DataStore,
        internal_manifest: InternalManifest,
        context: CiphertextElectionContext,
        ciphertext_ballots: List[CiphertextBallot],
    ) -> None:
        ballot_box = BallotBox(internal_manifest, context, ballot_store)

        first = True
        for ballot in ciphertext_ballots:
            if first:
                submitted_ballot = ballot_box.spoil(ballot)
            else:
                submitted_ballot = ballot_box.cast(ballot)
            first = False

            click.echo(
                f"Submitted Ballot Id: {ballot.object_id} state: {get_optional(submitted_ballot).state}"
            )

    def submit_votes(
        self, e2e_inputs: E2eInputs, build_election_results: BuildElectionResults
    ) -> DataStore:
        ballots = e2e_inputs.ballots
        internal_manifest = build_election_results.internal_manifest
        context = build_election_results.context
        ballot_store: DataStore = DataStore()
        ciphertext_ballots = self.__encrypt_votes(ballots, internal_manifest, context)
        self.__cast_and_spoil(
            ballot_store, internal_manifest, context, ciphertext_ballots
        )
        return ballot_store
