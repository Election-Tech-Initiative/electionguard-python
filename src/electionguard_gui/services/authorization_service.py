from typing import Optional
import eel

from electionguard_gui.services.configuration_service import get_is_admin
from electionguard_gui.services.service_base import ServiceBase


class AuthoriationService(ServiceBase):
    """Responsible for functionality related to authorization and user identify"""

    # todo: replace state based storage with configparser https://docs.python.org/3/library/configparser.html
    user_id: Optional[str] = None

    def expose(self) -> None:
        eel.expose(self.get_user_id)
        eel.expose(self.set_user_id)
        eel.expose(self.is_admin)

    def get_user_id(self) -> Optional[str]:
        return self.user_id

    def set_user_id(self, user_id: str) -> None:
        self.user_id = user_id

    # pylint: disable=no-self-use
    def is_admin(self) -> bool:
        return get_is_admin()
