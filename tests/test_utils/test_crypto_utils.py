# tests/test_utils/test_crypto_utils.py
import pytest
from utils.crypto_utils import CryptoUtils


@pytest.fixture
def crypto_utils():
    return CryptoUtils()


def test_crc32_checksum(crypto_utils):
    data1 = b"hello world"
    data2 = b"hello world"
    data3 = b"hello python"

    checksum1 = crypto_utils.crc32_checksum(data1)
    checksum2 = crypto_utils.crc32_checksum(data2)
    checksum3 = crypto_utils.crc32_checksum(data3)

    assert checksum1 == checksum2
    assert checksum1 != checksum3
    assert len(checksum1) == 8  # CRC32 is 8 hex characters


def test_sha256_hash(crypto_utils):
    data1 = b"secure message"
    data2 = b"secure message"
    data3 = b"another message"

    hash1 = crypto_utils.sha256_hash(data1)
    hash2 = crypto_utils.sha256_hash(data2)
    hash3 = crypto_utils.sha256_hash(data3)

    assert hash1 == hash2
    assert hash1 != hash3
    assert len(hash1) == 64  # SHA256 is 64 hex characters


def test_generate_uuid(crypto_utils):
    uuid1 = crypto_utils.generate_uuid()
    uuid2 = crypto_utils.generate_uuid()

    assert isinstance(uuid1, str)
    assert len(uuid1) == 36  # Standard UUID length with hyphens
    assert uuid1 != uuid2  # Should be unique
