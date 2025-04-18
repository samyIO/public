import logging
import pandas as pd
import numpy as np
from typing import Dict, Union


class DataValidator:

    def __init__(self, price_decimals: int = 8, volume_decimals: int = 2):
        self.price_decimals = price_decimals
        self.volume_decimals = volume_decimals
        self.price_columns = ["open", "high", "low", "close"]
        self.volume_columns = ["volume"]

    def clean_data(self, df: pd.DataFrame, fill_method: str = "ffill") -> pd.DataFrame:
        """
        Clean the data by handling missing values, outliers,
        and standardizing decimals.

        Args:
            df: Input DataFrame with crypto data
            fill_method: Method to fill missing values
            ('ffill', 'bfill', 'mean', or 'interpolate')

        Returns:
            Cleaned DataFrame
        """

        logging.info("Cleaning up data")
        # Create a copy to avoid modifying the original data
        df_cleaned = df.copy()

        # 1. Handle missing values
        df_cleaned = self._handle_missing_values(df_cleaned, fill_method)

        # 2. Remove duplicates
        df_cleaned = df_cleaned.drop_duplicates()

        # 3. Check for price anomalies
        df_cleaned = self._handle_price_anomalies(df_cleaned)

        # 4. Validate OHLC relationships
        df_cleaned = self._validate_ohlc(df_cleaned)

        # 5. Round numbers
        df_cleaned = self._round_numbers(df_cleaned)

        # 6. Sort by timestamp
        df_cleaned = df_cleaned.sort_index()

        logging.info("Clean-up successful")

        return df_cleaned

    def _handle_missing_values(self, df: pd.DataFrame, method: str) -> pd.DataFrame:
        """Handle missing values using the specified method."""

        logging.info("Handle missing values")
        if method == "mean":
            return df.fillna(df.mean())
        elif method == "ffill":
            return df.ffill().bfill()  # Use bfill as backup
        elif method == "bfill":
            return df.bfill().ffill()  # Use ffill as backup
        elif method == "interpolate":
            return df.interpolate(method="time").ffill().bfill()
        else:
            raise ValueError(f"Unsupported fill method: {method}")

    def _handle_price_anomalies(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Detect and handle price anomalies using rolling statistics.
        Marks extreme outliers (beyond 4 standard deviations) as NaN
        and interpolates them.
        """

        logging.info("Handle anomalies")
        for col in self.price_columns:
            # Calculate rolling mean and std
            rolling_mean = df[col].rolling(window=48, min_periods=1).mean()
            rolling_std = df[col].rolling(window=48, min_periods=1).std()

            # Create masks for upper and lower bounds (4 standard deviations)
            upper_bound = rolling_mean + 4 * rolling_std
            lower_bound = rolling_mean - 4 * rolling_std

            # Mark outliers as NaN
            df.loc[(df[col] > upper_bound) | (df[col] < lower_bound), col] = np.nan

            # Interpolate marked values
            df[col] = df[col].interpolate(method="time").ffill().bfill()

        return df

    def _validate_ohlc(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Validate and fix OHLC relationships:
        - High should be the highest price
        - Low should be the lowest price
        - Open and Close should be between High and Low
        """

        logging.info("Validating ohlc")
        df["high"] = df[["high", "low", "open", "close"]].max(axis=1)
        df["low"] = df[["high", "low", "open", "close"]].min(axis=1)

        return df

    def _round_numbers(self, df: pd.DataFrame) -> pd.DataFrame:
        """Round numbers to specified decimal places."""

        # Round price columns
        for col in self.price_columns:
            df[col] = df[col].round(self.price_decimals)

        # Round volume columns
        for col in self.volume_columns:
            df[col] = df[col].round(self.volume_decimals)

        return df

    def validate_data(self, df: pd.DataFrame) -> Dict[str, Union[bool, str]]:
        """
        Perform validation checks on the data and return a dictionary of results.

        Returns:
            Dictionary containing validation results
        """

        logging.info("Validating data..")
        results = {
            "has_missing_values": df.isnull().any().any(),
            "has_duplicates": df.index.duplicated().any(),
            "timestamp_gaps": self._check_timestamp_gaps(df),
            "ohlc_violations": self._check_ohlc_violations(df),
            "negative_values": self._check_negative_values(df),
        }
        logging.info("Validation successful")
        return results

    def _check_timestamp_gaps(self, df: pd.DataFrame) -> str:
        """Check for gaps in timestamp sequence."""
        if len(df) < 2:
            return "Too few rows to check gaps"

        # Calculate expected interval from first two rows
        expected_interval = df.index[1] - df.index[0]
        actual_intervals = df.index[1:] - df.index[:-1]

        gaps = (actual_intervals != expected_interval).sum()
        return f"Found {gaps} timestamp gaps" if gaps > 0 else "No gaps found"

    def _check_ohlc_violations(self, df: pd.DataFrame) -> str:
        """Check for OHLC relationship violations."""
        violations = (
            (df["high"] < df["low"]).any()
            or (df["high"] < df["open"]).any()
            or (df["high"] < df["close"]).any()
            or (df["low"] > df["open"]).any()
            or (df["low"] > df["close"]).any()
        )
        return "OHLC violations found" if violations else "No OHLC violations"

    def _check_negative_values(self, df: pd.DataFrame) -> str:
        """Check for negative values in price and volume."""
        has_negative = (df[self.price_columns + self.volume_columns] < 0).any().any()
        return "Negative values found" if has_negative else "No negative values"
