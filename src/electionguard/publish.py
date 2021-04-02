from os import path
from typing import Iterable

from .ballot import PlaintextBallot, CiphertextBallot, SubmittedBallot
from .guardian import GuardianRecord
from .election import CiphertextElectionContext, ElectionConstants
from .encrypt import EncryptionDevice
from .manifest import Manifest
from .tally import PlaintextTally, PublishedCiphertextTally
from .utils import make_directory

RESULTS_DIR = "results"
MANIFEST_FILE_NAME = "manifest"
CONTEXT_FILE_NAME = "context"
CONSTANTS_FILE_NAME = "constants"
ENCRYPTED_TALLY_FILE_NAME = "encrypted_tally"
TALLY_FILE_NAME = "tally"

DEVICE_PREFIX = "device_"
COEFFICIENT_PREFIX = "coefficient_validation_set_"
BALLOT_PREFIX = "ballot_"

PLAINTEXT_BALLOT_PREFIX = "plaintext_ballot_"
GUARDIAN_PREFIX = "guardian_"

# TODO #148 Revert PlaintextTally to PublishedPlaintextTally after moving spoiled info
def publish(
    manifest: Manifest,
    context: CiphertextElectionContext,
    constants: ElectionConstants,
    devices: Iterable[EncryptionDevice],
    ciphertext_ballots: Iterable[SubmittedBallot],
    spoiled_ballots: Iterable[PlaintextTally],
    ciphertext_tally: PublishedCiphertextTally,
    plaintext_tally: PlaintextTally,
    guardian_records: Iterable[GuardianRecord],
    results_directory: str = RESULTS_DIR,
) -> None:
    """Publishes the election record as json"""

    devices_directory = path.join(results_directory, "devices")
    guardian_directory = path.join(results_directory, "guardians")
    ballots_directory = path.join(results_directory, "encrypted_ballots")
    spoiled_directory = path.join(results_directory, "spoiled_ballots")

    make_directory(results_directory)
    manifest.to_json_file(MANIFEST_FILE_NAME, results_directory)
    context.to_json_file(CONTEXT_FILE_NAME, results_directory)
    constants.to_json_file(CONSTANTS_FILE_NAME, results_directory)

    make_directory(devices_directory)
    for device in devices:
        device_name = DEVICE_PREFIX + str(device.uuid)
        device.to_json_file(device_name, devices_directory)

    make_directory(guardian_directory)
    if guardian_records is not None:
        for guardian_record in guardian_records:
            set_name = COEFFICIENT_PREFIX + guardian_record.guardian_id
            guardian_record.to_json_file(set_name, guardian_directory)

    make_directory(ballots_directory)
    for ballot in ciphertext_ballots:
        name = BALLOT_PREFIX + ballot.object_id
        ballot.to_json_file(name, ballots_directory)

    make_directory(spoiled_directory)
    for spoiled_ballot in spoiled_ballots:
        name = BALLOT_PREFIX + spoiled_ballot.object_id
        spoiled_ballot.to_json_file(name, spoiled_directory)

    ciphertext_tally.to_json_file(ENCRYPTED_TALLY_FILE_NAME, results_directory)
    plaintext_tally.to_json_file(TALLY_FILE_NAME, results_directory)


def publish_private_data(
    plaintext_ballots: Iterable[PlaintextBallot],
    ciphertext_ballots: Iterable[CiphertextBallot],
    guardian_records: Iterable[GuardianRecord],
    results_directory: str = RESULTS_DIR,
) -> None:
    """
    Publish the private data for an election.
    Useful for generating sample data sets.
    Do not use this in a production application.
    """

    private_directory = path.join(results_directory, "private")
    plaintext_ballots_directory = path.join(private_directory, "plaintext")
    encrypted_ballots_directory = path.join(private_directory, "encrypted")

    make_directory(results_directory)
    make_directory(private_directory)

    for guardian_record in guardian_records:
        guardian_name = GUARDIAN_PREFIX + guardian_record.guardian_id
        guardian_record.to_json_file(
            guardian_name, private_directory, strip_privates=False
        )

    make_directory(plaintext_ballots_directory)
    for plaintext_ballot in plaintext_ballots:
        name = PLAINTEXT_BALLOT_PREFIX + plaintext_ballot.object_id
        plaintext_ballot.to_json_file(name, plaintext_ballots_directory)

    make_directory(encrypted_ballots_directory)
    for ciphertext_ballot in ciphertext_ballots:
        name = BALLOT_PREFIX + ciphertext_ballot.object_id
        ciphertext_ballot.to_json_file(name, encrypted_ballots_directory)
