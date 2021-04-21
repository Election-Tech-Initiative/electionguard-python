#!/usr/bin/env python
from random import randint
from shutil import rmtree
from typing import List

from electionguard.ballot import (
    BallotBoxState,
    CiphertextBallot,
    SubmittedBallot,
)
from electionguard.data_store import DataStore
from electionguard.ballot_box import BallotBox, get_ballots
from electionguard.decryption_mediator import DecryptionMediator
from electionguard.encrypt import (
    EncryptionDevice,
    EncryptionMediator,
)
from electionguard.publish import publish, publish_private_data, RESULTS_DIR
from electionguard.tally import tally_ballots
from electionguard.utils import get_optional

from .ballot_factory import BallotFactory
from .decryption_helper import DecryptionHelper
from .election_factory import ElectionFactory, QUORUM


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
        self.encryption_device = self.election_factory.get_encryption_device()

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
            manifest,
            private_data,
        ) = self.election_factory.get_hamilton_manifest_with_encryption_context()
        plaintext_ballots = (
            self.ballot_factory.generate_fake_plaintext_ballots_for_election(
                manifest.internal_manifest, number_of_ballots
            )
        )
        self.encrypter = EncryptionMediator(
            manifest.internal_manifest, manifest.context, self.encryption_device
        )

        # Encrypt some ballots
        ciphertext_ballots: List[CiphertextBallot] = []
        for plaintext_ballot in plaintext_ballots:
            ciphertext_ballots.append(
                get_optional(self.encrypter.encrypt(plaintext_ballot))
            )

        ballot_store = DataStore()
        ballot_box = BallotBox(
            manifest.internal_manifest, manifest.context, ballot_store
        )

        # Randomly cast/spoil the ballots
        submitted_ballots: List[SubmittedBallot] = []
        for ballot in ciphertext_ballots:
            if randint(0, 100) < spoil_rate:
                submitted_ballots.append(ballot_box.spoil(ballot))
            else:
                submitted_ballots.append(ballot_box.cast(ballot))

        # Tally
        spoiled_ciphertext_ballots = get_ballots(ballot_store, BallotBoxState.SPOILED)
        ciphertext_tally = get_optional(
            tally_ballots(ballot_store, manifest.internal_manifest, manifest.context)
        )

        # Decrypt
        mediator = DecryptionMediator("sample-manifest-decrypter", manifest.context)
        available_guardians = (
            private_data.guardians
            if use_all_guardians
            else private_data.guardians[0:QUORUM]
        )
        DecryptionHelper.perform_decryption_setup(
            available_guardians,
            mediator,
            manifest.context,
            ciphertext_tally,
            spoiled_ciphertext_ballots,
        )

        plaintext_tally = get_optional(mediator.get_plaintext_tally(ciphertext_tally))
        plaintext_spoiled_ballots = get_optional(
            mediator.get_plaintext_ballots(spoiled_ciphertext_ballots)
        )

        # Publish
        publish(
            manifest.manifest,
            manifest.context,
            manifest.constants,
            [self.encryption_device],
            submitted_ballots,
            plaintext_spoiled_ballots.values(),
            ciphertext_tally.publish(),
            plaintext_tally,
            manifest.guardians,
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
