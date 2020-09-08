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
DEFAULT_SPOIL_RATE = 50
DEFAULT_USE_ALL_GUARDIANS = False


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
        spoil_rate: int = DEFAULT_SPOIL_RATE,
        use_all_guardians: bool = DEFAULT_USE_ALL_GUARDIANS,
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
            if randint(0, 100) < spoil_rate:
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
            if use_all_guardians or i < QUORUM:
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
    import argparse

    parser = argparse.ArgumentParser(
        description="Generate sample ballot data",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "-n",
        "--number-of-ballots",
        metavar="<count>",
        default=DEFAULT_NUMBER_OF_BALLOTS,
        type=int,
        help="The number of ballots to generate.",
    )
    parser.add_argument(
        "-s",
        "--spoil-rate",
        metavar="<rate>",
        default=DEFAULT_SPOIL_RATE,
        type=int,
        help="The approximate percentage of total ballots to spoil instead of cast. Provide a number from 0-100.",
    )
    parser.add_argument(
        "-a",
        "--all-guardians",
        default=DEFAULT_USE_ALL_GUARDIANS,
        action="store_true",
        help="If specified, all guardians will be included.  Otherwise, only the threshold number will be included.",
    )
    args = parser.parse_args()

    ElectionSampleDataGenerator().generate(
        args.number_of_ballots, args.spoil_rate, args.all_guardians
    )
