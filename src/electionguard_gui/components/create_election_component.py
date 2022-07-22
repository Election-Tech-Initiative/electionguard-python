from tempfile import gettempdir
from typing import Any
import eel
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
)


class CreateElectionComponent(ComponentBase):
    """Responsible for functionality related to creating encryption packages for elections"""

    _key_ceremony_service: KeyCeremonyService
    _setup_input_retrieval_step: GuiSetupInputRetrievalStep
    _setup_election_builder_step: SetupElectionBuilderStep
    _election_service: ElectionService
    _output_setup_files_step: OutputSetupFilesStep

    def __init__(
        self,
        key_ceremony_service: KeyCeremonyService,
        election_service: ElectionService,
        setup_input_retrieval_step: GuiSetupInputRetrievalStep,
        setup_election_builder_step: SetupElectionBuilderStep,
        output_setup_files_step: OutputSetupFilesStep,
    ) -> None:
        self._key_ceremony_service = key_ceremony_service
        self._setup_input_retrieval_step = setup_input_retrieval_step
        self._setup_election_builder_step = setup_election_builder_step
        self._election_service = election_service
        self._output_setup_files_step = output_setup_files_step

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
        self, key_ceremony_id: str, election_name: str, manifest: str, url: str
    ) -> dict[str, Any]:
        self._log.debug(
            f"Creating election key_ceremony_id: {key_ceremony_id}, "
            + f"election_name: {election_name}, "
            + f"manifest: {manifest}, "
            + f"url: {url}"
        )
        db = self._db_service.get_db()
        existing_elections = db.elections.find_one({"election_name": election_name})
        if existing_elections:
            fail_result: dict[str, Any] = eel_fail("Election already exists")
            return fail_result

        key_ceremony = self._key_ceremony_service.get(db, key_ceremony_id)

        election_inputs = self._setup_input_retrieval_step.get_gui_inputs(
            key_ceremony.guardian_count, key_ceremony.quorum, url, manifest
        )
        joint_key = key_ceremony.get_joint_key()
        build_election_results = (
            self._setup_election_builder_step.build_election_for_setup(
                election_inputs, joint_key
            )
        )
        out_dir = gettempdir()
        self._output_setup_files_step.output(
            election_inputs, build_election_results, out_dir, out_dir
        )
        # context_file = files[0]
        # constants_file = files[1]

        # election = self._key_ceremony_service.create_election(
        #     db, key_ceremony, election_name, manifest
        # )
        return eel_success("success")
