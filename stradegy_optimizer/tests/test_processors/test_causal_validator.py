# tests/test_processors/test_causal_validator.py
import pytest
import pandas as pd
from datetime import datetime, timedelta
from src.processors.causal_validator import CausalValidator

@pytest.fixture
def causal_validator():
    return CausalValidator()

def test_validate_timestamp_causality_valid(causal_validator):
    computation_time = datetime(2023, 1, 1, 10)
    data = pd.DataFrame({
        'timestamp': [datetime(2023, 1, 1, 9), datetime(2023, 1, 1, 10)],
        'value': [1, 2]
    })
    assert causal_validator.validate_timestamp_causality(computation_time, data) is True

def test_validate_timestamp_causality_invalid(causal_validator):
    computation_time = datetime(2023, 1, 1, 9)
    data = pd.DataFrame({
        'timestamp': [datetime(2023, 1, 1, 9), datetime(2023, 1, 1, 10)],
        'value': [1, 2]
    })
    assert causal_validator.validate_timestamp_causality(computation_time, data) is False

def test_validate_timestamp_causality_empty_data(causal_validator):
    computation_time = datetime(2023, 1, 1, 10)
    data = pd.DataFrame({'timestamp': [], 'value': []})
    assert causal_validator.validate_timestamp_causality(computation_time, data) is True

def test_validate_causal_chain_valid(causal_validator):
    proposal_time = datetime(2023, 1, 1, 10)
    # Mock causal chain references - a real one would be more complex
    chain = [
        type('obj', (object,), {'timestamp': datetime(2023, 1, 1, 9)}),
        type('obj', (object,), {'timestamp': datetime(2023, 1, 1, 8)})
    ]
    assert causal_validator.validate_causal_chain(chain, proposal_time) is True

def test_validate_causal_chain_invalid(causal_validator):
    proposal_time = datetime(2023, 1, 1, 9)
    chain = [
        type('obj', (object,), {'timestamp': datetime(2023, 1, 1, 9)}),
        type('obj', (object,), {'timestamp': datetime(2023, 1, 1, 10)}) # Future data
    ]
    assert causal_validator.validate_causal_chain(chain, proposal_time) is False
