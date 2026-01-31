import hashlib
import binascii
import logging

class CryptoUtils:
    """
    Utility functions for checksums and hashing.
    """
    def __init__(self):
        logging.info("Initialized CryptoUtils.")

    def crc32_checksum(self, data: bytes) -> str:
        """
        Calculates the CRC32 checksum of given bytes data.
        Returns the checksum as a hexadecimal string.
        """
        crc = binascii.crc32(data) & 0xFFFFFFFF
        return f"{crc:08x}"

    def sha256_hash(self, data: bytes) -> str:
        """
        Calculates the SHA256 hash of given bytes data.
        Returns the hash as a hexadecimal string.
        """
        return hashlib.sha256(data).hexdigest()

    def generate_uuid(self) -> str:
        """
        Generates a UUID (Universally Unique Identifier).
        """
        import uuid
        return str(uuid.uuid4())
