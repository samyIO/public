import os
from forecasting.nhits_forecast import NHitsForecaster
from dotenv import load_dotenv

os.environ["DATA_PATH"] = "resources/data"
os.environ["OUTPUT_PATH"] = "resources/results"
load_dotenv()

if __name__ == "__main__":
    NHitsForecaster().run_forecast()