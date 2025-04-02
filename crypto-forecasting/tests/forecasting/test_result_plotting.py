import unittest
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
import matplotlib.dates as mdates
import os
from unittest.mock import patch, MagicMock

from src.forecasting.result_plotting import ResultPlotter


class TestResultPlotter(unittest.TestCase):
    def setUp(self):
        """Set up test environment before each test method."""
        # Use non-interactive backend for testing
        plt.switch_backend('Agg')
        
        # Create plots directory if it doesn't exist
        os.makedirs('plots', exist_ok=True)
        
        # Set up timeframe configs for testing
        self.timeframe_configs = {
            '15m': {'input_size': 96, 'horizon': 24},
            '1h': {'input_size': 48, 'horizon': 12},
            '4h': {'input_size': 36, 'horizon': 9},
            '1d': {'input_size': 20, 'horizon': 5}
        }
        
        # Create mock data directly without loading from files
        self.ohlcv_df_1h = self.create_mock_ohlcv_data('1h')
        
        # Create sample y_df and forecast_df with the same index as ohlcv_df
        self.y_df = self.create_y_df(self.ohlcv_df_1h)
        self.forecast_df = self.create_forecast_df(self.ohlcv_df_1h)
        
        # Create ResultPlotter instance
        self.symbol = 'BTC'
        self.plotter = ResultPlotter(
            symbol=self.symbol,
            ohlcv_df=self.ohlcv_df_1h,
            y_df=self.y_df,
            forecast_df=self.forecast_df
        )
    
    def create_mock_ohlcv_data(self, timeframe):
        """Create mock OHLCV data for testing."""
        # Determine time delta based on timeframe
        delta_map = {
            '15m': timedelta(minutes=15),
            '1h': timedelta(hours=1),
            '4h': timedelta(hours=4),
            '1d': timedelta(days=1)
        }
        delta = delta_map.get(timeframe, timedelta(hours=1))
        
        # Create timestamps
        input_size = self.timeframe_configs[timeframe]['input_size']
        horizon = self.timeframe_configs[timeframe]['horizon']
        total_periods = input_size + horizon
        
        end_date = datetime.now()
        timestamps = [end_date - delta * i for i in range(total_periods, 0, -1)]
        timestamps.sort()
        
        # Create price data (simple upward trend with some noise)
        base_price = 50000  # Starting price for BTC mock
        price_data = [base_price * (1 + 0.001 * i + 0.0005 * np.random.randn()) for i in range(len(timestamps))]
        
        # Create OHLCV dataframe
        df = pd.DataFrame({
            'timestamp': timestamps,
            'open': price_data,
            'high': [p * (1 + 0.001 * np.random.random()) for p in price_data],
            'low': [p * (1 - 0.001 * np.random.random()) for p in price_data],
            'close': price_data,
            'volume': [100000 * np.random.random() for _ in range(len(timestamps))]
        })
        
        # Keep timestamp both as a column and as the index
        # This is needed because ResultPlotter accesses self.ohlcv_df['timestamp']
        df.set_index('timestamp', inplace=True, drop=False)
        
        return df
    
    def create_y_df(self, ohlcv_df):
        """Create sample y_df with returns."""
        # Calculate simple returns
        returns = ohlcv_df['close'].pct_change().dropna()
        
        # Create y_df DataFrame with 'ds' and 'y' columns
        y_df = pd.DataFrame({
            'ds': returns.index,
            'y': returns.values
        })
        
        return y_df
    
    def create_forecast_df(self, ohlcv_df):
        """Create sample forecast_df with predicted returns."""
        # Get the last date from the OHLCV data
        last_date = ohlcv_df.index[-1]
        
        # Determine timeframe from the data
        if len(ohlcv_df) > 1:
            time_diff = ohlcv_df.index[1] - ohlcv_df.index[0]
            
            # Determine which timeframe config to use
            if time_diff.total_seconds() == 15 * 60:
                horizon = self.timeframe_configs['15m']['horizon']
                delta = timedelta(minutes=15)
            elif time_diff.total_seconds() == 60 * 60:
                horizon = self.timeframe_configs['1h']['horizon']
                delta = timedelta(hours=1)
            elif time_diff.total_seconds() == 4 * 60 * 60:
                horizon = self.timeframe_configs['4h']['horizon']
                delta = timedelta(hours=4)
            else:
                horizon = self.timeframe_configs['1d']['horizon']
                delta = timedelta(days=1)
        else:
            # Default to 1h if we can't determine
            horizon = self.timeframe_configs['1h']['horizon']
            delta = timedelta(hours=1)
        
        # Generate future dates
        future_dates = [last_date + delta * (i+1) for i in range(horizon)]
        
        # Generate some mock forecasted returns
        forecast_returns = [0.001 * np.random.randn() for _ in range(horizon)]
        
        # Create forecast DataFrame
        forecast_df = pd.DataFrame({
            'ds': future_dates,
            'NHITS': forecast_returns
        })
        
        return forecast_df
    
    def tearDown(self):
        """Clean up after each test."""
        os.rmdir("plots")
        plt.close('all')
    
    def test_convert_returns_to_prices(self):
        """Test the convert_returns_to_prices method."""
        # Execute the method
        historical_df, forecast_df = self.plotter.convert_returns_to_prices()
        
        # Verify the output structure
        self.assertIsInstance(historical_df, pd.DataFrame)
        self.assertIsInstance(forecast_df, pd.DataFrame)
        
        # Check that historical_df has the expected columns
        self.assertIn('ds', historical_df.columns)
        self.assertIn('y', historical_df.columns)
        self.assertIn('price', historical_df.columns)
        
        # Check that forecast_df has the expected columns
        self.assertIn('ds', forecast_df.columns)
        self.assertIn('NHITS', forecast_df.columns)
        self.assertIn('absolute_price', forecast_df.columns)
        
        # Verify that all absolute_price values in forecast_df are not None
        self.assertTrue(forecast_df['absolute_price'].notna().all())
    
    @patch('matplotlib.pyplot.savefig')
    def test_plot_absolute_prices_properties(self, mock_savefig):
        """Test that the plot_absolute_prices method creates a figure with expected properties."""
        # Mock savefig to avoid file system operations
        mock_savefig.return_value = None
        
        # Create plots directory if needed
        os.makedirs('plots', exist_ok=True)
        
        # Execute the plotting method
        fig = self.plotter.plot_absolute_prices(
            figsize=(10, 5),
            timeframe_configs=self.timeframe_configs,
            timeframe='1h'
        )
        
        # Verify that a figure was created
        self.assertIsInstance(fig, plt.Figure)
        
        # Get the axes from the figure
        axes = fig.get_axes()
        self.assertEqual(len(axes), 1)  # Should have one axis
        ax = axes[0]
        
        # Verify plot title
        self.assertTrue('BTC' in ax.get_title())
        self.assertTrue('1h' in ax.get_title())
        
        # Verify axis labels
        self.assertEqual(ax.get_xlabel(), 'Date')
        self.assertEqual(ax.get_ylabel(), 'Price (USD)')
        
        # Verify there are at least two lines (historical and forecast)
        self.assertGreaterEqual(len(ax.get_lines()), 2)
        
        # Verify there's a legend
        self.assertTrue(ax.get_legend() is not None)
        
        # Verify x-axis formatter is a DateFormatter
        self.assertIsInstance(ax.xaxis.get_major_formatter(), mdates.DateFormatter)
        
        # Verify savefig was called
        mock_savefig.assert_called()
    
    @patch('matplotlib.pyplot.savefig')
    def test_plot_absolute_prices_different_timeframes(self, mock_savefig):
        """Test the plot_absolute_prices method with different timeframes."""
        # Mock savefig to avoid file system operations
        mock_savefig.return_value = None
        
        # Create plots directory if needed
        os.makedirs('plots', exist_ok=True)
        
        timeframes = ['15m', '1h', '4h', '1d']
        
        for timeframe in timeframes:
            # Create mock data for this timeframe
            ohlcv_df = self.create_mock_ohlcv_data(timeframe)
            
            # Update the plotter with the new data
            self.plotter.ohlcv_df = ohlcv_df
            self.plotter.y_df = self.create_y_df(ohlcv_df)
            self.plotter.forecast_df = self.create_forecast_df(ohlcv_df)
            
            # Execute the plotting method
            fig = self.plotter.plot_absolute_prices(
                timeframe_configs=self.timeframe_configs,
                timeframe=timeframe
            )
            
            # Verify that a figure was created
            self.assertIsInstance(fig, plt.Figure)
            
            # Verify timeframe is in the title
            ax = fig.get_axes()[0]
            self.assertTrue(timeframe in ax.get_title())
            
            # Verify savefig was called
            mock_savefig.assert_called()
            
            # Reset mock for next iteration
            mock_savefig.reset_mock()
            
            # Close the figure to free memory
            plt.close(fig)
    
    def test_error_handling(self):
        """Test that appropriate errors are raised for invalid input."""
        # Test missing timeframe_configs
        with self.assertRaises(ValueError):
            self.plotter.plot_absolute_prices()
        
        # Test with None values for y_df and forecast_df
        temp_plotter = ResultPlotter(
            symbol=self.symbol,
            ohlcv_df=self.ohlcv_df_1h,
            y_df=None,
            forecast_df=None
        )
        
        with self.assertRaises(ValueError):
            temp_plotter.convert_returns_to_prices()


if __name__ == '__main__':
    unittest.main()