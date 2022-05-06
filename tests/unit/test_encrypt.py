from unittest import TestCase

from electionguard.elgamal import elgamal_keypair_from_secret
from electionguard.encrypt import (
    ContestData,
    ContestErrorType,
    contest_from,
    encrypt_contest,
)
from electionguard.group import ONE_MOD_Q, TWO_MOD_Q, rand_q
from electionguard.manifest import (
    SelectionDescription,
    VoteVariationType,
    ContestDescriptionWithPlaceholders,
)
from electionguard.serialize import TruncationError, to_raw
from electionguard.utils import get_optional


def get_sample_contest_description() -> ContestDescriptionWithPlaceholders:
    ballot_selections = [
        SelectionDescription(
            "some-object-id-affirmative", 0, "some-candidate-id-affirmative"
        ),
        SelectionDescription(
            "some-object-id-negative", 1, "some-candidate-id-negative"
        ),
    ]
    placeholder_selections = [
        SelectionDescription(
            "some-object-id-placeholder", 2, "some-candidate-id-placeholder"
        )
    ]
    metadata = ContestDescriptionWithPlaceholders(
        "some-contest-object-id",
        0,
        "some-electoral-district-id",
        VoteVariationType.one_of_m,
        1,
        1,
        "some-referendum-contest-name",
        ballot_selections,
        None,
        None,
        placeholder_selections,
    )
    return metadata


class TestEncrypt(TestCase):
    """Test encryption"""

    def test_contest_data_conversion(self) -> None:
        """Test contest data encoding to padded to bytes then decoding."""

        # Arrange
        error = ContestErrorType.OverVote
        error_data = ["overvote-id-1", "overvote-id-2", "overvote-id-3"]
        write_ins = {
            "writein-id-1": "Teri Dactyl",
            "writein-id-2": "Allie Grater",
            "writein-id-3": "Anna Littlical",
            "writein-id-4": "Polly Wannakrakouer",
        }
        overflow_error_data = ["overflow-id" * 50]

        empty_contest_data = ContestData()
        write_in_contest_data = ContestData(write_ins=write_ins)
        overvote_contest_data = ContestData(error, error_data)
        overvote_and_write_in_contest_data = ContestData(error, error_data, write_ins)
        overflow_contest_data = ContestData(error, overflow_error_data, write_ins)

        # Act & Assert
        self._padding_cycle(empty_contest_data)
        self._padding_cycle(write_in_contest_data)
        self._padding_cycle(overvote_contest_data)
        self._padding_cycle(overvote_and_write_in_contest_data)
        self._padding_cycle(overflow_contest_data)

    def _padding_cycle(self, data: ContestData) -> None:
        """Run full cycle of padding and unpadding."""
        EXPECTED_PADDED_LENGTH = 512

        try:
            padded = data.to_bytes()
            unpadded = ContestData.from_bytes(padded)

            self.assertEqual(EXPECTED_PADDED_LENGTH, len(padded))
            self.assertEqual(data, unpadded)

        except TruncationError:
            # Validate JSON exceeds allowed length
            json = to_raw(data)
            self.assertLess(EXPECTED_PADDED_LENGTH, len(json))

    def test_encrypt_simple_contest_referendum_succeeds(self) -> None:
        # Arrange
        keypair = get_optional(elgamal_keypair_from_secret(TWO_MOD_Q))
        nonce = rand_q()
        encryption_seed = ONE_MOD_Q
        contest_description = get_sample_contest_description()
        contest = contest_from(contest_description)
        contest_hash = contest_description.crypto_hash()

        # Act
        encrypted_contest = encrypt_contest(
            contest,
            contest_description,
            keypair.public_key,
            encryption_seed,
            nonce,
            should_verify_proofs=True,
        )

        # Assert
        self.assertIsNotNone(encrypted_contest)
        if encrypted_contest is not None:
            self.assertTrue(
                encrypted_contest.is_valid_encryption(
                    contest_hash, keypair.public_key, encryption_seed
                )
            )

    def test_contest_encrypt_with_overvotes(self) -> None:

        # Arrange
        keypair = get_optional(elgamal_keypair_from_secret(TWO_MOD_Q))
        nonce = rand_q()
        encryption_seed = ONE_MOD_Q
        contest_description = get_sample_contest_description()
        contest = contest_from(contest_description)
        contest_hash = contest_description.crypto_hash()

        # Add Overvotes
        for selection in contest.ballot_selections:
            selection.vote = 1

        # Act
        encrypted_contest = encrypt_contest(
            contest,
            contest_description,
            keypair.public_key,
            encryption_seed,
            nonce,
            should_verify_proofs=True,
        )

        # Assert
        self.assertIsNotNone(encrypted_contest)
        self.assertIsNotNone(encrypted_contest.extended_data)
        self.assertTrue(
            encrypted_contest.is_valid_encryption(
                contest_hash, keypair.public_key, encryption_seed
            )
        )

        # Act
        decrypted_data = get_optional(
            encrypted_contest.extended_data.decrypt(keypair.secret_key, encryption_seed)
        )
        contest_data = ContestData.from_bytes(decrypted_data)

        # Assert
        self.assertIsNotNone(contest_data)
        self.assertIsNotNone(contest_data.error)
        self.assertIsNotNone(contest_data.error_data)
        self.assertEqual(contest_data.error, ContestErrorType.OverVote)
        self.assertGreater(len(contest_data.error_data), 0)

    def test_contest_encrypt_with_write_ins(self):

        # Arrange
        keypair = get_optional(elgamal_keypair_from_secret(TWO_MOD_Q))
        nonce = rand_q()
        encryption_seed = ONE_MOD_Q
        contest_description = get_sample_contest_description()
        contest = contest_from(contest_description)
        contest_hash = contest_description.crypto_hash()

        # Add Write-ins
        for selection in contest.ballot_selections:
            selection.write_in = "write_in"

        # Act
        encrypted_contest = encrypt_contest(
            contest,
            contest_description,
            keypair.public_key,
            encryption_seed,
            nonce,
            should_verify_proofs=True,
        )

        # Assert
        self.assertIsNotNone(encrypted_contest)
        self.assertIsNotNone(encrypted_contest.extended_data)
        self.assertTrue(
            encrypted_contest.is_valid_encryption(
                contest_hash, keypair.public_key, encryption_seed
            )
        )

        # Act
        decrypted_data = get_optional(
            encrypted_contest.extended_data.decrypt(keypair.secret_key, encryption_seed)
        )
        contest_data = ContestData.from_bytes(decrypted_data)

        # Assert
        self.assertIsNotNone(contest_data)
        self.assertIsNotNone(contest_data.write_ins)
        if contest_data is not None and contest_data.write_ins is not None:
            self.assertGreater(len(contest_data.write_ins), 0)
