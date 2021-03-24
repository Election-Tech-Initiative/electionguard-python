from .hash import hash_elems
from .group import ElementModQ


def get_hash_for_device(
    uuid: int, session_id: str, launch_code: int, location: str
) -> ElementModQ:
    """
    Get starting hash for given device
    :param uuid: Unique identifier of device
    :param location: Location of device
    :return: Starting hash of device
    """
    return hash_elems(uuid, session_id, launch_code, location)


def get_ballot_code(
    prev_code: ElementModQ, timestamp: int, ballot_hash: ElementModQ
) -> ElementModQ:
    """
    Get the rotated code for a particular ballot.
    :param prev_code: Previous code or starting hash from device
    :param timestamp: Timestamp in ticks
    :param ballot_hash: Hash of ballot
    :return: code
    """
    return hash_elems(prev_code, timestamp, ballot_hash)
