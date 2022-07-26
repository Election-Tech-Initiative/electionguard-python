from typing import List
import eel

from electionguard_gui.components import (
    ViewElectionComponent,
    ComponentBase,
    CreateElectionComponent,
    CreateKeyCeremonyComponent,
    KeyCeremonyListComponent,
    KeyCeremonyDetailsComponent,
    ElectionListComponent,
    ExportEncryptionPackage,
    UploadBallotsComponent,
    CreateDecryptionComponent,
    ViewDecryptionComponent,
)

from electionguard_gui.services import (
    AuthorizationService,
    DbService,
    EelLogService,
    KeyCeremonyStateService,
    ServiceBase,
    BallotUploadService,
    DecryptionService,
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
        db_service: DbService,
        guardian_home_component: KeyCeremonyListComponent,
        create_key_ceremony_component: CreateKeyCeremonyComponent,
        key_ceremony_details_component: KeyCeremonyDetailsComponent,
        authorization_service: AuthorizationService,
        key_ceremony_state_service: KeyCeremonyStateService,
        create_election_component: CreateElectionComponent,
        view_election_component: ViewElectionComponent,
        election_list_component: ElectionListComponent,
        export_encryption_package: ExportEncryptionPackage,
        upload_ballots_component: UploadBallotsComponent,
        ballot_upload_service: BallotUploadService,
        decryption_service: DecryptionService,
        create_decryption_component: CreateDecryptionComponent,
        view_decryption_component: ViewDecryptionComponent,
    ) -> None:
        super().__init__()

        self.log_service = log_service
        self.db_service = db_service

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
        ]

        self.services = [
            authorization_service,
            db_service,
            log_service,
            key_ceremony_state_service,
            ballot_upload_service,
            decryption_service,
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
