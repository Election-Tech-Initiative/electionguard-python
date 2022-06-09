from time import sleep
from typing import Any
import eel
from pymongo import MongoClient
from pymongo.database import Database

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
def start_ceremony(key_name: str, guardian_count: int, quorum: int) -> dict[str, Any]:
    print(
        f"Starting ceremony: key_name: {key_name}, guardian_count: {guardian_count}, quorum: {quorum}"
    )
    # todo: parameterize db credentials here and in docker-compose.db.yml
    client: MongoClient = MongoClient(
        "localhost", 27017, username="root", password="example"
    )
    db: Database = client.ElectionGuardDb
    keys_collection = db.keys
    existing_keys = keys_collection.find_one({"key_name": key_name})
    if existing_keys:
        print(f"record '{key_name}' already exists")
        return eel_fail("Key name already exists")
    key = {
        "key_name": key_name,
        "guardian_count": guardian_count,
        "quorum": quorum,
        "guardians_joined": 0,
    }
    print(f"creating '{key_name}' record")
    keys_collection.insert_one(key)
    # todo: poll until guardians accept key
    sleep(1)
    return eel_success()


def eel_fail(message: str) -> dict[str, Any]:
    return {"success": False, "message": message}


def eel_success() -> dict[str, Any]:
    return {"success": True}


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
