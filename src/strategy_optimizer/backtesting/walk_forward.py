import logging

import pandas as pd


class WalkForward:
    """
    Implements walk-forward validation for robust strategy testing.
    """

    def __init__(self, config, backtest_engine):
        self.config = config
        self.backtest_engine = backtest_engine
        logging.info("Initialized WalkForward.")

    def split_datasets(self, data: pd.DataFrame, cal_pct=60, val_pct=20, test_pct=20):
        """
        Splits the data into calibration, validation, and test sets.
        """
        if cal_pct + val_pct + test_pct != 100:
            raise ValueError("Percentages must sum to 100.")

        n = len(data)
        cal_end = int(n * (cal_pct / 100))
        val_end = int(n * ((cal_pct + val_pct) / 100))

        calibration_set = data.iloc[:cal_end]
        validation_set = data.iloc[cal_end:val_end]
        test_set = data.iloc[val_end:]

        logging.info(
            f"Split dataset into: Calibration ({len(calibration_set)}), "
            f"Validation ({len(validation_set)}), Test ({len(test_set)})"
        )

        return calibration_set, validation_set, test_set

    def rolling_walk_forward(
        self,
        symbol: str,
        start_date: str,
        end_date: str,
        params: dict,
        window_size: int,
        step_size: int,
    ):
        """
        Performs a rolling walk-forward analysis.

        In each iteration, it trains on a window of data and tests on the next segment.
        This is a placeholder and would be much more complex in a real system.
        """
        logging.info("Starting rolling walk-forward analysis.")

        all_data = self.backtest_engine.signal_generator.indicator_engine.market_data_bus.get_candles(
            symbol, start_date, end_date
        )

        if all_data.empty:
            logging.error("No data for walk-forward analysis.")
            return

        n = len(all_data)
        results = []

        for i in range(0, n - window_size, step_size):
            train_window = all_data.iloc[i : i + window_size]
            test_window = all_data.iloc[i + window_size : i + window_size + step_size]

            if test_window.empty:
                continue

            # In a real scenario, you would optimize parameters on the train_window
            # and then test the optimal parameters on the test_window.
            # For now, we'll just run the backtest with the given params.

            logging.info(
                f"Running walk-forward iteration on test window: "
                f"{test_window.iloc[0]['timestamp']} to {test_window.iloc[-1]['timestamp']}"
            )

            result = self.backtest_engine.run_backtest(
                symbol,
                train_window.iloc[0]["timestamp"].isoformat(),
                test_window.iloc[-1]["timestamp"].isoformat(),
                params,
            )
            if result:
                results.append(result)

        logging.info("Walk-forward analysis complete.")
        return results
