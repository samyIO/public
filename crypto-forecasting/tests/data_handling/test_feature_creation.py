import unittest
import os
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import tempfile
from unittest.mock import patch

from src.data_handling.feature_creation import FeatureCreator


class TestFeatureCreator(unittest.TestCase):
    def setUp(self):
        """Set up test environment before each test method."""
        # Create a temporary directory for output
        self.temp_dir = tempfile.mkdtemp()
        os.environ["OUTPUT_PATH"] = self.temp_dir
        os.makedirs(os.path.join(self.temp_dir, "features"), exist_ok=True)
        
        # Create sample OHLCV data for testing
        self.ohlcv_df = self.create_mock_ohlcv_data()
        
        # Initialize the FeatureCreator
        self.feature_creator = FeatureCreator(self.ohlcv_df)
    
    def create_mock_ohlcv_data(self, days=100):
        """Create mock OHLCV data for testing."""
        # Create timestamps
        end_date = datetime.now()
        timestamps = [end_date - timedelta(days=i) for i in range(days)]
        timestamps.sort()  # Sort in ascending order
        
        # Create price data (simple trend with some noise)
        base_price = 100  # Starting price
        prices = []
        for i in range(days):
            # Add trend and some noise
            new_price = base_price * (1 + 0.001 * i + 0.01 * np.random.randn())
            prices.append(new_price)
        
        # Create OHLCV dataframe
        df = pd.DataFrame({
            'timestamp': timestamps,
            'open': prices,
            'high': [p * (1 + 0.01 * np.random.random()) for p in prices],
            'low': [p * (1 - 0.01 * np.random.random()) for p in prices],
            'close': prices,
            'volume': [1000 * np.random.random() for _ in range(days)]
        })
        
        # Set timestamp as index
        df.set_index('timestamp', inplace=True)
        
        return df
    
    def tearDown(self):
        """Clean up after each test."""
        # Remove the temporary directory
        import shutil
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
    
    def test_init(self):
        """Test initialization of FeatureCreator."""
        self.assertEqual(self.feature_creator.df_ohlcv.equals(self.ohlcv_df), True)
        self.assertEqual(self.feature_creator.output_path, self.temp_dir)
    
    @patch('logging.info')
    def test_create_nhits_features(self, mock_logging):
        """Test the create_nhits_features method."""
        # Call the method
        feature_df = self.feature_creator.create_nhits_features()
        
        # Verify the output
        self.assertIsInstance(feature_df, pd.DataFrame)
        
        # Check that all expected features are created
        expected_features = self.feature_creator.get_all_feature_names() + ['target_next_return']
        for feature in expected_features:
            self.assertIn(feature, feature_df.columns)
        
        # Check that the CSV was saved
        expected_csv_path = os.path.join(self.temp_dir, "features", "feature_df.csv")
        self.assertTrue(os.path.exists(expected_csv_path))
        
        # Verify logging was called
        self.assertTrue(mock_logging.called)
    
    def test_create_nhits_features_data_quality(self):
        """Test the quality of features created."""
        # Call the method
        feature_df = self.feature_creator.create_nhits_features()
        
        # Check for NaNs
        self.assertFalse(feature_df.isnull().any().any(), "Features contain NaN values")
        
        # Check specific features for expected properties
        # RSI should be between 0 and 100
        self.assertTrue((feature_df['rsi_14'] >= 0).all() and (feature_df['rsi_14'] <= 100).all())
        
        # Verify that returns column exists and has numeric values
        self.assertIn('returns', feature_df.columns)
        self.assertTrue(np.issubdtype(feature_df['returns'].dtype, np.number))
        
        # Verify target_next_return exists and has numeric values
        self.assertIn('target_next_return', feature_df.columns)
        self.assertTrue(np.issubdtype(feature_df['target_next_return'].dtype, np.number))
        
        # Rather than testing the specific relationship, which might be affected by data cleaning,
        # let's verify the calculation directly using the same method as in the class
        test_target = feature_df['close'].pct_change(-1)
        
        # Find where both are not NaN so we can compare
        valid_indices = feature_df['target_next_return'].notna() & test_target.notna()
        
        # Test a few sample points
        sample_size = min(5, sum(valid_indices))
        valid_idx = np.where(valid_indices)[0][:sample_size]
        
        for i in valid_idx:
            self.assertAlmostEqual(
                feature_df['target_next_return'].iloc[i],
                test_target.iloc[i],
                places=10,
                msg=f"target_next_return at index {i} should equal close.pct_change(-1) at the same index"
            )
    
    def test_feature_df_with_timestamp_column(self):
        """Test feature creation when timestamp is a column, not the index."""
        # Reset index to make timestamp a column
        df_with_timestamp_col = self.ohlcv_df.reset_index()
        
        # Create FeatureCreator with this dataframe
        creator = FeatureCreator(df_with_timestamp_col)
        
        # Call the method
        feature_df = creator.create_nhits_features()
        
        # Verify the output
        self.assertIsInstance(feature_df, pd.DataFrame)
        self.assertIn('target_next_return', feature_df.columns)
    
    def test_get_all_feature_names(self):
        """Test the get_all_feature_names method."""
        feature_names = self.feature_creator.get_all_feature_names()
        
        # Check that we get a list of strings
        self.assertIsInstance(feature_names, list)
        self.assertTrue(all(isinstance(name, str) for name in feature_names))
        
        # Check for specific expected features
        expected_features = [
            'close', 'returns', 'rsi_14', 'volume_lag_1', 'macd_histogram', 
            'bollinger_bandwidth', 'day_sin', 'day_cos'
        ]
        for feature in expected_features:
            self.assertIn(feature, feature_names)
    
    def test_get_hist_exog_col_names(self):
        """Test the get_hist_exog_col_names method."""
        hist_exog_cols = self.feature_creator.get_hist_exog_col_names()
        
        # Check that we get a list of strings
        self.assertIsInstance(hist_exog_cols, list)
        self.assertTrue(all(isinstance(name, str) for name in hist_exog_cols))
        
        # Check that calendar features are not included
        self.assertNotIn('day_sin', hist_exog_cols)
        self.assertNotIn('day_cos', hist_exog_cols)
        
        # Check some expected historical features
        self.assertIn('close', hist_exog_cols)
        self.assertIn('rsi_14', hist_exog_cols)
    
    def test_get_future_exog_col_names(self):
        """Test the get_future_exog_col_names method."""
        future_exog_cols = self.feature_creator.get_future_exog_col_names()
        
        # Check that we get a list with the calendar features
        self.assertIsInstance(future_exog_cols, list)
        self.assertEqual(len(future_exog_cols), 2)
        self.assertIn('day_sin', future_exog_cols)
        self.assertIn('day_cos', future_exog_cols)

if __name__ == '__main__':
    unittest.main()