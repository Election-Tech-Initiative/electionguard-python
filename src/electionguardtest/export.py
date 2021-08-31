"""
Sample generation tool to export data from the election.

Specifically constructed to assist with creating sample data.
The export here is by no means exhaustive or prescriptive of how one
may choose to export the data for publishing the election.

Refer to the ElectionGuard spec for any specifics.
"""

from os import path
from typing import Iterable

from electionguard.ballot import PlaintextBallot, CiphertextBallot, SubmittedBallot
from electionguard.constants import ElectionConstants
from electionguard.election_polynomial import LagrangeCoefficientsRecord
from electionguard.guardian import GuardianRecord, PrivateGuardianRecord
from electionguard.election import CiphertextElectionContext
from electionguard.encrypt import EncryptionDevice
from electionguard.manifest import Manifest
from electionguard.tally import PlaintextTally, PublishedCiphertextTally

from .serialize import to_file

RESULTS_DIR = "results"
MANIFEST_FILE_NAME = "manifest"
CONTEXT_FILE_NAME = "context"
CONSTANTS_FILE_NAME = "constants"
COEFFICIENTS_FILE_NAME = "coefficients"
ENCRYPTED_TALLY_FILE_NAME = "encrypted_tally"
TALLY_FILE_NAME = "tally"

DEVICE_PREFIX = "device_"
BALLOT_PREFIX = "ballot_"

PLAINTEXT_BALLOT_PREFIX = "plaintext_ballot_"
GUARDIAN_PREFIX = "guardian_"


# TODO #148 Revert PlaintextTally to PublishedPlaintextTally after moving spoiled info
def export(
    manifest: Manifest,
    context: CiphertextElectionContext,
    constants: ElectionConstants,
    devices: Iterable[EncryptionDevice],
    ciphertext_ballots: Iterable[SubmittedBallot],
    spoiled_ballots: Iterable[PlaintextTally],
    ciphertext_tally: PublishedCiphertextTally,
    plaintext_tally: PlaintextTally,
    guardian_records: Iterable[GuardianRecord],
    lagrange_coefficients: LagrangeCoefficientsRecord,
    results_directory: str = RESULTS_DIR,
) -> None:
    """Export the data required to publish the election record as json."""
    devices_directory = path.join(results_directory, "devices")
    guardian_directory = path.join(results_directory, "guardians")
    ballots_directory = path.join(results_directory, "encrypted_ballots")
    spoiled_directory = path.join(results_directory, "spoiled_ballots")

    to_file(manifest, MANIFEST_FILE_NAME, results_directory)
    to_file(context, CONTEXT_FILE_NAME, results_directory)
    to_file(constants, CONSTANTS_FILE_NAME, results_directory)
    to_file(lagrange_coefficients, COEFFICIENTS_FILE_NAME, results_directory)

    for device in devices:
        to_file(device, DEVICE_PREFIX + str(device.device_id), devices_directory)

    if guardian_records is not None:
        for guardian_record in guardian_records:
            to_file(
                guardian_record,
                GUARDIAN_PREFIX + guardian_record.guardian_id,
                guardian_directory,
            )

    for ballot in ciphertext_ballots:
        to_file(ballot, BALLOT_PREFIX + ballot.object_id, ballots_directory)

    for spoiled_ballot in spoiled_ballots:
        to_file(
            spoiled_ballot, BALLOT_PREFIX + spoiled_ballot.object_id, spoiled_directory
        )

    to_file(ciphertext_tally, ENCRYPTED_TALLY_FILE_NAME, results_directory)
    to_file(plaintext_tally, TALLY_FILE_NAME, results_directory)


def export_private_data(
    plaintext_ballots: Iterable[PlaintextBallot],
    ciphertext_ballots: Iterable[CiphertextBallot],
    private_guardian_records: Iterable[PrivateGuardianRecord],
    results_directory: str = RESULTS_DIR,
) -> None:
    """Export the private data for an election.

    Useful for generating sample data sets.
    WARNING: DO NOT USE this in a production application.
    """
    private_directory = path.join(results_directory, "private")
    gaurdians_directory = path.join(private_directory, "guardians")
    plaintext_ballots_directory = path.join(private_directory, "plaintext")
    encrypted_ballots_directory = path.join(private_directory, "encrypted")

    for private_guardian_record in private_guardian_records:
        to_file(
            private_guardian_record,
            GUARDIAN_PREFIX + private_guardian_record.guardian_id,
            gaurdians_directory,
        )

    for plaintext_ballot in plaintext_ballots:
        to_file(
            plaintext_ballot,
            PLAINTEXT_BALLOT_PREFIX + plaintext_ballot.object_id,
            plaintext_ballots_directory,
        )

    for ciphertext_ballot in ciphertext_ballots:
        to_file(
            ciphertext_ballot,
            BALLOT_PREFIX + ciphertext_ballot.object_id,
            encrypted_ballots_directory,
        )
