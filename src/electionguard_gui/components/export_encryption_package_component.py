import os
from tempfile import gettempdir
from typing import Any
from shutil import unpack_archive
import eel
from electionguard_gui.eel_utils import eel_success
from electionguard_gui.components.component_base import ComponentBase
from electionguard_gui.services import ElectionService
from electionguard_gui.services.export_service import get_download_path


class ExportEncryptionPackageComponent(ComponentBase):
    """Responsible for exporting an encryption package for an election"""

    _election_service: ElectionService

    def __init__(self, election_service: ElectionService) -> None:
        self._election_service = election_service

    def expose(self) -> None:
        eel.expose(self.get_encryption_package_export_locations)
        eel.expose(self.export_encryption_package)

    def get_encryption_package_export_locations(self) -> dict[str, Any]:
        self._log.trace("getting export locations")
        common_root_dirs = [get_download_path(), gettempdir()]
        locations = [
            os.path.join(location, "public_encryption_package")
            for location in common_root_dirs
        ]
        return eel_success(locations)

    def export_encryption_package(
        self, election_id: str, location: str
    ) -> dict[str, Any]:
        db = self._db_service.get_db()
        election = self._election_service.get(db, election_id)
        self._log.debug(f"unzipping: {election.encryption_package_file} to {location}")
        unpack_archive(election.encryption_package_file, location)
        return eel_success()
