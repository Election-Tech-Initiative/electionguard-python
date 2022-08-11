from typing import Optional
import eel

from electionguard_gui.services.configuration_service import ConfigurationService
from electionguard_gui.services.service_base import ServiceBase


class AuthorizationService(ServiceBase):
    """Responsible for functionality related to authorization and user identify"""

    _is_admin: bool

    def __init__(self, config_service: ConfigurationService) -> None:
        self._is_admin = config_service.get_is_admin()

    # todo: replace state based storage with configparser https://docs.python.org/3/library/configparser.html
    user_id: Optional[str] = None

    def expose(self) -> None:
        eel.expose(self.get_user_id)
        eel.expose(self.set_user_id)
        eel.expose(self.is_admin)

    def get_required_user_id(self) -> str:
        if self.user_id is None:
            raise Exception("User must be logged in")
        return self.user_id

    def get_user_id(self) -> Optional[str]:
        return self.user_id

    def set_user_id(self, user_id: str) -> None:
        self.user_id = user_id

    def is_admin(self) -> bool:
        return self._is_admin
