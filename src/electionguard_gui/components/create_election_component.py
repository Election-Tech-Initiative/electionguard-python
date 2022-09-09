from os import path
from shutil import make_archive, rmtree
from typing import Any
import eel
from electionguard.constants import get_constants
from electionguard.guardian import Guardian
from electionguard_cli.setup_election.output_setup_files_step import (
    OutputSetupFilesStep,
)
from electionguard_cli.setup_election.setup_election_builder_step import (
    SetupElectionBuilderStep,
)
from electionguard_gui.eel_utils import eel_fail, eel_success
from electionguard_gui.components.component_base import ComponentBase
from electionguard_gui.services import (
    KeyCeremonyService,
    GuiSetupInputRetrievalStep,
    ElectionService,
    GuardianService,
)
from electionguard_gui.services.directory_service import get_data_dir


class CreateElectionComponent(ComponentBase):
    """Responsible for functionality related to creating encryption packages for elections"""

    _COMPRESSION_FORMAT = "zip"

    _key_ceremony_service: KeyCeremonyService
    _setup_input_retrieval_step: GuiSetupInputRetrievalStep
    _setup_election_builder_step: SetupElectionBuilderStep
    _election_service: ElectionService
    _output_setup_files_step: OutputSetupFilesStep
    _guardian_service: GuardianService

    def __init__(
        self,
        key_ceremony_service: KeyCeremonyService,
        election_service: ElectionService,
        setup_input_retrieval_step: GuiSetupInputRetrievalStep,
        setup_election_builder_step: SetupElectionBuilderStep,
        output_setup_files_step: OutputSetupFilesStep,
        guardian_service: GuardianService,
    ) -> None:
        self._key_ceremony_service = key_ceremony_service
        self._setup_input_retrieval_step = setup_input_retrieval_step
        self._setup_election_builder_step = setup_election_builder_step
        self._election_service = election_service
        self._output_setup_files_step = output_setup_files_step
        self._guardian_service = guardian_service

    def expose(self) -> None:
        eel.expose(self.get_keys)
        eel.expose(self.create_election)

    def get_keys(self) -> dict[str, Any]:
        self._log.debug("Getting keys")
        db = self._db_service.get_db()
        completed_key_ceremonies = self._key_ceremony_service.get_completed(db)
        keys = [
            key_ceremony.to_id_name_dict() for key_ceremony in completed_key_ceremonies
        ]
        return eel_success(keys)

    def create_election(
        self, key_ceremony_id: str, election_name: str, manifest_raw: str, url: str
    ) -> dict[str, Any]:
        try:
            self._log.debug(
                f"Creating election key_ceremony_id: {key_ceremony_id}, "
                + f"election_name: {election_name}, "
                + f"url: {url}"
            )
            db = self._db_service.get_db()
            existing_elections = db.elections.find_one({"election_name": election_name})
            if existing_elections:
                fail_result: dict[str, Any] = eel_fail("Election already exists")
                return fail_result

            key_ceremony = self._key_ceremony_service.get(db, key_ceremony_id)

            guardians = [
                Guardian.from_public_key(
                    key_ceremony.guardian_count, key_ceremony.quorum, key
                )
                for key in key_ceremony.keys
            ]
            election_inputs = self._setup_input_retrieval_step.get_gui_inputs(
                key_ceremony.guardian_count,
                key_ceremony.quorum,
                guardians,
                url,
                manifest_raw,
            )
            joint_key = key_ceremony.get_joint_key()
            build_election_results = (
                self._setup_election_builder_step.build_election_for_setup(
                    election_inputs, joint_key
                )
            )

            temp_out_dir = path.join(get_data_dir(), "election_setup")
            self._output_setup_files_step.output(
                election_inputs, build_election_results, temp_out_dir, None
            )
            zip_file = path.join(
                get_data_dir(),
                "encryption_packages",
                key_ceremony_id,
                "public_encryption_package",
            )
            encryption_package_file = self._zip(temp_out_dir, zip_file)
            guardian_records = [
                guardian.publish() for guardian in election_inputs.guardians
            ]
            constants = get_constants()
            election_id = self._election_service.create_election(
                db,
                election_name,
                key_ceremony,
                election_inputs.manifest,
                build_election_results.context,
                constants,
                guardian_records,
                encryption_package_file,
                url,
            )
            return eel_success(election_id)
        # pylint: disable=broad-except
        except Exception as e:
            return self.handle_error(e)

    def _zip(self, dir_to_zip: str, zip_file_to_make: str) -> str:
        make_archive(zip_file_to_make, self._COMPRESSION_FORMAT, dir_to_zip)
        rmtree(dir_to_zip)
        self._log.debug(f"Temp zip file: {zip_file_to_make}.{self._COMPRESSION_FORMAT}")
        return f"{zip_file_to_make}.{self._COMPRESSION_FORMAT}"
