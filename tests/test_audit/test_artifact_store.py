# tests/test_audit/test_artifact_store.py
import json
from datetime import datetime, timezone

import pytest
from strategy_optimizer.audit.artifact_store import ArtifactStore
from strategy_optimizer.data_bus.schemas import AuditAction, AuditVerdict, TieredFinding
from strategy_optimizer.utils.crypto_utils import CryptoUtils
from strategy_optimizer.storage.artifact_manager import ArtifactManager


@pytest.fixture
def crypto_utils():
    return CryptoUtils()


@pytest.fixture
def mock_artifact_manager(mocker):
    mock = mocker.Mock(spec=ArtifactManager)
    mock.get_artifact_uri.return_value = "file:///mock/path/artifact.json"
    mock.download_artifact.return_value = (
        None  # Default for testing retrieve non-existent
    )
    return mock


@pytest.fixture
def artifact_store(test_config, mock_artifact_manager, crypto_utils):
    return ArtifactStore(test_config, mock_artifact_manager, crypto_utils)


@pytest.fixture
def sample_audit_verdict():
    return AuditVerdict(
        audit_id="test_audit_id",
        proposal_id="test_proposal_id",
        timestamp=datetime.now(timezone.utc),
        tiered_findings=[
            TieredFinding(tier="T2", code="T2_Test", explanation="Test explanation")
        ],
        action=AuditAction(
            type="ALLOW_WITH_RESTRICTION", restrictions={"max_order_size_pct": 0.5}
        ),
        artifact_refs=[],
        checksum="",
    )


def test_store_artifact(artifact_store, mock_artifact_manager, sample_audit_verdict):
    mock_artifact_manager.upload_artifact.return_value = (
        "file:///mock/path/artifact.json",
        "dummy_checksum",
    )
    verdict = artifact_store.store_artifact(sample_audit_verdict)

    assert verdict.artifact_refs[0] == "file:///mock/path/artifact.json"
    assert verdict.checksum == "dummy_checksum"

    mock_artifact_manager.upload_artifact.assert_called_once()


def test_retrieve_artifact_not_found(artifact_store, mock_artifact_manager):
    mock_artifact_manager.download_artifact.return_value = (None, None)
    verdict = artifact_store.retrieve_artifact("non_existent_audit")
    assert verdict is None

    mock_artifact_manager.download_artifact.assert_called_once_with(
        "audit_non_existent_audit.json"
    )


def test_retrieve_artifact_found(
    artifact_store, mock_artifact_manager, sample_audit_verdict, crypto_utils
):
    # Mock download_artifact to return a valid JSON string and checksum
    verdict_json = sample_audit_verdict.model_dump_json()
    checksum = crypto_utils.sha256_hash(verdict_json.encode("utf-8"))
    mock_artifact_manager.download_artifact.return_value = (verdict_json, checksum)

    verdict = artifact_store.retrieve_artifact(sample_audit_verdict.audit_id)
    assert verdict is not None
    assert isinstance(verdict, AuditVerdict)
    assert verdict.proposal_id == sample_audit_verdict.proposal_id
