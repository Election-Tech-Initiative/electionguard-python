#!/usr/bin/env python

from typing import Callable, Dict, List, Union
from os import path
from shutil import rmtree
from unittest import TestCase

from random import randint

from electionguardtest.election_factory import ElectionFactory
from electionguardtest.ballot_factory import BallotFactory

from electionguard.utils import get_optional

# Step 0 - Configure Election
from electionguard.election import (
    ElectionConstants,
    ElectionDescription,
    InternalElectionDescription,
    CiphertextElectionContext,
)
from electionguard.election_builder import ElectionBuilder

# Step 1 - Key Ceremony
from electionguard.guardian import Guardian
from electionguard.key_ceremony import CoefficientValidationSet
from electionguard.key_ceremony_mediator import KeyCeremonyMediator

# Step 2 - Encrypt Votes
from electionguard.ballot import (
    BallotBoxState,
    CiphertextBallot,
    PlaintextBallot,
    CiphertextAcceptedBallot,
)
from electionguard.encrypt import EncryptionDevice
from electionguard.encrypt import EncryptionMediator

# Step 3 - Cast and Spoil
from electionguard.ballot_store import BallotStore
from electionguard.ballot_box import BallotBox

# Step 4 - Decrypt Tally
from electionguard.tally import (
    tally_ballots,
    CiphertextTally,
    PublishedCiphertextTally,
    PlaintextTally,
    publish_ciphertext_tally,
)
from electionguard.decryption_mediator import DecryptionMediator

# Step 5 - Publish and Verify
from electionguard.publish import (
    publish,
    DEVICE_PREFIX,
    COEFFICIENTS_DIR,
    COEFFICIENT_PREFIX,
    DEVICES_DIR,
    RESULTS_DIR,
    CONSTANTS_FILE_NAME,
    DESCRIPTION_FILE_NAME,
    CONTEXT_FILE_NAME,
    ENCRYPTED_TALLY_FILE_NAME,
    TALLY_FILE_NAME,
    SPOILED_DIR,
    BALLOTS_DIR,
    BALLOT_PREFIX,
)


