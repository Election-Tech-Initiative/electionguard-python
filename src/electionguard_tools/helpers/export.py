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
from electionguard.serialize import to_file
from electionguard.tally import PlaintextTally, PublishedCiphertextTally


# Public
ELECTION_RECORD_DIR = "election_record"
DEVICES_DIR = "encryption_devices"
GUARDIANS_DIR = "guardians"
SUBMITTED_BALLOTS_DIR = "submitted_ballots"
SPOILED_BALLOTS_DIR = "spoiled_ballots"

MANIFEST_FILE_NAME = "manifest"
CONTEXT_FILE_NAME = "context"
CONSTANTS_FILE_NAME = "constants"
COEFFICIENTS_FILE_NAME = "coefficients"
ENCRYPTED_TALLY_FILE_NAME = "encrypted_tally"
TALLY_FILE_NAME = "tally"
SUBMITTED_BALLOT_PREFIX = "submitted_ballot_"
SPOILED_BALLOT_PREFIX = "spoiled_ballot_"
DEVICE_PREFIX = "device_"
GUARDIAN_PREFIX = "guardian_"

# Private
PRIVATE_DATA_DIR = "election_private_data"
PLAINTEXT_BALLOT_PREFIX = "plaintext_ballot_"
CIPHERTEXT_BALLOT_PREFIX = "ciphertext_ballot_"
PRIVATE_GUARDIAN_PREFIX = "private_guardian_"


# TODO #148 Revert PlaintextTally to PublishedPlaintextTally after moving spoiled info
def export_record(
    manifest: Manifest,
    context: CiphertextElectionContext,
    constants: ElectionConstants,
    devices: Iterable[EncryptionDevice],
    submitted_ballots: Iterable[SubmittedBallot],
    spoiled_ballots: Iterable[PlaintextTally],
    ciphertext_tally: PublishedCiphertextTally,
    plaintext_tally: PlaintextTally,
    guardian_records: Iterable[GuardianRecord],
    lagrange_coefficients: LagrangeCoefficientsRecord,
    election_record_directory: str = ELECTION_RECORD_DIR,
) -> None:
    """Export a publishable election record"""
    devices_directory = path.join(election_record_directory, DEVICES_DIR)
    guardian_directory = path.join(election_record_directory, GUARDIANS_DIR)
    ballots_directory = path.join(election_record_directory, SUBMITTED_BALLOTS_DIR)
    spoiled_directory = path.join(election_record_directory, SPOILED_BALLOTS_DIR)

    to_file(manifest, MANIFEST_FILE_NAME, election_record_directory)
    to_file(context, CONTEXT_FILE_NAME, election_record_directory)
    to_file(constants, CONSTANTS_FILE_NAME, election_record_directory)
    to_file(lagrange_coefficients, COEFFICIENTS_FILE_NAME, election_record_directory)

    for device in devices:
        to_file(device, DEVICE_PREFIX + str(device.device_id), devices_directory)

    if guardian_records is not None:
        for guardian_record in guardian_records:
            to_file(
                guardian_record,
                GUARDIAN_PREFIX + guardian_record.guardian_id,
                guardian_directory,
            )

    for ballot in submitted_ballots:
        to_file(ballot, SUBMITTED_BALLOT_PREFIX + ballot.object_id, ballots_directory)

    for spoiled_ballot in spoiled_ballots:
        to_file(
            spoiled_ballot,
            SPOILED_BALLOT_PREFIX + spoiled_ballot.object_id,
            spoiled_directory,
        )

    to_file(ciphertext_tally, ENCRYPTED_TALLY_FILE_NAME, election_record_directory)
    to_file(plaintext_tally, TALLY_FILE_NAME, election_record_directory)


def export_private_data(
    plaintext_ballots: Iterable[PlaintextBallot],
    ciphertext_ballots: Iterable[CiphertextBallot],
    private_guardian_records: Iterable[PrivateGuardianRecord],
    private_directory: str = PRIVATE_DATA_DIR,
) -> None:
    """Export non-publishable private data for an election.

    Useful for generating sample data sets.
    WARNING: DO NOT USE this in a production application.
    """
    gaurdians_directory = path.join(private_directory, "private_guardians")
    plaintext_ballots_directory = path.join(private_directory, "plaintext_ballots")
    encrypted_ballots_directory = path.join(private_directory, "ciphertext_ballots")

    for private_guardian_record in private_guardian_records:
        to_file(
            private_guardian_record,
            PRIVATE_GUARDIAN_PREFIX + private_guardian_record.guardian_id,
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
            CIPHERTEXT_BALLOT_PREFIX + ciphertext_ballot.object_id,
            encrypted_ballots_directory,
        )
