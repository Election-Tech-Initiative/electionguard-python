from typing import List
from os import environ
from sys import exit
import eel

from electionguard_gui.authorization_service import AuthoriationService
from electionguard_gui.component_base import ComponentBase
from electionguard_gui.create_key_ceremony_component import CreateKeyCeremonyComponent
from electionguard_gui.guardian_home_component import GuardianHomeComponent
from electionguard_gui.services.db_service import DbService
from electionguard_gui.setup_election_component import SetupElectionComponent


class MainApp:
    """Responsible for functionality related to the main app"""

    DB_PASSWORD_KEY = "EG_DB_PASSWORD"

    components: List[ComponentBase] = [
        GuardianHomeComponent(),
        CreateKeyCeremonyComponent(),
        SetupElectionComponent(),
        AuthoriationService(),
    ]

    def get_param(self, param_name: str) -> str:
        try:
            return environ[param_name]
        except KeyError:
            print(f"The environment variable {param_name} is not set.")
            exit(1)

    def start(self) -> None:
        db_password = self.get_param(self.DB_PASSWORD_KEY)
        db_service = DbService(db_password)

        for component in self.components:
            component.init(db_service)

        eel.init("src/electionguard_gui/web")
        eel.start("main.html", size=(1024, 768), port=0)


def run() -> None:
    MainApp().start()
