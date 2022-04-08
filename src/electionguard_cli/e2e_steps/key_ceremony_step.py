from electionguard.key_ceremony import (
    ElectionKey,
)
from electionguard.key_ceremony_mediator import KeyCeremonyMediator
from electionguard.utils import get_optional
from electionguard_tools.helpers.key_ceremony_orchestrator import (
    KeyCeremonyOrchestrator,
)

from ..cli_models.e2e_inputs import E2eInputs
from .e2e_step_base import E2eStepBase


class KeyCeremonyStep(E2eStepBase):
    """Responsible for running a key ceremony and producing an elgamal public key given a list of guardians."""

    def run_key_ceremony(self, election_inputs: E2eInputs) -> ElectionKey:
        self.print_header("Performing key ceremony")

        guardians = election_inputs.guardians
        mediator: KeyCeremonyMediator = KeyCeremonyMediator(
            "mediator_1", guardians[0].ceremony_details
        )
        KeyCeremonyOrchestrator.perform_full_ceremony(guardians, mediator)
        KeyCeremonyOrchestrator.perform_round_1(guardians, mediator)
        if not mediator.all_guardians_announced():
            raise ValueError("All guardians failed to announce successfully")
        KeyCeremonyOrchestrator.perform_round_2(guardians, mediator)
        KeyCeremonyOrchestrator.perform_round_3(guardians, mediator)
        election_key = mediator.publish_election_key()

        self.print_value("Election Key", get_optional(election_key).public_key)
        return get_optional(election_key)
