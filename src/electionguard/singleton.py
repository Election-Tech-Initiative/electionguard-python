from typing import Any


class Singleton:
    """A Singleton Class"""

    __instance = None

    @staticmethod
    def get_instance() -> Any:
        """Get a static instance of the derived class."""
        if Singleton.__instance is None:
            Singleton()
        return Singleton.__instance

    def __init__(self) -> None:
        if Singleton.__instance is None:
            Singleton.__instance = self
