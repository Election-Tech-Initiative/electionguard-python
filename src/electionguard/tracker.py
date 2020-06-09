from typing import List

from .hash import hash_elems
from .group import ElementModQ, q_to_bytes, bytes_to_q
from .words import get_word, get_index_from_word

DEFAULT_SEPERATOR = "-"


def get_hash_for_device(uuid: int, location: str) -> ElementModQ:
    """
    Get starting hash for given device
    :param uuid: Unique identifier of device
    :param location: Location of device
    :return: Starting hash of device
    """
    return hash_elems(uuid, location)


def get_rotating_tracker_hash(
    seed_hash: ElementModQ, timestamp: int, ballot_hash: ElementModQ
) -> ElementModQ:
    """
    Get the rotated tracker hash for a particular ballot. 
    :param prev_hash: Previous hash or starting hash from device
    :param timestamp: Timestamp in ticks
    :param ballot_hash: Hash of ballot to track
    :return: Tracker hash
    """
    return hash_elems(seed_hash, timestamp, ballot_hash)


def tracker_hash_to_words(
    tracker_hash: ElementModQ, seperator: str = DEFAULT_SEPERATOR
) -> str:
    """
    Convert tracker has to human readable / friendly words
    :param hash: Tracker hash
    :return: Human readable tracker string
    """

    segments = q_to_bytes(tracker_hash)
    int_values = [x for x in segments]
    words: List[str] = []
    # FIXME Reduce length of segments
    for value in int_values:
        words.append(get_word(value))
    return seperator.join(words)


def tracker_words_to_hash(
    tracker_words: str, seperator: str = DEFAULT_SEPERATOR
) -> ElementModQ:
    """
    Convert tracker from human readable / friendly words to hash
    :param tracker_words: Tracker words
    :param seperator: Seperator used between words
    :return: Tracker hash
    """
    words = tracker_words.split(seperator)
    int_values: List[int] = []
    for word in words:
        int_values.append(get_index_from_word(word))
    value = bytes(int_values)
    return bytes_to_q(value)
