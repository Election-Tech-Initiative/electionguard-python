from typing import List
import eel

from .components.component_base import ComponentBase
from .components.create_key_ceremony_component import (
    CreateKeyCeremonyComponent,
)
from .components.guardian_home_component import GuardianHomeComponent
from .components.key_ceremony_details_component import (
    KeyCeremonyDetailsComponent,
)
from .components.setup_election_component import SetupElectionComponent

from .services.authorization_service import AuthoriationService
from .services.db_service import DbService
from .services.eel_log_service import EelLogService


class MainApp:
    """Responsible for functionality related to the main app"""

    components: List[ComponentBase] = [
        GuardianHomeComponent(),
        CreateKeyCeremonyComponent(),
        SetupElectionComponent(),
        KeyCeremonyDetailsComponent(),
    ]

    def start(self) -> None:
        try:
            db_service = DbService()
            auth_service = AuthoriationService()
            log_service = EelLogService()
            services = [db_service, auth_service, log_service]

            for service in services:
                service.init()

            for component in self.components:
                component.init(db_service, auth_service, log_service)

            eel.init("src/electionguard_gui/web")
            eel.start("main.html", size=(1024, 768), port=0)
        except Exception as e:
            log_service.error(e)
            raise e


def run() -> None:
    MainApp().start()
