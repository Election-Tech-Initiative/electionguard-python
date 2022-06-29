import os
from unittest.mock import patch
from unittest import TestCase
from electionguard import PrimeOption

from electionguard.byte_padding import TruncationError
from electionguard.elgamal import (
    HashedElGamalCiphertext,
    elgamal_keypair_from_secret,
)
from electionguard.encrypt import (
    ContestData,
    ContestErrorType,
    contest_from,
    encrypt_contest,
)
from electionguard.group import ONE_MOD_Q, TWO_MOD_Q, ElementModP, ElementModQ, rand_q
from electionguard.manifest import (
    SelectionDescription,
    VoteVariationType,
    ContestDescriptionWithPlaceholders,
)
from electionguard.serialize import to_raw
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
        write_in_value = "write_in"

        # Add Write-ins
        for selection in contest.ballot_selections:
            selection.write_in = write_in_value

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
            for write_in in contest_data.write_ins.values():
                self.assertEqual(write_in, write_in_value)

    @patch.dict(os.environ, {"PRIME_OPTION": PrimeOption.Standard.value})
    def test_contest_data_integration(self) -> None:
        """Contest data encryption done with production primes to match other repositories."""

        # Arrange
        keypair = get_optional(
            elgamal_keypair_from_secret(
                ElementModQ(
                    "094CDA6CEB3332D62438B6D37BBA774D23C420FA019368671AD330AD50456603"
                )
            )
        )
        encryption_seed = ElementModQ(
            "6E418518C6C244CA58399C0F47A9C761BAE7B876F8F5360D8D15FCFF26A42BAA"
        )

        # pylint: disable=line-too-long
        encrypted_contest_data = HashedElGamalCiphertext(
            ElementModP(
                "C102BAB526517D74FE5D5C249E7F422993C0306C40A9398FBAD01A0D3547B50BDFD77C6EFC187C7B1FD7918A0B3C2A2FB0A3776A7240F9A75410569379B3D16877B547F52E79542C1129F6E369F2D006D0A1AA3919F0228CA07F5C9A4DFD1118A606AA4B7000F9EDC65963F130663FD4F7246F7CFE7A38F1E1DC9BC0698CAB881DCD5A75E6D7165B329C28D80B719D7A2ED50031A2448A4528275FF161F541CFE304A28CBE7193A4BF8676B2D4F2DE68F175C5B4BFD14B4B1D9868D00E0BD95B6491C96460159DEABF85239B10A7C86B3D975EF58BBF833C6ABFFF223DAF78C1AE4C6F64D084C4118F3B5A2618628FA18852BAB55DCE95C04FFCBBAF582D75C7B8B830424C74A8F8EACD154300FD67CF753EE14FCE94DDED95F1DD2C1386D92B3FF03A9D6EDEE0F67EC80C72E6425B4EA1C17D7B9CC5B2165905373A4E304496462CE2BA077F195302A39C52F0077CA682BC718074F928040D1A36F585AC187A741F51C843C5ED88BC5FB8B86ED96C42BCF84EDF833489D7D3AC407C6D0740CC94BA1D5B885EB430CE8C6017F8660A6C72F4378BF133AA663DBA36CAB967AAC0F7738478110ECEABAE3E914CB7A796C5394F7DF150940BEA43264765B34851ADE4E5F1F213C25DCF66D35BE92611555D8C05ACFDF1AC5CA82B7D7F0D9BE49596F8B7F3269D9887F40B4BAB5C3D2BA7049B6D2119C3D0D01501836203412869E0"
            ),
            "F8E994D157A065A1DB2DA5E38645C283F7CCB339E13F0DE29B83A4EFA2F4366C626FC8E318AF81DCB2E6083A598F8916A5FEEC3C1A1B8EBEB4081F3CB92FA86E000B4994B77EE173072D796D21EE771F4D8F50E7DC50A7945E35059F893DD0A67C53DF5A3439A89E990C5B7568912CD2655B39E943511E1B0DF8A8E1FEF4EAC3923A5B5DDF1A658335E97AA6EB12E4EEE1394D91548F3E8446E9BBF4207D873F54298B446A7D689FF60A6F60B3FC6B8319EC17FA424F0461949CD49B764C6360AC0D492696E43EE83A6A7CE7AEA4DDBA206F365AA81E918F63709DE796F0338CCD311360D97CDC821506D3EDB434922264966B8AF7E304A403E18384DDCF53AEF1FFC19A66FBCD9C2D04EFC8F2D456BE52DB9C460E3CA10AC4ABFE0B726E19A715546F1CD9CA89C57ED52DA9D78C30BEFE5FE99A8BDEA33B7C06EDFD4E92D514661CD55B99B54E5C468118E16F4827F78FB381845B093F202111E3B84CFCF8DAEE7948BA57698475F3EBC3729559835BF63AAB0F5659019965A2F0CF55E953B1CD37BCBED8EA0D5F161D461E03031BA7D0B042B978F7F6776DDFBCAA7145DE30BA24C29BDFA05C7CCF54D7DD58E75143A16F8619053FCF4DE7BDCCA031F0873A65ACCC56FE78F32B8FC192D2106CF1A1E5339A5C5657E6703D7F30F908CEEF05A84C67C426B187CBC1599FB334307146EAECB16774C5CB7630F4CB093E840086",
            "BBCDE57B7E92BB8607696E09FE629A2B9665D809649B751333023983C001C191",
        )

        # Act
        decrypted_contest_data = encrypted_contest_data.decrypt(
            keypair.secret_key, encryption_seed
        )

        contest_data = ContestData.from_bytes(decrypted_contest_data)

        self.assertIsNotNone(contest_data)
        self.assertEqual(contest_data.error, ContestErrorType.OverVote)
        self.assertEqual(len(contest_data.error_data), 3)
        self.assertEqual(len(contest_data.write_ins), 1)
        self.assertEqual(
            contest_data.write_ins["write-in-selection"], "Susan B. Anthony"
        )
