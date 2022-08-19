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
from electionguard.election_polynomial import LagrangeCoefficientsRecord
from electionguard.encrypt import (
    EncryptionDevice,
    EncryptionMediator,
)
from electionguard.guardian import PrivateGuardianRecord
from electionguard.tally import tally_ballots
from electionguard.type import BallotId
from electionguard.utils import get_optional

from electionguard_tools.factories.ballot_factory import BallotFactory
from electionguard_tools.factories.election_factory import ElectionFactory, QUORUM
from electionguard_tools.helpers.tally_ceremony_orchestrator import (
    TallyCeremonyOrchestrator,
)
from electionguard_tools.helpers.export import (
    export_record,
    export_private_data,
    ELECTION_RECORD_DIR,
    PRIVATE_DATA_DIR,
)


DEFAULT_NUMBER_OF_BALLOTS = 5
DEFAULT_SPOIL_RATE = 50
DEFAULT_USE_ALL_GUARDIANS = False
DEFAULT_USE_PRIVATE_DATA = False
DEFAULT_SPEC_VERSION = "1.0"
DEFAULT_SAMPLE_MANIFEST = "hamilton-general"


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
        use_private_data: bool = DEFAULT_USE_PRIVATE_DATA,
        sample_manifest: str = DEFAULT_SAMPLE_MANIFEST,
    ) -> None:
        """
        Generate the sample data set
        """

        # Clear the results directory
        rmtree(ELECTION_RECORD_DIR, ignore_errors=True)
        rmtree(PRIVATE_DATA_DIR, ignore_errors=True)

        # Configure the election
        # TODO: pass the spec version and the manifest name in
        (
            public_data,
            private_data,
        ) = self.election_factory.get_sample_manifest_with_encryption_context(
            sample_manifest
        )
        plaintext_ballots = (
            self.ballot_factory.generate_fake_plaintext_ballots_for_election(
                public_data.internal_manifest, number_of_ballots
            )
        )
        self.encrypter = EncryptionMediator(
            public_data.internal_manifest, public_data.context, self.encryption_device
        )

        # Encrypt some ballots
        ciphertext_ballots: List[CiphertextBallot] = []
        for plaintext_ballot in plaintext_ballots:
            ciphertext_ballots.append(
                get_optional(self.encrypter.encrypt(plaintext_ballot))
            )

        ballot_store: DataStore[BallotId, SubmittedBallot] = DataStore()
        ballot_box = BallotBox(
            public_data.internal_manifest, public_data.context, ballot_store
        )

        # Randomly cast/spoil the ballots
        submitted_ballots: List[SubmittedBallot] = []
        for ballot in ciphertext_ballots:
            if randint(0, 100) < spoil_rate:
                submitted_ballots.append(get_optional(ballot_box.spoil(ballot)))
            else:
                submitted_ballots.append(get_optional(ballot_box.cast(ballot)))

        # Tally
        spoiled_ciphertext_ballots = get_ballots(ballot_store, BallotBoxState.SPOILED)
        ciphertext_tally = get_optional(
            tally_ballots(
                ballot_store, public_data.internal_manifest, public_data.context
            )
        )

        # Decrypt
        mediator = DecryptionMediator("sample-manifest-decrypter", public_data.context)
        available_guardians = (
            private_data.guardians
            if use_all_guardians
            else private_data.guardians[0:QUORUM]
        )

        spoiled_ballots = list(spoiled_ciphertext_ballots.values())

        if not use_all_guardians:
            available_guardians = private_data.guardians[0:QUORUM]
            all_guardian_keys = [
                guardian.share_key() for guardian in private_data.guardians
            ]

            TallyCeremonyOrchestrator.perform_compensated_decryption_setup(
                available_guardians,
                all_guardian_keys,
                mediator,
                public_data.context,
                ciphertext_tally,
                spoiled_ballots,
            )
        else:
            TallyCeremonyOrchestrator.perform_decryption_setup(
                available_guardians,
                mediator,
                public_data.context,
                ciphertext_tally,
                spoiled_ballots,
            )

        plaintext_tally = mediator.get_plaintext_tally(
            ciphertext_tally, public_data.manifest
        )
        plaintext_spoiled_ballots = list(
            get_optional(
                mediator.get_plaintext_ballots(spoiled_ballots, public_data.manifest)
            ).values()
        )

        if plaintext_tally:
            export_record(
                public_data.manifest,
                public_data.context,
                public_data.constants,
                [self.encryption_device],
                submitted_ballots,
                plaintext_spoiled_ballots,
                ciphertext_tally.publish(),
                plaintext_tally,
                public_data.guardians,
                LagrangeCoefficientsRecord(mediator.get_lagrange_coefficients()),
            )

            if use_private_data:
                export_private_data(
                    plaintext_ballots,
                    ciphertext_ballots,
                    [
                        # pylint: disable=protected-access
                        PrivateGuardianRecord(
                            guardian.id,
                            guardian._election_keys,
                            guardian._backups_to_share,
                            guardian._guardian_election_public_keys,
                            guardian._guardian_election_partial_key_backups,
                            guardian._guardian_election_partial_key_verifications,
                        )
                        for guardian in private_data.guardians
                    ],
                )


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="Generate sample ballot data",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )

    parser.add_argument(
        "-m",
        "--manifest",
        metavar="<manifest>",
        default=DEFAULT_SAMPLE_MANIFEST,
        type=str,
        help="The manifest to use to generate sample data.",
        choices=["full", "hamilton-general", "minimal", "small"],
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
    parser.add_argument(
        "-p",
        "--private-data",
        default=DEFAULT_USE_PRIVATE_DATA,
        action="store_true",
        help="Include private data when generating.",
    )
    parser.add_argument(
        "-v",
        "--version",
        default=DEFAULT_SPEC_VERSION,
        type=str,
        help="The spec version to use.",
        choices=[DEFAULT_SPEC_VERSION],
    )
    args = parser.parse_args()

    ElectionSampleDataGenerator().generate(
        args.number_of_ballots,
        args.spoil_rate,
        args.all_guardians,
        args.private_data,
        args.manifest,
    )
