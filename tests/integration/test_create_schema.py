import json
from unittest import TestCase
from shutil import rmtree

from electionguard.constants import ElectionConstants
from electionguard.election import CiphertextElectionContext
from electionguard.guardian import GuardianRecord
from electionguard.manifest import Manifest
from electionguard.ballot import (
    CiphertextBallot,
    PlaintextBallot,
    SubmittedBallot,
)
from electionguard.ballot_compact import CompactPlaintextBallot, CompactSubmittedBallot
from electionguard.election_polynomial import LagrangeCoefficientsRecord
from electionguard.encrypt import EncryptionDevice
from electionguard.tally import (
    PublishedCiphertextTally,
    PlaintextTally,
)
from electionguard.serialize import construct_path, get_schema, to_file


class TestCreateSchema(TestCase):
    """Test creating schema."""

    schema_dir = "schemas"
    remove_schema = False

    # TODO Fix Pydantic errors with json schema
    resolve_pydantic_errors = False

    def test_create_schema(self) -> None:

        to_file(
            json.loads((get_schema(CiphertextElectionContext))),
            construct_path("context_schema"),
            self.schema_dir,
        )

        to_file(
            json.loads(get_schema(ElectionConstants)),
            construct_path("constants_schema"),
            self.schema_dir,
        )

        to_file(
            json.loads(get_schema(EncryptionDevice)),
            construct_path("device_schema"),
            self.schema_dir,
        )

        to_file(
            json.loads(get_schema(LagrangeCoefficientsRecord)),
            construct_path("coefficients_schema"),
            self.schema_dir,
        )

        if self.resolve_pydantic_errors:
            to_file(
                json.loads(get_schema(Manifest)),
                construct_path("manifest_schema"),
                self.schema_dir,
            )
            to_file(
                json.loads(get_schema(GuardianRecord)),
                construct_path("guardian_schema"),
                self.schema_dir,
            )
            to_file(
                json.loads(get_schema(PlaintextBallot)),
                construct_path("plaintext_ballot_schema"),
                self.schema_dir,
            )
            to_file(
                json.loads(get_schema(CiphertextBallot)),
                construct_path("ciphertext_ballot_schema"),
                self.schema_dir,
            )
            to_file(
                json.loads(get_schema(SubmittedBallot)),
                construct_path("submitted_ballot_schema"),
                self.schema_dir,
            )
            to_file(
                json.loads(get_schema(CompactPlaintextBallot)),
                construct_path("compact_plaintext_ballot_schema"),
                self.schema_dir,
            )
            to_file(
                json.loads(get_schema(CompactSubmittedBallot)),
                construct_path("compact_submitted_ballot_schema"),
                self.schema_dir,
            )
            to_file(
                json.loads(get_schema(PlaintextTally)),
                construct_path("plaintext_tally_schema"),
                self.schema_dir,
            )
            to_file(
                json.loads(get_schema(PublishedCiphertextTally)),
                construct_path("ciphertext_tally_schema"),
                self.schema_dir,
            )

        if self.remove_schema:
            rmtree(self.schema_dir)
