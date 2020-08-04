import os
import shutil
from datetime import timedelta
from os import remove, path, mkdir
from typing import Type, TypeVar, List
from unittest import TestCase

from hypothesis import settings, HealthCheck, Phase, given
from hypothesis.strategies import integers

from electionguard.ballot import (
    from_ciphertext_ballot,
    BallotBoxState,
    CiphertextAcceptedBallot,
    _list_eq,
)
from electionguard.election import (
    CiphertextElectionContext,
    ElectionConstants,
    ElectionDescription,
)
from electionguard.encrypt import encrypt_ballot
from electionguard.group import ElementModQ
from electionguard.logs import log_info, log_error
from electionguard.nonces import Nonces
from electionguard.serializable import (
    set_deserializers,
    set_serializers,
    write_json_file,
)
from electionguard.utils import make_directory
from electionguardtest.election import (
    elections_and_ballots,
    ELECTIONS_AND_BALLOTS_TUPLE_TYPE,
)
from electionguardtest.group import elements_mod_q


class TestSerializable(TestCase):
    def test_write_json_file(self) -> None:
        # Arrange
        json_data = '{ "test" : 1 }'
        file_name = "json_write_test"
        json_file = file_name + ".json"

        # Act
        write_json_file(json_data, file_name)

        # Assert
        with open(json_file) as reader:
            self.assertEqual(reader.read(), json_data)

        # Cleanup
        remove(json_file)

    def test_setup_serialization(self) -> None:
        # Act
        set_serializers()

    def test_setup_deserialization(self) -> None:
        # Act
        set_deserializers()

    @settings(
        deadline=timedelta(milliseconds=10000),
        suppress_health_check=[HealthCheck.too_slow],
        max_examples=5,
        # disabling the "shrink" phase, because it runs very slowly
        phases=[Phase.explicit, Phase.reuse, Phase.generate, Phase.target],
    )
    @given(
        integers(1, 3).flatmap(lambda n: elections_and_ballots(n)), elements_mod_q(),
    )
    def test_eg_serialization(
        self, everything: ELECTIONS_AND_BALLOTS_TUPLE_TYPE, seed_hash: ElementModQ,
    ):
        # This test generates a few encrypted ballots, writes them and their associated
        # metadata out to the filesystem, then reads them all back in again. The goal is
        # to make sure that writing data out and reading it back yields the original data.

        # This exercises serialization / deserialization as well as the equality methods.

        # Not here: any exercise of CiphertextTally or related classes. That should be
        # a separate test.

        election_description, ied, ballots, secret_key, context = everything

        num_ballots = len(ballots)
        nonces = Nonces(seed_hash)[:num_ballots]
        self.assertEqual(len(nonces), num_ballots)
        self.assertTrue(len(ied.contests) > 0)

        encrypted_ballots = [
            from_ciphertext_ballot(
                encrypt_ballot(ballot, ied, context, seed_hash, nonce),
                BallotBoxState.CAST,
            )
            for ballot, nonce in zip(ballots, nonces)
        ]

        # write everything out to disk
        results_dir = "serialization_testing"

        try:
            shutil.rmtree(results_dir)
        except FileNotFoundError:
            pass

        set_serializers()
        set_deserializers()

        log_info(f"test_eg_serialization: writing to {results_dir}")
        if not path.exists(results_dir):
            mkdir(results_dir)

        ELECTION_DESCRIPTION = "election_description"
        CRYPTO_CONSTANTS = "constants"
        CRYPTO_CONTEXT = "cryptographic_context"

        log_info("test_eg_serialization: writing election metadata")
        election_description.to_json_file(ELECTION_DESCRIPTION, results_dir)

        log_info("test_eg_serialization: writing crypto context")
        context.to_json_file(CRYPTO_CONTEXT, results_dir)

        log_info("test_eg_serialization: writing crypto constants")
        constants = ElectionConstants()
        constants.to_json_file(CRYPTO_CONSTANTS, results_dir)

        log_info("test_eg_serialization: writing ballots")
        ballots_dir = path.join(results_dir, "ballots")
        make_directory(ballots_dir)
        for ballot in encrypted_ballots:
            ballot.to_json_file(ballot.object_id, ballots_dir)

        # read everything back in again
        if not path.exists(results_dir):
            log_error(f"Path ({results_dir}) not found, cannot load the fast-tally")
            return None

        election_description2 = _load_helper(
            results_dir, ELECTION_DESCRIPTION, ElectionDescription
        )

        self.assertEqual(election_description, election_description2)

        constants2: ElectionConstants = _load_helper(
            results_dir, CRYPTO_CONSTANTS, ElectionConstants
        )
        self.assertEqual(constants, constants2)

        context2 = _load_helper(results_dir, CRYPTO_CONTEXT, CiphertextElectionContext)
        self.assertEqual(context, context2)

        ballots_dir = path.join(results_dir, "ballots")
        ballot_files = _all_filenames(ballots_dir)

        encrypted_ballots2: List[CiphertextAcceptedBallot] = [
            _load_helper(".", s, CiphertextAcceptedBallot, file_suffix="")
            for s in ballot_files
        ]
        self.assertTrue(_list_eq(encrypted_ballots, encrypted_ballots2))

        # final cleanup: delete the directory used for the tests
        try:
            shutil.rmtree(results_dir)
        except FileNotFoundError:
            pass


T = TypeVar("T")


def _load_helper(
    dir_name: str, file_prefix: str, class_handle: Type[T], file_suffix: str = ".json",
) -> T:
    # This method is fine for its use in the above tests, but can raise a variety of exceptions
    # if something goes wrong. Additional error handling would be necessary to use this in
    # production code.

    filename = path.join(dir_name, file_prefix + file_suffix)
    s = os.stat(filename)
    if s.st_size == 0:
        log_error(f"The file ({filename}) is empty")
        return None

    with open(filename, "r") as subject:
        data = subject.read()
        return class_handle.from_json(data)


def _all_filenames(root_dir: str) -> List[str]:
    results: List[str] = []
    for root, dirs, files in os.walk(root_dir):
        for file in files:
            results.append(path.join(root, file))
    return results
