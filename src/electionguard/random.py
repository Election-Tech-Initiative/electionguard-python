from typing import Iterable, Iterator, List

from electionguard.group import ElementModQ, int_to_q
from electionguard.hash import hash_elems


class RandomIterable(Iterable[ElementModQ]):
    """
    Creates an iterable of random elements in [0,Q), seeded from an initial element in [0,Q).
    If you start with the same seed, you'll get exactly the same sequence.
    """
    def __init__(self, seed: ElementModQ) -> None:
        self.seed: ElementModQ = seed
        self.__ctr: int = 0

    def __iter__(self) -> Iterator[ElementModQ]:
        return self

    def __next__(self) -> ElementModQ:
        return self.next()

    def next(self) -> ElementModQ:
        """
        Returns the next random number from this iterable.
        """
        old_ctr = self.__ctr
        self.__ctr += 1
        return hash_elems(self.seed, int_to_q(old_ctr))

    def take(self, n: int) -> List[ElementModQ]:
        """
        Returns a list of the n next random numbers from this iterable.
        """
        l: List[ElementModQ] = []
        for i in range(0, n):
            l.append(self.next())

        return l
