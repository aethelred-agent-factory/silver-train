# tests/test_storage/test_artifact_manager.py
import json
import os

import pytest
from src.storage.artifact_manager import ArtifactManager
from src.utils.crypto_utils import CryptoUtils


@pytest.fixture
def crypto_utils():
    return CryptoUtils()


@pytest.fixture
def local_artifact_manager(test_config, tmp_path, crypto_utils):
    artifact_dir = tmp_path / "artifacts"
    artifact_dir.mkdir()
    test_config["system_config"]["paths"]["artifacts"] = str(artifact_dir)
    # Ensure S3 is not used for this fixture
    os.environ["S3_BUCKET"] = ""
    return ArtifactManager(test_config, crypto_utils)


def test_upload_artifact_local(local_artifact_manager, tmp_path, crypto_utils):
    data = "test artifact content"
    artifact_id = "test_artifact_1.json"

    uri, checksum = local_artifact_manager.upload_artifact(data, artifact_id)

    assert uri.startswith("file://")

    file_path = tmp_path / "artifacts" / artifact_id
    assert file_path.exists()
    assert file_path.read_text() == data

    checksum_file = tmp_path / "artifacts" / f"{artifact_id}.sha256"
    assert checksum_file.exists()
    assert checksum_file.read_text() == crypto_utils.sha256_hash(data.encode("utf-8"))


def test_download_artifact_local(local_artifact_manager, tmp_path, crypto_utils):
    data = "another test artifact"
    artifact_id = "test_artifact_2.txt"

    local_artifact_manager.upload_artifact(data, artifact_id)  # Upload first

    downloaded_data, checksum = local_artifact_manager.download_artifact(artifact_id)
    assert downloaded_data == data


def test_download_artifact_local_not_found(local_artifact_manager):
    downloaded_data, checksum = local_artifact_manager.download_artifact(
        "non_existent.json"
    )
    assert downloaded_data is None
    assert checksum is None


def test_download_artifact_local_checksum_mismatch(
    local_artifact_manager, tmp_path, crypto_utils
):
    data = "corrupted content"
    artifact_id = "test_artifact_3.json"

    # Manually create artifact and a wrong checksum file
    file_path = tmp_path / "artifacts" / artifact_id
    file_path.write_text("original content")

    checksum_file = tmp_path / "artifacts" / f"{artifact_id}.sha256"
    checksum_file.write_text("wrong_checksum")

    downloaded_data, checksum = local_artifact_manager.download_artifact(artifact_id)
    assert downloaded_data is None  # Should fail due to checksum mismatch
