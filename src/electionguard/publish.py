from os import path
from typing import Iterable

from .ballot import PlaintextBallot, CiphertextBallot, CiphertextAcceptedBallot
from .guardian import Guardian
from .election import CiphertextElectionContext, ElectionConstants, ElectionDescription
from .encrypt import EncryptionDevice
from .key_ceremony import CoefficientValidationSet
from .tally import PlaintextTally, PublishedCiphertextTally
from .utils import make_directory

RESULTS_DIR = "results"
DEVICES_DIR = path.join(RESULTS_DIR, "devices")
COEFFICIENTS_DIR = path.join(RESULTS_DIR, "coefficients")
BALLOTS_DIR = path.join(RESULTS_DIR, "encrypted_ballots")
SPOILED_DIR = path.join(RESULTS_DIR, "spoiled_ballots")
PRIVATE_DIR = path.join(RESULTS_DIR, "private")
PLAINTEXT_BALLOTS_DIR = path.join(PRIVATE_DIR, "plaintext")
ENCRYPTED_BALLOTS_DIR = path.join(PRIVATE_DIR, "encrypted")

DESCRIPTION_FILE_NAME = "description"
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
    description: ElectionDescription,
    context: CiphertextElectionContext,
    constants: ElectionConstants,
    devices: Iterable[EncryptionDevice],
    ciphertext_ballots: Iterable[CiphertextAcceptedBallot],
    spoiled_ballots: Iterable[CiphertextAcceptedBallot],
    ciphertext_tally: PublishedCiphertextTally,
    plaintext_tally: PlaintextTally,
    coefficient_validation_sets: Iterable[CoefficientValidationSet] = None,
    results_directory: str = RESULTS_DIR,
) -> None:
    """Publishes the election record as json"""

    make_directory(results_directory)
    description.to_json_file(DESCRIPTION_FILE_NAME, results_directory)
    context.to_json_file(CONTEXT_FILE_NAME, results_directory)
    constants.to_json_file(CONSTANTS_FILE_NAME, results_directory)

    make_directory(DEVICES_DIR)
    for device in devices:
        device_name = DEVICE_PREFIX + str(device.uuid)
        device.to_json_file(device_name, DEVICES_DIR)

    make_directory(COEFFICIENTS_DIR)
    if coefficient_validation_sets is not None:
        for coefficient_validation_set in coefficient_validation_sets:
            set_name = COEFFICIENT_PREFIX + coefficient_validation_set.owner_id
            coefficient_validation_set.to_json_file(set_name, COEFFICIENTS_DIR)

    make_directory(BALLOTS_DIR)
    for ballot in ciphertext_ballots:
        ballot_name = BALLOT_PREFIX + ballot.object_id
        ballot.to_json_file(ballot_name, BALLOTS_DIR)

    make_directory(SPOILED_DIR)
    for ballot in spoiled_ballots:
        ballot_name = BALLOT_PREFIX + ballot.object_id
        ballot.to_json_file(ballot_name, SPOILED_DIR)

    ciphertext_tally.to_json_file(ENCRYPTED_TALLY_FILE_NAME, results_directory)
    plaintext_tally.to_json_file(TALLY_FILE_NAME, results_directory)


def publish_private_data(
    plaintext_ballots: Iterable[PlaintextBallot],
    ciphertext_ballots: Iterable[CiphertextBallot],
    guardians: Iterable[Guardian],
    results_directory: str = RESULTS_DIR,
) -> None:
    """
    Publish the private data for an election.  
    Useful for generating sample data sets.  
    Do not use this in a production application.
    """

    make_directory(results_directory)
    make_directory(PRIVATE_DIR)

    for guardian in guardians:
        guardian_name = GUARDIAN_PREFIX + guardian.object_id
        guardian.to_json_file(guardian_name, PRIVATE_DIR, strip_privates=False)

    make_directory(PLAINTEXT_BALLOTS_DIR)
    for plaintext_ballot in plaintext_ballots:
        ballot_name = PLAINTEXT_BALLOT_PREFIX + plaintext_ballot.object_id
        plaintext_ballot.to_json_file(ballot_name, PLAINTEXT_BALLOTS_DIR)

    make_directory(ENCRYPTED_BALLOTS_DIR)
    for ciphertext_ballot in ciphertext_ballots:
        ballot_name = BALLOT_PREFIX + ciphertext_ballot.object_id
        ciphertext_ballot.to_json_file(ballot_name, ENCRYPTED_BALLOTS_DIR)
