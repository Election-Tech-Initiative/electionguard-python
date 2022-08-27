import traceback
from typing import List
import eel

from electionguard_gui.components import (
    ViewElectionComponent,
    ComponentBase,
    CreateElectionComponent,
    CreateKeyCeremonyComponent,
    GuardianHomeComponent,
    KeyCeremonyDetailsComponent,
    ElectionListComponent,
    ExportEncryptionPackageComponent,
    UploadBallotsComponent,
    CreateDecryptionComponent,
    ViewDecryptionComponent,
    ExportElectionRecordComponent,
    ViewTallyComponent,
    ViewSpoiledBallotComponent,
)

from electionguard_gui.services import (
    AuthorizationService,
    DbService,
    EelLogService,
    ServiceBase,
    ConfigurationService,
    VersionService,
)


class MainApp:
    """Responsible for functionality related to the main app"""

    log_service: EelLogService
    db_service: DbService
    components: List[ComponentBase]
    services: List[ServiceBase]

    def __init__(
        self,
        log_service: EelLogService,
        config_service: ConfigurationService,
        db_service: DbService,
        guardian_home_component: GuardianHomeComponent,
        create_key_ceremony_component: CreateKeyCeremonyComponent,
        key_ceremony_details_component: KeyCeremonyDetailsComponent,
        authorization_service: AuthorizationService,
        create_election_component: CreateElectionComponent,
        view_election_component: ViewElectionComponent,
        election_list_component: ElectionListComponent,
        export_encryption_package: ExportEncryptionPackageComponent,
        upload_ballots_component: UploadBallotsComponent,
        create_decryption_component: CreateDecryptionComponent,
        view_decryption_component: ViewDecryptionComponent,
        export_election_record_component: ExportElectionRecordComponent,
        view_tally_component: ViewTallyComponent,
        view_spoiled_ballot_component: ViewSpoiledBallotComponent,
        version_service: VersionService,
    ) -> None:
        super().__init__()

        self.log_service = log_service
        self.db_service = db_service
        self.config_service = config_service

        self.components = [
            guardian_home_component,
            create_key_ceremony_component,
            key_ceremony_details_component,
            create_election_component,
            view_election_component,
            election_list_component,
            export_encryption_package,
            upload_ballots_component,
            create_decryption_component,
            view_decryption_component,
            export_election_record_component,
            view_tally_component,
            view_spoiled_ballot_component,
        ]

        # services that need to expose methods to the UI
        self.services = [
            authorization_service,
            db_service,
            log_service,
            version_service,
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
            mode = self.config_service.get_mode()
            port = self.config_service.get_port()
            host = self.config_service.get_host()
            self.log_service.debug(f"Starting eel port={port} mode={mode} host={host}")
            eel.start(
                "index.html",
                size=(1024, 768),
                port=port,
                mode=mode,
                host=host,
                close_callback=self.on_close,
            )
            self.log_service.info("Exiting main app normally")
        except Exception as e:
            self.log_service.error("error in main app start", e)
            traceback.print_exc()
            raise e

    def on_close(self, _page: str, _open_sockets: list) -> None:
        self.log_service.info(
            "To close the egui app ensure the browser tab is closed and hit Ctrl+C"
        )
