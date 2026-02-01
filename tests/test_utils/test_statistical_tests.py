# tests/test_utils/test_statistical_tests.py
import numpy as np
import pandas as pd
import pytest
from utils.statistical_tests import StatisticalTests


@pytest.fixture
def statistical_tests():
    return StatisticalTests()


@pytest.fixture
def sample_data_series():
    # A series with a clear mean and variance
    return pd.Series(np.random.normal(loc=10, scale=2, size=100))


@pytest.fixture
def sample_data_series_b():
    # A second series, slightly different mean
    return pd.Series(np.random.normal(loc=10.5, scale=2, size=100))


def mean_func(data):
    return data.mean()


def test_bootstrap_ci(statistical_tests, sample_data_series):
    lower, upper = statistical_tests.bootstrap_ci(
        sample_data_series, mean_func, iterations=100
    )  # Reduced iterations for faster test
    assert isinstance(lower, float)
    assert isinstance(upper, float)
    assert lower < upper
    # Basic check: mean should be within the CI for large enough data
    assert lower <= sample_data_series.mean() <= upper


def test_permutation_test(statistical_tests, sample_data_series, sample_data_series_b):
    p_value = statistical_tests.permutation_test(
        sample_data_series, sample_data_series_b, mean_func, permutations=100
    )  # Reduced for faster test
    assert isinstance(p_value, float)
    assert 0 <= p_value <= 1


def test_t_test(statistical_tests, sample_data_series, sample_data_series_b):
    t_stat, p_value = statistical_tests.t_test(sample_data_series, sample_data_series_b)
    assert isinstance(t_stat, float)
    assert isinstance(p_value, float)
    assert 0 <= p_value <= 1
