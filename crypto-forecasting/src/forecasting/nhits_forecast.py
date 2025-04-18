import os
import logging
import pandas as pd
from neuralforecast import NeuralForecast
from neuralforecast.models import NHITS
from neuralforecast.losses.pytorch import MAE
from data_handling.data_fetcher import BinanceDataFetcher
from data_handling.feature_creation import FeatureCreator
from forecasting.result_plotting import ResultPlotter


class NHitsForecaster:

    def __init__(self, symbol="ALGOUSDT", timeframe="1h"):
        """Initialize the forecaster with improved configurations."""

        self.symbol = symbol
        self.timeframe = timeframe
        self.use_gpu = bool(os.environ.get("USE_GPU"))
        self.output_path = str(os.environ.get("OUTPUT_PATH"))
        self.fetcher = BinanceDataFetcher()
        self.model = None
        self.y_df = None
        self.ohlcv_df = None
        self.forecast_df = None

        # create absolute input sizes
        self.timeframe_configs = {
            "15m": {"horizon": 96, "input_size": 96 * 7, "freq": "15min"},
            "1h": {"horizon": 24, "input_size": 168, "freq": "h"},
            "4h": {"horizon": 42, "input_size": 6 * 30, "freq": "4h"},
            "1d": {"horizon": 30, "input_size": 365, "freq": "D"},
        }

        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            # This handler directs logs to sys.stderr (console)
            handlers=[logging.StreamHandler()],
        )

    def prepare_data(self):
        """
        Fetch, clean, and prepare data with enhanced features.
        """

        logging.info(f"Preparing {self.timeframe} data for {self.symbol}...")

        try:
            # Try to load existing data
            data_dict = self.fetcher.load_multi_timeframe_from_csv(
                self.symbol, timeframe_filter=self.timeframe
            )
            if self.timeframe not in data_dict:
                raise ValueError(f"No data found for {self.timeframe}")
            ohlcv_df = data_dict[self.timeframe]
            self.ohlcv_df = ohlcv_df
        except Exception as e:
            logging.info(f"Error loading existing data: {e}")
            logging.info("Fetching new data from Binance...")
            data_dict = self.fetcher.fetch_multi_timeframe(
                symbol=self.symbol, timeframe_filter=self.timeframe
            )
            ohlcv_df = data_dict[self.timeframe]

        f_engineer = FeatureCreator(self.ohlcv_df)
        df_features = f_engineer.create_nhits_features()

        # Convert to Nixtla format (unique_id, ds, y)
        y_df = pd.DataFrame(
            {
                "unique_id": f"{self.symbol}_{self.timeframe}",
                "ds": df_features.index,
                "y": df_features["target_next_return"],
            }
        )

        # Add features as additional columns if they exist
        feature_columns = f_engineer.get_all_feature_names()

        for col in feature_columns:
            if col in df_features.columns:
                y_df[col] = df_features[col]

        logging.info(
            f"Prepared {len(y_df)} data points with "
            + f" {sum([1 for col in feature_columns if col in y_df.columns])}"
            + f"additional features"
        )

        y_df = y_df.dropna()
        self.y_df = y_df
        logging.info("Preparation successful")
        return y_df

    def train_model(self):
        """
        Train the NHITS model with simplified configuration.
        """
        # Get data with enhanced features

        if self.y_df is None:
            raise ValueError("Error loading data for training")

        data_df = self.y_df

        # Get configuration for this timeframe
        config = self.timeframe_configs[self.timeframe]
        horizon = config["horizon"]
        input_size = config["input_size"]
        freq = config["freq"]

        # Create NHITS model with simpler configuration
        model = NHITS(
            h=horizon,
            input_size=input_size,
            loss=MAE(),
            max_steps=1000,
            val_check_steps=50,
            early_stop_patience_steps=0,  # Disable early stopping with 0
            dropout_prob_theta=0.1,
            n_blocks=[1, 1, 1],
            n_pool_kernel_size=[2, 2, 2],
            n_freq_downsample=[2, 2, 1],
            scaler_type="minmax",  # best results
            random_seed=42,
            accelerator="gpu" if self.use_gpu else "cpu",
        )

        # Initialize and train model
        nf = NeuralForecast(models=[model], freq=freq)
        logging.info("Training model... (this may take several minutes)")
        nf.fit(df=data_df)

        # Store the model
        self.model = nf

    def predict(self):
        """
        Generate forecasts using the trained model.
        """

        if self.model is None:
            raise ValueError("Model has not been trained. Call train_model() first.")

        # Generate forecasts
        logging.info("Generating forecasts...")
        forecasts = self.model.predict()

        # Clean column names
        forecasts.columns = forecasts.columns.str.replace("-median", "")

        # Store forecasts
        self.forecast_df = forecasts
        save_path = f"{self.output_path}/forecasts/{self.symbol}_forecast_df.csv"
        forecasts.to_csv(save_path)
        logging.info(f"Prediction successful, forecasting df saved to {save_path}")

    def run_forecast(self):
        """
        Run the complete enhanced forecasting pipeline.
        """

        try:
            # Prepare data
            logging.info("Step 1: Preparing data for training")
            self.prepare_data()
            # Train model
            logging.info("Step 2: Training neural forecasting model...")
            self.train_model()

            # Generate forecasts
            logging.info("Step 3: Generating price forecasts...")
            self.predict()

            # Plot forecasts
            logging.info("Step 4: Creating visualization...")
            plotter = ResultPlotter(
                self.symbol, self.ohlcv_df, self.y_df, self.forecast_df
            )
            plotter.plot_absolute_prices(
                timeframe_configs=self.timeframe_configs, timeframe=self.timeframe
            )

            logging.info("Forecasting pipeline successful")
        except Exception as e:
            logging.error(f"Error in forecasting pipeline: {e}")
