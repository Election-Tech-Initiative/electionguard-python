from typing import Optional, NamedTuple
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives.asymmetric.rsa import (
    generate_private_key,
    RSAPrivateKey,
    RSAPrivateKeyWithSerialization,
    RSAPublicKey,
)
from cryptography.hazmat.primitives.asymmetric.padding import PKCS1v15
from cryptography.hazmat.primitives.serialization import (
    Encoding,
    load_pem_private_key,
    load_pem_public_key,
    NoEncryption,
    PrivateFormat,
    PublicFormat,
)


PUBLIC_EXPONENT = 65537
KEY_SIZE = 4096
PADDING = 11
MAX_BITS = int(KEY_SIZE / 8) - PADDING
ISO_ENCODING = "ISO-8859-1"
BYTE_ORDER = "big"


class RSAKeyPair(NamedTuple):
    """Key pair of RSA pkcs1 in bytes"""

    private_key: str
    public_key: str


def rsa_keypair() -> RSAKeyPair:
    """
    Create RSA keypair

    :return: RSA key pair
    """

    private_key: RSAPrivateKeyWithSerialization = generate_private_key(
        public_exponent=PUBLIC_EXPONENT, key_size=KEY_SIZE, backend=default_backend()
    )
    private_key_bytes = private_key.private_bytes(
        encoding=Encoding.PEM,
        format=PrivateFormat.TraditionalOpenSSL,
        encryption_algorithm=NoEncryption(),
    )
    private_key_string = str(private_key_bytes, ISO_ENCODING)

    public_key: RSAPublicKey = private_key.public_key()
    public_key_bytes = public_key.public_bytes(
        encoding=Encoding.PEM, format=PublicFormat.SubjectPublicKeyInfo
    )
    public_key_string = str(public_key_bytes, ISO_ENCODING)

    return RSAKeyPair(private_key_string, public_key_string)


def rsa_encrypt(message: str, public_key: str) -> Optional[str]:
    """
    Encrypt with RSA public key

    :param message: Message
    :param key_pair: RSA public key
    :return: Encrypted message
    """
    data = bytes(public_key, ISO_ENCODING)
    rsa_public_key: RSAPublicKey = load_pem_public_key(data, backend=default_backend())
    plaintext = bytes.fromhex(message)
    if len(plaintext) > MAX_BITS:
        return None
    ciphertext = rsa_public_key.encrypt(plaintext, PKCS1v15())
    return str(ciphertext, ISO_ENCODING)


def rsa_decrypt(encrypted_message: str, private_key: str) -> Optional[str]:
    """
    Decrypt with RSA private key

    :param encrypted_message: Encrypted message
    :param private_key: RSA private key
    :return: Message
    """

    data = bytes(private_key, ISO_ENCODING)
    rsa_private_key: RSAPrivateKey = load_pem_private_key(
        data, password=None, backend=default_backend()
    )
    ciphertext = bytes(encrypted_message, ISO_ENCODING)
    try:
        plaintext = rsa_private_key.decrypt(ciphertext, PKCS1v15())
    except ValueError:
        return None
    hex_str = plaintext.hex()
    return hex_str
