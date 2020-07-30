from os import path
from typing import Iterable

from .ballot import CiphertextBallot
from .election import CiphertextElectionContext, ElectionConstants, ElectionDescription
from .encrypt import EncryptionDevice
from .key_ceremony import CoefficientValidationSet
from .serializable import set_serializers
from .tally import CiphertextTally, PlaintextTally
from .utils import make_directory

RESULTS_DIR = "results"
DEVICES_DIR = path.join(RESULTS_DIR, "devices")
COEFFICIENTS_DIR = path.join(RESULTS_DIR, "coefficients")
BALLOTS_DIR = path.join(RESULTS_DIR, "encrypted_ballots")
SPOILED_DIR = path.join(RESULTS_DIR, "spoiled_ballots")

DESCRIPTION_FILE_NAME = "description"
CONTEXT_FILE_NAME = "context"
CONSTANTS_FILE_NAME = "constants"
ENCRYPTED_TALLY_FILE_NAME = "encrypted_tally"
TALLY_FILE_NAME = "tally"

DEVICE_PREFIX = "device_"
COEFFICIENT_PREFIX = "coefficient_validation_set_"
BALLOT_PREFIX = "ballot_"


def publish(
    description: ElectionDescription,
    context: CiphertextElectionContext,
    constants: ElectionConstants,
    devices: Iterable[EncryptionDevice],
    ciphertext_ballots: Iterable[CiphertextBallot],
    ciphertext_tally: CiphertextTally,
    plaintext_tally: PlaintextTally,
    coefficient_validation_sets: Iterable[CoefficientValidationSet] = None,
    results_directory: str = RESULTS_DIR,
) -> None:
    """Publishes the election record as json"""

    set_serializers()

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
    for ballot in ciphertext_tally.spoiled_ballots.values():
        ballot_name = BALLOT_PREFIX + ballot.object_id
        ballot.to_json_file(ballot_name, SPOILED_DIR)

    ciphertext_tally.to_json_file(ENCRYPTED_TALLY_FILE_NAME, results_directory)
    plaintext_tally.to_json_file(TALLY_FILE_NAME, results_directory)
