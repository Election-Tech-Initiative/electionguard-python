#!/usr/bin/env python

from typing import Callable, Dict, List, Union
from os import path
from shutil import rmtree
from random import randint
from dataclasses import asdict

from tests.base_test_case import BaseTestCase

from electionguard.type import BALLOT_ID
from electionguard.utils import get_optional

# Step 0 - Configure Election
from electionguard.constants import ElectionConstants, get_constants
from electionguard.election import CiphertextElectionContext
from electionguard.election_builder import ElectionBuilder
from electionguard.manifest import Manifest, InternalManifest

# Step 1 - Key Ceremony
from electionguard.guardian import Guardian, GuardianRecord
from electionguard.key_ceremony_mediator import KeyCeremonyMediator

# Step 2 - Encrypt Votes
from electionguard.ballot import (
    BallotBoxState,
    CiphertextBallot,
    PlaintextBallot,
    SubmittedBallot,
)
from electionguard.encrypt import EncryptionDevice
from electionguard.encrypt import EncryptionMediator

# Step 3 - Cast and Spoil
from electionguard.data_store import DataStore
from electionguard.ballot_box import BallotBox, get_ballots

# Step 4 - Decrypt Tally
from electionguard.tally import (
    PublishedCiphertextTally,
    tally_ballots,
    CiphertextTally,
    PlaintextTally,
)
from electionguard.decryption_mediator import DecryptionMediator
from electionguard.election_polynomial import LagrangeCoefficientsRecord

# Step 5 - Publish and Verify
from electionguard_tools.helpers.export import (
    COEFFICIENTS_FILE_NAME,
    export,
    BALLOT_PREFIX,
    CONSTANTS_FILE_NAME,
    CONTEXT_FILE_NAME,
    DEVICE_PREFIX,
    ENCRYPTED_TALLY_FILE_NAME,
    GUARDIAN_PREFIX,
    MANIFEST_FILE_NAME,
    TALLY_FILE_NAME,
)
from electionguard_tools.helpers.serialize import from_file_to_dataclass, construct_path

from electionguard_tools.factories.ballot_factory import BallotFactory
from electionguard_tools.factories.election_factory import (
    ElectionFactory,
    NUMBER_OF_GUARDIANS,
)
from electionguard_tools.helpers.identity_encrypt import (
    identity_auxiliary_encrypt,
    identity_auxiliary_decrypt,
)

RESULTS_DIR = "test-results"
DEVICES_DIR = path.join(RESULTS_DIR, "devices")
GUARDIAN_DIR = path.join(RESULTS_DIR, "guardians")
BALLOTS_DIR = path.join(RESULTS_DIR, "encrypted_ballots")
SPOILED_DIR = path.join(RESULTS_DIR, "spoiled_ballots")

