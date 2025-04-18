import logging
import numpy as np
import ta
import os


class FeatureCreator:

    def __init__(self, df_ohlcv):
        self.df_ohlcv = df_ohlcv
        self.output_path = str(os.environ.get("OUTPUT_PATH"))

    def create_nhits_features(self):
        """
        Create a feature dataframe for N-HITS model from OHLCV data.

        Parameters:
        -----------
        df_ohlcv : pandas.DataFrame
            DataFrame with columns: timestamp (index), open, high, low, close, volume

        Returns:
        --------
        pandas.DataFrame
            DataFrame with all calculated features
        """

        logging.info("Creating features for training...")
        # Make a copy to avoid modifying the original
        df = self.df_ohlcv.copy()

        # Ensure timestamp is the index
        if "timestamp" in df.columns:
            df = df.set_index("timestamp")

        logging.info("Calculating relevant technical indicators")
        # Calculate basic price features
        df["returns"] = df["close"].pct_change()
        df["log_returns"] = np.log(df["close"] / df["close"].shift(1))

        # Calculate high-low range
        df["high_low_range"] = (df["high"] - df["low"]) / df["low"]

        # Lagged features
        df["high_low_range_lag_1"] = df["high_low_range"].shift(1)
        df["high_low_range_lag_3"] = df["high_low_range"].shift(3)

        for i in range(1, 6):
            df[f"volume_lag_{i}"] = df["volume"].shift(i)

        # Volume features
        df["volume_sma_10"] = df["volume"].rolling(window=10).mean()
        df["volume_delta_pct"] = df["volume"].pct_change() * 100

        # Calendar features
        # todo: this is only for daily data, adjust for hourly and 15 min aswell
        df["day_of_week"] = df.index.dayofweek
        df["day_sin"] = np.sin(df["day_of_week"] * (2 * np.pi / 7))
        df["day_cos"] = np.cos(df["day_of_week"] * (2 * np.pi / 7))

        # Technical indicators
        # RSI
        df["rsi_14"] = ta.momentum.RSIIndicator(df["close"], window=14).rsi()

        # MACD
        macd = ta.trend.MACD(df["close"])
        df["macd_histogram"] = macd.macd_diff()

        # EMAs and slope
        df["ema_10"] = ta.trend.EMAIndicator(df["close"], window=10).ema_indicator()
        df["slope_ema_10"] = df["ema_10"].diff()

        # SMA for distance calculation
        df["sma_50"] = ta.trend.SMAIndicator(df["close"], window=50).sma_indicator()
        df["distance_to_sma_50"] = (df["close"] - df["sma_50"]) / df["sma_50"] * 100

        # Volatility indicators
        bollinger = ta.volatility.BollingerBands(df["close"], window=20, window_dev=2)
        df["bollinger_bandwidth"] = bollinger.bollinger_wband()

        atr = ta.volatility.AverageTrueRange(
            df["high"], df["low"], df["close"], window=14
        )
        df["atr_14"] = atr.average_true_range()
        df["atr_percent_14"] = df["atr_14"] / df["close"] * 100

        # prediction target
        df["target_next_return"] = df["close"].pct_change(-1)

        # Drop NaN values that result from calculations
        df = df.dropna()

        print(f"All features: \n {df.columns}")

        # Select only the features we got from corr analysis
        selected_features = [
            "close",
            "returns",
            "log_returns",
            "high_low_range_lag_1",
            "high_low_range_lag_3",
            "volume_lag_1",
            "volume_lag_3",
            "volume_lag_4",
            "volume_lag_5",
            "volume_sma_10",
            "volume_delta_pct",
            "rsi_14",
            "macd_histogram",
            "slope_ema_10",
            "distance_to_sma_50",
            "bollinger_bandwidth",
            "atr_percent_14",
            "day_sin",
            "day_cos",
            "target_next_return",
        ]
        feature_df = df[selected_features]
        save_path = f"{self.output_path}/features/feature_df.csv"
        feature_df.to_csv(save_path)
        logging.info(f"Feature creation successful, feature_df saved to: {save_path}")
        return df[selected_features]

    def get_all_feature_names(self):
        return [
            "close",
            "returns",
            "log_returns",
            "high_low_range_lag_1",
            "high_low_range_lag_3",
            "volume_lag_1",
            "volume_lag_3",
            "volume_lag_4",
            "volume_lag_5",
            "volume_sma_10",
            "volume_delta_pct",
            "rsi_14",
            "macd_histogram",
            "slope_ema_10",
            "distance_to_sma_50",
            "bollinger_bandwidth",
            "atr_percent_14",
            "day_sin",
            "day_cos",
        ]

    def get_hist_exog_col_names(self):
        return [
            "close",
            "returns",
            "log_returns",
            "high_low_range_lag_1",
            "high_low_range_lag_3",
            "volume_lag_1",
            "volume_lag_3",
            "volume_lag_4",
            "volume_lag_5",
            "volume_sma_10",
            "volume_delta_pct",
            "rsi_14",
            "macd_histogram",
            "slope_ema_10",
            "distance_to_sma_50",
            "bollinger_bandwidth",
            "atr_percent_14",
        ]

    def get_future_exog_col_names(self):
        return ["day_sin", "day_cos"]
