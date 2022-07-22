from dependency_injector import containers, providers
from dependency_injector.providers import Factory, Singleton
from electionguard_cli.setup_election.output_setup_files_step import (
    OutputSetupFilesStep,
)
from electionguard_cli.setup_election.setup_election_builder_step import (
    SetupElectionBuilderStep,
)
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
from electionguard_gui.main_app import MainApp
from electionguard_gui.services import (
    AuthorizationService,
    DbService,
    EelLogService,
    ElectionService,
    GuardianService,
    KeyCeremonyService,
    KeyCeremonyStateService,
    GuiSetupInputRetrievalStep,
)
from electionguard_gui.services.key_ceremony_stages import (
    KeyCeremonyS1JoinService,
    KeyCeremonyS2AnnounceService,
    KeyCeremonyS3MakeBackupService,
    KeyCeremonyS4ShareBackupService,
    KeyCeremonyS5VerifyBackupService,
    KeyCeremonyS6PublishKeyService,
)


class Container(containers.DeclarativeContainer):
    """Responsible for dependency injection and how components are wired together"""

    # services
    log_service: Factory[EelLogService] = providers.Factory(EelLogService)
    db_service: Singleton[DbService] = providers.Singleton(
        DbService, log_service=log_service
    )
    key_ceremony_service: Factory[KeyCeremonyService] = providers.Factory(
        KeyCeremonyService
    )
    election_service: Factory[ElectionService] = providers.Factory(
        ElectionService, log_service=log_service
    )
    authorization_service: Singleton[AuthorizationService] = providers.Singleton(
        AuthorizationService
    )
    key_ceremony_state_service: Factory[KeyCeremonyStateService] = providers.Factory(
        KeyCeremonyStateService, log_service=log_service
    )
    guardian_service: Factory[GuardianService] = providers.Factory(
        GuardianService, log_service=log_service
    )
    setup_input_retrieval_step: Factory[GuiSetupInputRetrievalStep] = providers.Factory(
        GuiSetupInputRetrievalStep
    )
    setup_election_builder_step: Factory[SetupElectionBuilderStep] = providers.Factory(
        SetupElectionBuilderStep
    )
    output_setup_files_step: Factory[OutputSetupFilesStep] = providers.Factory(
        OutputSetupFilesStep
    )

    # key ceremony services
    key_ceremony_s1_join_service: Factory[KeyCeremonyS1JoinService] = providers.Factory(
        KeyCeremonyS1JoinService,
        log_service=log_service,
        db_service=db_service,
        key_ceremony_service=key_ceremony_service,
        auth_service=authorization_service,
        key_ceremony_state_service=key_ceremony_state_service,
        guardian_service=guardian_service,
    )
    key_ceremony_s2_announce_service: Factory[
        KeyCeremonyS2AnnounceService
    ] = providers.Factory(
        KeyCeremonyS2AnnounceService,
        log_service=log_service,
        db_service=db_service,
        key_ceremony_service=key_ceremony_service,
        auth_service=authorization_service,
        key_ceremony_state_service=key_ceremony_state_service,
        guardian_service=guardian_service,
    )
    key_ceremony_s3_make_backup_service: Factory[
        KeyCeremonyS3MakeBackupService
    ] = providers.Factory(
        KeyCeremonyS3MakeBackupService,
        log_service=log_service,
        db_service=db_service,
        key_ceremony_service=key_ceremony_service,
        auth_service=authorization_service,
        key_ceremony_state_service=key_ceremony_state_service,
        guardian_service=guardian_service,
    )
    key_ceremony_s4_share_backup_service: Factory[
        KeyCeremonyS4ShareBackupService
    ] = providers.Factory(
        KeyCeremonyS4ShareBackupService,
        log_service=log_service,
        db_service=db_service,
        key_ceremony_service=key_ceremony_service,
        auth_service=authorization_service,
        key_ceremony_state_service=key_ceremony_state_service,
        guardian_service=guardian_service,
    )
    key_ceremony_s5_verification_service: Factory[
        KeyCeremonyS5VerifyBackupService
    ] = providers.Factory(
        KeyCeremonyS5VerifyBackupService,
        log_service=log_service,
        db_service=db_service,
        key_ceremony_service=key_ceremony_service,
        auth_service=authorization_service,
        key_ceremony_state_service=key_ceremony_state_service,
        guardian_service=guardian_service,
    )
    key_ceremony_s6_publish_key_service: Factory[
        KeyCeremonyS6PublishKeyService
    ] = providers.Factory(
        KeyCeremonyS6PublishKeyService,
        log_service=log_service,
        db_service=db_service,
        key_ceremony_service=key_ceremony_service,
        auth_service=authorization_service,
        key_ceremony_state_service=key_ceremony_state_service,
        guardian_service=guardian_service,
    )

    # components
    guardian_home_component: Factory[KeyCeremonyListComponent] = providers.Factory(
        KeyCeremonyListComponent, key_ceremony_service=key_ceremony_service
    )
    create_election_component: Factory[CreateElectionComponent] = providers.Factory(
        CreateElectionComponent,
        key_ceremony_service=key_ceremony_service,
        election_service=election_service,
        setup_election_builder_step=setup_election_builder_step,
        setup_input_retrieval_step=setup_input_retrieval_step,
    )
    create_key_ceremony_component: Factory[
        CreateKeyCeremonyComponent
    ] = providers.Factory(
        CreateKeyCeremonyComponent,
        key_ceremony_service=key_ceremony_service,
        auth_service=authorization_service,
    )
    key_ceremony_details_component: Factory[
        KeyCeremonyDetailsComponent
    ] = providers.Factory(
        KeyCeremonyDetailsComponent,
        key_ceremony_service=key_ceremony_service,
        auth_service=authorization_service,
        key_ceremony_state_service=key_ceremony_state_service,
        key_ceremony_s1_join_service=key_ceremony_s1_join_service,
        key_ceremony_s2_announce_service=key_ceremony_s2_announce_service,
        key_ceremony_s3_make_backup_service=key_ceremony_s3_make_backup_service,
        key_ceremony_s4_share_backup_service=key_ceremony_s4_share_backup_service,
        key_ceremony_s5_verification_service=key_ceremony_s5_verification_service,
        key_ceremony_s6_publish_key_service=key_ceremony_s6_publish_key_service,
    )
    setup_election_component: Factory[SetupElectionComponent] = providers.Factory(
        SetupElectionComponent
    )

    # main
    main_app: Factory[MainApp] = providers.Factory(
        MainApp,
        log_service=log_service,
        db_service=db_service,
        guardian_home_component=guardian_home_component,
        create_key_ceremony_component=create_key_ceremony_component,
        key_ceremony_details_component=key_ceremony_details_component,
        setup_election_component=setup_election_component,
        authorization_service=authorization_service,
        key_ceremony_state_service=key_ceremony_state_service,
        create_election_component=create_election_component,
    )
