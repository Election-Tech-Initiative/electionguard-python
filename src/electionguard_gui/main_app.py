from typing import List
import eel

from electionguard_gui.components.component_base import ComponentBase
from electionguard_gui.components.create_election_component import (
    CreateElectionComponent,
)
from electionguard_gui.components.create_key_ceremony_component import (
    CreateKeyCeremonyComponent,
)
from electionguard_gui.components.key_ceremony_list_component import (
    KeyCeremonyListComponent,
)
from electionguard_gui.components.key_ceremony_details_component import (
    KeyCeremonyDetailsComponent,
)
from electionguard_gui.components.setup_election_component import SetupElectionComponent

from electionguard_gui.services.authorization_service import AuthorizationService
from electionguard_gui.services.db_service import DbService
from electionguard_gui.services.eel_log_service import EelLogService
from electionguard_gui.services.key_ceremony_state_service import (
    KeyCeremonyStateService,
)
from electionguard_gui.services.service_base import ServiceBase


class MainApp:
    """Responsible for functionality related to the main app"""

    log_service: EelLogService
    db_service: DbService
    components: List[ComponentBase]
    services: List[ServiceBase]

    def __init__(
        self,
        log_service: EelLogService,
        db_service: DbService,
        guardian_home_component: KeyCeremonyListComponent,
        create_key_ceremony_component: CreateKeyCeremonyComponent,
        key_ceremony_details_component: KeyCeremonyDetailsComponent,
        setup_election_component: SetupElectionComponent,
        authorization_service: AuthorizationService,
        key_ceremony_state_service: KeyCeremonyStateService,
        create_election_component: CreateElectionComponent,
    ) -> None:
        super().__init__()

        self.log_service = log_service
        self.db_service = db_service

        self.components = [
            guardian_home_component,
            create_key_ceremony_component,
            key_ceremony_details_component,
            setup_election_component,
            create_election_component,
        ]

        self.services = [
            authorization_service,
            db_service,
            log_service,
            key_ceremony_state_service,
        ]

    def start(self) -> None:
        try:
            self.log_service.debug("Starting main app")

            for service in self.services:
                service.init()

            for component in self.components:
                component.init(self.db_service, self.log_service)

            self.db_service.verify_db_connection()
            eel.init("src/electionguard_gui/web")
            self.log_service.debug("Starting eel")
            eel.start("main.html", size=(1024, 768), port=0)
        except Exception as e:
            self.log_service.error(e)
            raise e
