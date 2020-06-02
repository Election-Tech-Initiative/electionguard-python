from typing import Dict, NamedTuple

from .election_key_pair import ElectionKeyPair
from .group import int_to_p_unchecked, int_to_q_unchecked


class CeremonyDetails(NamedTuple):
    """
    Details of key ceremony
    """

    number_of_guardians: int
    quorum: int


class KeyCeremonyMediator:
    ceremony_details: CeremonyDetails

    def __init__(self, ceremony_details: CeremonyDetails):
        self.ceremony_details = ceremony_details

    # Auxiliary
    def store_auxiliary_public_key(self, guardian_id: str, public_key: str) -> None:
        pass

    def all_auxiliary_public_keys_received(self) -> bool:
        return True

    def get_auxiliary_public_keys(self, guardian_id: str) -> Dict[str, str]:
        print(guardian_id)
        return {}

    # Election
    def store_election_keys(
        self, guardian_id: str, public_key: str, partial_secret_keys: Dict[str, str]
    ) -> None:
        pass

    def all_election_keys_recieved(self) -> bool:
        """
        Verifies that all shares have been received by each of the trustees. Essentially ensure all trustees received all the needed shares.
        """
        return True

    def get_election_keys(self, guardian_id: str) -> Dict[str, str]:
        print(guardian_id)
        return {}

    # Exchange Shared Partial Secret Keys
    def acknowledge_election_keys_received(self, guardian_id: str) -> None:
        """
        For trustee to identify that they have received all shares
        """
        print(guardian_id)

    # Ensure all trustee verified partial secret key
    def acknowledge_election_keys_verified(self, guardian_id: str) -> None:
        """
        Receive a single trustees verification of the shares
        """
        print(guardian_id)

    def all_election_keys_verified(self) -> bool:
        """
        Verify all trustees have verified their received shares
        """
        return True

    # Points to combine_trustee_public_election_keys
    # JointElectionKey
    def publish_joint_election_key(self) -> None:
        return


def generate_election_keys() -> ElectionKeyPair:
    """
    Get the appropriate pieces to share from the private key of a trustee and Schnoor proof for each piece.
    """
    return ElectionKeyPair(int_to_q_unchecked(0), int_to_p_unchecked(0))


def generate_election_partial_secret_keys(
    secret_key: str, ceremony_details: CeremonyDetails
) -> str:
    """
    Get the appropriate pieces to share from the private key of a trustee and Schnoor proof for each piece.
    """
    print(secret_key, ceremony_details)
    return ""


# KeyCeremony_Trustee_verify_shares
def verify_election_partial_secret_key() -> bool:
    """
    Validate a shared private key is proper and the Key Ceremony can continue.
    """
    return True


# KeyCeremony_Coordinator_publish_joint_key
# JointElectionKey
def combine_election_public_keys() -> None:
    return
