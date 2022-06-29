from enum import IntEnum

PAD_INDICATOR_SIZE = 2


class PaddedDataSize(IntEnum):
    """Define the sizes for padded data."""

    DataSize = 512
    Bytes_512 = DataSize - PAD_INDICATOR_SIZE
