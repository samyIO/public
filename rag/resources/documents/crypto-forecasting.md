# Project: Crypto-Forecasting
Developed in February 2025

## Introduction

This project was my approach to learn more about traditional AI and the financial market. I'm interested in technical analysis and indicator correlations, therefore I found forecasting to be a good topic to combine my interest in AI with those topics.

The goal of this program is to forecast the behavior of an asset chart as accurately as possible. I experimented with different training metrics, feature compositions, and feature extraction methods to learn about the influence of each on the training outcome.
Ultimately, I identified core configurations that led to promising results.

### Data Source

Starting with the data, I use OHLCV data, that is gathered via publicly available APIs. In this specific case I used the public Binance API. The API handler requests multiple timeframes of data to explore.

### Baseline

As baseline, I used the actual asset chart of that time period from TradingView, a commonly
known Trading Platform.

![Baseline](resources/readme/baseline.png)

### Challenges

The biggest challenges actually arised in the preparation phase. Financial education is such a broad
area that it was very hard to identify the set of knowledge required to solve the task successfully.
While I was confident with the AI forecasting part, I've spent much time on learning indicators, correlations,
and macro-economic influences, since I had to gather how a price of an asset is constructed.

The second major challenge was the feature extraction.
After I had figured out necessary indicators, examining the correct feature set for the model training
resulted in a deep dive into technical analysis methods and trading strategies to get a feeling on how 
the indicators are effectively used in broadly accepted frameworks.
Later in the process I used correlation analysis and AI further optimize the feature choice.

### Model Choice

Choosing a model was one of the easier parts due to the framework I used to train and inference the models.
Nixtla offers a streamlined training and inference approach that is applicable to multiple model types, 
so I could freely play around and interchange the models without changing the code too much.

Finally NHits turned out to be the best model for the taks when compared to LSTM's or lightGbm.

NHits excels in understanding timely correlations on different timeframes and scales. This also is in line with the nature of the data and the actual goal.


### Result

After a longer experimentation phase, and several failures, using NHits and training it on the extracted feature set lead to promising results when using the MAE loss function.

![Result](resources/readme/result.png)

Note: In the results/plots folder you can find result plots of some experimentation runs.

### Evaluation

Due to the one-week timeframe of this project I decided to stick with baseline comparison as evaluation benchmark. This provides the benefit of an easy-to-understand result, without the need of in-depth technical knowledge, which eases the presentation. 

### Results

 The following files will be generated in the resources/results/ folder.

- plots/ALGOUSDT_1h_forecast.png (visualized forecast)
- forecasts/ALGOUSDT_forecast_df.csv (forecast result data)
- features/feature_df.csv (created features data)

Note:
Take a look at the other plots provided to get a feeling for the impact of the scaler choice.