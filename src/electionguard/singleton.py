from typing import ClassVar, Self


class Singleton:
    """A Singleton Class"""

    _instances: ClassVar[dict[type, "Singleton"]] = {}

    @classmethod
    def get_instance(cls) -> Self:
        """Get a static instance of the derived class."""
        if cls not in Singleton._instances:
            cls()
        instance = Singleton._instances[cls]
        assert isinstance(instance, cls)
        return instance

    def __init__(self) -> None:
        Singleton._instances.setdefault(type(self), self)
