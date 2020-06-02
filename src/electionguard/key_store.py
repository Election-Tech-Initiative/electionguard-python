from typing import Dict, Optional, NamedTuple, Tuple

from .errors import MissingKeyForGuardianError


class SharedKey(NamedTuple):
    sender_id: str
    recipient_id: str
    key: Optional[str]


class KeyStore:
    _key_store: Dict[str, Optional[str]]

    def set(self, guardian_id: str, key: Optional[str] = None) -> None:
        self._key_store[guardian_id] = key

    def get(self, guardian_id: str) -> Optional[str]:
        return self._key_store[guardian_id]


class ShareableKeyStore:
    _key_store: Dict[str, Tuple[Optional[str], bool]]

    def set(self, guardian_id: str, key: Optional[str] = None) -> None:
        self._key_store[guardian_id] = (key, False)

    def get(self, guardian_id: str) -> Tuple[str, bool]:
        key = self._key_store[guardian_id]
        if not key or key[0] is None:
            raise MissingKeyForGuardianError
        return (key[0], key[1])


def share_public_key(sender_id: str, recipient_id: str, public_key: str) -> SharedKey:
    return SharedKey(sender_id, recipient_id, public_key)


def share_secret_key(sender_id: str, recipient_id: str, secret_key: str) -> SharedKey:
    # TODO Implement Encryption of Secret Key
    return SharedKey(sender_id, recipient_id, secret_key)
