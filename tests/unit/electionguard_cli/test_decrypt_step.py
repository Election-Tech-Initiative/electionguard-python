import click

from tests.base_test_case import BaseTestCase

from electionguard.ballot_box import BallotBox, BallotBoxState, get_ballots
from electionguard.data_store import DataStore
from electionguard.encrypt import EncryptionMediator
from electionguard.guardian import Guardian
from electionguard.key_ceremony import CeremonyDetails
from electionguard.key_ceremony_mediator import KeyCeremonyMediator
from electionguard.tally import tally_ballots
from electionguard.utils import get_optional
from electionguard_cli.cli_models import BuildElectionResults
from electionguard_cli.cli_steps import DecryptStep
import electionguard_tools.factories.ballot_factory as BallotFactory
import electionguard_tools.factories.election_factory as ElectionFactory
from electionguard_tools.helpers.election_builder import ElectionBuilder
from electionguard_tools.helpers.key_ceremony_orchestrator import (
    KeyCeremonyOrchestrator,
)
from electionguard_tools.helpers.tally_accumulate import accumulate_plaintext_ballots

NUMBER_OF_GUARDIANS = 3
QUORUM = 2


class TestDecryptStep(BaseTestCase):
    """Decrypt step tests"""

    def setUp(self):
        super().setUp()
        ceremony_details = CeremonyDetails(NUMBER_OF_GUARDIANS, QUORUM)
        self.guardians: list[Guardian] = KeyCeremonyOrchestrator.create_guardians(
            ceremony_details
        )
        key_ceremony_mediator = KeyCeremonyMediator("mediator", ceremony_details)
        KeyCeremonyOrchestrator.perform_full_ceremony(
            self.guardians, key_ceremony_mediator
        )
        joint_key = get_optional(key_ceremony_mediator.publish_joint_key())

        self.manifest = ElectionFactory.ElectionFactory().get_fake_manifest()
        builder = ElectionBuilder(NUMBER_OF_GUARDIANS, QUORUM, self.manifest)
        builder.set_public_key(joint_key.joint_public_key)
        builder.set_commitment_hash(joint_key.commitment_hash)
        internal_manifest, context = get_optional(builder.build())
        self.build_results = BuildElectionResults(internal_manifest, context)

        ballot_factory = BallotFactory.BallotFactory()
        encrypter = EncryptionMediator(
            internal_manifest,
            context,
            ElectionFactory.ElectionFactory.get_encryption_device(),
        )
        cast = [
            ballot_factory.get_fake_ballot(internal_manifest, f"cast-{i}")
            for i in range(3)
        ]
        spoiled = ballot_factory.get_fake_ballot(internal_manifest, "spoiled")
        store: DataStore = DataStore()
        ballot_box = BallotBox(internal_manifest, context, store)
        for ballot in cast:
            ballot_box.cast(get_optional(encrypter.encrypt(ballot)))
        ballot_box.spoil(get_optional(encrypter.encrypt(spoiled)))

        self.ciphertext_tally = get_optional(
            tally_ballots(store, internal_manifest, context)
        )
        self.spoiled_ballots = list(get_ballots(store, BallotBoxState.SPOILED).values())
        self.expected_tally = accumulate_plaintext_ballots(cast)

    def _decrypt(self, guardians: list[Guardian]):
        return DecryptStep().decrypt(
            self.ciphertext_tally,
            self.spoiled_ballots,
            guardians,
            self.build_results,
            self.manifest,
        )

    def _assert_tally_correct(self, results) -> None:
        for contest in results.plaintext_tally.contests.values():
            for selection_id, selection in contest.selections.items():
                self.assertEqual(
                    selection.tally, self.expected_tally.get(selection_id, 0)
                )
        self.assertEqual(len(results.plaintext_spoiled_ballots), 1)

    def test_decrypt_with_all_guardians(self):
        self._assert_tally_correct(self._decrypt(self.guardians))

    def test_decrypt_with_missing_guardian_meeting_quorum(self):
        self._assert_tally_correct(self._decrypt(self.guardians[:QUORUM]))

    def test_decrypt_below_quorum_fails_clearly(self):
        with self.assertRaises(click.ClickException):
            self._decrypt(self.guardians[: QUORUM - 1])
