from typing import List
import eel

from electionguard_gui.authorization_service import AuthoriationService
from electionguard_gui.component_base import ComponentBase
from electionguard_gui.create_key_ceremony_component import CreateKeyCeremonyComponent
from electionguard_gui.guardian_home_component import GuardianHomeComponent
from electionguard_gui.services.db_service import DbService
from electionguard_gui.setup_election_component import SetupElectionComponent


class MainApp:
    """Responsible for functionality related to the main app"""

    components: List[ComponentBase] = [
        GuardianHomeComponent(),
        CreateKeyCeremonyComponent(),
        SetupElectionComponent(),
        AuthoriationService(),
    ]

    def start(self) -> None:
        db_service = DbService()

        for component in self.components:
            component.init(db_service)

        eel.init("src/electionguard_gui/web")
        eel.start("main.html", size=(1024, 768), port=0)


def run() -> None:
    MainApp().start()
