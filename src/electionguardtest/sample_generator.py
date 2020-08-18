#!/usr/bin/env python
from random import randint
from shutil import rmtree
from typing import List
import uuid

from electionguardtest.election_factory import ElectionFactory, QUORUM
from electionguardtest.ballot_factory import BallotFactory

from electionguard.ballot import (
    CiphertextBallot,
    CiphertextAcceptedBallot,
)
from electionguard.ballot_store import BallotStore
from electionguard.ballot_box import BallotBox
from electionguard.decryption_mediator import DecryptionMediator
from electionguard.encrypt import EncryptionDevice, EncryptionMediator
from electionguard.publish import publish, publish_private_data, RESULTS_DIR
from electionguard.tally import tally_ballots, publish_ciphertext_tally
from electionguard.utils import get_optional

DEFAULT_NUMBER_OF_BALLOTS = 5
CAST_SPOIL_RATIO = 50
THRESHOLD_ONLY = True


class ElectionSampleDataGenerator:
    """
    Generates sample data for an example election using the "Hamilton County" data set.
    """

    election_factory: ElectionFactory
    ballot_factory: BallotFactory

    encryption_device: EncryptionDevice
    encrypter: EncryptionMediator

    def __init__(self) -> None:
        """Initialize the class"""
        self.election_factory = ElectionFactory()
        self.ballot_factory = BallotFactory()
        self.encryption_device = EncryptionDevice(f"polling-place-{str(uuid.uuid1())}")

    def generate(
        self,
        number_of_ballots: int = DEFAULT_NUMBER_OF_BALLOTS,
        cast_spoil_ratio: int = CAST_SPOIL_RATIO,
    ):
        """
        Generate the sample data set
        """

        # Clear the results directory
        rmtree(RESULTS_DIR, ignore_errors=True)

        # Configure the election
        (
            public_data,
            private_data,
        ) = self.election_factory.get_hamilton_election_with_encryption_context()
        plaintext_ballots = self.ballot_factory.generate_fake_plaintext_ballots_for_election(
            public_data.metadata, number_of_ballots
        )
        self.encrypter = EncryptionMediator(
            public_data.metadata, public_data.context, self.encryption_device
        )

        # Encrypt some ballots
        ciphertext_ballots: List[CiphertextBallot] = []
        for plaintext_ballot in plaintext_ballots:
            ciphertext_ballots.append(
                get_optional(self.encrypter.encrypt(plaintext_ballot))
            )

        ballot_store = BallotStore()
        ballot_box = BallotBox(public_data.metadata, public_data.context, ballot_store)

        # Randomly cast/spoil the ballots
        accepted_ballots: List[CiphertextAcceptedBallot] = []
        for ballot in ciphertext_ballots:
            if randint(0, 100) % cast_spoil_ratio == 0:
                accepted_ballots.append(ballot_box.spoil(ballot))
            else:
                accepted_ballots.append(ballot_box.cast(ballot))

        # Tally
        ciphertext_tally = get_optional(
            tally_ballots(ballot_store, public_data.metadata, public_data.context)
        )

        # Decrypt
        decrypter = DecryptionMediator(
            public_data.metadata, public_data.context, ciphertext_tally
        )

        for i, guardian in enumerate(private_data.guardians):
            if i < QUORUM or not THRESHOLD_ONLY:
                decrypter.announce(guardian)

        plaintext_tally = get_optional(decrypter.get_plaintext_tally())

        # Publish
        publish(
            public_data.description,
            public_data.context,
            public_data.constants,
            [self.encryption_device],
            accepted_ballots,
            ciphertext_tally.spoiled_ballots.values(),
            publish_ciphertext_tally(ciphertext_tally),
            plaintext_tally,
            public_data.guardians,
        )

        publish_private_data(
            plaintext_ballots, ciphertext_ballots, private_data.guardians
        )


if __name__ == "__main__":
    ElectionSampleDataGenerator().generate()
