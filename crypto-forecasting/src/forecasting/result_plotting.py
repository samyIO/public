import logging
import os
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates


class ResultPlotter:

    def __init__(self, symbol, ohlcv_df, y_df, forecast_df):
        self.symbol = symbol
        self.ohlcv_df = ohlcv_df
        self.y_df = y_df
        self.forecast_df = forecast_df

    def convert_returns_to_prices(self):
        """
        Convert percentage returns in y_df and forecast_df back to absolute prices.

        Returns:
        --------
        tuple: (historical_prices, forecast_prices)
            DataFrames containing the historical and forecasted absolute prices
        """

        logging.info("converting returns to absolute prices")
        if self.y_df is None or self.forecast_df is None:
            raise ValueError(
                "Both historical data and forecast data "
                "must be available. Run train_model() and predict() first."
            )

        # Get the last known closing price
        last_price = self.ohlcv_df["close"].iloc[-1]
        last_date = self.ohlcv_df.index[-1]

        logging.info(f"Last known price for {self.symbol} at {last_date}: {last_price}")

        # Create a copy of the dataframes to avoid modifying originals
        y_df_copy = self.y_df.copy()
        forecast_df_copy = self.forecast_df.copy()

        # Add absolute price column to historical data
        y_df_copy["absolute_price"] = None

        # Converting returns to prices requires working backwards from the last known price
        # For the historical data, we need the actual values, not the predicted next return

        # Get the original data again to match timestamps
        historical_prices = pd.DataFrame(
            {"ds": self.ohlcv_df["timestamp"], "price": self.ohlcv_df["close"]}
        )

        # Merge with the y_df to get matching timestamps
        y_df_with_prices = pd.merge(y_df_copy, historical_prices, on="ds", how="left")

        # For forecast data, we need to calculate prices based on returns
        # Initialize the first forecasted price using the last known price
        current_price = last_price
        forecast_df_copy["absolute_price"] = None

        # The forecast column name in forecast_df
        forecast_column = f"NHITS"

        # Calculate absolute prices for each forecasted period
        for idx, row in forecast_df_copy.iterrows():
            # Apply the forecasted return to get the next price
            # If return is 0.01 (1%), then new_price = current_price * (1 + 0.01)
            return_value = row[forecast_column]
            new_price = current_price * (1 + return_value)
            forecast_df_copy.at[idx, "absolute_price"] = new_price
            current_price = new_price

        logging.info("Conversion successful")
        return y_df_with_prices, forecast_df_copy

    def plot_absolute_prices(
        self, figsize=(14, 7), title=None, timeframe_configs=None, timeframe="1h"
    ):
        """
        Plot historical and forecasted prices in absolute terms.

        Parameters:
        -----------
        save_path : str, optional
            Path to save the figure. If None, the figure is displayed but not saved.
        figsize : tuple, optional
            Figure size as (width, height) in inches.
        title : str, optional
            Custom title for the plot. If None, a default title is used.

        Returns:
        --------
        fig : matplotlib.figure.Figure
            The generated figure.
        """

        logging.info("Plotting absolute prices")
        if timeframe_configs is None:
            raise ValueError("Missing timeframe configs for plotting")

        # Convert returns to absolute prices
        historical_df, forecast_df = self.convert_returns_to_prices()

        if historical_df is None or forecast_df is None:
            raise ValueError("Failed to convert returns to prices.")

        # Set up figure
        fig, ax = plt.subplots(figsize=figsize)

        # Get the last date from historical data
        last_date = historical_df["ds"].max()
        logging.info(f"last known date extracted: {last_date}")
        # Filter historical data to not be too crowded (show only recent history)
        config = timeframe_configs[timeframe]
        history_points = min(config["input_size"], len(historical_df))
        recent_history = historical_df.iloc[-history_points:]
        logging.info(f"Chosen timeframe: {config}")
        # Plot historical prices
        ax.plot(
            recent_history["ds"],
            recent_history["price"],
            label="Historical",
            color="blue",
            linewidth=2,
        )

        # Plot forecasted prices
        ax.plot(
            forecast_df["ds"],
            forecast_df["absolute_price"],
            label="Forecast",
            color="red",
            linestyle="--",
            linewidth=2,
        )

        # Add vertical line to mark the separation between historical and forecast
        ax.axvline(x=last_date, color="gray", linestyle="-", linewidth=1)

        # Customize plot
        if title is None:
            title = f"{self.symbol} Price Forecast ({timeframe} timeframe)"
        ax.set_title(title, fontsize=16)
        ax.set_xlabel("Date", fontsize=12)
        ax.set_ylabel("Price (USD)", fontsize=12)
        ax.legend(fontsize=12)
        ax.grid(True, alpha=0.3)

        # Format x-axis with date and hour formatting

        # Choose the appropriate date format based on timeframe
        if timeframe in ["15m", "1h"]:
            # For shorter timeframes, show date and hour
            date_format = mdates.DateFormatter("%m-%d %H:%M")
            # Set major ticks every 6 hours
            ax.xaxis.set_major_locator(mdates.HourLocator(interval=6))
        elif timeframe == "4h":
            # For 4h timeframe, show date and hour
            date_format = mdates.DateFormatter("%m-%d %H:%M")
            # Set major ticks every day
            ax.xaxis.set_major_locator(mdates.DayLocator(interval=1))
        else:
            # For daily timeframe, show only dates
            date_format = mdates.DateFormatter("%Y-%m-%d")
            # Set major ticks every 5 days
            ax.xaxis.set_major_locator(mdates.DayLocator(interval=5))

        ax.xaxis.set_major_formatter(date_format)

        # Rotate x-axis labels for better readability
        plt.setp(ax.get_xticklabels(), rotation=45, ha="right")

        # Add annotations
        horizon_text = f"Forecast Horizon: {config['horizon']} periods"
        plt.figtext(0.02, 0.02, horizon_text, fontsize=10)

        # Save the figure if a path is provided
        output_path = str(os.environ.get("OUTPUT_PATH"))
        save_path = f"{output_path}/plots/{self.symbol}_{timeframe}_forecast"
        if save_path:
            plt.savefig(save_path, bbox_inches="tight", dpi=300)
            logging.info(f"Figure saved to {save_path}")

        plt.tight_layout()
        logging.info("Plotting successful")

        return fig
