import tempfile
import eel

from electionguard_cli.cli_steps import KeyCeremonyStep
from electionguard_cli.setup_election.output_setup_files_step import (
    OutputSetupFilesStep,
)
from electionguard_cli.setup_election.setup_election_builder_step import (
    SetupElectionBuilderStep,
)
from electionguard_gui.components.component_base import ComponentBase
from electionguard_gui.eel_utils import eel_success
from electionguard_gui.gui_setup_election.gui_setup_input_retrieval_step import (
    GuiSetupInputRetrievalStep,
)


class SetupElectionComponent(ComponentBase):
    """Responsible for functionality related to setting up an election"""

    def expose(self) -> None:
        eel.expose(self.setup_election)

    # pylint: disable=no-self-use
    def setup_election(
        self, guardian_count: int, quorum: int, verification_url: str, manifest: str
    ) -> str:
        election_inputs = GuiSetupInputRetrievalStep().get_gui_inputs(
            guardian_count, quorum, verification_url, manifest
        )
        joint_key = KeyCeremonyStep().run_key_ceremony(election_inputs.guardians)
        build_election_results = SetupElectionBuilderStep().build_election_for_setup(
            election_inputs, joint_key
        )
        out_dir = tempfile.gettempdir()
        files = OutputSetupFilesStep().output(
            election_inputs, build_election_results, out_dir, out_dir
        )
        context_file = files[0]
        constants_file = files[1]
        self.log.debug(
            f"Setup complete, context: {context_file}, constants: {constants_file}"
        )
        with open(context_file, "r", encoding="utf-8") as context_file:
            context_raw: str = context_file.read()
            return eel_success(context_raw)
