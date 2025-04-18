import unittest
import os
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import sys
from unittest.mock import patch
import logging

from src.data_handling.data_validator import DataValidator


class TestDataValidator(unittest.TestCase):
    def setUp(self):
        """Set up test environment before each test method."""
        # Create sample OHLCV data for testing
        self.regular_df = self.create_sample_ohlcv_data()
        self.problematic_df = self.create_problematic_ohlcv_data()

        # Initialize the DataValidator
        self.validator = DataValidator(price_decimals=8, volume_decimals=2)

        # Disable logging during tests
        logging.disable(logging.CRITICAL)

    def tearDown(self):
        """Clean up after each test."""
        # Re-enable logging
        logging.disable(logging.NOTSET)

    def create_sample_ohlcv_data(self):
        """Create clean sample OHLCV data for testing."""
        # Create timestamps for the last 100 hours
        timestamps = pd.date_range(start="2023-01-01", periods=100, freq="1h")

        # Generate price data (upward trend with some fluctuations)
        base_price = 10000.0
        random_state = np.random.RandomState(42)  # For reproducibility

        data = []
        current_price = base_price

        for i in range(100):
            # Random price movement
            price_change = current_price * random_state.normal(0.001, 0.01)
            current_price += price_change

            # Create OHLCV row with realistic relationships
            open_price = current_price
            close_price = current_price * (1 + random_state.normal(0, 0.005))
            high_price = max(open_price, close_price) * (
                1 + abs(random_state.normal(0, 0.003))
            )
            low_price = min(open_price, close_price) * (
                1 - abs(random_state.normal(0, 0.003))
            )
            volume = random_state.uniform(100, 1000)

            data.append(
                {
                    "timestamp": timestamps[i],
                    "open": open_price,
                    "high": high_price,
                    "low": low_price,
                    "close": close_price,
                    "volume": volume,
                }
            )

        # Create DataFrame
        df = pd.DataFrame(data)
        df.set_index("timestamp", inplace=True)

        return df

    def create_problematic_ohlcv_data(self):
        """Create OHLCV data with various issues for testing."""
        # Start with regular data
        df = self.create_sample_ohlcv_data().copy()

        # Introduce NaN values
        df.iloc[10:15, df.columns.get_indexer(["open", "close"])] = np.nan

        # Introduce duplicates by explicitly creating duplicate index values
        # We need to reset the index, duplicate a row, then set the index again
        df_reset = df.reset_index()
        duplicate_timestamp = df_reset.iloc[20]["timestamp"]
        new_row = df_reset.iloc[20].copy()
        df_reset.loc[len(df_reset)] = new_row
        df_reset.iloc[-1, df_reset.columns.get_indexer(["timestamp"])] = (
            duplicate_timestamp
        )
        df = df_reset.set_index("timestamp")

        # Introduce OHLC violations
        df.loc[df.index[30], "high"] = (
            df.loc[df.index[30], "low"] * 0.9
        )  # High less than low
        df.loc[df.index[40], "low"] = (
            df.loc[df.index[40], "open"] * 1.1
        )  # Low greater than open

        # Introduce outliers
        df.loc[df.index[50], "close"] = df.loc[df.index[50], "close"] * 5  # Price spike

        # Introduce negative values
        df.loc[df.index[60], "volume"] = -100

        # Introduce timestamp gaps (remove some rows)
        df = df.drop(df.index[70:75])

        return df

    def test_init(self):
        """Test initialization of DataValidator."""
        # Test default initialization
        validator = DataValidator()
        self.assertEqual(validator.price_decimals, 8)
        self.assertEqual(validator.volume_decimals, 2)

        # Test custom initialization
        validator = DataValidator(price_decimals=4, volume_decimals=0)
        self.assertEqual(validator.price_decimals, 4)
        self.assertEqual(validator.volume_decimals, 0)

    def test_clean_data_default(self):
        """Test clean_data method with default parameters."""
        # Use the problematic data
        cleaned_df = self.validator.clean_data(self.problematic_df)

        # Verify cleaning effects
        self.assertEqual(
            cleaned_df.isnull().sum().sum(), 0, "Should have no NaN values"
        )
        self.assertEqual(
            sum(cleaned_df.index.duplicated()), 0, "Should have no duplicates"
        )

        # Check that OHLC relationships are fixed
        self.assertTrue(
            (cleaned_df["high"] >= cleaned_df["low"]).all(), "High should be >= Low"
        )
        self.assertTrue(
            (cleaned_df["high"] >= cleaned_df["open"]).all(), "High should be >= Open"
        )
        self.assertTrue(
            (cleaned_df["high"] >= cleaned_df["close"]).all(), "High should be >= Close"
        )
        self.assertTrue(
            (cleaned_df["low"] <= cleaned_df["open"]).all(), "Low should be <= Open"
        )
        self.assertTrue(
            (cleaned_df["low"] <= cleaned_df["close"]).all(), "Low should be <= Close"
        )

        # Check rounding
        for col in self.validator.price_columns:
            decimal_count = (
                cleaned_df[col].astype(str).str.split(".").str[1].str.len().max()
            )
            self.assertLessEqual(
                decimal_count,
                self.validator.price_decimals,
                f"{col} should be rounded to {self.validator.price_decimals} decimals",
            )

        for col in self.validator.volume_columns:
            decimal_count = (
                cleaned_df[col].astype(str).str.split(".").str[1].str.len().max()
            )
            self.assertLessEqual(
                decimal_count,
                self.validator.volume_decimals,
                f"{col} should be rounded to {self.validator.volume_decimals} decimals",
            )

    def test_clean_data_with_different_fill_methods(self):
        """Test clean_data with different fill methods."""
        # Create data with NaN values
        df_with_nans = self.regular_df.copy()
        df_with_nans.iloc[
            10:15, df_with_nans.columns.get_indexer(["open", "close"])
        ] = np.nan

        fill_methods = ["ffill", "bfill", "mean", "interpolate"]

        for method in fill_methods:
            cleaned_df = self.validator.clean_data(df_with_nans, fill_method=method)
            self.assertEqual(
                cleaned_df.isnull().sum().sum(),
                0,
                f"Method {method} should fill all NaN values",
            )

    def test_handle_missing_values_invalid_method(self):
        """Test _handle_missing_values with invalid method."""
        with self.assertRaises(ValueError):
            self.validator._handle_missing_values(self.regular_df, "invalid_method")

    def test_handle_price_anomalies(self):
        """Test _handle_price_anomalies method."""
        # Create a dataset that will properly trigger the outlier detection
        # We need to create a case where:
        # 1. We have enough data for the rolling window (48 points)
        # 2. The outlier is extreme compared to historical data
        # 3. The outlier appears AFTER we have enough history

        n_points = 60
        base_price = 100

        # Create prices with a small amount of noise
        np.random.seed(42)  # For reproducibility
        noise = np.random.normal(0, 1, n_points)
        prices = base_price + noise

        # Make a copy for different columns
        open_prices = prices.copy()
        high_prices = prices * 1.05
        low_prices = prices * 0.95
        close_prices = prices.copy()

        # Create the dataframe
        index = pd.date_range(start="2023-01-01", periods=n_points, freq="1h")
        df = pd.DataFrame(
            {
                "open": open_prices,
                "high": high_prices,
                "low": low_prices,
                "close": close_prices,
                "volume": np.ones(n_points) * 1000,
            },
            index=index,
        )

        # Now, create a copy and add an extreme outlier AFTER we have 48+ points of history
        df_with_outlier = df.copy()
        outlier_idx = 50
        original_value = float(df_with_outlier.iloc[outlier_idx]["close"])

        # Set the outlier to be 20x the normal value (will be well beyond 4 std)
        df_with_outlier.loc[df_with_outlier.index[outlier_idx], "close"] = (
            original_value * 20
        )

        # Save the outlier value for comparison
        outlier_value = df_with_outlier.iloc[outlier_idx]["close"]

        # Run the anomaly detection
        with patch("logging.info"):  # Suppress logging
            result_df = self.validator._handle_price_anomalies(df_with_outlier)

        # The outlier should have been replaced with a different value
        self.assertNotEqual(
            result_df.iloc[outlier_idx]["close"],
            outlier_value,
            f"The outlier ({outlier_value}) should have been replaced",
        )

        # The replaced value should be closer to the normal range
        self.assertLess(
            abs(result_df.iloc[outlier_idx]["close"] - original_value),
            abs(outlier_value - original_value),
            "The replaced value should be closer to the normal price level",
        )

    def test_validate_ohlc(self):
        """Test _validate_ohlc method."""
        # Create data with OHLC violations
        df_with_violations = self.regular_df.copy()
        df_with_violations.iloc[
            30, df_with_violations.columns.get_indexer(["high"])
        ] = 9000  # Lower than expected
        df_with_violations.iloc[30, df_with_violations.columns.get_indexer(["low"])] = (
            11000  # Higher than expected
        )

        # Run validation
        fixed_df = self.validator._validate_ohlc(df_with_violations)

        # Check that violations are fixed
        self.assertTrue((fixed_df["high"] >= fixed_df["low"]).all())
        self.assertTrue((fixed_df["high"] >= fixed_df["open"]).all())
        self.assertTrue((fixed_df["high"] >= fixed_df["close"]).all())
        self.assertTrue((fixed_df["low"] <= fixed_df["open"]).all())
        self.assertTrue((fixed_df["low"] <= fixed_df["close"]).all())

    def test_round_numbers(self):
        """Test _round_numbers method."""
        # Create data with many decimal places
        df_unrounded = self.regular_df.copy()
        df_unrounded["open"] = df_unrounded["open"] + 0.123456789
        df_unrounded["volume"] = df_unrounded["volume"] + 0.123456789

        # Round numbers
        rounded_df = self.validator._round_numbers(df_unrounded)

        # Check that price columns are rounded to price_decimals
        for col in self.validator.price_columns:
            decimal_places = (
                rounded_df[col].astype(str).str.split(".").str[1].str.len().max()
            )
            self.assertLessEqual(decimal_places, self.validator.price_decimals)

        # Check that volume columns are rounded to volume_decimals
        for col in self.validator.volume_columns:
            decimal_places = (
                rounded_df[col].astype(str).str.split(".").str[1].str.len().max()
            )
            self.assertLessEqual(decimal_places, self.validator.volume_decimals)

    def test_validate_data(self):
        """Test validate_data method."""
        # Test with clean data
        results = self.validator.validate_data(self.regular_df)
        self.assertFalse(results["has_missing_values"])
        self.assertFalse(results["has_duplicates"])
        self.assertEqual(results["ohlc_violations"], "No OHLC violations")
        self.assertEqual(results["negative_values"], "No negative values")

        # Test with problematic data
        results = self.validator.validate_data(self.problematic_df)
        self.assertTrue(results["has_missing_values"])
        self.assertTrue(results["has_duplicates"])
        self.assertIn("OHLC violations found", results["ohlc_violations"])
        self.assertIn("Negative values found", results["negative_values"])
        self.assertIn("gaps", results["timestamp_gaps"])

    def test_check_timestamp_gaps(self):
        """Test _check_timestamp_gaps method."""
        # Create a dataframe with consistent intervals
        # The current implementation is creating timestamps with hour intervals
        # but the test might be too sensitive to the exact timestamps
        timestamps = pd.date_range(start="2023-01-01", periods=100, freq="1h")
        df_no_gaps = self.regular_df.copy()
        df_no_gaps.index = timestamps

        result = self.validator._check_timestamp_gaps(df_no_gaps)
        self.assertEqual(result, "No gaps found")

        # Test with gaps
        df_with_gaps = df_no_gaps.copy()
        df_with_gaps = df_with_gaps.drop(df_with_gaps.index[10:15])
        result = self.validator._check_timestamp_gaps(df_with_gaps)
        self.assertIn("Found", result)
        self.assertIn("gaps", result)

        # Test with too few rows
        single_row_df = self.regular_df.iloc[[0]]
        result = self.validator._check_timestamp_gaps(single_row_df)
        self.assertEqual(result, "Too few rows to check gaps")

    def test_check_ohlc_violations(self):
        """Test _check_ohlc_violations method."""
        # Test with no violations
        result = self.validator._check_ohlc_violations(self.regular_df)
        self.assertEqual(result, "No OHLC violations")

        # Test with violations
        df_with_violations = self.regular_df.copy()
        df_with_violations.loc[df_with_violations.index[10], "high"] = (
            9000  # Set high below other values
        )
        result = self.validator._check_ohlc_violations(df_with_violations)
        self.assertEqual(result, "OHLC violations found")

    def test_check_negative_values(self):
        """Test _check_negative_values method."""
        # Test with no negative values
        result = self.validator._check_negative_values(self.regular_df)
        self.assertEqual(result, "No negative values")

        # Test with negative values
        df_with_negatives = self.regular_df.copy()
        df_with_negatives.loc[df_with_negatives.index[10], "volume"] = -100
        result = self.validator._check_negative_values(df_with_negatives)
        self.assertEqual(result, "Negative values found")


if __name__ == "__main__":
    unittest.main()
