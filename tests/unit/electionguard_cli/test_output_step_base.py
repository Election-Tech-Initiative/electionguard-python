from types import SimpleNamespace

from tests.base_test_case import BaseTestCase

from electionguard.key_ceremony import CeremonyDetails
from electionguard.key_ceremony_mediator import KeyCeremonyMediator
from electionguard_cli.cli_steps import OutputStepBase
from electionguard_tools.helpers.key_ceremony_orchestrator import (
    KeyCeremonyOrchestrator,
)


class TestOutputStepBase(BaseTestCase):
    """Output step tests"""

    def test_guardian_records_include_missing_guardians(self):
        # Arrange
        ceremony_details = CeremonyDetails(3, 2)
        guardians = KeyCeremonyOrchestrator.create_guardians(ceremony_details)
        KeyCeremonyOrchestrator.perform_full_ceremony(
            guardians, KeyCeremonyMediator("mediator", ceremony_details)
        )
        present = SimpleNamespace(guardians=guardians[:2])

        # Act
        # pylint: disable=protected-access
        records = OutputStepBase._get_guardian_records(present)

        # Assert
        self.assertEqual(
            [record.guardian_id for record in records],
            [guardian.id for guardian in guardians],
        )
        self.assertEqual(records, [guardian.publish() for guardian in guardians])
