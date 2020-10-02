from typing import List, Optional
from .hash import hash_elems
from .group import ElementModQ
from .words import get_word

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

    segments = tracker_hash.to_bytes()
    words: List[str] = []
    for i in range(0, len(segments), 4):
        # Select 4 bytes for the segment
        first = segments[i]
        second = segments[i + 1]
        third = segments[i + 2]
        fourth = segments[i + 3]

        # word is byte(1) + 1/2 of byte(2)
        word_part = get_word((first * 16 + (second >> 4)))

        # hex is other 1/2 of byte(2) + byte(3) + byte(4)
        hex_part = [
            format((second & 0x0F) >> 0, "1X"),
            format((third & 0xF0) >> 4, "1X"),
            format((third & 0x0F) >> 0, "1X"),
            format((fourth & 0xF0) >> 4, "1X"),
            format((fourth & 0x0F) >> 0, "1X"),
        ]
        if word_part is None:
            return None
        words.append(word_part)
        words.append("".join(hex_part))
    # FIXME ISSUE #82 Minimize length of tracker
    return seperator.join(words)
