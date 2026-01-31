# tests/test_optimizer/test_parameter_memory.py
import pytest
from src.optimizer.parameter_memory import ParameterMemory
from src.storage.state_manager import StateManager


@pytest.fixture
def parameter_memory(in_memory_state_manager):
    return ParameterMemory(in_memory_state_manager)


def test_log_tested(parameter_memory):
    params = {"min_score": 2.0, "rsi_oversold": 30}
    regime = "TREND"
    result = "success"
    metrics = {"profit": 5.0}

    parameter_memory.log_tested(params, regime, metrics, result)

    # Verify directly from the state manager
    query = "SELECT params_hash, regime, result FROM parameter_history WHERE params_hash = ? AND regime = ?"
    params_hash = parameter_memory._hash_params(params)
    retrieved = parameter_memory.state_manager.execute_query(
        query, (params_hash, regime), fetch="one"
    )

    assert retrieved is not None
    assert retrieved[0] == params_hash
    assert retrieved[1] == regime
    assert retrieved[2] == result


def test_has_been_tested(parameter_memory):
    params1 = {"min_score": 2.0, "rsi_oversold": 30}
    regime1 = "TREND"
    parameter_memory.log_tested(params1, regime1, {"profit": 5.0}, "success")

    assert parameter_memory.has_been_tested(params1, regime1) is True

    params2 = {"min_score": 2.5, "rsi_oversold": 30}  # Different params
    regime2 = "RANGE"
    assert parameter_memory.has_been_tested(params2, regime1) is False
    assert parameter_memory.has_been_tested(params1, regime2) is False
    assert parameter_memory.has_been_tested(params2, regime2) is False


def test_hash_params(parameter_memory):
    params1 = {"a": 1, "b": "hello"}
    params2 = {"b": "hello", "a": 1}  # Same params, different order
    params3 = {"a": 1, "b": "world"}  # Different params

    hash1 = parameter_memory._hash_params(params1)
    hash2 = parameter_memory._hash_params(params2)
    hash3 = parameter_memory._hash_params(params3)

    assert hash1 == hash2  # Hashes should be the same for same content
    assert hash1 != hash3  # Hashes should be different for different content
