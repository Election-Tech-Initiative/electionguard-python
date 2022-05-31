import eel

from electionguard_cli.cli_steps import ElectionBuilderStep, KeyCeremonyStep
from electionguard_cli.setup_election.output_setup_files_step import (
    OutputSetupFilesStep,
)

from electionguard_gui.gui_setup_election.gui_setup_input_retrieval_step import (
    GuiSetupInputRetrievalStep,
)


@eel.expose
def setup_election(guardian_count: int, quorum: int, manifest: str) -> None:
    election_inputs = GuiSetupInputRetrievalStep().get_gui_inputs(
        guardian_count, quorum, manifest
    )
    joint_key = KeyCeremonyStep().run_key_ceremony(election_inputs.guardians)
    build_election_results = ElectionBuilderStep().build_election_with_key(
        election_inputs, joint_key
    )
    OutputSetupFilesStep().output(election_inputs, build_election_results)
    print(
        f"Setting up election with guardianCount: {guardian_count}, quorum: {quorum}, manifest: {manifest}"
    )


def run() -> None:
    eel.init("src/electionguard_gui/web")
    eel.start("main.html", size=(1024, 768))
