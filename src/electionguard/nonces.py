from typing import Union, Sequence, List, overload

from electionguard.group import ElementModQ, ElementModPOrQ
from electionguard.hash import hash_elems


class Nonces(Sequence[ElementModQ]):
    """
    Creates a sequence of random elements in [0,Q), seeded from an initial element in [0,Q).
    If you start with the same seed, you'll get exactly the same sequence. Optional string
    or ElementModPOrQ "headers" can be included alongside the seed both at construction time
    and when asking for the next nonce. This is useful when specifying what a nonce is
    being used for, to avoid various kinds of subtle cryptographic attacks.

    The Nonces class is a Sequence. It can be iterated, or it can be treated as an array
    and indexed. Asking for a nonce is constant time, regardless of the index.
    """

    def __init__(self, seed: ElementModQ, *headers: Union[str, ElementModPOrQ]) -> None:
        if len(headers) > 0:
            self.__seed: ElementModQ = hash_elems(seed, *headers)
        else:
            self.__seed = seed

    # https://github.com/python/mypy/issues/4108
    @overload
    def __getitem__(self, index: int) -> ElementModQ:
        pass

    @overload
    def __getitem__(self, index: slice) -> List[ElementModQ]:
        pass

    def __getitem__(
        self, index: Union[slice, int]
    ) -> Union[ElementModQ, List[ElementModQ]]:
        if isinstance(index, int):
            return self.get_with_headers(index)
        else:
            if isinstance(index.stop, int):
                # Handling slices is a pain: https://stackoverflow.com/a/42731787
                indices = range(index.start or 0, index.stop, index.step or 1)
                return [self[i] for i in indices]
            else:
                raise TypeError("Cannot take unbounded slice of Nonces")

    def __len__(self) -> int:
        raise TypeError("Nonces does not have finite length")

    def get_with_headers(self, item: int, *headers: str) -> ElementModQ:
        """
        Gets an item from the sequence at any offset. Headers can be included
        to optionally help specify what a nonce is being used for.

        :param item: Index into the nonces.
        :param headers:  Optional string headers.
        """
        if item < 0:
            raise TypeError("Nonces do not support negative indices.")
        return hash_elems(self.__seed, item, *headers)
