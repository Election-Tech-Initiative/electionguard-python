from typing import List, Optional

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
    prev_hash: ElementModQ, timestamp: int, ballot_hash: ElementModQ
) -> ElementModQ:
    """
    Get the rotated tracker hash for a particular ballot. 
    :param prev_hash: Previous hash or starting hash from device
    :param timestamp: Timestamp in ticks
    :param ballot_hash: Hash of ballot to track
    :return: Tracker hash
    """
    return hash_elems(prev_hash, timestamp, ballot_hash)


def tracker_hash_to_words(
    tracker_hash: ElementModQ, seperator: str = DEFAULT_SEPERATOR
) -> Optional[str]:
    """
    Convert tracker has to human readable / friendly words
    :param hash: Tracker hash
    :return: Human readable tracker string or None
    """

    segments = q_to_bytes(tracker_hash)
    words: List[str] = []
    for value in segments:
        word = get_word(value)
        if word is None:
            return None
        words.append(word)
    # FIXME ISSUE #82 Minimize length of tracker
    return seperator.join(words)


def tracker_words_to_hash(
    tracker_words: str, seperator: str = DEFAULT_SEPERATOR
) -> Optional[ElementModQ]:
    """
    Convert tracker from human readable / friendly words to hash
    :param tracker_words: Tracker words
    :param seperator: Seperator used between words
    :return: Tracker hash or None
    """
    words = tracker_words.split(seperator)
    int_values: List[int] = []
    for word in words:
        index = get_index_from_word(word)
        if index is None:
            return None
        int_values.append(index)
    value = bytes(int_values)
    return bytes_to_q(value)
