import click
from electionguard_cli.cli_models import BuildElectionResults, E2eSubmitResults
from electionguard_cli.cli_models.e2e_inputs import E2eInputs
from electionguard_cli.e2e_steps.e2e_step_base import E2eStepBase
from electionguard.constants import get_constants

from electionguard.serialize import from_file, construct_path
from electionguard_tools.helpers.export import (
    PRIVATE_DATA_DIR,
    ELECTION_RECORD_DIR,
    export_private_data,
    export_record,
)


class ElectionRecordStep(E2eStepBase):
    """Responsible for publishing an election record after an election has completed."""

    def run(
        self,
        election_inputs: E2eInputs,
        build_election_results: BuildElectionResults,
        submit_results: E2eSubmitResults,
    ) -> None:
        self.print_header("Election Record")
        click.echo(election_inputs.output_path)
        guardian_records = [
            guardian.publish() for guardian in election_inputs.guardians
        ]
        private_guardian_records = [
            guardian.export_private_data() for guardian in election_inputs.guardians
        ]

        constants = get_constants()
        # export_record(
        #     election_inputs.manifest,
        #     build_election_results.context,
        #     constants,
        #     [submit_results.device],
        #     submit_results.ballot_store.all(),
        #     plaintext_spoiled_ballots.values(),
        #     ciphertext_tally.publish(),
        #     plaintext_tally,
        #     guardian_records,
        #     lagrange_coefficients,
        # )
        # self._assert_message(
        #     "Publish",
        #     f"Election Record published to: {ELECTION_RECORD_DIR}",
        #     path.exists(ELECTION_RECORD_DIR),
        # )

        # export_private_data(
        #     self.plaintext_ballots,
        #     self.ciphertext_ballots,
        #     self.private_guardian_records,
        # )
        # self._assert_message(
        #     "Export private data",
        #     f"Private data exported to: {PRIVATE_DATA_DIR}",
        #     path.exists(PRIVATE_DATA_DIR),
        # )

        # ZIP_SUFFIX = "zip"
        # make_archive(ELECTION_RECORD_DIR, ZIP_SUFFIX, ELECTION_RECORD_DIR)
        # make_archive(PRIVATE_DATA_DIR, ZIP_SUFFIX, PRIVATE_DATA_DIR)

        # self.deserialize_data()

        # if self.REMOVE_RAW_OUTPUT:
        #     rmtree(ELECTION_RECORD_DIR)
        #     rmtree(PRIVATE_DATA_DIR)

        # if self.REMOVE_ZIP_OUTPUT:
        #     remove(f"{ELECTION_RECORD_DIR}.{ZIP_SUFFIX}")
        #     remove(f"{PRIVATE_DATA_DIR}.{ZIP_SUFFIX}")

    def deserialize_data(self) -> None:
        """Ensure published data can be deserialized."""

        # # Deserialize
        # manifest_from_file = from_file(
        #     Manifest,
        #     construct_path(MANIFEST_FILE_NAME, ELECTION_RECORD_DIR),
        # )
        # self.assertEqualAsDicts(self.manifest, manifest_from_file)

        # context_from_file = from_file(
        #     CiphertextElectionContext,
        #     construct_path(CONTEXT_FILE_NAME, ELECTION_RECORD_DIR),
        # )
        # self.assertEqualAsDicts(self.context, context_from_file)

        # constants_from_file = from_file(
        #     ElectionConstants, construct_path(CONSTANTS_FILE_NAME, ELECTION_RECORD_DIR)
        # )
        # self.assertEqualAsDicts(self.constants, constants_from_file)

        # coefficients_from_file = from_file(
        #     LagrangeCoefficientsRecord,
        #     construct_path(COEFFICIENTS_FILE_NAME, ELECTION_RECORD_DIR),
        # )
        # self.assertEqualAsDicts(self.lagrange_coefficients, coefficients_from_file)

        # device_from_file = from_file(
        #     EncryptionDevice,
        #     construct_path(
        #         DEVICE_PREFIX + str(self.device.device_id), devices_directory
        #     ),
        # )
        # self.assertEqualAsDicts(self.device, device_from_file)

        # for ballot in self.ballot_store.all():
        #     ballot_from_file = from_file(
        #         SubmittedBallot,
        #         construct_path(
        #             SUBMITTED_BALLOT_PREFIX + ballot.object_id,
        #             submitted_ballots_directory,
        #         ),
        #     )
        #     self.assertTrue(
        #         ballot_from_file.is_valid_encryption(
        #             self.internal_manifest.manifest_hash,
        #             self.context.elgamal_public_key,
        #             self.context.crypto_extended_base_hash,
        #         )
        #     )
        #     self.assertEqualAsDicts(ballot, ballot_from_file)

        # for spoiled_ballot in self.plaintext_spoiled_ballots.values():
        #     spoiled_ballot_from_file = from_file(
        #         PlaintextTally,
        #         construct_path(
        #             SPOILED_BALLOT_PREFIX + spoiled_ballot.object_id,
        #             spoiled_ballots_directory,
        #         ),
        #     )
        #     self.assertEqualAsDicts(spoiled_ballot, spoiled_ballot_from_file)

        # published_ciphertext_tally_from_file = from_file(
        #     PublishedCiphertextTally,
        #     construct_path(ENCRYPTED_TALLY_FILE_NAME, ELECTION_RECORD_DIR),
        # )
        # self.assertEqualAsDicts(
        #     self.ciphertext_tally.publish(),
        #     published_ciphertext_tally_from_file,
        # )

        # plainttext_tally_from_file = from_file(
        #     PlaintextTally, construct_path(TALLY_FILE_NAME, ELECTION_RECORD_DIR)
        # )
        # self.assertEqualAsDicts(self.plaintext_tally, plainttext_tally_from_file)

        # for guardian_record in self.guardian_records:
        #     guardian_record_from_file = from_file(
        #         GuardianRecord,
        #         construct_path(
        #             GUARDIAN_PREFIX + guardian_record.guardian_id, guardians_directory
        #         ),
        #     )
        #     self.assertEqualAsDicts(guardian_record, guardian_record_from_file)
