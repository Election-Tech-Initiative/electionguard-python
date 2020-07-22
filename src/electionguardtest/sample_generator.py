#!/usr/bin/env python
from random import randint
from shutil import rmtree
from typing import List
import uuid

from electionguardtest.election_factory import ElectionFactory
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
from electionguard.tally import tally_ballots
from electionguard.utils import get_optional

DEFAULT_NUMBER_OF_BALLOTS = 100
CAST_SPOIL_RATIO = 10


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
        self.encryption_device = EncryptionDevice(f"polling-place-{uuid.uuid1}")

    def generate(self):
        """
        Generate the sample data set
        """

        rmtree(RESULTS_DIR, ignore_errors=True)

        (
            public_data,
            private_data,
        ) = self.election_factory.get_hamilton_election_with_encryption_context()
        plaintext_ballots = self.ballot_factory.generate_fake_plaintext_ballots_for_election(
            public_data.metadata, DEFAULT_NUMBER_OF_BALLOTS
        )
        self.encrypter = EncryptionMediator(
            public_data.metadata, public_data.context, self.encryption_device
        )

        ciphertext_ballots: List[CiphertextBallot] = []
        for plaintext_ballot in plaintext_ballots:
            ciphertext_ballots.append(
                get_optional(self.encrypter.encrypt(plaintext_ballot))
            )

        ballot_store = BallotStore()
        ballot_box = BallotBox(public_data.metadata, public_data.context, ballot_store)

        accepted_ballots: List[CiphertextAcceptedBallot] = []
        for ballot in ciphertext_ballots:
            if randint(0, 100) % 10 == 0:
                accepted_ballots.append(ballot_box.spoil(ballot))
            else:
                accepted_ballots.append(ballot_box.cast(ballot))

        ciphertext_tally = get_optional(
            tally_ballots(ballot_store, public_data.metadata, public_data.context)
        )

        decrypter = DecryptionMediator(
            public_data.metadata, public_data.context, ciphertext_tally
        )

        for guardian in private_data.guardians:
            decrypter.announce(guardian)

        plaintext_tally = get_optional(decrypter.get_plaintext_tally())

        publish(
            public_data.description,
            public_data.context,
            public_data.constants,
            accepted_ballots,
            ciphertext_tally,
            plaintext_tally,
            public_data.guardians,
        )

        publish_private_data(
            plaintext_ballots, ciphertext_ballots, private_data.guardians
        )


if __name__ == "__main__":
    ElectionSampleDataGenerator().generate()
