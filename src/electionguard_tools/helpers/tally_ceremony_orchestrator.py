from typing import List

from electionguard.ballot import SubmittedBallot
from electionguard.election import CiphertextElectionContext
from electionguard.guardian import Guardian, get_valid_ballot_shares
from electionguard.decryption_mediator import DecryptionMediator
from electionguard.key_ceremony import ElectionPublicKey
from electionguard.tally import CiphertextTally
from electionguard.utils import get_optional


class TallyCeremonyOrchestrator:
    """Helper to assist in the decryption process particularly for testing"""

    @staticmethod
    def perform_decryption_setup(
        available_guardians: List[Guardian],
        mediator: DecryptionMediator,
        context: CiphertextElectionContext,
        ciphertext_tally: CiphertextTally,
        submitted_ballots: List[SubmittedBallot] = None,
    ) -> None:
        """
        Perform the necessary setup to ensure that a mediator can decrypt with all guardians available
        """
        TallyCeremonyOrchestrator.announcement(
            available_guardians,
            [guardian.share_key() for guardian in available_guardians],
            mediator,
            context,
            ciphertext_tally,
            submitted_ballots,
        )

    @staticmethod
    def perform_compensated_decryption_setup(
        available_guardians: List[Guardian],
        all_guardians_keys: List[ElectionPublicKey],
        mediator: DecryptionMediator,
        context: CiphertextElectionContext,
        ciphertext_tally: CiphertextTally,
        submitted_ballots: List[SubmittedBallot] = None,
    ) -> None:
        """
        Perform the necessary setup to ensure that a mediator can decrypt when there are guardians missing
        """
        TallyCeremonyOrchestrator.announcement(
            available_guardians,
            all_guardians_keys,
            mediator,
            context,
            ciphertext_tally,
            submitted_ballots,
        )
        TallyCeremonyOrchestrator.exchange_compensated_decryption_shares(
            available_guardians, mediator, context, ciphertext_tally, submitted_ballots
        )

    @staticmethod
    def announcement(
        available_guardians: List[Guardian],
        all_guardians_keys: List[ElectionPublicKey],
        mediator: DecryptionMediator,
        context: CiphertextElectionContext,
        ciphertext_tally: CiphertextTally,
        submitted_ballots: List[SubmittedBallot] = None,
    ) -> None:
        """
        Each available guardian announces their presence. The missing guardians are also announced
        """
        if submitted_ballots is None:
            submitted_ballots = []

        # Announce available guardians
        for available_guardian in available_guardians:
            guardian_key = available_guardian.share_key()
            tally_share = get_optional(
                available_guardian.compute_tally_share(ciphertext_tally, context)
            )
            ballot_shares = get_valid_ballot_shares(
                available_guardian.compute_ballot_shares(submitted_ballots, context)
            )

            mediator.announce(guardian_key, tally_share, ballot_shares)  # type: ignore

        # Announce missing guardians
        # Get all guardian keys and filter to determine the missing guardians
        available_guardian_ids = [guardian.id for guardian in available_guardians]
        missing_guardians = [
            key
            for key in all_guardians_keys
            if key.owner_id not in available_guardian_ids
        ]

        for missing_guardian_key in missing_guardians:
            mediator.announce_missing(missing_guardian_key)

    @staticmethod
    def exchange_compensated_decryption_shares(
        available_guardians: List[Guardian],
        mediator: DecryptionMediator,
        context: CiphertextElectionContext,
        ciphertext_tally: CiphertextTally,
        submitted_ballots: List[SubmittedBallot] = None,
    ) -> None:
        """
        Available guardians generate the compensated decryption shares for the missing guardians
        and send to the mediator.
        """
        if submitted_ballots is None:
            submitted_ballots = []

        # Exchange compensated shares
        missing_guardians = mediator.get_missing_guardians()
        for available_guardian in available_guardians:
            for missing_guardian in missing_guardians:
                tally_share = available_guardian.compute_compensated_tally_share(
                    missing_guardian.owner_id,
                    ciphertext_tally,
                    context,
                )
                if tally_share is not None:
                    mediator.receive_tally_compensation_share(tally_share)

                ballot_shares = get_valid_ballot_shares(
                    available_guardian.compute_compensated_ballot_shares(
                        missing_guardian.owner_id,
                        submitted_ballots,
                        context,
                    )
                )
                mediator.receive_ballot_compensation_shares(ballot_shares)

        # Combine compensated shares into decryption share for missing guardians
        mediator.reconstruct_shares_for_tally(ciphertext_tally)
        mediator.reconstruct_shares_for_ballots(submitted_ballots)
