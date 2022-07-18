from dependency_injector import containers, providers
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
from electionguard_gui.main_app import MainApp
from electionguard_gui.services.authorization_service import AuthorizationService
from electionguard_gui.services.db_service import DbService

from electionguard_gui.services.eel_log_service import EelLogService
from electionguard_gui.services.key_ceremony_service import KeyCeremonyService
from electionguard_gui.services.key_ceremony_state_service import (
    KeyCeremonyStateService,
)


class Container(containers.DeclarativeContainer):
    """Responsible for dependency injection and how components are wired together"""

    log_service = providers.Factory(EelLogService)
    db_service = providers.Singleton(DbService, log_service=log_service)
    key_ceremony_service = providers.Factory(KeyCeremonyService, db_service=db_service)
    authorization_service = providers.Singleton(AuthorizationService)
    key_ceremony_state_service = providers.Factory(
        KeyCeremonyStateService, log_service=log_service
    )

    # components
    guardian_home_component = providers.Factory(
        KeyCeremonyListComponent, key_ceremony_service=key_ceremony_service
    )
    create_key_ceremony_component = providers.Factory(
        CreateKeyCeremonyComponent,
        key_ceremony_service=key_ceremony_service,
        auth_service=authorization_service,
    )
    key_ceremony_details_component = providers.Factory(
        KeyCeremonyDetailsComponent,
        key_ceremony_service=key_ceremony_service,
        auth_service=authorization_service,
        key_ceremony_state_service=key_ceremony_state_service,
    )
    setup_election_component = providers.Factory(SetupElectionComponent)

    # main
    main_app = providers.Factory(
        MainApp,
        log_service=log_service,
        db_service=db_service,
        guardian_home_component=guardian_home_component,
        create_key_ceremony_component=create_key_ceremony_component,
        key_ceremony_details_component=key_ceremony_details_component,
        setup_election_component=setup_election_component,
        authorization_service=authorization_service,
        key_ceremony_state_service=key_ceremony_state_service,
    )
