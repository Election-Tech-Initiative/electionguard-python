import eel
from electionguard_gui.services.service_base import ServiceBase


class VersionService(ServiceBase):
    """Responsible for retrieving version information"""

    def expose(self) -> None:
        eel.expose(self.get_version)

    def get_version(self) -> str:
        return "0.0.1"
