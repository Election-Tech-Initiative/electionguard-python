from time import sleep
import eel

from electionguard_cli.cli_steps import KeyCeremonyStep
from electionguard_cli.setup_election.output_setup_files_step import (
    OutputSetupFilesStep,
)
from electionguard_cli.setup_election.setup_election_builder_step import (
    SetupElectionBuilderStep,
)
from electionguard_gui.gui_setup_election.gui_setup_input_retrieval_step import (
    GuiSetupInputRetrievalStep,
)


@eel.expose
def start_ceremony(key_name: str, guardian_count: int, quorum: int) -> None:
    print(
        f"Starting ceremony: key_name: {key_name}, guardian_count: {guardian_count}, quorum: {quorum}"
    )
    sleep(5)


@eel.expose
def setup_election(guardian_count: int, quorum: int, manifest: str) -> str:
    election_inputs = GuiSetupInputRetrievalStep().get_gui_inputs(
        guardian_count, quorum, manifest
    )
    joint_key = KeyCeremonyStep().run_key_ceremony(election_inputs.guardians)
    build_election_results = SetupElectionBuilderStep().build_election_for_setup(
        election_inputs, joint_key
    )
    files = OutputSetupFilesStep().output(election_inputs, build_election_results)
    context_file = files[0]
    constants_file = files[1]
    print(f"Setup complete, context: {context_file}, constants: {constants_file}")
    with open(context_file, "r", encoding="utf-8") as context_file:
        context_raw: str = context_file.read()
        return context_raw


def run() -> None:
    eel.init("src/electionguard_gui/web")
    eel.start("main.html", size=(1024, 768))