# pylint: disable=too-many-instance-attributes
class TestEndToEndElection(BaseTestCase):
    """
    Test a complete simple example of executing an End-to-End encrypted election.
    In a real world scenario all of these steps would not be completed on the same machine.
    """

    NUMBER_OF_GUARDIANS = 5
    QUORUM = 3

    REMOVE_OUTPUT = False

    # Step 0 - Configure Election
    manifest: Manifest
    election_builder: ElectionBuilder
    internal_manifest: InternalManifest
    context: CiphertextElectionContext
    constants: ElectionConstants

    # Step 1 - Key Ceremony
    mediator: KeyCeremonyMediator
    guardians: List[Guardian] = []

    # Step 2 - Encrypt Votes
    device: EncryptionDevice
    encrypter: EncryptionMediator
    plaintext_ballots: List[PlaintextBallot]
    ciphertext_ballots: List[CiphertextBallot] = []

    # Step 3 - Cast and Spoil
    ballot_store: DataStore[BALLOT_ID, SubmittedBallot]
    ballot_box: BallotBox
    submitted_ballots: Dict[BALLOT_ID, SubmittedBallot]

    # Step 4 - Decrypt Tally
    ciphertext_tally: CiphertextTally
    plaintext_tally: PlaintextTally
    plaintext_spoiled_ballots: Dict[str, PlaintextTally]
    decryption_mediator: DecryptionMediator
    lagrange_coefficients: LagrangeCoefficientsRecord

    # Step 5 - Publish
    guardian_records: List[GuardianRecord] = []

    def test_end_to_end_election(self) -> None:
        """
        Execute the simplified end-to-end test demonstrating each component of the system.
        """
        self.step_0_configure_election()
        self.step_1_key_ceremony()
        self.step_2_encrypt_votes()
        self.step_3_cast_and_spoil()
        self.step_4_decrypt_tally()
        self.step_5_publish()

    def step_0_configure_election(self) -> None:
        """
        To conduct an election, load an `Manifest` file
        """

        # Load a pre-configured Election Description
        # TODO: replace with complex election
        self.manifest = ElectionFactory().get_simple_manifest_from_file()
        print(
            f"""
            {'-'*40}\n
            # Election Summary:
            # Scope: {self.manifest.election_scope_id}
            # Geopolitical Units: {len(self.manifest.geopolitical_units)}
            # Parties: {len(self.manifest.parties)}
            # Candidates: {len(self.manifest.candidates)}
            # Contests: {len(self.manifest.contests)}
            # Ballot Styles: {len(self.manifest.ballot_styles)}\n
            {'-'*40}\n
            """
        )
        self._assert_message(
            Manifest.is_valid.__qualname__,
            "Verify that the input election meta-data is well-formed",
            self.manifest.is_valid(),
        )

        # Create an Election Builder
        self.election_builder = ElectionBuilder(
            self.NUMBER_OF_GUARDIANS, self.QUORUM, self.manifest
        )
        self._assert_message(
            ElectionBuilder.__qualname__,
            f"Created with number_of_guardians: {self.NUMBER_OF_GUARDIANS} quorum: {self.QUORUM}",
        )

        # Move on to the Key Ceremony

    def step_1_key_ceremony(self) -> None:
        """
        Using the NUMBER_OF_GUARDIANS, generate public-private keypairs and share
        representations of those keys with QUORUM of other Guardians.  Then, combine
        the public election keys to make a joint election key that is used to encrypt ballots
        """

        # Setup Guardians
        for i in range(self.NUMBER_OF_GUARDIANS):
            self.guardians.append(
                Guardian(
                    "guardian_" + str(i + 1),
                    i + 1,
                    self.NUMBER_OF_GUARDIANS,
                    self.QUORUM,
                )
            )

        # Setup Mediator
        self.mediator = KeyCeremonyMediator(
            "mediator_1", self.guardians[0].ceremony_details
        )

        # ROUND 1: Public Key Sharing
        # Announce
        for guardian in self.guardians:
            self.mediator.announce(guardian.share_public_keys())

        # Share Keys
        for guardian in self.guardians:
            announced_keys = get_optional(self.mediator.share_announced())
            for key_set in announced_keys:
                if guardian.id is not key_set.election.owner_id:
                    guardian.save_guardian_public_keys(key_set)

        self._assert_message(
            KeyCeremonyMediator.all_guardians_announced.__qualname__,
            "Confirms all guardians have shared their public keys",
            self.mediator.all_guardians_announced(),
        )

        # ROUND 2: Election Partial Key Backup Sharing
        # Share Backups
        for sending_guardian in self.guardians:
            sending_guardian.generate_election_partial_key_backups(
                identity_auxiliary_encrypt
            )
            backups = []
            for designated_guardian in self.guardians:
                if designated_guardian.id != sending_guardian.id:
                    backups.append(
                        get_optional(
                            sending_guardian.share_election_partial_key_backup(
                                designated_guardian.id
                            )
                        )
                    )
            self.mediator.receive_backups(backups)
            self._assert_message(
                KeyCeremonyMediator.receive_backups.__qualname__,
                "Receive election partial key backups from key owning guardian",
                len(backups) == NUMBER_OF_GUARDIANS - 1,
            )

        self._assert_message(
            KeyCeremonyMediator.all_backups_available.__qualname__,
            "Confirm all guardians have shared their election partial key backups",
            self.mediator.all_backups_available(),
        )

        # Receive Backups
        for designated_guardian in self.guardians:
            backups = get_optional(self.mediator.share_backups(designated_guardian.id))
            self._assert_message(
                KeyCeremonyMediator.share_backups.__qualname__,
                "Share election partial key backups for the designated guardian",
                len(backups) == NUMBER_OF_GUARDIANS - 1,
            )
            for backup in backups:
                designated_guardian.save_election_partial_key_backup(backup)

        # ROUND 3: Verification of Backups
        # Verify Backups
        for designated_guardian in self.guardians:
            verifications = []
            for backup_owner in self.guardians:
                if designated_guardian.id is not backup_owner.id:
                    verification = (
                        designated_guardian.verify_election_partial_key_backup(
                            backup_owner.id, identity_auxiliary_decrypt
                        )
                    )
                    verifications.append(get_optional(verification))
            self.mediator.receive_backup_verifications(verifications)

        self._assert_message(
            KeyCeremonyMediator.all_backups_verified.__qualname__,
            "Confirms all guardians have verified the backups of all other guardians",
            self.mediator.all_backups_verified(),
        )

        # FINAL: Publish Joint Key
        joint_key = self.mediator.publish_joint_key()
        self._assert_message(
            KeyCeremonyMediator.publish_joint_key.__qualname__,
            "Publishes the Joint Election Key",
            joint_key is not None,
        )

        # Build the Election
        self.election_builder.set_public_key(get_optional(joint_key).joint_public_key)
        self.election_builder.set_commitment_hash(
            get_optional(joint_key).commitment_hash
        )
        self.internal_manifest, self.context = get_optional(
            self.election_builder.build()
        )
        self.constants = get_constants()

        # Move on to encrypting ballots

    def step_2_encrypt_votes(self) -> None:
        """
        Using the `CiphertextElectionContext` encrypt ballots for the election
        """

        # Configure the Encryption Device
        self.device = ElectionFactory.get_encryption_device()
        self.encrypter = EncryptionMediator(
            self.internal_manifest, self.context, self.device
        )
        self._assert_message(
            EncryptionDevice.__qualname__,
            f"Ready to encrypt at location: {self.device.location}",
        )

        # Load some Ballots
        self.plaintext_ballots = BallotFactory().get_simple_ballots_from_file()
        self._assert_message(
            PlaintextBallot.__qualname__,
            f"Loaded ballots: {len(self.plaintext_ballots)}",
            len(self.plaintext_ballots) > 0,
        )

        # Encrypt the Ballots
        for plaintext_ballot in self.plaintext_ballots:
            encrypted_ballot = self.encrypter.encrypt(plaintext_ballot)
            self._assert_message(
                EncryptionMediator.encrypt.__qualname__,
                f"Ballot Id: {plaintext_ballot.object_id}",
                encrypted_ballot is not None,
            )
            self.ciphertext_ballots.append(get_optional(encrypted_ballot))

        # Next, we cast or spoil the ballots

    def step_3_cast_and_spoil(self) -> None:
        """
        Accept each ballot by marking it as either cast or spoiled.
        This example demonstrates one way to accept ballots using the `BallotBox` class
        """

        # Configure the Ballot Box
        self.ballot_store = DataStore()
        self.ballot_box = BallotBox(
            self.internal_manifest, self.context, self.ballot_store
        )

        # Randomly cast or spoil the ballots
        for ballot in self.ciphertext_ballots:
            if randint(0, 1):
                submitted_ballot = self.ballot_box.cast(ballot)
            else:
                submitted_ballot = self.ballot_box.spoil(ballot)

            self._assert_message(
                BallotBox.__qualname__,
                f"Submitted Ballot Id: {ballot.object_id} state: {get_optional(submitted_ballot).state}",
                submitted_ballot is not None,
            )

    def step_4_decrypt_tally(self) -> None:
        """
        Homomorphically combine the selections made on all of the cast ballots
        and use the Available Guardians to decrypt the combined tally.
        In this way, no individual voter's cast ballot is ever decrypted drectly.
        """

        # Generate a Homomorphically Accumulated Tally of the ballots
        self.ciphertext_tally = get_optional(
            tally_ballots(self.ballot_store, self.internal_manifest, self.context)
        )
        self.submitted_ballots = get_ballots(self.ballot_store, BallotBoxState.SPOILED)
        self._assert_message(
            tally_ballots.__qualname__,
            f"""
            - cast: {self.ciphertext_tally.cast()}
            - spoiled: {self.ciphertext_tally.spoiled()}
            Total: {len(self.ciphertext_tally)}
            """,
            self.ciphertext_tally is not None,
        )

        # Configure the Decryption
        submitted_ballots_list = list(self.submitted_ballots.values())
        self.decryption_mediator = DecryptionMediator(
            "decryption-mediator",
            self.context,
        )

        # Announce each guardian as present
        count = 0
        for guardian in self.guardians:
            guardian_key = guardian.share_election_public_key()
            tally_share = guardian.compute_tally_share(
                self.ciphertext_tally, self.context
            )
            ballot_shares = guardian.compute_ballot_shares(
                submitted_ballots_list, self.context
            )
            self.decryption_mediator.announce(
                guardian_key, get_optional(tally_share), ballot_shares
            )
            count += 1
            self._assert_message(
                DecryptionMediator.announce.__qualname__,
                f"Guardian Present: {guardian.id}",
                len(self.decryption_mediator.get_available_guardians()) == count,
            )

        self.lagrange_coefficients = LagrangeCoefficientsRecord(
            list(self.decryption_mediator.get_lagrange_coefficients().values())
        )

        # Get the plaintext Tally
        self.plaintext_tally = get_optional(
            self.decryption_mediator.get_plaintext_tally(self.ciphertext_tally)
        )
        self._assert_message(
            DecryptionMediator.get_plaintext_tally.__qualname__,
            "Tally Decrypted",
            self.plaintext_tally is not None,
        )

        # Get the plaintext Spoiled Ballots
        self.plaintext_spoiled_ballots = get_optional(
            self.decryption_mediator.get_plaintext_ballots(submitted_ballots_list)
        )
        self._assert_message(
            DecryptionMediator.get_plaintext_ballots.__qualname__,
            "Spoiled Ballots Decrypted",
            self.plaintext_tally is not None,
        )

        # Now, compare the results
        self.compare_results()

    def compare_results(self) -> None:
        """
        Compare the results to ensure the decryption was done correctly.
        """
        print(
            f"""
            {'-'*40}
            # Election Results:

            """
        )

        # Create a representation of each contest's tally
        selection_ids = [
            selection.object_id
            for contest in self.manifest.contests
            for selection in contest.ballot_selections
        ]
        expected_plaintext_tally: Dict[str, int] = {key: 0 for key in selection_ids}

        # Tally the expected values from the loaded ballots
        for ballot in self.plaintext_ballots:
            if (
                get_optional(self.ballot_store.get(ballot.object_id)).state
                == BallotBoxState.CAST
            ):
                for contest in ballot.contests:
                    for selection in contest.ballot_selections:
                        expected_plaintext_tally[selection.object_id] += selection.vote

        # Compare the expected tally to the decrypted tally
        for tally_contest in self.plaintext_tally.contests.values():
            print(f" Contest: {tally_contest.object_id}")
            for tally_selection in tally_contest.selections.values():
                expected = expected_plaintext_tally[tally_selection.object_id]
                self._assert_message(
                    f"   - Selection: {tally_selection.object_id}",
                    f"expected: {expected}, actual: {tally_selection.tally}",
                    expected == tally_selection.tally,
                )
        print(f"\n{'-'*40}\n")

        # Compare the expected values for each spoiled ballot
        for ballot in self.plaintext_ballots:
            if (
                get_optional(self.ballot_store.get(ballot.object_id)).state
                == BallotBoxState.SPOILED
            ):
                print(f"\nSpoiled Ballot: {ballot.object_id}")
                for contest in ballot.contests:
                    print(f"\n Contest: {contest.object_id}")
                    for selection in contest.ballot_selections:
                        expected = selection.vote
                        decrypted_selection = (
                            self.plaintext_spoiled_ballots[ballot.object_id]
                            .contests[contest.object_id]
                            .selections[selection.object_id]
                        )
                        self._assert_message(
                            f"   - Selection: {selection.object_id}",
                            f"expected: {expected}, actual: {decrypted_selection.tally}",
                            expected == decrypted_selection.tally,
                        )

    def step_5_publish(self) -> None:
        """Publish results/artifacts of the election."""

        self.guardian_records = [guardian.publish() for guardian in self.guardians]

        export(
            self.manifest,
            self.context,
            self.constants,
            [self.device],
            self.ballot_store.all(),
            self.plaintext_spoiled_ballots.values(),
            self.ciphertext_tally.publish(),
            self.plaintext_tally,
            self.guardian_records,
            self.lagrange_coefficients,
            RESULTS_DIR,
        )
        self._assert_message(
            "Publish",
            f"Artifacts published to: {RESULTS_DIR}",
            path.exists(RESULTS_DIR),
        )

        self.deserialize_data()

        if self.REMOVE_OUTPUT:
            rmtree(RESULTS_DIR)

    def deserialize_data(self) -> None:
        """Ensure published data can be deserialized."""

        # Deserialize
        manifest_from_file = from_file_to_dataclass(
            Manifest,
            construct_path(MANIFEST_FILE_NAME, RESULTS_DIR),
        )
        self.assertEqualAsDicts(self.manifest, manifest_from_file)

        context_from_file = from_file_to_dataclass(
            CiphertextElectionContext, construct_path(CONTEXT_FILE_NAME, RESULTS_DIR)
        )
        self.assertEqualAsDicts(self.context, context_from_file)

        constants_from_file = from_file_to_dataclass(
            ElectionConstants, construct_path(CONSTANTS_FILE_NAME, RESULTS_DIR)
        )
        self.assertEqualAsDicts(self.constants, constants_from_file)

        coefficients_from_file = from_file_to_dataclass(
            LagrangeCoefficientsRecord,
            construct_path(COEFFICIENTS_FILE_NAME, RESULTS_DIR),
        )
        self.assertEqualAsDicts(self.lagrange_coefficients, coefficients_from_file)

        device_from_file = from_file_to_dataclass(
            EncryptionDevice,
            construct_path(DEVICE_PREFIX + str(self.device.device_id), DEVICES_DIR),
        )
        self.assertEqualAsDicts(self.device, device_from_file)

        for ballot in self.ballot_store.all():
            ballot_from_file = from_file_to_dataclass(
                SubmittedBallot,
                construct_path(BALLOT_PREFIX + ballot.object_id, BALLOTS_DIR),
            )
            self.assertEqualAsDicts(ballot, ballot_from_file)

        for spoiled_ballot in self.plaintext_spoiled_ballots.values():
            spoiled_ballot_from_file = from_file_to_dataclass(
                PlaintextTally,
                construct_path(BALLOT_PREFIX + spoiled_ballot.object_id, SPOILED_DIR),
            )
            self.assertEqualAsDicts(spoiled_ballot, spoiled_ballot_from_file)

        published_ciphertext_tally_from_file = from_file_to_dataclass(
            PublishedCiphertextTally,
            construct_path(ENCRYPTED_TALLY_FILE_NAME, RESULTS_DIR),
        )
        self.assertEqualAsDicts(
            self.ciphertext_tally.publish(),
            published_ciphertext_tally_from_file,
        )

        plainttext_tally_from_file = from_file_to_dataclass(
            PlaintextTally, construct_path(TALLY_FILE_NAME, RESULTS_DIR)
        )
        self.assertEqualAsDicts(self.plaintext_tally, plainttext_tally_from_file)

        for guardian_record in self.guardian_records:
            guardian_record_from_file = from_file_to_dataclass(
                GuardianRecord,
                construct_path(
                    GUARDIAN_PREFIX + guardian_record.guardian_id, GUARDIAN_DIR
                ),
            )
            self.assertEqualAsDicts(guardian_record, guardian_record_from_file)

    def _assert_message(
        self, name: str, message: str, condition: Union[Callable, bool] = True
    ) -> None:
        if callable(condition):
            result = condition()
        else:
            result = condition

        print(f"{name}: {message}: {result}")
        self.assertTrue(result)

    def assertEqualAsDicts(self, first: object, second: object):
        """
        Specialty assertEqual to compare dataclasses as dictionaries.

        This is relevant specifically to using pydantic dataclasses to import.
        Pydantic reconstructs dataclasses with name uniqueness to add their validation.
        This creates a naming issue where the default equality check fails.
        """
        self.assertEqual(asdict(first), asdict(second))


if __name__ == "__main__":
    print("Welcome to the ElectionGuard end-to-end test")
    TestEndToEndElection().test_end_to_end_election()
