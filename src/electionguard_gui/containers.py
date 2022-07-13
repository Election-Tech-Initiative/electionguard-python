from dependency_injector import containers, providers
from electionguard_gui.main_app import MainApp
from electionguard_gui.services.db_service import DbService

from electionguard_gui.services.eel_log_service import EelLogService


class Container(containers.DeclarativeContainer):
    """Responsible for dependency injection and how components are wired together"""

    log_service = providers.Factory(EelLogService)
    db_service = providers.Factory(DbService, log_service=log_service)
    main_app = providers.Factory(
        MainApp, log_service=log_service, db_service=db_service
    )
