from typing import List
import eel

from electionguard_gui.component_base import ComponentBase
from electionguard_gui.create_key_component import CreateKeyComponent
from electionguard_gui.guardian_home_component import GuardianHomeComponent
from electionguard_gui.setup_election_component import SetupElectionComponent


class MainApp:
    """Responsible for functionality related to the main app"""

    components: List[ComponentBase] = [
        GuardianHomeComponent(),
        CreateKeyComponent(),
        SetupElectionComponent(),
    ]

    def start(self) -> None:
        for component in self.components:
            component.expose()

        eel.init("src/electionguard_gui/web")
        eel.start("main.html", size=(1024, 768))


def run() -> None:
    MainApp().start()
