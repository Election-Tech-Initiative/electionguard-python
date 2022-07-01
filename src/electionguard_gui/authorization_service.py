from typing import Optional
import eel

from electionguard_gui.component_base import ComponentBase


class AuthoriationService(ComponentBase):
    """Responsible for functionality related to authorization and user identify"""

    # todo: replace state based storage with configparser https://docs.python.org/3/library/configparser.html
    user_id: Optional[str] = None

    def expose(self) -> None:
        eel.expose(self.get_user_id)
        eel.expose(self.set_user_id)

    def get_user_id(self) -> Optional[str]:
        return self.user_id

    def set_user_id(self, user_id: str) -> None:
        self.user_id = user_id
