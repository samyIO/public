import glob
import os
import time
import requests
import logging
import pandas as pd
from datetime import datetime, timedelta

from data_handling.data_validator import DataValidator


class BinanceDataFetcher:

    def __init__(self):
        self.base_url = "https://api.binance.com/api/v3/klines"
        self.data_path = str(os.environ.get("DATA_PATH"))
    
    def fetch_multi_timeframe(self, symbol="ALGOUSDT", timeframe_filter=None):
        """
        Fetch data for multiple timeframes

                Args:
        symbol: Trading pair symbol (e.g., "ALGOUSDT")
        timeframe_filter: Optional specific timeframe to load
        
        Returns:
        Dictionary containing DataFrames for each timeframe
        """

        logging.info("Fetching data from API")
        timeframes = {
            '15m': {'days': 60},  # 2 months of 15m data
            '1h': {'days': 365},  # 1 year of hourly data
            '4h': {'days': 365},  # 1 year of 4h data
            '1d': {'days': 365}   # 1 year of daily data
        }
        # If timeframe_filter is specified, only update that timeframe
        if timeframe_filter:
            if timeframe_filter not in timeframes:
                raise ValueError(f"Invalid timeframe: {timeframe_filter}")
            timeframes = {timeframe_filter: timeframes[timeframe_filter]}        
        
        multi_data = {}
        request_count = 0
        minute_start = time.time()
        
        for interval, config in timeframes.items():
            start_date = datetime.now() - timedelta(days=config['days'])
            end_date = datetime.now()
            start_ts = int(start_date.timestamp() * 1000)
            end_ts = int(end_date.timestamp() * 1000)
            all_data = []
            
            current_start = start_ts
            while current_start < end_ts:
                # Rate limit check
                current_time = time.time()
                if current_time - minute_start >= 60:
                    request_count = 0
                    minute_start = current_time
                
                params = {
                    'symbol': symbol,
                    'interval': interval,
                    'startTime': current_start,
                    'limit': 100
                }
                
                try:
                    response = requests.get(self.base_url, params=params)
                    request_count += 1
                    
                    # Check for 429 (Too Many Requests) status
                    if response.status_code == 429:
                        retry_after = int(response.headers.get('Retry-After', 60))
                        logging.info(f"Rate limit exceeded, waiting for {retry_after} seconds")
                        time.sleep(retry_after)
                        continue
                        
                    batch_data = response.json()
                    
                    if not batch_data:
                        break
                        
                    all_data.extend(batch_data)
                    current_start = int(batch_data[-1][0]) + 1
                    
                    # Dynamic sleep based on rate limit usage
                    if request_count % 10 == 0:  # Check headers every 10 requests
                        used_weight = int(response.headers.get('X-MBX-USED-WEIGHT-1M', 0))
                        if used_weight > 800:  # If we're using too much weight
                            time.sleep(1)
                        else:
                            time.sleep(0.1)  # Minimal delay otherwise
                    
                except Exception as e:
                    logging.info(f"Error fetching {interval} data: {e}")
                    continue
                    
            if all_data:
                df = pd.DataFrame(all_data, columns=[
                    'timestamp', 'open', 'high', 'low', 'close', 'volume',
                ])
                
                # Process DataFrame
                df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
                for col in ['open', 'high', 'low', 'close', 'volume']:
                    df[col] = df[col].astype(float)
                
                df.set_index('timestamp', inplace=True)
                
                # Initialize the validator
                validator = DataValidator(price_decimals=4, volume_decimals=2)

                # Clean the data
                cleaned_df = validator.clean_data(df, fill_method='ffill')

                # Validate the data
                validation_results = validator.validate_data(cleaned_df)
                logging.info(validation_results)

                # Save to CSV with data directory
                os.makedirs(self.data_path, exist_ok=True)
                csv_filename = f"{self.data_path}/{symbol}_{interval}_{start_date.strftime('%Y%m%d')}_{end_date.strftime('%Y%m%d')}.csv"
                df.to_csv(csv_filename)
                
                multi_data[interval] = df
                logging.info(f"{interval} data: {len(df)} candles from {df.index.min()} to {df.index.max()}")
                logging.info(f"Data saved to {csv_filename}")

        logging.info("Data Fetching successful")        
        return multi_data
    
    def load_multi_timeframe_from_csv(self, symbol="ALGOUSDT", timeframe_filter=None):
        """
        Load multi-timeframe data from stored CSV files, if filter is set only load 
        the filtered data set
        
        Args:
        symbol: Trading pair symbol (e.g., "ALGOUSDT")
        timeframe_filter: Optional specific timeframe to load
        
        Returns:
        Dictionary containing DataFrames for each timeframe
        """

        logging.info(f"loading ohlcv data from path {self.data_path}")
        timeframes = ['15m', '1h', '4h', '1d']
        
        # If timeframe_filter is specified, only update that timeframe list
        if timeframe_filter:
            if timeframe_filter not in timeframes:
                raise ValueError(f"Invalid timeframe: {timeframe_filter}")
            timeframes = [timeframe_filter]
        
        multi_data = {}
        
        for timeframe in timeframes:
            try:
                # List all CSV files for this symbol and timeframe
                csv_pattern = f"{self.data_path}/{symbol}_{timeframe}_*.csv"
                matching_files = glob.glob(csv_pattern)
                
                if not matching_files:
                    logging.info(f"No CSV file found for {timeframe} timeframe")
                    continue
                    
                # Get the most recent file
                latest_file = max(matching_files)
                
                df = pd.read_csv(latest_file)
                
                # Convert timestamp to datetime but keep as column (not index)
                # Transform to index when needed for features
                df['timestamp'] = pd.to_datetime(df['timestamp'])
                
                # Reset the index to make sure we have an integer index
                if df.index.name == 'timestamp':
                    df = df.reset_index()
                
                # Convert columns to proper types
                for col in ['open', 'high', 'low', 'close', 'volume']:
                    df[col] = df[col].astype(float)
                    
                multi_data[timeframe] = df
            except Exception as e:
                logging.info(f"Error loading {timeframe} data: {e}")
                continue

        logging.info(f"Loaded {timeframe} data from {latest_file}: {len(df)} candles")           
        return multi_data
