from typing import List
from enum import Enum

# pylint: disable=no-name-in-module
from gmpy2 import xmpz, powmod

# Note that this file is carefully designed not to depend on group.py, allowing us to refer to
# code here from within constants.py.


class PowRadixOption(Enum):
    """
    Different acceleration options for the `PowRadix` acceleration of modular exponentiation.
    """

    NO_ACCELERATION = 1
    LOW_MEMORY_USE = 2  # 4.8MB per instance of PowRadix (see group.py)
    HIGH_MEMORY_USE = 3  # 84MB per instance
    EXTREME_MEMORY_USE = 4  # 573MB per instance


# Modular exponentiation performance improvements via Olivier Pereira
# https://github.com/pereira/expo-fixed-basis/blob/main/powradix.py
class PowRadix:
    """Internal class, used for accelerating modular exponentiation."""

    basis: xmpz
    table_length: int
    k: int
    table: List[List[xmpz]]
    small_prime: xmpz
    large_prime: xmpz

    def __init__(
        self, basis: xmpz, option: PowRadixOption, small_prime: xmpz, large_prime: xmpz
    ):
        """
        The basis is to be used with future calls to the `pow` method, such that
        `PowRadix(basis).pow(e) == powmod(basis, e, P)`, except the computation
        will run much faster. By specifying which `PowRadixOption` to use, the
        table will either use more or less memory, corresponding to greater
        acceleration.

        `PowRadixOption.NO_ACCELERATION` uses no extra memory and just calls `powmod`.

        `PowRadixOption.LOW_MEMORY_USE` corresponds to 4.2MB of state per instance of PowRadix.

        `PowRadixOption.HIGH_MEMORY_USE` corresponds to 84MB of state per instance of PowRadix.

        `PowRadixOption.EXTREME_MEMORY_USE` corresponds to 537MB of state per instance of PowRadix.
        """

        self.basis = basis
        e_size = 256  # Size of the exponent
        one_mpz = xmpz(1)

        if option == PowRadixOption.NO_ACCELERATION:
            self.k = 0
            return

        if option == PowRadixOption.LOW_MEMORY_USE:
            k = 8
        elif option == PowRadixOption.HIGH_MEMORY_USE:
            k = 13
        else:
            k = 16

        # we save local copies for speed, since we want the pow function to go as fast as absolutely possible
        self.large_prime = large_prime
        self.small_prime = small_prime

        self.table_length = -(-e_size // k)  # Double negative to take the ceiling
        self.k = k

        table: List[List[xmpz]] = []
        row_basis = basis
        running_basis = row_basis
        for _ in range(self.table_length):
            row = [one_mpz]
            for _ in range(1, 2 ** k):
                row.append(running_basis)
                running_basis = running_basis * row_basis % self.large_prime
            table.append(row)
            row_basis = running_basis
        self.table = table

    def pow(self, e: xmpz, normalize_e: bool = True) -> xmpz:
        """
        Computes the basis to the given exponent, optionally normalizing
        the exponent beforehand if it's out of range.
        """
        if normalize_e:
            e = e % self.small_prime

        if self.k == 0:
            return powmod(self.basis, e, self.large_prime)

        y = xmpz(1)
        for i in range(self.table_length):
            e_slice = e[i * self.k : (i + 1) * self.k]
            y = y * self.table[i][e_slice] % self.large_prime
        return y