class TestEndToEndElection(TestCase):
    """
    Test a complete simple example of executing an End-to-End encrypted election.
    In a real world scenario all of these steps would not be completed on the same machine.
    """

    NUMBER_OF_GUARDIANS = 5
    QUORUM = 3

    REMOVE_OUTPUT = False

    # Step 0 - Configure Election
    description: ElectionDescription
    election_builder: ElectionBuilder
    metadata: InternalElectionDescription
    context: CiphertextElectionContext
    constants: ElectionConstants

    # Step 1 - Key Ceremony
    mediator: KeyCeremonyMediator
    guardians: List[Guardian] = []
    coefficient_validation_sets: List[CoefficientValidationSet] = []

    # Step 2 - Encrypt Votes
    device: EncryptionDevice
    encrypter: EncryptionMediator
    plaintext_ballots: List[PlaintextBallot]
    ciphertext_ballots: List[CiphertextBallot] = []

    # Step 3 - Cast and Spoil
    ballot_store: BallotStore
    ballot_box: BallotBox

    # Step 4 - Decrypt Tally
    ciphertext_tally: CiphertextTally
    plaintext_tally: PlaintextTally
    decrypter: DecryptionMediator

    def test_end_to_end_election(self) -> None:
        """
        Execute the simplified end-to-end test demonstrating each component of the system.
        """
        self.step_0_configure_election()
        self.step_1_key_ceremony()
        self.step_2_encrypt_votes()
        self.step_3_cast_and_spoil()
        self.step_4_decrypt_tally()
        self.step_5_publish_and_verify()

    def step_0_configure_election(self) -> None:
        """
        To conduct an election, load an `ElectionDescription` file
        """

        # Load a pre-configured Election Description
        # TODO: replace with complex election
        self.description = ElectionFactory().get_simple_election_from_file()
        print(
            f"""
            {'-'*40}\n
            # Election Summary:
            # Scope: {self.description.election_scope_id}
            # Geopolitical Units: {len(self.description.geopolitical_units)}
            # Parties: {len(self.description.parties)}
            # Candidates: {len(self.description.candidates)}
            # Contests: {len(self.description.contests)}
            # Ballot Styles: {len(self.description.ballot_styles)}\n
            {'-'*40}\n
            """
        )
        self._assert_message(
            ElectionDescription.is_valid.__qualname__,
            "Verify that the input election meta-data is well-formed",
            self.description.is_valid(),
        )

        # Create an Election Builder
        self.election_builder = ElectionBuilder(
            self.NUMBER_OF_GUARDIANS, self.QUORUM, self.description
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
                Guardian("guardian_" + str(i), i, self.NUMBER_OF_GUARDIANS, self.QUORUM)
            )

        # Setup Mediator
        self.mediator = KeyCeremonyMediator(self.guardians[0].ceremony_details)

        # Attendance (Public Key Share)
        for guardian in self.guardians:
            self.mediator.announce(guardian)

        self._assert_message(
            KeyCeremonyMediator.all_guardians_in_attendance.__qualname__,
            "Confirms all guardians have shared their public keys",
            self.mediator.all_guardians_in_attendance(),
        )

        # Run the Key Ceremony process,
        # Which shares the keys among the guardians
        orchestrated = self.mediator.orchestrate()
        self._assert_message(
            KeyCeremonyMediator.orchestrate.__qualname__,
            "Executes the key exchange between guardians",
            orchestrated is not None,
        )

        self._assert_message(
            KeyCeremonyMediator.all_election_partial_key_backups_available.__qualname__,
            "Confirm sall guardians have shared their partial key backups",
            self.mediator.all_election_partial_key_backups_available(),
        )

        # Verification
        verified = self.mediator.verify()
        self._assert_message(
            KeyCeremonyMediator.verify.__qualname__,
            "Confirms all guardians truthfully executed the ceremony",
            verified,
        )

        self._assert_message(
            KeyCeremonyMediator.all_election_partial_key_verifications_received.__qualname__,
            "Confirms all guardians have submitted a verification of the backups of all other guardians",
            self.mediator.all_election_partial_key_verifications_received(),
        )

        self._assert_message(
            KeyCeremonyMediator.all_election_partial_key_backups_verified.__qualname__,
            "Confirms all guardians have verified the backups of all other guardians",
            self.mediator.all_election_partial_key_backups_verified(),
        )

        # Joint Key
        joint_key = self.mediator.publish_joint_key()
        self._assert_message(
            KeyCeremonyMediator.publish_joint_key.__qualname__,
            "Publishes the Joint Election Key",
            joint_key is not None,
        )

        # Save Validation Keys
        for guardian in self.guardians:
            self.coefficient_validation_sets.append(
                guardian.share_coefficient_validation_set()
            )

        # Build the Election
        self.election_builder.set_public_key(get_optional(joint_key))
        self.metadata, self.context = get_optional(self.election_builder.build())
        self.constants = ElectionConstants()

        # Move on to encrypting ballots

    def step_2_encrypt_votes(self) -> None:
        """
        Using the `CiphertextElectionContext` encrypt ballots for the election
        """

        # Configure the Encryption Device
        self.device = EncryptionDevice("polling-place-one")
        self.encrypter = EncryptionMediator(self.metadata, self.context, self.device)
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
        self.ballot_store = BallotStore()
        self.ballot_box = BallotBox(self.metadata, self.context, self.ballot_store)

        # Randomly cast or spoil the ballots
        for ballot in self.ciphertext_ballots:
            if randint(0, 1):
                accepted_ballot = self.ballot_box.cast(ballot)
            else:
                accepted_ballot = self.ballot_box.spoil(ballot)

            self._assert_message(
                BallotBox.__qualname__,
                f"Accepted Ballot Id: {ballot.object_id} state: {get_optional(accepted_ballot).state}",
                accepted_ballot is not None,
            )

    def step_4_decrypt_tally(self) -> None:
        """
        Homomorphically combine the selections made on all of the cast ballots
        and use the Available Guardians to decrypt the combined tally.
        In this way, no individual voter's cast ballot is ever decrypted drectly.
        """

        # Generate a Homomorphically Accumulated Tally of the ballots
        self.ciphertext_tally = get_optional(
            tally_ballots(self.ballot_store, self.metadata, self.context)
        )
        self._assert_message(
            tally_ballots.__qualname__,
            f"""
            - cast: {self.ciphertext_tally.count()} 
            - spoiled: {len(self.ciphertext_tally.spoiled_ballots)}
            Total: {len(self.ciphertext_tally)}
            """,
            self.ciphertext_tally is not None,
        )

        # Configure the Decryption
        self.decrypter = DecryptionMediator(
            self.metadata, self.context, self.ciphertext_tally
        )

        # Announce each guardian as present
        for guardian in self.guardians:
            decryption_share = self.decrypter.announce(guardian)
            self._assert_message(
                DecryptionMediator.announce.__qualname__,
                f"Guardian Present: {guardian.object_id}",
                decryption_share is not None,
            )

        # Get the Plain Text Tally
        self.plaintext_tally = get_optional(self.decrypter.get_plaintext_tally())
        self._assert_message(
            DecryptionMediator.get_plaintext_tally.__qualname__,
            "Tally Decrypted",
            self.plaintext_tally is not None,
        )

        # Now, compare the results
        self.compare_results()

    def compare_results(self) -> None:
        """
        Compare the results to ensure the decryption was done correctly
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
            for contest in self.metadata.contests
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
                        expected_plaintext_tally[
                            selection.object_id
                        ] += selection.to_int()

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
        for ballot_id, accepted_ballot in self.ciphertext_tally.spoiled_ballots.items():
            if accepted_ballot.state == BallotBoxState.SPOILED:
                for plaintext_ballot in self.plaintext_ballots:
                    if ballot_id == plaintext_ballot.object_id:
                        print(f"\nSpoiled Ballot: {ballot_id}")
                        for contest in plaintext_ballot.contests:
                            print(f"\n Contest: {contest.object_id}")
                            for selection in contest.ballot_selections:
                                expected = selection.to_int()
                                decrypted_selection = (
                                    self.plaintext_tally.spoiled_ballots[ballot_id][
                                        contest.object_id
                                    ].selections[selection.object_id]
                                )
                                self._assert_message(
                                    f"   - Selection: {selection.object_id}",
                                    f"expected: {expected}, actual: {decrypted_selection.tally}",
                                    expected == decrypted_selection.tally,
                                )

    def step_5_publish_and_verify(self) -> None:
        """Publish and verify steps of the election"""
        self.publish_results()
        self.verify_results()

        if self.REMOVE_OUTPUT:
            rmtree(RESULTS_DIR)

    def publish_results(self) -> None:
        """
        Publish results/artifacts of the election
        """
        publish(
            self.description,
            self.context,
            self.constants,
            [self.device],
            self.ballot_store.all(),
            self.ciphertext_tally.spoiled_ballots.values(),
            publish_ciphertext_tally(self.ciphertext_tally),
            self.plaintext_tally,
            self.coefficient_validation_sets,
        )
        self._assert_message(
            "Publish",
            f"Artifacts published to: {RESULTS_DIR}",
            path.exists(RESULTS_DIR),
        )

    def verify_results(self) -> None:
        """Verify results of election"""

        # Deserialize
        description_from_file = ElectionDescription.from_json_file(
            DESCRIPTION_FILE_NAME, RESULTS_DIR
        )
        self.assertEqual(self.description, description_from_file)

        context_from_file = CiphertextElectionContext.from_json_file(
            CONTEXT_FILE_NAME, RESULTS_DIR
        )
        self.assertEqual(self.context, context_from_file)

        constants_from_file = ElectionConstants.from_json_file(
            CONSTANTS_FILE_NAME, RESULTS_DIR
        )
        self.assertEqual(self.constants, constants_from_file)

        device_name = DEVICE_PREFIX + str(self.device.uuid)
        device_from_file = EncryptionDevice.from_json_file(device_name, DEVICES_DIR)
        self.assertEqual(self.device, device_from_file)

        ciphertext_ballots: List[CiphertextAcceptedBallot] = []
        for ballot in self.ballot_store.all():
            ballot_name = BALLOT_PREFIX + ballot.object_id
            ballot_from_file = CiphertextAcceptedBallot.from_json_file(
                ballot_name, BALLOTS_DIR
            )
            self.assertEqual(ballot, ballot_from_file)

        spoiled_ballots: List[CiphertextAcceptedBallot] = []
        for spoiled_ballot in self.ciphertext_tally.spoiled_ballots.values():
            ballot_name = BALLOT_PREFIX + spoiled_ballot.object_id
            spoiled_ballot_from_file = CiphertextAcceptedBallot.from_json_file(
                ballot_name, SPOILED_DIR
            )
            self.assertEqual(spoiled_ballot, spoiled_ballot_from_file)

        ciphertext_tally_from_file = PublishedCiphertextTally.from_json_file(
            ENCRYPTED_TALLY_FILE_NAME, RESULTS_DIR
        )
        self.assertEqual(
            publish_ciphertext_tally(self.ciphertext_tally), ciphertext_tally_from_file
        )

        plainttext_tally_from_file = PlaintextTally.from_json_file(
            TALLY_FILE_NAME, RESULTS_DIR
        )
        self.assertEqual(self.plaintext_tally, plainttext_tally_from_file)

        coefficient_validation_sets: List[CoefficientValidationSet] = []
        for coefficient_validation_set in self.coefficient_validation_sets:
            set_name = COEFFICIENT_PREFIX + coefficient_validation_set.owner_id
            coefficient_validation_set_from_file = (
                CoefficientValidationSet.from_json_file(set_name, COEFFICIENTS_DIR)
            )
            self.assertEqual(
                coefficient_validation_set, coefficient_validation_set_from_file
            )

    def _assert_message(
        self, name: str, message: str, condition: Union[Callable, bool] = True
    ) -> None:
        if callable(condition):
            result = condition()
        else:
            result = condition

        print(f"{name}: {message}: {result}")
        self.assertTrue(result)


if __name__ == "__main__":
    print(f"Welcome to the ElectionGuard end-to-end test")
    TestEndToEndElection().test_end_to_end_election()
