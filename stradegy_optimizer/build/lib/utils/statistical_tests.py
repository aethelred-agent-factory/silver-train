import numpy as np
import pandas as pd
import logging
from scipy.stats import ttest_ind

class StatisticalTests:
    """
    Provides functions for statistical tests, like bootstrap confidence intervals.
    """
    def __init__(self):
        logging.info("Initialized StatisticalTests.")

    def bootstrap_ci(self, data: pd.Series, metric_func, iterations=2000, confidence_level=0.95) -> tuple:
        """
        Calculates a bootstrap confidence interval for a given metric.
        
        Args:
            data: A pandas Series of values to sample from.
            metric_func: A function that takes a pandas Series and returns a single metric.
            iterations: Number of bootstrap samples.
            confidence_level: The confidence level for the interval (e.g., 0.95 for 95%).
            
        Returns:
            A tuple (lower_bound, upper_bound) of the confidence interval.
        """
        if len(data) == 0:
            return (np.nan, np.nan)

        bootstrap_samples = []
        for _ in range(iterations):
            sample = data.sample(n=len(data), replace=True)
            bootstrap_samples.append(metric_func(sample))

        # Calculate the confidence interval
        lower_bound = np.percentile(bootstrap_samples, (1 - confidence_level) / 2 * 100)
        upper_bound = np.percentile(bootstrap_samples, (1 + confidence_level) / 2 * 100)
        
        logging.info(f"Bootstrap CI ({confidence_level*100}%): [{lower_bound:.4f}, {upper_bound:.4f}]")
        return (lower_bound, upper_bound)

    def permutation_test(self, data_a: pd.Series, data_b: pd.Series, metric_func, permutations=1000) -> float:
        """
        Performs a permutation test to assess if two samples come from the same distribution.
        
        Args:
            data_a, data_b: Pandas Series of values for the two samples.
            metric_func: A function that takes a pandas Series and returns a single metric.
            permutations: Number of permutations.
            
        Returns:
            The p-value of the test.
        """
        combined_data = pd.concat([data_a, data_b])
        observed_diff = metric_func(data_a) - metric_func(data_b)

        diffs = []
        for _ in range(permutations):
            permuted_data = combined_data.sample(frac=1, replace=False)
            perm_a = permuted_data.iloc[:len(data_a)]
            perm_b = permuted_data.iloc[len(data_a):]
            diffs.append(metric_func(perm_a) - metric_func(perm_b))

        p_value = np.sum(np.abs(diffs) >= np.abs(observed_diff)) / permutations
        
        logging.info(f"Permutation test p-value: {p_value:.4f}")
        return p_value

    def t_test(self, data_a: pd.Series, data_b: pd.Series, equal_var=False) -> tuple:
        """
        Performs an independent t-test on two samples.
        
        Args:
            data_a, data_b: Pandas Series of values for the two samples.
            equal_var: Assume equal variances (True) or not (False).
            
        Returns:
            A tuple (t_statistic, p_value).
        """
        t_stat, p_value = ttest_ind(data_a, data_b, equal_var=equal_var)
        logging.info(f"Independent t-test: t-statistic={t_stat:.4f}, p-value={p_value:.4f}")
        return t_stat, p_value
